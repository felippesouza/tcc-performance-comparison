# Relatório Final de Benchmark Local: Java 25 (VT) vs Go 1.25 (Goroutines)

**Data:** 10 de Março de 2026  
**Ambiente:** Local (Docker Desktop - Windows)  
**Infraestrutura:** PostgreSQL (max_connections=300), Redis (7-alpine), Mock API (Latência 200-500ms)  
**Cenário:** Estresse de Pagamentos em ambiente controlado.

## 📊 Tabela de Resultados

| Métrica | Java 25 (Virtual Threads) | Go 1.25 (Goroutines) | Veredito |
| :--- | :--- | :--- | :--- |
| **Throughput (RPS)** | 553.7 req/s | **772.3 req/s** | Go processou 39.5% mais requisições. |
| **Latência Média** | 178.4 ms | **99.1 ms** | Go foi 44.4% mais rápido na resposta média. |
| **Latência P95** | 702.8 ms | **450.2 ms** | Go manteve latência P95 36% menor. |
| **Pior Caso (Max)** | 1.91 s | **0.52 s** | Go foi muito mais consistente (menos jitter). |
| **Taxa de Erro** | **0.00%** | **0.00%** | Ambos demonstraram robustez industrial. |

## 🧠 Conclusões Técnicas para o TCC

### O Triunfo do Runtime Go
O Go 1.25 reafirma sua posição como runtime otimizado para alta concorrência. A integração nativa do scheduler com o `netpoller` permite que as Goroutines sejam suspensas e retomadas com um custo computacional extremamente baixo. A estabilidade da latência máxima (sub-600ms) indica um gerenciamento de memória superior em cenários de alta pressão de I/O.

### A Evolução da JVM
O Java 25, utilizando Virtual Threads, demonstrou ser uma alternativa viável e robusta ao Go. Embora possua uma latência média superior (overhead da JVM/JIT), a estabilidade de 0% de erro e o throughput de 550 RPS validam que a barreira histórica do Java para aplicações I/O bound foi quebrada. O aumento da latência máxima para 1.9s sugere que, embora as threads sejam eficientes, a gestão de recursos compartilhados (como heap e JIT) ainda introduz latência de cauda (tail latency) maior que a do Go.

## 🚀 Próximos Passos (GCP)
Os dados locais sugerem que o Go vencerá na GCP em termos de velocidade bruta, mas a margem pode diminuir com o JIT aquecido e CPUs dedicadas. O foco na GCP será:
1. Validar se o **Jitter** do Java diminui em ambiente Linux puro.
2. Comparar o **Footprint de Memória (RAM)** real via métricas do container.
3. Observar o comportamento do **ZGC Generacional** sob carga sustentada por 10+ minutos.

---
*Documento gerado para consolidação da pesquisa científica de TCC.*
