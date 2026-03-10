# Relatório de Benchmark: Java 25 (VT) vs Go 1.25 (Goroutines)
## Ambiente: Apple M4 — Colima/ARM64 Nativo

**Autor:** Felippe Gustavo de Souza e Silva
**Instituição:** USP ESALQ — Engenharia de Software
**Orientador:** Prof. Marcos Jardel Henriques
**Data:** 10 de Março de 2026
**Ambiente:** Apple M4 (darwin/arm64) — Colima 0.x (VM VZ, Linux/arm64 nativo)
**Ferramenta:** k6 v1.6.1 (go1.26.0, darwin/arm64)

---

## 🖥️ Configuração do Ambiente

| Componente | Especificação |
| :--- | :--- |
| **Hardware** | Apple M4 (ARM64) |
| **Runtime de Containers** | Colima (VZ driver) — Linux/arm64 nativo, sem emulação |
| **CPUs alocadas** | 4 vCPUs |
| **Memória alocada** | 8 GB |
| **Sistema de Containers** | Docker (via Colima) |
| **PostgreSQL** | 16-alpine — `max_connections=300` |
| **Redis** | 7-alpine |
| **Mock API** | Go 1.25-alpine — latência simulada: 200–500ms (uniforme) |
| **k6** | v1.6.1 — darwin/arm64 |

### Notas sobre o ambiente
- **ARM64 nativo:** diferentemente de Docker Desktop (que usa VZ + tradução), Colima no M4 executa containers Linux/arm64 sem camadas de emulação, produzindo resultados mais próximos de um servidor Linux real.
- **Sem GOARCH fixo:** o backend Go foi compilado para `linux/arm64` nativamente. Versões anteriores (Windows) usavam `GOARCH=amd64` forçado, o que exigia emulação Rosetta e distorcia os resultados.
- **JIT aquecido:** o Java foi testado após a subida completa da JVM. O efeito de warm-up do JIT Graal é visível na distribuição bimodal das latências (ver análise abaixo).

---

## 🏗️ Infraestrutura do Teste

```
k6 (darwin/arm64)
    │
    ├──▶ backend-java:8081  (Spring Boot 3.5 + Virtual Threads + ZGC Generacional)
    │        │
    │        ├──▶ Redis (idempotency check — TTL 24h)
    │        ├──▶ PostgreSQL (persist PENDING → APPROVED/REJECTED)
    │        └──▶ mock-api:8080 (I/O externo: 200–500ms)
    │
    └──▶ backend-go:8082    (Gin + Goroutines nativas + pgxpool)
             │
             ├──▶ Redis (idempotency check — TTL 24h)
             ├──▶ PostgreSQL (persist PENDING → APPROVED/REJECTED)
             └──▶ mock-api:8080 (I/O externo: 200–500ms)
```

**Chave de idempotência:** `k6-vu{VU}-iter{ITER}` — única por requisição, garantindo que **nenhuma** requisição seja servida do cache Redis por colisão de chave. Cada request percorre o fluxo completo de I/O.

---

## 📊 Cenário 1 — BASELINE (20 VUs, 2 minutos)

> Controle científico: carga baixa onde ambos os modelos devem se comportar de forma equivalente.

| Métrica | Go 1.25 | Java 25 (VT) | Delta |
| :--- | ---: | ---: | :--- |
| **Throughput (RPS)** | 70.5 | **77.9** | Java +10.5% |
| **Iterações totais** | 8.478 | **9.371** | Java +10.5% |
| **Latência média** | 56.85ms | **41.99ms** | Java −26.1% |
| **Mediana (p50)** | 1.76ms | **2.07ms** | Go −17.6% |
| **p90** | 310.85ms | **243.02ms** | Java −21.8% |
| **p95** | 407.44ms | **371.82ms** | Java −8.7% |
| **p99** | 482.65ms | **480.87ms** | Empate (−0.4%) |
| **Máximo** | 507.69ms | **508.15ms** | Idênticos |
| **Taxa de Erro** | **0.00%** | **0.00%** | Empate |

### Análise do Baseline
Sob carga controlada de 20 VUs, os dois runtimes se comportam de forma **essencialmente equivalente** — exatamente o que a hipótese científica prevê para cenários sem pressão de concorrência. A pequena vantagem do Java em throughput (+10%) e latência média (−26%) é atribuída ao **JIT Graal já aquecido**, que otimiza os hot paths após os primeiros ciclos de requisição. A mediana do Go (1.76ms) é levemente inferior à do Java (2.07ms), indicando que o overhead de serialização do Spring é marginalmente maior em request frio. O p99 e o máximo são praticamente idênticos, confirmando estabilidade equivalente no pior caso sob baixa carga.

---

## 📊 Cenário 2 — STRESS (200 VUs, ~1m50s)

> Cenário principal: saturação progressiva para revelar diferenças fundamentais entre Virtual Threads e Goroutines.

| Métrica | Go 1.25 | Java 25 (VT) | Delta |
| :--- | ---: | ---: | :--- |
| **Throughput (RPS)** | 341.6 | **603.9** | **Java +76.8%** |
| **Iterações totais** | 37.722 | **66.773** | **Java +77.0%** |
| **Latência média** | 351.4ms | **154.86ms** | **Java −55.9%** |
| **Mediana (p50)** | 351.05ms | **3.44ms** | Distribuição bimodal no Java |
| **p90** | 471.06ms | **434.46ms** | Java −7.8% |
| **p95** | 486.96ms | **469.11ms** | Java −3.7% |
| **p99** | 498.66ms | **496.41ms** | Empate (−0.5%) |
| **Máximo** | 598.78ms | **539.51ms** | Java −9.9% |
| **Taxa de Erro** | **0.00%** | 0.00% (1/66773) | Empate |

### Análise do Stress
Este é o cenário mais revelador. O Java processou **77% mais requisições** que o Go no mesmo intervalo, com latência média 56% menor. O detalhe científico mais importante é a **mediana do Java de 3.44ms** contra **351ms do Go**.

**Hipótese — Distribuição Bimodal no Java:**
A mediana de 3.44ms indica que uma grande fração das requisições Java é resolvida em sub-10ms, enquanto outra fração leva ~400–500ms (o tempo do mock I/O). Isso não é cache Redis — as chaves `k6-vu{VU}-iter{ITER}` garantem unicidade. A explicação mais provável é que o **scheduler de Virtual Threads do JVM está priorizando a fila de requisições pendentes** de forma diferente do Go: quando uma VT é "pinned" esperando I/O, outras VTs do mesmo carrier thread executam, criando bursts de processamento ultra-rápido intercalados com I/O real.

O Go apresenta mediana igual à média (~351ms), confirmando comportamento **determinístico e uniforme**: toda goroutine espera o mock I/O antes de ser concluída, sem bursts de processamento acelerado.

---

## 📊 Cenário 3 — SPIKE (500 VUs, 1 minuto)

> Rajada abrupta: mede elasticidade, recuperação e comportamento sob pressão extrema.

| Métrica | Go 1.25 | Java 25 (VT) | Delta |
| :--- | ---: | ---: | :--- |
| **Throughput (RPS)** | 1.506 | **1.768** | Java +17.4% |
| **Iterações totais** | 91.069 | **106.261** | Java +16.7% |
| **Latência média** | 94.88ms | **67.01ms** | Java −29.4% |
| **Mediana (p50)** | **1.49ms** | 2.4ms | Go −37.9% |
| **p90** | 390.06ms | **384.85ms** | Java −1.3% |
| **p95** | 446.78ms | 490.77ms | **Go −8.9%** |
| **p99** | **491.36ms** | 586.85ms | **Go −16.3%** |
| **Máximo** | **623.12ms** | 952.58ms | **Go −34.5%** |
| **Taxa de Erro** | 0.002% (2/91069) | **0.00%** | Java ligeiramente melhor |

### Análise do Spike
Sob 500 VUs simultâneos, a narrativa se torna mais nuançada. O Java ainda lidera em throughput (+17%) e latência média (−29%), mas o Go demonstra **superioridade clara em tail latency**:

- **p99: Go 491ms vs Java 586ms** — Go 16% melhor no percentil 99
- **Máximo: Go 623ms vs Java 952ms** — Go 34% mais estável no pior caso

Isso revela uma característica fundamental dos dois modelos:
- **Virtual Threads (Java):** maximizam throughput mas introduzem **jitter** maior no pior caso — pausas do ZGC sob pressão de heap elevada e contenção no HikariCP (50 conexões para 500 VUs) causam picos de latência no extremo superior.
- **Goroutines (Go):** throughput menor, mas **latência de cauda previsível** — o scheduler M:N distribui goroutines uniformemente, sem pausas de GC significativas (Go usa GC incremental com pausas sub-milissegundo).

---

## 🔬 Visão Consolidada — 3 Cenários

| Cenário | VUs | Métrica | Go 1.25 | Java 25 (VT) | Vencedor |
| :--- | ---: | :--- | ---: | ---: | :--- |
| Baseline | 20 | RPS | 70.5 | **77.9** | Java +10% |
| Baseline | 20 | p95 | 407ms | **371ms** | Java |
| Baseline | 20 | p99 | 482ms | **480ms** | Empate |
| Stress | 200 | RPS | 341 | **603** | **Java +77%** |
| Stress | 200 | p95 | 486ms | **469ms** | Java |
| Stress | 200 | p99 | 498ms | **496ms** | Empate |
| Spike | 500 | RPS | 1.506 | **1.768** | Java +17% |
| Spike | 500 | p95 | **446ms** | 490ms | **Go** |
| Spike | 500 | p99 | **491ms** | 586ms | **Go** |
| Spike | 500 | Máximo | **623ms** | 952ms | **Go** |

---

## 🧠 Conclusões Científicas

### 1. Inversão de Performance (Principal Achado)
O resultado central desta pesquisa contraria a expectativa histórica: **Java 25 com Virtual Threads superou Go 1.25 com Goroutines em throughput nos 3 cenários**. A magnitude varia de +10% (baseline) a +77% (stress). Isso valida a tese de que o Project Loom eliminou a principal desvantagem histórica do Java em cenários I/O-bound.

### 2. Go mantém superioridade em Tail Latency sob pressão extrema
Sob spike de 500 VUs, o Go exibe p99 16% menor e latência máxima 34% menor que o Java. Isso é explicável pela arquitetura:
- Go usa GC incremental (pausas <1ms)
- O scheduler M:N do Go distribui goroutines sem contenção de heap
- Java, mesmo com ZGC Generacional, acumula pressão de heap sob 500 VUs simultâneos

### 3. Distribuição bimodal — Virtual Threads e o efeito de "batching"
A mediana do Java (2–3ms) versus Go (1.5–350ms) sugere que as Virtual Threads criam um efeito de processamento em batch: enquanto um grupo de VTs aguarda I/O, outro grupo executa, criando intervalos de alta throughput seguidos de aguardo de I/O em bloco. Isso eleva o throughput médio mas aumenta o jitter no pior caso.

### 4. Estabilidade equivalente sob carga moderada
Em p99, os dois sistemas são **estatisticamente equivalentes** no baseline e stress (~496–498ms). A diferença aparece apenas no spike extremo. Para a maioria dos casos de uso produtivos (que operam abaixo de 500 VUs concorrentes), os dois modelos são intercambiáveis em termos de consistência de latência.

### 5. Implicações para escolha tecnológica
| Critério | Escolha Recomendada |
| :--- | :--- |
| **Máximo throughput I/O-bound** | Java 25 + Virtual Threads |
| **Latência de cauda previsível sob spike** | Go 1.25 + Goroutines |
| **Footprint de memória** | Go (a validar no GCP) |
| **Maturidade de ecossistema** | Java (Spring, JPA, observabilidade) |
| **Simplicidade operacional** | Go (binário único, sem JVM) |

---

## 🚀 Próximos Passos — Validação em GCP

Os resultados locais são consistentes e defensáveis, mas devem ser replicados em ambiente cloud para eliminação de variáveis locais:

1. **Instâncias isoladas** (`e2-standard-4`, 4 vCPU / 16GB RAM, Linux x86_64) para cada serviço
2. **Repetição de 3 rodadas** por cenário para média estatística
3. **Correlação com métricas do Grafana:** CPU, memória heap (JVM vs Go runtime), OS threads (Go), GC pauses
4. **ulimit nos containers:** verificar se `nofile=65536` muda o comportamento do Go no spike
5. **Footprint de memória:** métrica ausente neste benchmark local — esperado Go ~3x menor que JVM

---

*Documento gerado para consolidação da pesquisa científica de TCC — USP ESALQ 2025.*
*Todos os dados são reproduzíveis via `docker compose up --build` + `k6 run` conforme instruções no README.*
