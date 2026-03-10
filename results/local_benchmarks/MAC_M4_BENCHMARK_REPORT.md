# Relatório de Benchmark: Java 25 (VT) vs Go 1.25 (Goroutines)
## Ambiente: Apple M4 — Colima/ARM64 Nativo

**Autor:** Felippe Gustavo de Souza e Silva
**Instituição:** USP ESALQ — Engenharia de Software
**Orientador:** Prof. Marcos Jardel Henriques
**Data:** 10 de Março de 2026
**Ambiente:** Apple M4 (darwin/arm64) — Colima (VM VZ, Linux/arm64 nativo)
**Ferramenta:** k6 v1.6.1 (go1.26.0, darwin/arm64)

---

## ⚠️ Nota Metodológica — Falha Detectada e Corrigida

Durante a primeira rodada de testes, uma falha crítica de isolamento foi identificada:

**Problema:** O `X-Idempotency-Key` gerado pelo k6 usa `k6-vu${__VU}-iter${__ITER}`, onde `__ITER` reseta a zero a cada nova execução do `k6 run`. Como Go e Java foram testados sequencialmente no **mesmo Redis**, o Java (rodando segundo) encontrava as chaves do Go já armazenadas no Redis, obtendo cache hits espúrios para ~56% das requisições. Isso inflou artificialmente o throughput e a latência média do Java.

**Sintoma observado:** Java stress reportava 603 RPS e mediana de 3.44ms — fisicamente impossível dado que o mock externo impõe 200–500ms de latência mínima por request.

**Correção aplicada:** Redis foi limpo via `FLUSHALL` antes de **cada** teste individual. Os resultados abaixo refletem dados com isolamento completo.

**Lição para replicabilidade:** Antes de qualquer rodada de benchmark, executar:
```bash
docker exec tcc-redis redis-cli FLUSHALL
```

---

## 🖥️ Configuração do Ambiente

| Componente | Especificação |
| :--- | :--- |
| **Hardware** | Apple M4 (ARM64) |
| **Runtime de Containers** | Colima (VZ driver) — Linux/arm64 nativo, sem emulação x86 |
| **CPUs alocadas** | 4 vCPUs |
| **Memória alocada** | 8 GB |
| **PostgreSQL** | 16-alpine — `max_connections=300` |
| **Pool de conexões DB** | HikariCP: 200 (Java) / pgxpool MaxConns: 200 (Go) |
| **Redis** | 7-alpine — isolado entre cada teste via FLUSHALL |
| **Mock API** | Go 1.25-alpine — latência simulada: 200–500ms (uniforme) |
| **k6** | v1.6.1 — darwin/arm64 |

---

## 🏗️ Infraestrutura do Teste

```
k6 (darwin/arm64)
    │
    ├──▶ backend-java:8081  (Spring Boot 3.5 + Virtual Threads + ZGC Generacional)
    │        ├──▶ Redis FLUSHALL antes do teste
    │        ├──▶ PostgreSQL (persist PENDING → APPROVED/REJECTED)
    │        └──▶ mock-api:8080 (I/O externo: 200–500ms)
    │
    └──▶ backend-go:8082    (Gin + Goroutines nativas + pgxpool)
             ├──▶ Redis FLUSHALL antes do teste
             ├──▶ PostgreSQL (persist PENDING → APPROVED/REJECTED)
             └──▶ mock-api:8080 (I/O externo: 200–500ms)
```

**Chave de idempotência:** `k6-vu{VU}-iter{ITER}` — única por request dentro de uma execução. Redis limpo antes de cada `k6 run` garante que **nenhuma** requisição seja servida do cache. Todo request percorre o fluxo completo: Redis GET → DB INSERT → HTTP externo (200–500ms) → DB UPDATE → Redis SET.

---

## 📊 Cenário 1 — BASELINE (20 VUs, 2 minutos)

> Controle científico: carga baixa onde ambos os modelos devem comportar-se de forma equivalente.

| Métrica | Go 1.25 | Java 25 (VT) | Delta |
| :--- | ---: | ---: | :--- |
| **Throughput (RPS)** | 24.4 | **24.5** | Empate (+0.4%) |
| **Iterações totais** | 2.943 | **2.944** | Empate |
| **Latência média** | 354.3ms | **353.6ms** | Empate (−0.2%) |
| **Mediana (p50)** | 355.2ms | **352.1ms** | Empate |
| **p90** | 471.0ms | **476.2ms** | Empate |
| **p95** | 487.5ms | **492.0ms** | Empate |
| **Máximo** | **527ms** | 509ms | Java −3.5% |
| **Taxa de Erro** | **0.00%** | **0.00%** | Empate |

### Análise do Baseline
Sob 20 VUs com Redis isolado, os dois runtimes são **estatisticamente indistinguíveis**. Throughput, latência média, mediana e percentis são equivalentes dentro da margem de ruído de medição. Isso confirma o controle científico: abaixo do ponto de saturação, o modelo de concorrência não faz diferença — ambos são igualmente eficientes para I/O-bound.

---

## 📊 Cenário 2 — STRESS (200 VUs, ~1m50s)

> Cenário principal: saturação progressiva para revelar diferenças entre Virtual Threads e Goroutines.

| Métrica | Go 1.25 | Java 25 (VT) | Delta |
| :--- | ---: | ---: | :--- |
| **Throughput (RPS)** | **341.2** | 339.9 | Empate (−0.4%) |
| **Iterações totais** | **37.674** | 37.486 | Empate |
| **Latência média** | **352ms** | 354ms | Empate (+0.6%) |
| **Mediana (p50)** | **351.9ms** | 353.7ms | Empate |
| **p90** | **471.6ms** | 474.7ms | Empate |
| **p95** | **486.6ms** | 489.9ms | Empate |
| **Máximo** | **547ms** | 639ms | Go −14.4% |
| **Taxa de Erro** | **0.00%** | **0.00%** | Empate |

### Análise do Stress
Com isolamento correto, o resultado é surpreendentemente claro: **empate total em throughput e latência média**. Go 341 RPS vs Java 339 RPS é diferença estatística de ruído. A única diferença mensurável é no máximo: Go 547ms vs Java 639ms — Go apresenta menor jitter no pior caso individual, possivelmente pela ausência de pausas de GC sob pressão de heap.

---

## 📊 Cenário 3 — SPIKE (500 VUs, 1 minuto)

> Rajada abrupta: mede elasticidade, recuperação e comportamento sob pressão extrema.

| Métrica | Go 1.25 | Java 25 (VT) | Delta |
| :--- | ---: | ---: | :--- |
| **Throughput (RPS)** | **650.3** | 359.5 | **Go +80.9%** |
| **Iterações totais** | **39.272** | 21.646 | **Go +81.4%** |
| **Latência média** | **352ms** | 722ms | **Go −51.3%** |
| **Mediana (p50)** | **352ms** | 750ms | **Go −53.1%** |
| **p90** | **473ms** | 897ms | **Go −47.3%** |
| **p95** | **488ms** | 916ms | **Go −46.7%** |
| **Máximo** | **871ms** | 1.67s | **Go −47.9%** |
| **Taxa de Erro** | 0.14% (56/39272) | **0.00%** | Java ligeiramente melhor |

### Análise do Spike
Sob rajada abrupta de 500 VUs, **Go domina amplamente**. O Go manteve throughput de 650 RPS e latência estável (~352ms), enquanto o Java colapsou para 359 RPS com latência média de 722ms — o dobro do tempo de resposta.

**Por que o Java degrada no spike?**
Com 500 VUs concorrentes e pool HikariCP limitado a 200 conexões, 300 Virtual Threads ficam em fila aguardando uma conexão disponível. Esse enfileiramento aumenta a latência de forma cumulativa. O ZGC também sofre sob pressão de heap com 500 threads simultâneas, introduzindo pausas adicionais.

**Por que o Go é resiliente?**
O pgxpool gerencia as 200 conexões de forma eficiente e o scheduler M:N do Go distribui goroutines uniformemente entre as OS threads. Goroutines aguardando conexão DB consomem ~2KB de stack cada — o Go pode manter 500 goroutines em espera com overhead de ~1MB, enquanto no Java o overhead da fila virtual é maior.

**Nota:** O threshold do spike era `errors < 5%`. O Go ficou em 0.14% (56 erros em 39.272 requests) — dentro do limite científico aceitável. Esses erros ocorrem no pico de ramp-up (5s para 500 VUs), quando conexões TCP ainda estão sendo estabelecidas.

---

## 🔬 Visão Consolidada — Resultados Corrigidos

| Cenário | VUs | Métrica | Go 1.25 | Java 25 (VT) | Vencedor |
| :--- | ---: | :--- | ---: | ---: | :--- |
| Baseline | 20 | RPS | 24.4 | 24.5 | **Empate** |
| Baseline | 20 | Média | 354ms | 353ms | **Empate** |
| Baseline | 20 | p95 | 487ms | 492ms | **Empate** |
| Stress | 200 | RPS | 341 | 339 | **Empate** |
| Stress | 200 | Média | 352ms | 354ms | **Empate** |
| Stress | 200 | Máximo | **547ms** | 639ms | Go |
| Spike | 500 | RPS | **650** | 359 | **Go +81%** |
| Spike | 500 | Média | **352ms** | 722ms | **Go** |
| Spike | 500 | p95 | **488ms** | 916ms | **Go** |
| Spike | 500 | Erros | 0.14% | **0.00%** | Java |

---

## 🧠 Conclusões Científicas — Versão Corrigida

### 1. Equivalência sob carga moderada (Principal Achado)
Com metodologia correta, Java 25 Virtual Threads e Go 1.25 Goroutines são **estatisticamente equivalentes** no baseline (20 VUs) e no stress (200 VUs). Esta é a validação central da tese: o Project Loom eliminou a diferença histórica de performance entre Java e Go para workloads I/O-bound. Ambos os modelos de concorrência são igualmente eficientes até o ponto de saturação do pool de conexões.

### 2. Go superior sob pressão extrema de spike
Acima de 200 VUs concorrentes, o Go demonstra resiliência superior (+81% throughput, −51% latência). O fator limitante no Java é o pool HikariCP (200 conexões para 500 VUs), que cria fila de espera e infla a latência cumulativamente. O Go lida melhor com contenção de recursos por design do scheduler M:N e menor overhead por goroutine em espera.

### 3. Implicação direta: dimensionamento de pool
O resultado do spike indica que a superioridade do Go sob carga extrema é parcialmente atribuível ao dimensionamento do pool (200 conexões para 500 VUs = 60% das threads em espera). Um teste com pool proporcional ao número de VUs (ex: 500 conexões para 500 VUs) poderia equalizar os resultados. **Este é o próximo experimento recomendado para GCP.**

### 4. Estabilidade de erro
Java 0.00% de erros em todos os cenários vs Go 0.14% no spike. Ambos dentro do limite científico (<5%), mas indica que o backpressure do HikariCP no Java é mais gracioso (enfileira) enquanto o Go pode rejeitar conexões TCP no ramp-up abrupto.

### 5. Implicações para escolha tecnológica
| Critério | Recomendação |
| :--- | :--- |
| **Carga previsível e moderada (até ~200 VUs)** | Indiferente — performance idêntica |
| **Spike / carga imprevisível** | Go — scheduler mais resiliente sob contenção |
| **Ecossistema e maturidade** | Java — Spring, JPA, observabilidade nativa |
| **Footprint de memória** | Go — a validar no GCP |
| **Simplicidade operacional** | Go — binário único, sem JVM |

---

## 🚀 Próximos Passos — Validação em GCP

1. **Replicar com `FLUSHALL` antes de cada teste** — protocolo já documentado
2. **Testar com pool proporcional ao VU count** — ex: 500 conexões no spike — para isolar se a diferença é do scheduler ou do pool
3. **3 rodadas por cenário** — média estatística para eliminar jitter de rede
4. **Métricas de memória e CPU** via Grafana — comparar footprint real de JVM vs Go runtime
5. **Instâncias dedicadas por serviço** — PostgreSQL, Redis e backends em VMs separadas

---

## ❌ Resultados Invalidados (Primeira Rodada — Redis Poluído)

Os resultados abaixo são mantidos por transparência metodológica, mas **não devem ser usados como dados científicos**. Eles demonstram como a contaminação de cache pode criar uma falsa superioridade do Java:

| Cenário | Métrica | Go (correto) | Java (com cache hits espúrios) | Inflação |
| :--- | :--- | ---: | ---: | ---: |
| Stress | RPS | 341 | 603 🚨 | +77% falso |
| Stress | Mediana | 351ms | 3.4ms 🚨 | −99% falso |
| Stress | Média | 352ms | 154ms 🚨 | −56% falso |

---

*Documento gerado para consolidação da pesquisa científica de TCC — USP ESALQ 2025.*
*Resultados reproduzíveis via `docker exec tcc-redis redis-cli FLUSHALL && k6 run ...`*
