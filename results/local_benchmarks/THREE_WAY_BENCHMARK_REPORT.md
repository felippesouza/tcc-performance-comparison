# Relatorio Estatistico -- Benchmark TCC
**Diretorio:** `results/runs/20260312_104336`
**Gerado em:** 20260312_104336

> Valores: media +/- desvio padrao (N rodadas por cenario/backend)
> RAM capturada via `docker stats` em tempo real durante cada k6 run

## Cenario: BASELINE (20 VUs, 2 min)

| Metrica | Java 25 (VT) | Go 1.25 | Quarkus Native | Java vs Go | Java vs Quarkus | Go vs Quarkus |
| :--- | ---: | ---: | ---: | :--- | :--- | :--- |
| Latencia Media (ms) | 358.0 +/-2.0 | 354.1 +/-2.7 | 356.6 +/-1.6 | Empate | Empate | Empate |
| Mediana p50 (ms) | 359.0 +/-1.8 | 354.6 +/-6.4 | 356.1 +/-1.2 | Empate | Empate | Empate |
| p95 (ms) | 491.9 +/-1.4 | 489.4 +/-1.7 | 491.9 +/-1.3 | Empate | Empate | Empate |
| p99 (ms) | 504.4 +/-1.8 | 500.4 +/-1.0 | 502.7 +/-0.7 | Empate | Empate | Empate |
| Total Requests | 2917.7 +/-11.7 | 2945.0 +/-17.4 | 2929.3 +/-11.0 | Empate | Empate | Empate |
| RPS (req/s) | 24.5 +/-0.2 | 24.6 +/-0.2 | 24.4 +/-0.1 | Empate | Empate | Empate |
| Taxa de Erro (%) | 0.00% | 0.00% | 0.00% | Empate | Empate | Empate |
| **RAM Pico (MB)**  | 789.0 +/-51.2 MB | 32.4 +/-0.6 MB | 55.5 +/-8.4 MB | Go -95.9% | Quarkus -93.0% | Go -71.2% |
| **RAM Media (MB)** | 768.8 +/-61.6 MB | 29.6 +/-1.5 MB | 51.6 +/-9.9 MB | Go -96.1% | Quarkus -93.3% | Go -74.4% |

## Cenario: STRESS (200 VUs, ~2 min)

| Metrica | Java 25 (VT) | Go 1.25 | Quarkus Native | Java vs Go | Java vs Quarkus | Go vs Quarkus |
| :--- | ---: | ---: | ---: | :--- | :--- | :--- |
| Latencia Media (ms) | 353.4 +/-0.5 | 351.6 +/-0.2 | 353.5 +/-0.6 | Empate | Empate | Empate |
| Mediana p50 (ms) | 353.4 +/-0.6 | 351.8 +/-0.1 | 353.3 +/-0.8 | Empate | Empate | Empate |
| p95 (ms) | 488.4 +/-0.3 | 486.3 +/-0.3 | 488.5 +/-0.4 | Empate | Empate | Empate |
| p99 (ms) | 500.5 +/-0.4 | 498.7 +/-0.4 | 500.4 +/-0.4 | Empate | Empate | Empate |
| Total Requests | 37554.0 +/-39.9 | 37702.3 +/-16.7 | 37545.3 +/-49.9 | Empate | Empate | Empate |
| RPS (req/s) | 342.0 +/-0.5 | 343.4 +/-0.4 | 341.8 +/-0.7 | Empate | Empate | Empate |
| Taxa de Erro (%) | 0.0 +/-0.0 | 0.0 +/-0.0 | 0.0 +/-0.0 | --- | --- | Go -3116.4% |
| **RAM Pico (MB)**  | 1378.7 +/-486.1 MB | 49.7 +/-2.1 MB | 147.7 +/-36.0 MB | Go -96.4% | Quarkus -89.3% | Go -197.4% |
| **RAM Media (MB)** | 1115.1 +/-259.7 MB | 44.4 +/-2.8 MB | 81.6 +/-5.3 MB | Go -96.0% | Quarkus -92.7% | Go -83.6% |

## Cenario: SPIKE (500 VUs, 1 min)

| Metrica | Java 25 (VT) | Go 1.25 | Quarkus Native | Java vs Go | Java vs Quarkus | Go vs Quarkus |
| :--- | ---: | ---: | ---: | :--- | :--- | :--- |
| Latencia Media (ms) | 723.8 +/-3.1 | 353.6 +/-2.6 | 360.2 +/-5.2 | Go -51.1% | Quarkus -50.2% | Empate |
| Mediana p50 (ms) | 748.9 +/-3.0 | 353.3 +/-2.6 | 360.0 +/-3.8 | Go -52.8% | Quarkus -51.9% | Empate |
| p95 (ms) | 917.8 +/-3.1 | 488.4 +/-1.6 | 495.2 +/-5.0 | Go -46.8% | Quarkus -46.0% | Empate |
| p99 (ms) | 985.8 +/-60.9 | 504.8 +/-10.0 | 549.8 +/-70.8 | Go -48.8% | Quarkus -44.2% | Go -8.9% |
| Total Requests | 21610.3 +/-79.6 | 39176.0 +/-223.6 | 38607.3 +/-429.3 | Go +81.3% | Quarkus +78.7% | Empate |
| RPS (req/s) | 362.3 +/-1.4 | 655.3 +/-4.9 | 646.3 +/-6.2 | Go +80.8% | Quarkus +78.4% | Empate |
| Taxa de Erro (%) | 0.0 +/-0.0 | 0.2 +/-0.2 | 0.5 +/-0.5 | --- | --- | Go -211.5% |
| **RAM Pico (MB)**  | 1935.0 +/-1.6 MB | 78.1 +/-1.2 MB | 463.8 +/-33.2 MB | Go -96.0% | Quarkus -76.0% | Go -494.1% |
| **RAM Media (MB)** | 1930.8 +/-2.6 MB | 68.5 +/-3.7 MB | 347.3 +/-60.1 MB | Go -96.5% | Quarkus -82.0% | Go -407.2% |

