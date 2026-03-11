# Relatorio Estatistico -- Benchmark TCC
**Diretorio:** `results/runs/20260311_162612`
**Gerado em:** 20260311_162612

> Valores: media +/- desvio padrao (N rodadas por cenario/backend)
> RAM capturada via `docker stats` em tempo real durante cada k6 run

## Cenario: BASELINE (20 VUs, 2 min)

| Metrica | Java 25 (VT) | Go 1.25 | Quarkus Native | Java vs Go | Java vs Quarkus | Go vs Quarkus |
| :--- | ---: | ---: | ---: | :--- | :--- | :--- |
| Latencia Media (ms) | 358.9 +/-1.1 | 352.7 +/-1.0 | 358.0 +/-0.7 | Empate | Empate | Empate |
| Mediana p50 (ms) | 359.7 +/-2.0 | 351.2 +/-1.1 | 357.4 +/-0.6 | Go -2.4% | Empate | Empate |
| p95 (ms) | 493.1 +/-2.1 | 489.5 +/-0.5 | 492.3 +/-0.4 | Empate | Empate | Empate |
| p99 (ms) | 506.1 +/-2.9 | 501.8 +/-0.7 | 504.0 +/-0.4 | Empate | Empate | Empate |
| Total Requests | 2912.0 +/-7.0 | 2952.7 +/-8.3 | 2919.0 +/-5.3 | Empate | Empate | Empate |
| Taxa de Erro (%) | 0.00% | 0.00% | 0.00% | Empate | Empate | Empate |
| **RAM Pico (MB)**  | 753.0 +/-96.3 MB | 61.0 +/-0.9 MB | 55.9 +/-11.1 MB | Go -91.9% | Go -92.6% | Go -8.3% |
| **RAM Media (MB)** | 733.0 +/-90.6 MB | 57.6 +/-1.2 MB | 51.8 +/-10.9 MB | Go -92.1% | Go -92.9% | Go -10.0% |

## Cenario: STRESS (200 VUs, ~2 min)

| Metrica | Java 25 (VT) | Go 1.25 | Quarkus Native | Java vs Go | Java vs Quarkus | Go vs Quarkus |
| :--- | ---: | ---: | ---: | :--- | :--- | :--- |
| Latencia Media (ms) | 354.0 +/-1.1 | 351.8 +/-1.0 | 2719.7 +/-15.8 | Empate | Java -668.3% | Java -673.1% |
| Mediana p50 (ms) | 354.3 +/-1.1 | 351.6 +/-1.3 | 3294.0 +/-16.9 | Empate | Java -829.8% | Java -836.8% |
| p95 (ms) | 488.7 +/-1.0 | 486.8 +/-0.5 | 3561.1 +/-8.4 | Empate | Java -628.8% | Java -631.6% |
| p99 (ms) | 500.6 +/-1.0 | 498.7 +/-0.5 | 3626.5 +/-5.7 | Empate | Java -624.5% | Java -627.2% |
| Total Requests | 37505.3 +/-101.7 | 37690.7 +/-80.8 | 6104.7 +/-34.0 | Empate | Java +83.7% | Java +83.8% |
| Taxa de Erro (%) | 0.0 +/-0.0 | 0.0 +/-0.0 | 0.0 +/-0.0 | --- | Empate | Go -100.0% |
| **RAM Pico (MB)**  | 1420.0 +/-419.9 MB | 78.8 +/-3.6 MB | 91.1 +/-6.3 MB | Go -94.4% | Go -93.6% | Java -15.6% |
| **RAM Media (MB)** | 1281.8 +/-415.4 MB | 72.9 +/-3.6 MB | 68.2 +/-1.0 MB | Go -94.3% | Go -94.7% | Go -6.5% |

## Cenario: SPIKE (500 VUs, 1 min)

| Metrica | Java 25 (VT) | Go 1.25 | Quarkus Native | Java vs Go | Java vs Quarkus | Go vs Quarkus |
| :--- | ---: | ---: | ---: | :--- | :--- | :--- |
| Latencia Media (ms) | 724.3 +/-1.7 | 353.4 +/-0.7 | 4645.7 +/-19.1 | Go -51.2% | Java -541.4% | Java -1214.6% |
| Mediana p50 (ms) | 751.1 +/-0.6 | 353.4 +/-1.1 | 5007.6 +/-1.9 | Go -52.9% | Java -566.7% | Java -1316.9% |
| p95 (ms) | 918.8 +/-3.9 | 488.3 +/-1.2 | 5439.4 +/-1.9 | Go -46.9% | Java -492.0% | Java -1014.1% |
| p99 (ms) | 997.0 +/-80.2 | 500.4 +/-1.1 | 5484.4 +/-1.7 | Go -49.8% | Java -450.1% | Java -996.1% |
| Total Requests | 21595.7 +/-40.3 | 39182.3 +/-62.6 | 3966.3 +/-10.3 | Go +81.4% | Java +81.6% | Java +89.9% |
| Taxa de Erro (%) | 0.0 +/-0.0 | 0.2 +/-0.2 | 38.3 +/-1.0 | --- | --- | Java -23831.6% |
| **RAM Pico (MB)**  | 1937.7 +/-4.1 MB | 108.0 +/-1.6 MB | 250.4 +/-29.8 MB | Go -94.4% | Go -87.1% | Java -131.8% |
| **RAM Media (MB)** | 1874.9 +/-100.0 MB | 98.7 +/-2.8 MB | 163.6 +/-3.7 MB | Go -94.7% | Go -91.3% | Java -65.8% |

