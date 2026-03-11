# Metodologia de Benchmark — Detalhamento Científico
## Java 25 Virtual Threads vs Go 1.25 Goroutines

**Autor:** Felippe Gustavo de Souza e Silva
**Instituição:** USP ESALQ — Engenharia de Software
**Versão:** 1.0 — Março de 2026

---

## 1. Ferramenta de Carga: k6

### 1.1 Por que k6 e não JMeter, Gatling ou Locust?

| Critério | k6 | JMeter | Gatling | Locust |
| :--- | :--- | :--- | :--- | :--- |
| **Modelo de concorrência** | Goroutines (Go) | Threads Java | Coroutines (Scala/Akka) | Greenlets (Python) |
| **Overhead do gerador** | Mínimo (~2KB/VU) | Alto (~1MB/thread) | Médio | Médio |
| **Scripting** | JavaScript ES2015+ | XML/GUI | Scala DSL | Python |
| **Saída de dados** | NDJSON, CSV, InfluxDB | XML, CSV | Gatling report | CSV |
| **Reprodutibilidade** | Alta (código versionável) | Baixa (GUI state) | Alta | Alta |
| **Distribuído** | k6 Cloud / k6 operator | Complexo | Injector nodes | Master/worker |

**Decisão:** k6 foi escolhido por ter o menor overhead por VU (Virtual User), garantindo que o gerador de carga não se torne o gargalo do experimento. Com JMeter, cada thread do gerador consome ~1MB — com 500 VUs simultâneos, o gerador usaria 500MB apenas para existir, competindo por recursos com o backend sendo testado. k6 com 500 VUs consome menos de 10MB.

### 1.2 Modelo de VU (Virtual User)

No k6, cada **VU (Virtual User)** é uma goroutine que executa o script em loop contínuo:

```
VU lifecycle:
  setup() → [default function loop] → teardown()
                   ↕ repete até fim do teste
```

Cada iteração de um VU:
1. Monta o payload JSON com `amount` aleatório
2. Gera a `X-Idempotency-Key` única: `k6-vu{N}-iter{I}`
3. Envia `POST /payments`
4. Valida resposta (status 201 + campo `id`)
5. Dorme 100ms (`sleep(0.1)`)
6. Repete

O `sleep(0.1)` é intencional e calibrado: com latência de resposta de ~350ms e 100ms de think time, cada VU gera aproximadamente **2,2 requests/segundo**. Com 200 VUs: **~440 requests simultâneos em-flight** a qualquer momento — expondo o comportamento de concorrência do backend.

### 1.3 Relação VUs → RPS (Lei de Little)

A **Lei de Little** (John D.C. Little, 1961) estabelece:

```
N = λ × W

onde:
  N = número médio de requisições em-flight (≈ VUs ativos)
  λ = taxa de chegada (RPS)
  W = tempo médio de serviço (latência média)
```

Invertendo: `λ = N / W`

Para o cenário stress (200 VUs, latência ~352ms):
```
λ = 200 / (0.352 + 0.100) = 200 / 0.452 ≈ 442 req/s teórico
```
Resultado observado: ~340 RPS — o delta reflete overhead de conexão TCP, handshake Redis e variância do mock (200–500ms).

Esta lei é usada no Painel 17 do Grafana para estimar requests in-flight do Java sem gauge direto.

---

## 2. Desenho dos Cenários

### 2.1 Filosofia geral

Três cenários foram desenhados para responder perguntas científicas distintas, seguindo a estrutura de **experimento controlado**:

```
Pergunta 1: os runtimes são equivalentes em condições normais?
  → Baseline (20 VUs) — controle científico

Pergunta 2: qual runtime é mais eficiente sob carga sustentada?
  → Stress (200 VUs) — cenário principal

Pergunta 3: qual runtime é mais resiliente a picos abruptos?
  → Spike (500 VUs) — teste de elasticidade
```

### 2.2 Cenário 1 — Baseline (Controle)

```javascript
stages: [
  { duration: '30s', target: 10 },   // rampa suave
  { duration: '60s', target: 20 },   // 20 VUs sustentados (janela de coleta)
  { duration: '30s', target: 0 },    // cool-down
]
thresholds: { p95 < 1000ms, erros < 1% }
```

**Racional científico:** 20 VUs com mock de 350ms gera ~44 RPS — carga muito abaixo da capacidade de qualquer runtime moderno. **Ambos os sistemas devem se comportar identicamente**. Se divergirem, indica problema de configuração ou medição. É o grupo controle que valida a simetria do experimento.

**O que prova:** Que as diferenças observadas nos cenários seguintes são causadas pela carga, não por assimetrias de configuração.

### 2.3 Cenário 2 — Stress (Principal)

```javascript
stages: [
  { duration: '10s', target: 50 },   // warm-up: JVM aquece JIT
  { duration: '30s', target: 200 },  // ramp-up progressivo
  { duration: '60s', target: 200 },  // sustentação: janela principal de coleta
  { duration: '10s', target: 0 },    // cool-down gracioso
]
thresholds: { p95 < 800ms, p99 < 1500ms, erros < 1% }
```

**Por que 200 VUs?** O pool de conexões de ambos os backends foi configurado em 200 conexões (HikariCP e pgxpool). Com 200 VUs, **cada VU potencialmente precisa de 1 conexão simultânea** — o sistema opera no limite do pool sem entrar em contenção. É o ponto de máxima carga sustentável onde o scheduler de concorrência (Virtual Threads vs Goroutines) é mais evidenciado, sem o fator confundidor do pool.

**Por que o warm-up de 10s para 50 VUs?** A JVM precisa de carga para acionar o JIT compiler. Sem warm-up, os primeiros segundos do Java seriam medidos com código interpretado — resultado não representativo da performance em produção. O warm-up garante que ambos os runtimes sejam medidos em estado estacionário.

**Janela de coleta:** Os 60s de sustentação a 200 VUs são a janela principal de coleta de dados. O k6 reporta métricas agregadas de toda a execução, mas a fase estável é onde os percentis p95 e p99 são mais significativos.

### 2.4 Cenário 3 — Spike (Elasticidade)

```javascript
stages: [
  { duration: '10s', target: 10 },   // estado estável inicial
  { duration: '5s',  target: 500 },  // spike abrupto: 10→500 VUs em 5 segundos
  { duration: '30s', target: 500 },  // sustentação do pico
  { duration: '5s',  target: 10 },   // queda abrupta
  { duration: '10s', target: 0 },    // cool-down
]
thresholds: { p95 < 2000ms, p99 < 4000ms, erros < 5% }
```

**Por que 500 VUs com ramp de 5s?** Simula um cenário real de tráfego viral ou falha de balanceador de carga — situação onde o sistema recebe 25x mais tráfego do que o normal em segundos. O ramp abrupto (5s para 500 VUs) é propositalmente agressivo para revelar a **elasticidade do modelo de concorrência**: quanto tempo o runtime leva para provisionar goroutines/Virtual Threads suficientes?

**Por que threshold de erros relaxado (5%)?** O ramp de 5s para 500 VUs inevitavelmente causa alguns erros de estabelecimento de conexão TCP — isso é fisicamente esperado. O threshold de 5% define o limite científico aceitável: acima disso, o backend entrou em colapso; abaixo, o sistema se recuperou graciosamente.

**Variável de controle — pool=200 vs pool=500:** O spike com pool=200 testou **contenção de pool** (300 VUs aguardando 200 conexões). O spike com pool=500 isolou o **scheduler puro** (cada VU com conexão disponível). A comparação entre os dois resultados permitiu isolar a causa da diferença de performance.

---

## 3. Protocolo de Isolamento Redis

### 3.1 O problema descoberto (e por que é crítico)

O backend implementa **idempotência via Redis**: a chave `X-Idempotency-Key` é armazenada por 24h. Se o mesmo key chegar duas vezes, o segundo request retorna o resultado cacheado sem tocar no banco ou na API externa.

O k6 gera keys com `k6-vu${__VU}-iter${__ITER}`. O `__ITER` é um contador **por processo k6** — ele reseta para 0 a cada novo `k6 run`.

**Consequência:** Se Go for testado primeiro (keys `k6-vu1-iter0` até `k6-vu200-iter187`) e Java for testado depois, o Java encontra essas keys já no Redis e retorna cache hits para ~56% das requisições. O resultado foi detectado empiricamente: Java reportou mediana de 3,44ms — fisicamente impossível com mock de 200-500ms.

```
Primeira rodada (Redis poluído):
  Go:   341 RPS | latência 352ms  ← correto
  Java: 603 RPS | latência 3.4ms  ← INVÁLIDO (cache hits espúrios)
```

### 3.2 A solução implementada

```bash
# Antes de CADA execução individual do k6:
docker exec tcc-redis redis-cli FLUSHALL
```

Este comando foi incorporado ao `run_benchmarks.sh` e executado automaticamente antes de cada um dos 18 runs da bateria completa. Nenhum request é servido do cache — **todo request percorre o fluxo completo:**

```
Redis GET (miss) → PostgreSQL INSERT → HTTP externo (200–500ms) → PostgreSQL UPDATE → Redis SET → resposta 201
```

### 3.3 Por que não usar keys UUID em vez de VU+ITER?

UUID aleatório garantiria unicidade absoluta sem necessidade de FLUSHALL. A escolha de `k6-vu${__VU}-iter${__ITER}` foi **intencional**:

1. **Reprodutibilidade**: com UUID, dois runs do mesmo cenário geram cargas ligeiramente diferentes (distribuição aleatória diferente). Com VU+ITER, dois runs são **byte-a-byte idênticos em estrutura**, facilitando comparação direta.
2. **Debuggabilidade**: em caso de erro, é possível identificar exatamente qual VU e iteração falhou.
3. **O protocolo FLUSHALL resolve o problema** de contaminação de forma explícita e documentada.

---

## 4. Validade Estatística — 3 Rodadas com Média e Desvio Padrão

### 4.1 Por que 3 rodadas?

Uma única medição de benchmark pode ser afetada por:
- Variações de CPU scheduling do host
- Garbage Collection ocorrendo durante a medição
- Jitter de rede (mesmo em localhost via Docker)
- Paginação de memória do SO

Três rodadas independentes com Redis FLUSHALL entre cada uma permitem calcular **média ± desvio padrão** e **Coeficiente de Variação (CV)**:

```
CV% = (desvio padrão / média) × 100
```

**Interpretação do CV:**
- CV < 1%: excelente reprodutibilidade (resultado confiável)
- CV 1–5%: reprodutibilidade aceitável
- CV > 5%: alta variância (resultado questionável)

**Resultados obtidos:**

| Cenário | Métrica | Java CV% | Go CV% |
| :--- | :--- | ---: | ---: |
| Stress | Latência Média | 0.11% | 0.14% |
| Stress | Total Requests | 0.10% | 0.12% |
| Spike | Latência Média | 1.82% | 0.34% |

Todos os CVs abaixo de 2% — **qualidade científica publicável**.

### 4.2 Por que não mais rodadas?

Com CV < 0.2%, 3 rodadas são estatisticamente suficientes para este tipo de benchmark determinístico. O erro padrão da média (SEM = σ/√n) com n=3 e σ~0.4ms resulta em SEM~0.23ms — intervalo de confiança de 95% de ~±0.46ms para latência de ~352ms (erro relativo < 0.1%). Rodadas adicionais agregariam ruído de tempo (JVM warm-up diferente) sem reduzir a incerteza de forma significativa.

---

## 5. Simetria das Configurações

Um requisito fundamental para comparação justa é que **todas as variáveis sejam idênticas exceto o modelo de concorrência**.

### 5.1 Variáveis controladas

| Variável | Java | Go | Justificativa |
| :--- | :--- | :--- | :--- |
| **Pool DB** | HikariCP: 200 (padrão) / 500 (experimento) | pgxpool: 200 / 500 | Mesmos limites para não favorecer nenhum |
| **Timeout HTTP** | 5s (connect + read) | 5s (net/http.Client) | Mesma tolerância a lentidão |
| **TTL Redis** | 24h | 24h | Mesma janela de idempotência |
| **Porta** | 8081 | 8082 | Separadas para testes paralelos futuros |
| **Endpoint** | `POST /payments` | `POST /payments` | Idêntico |
| **Payload** | `{amount, cardNumber}` | `{amount, cardNumber}` | Idêntico |
| **GC** | ZGC Generacional | Go GC concorrente | Ambos sub-milissegundo |
| **Validação de domínio** | Compact constructor | `Validate()` method | Equivalentes |
| **Logging** | logstash-logback JSON | slog JSON | Equivalentes |
| **Graceful shutdown** | 30s | 30s | Equivalentes |

### 5.2 Métricas Prometheus simétricas

Ambos os backends expõem o mesmo histograma:

```
http_server_requests_seconds
  labels: method, uri, status, outcome
  buckets: [.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5]
```

Java via Micrometer, Go via prometheus/client_golang. Labels idênticos permitem queries PromQL idênticas no Grafana — sem ambiguidade na comparação.

---

## 6. Infraestrutura do Mock Externo

### 6.1 Por que um mock e não um serviço real?

O experimento mede **o modelo de concorrência**, não a performance de serviços externos. Um serviço real introduziria variáveis incontroláveis (latência de rede, carga do servidor externo, rate limiting). O mock garante **condições idênticas e reproduzíveis** para todos os testes.

### 6.2 Latência uniforme 200–500ms

```go
// mock-external-api/main.go
latency := minLatency + rng.Int63n(maxLatency-minLatency)
time.Sleep(time.Duration(latency) * time.Millisecond)
```

O intervalo 200–500ms foi escolhido para simular uma API de processadora de cartão real (Visa/Mastercard tipicamente respondem em 150–400ms). A distribuição uniforme (não normal) garante que ambos os backends recebam distribuições de latência estatisticamente idênticas ao longo de milhares de requests.

**Consequência importante:** Como ~350ms do tempo de cada request é I/O puro aguardando o mock, o benchmark é **I/O-bound por design** — exatamente o workload que maximiza a diferença entre modelos de concorrência (thread-per-request bloqueante vs não-bloqueante).

### 6.3 RNG por request (sem mutex)

```go
// Por request, não global:
rng := rand.New(rand.NewSource(time.Now().UnixNano()))
```

O mock usa um RNG por request para evitar contention de mutex sob alta concorrência. Com 500 VUs simultâneos, um RNG global seria um gargalo — todas as goroutines competiriam pelo lock. Esta decisão garante que o mock não introduza serialização artificial.

---

## 7. Fluxo Completo de uma Requisição

```
k6 VU (goroutine no gerador)
    │
    │ POST /payments
    │ X-Idempotency-Key: k6-vu{N}-iter{I}
    │ Content-Type: application/json
    ▼
[Backend Java | Backend Go]
    │
    ├─ 1. Redis GET k6-vu{N}-iter{I}
    │       → MISS (Redis limpo por FLUSHALL)
    │
    ├─ 2. Validação de domínio
    │       → amount > 0, cardNumber 13-19 chars
    │
    ├─ 3. PostgreSQL INSERT payments (status=PENDING)
    │       → UUID gerado pelo backend
    │
    ├─ 4. HTTP POST mock-api:8080/process-payment
    │       → aguarda 200–500ms (I/O blocking point)
    │       → Virtual Thread / Goroutine suspende aqui
    │
    ├─ 5. PostgreSQL UPDATE payments SET status=APPROVED|REJECTED
    │
    ├─ 6. Redis SET k6-vu{N}-iter{I} = resultado (TTL 24h)
    │
    └─ 7. HTTP 201 Created + {id, status, ...}
    │
    ▼
k6 VU: check(status==201, body.id exists) → errorRate.add()
```

**Ponto crítico de concorrência:** O passo 4 é onde Virtual Threads e Goroutines divergem em comportamento. Ambos suspendem a execução da unidade de concorrência enquanto aguardam a resposta HTTP — mas o mecanismo é diferente:
- **Virtual Thread:** suspende no carrier thread via Continuation, liberando a OS thread para outro VT
- **Goroutine:** suspende no scheduler Go via syscall netpoller, liberando a M thread para outra goroutine

Em ambos os casos, o resultado é não-bloqueio da OS thread — por isso o comportamento é equivalente para I/O-bound.

---

## 8. Coleta de Memória RAM

### 8.1 Método

Durante cada execução k6, o script `run_benchmarks.sh` inicia em paralelo:

```bash
docker stats --format "{{.MemUsage}}" tcc-backend-java >> java_baseline_round1.mem &
```

O `docker stats` sem `--no-stream` emite uma linha por segundo com o uso atual de memória do container no formato `256MiB / 8GiB`. O processo é terminado após o k6 finalizar.

### 8.2 O que docker stats mede

`docker stats` reporta o **RSS (Resident Set Size)** do container — toda a memória física alocada pelo processo, incluindo:
- **Java:** heap + non-heap (metaspace, code cache) + stacks de threads + overhead da JVM
- **Go:** heap + stacks de goroutines + runtime Go + código do binário

Esta é a métrica mais honesta para comparar footprint real em produção: é o que o sistema operacional vê como custo de rodar aquele processo.

### 8.3 Limitações

- Docker stats reporta com granularidade de ~1s — captura a tendência, não picos de GC sub-segundo
- Em ambientes containerizados, o cgroup de memória pode diferir levemente do RSS do processo host
- A variância de RAM do Java no baseline (±208MB) reflete aquecimento da JVM no primeiro cenário — após aquecimento, estabiliza em ±1MB

### 8.4 Parse e análise

O `analyze_results.py` processa os arquivos `.mem` removendo sequências de escape ANSI (que o docker stats emite em modo streaming), converte unidades (GiB → MB) e calcula pico e média por rodada, reportando média ± desvio padrão entre as 3 rodadas.

---

## 9. Decisões de Design que Afetam os Resultados

### 9.1 Por que não testar throughput máximo (RPS puro)?

Um benchmark de throughput máximo configuraria cada VU para enviar requests sem `sleep` e escalaria VUs até o sistema saturar completamente. Esta abordagem mede a capacidade bruta de processamento.

**Decisão:** Medir latência percentílica (p50, p95, p99) sob carga controlada é mais relevante para workloads de produção. Em sistemas reais, o objetivo é manter latência abaixo de SLAs (ex: p95 < 500ms) com carga variável — não maximizar RPS independente de latência.

### 9.2 Por que `sleep(0.1)` e não zero?

Sem sleep, cada VU envia requests em pipeline máximo. Com 200 VUs e latência de 350ms, isso geraria ~57.000 requests/s teórico — muito acima da capacidade do mock. O sistema colapsaria por saturação do gerador, não do backend.

O `sleep(0.1)` calibra a carga para ~340 RPS no stress — carga alta mas sustentável, que revela comportamento estável do scheduler sem saturar a infraestrutura de suporte (PostgreSQL, Redis, mock).

### 9.3 Por que PostgreSQL e não banco em memória?

Banco em memória (H2, SQLite) eliminaria o I/O de disco da equação. A decisão de usar PostgreSQL real foi intencional: o fluxo de pagamento em produção sempre usa banco transacional com persistência. Simular com H2 tornaria o benchmark artificialmente favorável a ambos os backends e desconectado da realidade operacional.

---

## 10. Limitações do Estudo

### 10.1 Ambiente local vs cloud

Os benchmarks no Apple M4/Colima rodam sobre uma camada de virtualização (Colima VZ). Em produção (GCP), os containers rodam em metal nu. Os resultados relativos (Go vs Java) devem ser preservados, mas os valores absolutos (RPS, latência) serão diferentes.

### 10.2 Ambiente compartilhado

Todos os containers (backends, PostgreSQL, Redis, mock) rodam no mesmo host com 4 vCPUs / 8GB. Em produção, cada serviço teria recursos dedicados. A principal implicação: **Java e Go competem pelos mesmos 4 vCPUs** — o impacto do GC Java (ZGC) em outros processos é minimamente observável, mas presente.

### 10.3 Modelo de carga sintética

Os 500 VUs do spike representam 500 usuários simultâneos fazendo exatamente 1 request cada. Na prática, usuários reais têm padrões de acesso muito mais variados (think time longo, bursts curtos, retries). O modelo de carga sintética maximiza a pressão sobre o modelo de concorrência, mas pode superestimar diferenças que seriam suavizadas com carga real.

### 10.4 Um único endpoint

O experimento testa exclusivamente `POST /payments` — um endpoint de escrita com I/O intenso. Endpoints de leitura (GET), operações em batch ou workloads CPU-bound podem apresentar resultados diferentes. A conclusão de equivalência entre VT e Goroutines é válida **para workloads I/O-bound**, que é o caso de uso mais comum em sistemas de pagamento.

### 10.5 Versões experimentais

Go 1.25 e Java 25 são versões recentes (Go 1.25 / Java 25 LTS). Comportamentos de scheduler podem mudar em versões futuras.

---

## 11. Protocolo de Reprodução

Para replicar completamente os resultados deste estudo:

```bash
# 1. Pré-requisitos
brew install k6 docker colima

# 2. Iniciar infraestrutura
colima start --cpu 4 --memory 8
docker compose -f docker-compose.yml \
               -f docker-compose.pool-experiment.yml \
               up -d --build

# 3. Aguardar backends (30s)
sleep 30
curl http://localhost:8081/actuator/health
curl http://localhost:8082/health

# 4. Executar bateria completa (3 rodadas × 3 cenários × 2 backends)
bash scripts/benchmarks/run_benchmarks.sh --rounds 3

# 5. Gerar relatório estatístico
RESULTS_DIR=$(ls -td results/runs/*/ | head -1)
python3 scripts/benchmarks/analyze_results.py "$RESULTS_DIR" --format markdown
```

**Tempo estimado:** 35–45 minutos para a bateria completa.

---

*Este documento descreve a metodologia completa do benchmark para fins de reprodutibilidade científica e defesa acadêmica.*
*Versão do experimento: pool=500 (docker-compose.pool-experiment.yml), 3 rodadas, Apple M4 ARM64.*
