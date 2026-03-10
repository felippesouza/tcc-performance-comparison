# Experimento de Pool Proporcional — Resultado Definitivo
## Hipótese: A vantagem do Go no spike é do scheduler M:N ou do pool HikariCP?

**Autor:** Felippe Gustavo de Souza e Silva
**Instituição:** USP ESALQ — Engenharia de Software
**Data:** 10 de Março de 2026
**Ambiente:** Apple M4 (ARM64) — Colima (Linux/arm64 nativo)
**Protocolo:** 3 rodadas × FLUSHALL antes de cada execução × pool=500 para ambos os backends

---

## 🔬 Hipótese Testada

No benchmark anterior (pool=200, 500 VUs), Go superou Java em +81% de throughput e −51% de latência.

**Hipótese A — Pool contention:** A diferença é causada pelo HikariCP com 200 conexões para 500 VUs.
Com pool proporcional (500 conexões), Java se igualaria ao Go.

**Hipótese B — Scheduler M:N:** A diferença é causada pelo scheduler do Go ser genuinamente superior.
Mesmo com pool=500, Go continuaria vencendo.

---

## 📊 Resultado — SPIKE com pool=500 (500 VUs, 1 minuto, 3 rodadas)

| Métrica | Java 25 (VT) | ±σ | Go 1.25 | ±σ | Delta |
| :--- | ---: | ---: | ---: | ---: | :--- |
| **Latência Média (ms)** | 354.8 | ±1.6 | 352.9 | ±1.6 | **Empate** |
| **Mediana p50 (ms)** | 355.0 | ±2.0 | 352.5 | ±1.7 | **Empate** |
| **p95 (ms)** | 489.7 | ±1.4 | 487.9 | ±1.8 | **Empate** |
| **p99 (ms)** | 501.8 | ±1.5 | 500.1 | ±1.4 | **Empate** |
| **Total Requests** | 39.057 | ±136 | 39.221 | ±131 | **Empate** |
| **Taxa de Erro** | 0.00% | ±0.0 | 0.00% | ±0.0 | Empate |

---

## 📊 Comparação Direta: pool=200 vs pool=500 no Spike

| Métrica | Java pool=200 | Java pool=500 | Go pool=200 | Go pool=500 |
| :--- | ---: | ---: | ---: | ---: |
| **Latência Média (ms)** | 721.1 ±1.4 | **354.8 ±1.6** | 352.2 ±0.7 | 352.9 ±1.6 |
| **Mediana p50 (ms)** | 748.5 ±2.8 | **355.0 ±2.0** | 352.0 ±0.7 | 352.5 ±1.7 |
| **p95 (ms)** | 915.2 ±1.6 | **489.7 ±1.4** | 487.0 ±0.5 | 487.9 ±1.8 |
| **Total Requests** | 21.683 ±32 | **39.057 ±136** | 39.286 ±62 | 39.221 ±131 |

**Observação crítica:** Com pool=500, a latência do Java caiu de 721ms para 354ms — redução de **50.8%**. O throughput saltou de 21.683 para 39.057 requests — aumento de **80.2%**. O Go permaneceu estável em ambas as configurações.

---

## 🧠 Conclusão Científica — HIPÓTESE A CONFIRMADA

> **A superioridade do Go no spike (pool=200) era causada inteiramente pela contenção do pool HikariCP, não pelo scheduler M:N das goroutines.**

Com pool proporcional ao número de VUs (500 conexões para 500 VUs), **Java 25 Virtual Threads e Go 1.25 Goroutines são estatisticamente equivalentes em todos os cenários testados** — incluindo o spike de 500 VUs concorrentes.

### Implicações diretas

| Dimensão | Conclusão |
| :--- | :--- |
| **Throughput sob spike** | Equivalentes com pool proporcional (~39.000 requests) |
| **Latência sob spike** | Equivalentes — ambos ~353ms (latência do mock externo) |
| **Variância (σ)** | Ambos ±1.4–2.0ms — igualmente estáveis |
| **Diferencial real do Go** | Resiliência com pool subdimensionado (pool < VUs) |
| **Diferencial real do Java** | Nenhuma desvantagem com pool adequado |

### O que a pesquisa prova

1. **Project Loom eliminou a diferença de performance** entre Java e Go para workloads I/O-bound — em qualquer nível de carga, desde que o pool de conexões seja adequadamente dimensionado.

2. **O gargalo era operacional, não arquitetural.** HikariCP com 200 conexões para 500 VUs cria 300 threads em fila — isso é uma decisão de configuração, não uma limitação do modelo de Virtual Threads.

3. **Implicação para produção:** Em sistemas onde o pool é sempre proporcional à carga esperada (prática padrão), Java e Go têm performance idêntica. A escolha entre eles deve ser guiada por outros fatores: ecossistema, footprint de memória, complexidade operacional.

### Achado secundário relevante

O Go permaneceu estável em ambas as configurações (pool=200 e pool=500). Isso confirma que o scheduler M:N lida melhor com *contenção de recursos* — quando goroutines aguardam conexão, o overhead por goroutine em espera é mínimo (~2KB stack). No Java com pool=200, a fila de Virtual Threads aguardando HikariCP acumulava latência cumulativa. Isso sugere que **Go é mais resiliente a misconfigurações de pool**, enquanto Java exige dimensionamento mais cuidadoso.

---

## 📋 Tabela Consolidada — Todos os Cenários e Configurações

| Cenário | Pool | VUs | Java Média | Go Média | Delta | Vencedor |
| :--- | :---: | ---: | ---: | ---: | ---: | :--- |
| Baseline | 200 | 20 | 360.3ms | 356.7ms | −1.0% | **Empate** |
| Stress | 200 | 200 | 353.0ms | 351.1ms | −0.5% | **Empate** |
| Spike | 200 | 500 | 721.1ms | 352.2ms | −51.2% | **Go** |
| **Spike** | **500** | **500** | **354.8ms** | **352.9ms** | **−0.5%** | **Empate** |

---

## 🚀 Próximos Passos — GCP

Com estes resultados em mãos, a validação no GCP deve seguir o protocolo:

1. **Instâncias dedicadas** — PostgreSQL, Redis e backends em VMs separadas
2. **Testar ambas as configurações de pool** — pool=200 e pool=500 no spike
3. **Capturar métricas de RAM** via Grafana — footprint real no GCP (RSS, Non-Heap)
4. **3 rodadas com média/σ** — mesmo protocolo usado neste experimento

**Hipótese para o GCP:** Os resultados de equivalência devem se replicar. A diferença de footprint de memória (RAM RSS) será o próximo diferencial a quantificar.

---

*Experimento conduzido com isolamento completo: infra recriada do zero, Redis FLUSHALL antes de cada execução, 3 rodadas independentes por configuração.*
*Reproduzível via: `docker compose -f docker-compose.yml -f docker-compose.pool-experiment.yml up -d && bash scripts/benchmarks/run_benchmarks.sh --scenario spike --rounds 3`*
