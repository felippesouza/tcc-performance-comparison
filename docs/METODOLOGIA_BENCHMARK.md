# Metodologia de Benchmark — Detalhamento Científico
## Estudo Comparativo de Modelos de Concorrência: Java 25 vs Go 1.25 vs Quarkus Native

**Autor:** Felippe Gustavo de Souza e Silva
**Instituição:** USP ESALQ — Engenharia de Software
**Orientador:** Prof. Marcos Jardel Henriques
**Versão:** 2.0 — Março de 2026

---

## Sumário

1. [Motivação e Pergunta Científica](#1-motivação-e-pergunta-científica)
2. [Por que três backends?](#2-por-que-três-backends)
3. [Ferramenta de Carga: k6](#3-ferramenta-de-carga-k6)
4. [Desenho dos Cenários](#4-desenho-dos-cenários)
5. [Protocolo de Isolamento Redis](#5-protocolo-de-isolamento-redis)
6. [Validade Estatística](#6-validade-estatística)
7. [Simetria das Configurações](#7-simetria-das-configurações)
8. [Descoberta e Correção das Configurações do Quarkus](#8-descoberta-e-correção-das-configurações-do-quarkus)
9. [JEP 491 e o Achado do HikariCP](#9-jep-491-e-o-achado-do-hikaricp)
10. [Experimento de Controle — pool=500](#10-experimento-de-controle--pool500)
11. [Infraestrutura do Mock Externo](#11-infraestrutura-do-mock-externo)
12. [Fluxo Completo de uma Requisição](#12-fluxo-completo-de-uma-requisição)
13. [Coleta de Memória RAM](#13-coleta-de-memória-ram)
14. [Decisões de Design](#14-decisões-de-design)
15. [Limitações do Estudo](#15-limitações-do-estudo)
16. [Protocolo de Reprodução](#16-protocolo-de-reprodução)

---

## 1. Motivação e Pergunta Científica

O crescimento de sistemas de alta concorrência em I/O-bound (APIs de pagamento, gateways, microsserviços) colocou em evidência dois modelos modernos de concorrência M:N — **Virtual Threads** (Java, Project Loom, JEP 444) e **Goroutines** (Go runtime). A questão central deste experimento é:

> *Dado o mesmo workload I/O-bound, os modelos M:N de Java e Go entregam performance equivalente? E qual o custo real de cada runtime em termos de memória e throughput?*

O cenário escolhido é um **Gateway de Pagamentos** — sistema canônico para I/O-bound: cada requisição envolve leitura do cache, escrita em banco, chamada a API externa (~350ms) e nova escrita em banco. É exatamente o workload para o qual Virtual Threads e Goroutines foram projetados.

A hipótese principal (H0) é:

> *Sob workload I/O-bound com pools corretamente configurados, Virtual Threads (Java) e Goroutines (Go) entregam throughput e latência estatisticamente equivalentes.*

---

## 2. Por que três backends?

A comparação binária Java vs Go deixa uma ambiguidade não resolvível sem um terceiro ponto de dados:

> *A diferença de RAM entre Java (~800MB) e Go (~35MB) vem do modelo de concorrência ou da JVM?*

### 2.1 A tríade de isolamento

O **Quarkus Native** (GraalVM Mandrel AOT) foi introduzido como terceiro backend para isolar variáveis:

| Comparação | Variável isolada | O que prova |
|:---|:---|:---|
| **Java JVM vs Quarkus Native** | Runtime (JVM vs nativo), mesmo código Java | O custo de RAM é da JVM, não da linguagem |
| **Go vs Quarkus Native** | Modelo de concorrência (M:N vs 1:1), ambos nativos | Custo puro do modelo de threading |
| **Java JVM vs Go** | Runtime + modelo (JVM+VT vs nativo+goroutines) | Comparação direta dos dois M:N |

### 2.2 O que o Quarkus representa

- **Runtime:** GraalVM Mandrel Native Image — binário nativo sem JVM, sem JIT, sem GC heap tradicional
- **Modelo de concorrência:** OS Threads 1:1 bloqueantes — cada requisição HTTP ocupa uma OS thread enquanto aguarda I/O
- **Significado científico:** É o modelo "tradicional" anterior ao Loom e às goroutines, servindo como baseline de contraste
- **Linguagem:** Java — permite comparação direta com o backend Java no nível de código (mesma lógica, mesmo Clean Architecture)

### 2.3 Achado emergente do Quarkus

O resultado mais rico do experimento foi inesperado: com pools corretamente configurados (ver Seção 8), **OS threads empatam com M:N em throughput** até o cenário de stress (200 VUs). A diferença real sob carga extrema (spike 500 VUs) é **RAM**, não throughput:

- Go: **78 MB**, 655 RPS
- Quarkus: **464 MB**, 646 RPS

600 OS threads × ~512 KB de stack = ~300 MB de RAM apenas para os stacks. Goroutines com ~2 KB cada = ~1 MB para 500 goroutines. **Mesmo throughput, 6× mais RAM** — esse é o custo real do modelo 1:1.

---

## 3. Ferramenta de Carga: k6

### 3.1 Por que k6 e não JMeter, Gatling ou Locust?

| Critério | k6 | JMeter | Gatling | Locust |
|:---|:---|:---|:---|:---|
| **Modelo de concorrência** | Goroutines (Go) | Threads Java | Coroutines (Akka) | Greenlets (Python) |
| **Overhead por VU** | ~2 KB | ~1 MB | ~200 KB | ~100 KB |
| **500 VUs — RAM do gerador** | < 10 MB | ~500 MB | ~100 MB | ~50 MB |
| **Scripting** | JavaScript ES2015+ | XML/GUI | Scala DSL | Python |
| **Output estruturado** | NDJSON, InfluxDB, CSV | XML, CSV | HTML report | CSV |
| **Reprodutibilidade** | Alta (código versionável) | Baixa (GUI state) | Alta | Alta |

**Decisão:** k6 garante que o gerador de carga não se torne o gargalo do experimento. Com JMeter, 500 threads do gerador consumiriam ~500 MB — competindo por recursos com os backends sendo testados na mesma máquina. k6 com 500 VUs consome < 10 MB.

### 3.2 Modelo de VU (Virtual User)

Cada VU é uma goroutine que executa em loop contínuo:

```
VU lifecycle:
  setup() → [default function loop] → teardown()
                   ↕ repete até fim do teste
```

Cada iteração:
1. Monta payload JSON com `amount` aleatório
2. Gera `X-Idempotency-Key` única: `k6-vu{N}-iter{I}`
3. Envia `POST /payments` ao backend-alvo
4. Valida resposta (`status == 201` + campo `id` presente)
5. Registra métricas (latência, erros)
6. Dorme 100ms (`sleep(0.1)`)
7. Repete

O `sleep(0.1)` é calibrado para gerar ~340 RPS com 200 VUs — carga sustentável que revela o comportamento do scheduler sem saturar os serviços de suporte.

### 3.3 Relação VUs → RPS (Lei de Little)

A **Lei de Little** (Little, 1961) estabelece:

```
N = λ × W

onde:
  N = número médio de requisições em-flight (≈ VUs ativos)
  λ = taxa de chegada (RPS)
  W = tempo médio de serviço (latência média + sleep)
```

Para o cenário stress (200 VUs, latência ~352ms):
```
λ = N / W = 200 / (0.352 + 0.100) = 200 / 0.452 ≈ 442 req/s teórico
Observado: ~342 RPS
Delta: overhead TCP, handshake Redis, variância do mock (200–500ms)
```

Para o cenário spike (500 VUs, latência ~354ms — Go/Quarkus):
```
λ = 500 / (0.354 + 0.100) = 500 / 0.454 ≈ 1101 req/s teórico
Observado: ~655 RPS (Go)
Delta: pool de conexões limita a ~200 conexões simultâneas ao DB
```

A lei de Little confirma que o sistema opera como esperado — o gap entre teórico e observado é explicado pelas restrições de infraestrutura (pool DB), não por bugs ou anomalias.

---

## 4. Desenho dos Cenários

### 4.1 Filosofia geral

Três cenários respondem perguntas científicas distintas:

```
Pergunta 1: os três runtimes são equivalentes em condições normais?
  → Baseline (20 VUs) — grupo controle

Pergunta 2: o modelo de threading faz diferença sob carga sustentada?
  → Stress (200 VUs) — cenário principal de comparação

Pergunta 3: qual runtime é mais resiliente a picos abruptos?
  → Spike (500 VUs) — teste de elasticidade extrema
```

### 4.2 Cenário 1 — Baseline (Controle Científico)

```javascript
stages: [
  { duration: '30s', target: 10 },   // rampa suave
  { duration: '60s', target: 20 },   // 20 VUs sustentados (janela de coleta)
  { duration: '30s', target: 0 },    // cool-down
]
thresholds: { http_req_duration: ['p95<1000'], error_rate: ['rate<0.01'] }
```

**Racional científico:** 20 VUs com mock de ~350ms gera ~44 RPS — muito abaixo da capacidade de qualquer runtime moderno. **Os três sistemas devem se comportar identicamente.** Se divergirem, indica problema de configuração ou medição. É o grupo controle que valida a simetria do experimento antes de escalar a carga.

**Resultado esperado e obtido:** Todos os três empataram em latência (~355ms) e throughput (~2.930 requests). A única diferença foi RAM: Java 789 MB (JVM), Quarkus 56 MB (nativo), Go 32 MB (nativo). Isso confirma que a diferença de RAM é do runtime, não da carga.

### 4.3 Cenário 2 — Stress (Principal)

```javascript
stages: [
  { duration: '10s', target: 50 },   // warm-up: JVM aquece JIT
  { duration: '30s', target: 200 },  // ramp-up progressivo
  { duration: '60s', target: 200 },  // sustentação: janela principal de coleta
  { duration: '10s', target: 0 },    // cool-down gracioso
]
thresholds: { http_req_duration: ['p95<800'], error_rate: ['rate<0.01'] }
```

**Por que 200 VUs?** O pool de conexões de todos os backends foi configurado em 200 conexões (HikariCP, pgxpool, Agroal). Com 200 VUs, cada VU potencialmente precisa de 1 conexão simultânea — o sistema opera no limite teórico do pool sem entrar em contenção excessiva. É o ponto de máxima carga sustentável.

**Por que warm-up de 10s com 50 VUs?** A JVM precisa de carga para acionar o JIT compiler (C1/C2). Sem warm-up, os primeiros segundos mediriam código interpretado — não representativo do steady-state de produção. Go e Quarkus Native não precisam de JIT (código já compilado AOT/nativo), mas o warm-up também beneficia o aquecimento do pool de conexões do PostgreSQL.

**Resultado obtido:** Todos os três empataram completamente — ~342 RPS, ~353ms latência, 0% erros. Isso confirma H0: com pools corretos, M:N (VT e goroutines) e 1:1 (OS threads) são equivalentes para I/O-bound.

### 4.4 Cenário 3 — Spike (Elasticidade)

```javascript
stages: [
  { duration: '10s', target: 10 },   // estado estável inicial
  { duration: '5s',  target: 500 },  // spike abrupto: 10→500 VUs em 5 segundos
  { duration: '30s', target: 500 },  // sustentação do pico
  { duration: '5s',  target: 10 },   // queda abrupta
  { duration: '10s', target: 0 },    // cool-down
]
thresholds: { http_req_duration: ['p95<2000'], error_rate: ['rate<0.05'] }
```

**Por que 500 VUs com ramp de 5s?** Simula tráfego viral ou falha de balanceador de carga — 25× o tráfego normal em segundos. O ramp abrupto revela a **elasticidade do modelo de concorrência**: goroutines e Virtual Threads são provisionadas em microssegundos; OS threads requerem syscall de criação (~10µs cada).

**Por que threshold relaxado (5%)?** O ramp de 5s para 500 VUs inevitavelmente gera alguns erros de estabelecimento de conexão TCP. O threshold de 5% define o limite científico aceitável de degradação graceful.

**Resultado obtido e interpretado:** Go (655 RPS, 78 MB) e Quarkus (646 RPS, 464 MB) empatam em throughput; Java degrada para 362 RPS. A causa da degradação do Java é detalhada na Seção 9.

---

## 5. Protocolo de Isolamento Redis

### 5.1 O problema descoberto

O backend implementa **idempotência via Redis**: `X-Idempotency-Key` é armazenada por 24h. Cache hit retorna resposta sem chamar o banco ou a API externa.

O k6 gera keys como `k6-vu${__VU}-iter${__ITER}`. O `__ITER` reseta para `0` a cada novo processo `k6 run`.

**Consequência:** Se Go for testado primeiro e Java depois, o Java encontra as keys do Go já no Redis e retorna cache hits para ~56% das requisições. Detectado empiricamente: Java reportou mediana de 3,44ms — fisicamente impossível com mock de 200–500ms.

```
Primeira rodada sem FLUSHALL (resultado inválido):
  Go:   341 RPS | latência 352ms  ← correto (sem cache hits)
  Java: 603 RPS | latência 3.4ms  ← INVÁLIDO (cache hits espúrios)
```

### 5.2 Solução implementada

```bash
# Antes de CADA execução individual do k6:
docker exec tcc-redis redis-cli FLUSHALL
```

Incorporado ao `run_benchmarks.sh` — executado automaticamente antes de cada um dos 27 runs (3 backends × 3 cenários × 3 rodadas). Garante que todo request percorra o fluxo completo:

```
Redis GET (miss) → PostgreSQL INSERT → HTTP externo (~350ms) → PostgreSQL UPDATE → Redis SET → 201
```

### 5.3 Por que não UUID em vez de VU+ITER?

UUID aleatório garantiria unicidade absoluta, dispensando FLUSHALL. A escolha de `k6-vu${__VU}-iter${__ITER}` foi **intencional**:

1. **Reprodutibilidade determinística:** dois runs do mesmo cenário geram estrutura de carga byte-a-byte idêntica — facilitando comparação direta entre backends.
2. **Debuggabilidade:** em caso de erro, é possível identificar exatamente qual VU e iteração falhou cruzando com logs do backend.
3. **Explicitação do protocolo:** o FLUSHALL explicita e documenta a decisão metodológica, tornando a reprodução inequívoca.

---

## 6. Validade Estatística

### 6.1 Por que 3 rodadas?

Uma única medição pode ser afetada por:
- Variações de CPU scheduling do host (Colima VM)
- Pausas de Garbage Collection (ZGC, Go GC)
- Jitter de rede Docker interno
- Paginação de memória do SO

Três rodadas independentes com FLUSHALL entre cada uma permitem calcular **média ± desvio padrão** e **Coeficiente de Variação (CV)**:

```
CV% = (desvio padrão / média) × 100
```

**Critério de qualidade:**
- CV < 1%: excelente reprodutibilidade (publicável)
- CV 1–5%: aceitável para benchmarks de sistema
- CV > 5%: resultado questionável

### 6.2 Resultados de CV obtidos

| Cenário | Métrica | Java 25 CV% | Go 1.25 CV% | Quarkus CV% |
|:---|:---|---:|---:|---:|
| Stress | Latência média | 0.11% | 0.14% | 0.21% |
| Stress | Total requests | 0.10% | 0.12% | 0.18% |
| Spike | Latência média (Go/Quarkus) | — | 0.34% | 0.43% |
| Spike | Latência média (Java) | 1.82% | — | — |

Todos os CVs abaixo de 2% — **qualidade científica adequada para publicação acadêmica**.

### 6.3 Erro padrão da média (SEM)

```
SEM = σ / √n

Para stress — latência Go (σ = 0.48ms, n = 3):
  SEM = 0.48 / √3 = 0.28ms
  IC 95% = ±0.55ms para média de 352ms
  Erro relativo < 0.16%
```

Com este nível de precisão, qualquer diferença de latência maior que ~1ms entre backends é **estatisticamente significativa** e não atribuível a variância de medição.

---

## 7. Simetria das Configurações

Comparação justa exige que **todas as variáveis sejam idênticas exceto o modelo de concorrência**.

### 7.1 Variáveis controladas

| Variável | Java 25 | Go 1.25 | Quarkus Native | Justificativa |
|:---|:---|:---|:---|:---|
| **Pool DB** | HikariCP: 200 | pgxpool: 200 | Agroal: 200 | Mesmos limites |
| **Timeout HTTP client** | 5s (RestClient) | 5s (net/http) | 5s (MicroProfile REST) | Mesma tolerância |
| **TTL Redis** | 24h | 24h | 24h | Mesma janela de idempotência |
| **Redis pool** | Lettuce (auto) | go-redis/v9: 200 | Quarkus Redis: 200 | Simétrico |
| **Porta** | 8081 | 8082 | 8083 | Separadas para testes paralelos |
| **Endpoint** | `POST /payments` | `POST /payments` | `POST /payments` | Idêntico |
| **Payload** | `{amount, cardNumber}` | `{amount, cardNumber}` | `{amount, cardNumber}` | Idêntico |
| **GC** | ZGC Generacional | Go GC concorrente | N/A (binário nativo) | Sub-milissegundo |
| **Arquitetura** | Clean Architecture | Clean Architecture | Clean Architecture | Mesma lógica de negócio |
| **Logging** | logstash-logback JSON | slog JSON | quarkus-logging JSON | Equivalentes |
| **Graceful shutdown** | 30s | 30s | 30s | Equivalentes |
| **Thread/goroutine pool** | VT ilimitadas (Loom) | Goroutines ilimitadas | OS Threads: 600 | Proporcional a 500 VUs |
| **HTTP client pool** | RestClient (automático) | net/http (automático) | MicroProfile REST: 600 | Proporcional a 500 VUs |

### 7.2 Métricas Prometheus simétricas

Os três backends expõem histograma compatível:

```
http_server_requests_seconds
  labels: method, uri, status, outcome
  buckets: [.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5]
```

Java via Micrometer, Go via `prometheus/client_golang`, Quarkus via Micrometer. Labels idênticos permitem queries PromQL idênticas no Grafana.

---

## 8. Descoberta e Correção das Configurações do Quarkus

### 8.1 Contexto

Na versão inicial do experimento (antes das correções), o Quarkus Native processava apenas ~56 req/s no cenário stress — contra ~342 req/s de Java e Go. Isso foi inicialmente interpretado como limitação arquitetural do modelo de OS threads. A análise forense revelou três bugs de configuração em cascata.

### 8.2 Bug 1 — Thread pool subdimensionado

**Sintoma:** Quarkus respondia apenas enquanto havia carrier threads disponíveis; requisições extras caíam em timeout silencioso.

**Causa:** `quarkus.thread-pool.max-threads` não configurado. Default do Vert.x é `CPUs × 8` — no ambiente Colima com 4 vCPUs, resultava em **32 threads**. Com 200 VUs e cada request segurando uma thread por ~350ms, o sistema saturava com apenas 32 requests simultâneos.

**Correção:**
```properties
# application.properties
quarkus.thread-pool.max-threads=${QUARKUS_MAX_THREADS:600}
quarkus.thread-pool.queue-size=1000
```

**Impacto medido:** Latência spike caiu de 7.069ms → 4.646ms.

### 8.3 Bug 2 — Redis pool subdimensionado

**Sintoma:** Após corrigir o thread pool, apareceram timeouts esporádicos no Redis.

**Causa:** `quarkus.redis.max-pool-size` não configurado. Default do Quarkus Redis client: **6 conexões**. Com 200 VUs fazendo 2 operações Redis por request, o pool recebia ~400 requisições Redis simultâneas — 67× acima da capacidade.

**Correção:**
```properties
quarkus.redis.max-pool-size=${REDIS_MAX_POOL_SIZE:200}
quarkus.redis.max-pool-waiting=500
```

### 8.4 Bug 3 — HTTP client pool subdimensionado (causa raiz do colapso)

**Sintoma:** Mesmo com thread pool e Redis corretos, Quarkus processava exatamente ~56 req/s.

**Causa root:** `quarkus.rest-client."config-key".connection-pool-size` default = **20 conexões por host**. Cada request ao mock-api ocupa uma conexão por ~350ms. Throughput máximo com 20 conexões: `20 / 0.35s = 57 req/s`. Observado: **56 req/s — correspondência exata**, confirmando o diagnóstico.

**Correção:**
```properties
quarkus.rest-client.external-api.connection-pool-size=${REST_CLIENT_POOL_SIZE:600}
```

**Impacto medido:** Stress passou de 56 req/s → 342 req/s (empate completo com Java e Go).

### 8.5 Implicação metodológica

Este achado demonstra que **resultados de benchmark são inválidos se os pools não estiverem simetricamente configurados**. O colapso inicial do Quarkus não era uma limitação de OS threads — era subutilização de infraestrutura por defaults inadequados para alta concorrência. A documentação explícita dessas correções é essencial para que o experimento seja reproduzível e comparável.

---

## 9. JEP 491 e o Achado do HikariCP

### 9.1 A hipótese inicial (incorreta)

A explicação original para a degradação do Java no spike era: *"HikariCP usa `synchronized` internamente, pinando Virtual Threads ao carrier OS thread."* Isso é documentado amplamente na literatura como a principal limitação de VTs com JDBC (Keppmann, 2023; Heinz Kabutz blog, 2024).

### 9.2 JEP 491 — Synchronize Virtual Threads without Pinning

O **JEP 491**, entregue no Java 24 e presente no Java 25, alterou o comportamento fundamental da JVM:

> *"A virtual thread will be able to be unmounted when it blocks in a synchronized method or statement."*

Antes do JEP 491: uma VT bloqueada em `synchronized` **pinava** a carrier thread — a OS thread ficava ocupada sem poder executar outras VTs.

Após o JEP 491: uma VT bloqueada em `synchronized` **suspende** normalmente, liberando a carrier thread para outras VTs — mesmo comportamento de `ReentrantLock` e `LockSupport`.

**Consequência:** Em Java 25, o problema de pinning do HikariCP **não existe mais** no nível de JVM.

### 9.3 Verificação empírica

O Dockerfile do backend Java inclui:

```dockerfile
ENTRYPOINT ["java",
  "-Djdk.tracePinnedThreads=full",   ← loga TODA vez que uma VT fica pinada
  "-jar", "app.jar"]
```

**Resultado nos logs durante os benchmarks:** Zero eventos de pinning registrados.

```bash
docker logs tcc-backend-java | grep -i "pinned"
# (sem saída — nenhum evento de pinning)
```

Isso confirma empiricamente que o JEP 491 está ativo e operacional no ambiente de teste.

### 9.4 A causa real da degradação do Java

Com pinning descartado, a investigação identificou a causa real: **contenção arquitetural no HikariCP sob concorrência extrema**.

HikariCP usa `synchronized` como mecanismo de serialização do pool de conexões. Com JEP 491:
- VTs **não ficam pinadas** no `synchronized` do HikariCP ✓
- VTs **ainda precisam serializar** a passagem pelo lock para adquirir/liberar conexões

Com 500 VTs simultâneas disputando o pool, o `synchronized` cria um **ponto único de serialização** com fila de espera. Cada VT aguarda sua vez no lock — não pin de carrier, mas contenção de throughput.

Go's `pgxpool` usa **channels nativos** (`chan *pgconn.PgConn`) — primitiva lock-free de sincronização do runtime Go. Sem gargalo de serialização.
Quarkus `Agroal` foi projetado sem `synchronized` no caminho crítico — usa CAS (Compare-And-Swap) atômico.

### 9.5 Implicação para o TCC

Este achado é **mais rico e mais preciso** do que a explicação original:

| Aspecto | Explicação anterior | Explicação corrigida |
|:---|:---|:---|
| Mecanismo | VT pinada ao carrier | Lock contention (sem pinning) |
| Nível | JVM | Biblioteca (HikariCP) |
| Java 25 | Ainda ocorreria | Confirmado empiricamente |
| Solução | Pool=500 ou JDBC não-pinante | Pool=500 ou pool VT-aware |
| Natureza | Modelo VT | Maturidade de ecossistema |

**Conclusão científica:** O modelo de Virtual Threads em Java 25 é correto e funcional (JEP 491 eliminou o pinning). A degradação observada reflete que o ecossistema de bibliotecas Java ainda não se adaptou completamente para explorar VTs sob concorrência extrema. Go's `pgxpool`, projetado nativamente para goroutines, não apresenta essa limitação.

---

## 10. Experimento de Controle — pool=500

### 10.1 Objetivo

Isolar a variável de contenção do pool para validar H0: *"com pools não limitantes, VTs e Goroutines são equivalentes"*.

### 10.2 Configuração

```yaml
# docker-compose override
backend-java:
  environment:
    HIKARI_MAX_POOL_SIZE: 500   # pool > 500 VUs → sem contenção
backend-go:
  environment:
    PG_MAX_CONNS: 500
```

### 10.3 Resultado do experimento de controle (spike, 500 VUs)

| Métrica | Java 25 (pool=500) | Go 1.25 (pool=500) | Delta |
|:---|:---|:---|:---|
| Latência média | 354ms | 354ms | **Empate** |
| p95 | 485ms | 488ms | **Empate** |
| Total requests | 39.201 | 39.182 | **Empate** |
| RPS | 653 | 655 | **Empate** |
| Taxa de erro | 0.1% | 0.2% | **Empate** |

**H0 confirmada:** Com pool=500 (sem contenção), Java VTs e goroutines entregam performance **estatisticamente indistinguível**.

### 10.4 Por que o experimento canônico usa pool=200?

O pool=200 foi escolhido como configuração canônica por duas razões:

1. **Realismo:** 200 conexões é uma configuração típica de produção para PostgreSQL (max_connections=300 server-side). Pool=500 requer configuração explícita do servidor.
2. **Valor científico:** O spike com pool=200 expõe o comportamento real dos backends sob contenção de recursos — condição que ocorre em produção. O experimento com pool=500 serve como **controle**, não como cenário principal.

Os resultados de ambos são arquivados em `results/local_benchmarks/` com seus respectivos relatórios.

---

## 11. Infraestrutura do Mock Externo

### 11.1 Por que um mock e não serviço real?

O experimento mede o **modelo de concorrência**, não a performance de serviços externos. Um serviço real introduziria variáveis incontroláveis (latência de rede WAN, carga do servidor externo, rate limiting, variação de SLA). O mock garante **condições idênticas e reproduzíveis**.

### 11.2 Latência uniforme 200–500ms

```go
// mock-external-api/main.go
latency := minLatency + rng.Int63n(maxLatency-minLatency)
time.Sleep(time.Duration(latency) * time.Millisecond)
```

O intervalo 200–500ms simula uma API de processadora de cartão real (Visa/Mastercard tipicamente: 150–400ms). A distribuição **uniforme** (não normal) garante que todos os backends recebam distribuições de latência estatisticamente idênticas ao longo de milhares de requests.

Este intervalo garante que o benchmark seja **I/O-bound por design** — o único workload que maximiza a diferença entre modelos de concorrência.

### 11.3 Bug de seed do RNG (corrigido)

**Problema original:** Com 500+ goroutines simultâneas, `time.Now().UnixNano()` pode retornar valores idênticos (resolução de nanosegundo excedida), produzindo seeds iguais e, consequentemente, distribuições artificialmente uniformes de latência — reduzindo a variância do mock.

**Solução:**
```go
// Antes (bug):
rand.New(rand.NewSource(time.Now().UnixNano()))

// Depois (corrigido):
rand.New(rand.NewSource(time.Now().UnixNano() ^ rand.Int63()))
```

O XOR com `rand.Int63()` usa o RNG global do Go (thread-safe) para garantir unicidade mesmo quando `UnixNano()` retorna valores idênticos.

---

## 12. Fluxo Completo de uma Requisição

```
k6 VU (goroutine no gerador)
    │
    │ POST /payments
    │ X-Idempotency-Key: k6-vu{N}-iter{I}
    │ Content-Type: application/json
    │ Authorization: (não aplicável — ambiente de teste)
    ▼
[Backend Java :8081 | Backend Go :8082 | Backend Quarkus :8083]
    │
    ├─ 1. Redis GET k6-vu{N}-iter{I}
    │       → MISS (Redis limpo por FLUSHALL antes do run)
    │
    ├─ 2. Validação de domínio
    │       → amount > 0, cardNumber 13–19 chars
    │       → Retorna 400 se inválido (não chega ao banco)
    │
    ├─ 3. PostgreSQL INSERT INTO payments
    │       → status = 'PENDING', id = UUID, created_at = now()
    │       → Conexão adquirida do pool e LIBERADA após commit
    │       (a conexão NÃO é mantida durante o passo 4)
    │
    ├─ 4. HTTP POST mock-api:8080/process-payment
    │       → aguarda 200–500ms  ← PONTO CRÍTICO DE CONCORRÊNCIA
    │
    │       Java (Virtual Thread):
    │         VT suspende via Continuation.yield()
    │         Carrier OS thread liberada para outro VT
    │
    │       Go (Goroutine):
    │         Goroutine suspende via netpoller (epoll/kqueue)
    │         M thread liberada para outra goroutine
    │
    │       Quarkus (OS Thread):
    │         OS thread BLOQUEADA durante toda a espera
    │         OS scheduler preempta para outra thread após quantum
    │
    ├─ 5. PostgreSQL UPDATE payments SET status='APPROVED'|'REJECTED'
    │       → Conexão adquirida e liberada após commit
    │
    ├─ 6. Redis SET k6-vu{N}-iter{I} = resultado (TTL 24h)
    │
    └─ 7. HTTP 201 Created
           {id, status, amount, cardNumber, externalId, createdAt}
    │
    ▼
k6 VU: check(status==201, body.id exists) → errorRate.add(failed)
       http_req_duration.add(latência)
```

**Nota sobre o passo 3:** A conexão ao PostgreSQL é liberada **antes** do passo 4. Isso é fundamental: se mantida durante a chamada externa, o pool de 200 conexões esgotaria com 200 VUs aguardando o mock (~350ms × 200 = todas as conexões ocupadas). A Clean Architecture com repositório por operação garante esse comportamento em todos os três backends.

---

## 13. Coleta de Memória RAM

### 13.1 Método

Durante cada execução k6, o script `run_benchmarks.sh` coleta em paralelo:

```bash
docker stats --no-stream --format "{{.MemUsage}}" tcc-backend-java >> java_${scenario}_round${n}.mem
```

Amostragem a cada segundo durante toda a execução do k6. O pico e a média são calculados pelo `analyze_results.py`.

### 13.2 O que docker stats mede

`docker stats` reporta o **RSS (Resident Set Size)** via cgroup — toda a memória física alocada pelo processo:

- **Java:** Heap (objetos) + Non-heap (Metaspace, Code Cache, Direct Buffers) + Stack das carrier threads (VTs têm stack virtual, não contam aqui) + overhead JVM
- **Go:** Heap (objetos GC) + Stacks de goroutines (~2 KB cada, crescem dinamicamente) + código do binário + runtime
- **Quarkus Native:** Heap Substrate (GraalVM) + Stacks de OS threads (~512 KB cada, estáticas) + código nativo

Esta é a métrica mais honesta para produção: é o que o sistema operacional cobra de memória física.

### 13.3 Por que RAM do Quarkus escala com VUs

No spike (500 VUs, 600 OS threads configuradas):
```
Stack de OS thread: ~512 KB (valor padrão JVM/libc para x86_64)
600 threads × 512 KB = ~300 MB apenas de stacks

Goroutine stack inicial: ~2 KB (go runtime, crescimento dinâmico)
500 goroutines × 2 KB = ~1 MB de stacks
```

Resultado observado: Quarkus spike = **464 MB** vs Go spike = **78 MB** para o mesmo throughput (~650 RPS). A diferença é estrutural — não há otimização de configuração que elimine o custo de stack de OS threads.

---

## 14. Decisões de Design

### 14.1 Por que latência percentílica e não throughput máximo puro?

Benchmark de throughput máximo satura o sistema completamente (RPS até colapso). Esta abordagem mede capacidade bruta mas não representa produção, onde o objetivo é manter latência abaixo de SLAs sob carga variável.

**Decisão:** Medir p95/p99 sob carga controlada (200 VUs stress, 500 VUs spike) é mais representativo de ambientes de pagamento reais, onde SLAs de p95 < 500ms são comuns.

### 14.2 Por que sleep(0.1) e não zero?

Sem sleep, 200 VUs com latência 350ms gerariam ~57.000 requests/s teórico — saturando o mock, o PostgreSQL e o Redis antes do backend. O backend não seria o gargalo. Com sleep(0.1), a carga é calibrada para ~340 RPS — alta o suficiente para revelar o comportamento do scheduler, baixa o suficiente para que o backend seja o único gargalo.

### 14.3 Por que PostgreSQL e não banco em memória?

Banco em memória (H2) eliminaria I/O de disco e tornaria os resultados artificialmente rápidos. O fluxo de pagamento em produção sempre usa banco transacional com persistência. PostgreSQL em Docker representa uma aproximação razoável do ambiente real, e os dois saves por request são operações simples (INSERT + UPDATE) que representam carga de I/O realista.

### 14.4 Por que pool=200 como configuração simétrica?

200 conexões é o máximo razoável para PostgreSQL com `max_connections=300` no servidor (reservando 100 para conexões administrativas e outros serviços). Configurações acima de 200 por backend exigiriam aumentar o `max_connections` do PostgreSQL — variável que deve ser mantida fixa no experimento.

---

## 15. Limitações do Estudo

### 15.1 Ambiente local vs cloud

Os benchmarks no Apple M4/Colima rodam sobre uma camada de virtualização ARM64. Em produção GCP (x86_64), os números absolutos (RPS, latência) serão diferentes. O **Quarkus Native binary é compilado para a arquitetura do build** — em GCP x86_64, seria necessário recompilar (o Dockerfile já suporta isso via Mandrel builder). Os resultados **relativos** (ranking entre os três backends) devem se preservar.

### 15.2 Ambiente compartilhado

Todos os containers rodam no mesmo host com 4 vCPUs / 8GB. Em produção, cada serviço teria recursos dedicados. Implicação: Java e Go competem pelos mesmos CPUs — o GC do Java pode impactar medições do Go quando rodados simultaneamente (motivo pelo qual o benchmark os executa **sequencialmente**, não em paralelo).

### 15.3 Modelo de carga sintética

500 VUs fazendo 1 request cada não representa fielmente usuários reais (think time variável, sessões longas, retries). A carga sintética maximiza a pressão sobre o scheduler, o que é o objetivo do experimento, mas pode superestimar diferenças que seriam suavizadas por padrões reais de acesso.

### 15.4 Escopo: único endpoint I/O-bound

O experimento testa exclusivamente `POST /payments` — escrita com I/O intenso. Endpoints de leitura, operações em batch, ou workloads CPU-bound podem apresentar resultados diferentes. A conclusão de equivalência entre os três modelos é válida **especificamente para workloads I/O-bound**, que é o caso de uso principal de gateways de pagamento.

### 15.5 Maturidade do ecossistema Java

O achado da contenção no HikariCP (Seção 9) indica que o ecossistema Java ainda está em adaptação para Virtual Threads. Versões futuras do HikariCP podem migrar internos para primitivas VT-aware, alterando os resultados do spike sem mudança no código de aplicação. O experimento documenta o estado do ecossistema em **março de 2026**.

### 15.6 Quarkus: modelo de contraste, não competidor principal

O Quarkus Native cumpre papel metodológico (isolar JVM vs modelo de concorrência), mas sua configuração de OS threads tem limitações conhecidas sob carga extrema (RAM ~6× maior que Go). Otimizações de concorrência do Quarkus (Vert.x event loop, Mutiny reactive) foram intencionalmente evitadas para manter OS threads puro como baseline de contraste.

---

## 16. Protocolo de Reprodução

Para replicar completamente os resultados deste estudo:

```bash
# 1. Pré-requisitos
brew install k6 docker colima python3

# 2. Configurar ambiente ARM64 (Apple Silicon)
colima start --cpu 4 --memory 8 --arch aarch64

# 3. Build e start da infraestrutura completa
docker compose up -d --build

# 4. Aguardar todos os backends (Quarkus Native: ~2s de inicialização)
sleep 10
curl -s http://localhost:8081/actuator/health | jq .status  # Java
curl -s http://localhost:8082/health | jq .status            # Go
curl -s http://localhost:8083/actuator/health | jq .status  # Quarkus

# 5. Executar bateria completa
#    27 runs: 3 backends × 3 cenários × 3 rodadas
#    FLUSHALL Redis automático antes de cada run
bash scripts/benchmarks/run_benchmarks.sh

# 6. Gerar relatório estatístico
RESULTS_DIR=$(ls -td results/runs/*/ | head -1)
python3 scripts/benchmarks/analyze_results.py "$RESULTS_DIR" --format markdown

# 7. Teardown completo (limpa volumes)
docker compose down --volumes
```

**Tempo estimado:** 55–70 minutos para a bateria completa de 27 runs.

**Variáveis de ambiente configuráveis:**
```bash
# Configuração canônica (pool=200, padrão)
docker compose up -d --build

# Experimento de controle (pool=500, isola HikariCP contention)
HIKARI_MAX_POOL_SIZE=500 PG_MAX_CONNS=500 docker compose up -d
```

---

*Este documento descreve a metodologia completa do benchmark para fins de reprodutibilidade científica e defesa acadêmica.*
*Versão do experimento: pool=200 (configuração canônica), 3 rodadas, Apple M4 ARM64, Colima.*
*Experimento de controle: pool=500, resultados em `results/local_benchmarks/POOL_EXPERIMENT_REPORT.md`.*
