
Analisando 27 arquivos em: results/runs/20260311_141726

# Relatorio Estatistico -- Benchmark TCC
**Diretorio:** `results/runs/20260311_141726`
**Gerado em:** 20260311_141726

> Valores: media +/- desvio padrao (N rodadas por cenario/backend)
> RAM capturada via `docker stats` em tempo real durante cada k6 run

## Cenario: BASELINE (20 VUs, 2 min)

| Metrica | Java 25 (VT) | Go 1.25 | Quarkus Native | Java vs Go | Java vs Quarkus |
| :--- | ---: | ---: | ---: | :--- | :--- |
| Latencia Media (ms) | 357.1 +/-1.0 | 353.3 +/-0.6 | 354.7 +/-0.5 | Empate | Empate |
| Mediana p50 (ms) | 357.1 +/-1.8 | 352.3 +/-2.0 | 354.4 +/-1.4 | Empate | Empate |
| p95 (ms) | 491.4 +/-2.7 | 488.8 +/-0.2 | 489.8 +/-0.9 | Empate | Empate |
| p99 (ms) | 503.9 +/-1.4 | 500.9 +/-0.9 | 502.5 +/-0.6 | Empate | Empate |
| Total Requests | 2924.3 +/-8.1 | 2949.0 +/-5.3 | 2941.7 +/-3.5 | Empate | Empate |
| Taxa de Erro (%) | 0.00% | 0.00% | 0.00% | Empate | Empate |
| **RAM Pico (MB)**  | 755.2 +/-56.3 MB | 33.0 +/-2.1 MB | 56.5 +/-9.7 MB | Go -95.6% | Go -92.5% |
| **RAM Media (MB)** | 746.9 +/-59.7 MB | 29.6 +/-2.0 MB | 51.8 +/-11.2 MB | Go -96.0% | Go -93.1% |

## Cenario: STRESS (200 VUs, ~2 min)

| Metrica | Java 25 (VT) | Go 1.25 | Quarkus Native | Java vs Go | Java vs Quarkus |
| :--- | ---: | ---: | ---: | :--- | :--- |
| Latencia Media (ms) | 353.3 +/-0.2 | 350.9 +/-0.3 | 2723.7 +/-5.0 | Empate | Java -670.9% |
| Mediana p50 (ms) | 352.8 +/-0.7 | 350.7 +/-0.5 | 3294.3 +/-12.2 | Empate | Java -833.7% |
| p95 (ms) | 488.5 +/-0.3 | 486.5 +/-0.4 | 3563.4 +/-12.7 | Empate | Java -629.4% |
| p99 (ms) | 500.6 +/-0.4 | 498.6 +/-0.2 | 3629.9 +/-24.4 | Empate | Java -625.2% |
| Total Requests | 37559.7 +/-7.6 | 37761.0 +/-29.5 | 6096.3 +/-8.1 | Empate | Java +83.8% |
| Taxa de Erro (%) | 0.0 +/-0.0 | 0.0 +/-0.0 | 0.0 +/-0.0 | --- | Empate |
| **RAM Pico (MB)**  | 1595.5 +/-577.1 MB | 50.0 +/-0.1 MB | 89.5 +/-6.3 MB | Go -96.9% | Go -94.4% |
| **RAM Media (MB)** | 1389.7 +/-548.0 MB | 45.1 +/-2.3 MB | 67.4 +/-0.4 MB | Go -96.8% | Go -95.2% |

## Cenario: SPIKE (500 VUs, 1 min)

| Metrica | Java 25 (VT) | Go 1.25 | Quarkus Native | Java vs Go | Java vs Quarkus |
| :--- | ---: | ---: | ---: | :--- | :--- |
| Latencia Media (ms) | 723.1 +/-2.9 | 353.1 +/-1.3 | 7069.8 +/-17.8 | Go -51.2% | Java -877.8% |
| Mediana p50 (ms) | 749.8 +/-3.5 | 353.3 +/-1.1 | 8586.1 +/-2.4 | Go -52.9% | Java -1045.2% |
| p95 (ms) | 917.4 +/-3.6 | 488.0 +/-1.3 | 8831.3 +/-18.8 | Go -46.8% | Java -862.6% |
| p99 (ms) | 970.4 +/-36.9 | 499.8 +/-1.2 | 8904.4 +/-23.1 | Go -48.5% | Java -817.6% |
| Total Requests | 21635.3 +/-80.9 | 39207.3 +/-112.6 | 2743.0 +/-6.1 | Go +81.2% | Java +87.3% |
| Taxa de Erro (%) | 0.0 +/-0.0 | 0.1 +/-0.2 | 0.0 +/-0.0 | --- | Empate |
| **RAM Pico (MB)**  | 1915.6 +/-13.6 MB | 78.6 +/-2.9 MB | 96.9 +/-8.6 MB | Go -95.9% | Go -94.9% |
| **RAM Media (MB)** | 1895.6 +/-16.5 MB | 69.0 +/-3.1 MB | 77.3 +/-2.5 MB | Go -96.4% | Go -95.9% |

