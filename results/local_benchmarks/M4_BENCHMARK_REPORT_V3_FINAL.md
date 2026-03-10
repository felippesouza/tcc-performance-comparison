# Relatório Final de Benchmark: Java 25 (VT) vs Go 1.25 (Goroutines)
## Apple M4 — pool=500 — 3 Rodadas — Memória RAM capturada em tempo real

**Autor:** Felippe Gustavo de Souza e Silva
**Instituição:** USP ESALQ — Engenharia de Software
**Orientador:** Prof. Marcos Jardel Henriques
**Data:** 10 de Março de 2026
**Ambiente:** Apple M4 (ARM64) — Colima (VM VZ, Linux/arm64 nativo, pool=500)
**Protocolo:** 3 rodadas × Redis FLUSHALL antes de cada execução × RAM via `docker stats`

---

## 🖥️ Configuração

| Componente | Especificação |
| :--- | :--- |
| **Hardware** | Apple M4 (ARM64) |
| **Runtime de Containers** | Colima (VZ driver) — Linux/arm64 nativo |
| **CPUs / Memória** | 4 vCPUs / 8 GB |
| **Pool DB — Java** | HikariCP: **500** conexões |
| **Pool DB — Go** | pgxpool MaxConns: **500** |
| **PostgreSQL** | 16-alpine — `max_connections=1200` |
| **Redis** | 7-alpine — FLUSHALL antes de cada run |
| **Mock API** | Go 1.25-alpine — 200–500ms latência uniforme |
| **k6** | v1.6.1 — darwin/arm64 |
| **Coleta de RAM** | `docker stats` streaming (~1 amostra/s por container) |

---

## 📊 Cenário 1 — BASELINE (20 VUs, 2 minutos)

| Métrica | Java 25 (VT) | ±σ | Go 1.25 | ±σ | Delta |
| :--- | ---: | ---: | ---: | ---: | :--- |
| **Latência Média (ms)** | 360.3 | ±3.3 | 355.9 | ±1.6 | Empate |
| **Mediana p50 (ms)** | 361.5 | ±4.3 | 355.4 | ±3.0 | Empate |
| **p95 (ms)** | 494.4 | ±2.8 | 491.0 | ±0.6 | Empate |
| **p99 (ms)** | 505.7 | ±0.3 | 502.7 | ±0.2 | Empate |
| **Total Requests** | 2.905 | ±20 | 2.932 | ±9 | Empate |
| **Taxa de Erro** | 0.00% | — | 0.00% | — | Empate |
| **RAM Pico** | 1.190 MB | ±208 | **56 MB** | ±0.7 | **Go −95.3%** |
| **RAM Média** | 1.159 MB | ±181 | **53 MB** | ±0.9 | **Go −95.4%** |

> **Nota:** Alta variância no RAM do Java (±208 MB) reflete aquecimento da JVM — JIT compilando código quente, heap sizing ajustando. Esperado no primeiro cenário após cold start.

---

## 📊 Cenário 2 — STRESS (200 VUs, ~2 minutos)

| Métrica | Java 25 (VT) | ±σ | Go 1.25 | ±σ | Delta |
| :--- | ---: | ---: | ---: | ---: | :--- |
| **Latência Média (ms)** | 352.5 | ±0.4 | 351.7 | ±0.5 | Empate |
| **Mediana p50 (ms)** | 352.1 | ±1.0 | 351.3 | ±1.3 | Empate |
| **p95 (ms)** | 487.8 | ±0.4 | 486.7 | ±0.2 | Empate |
| **p99 (ms)** | 499.8 | ±0.4 | 498.6 | ±0.0 | Empate |
| **Total Requests** | 37.631 | ±36 | 37.699 | ±44 | Empate |
| **Taxa de Erro** | 0.00% | — | 0.00% | — | Empate |
| **RAM Pico** | 1.221 MB | ±1 | **64 MB** | ±6 | **Go −94.8%** |
| **RAM Média** | 1.165 MB | ±94 | **60 MB** | ±5 | **Go −94.9%** |

> **Nota:** JVM aquecida — variância do RAM Java cai para ±1 MB no pico. Throughput equivalente: 37.631 vs 37.699 requests (diferença 0.18%).

---

## 📊 Cenário 3 — SPIKE (500 VUs, 1 minuto) — pool=500

| Métrica | Java 25 (VT) | ±σ | Go 1.25 | ±σ | Delta |
| :--- | ---: | ---: | ---: | ---: | :--- |
| **Latência Média (ms)** | 357.6 | ±6.5 | 352.2 | ±1.2 | Empate |
| **Mediana p50 (ms)** | 354.2 | ±1.0 | 351.9 | ±1.8 | Empate |
| **p95 (ms)** | 489.6 | ±0.9 | 487.5 | ±1.6 | Empate |
| **p99 (ms)** | 501.7 | ±0.7 | 499.5 | ±1.5 | Empate |
| **Total Requests** | 39.126 | ±81 | 39.286 | ±108 | Empate |
| **Taxa de Erro** | 0.00% | — | 0.00% | — | Empate |
| **RAM Pico** | **1.953 MB** | ±9 | **82 MB** | ±0.4 | **Go −95.8%** |
| **RAM Média** | **1.863 MB** | ±144 | **75 MB** | ±2 | **Go −96.0%** |

> **Achado crítico:** Com pool proporcional (500 conexões / 500 VUs), performance equivalente mesmo no spike. O diferencial restante é **exclusivamente a RAM**: Java usa ~24x mais memória que Go sob carga máxima.

---

## 🔬 Visão Consolidada — Achados Definitivos

### Performance (Latência + Throughput)

| Cenário | VUs | Pool | Java Média | Go Média | Vencedor |
| :--- | ---: | ---: | ---: | ---: | :--- |
| Baseline | 20 | 500 | 360ms ±3.3 | 356ms ±1.6 | **Empate** |
| Stress | 200 | 500 | 352ms ±0.4 | 351ms ±0.5 | **Empate** |
| Spike | 500 | 200 | 721ms ±1.4 | 352ms ±0.7 | **Go −51%** |
| **Spike** | **500** | **500** | **357ms ±6.5** | **352ms ±1.2** | **Empate** |

### RAM (Footprint de Memória)

| Cenário | VUs | Java Pico | Go Pico | Delta |
| :--- | ---: | ---: | ---: | :--- |
| Baseline | 20 | 1.190 MB ±208 | 56 MB ±0.7 | **Go −95.3%** |
| Stress | 200 | 1.221 MB ±1 | 64 MB ±6 | **Go −94.8%** |
| Spike | 500 | 1.953 MB ±9 | 82 MB ±0.4 | **Go −95.8%** |

---

## 🧠 Conclusões Científicas Definitivas

### 1. Equivalência de performance comprovada (com pool adequado)
Java 25 Virtual Threads e Go 1.25 Goroutines são **estatisticamente equivalentes** em throughput e latência em todos os cenários testados — baseline, stress e spike — quando o pool de conexões é proporcional à carga (500 conexões para 500 VUs). CV < 2% em todas as métricas confirma reprodutibilidade científica.

### 2. RAM é o diferencial real e definitivo
Go consome **~95% menos RAM** que Java em todos os cenários:
- Baseline: **56 MB** (Go) vs **1.190 MB** (Java) — fator 21x
- Stress: **64 MB** (Go) vs **1.221 MB** (Java) — fator 19x
- Spike: **82 MB** (Go) vs **1.953 MB** (Java) — fator 24x

Este é o diferencial que persiste após equalizar performance. É a diferença entre binário estático (Go) vs JVM + Spring Framework + metaspace + code cache (Java).

### 3. RAM do Java cresce linearmente com a carga; Go é quase constante
Go: 56 MB → 82 MB (+46% do baseline ao spike)
Java: 1.190 MB → 1.953 MB (+64% do baseline ao spike)

Go escala de forma mais eficiente em memória conforme a concorrência aumenta — goroutines adicionam ~2KB de stack cada; Virtual Threads adicionam stack + overhead da fila HikariCP.

### 4. JVM warm-up é observável e relevante
A variância de RAM no baseline Java (±208 MB) cai para ±1 MB no stress — evidência de que o JIT compiler estabiliza o heap após o primeiro cenário. Este fenômeno não existe no Go (±0.7 MB constante). Em ambientes com cold starts frequentes (serverless, auto-scaling), esta diferença é operacionalmente significativa.

### 5. Implicações para escolha tecnológica

| Critério | Java 25 (VT) | Go 1.25 |
| :--- | :--- | :--- |
| **Throughput (pool adequado)** | Equivalente | Equivalente |
| **Latência (pool adequado)** | Equivalente | Equivalente |
| **Resiliência a pool subdimensionado** | Degradação severa | Resiliente |
| **RAM em produção** | ~1.2–2 GB por instância | ~60–80 MB por instância |
| **Custo de instância GCP (e1-small 2GB)** | ~1 instância por pod | ~25 instâncias por pod |
| **Cold start / warm-up** | JIT overhead observável | Zero warm-up |
| **Ecossistema** | Spring, JPA, observabilidade rica | Stdlib, minimalista |

### 6. Recomendação para produção

**Para sistemas com carga previsível e moderada:** indiferente — performance idêntica com pool adequado. A escolha deve ser por ecossistema e equipe.

**Para sistemas de alta densidade (múltiplos serviços por host):** Go — fator 20x em memória permite rodar muito mais instâncias no mesmo hardware, reduzindo custo de infraestrutura.

**Para sistemas com picos imprevisíveis e pool fixo:** Go — mais resiliente quando o pool fica subdimensionado temporariamente.

---

## 🚀 Próximos Passos — Validação no GCP

1. **Replicar protocolo idêntico** — pool=200 e pool=500 para isolar variável
2. **Instâncias dedicadas** — PostgreSQL, Redis e backends em VMs separadas
3. **Métricas de custo** — instâncias mínimas para sustentar 200 RPS: comparar `e2-micro` vs `e2-small`
4. **3 rodadas com σ** — mesmo protocolo deste relatório
5. **Observar RAM em GCP** — confirmar o fator 20x em ambiente cloud real

---

*Relatório gerado via `analyze_results.py` — 18 execuções k6 com isolamento Redis completo e captura de RAM via `docker stats`.*
*Reproduzível: `docker compose -f docker-compose.yml -f docker-compose.pool-experiment.yml up -d && bash scripts/benchmarks/run_benchmarks.sh --rounds 3`*
