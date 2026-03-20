# Plano GKE — TCC Performance Comparison
**Migração do laboratório local (Apple M4 + Colima) para GKE (Google Kubernetes Engine)**

> **Objetivo científico:** Validar os resultados locais em ambiente cloud real (x86_64, Linux nativo, rede virtualizada), adicionar análise de densidade de pods e custo por RPS — dados que só existem em Kubernetes.

---

## Contexto: o que os resultados locais já provaram

| Cenário | Java 25 VT | Go 1.25 | Quarkus Native | Conclusão |
|---|---|---|---|---|
| Baseline + Stress (pool=200) | ~355ms | ~353ms | ~355ms | Empate estatístico (CV < 2%) |
| Spike (500 VUs, pool=200) | 723ms, 362 RPS | 353ms, 655 RPS | 360ms, 646 RPS | Go e Quarkus vencem em 80% |
| Spike (500 VUs, pool=500) | 357ms, equiv. | 352ms, equiv. | — | Empate quando pool adequado |
| RAM (Stress) | ~1.1 GB | ~44 MB | ~82 MB | Go −96%, Quarkus −93% vs Java |
| RAM (Spike) | ~1.9 GB | ~68 MB | ~347 MB | Go −96%, Quarkus −82% vs Java |

**O que ainda falta provar:**
1. O JIT da JVM em x86_64 Linux nativo (não ARM) pode reduzir ainda mais a latência do Java
2. Com resource limits reais de Kubernetes, qual é o custo mínimo por RPS de cada runtime
3. Quantas instâncias de cada backend cabem num node de produção padrão

---

## Arquitetura GKE proposta

```
┌─────────────────────────────────────────────────────────┐
│  GKE Cluster — zona: us-central1-a (single-zone, free)  │
│                                                         │
│  Node Pool: e2-standard-4 (4 vCPU / 16 GB) x 2 nodes   │
│                                                         │
│  Node 1 — Infraestrutura                                │
│  ┌──────────┐  ┌───────┐  ┌──────────┐                 │
│  │ postgres │  │ redis │  │ mock-api │                  │
│  └──────────┘  └───────┘  └──────────┘                 │
│                                                         │
│  Node 2 — Benchmarks (um backend por vez)               │
│  ┌──────────────┐  ┌──────────────────┐                 │
│  │ backend-java │  │ prometheus+grafana│                 │
│  │ ou backend-go│  └──────────────────┘                 │
│  │ ou quarkus   │                                       │
│  └──────────────┘                                       │
│                                                         │
│  k6 roda de VM externa (e2-micro) para isolar carga     │
└─────────────────────────────────────────────────────────┘
```

**Por que 2 nodes separados:**
- Elimina contenção de CPU/RAM entre infra e backend
- Garante que o resultado mede o runtime, não o Postgres disputando CPU

---

## Estimativa de custo

| Recurso | Tipo | Custo/hora | Horas estimadas | Total |
|---|---|---|---|---|
| Node infra | e2-standard-2 (2vCPU/8GB) | $0.067 | 8h | ~$0.54 |
| Node benchmark | e2-standard-4 (4vCPU/16GB) | $0.134 | 8h | ~$1.07 |
| VM k6 | e2-micro (2vCPU/1GB) | $0.008 | 8h | ~$0.06 |
| Artifact Registry | storage imagens | ~$0.001/GB | — | ~$0.10 |
| GKE control plane | zonal (1 cluster free) | $0.00 | — | $0.00 |
| **Total estimado** | | | | **~$2–5** |

Com $300 disponíveis, há margem para 50+ reexecuções completas sem preocupação.

---

## Fases do plano

### Fase 0 — Pré-requisitos (1 dia)

**Objetivo:** Configurar o ambiente GCP local.

```bash
# 1. Instalar ferramentas (se não tiver)
brew install google-cloud-sdk kubectl

# buildx não vem junto com o Docker do Homebrew — instalar separadamente
brew install docker-buildx
mkdir -p ~/.docker/cli-plugins
ln -sf /opt/homebrew/opt/docker-buildx/bin/docker-buildx ~/.docker/cli-plugins/docker-buildx
docker buildx version  # deve retornar: github.com/docker/buildx vX.X.X

# 2. Login e configuração do projeto
gcloud auth login
gcloud projects create tcc-performance-2026 --name="TCC Performance"
gcloud config set project tcc-performance-2026

# 3. Habilitar APIs necessárias
gcloud services enable \
  container.googleapis.com \
  artifactregistry.googleapis.com \
  compute.googleapis.com

# 4. Configurar billing (vincular ao crédito de $300)
# Feito via console: console.cloud.google.com/billing
```

---

### Fase 1 — Artifact Registry (1 dia)

**Objetivo:** Publicar as imagens Docker no registry do GCP.

Os Dockerfiles existentes já são multi-arch (Go não fixa GOARCH, Java usa eclipse-temurin).
O Quarkus usa Mandrel builder que suporta linux/amd64 nativamente.

```bash
# 1. Criar o registry
gcloud artifacts repositories create tcc-benchmarks \
  --repository-format=docker \
  --location=us-central1 \
  --description="TCC Performance Comparison Images"

# 2. Autenticar Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

REGISTRY="us-central1-docker.pkg.dev/tcc-performance-2026/tcc-benchmarks"

# 3. Build e push — Java 25
docker buildx build \
  --platform linux/amd64 \
  -t $REGISTRY/backend-java:latest \
  --push \
  apps/backend-java/

# 4. Build e push — Go 1.25
docker buildx build \
  --platform linux/amd64 \
  -t $REGISTRY/backend-go:latest \
  --push \
  apps/backend-go/

# 5. Build e push — Quarkus Native (~4min via Rosetta, validado localmente no M4)
docker buildx build \
  --platform linux/amd64 \
  -t $REGISTRY/backend-quarkus:latest \
  --push \
  apps/backend-quarkus/

# 6. Mock API
docker buildx build \
  --platform linux/amd64 \
  -t $REGISTRY/mock-api:latest \
  --push \
  apps/mock-external-api/
```

> **Quarkus validado localmente:** Build para `linux/amd64` testado e aprovado no M4 via
> Rosetta em ~4 min. GraalVM gerou binário `x86-64-v3` (AVX2) com 105MB — arquitetura
> compatível com todos os nodes `e2-standard` do GCP. Nenhum ajuste no Dockerfile necessário.

---

### Fase 2 — Cluster GKE (meio dia)

**Objetivo:** Criar o cluster com node pools separados para infra e benchmarks.

```bash
# 1. Criar cluster (control plane gratuito para cluster zonal)
gcloud container clusters create tcc-cluster \
  --zone us-central1-a \
  --num-nodes 1 \
  --machine-type e2-standard-2 \
  --disk-size 30 \
  --no-enable-autoupgrade

# 2. Node pool dedicado para benchmarks (nodes maiores)
gcloud container node-pools create benchmark-pool \
  --cluster tcc-cluster \
  --zone us-central1-a \
  --machine-type e2-standard-4 \
  --num-nodes 1 \
  --node-labels role=benchmark \
  --disk-size 30

# 3. Obter credenciais
gcloud container clusters get-credentials tcc-cluster --zone us-central1-a

# 4. Verificar
kubectl get nodes -L role
```

---

### Fase 3 — Manifests Kubernetes (2 dias)

**Objetivo:** Criar todos os manifests com resource limits definidos.
Estrutura de diretórios a criar:

```
k8s/
├── namespace.yaml
├── infra/
│   ├── postgres.yaml
│   ├── redis.yaml
│   └── mock-api.yaml
├── backends/
│   ├── backend-java.yaml
│   ├── backend-go.yaml
│   └── backend-quarkus.yaml
├── observability/
│   ├── prometheus-configmap.yaml
│   ├── prometheus.yaml
│   └── grafana.yaml
└── jobs/
    └── k6-job.yaml        # k6 como Job do Kubernetes (opcional)
```

**Resource limits — definição científica:**

| Container | CPU request | CPU limit | Mem request | Mem limit |
|---|---|---|---|---|
| backend-java | 500m | 2000m | 512Mi | 2048Mi |
| backend-go | 100m | 500m | 32Mi | 256Mi |
| backend-quarkus | 100m | 1000m | 64Mi | 512Mi |
| postgres | 500m | 1000m | 256Mi | 1024Mi |
| redis | 50m | 200m | 32Mi | 256Mi |
| mock-api | 100m | 500m | 32Mi | 128Mi |

> Os limits do Java são generosos intencionalmente — o objetivo é medir quanto ele
> realmente usa, não artificialmente limitá-lo. O que importa é que o Go e Quarkus
> provam que entregam a mesma performance com limits muito menores.

**Exemplo — backend-java.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-java
  namespace: tcc
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend-java
  template:
    metadata:
      labels:
        app: backend-java
    spec:
      nodeSelector:
        role: benchmark
      containers:
        - name: backend-java
          image: us-central1-docker.pkg.dev/tcc-performance-2026/tcc-benchmarks/backend-java:latest
          ports:
            - containerPort: 8081
          env:
            - name: SPRING_DATASOURCE_URL
              value: jdbc:postgresql://postgres:5432/gateway_db
            - name: EXTERNAL_API_BASE_URL
              value: http://mock-api:8080
            - name: SPRING_DATA_REDIS_HOST
              value: redis
            - name: HIKARI_MAX_POOL_SIZE
              value: "200"
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "2000m"
              memory: "2048Mi"
          readinessProbe:
            httpGet:
              path: /actuator/health
              port: 8081
            initialDelaySeconds: 30
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: backend-java
  namespace: tcc
spec:
  selector:
    app: backend-java
  ports:
    - port: 8081
      targetPort: 8081
  type: ClusterIP
```

**Mesma estrutura para Go e Quarkus — só mudam ports, env vars e resource limits.**

---

### Fase 4 — Script de benchmark adaptado para GKE (1 dia)

**Objetivo:** Adaptar `run_benchmarks.sh` para ambiente Kubernetes.

Diferenças em relação ao script local:
- `docker exec redis redis-cli FLUSHALL` → `kubectl exec -n tcc deploy/redis -- redis-cli FLUSHALL`
- `docker stats` para RAM → `kubectl top pod` (metrics-server já vem no GKE)
- URLs dos backends via `kubectl port-forward` ou LoadBalancer externo para o k6

**Estratégia para o k6:**
Rodar k6 de uma VM `e2-micro` externa ao cluster para simular carga real de rede:

```bash
# Criar VM para o k6
gcloud compute instances create k6-runner \
  --zone us-central1-a \
  --machine-type e2-micro \
  --image-family debian-11 \
  --image-project debian-cloud

# Expor backends via LoadBalancer temporário durante o benchmark
# (criar/deletar o service durante cada run para economizar)
```

Alternativamente, rodar o k6 dentro do cluster como `Job` Kubernetes — mais simples e elimina custo de VM extra. Os resultados ficam nos logs do Pod.

**Coleta de RAM em GKE:**
```bash
# Durante cada rodada, em background:
kubectl top pod -n tcc backend-java-<pod-id> --no-headers >> $mem_file &
```

O `kubectl top` coleta com granularidade de ~15s. Para granularidade maior, usar as métricas do Prometheus já configurado (`container_memory_working_set_bytes`).

---

### Fase 5 — Experimento de densidade (exclusivo do GKE)

**Objetivo:** O experimento científico mais valioso desta fase.

**Pergunta:** Dado um node `e2-standard-4` (4 vCPU / 16 GB), quantas instâncias de cada backend conseguem rodar simultaneamente entregando o mesmo throughput alvo (ex: 100 RPS cada)?

```bash
# Escalar backends horizontalmente e medir limite prático
kubectl scale deployment backend-go -n tcc --replicas=10
kubectl scale deployment backend-java -n tcc --replicas=3  # Java limita pela RAM

# Medir: quantas réplicas até o node atingir 80% de RAM
kubectl top nodes
kubectl top pods -n tcc
```

**Resultado esperado e impacto:**

| Backend | RAM por pod | Pods num e2-standard-4 (16GB) | Custo GCP (e2-standard-4/mês) | Custo por pod/mês |
|---|---|---|---|---|
| Java 25 VT | ~1.5 GB | ~8 pods | ~$97 | ~$12.12 |
| Quarkus Native | ~200 MB | ~64 pods | ~$97 | ~$1.51 |
| Go 1.25 | ~80 MB | ~160 pods | ~$97 | ~$0.60 |

Esse dado transforma o TCC de "benchmark técnico" em "análise de custo de infraestrutura".

---

### Fase 6 — Protocolo de execução idêntico ao local

**Cenários (mesmos do M4):**

| # | Cenário | VUs | Duração | Pool | Rodadas |
|---|---|---|---|---|---|
| 1 | Baseline | 20 | 2 min | 200 | 3 |
| 2 | Stress | 200 | 2 min | 200 | 3 |
| 3 | Spike | 500 | 1 min | 200 | 3 |
| 4 | Spike (pool adequado) | 500 | 1 min | 500 | 3 |

**Protocolo de isolamento (igual ao M4):**
- Redis FLUSHALL antes de cada rodada
- Apenas um backend rodando por vez (os outros com replicas=0)
- Aguardar readinessProbe antes de iniciar k6
- 3 rodadas por configuração → calcular média ± σ → validar CV < 5%

**Resultado total:** 4 cenários × 3 backends × 3 rodadas = **36 execuções k6**

---

### Fase 7 — Resultados e documentação TCC

**Estrutura dos resultados:**
```
results/
├── local_benchmarks/          # já existente (Apple M4)
│   └── M4_BENCHMARK_REPORT_V3_FINAL.md
└── gke_benchmarks/            # novo
    ├── runs/
    │   └── <timestamp>/
    │       ├── java_baseline_round1.json
    │       └── ...
    ├── GKE_BENCHMARK_REPORT.md
    └── DENSITY_ANALYSIS.md    # o diferencial científico
```

**Comparação final M4 vs GKE:**
A comparação entre ambientes é um dado científico por si só:
- Se Java melhora mais que Go no GKE x86_64 → JIT em x86 é melhor que ARM64 (hipótese válida)
- Se Go mantém vantagem de RAM idêntica → footprint é estrutural, não arquitetural
- Se Quarkus Native surpreende em x86_64 → AOT pode ser ainda mais eficiente sem JVM

---

## Cronograma proposto (encaixar no TCC até Novembro)

| Mês | Atividade |
|---|---|
| Abril | Fase 0–1: GCP setup, build e push das imagens |
| Maio | Fase 2–3: Cluster GKE + manifests Kubernetes |
| Junho | Fase 4–5: Execução dos benchmarks + experimento de densidade |
| Julho | Fase 6: Análise dos resultados e relatório comparativo M4 vs GKE |
| Agosto | Início da escrita do TCC com todos os dados em mãos |
| Setembro–Outubro | Escrita, revisão, correções |
| Outubro | Entrega |

---

## Riscos e mitigações

| Risco | Probabilidade | Mitigação |
|---|---|---|
| Build do Quarkus Native falhar em x86_64 | ~~Média~~ **Baixa** | ✅ Validado: build `linux/amd64` bem-sucedido em ~4min no M4 via Rosetta, binário x86-64-v3 de 105MB gerado corretamente |
| Custo exceder $300 | Baixa | Monitorar via `gcloud billing` + criar budget alert em $50 |
| Java superar Go em x86_64 e complicar a narrativa | Baixa-Média | Esse é um resultado científico válido — documentar como achado, não como problema |
| Métricas de RAM do `kubectl top` com baixa granularidade | Média | Usar `container_memory_working_set_bytes` via Prometheus (já configurado no stack) |
| Rede entre pods introduzir latência não controlada | Baixa | Node affinity garante infra e backend no mesmo zone; latência intra-cluster GKE é < 1ms |

---

## O que o GKE prova que o M4 não prova

1. **Reprodutibilidade em ambiente neutro** — x86_64 Linux nativo, sem camada de virtualização
2. **Resource limits reais** — como cada runtime se comporta com CPU/RAM limitados por Kubernetes
3. **Custo por RPS calculado** — dado econômico direto para decisão arquitetural
4. **Densidade de pods** — quantas instâncias cabem por node de produção
5. **Cold start em cloud** — JVM warm-up em ambiente com cold starts frequentes (auto-scaling)
6. **Dado citável** — resultados em GKE são reproduzíveis por qualquer pessoa com créditos GCP

---

## Próximo passo imediato

```bash
# Verificar se o buildx já está configurado para linux/amd64
docker buildx ls

# Testar o build do Java local para linux/amd64 antes de subir para o GCP
docker buildx build \
  --platform linux/amd64 \
  --load \
  -t backend-java:test-amd64 \
  apps/backend-java/
```

✅ **Validado em 20/03/2026:** Os 3 backends compilam corretamente para `linux/amd64` no M4.
- Go: ~1 min (cross-compile nativo)
- Java: ~5 min (temurin:25 tem imagem amd64)
- Quarkus Native: ~4 min via Rosetta (binário x86-64-v3, 105MB)

A Fase 1 pode ser executada diretamente sem ajustes nos Dockerfiles.
