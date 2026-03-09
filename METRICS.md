# Estratégia de Observabilidade e Métricas (TCC)

Este documento descreve como realizar a medição de performance para a comparação entre Java 25 e Go.

## Endpoints de Monitoramento (Java)

- **Swagger UI:** `http://localhost:8081/swagger-ui.html` (Para documentação dos contratos)
- **Prometheus Metrics:** `http://localhost:8081/actuator/prometheus` (Dados brutos para o Grafana)
- **Health Check:** `http://localhost:8081/actuator/health`

## Métricas Chave para a Pesquisa

Para a monografia, foque nos seguintes indicadores extraídos do Actuator:

1.  **JVM Virtual Threads:**
    - `jvm.threads.live` vs `jvm.threads.peak`: Monitore se o número de threads do sistema operacional se mantém baixo enquanto o throughput sobe.
2.  **Latência de I/O (Onde o Loom brilha):**
    - `http.server.requests.seconds_max`: Mede o tempo máximo de resposta sob carga.
    - `http.server.requests.seconds_avg`: Mede a latência média.
3.  **Consumo de Recursos (GKE):**
    - `process.cpu.usage`: Percentual de CPU consumido por requisição.
    - `jvm.memory.used`: Memória Heap utilizada (comparar com o footprint do Go).

## Configuração do Experimento Científico

Para garantir a validade dos dados:
1.  **Aquecimento (Warm-up):** Rodar o teste por 2 minutos antes de coletar os dados reais (devido ao JIT do Java).
2.  **Carga Constante:** Usar o k6 para manter uma taxa fixa de requisições por segundo (ex: 500 RPS).
3.  **Ambiente Isolado:** Rodar cada backend individualmente no GKE com `resource limits` idênticos.
