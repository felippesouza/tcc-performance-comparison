# Relatório de Benchmark Local: Java 25 (VT) vs Go 1.25 (Goroutines)

**Data:** 10 de Março de 2026  
**Ambiente:** Local (Docker Desktop - Windows)  
**Cenário:** Estresse de Pagamentos (I/O Bound: Postgres + Redis + API Externa)  
**Carga:** 200 Usuários Simultâneos (VUs) por 110 segundos.

## 📊 Quadro Comparativo

| Métrica | Java 25 (Virtual Threads) | Go 1.25 (Goroutines) | Veredito Técnico |
| :--- | :--- | :--- | :--- |
| **Throughput (RPS)** | 553.7 req/s | **811.1 req/s** | Go é ~46% mais veloz em vazão bruta. |
| **Latência Média** | 178.4 ms | **89.2 ms** | Go responde 50% mais rápido em média. |
| **Latência P95** | 702.8 ms | **578.2 ms** | Ambos passaram no threshold (< 800ms). |
| **Taxa de Erro** | **0.00%** | 31.07% | Java demonstrou estabilidade superior. |
| **Conexões DB (Pool)** | 200 | 200 | Configuração simétrica. |

## 🧠 Análise Crítica

### Java 25 (Virtual Threads / Project Loom)
O Java demonstrou uma maturidade impressionante com o **ZGC Generacional**. Mesmo sob carga pesada, o sistema não apresentou falhas de conexão ou erros de aplicação. O enfileiramento de requisições foi gerenciado de forma graciosa, mantendo a integridade de todas as transações de pagamento. É a escolha ideal para sistemas onde a **consistência** é mandatória.

### Go 1.25 (Goroutines)
O Go provou ser uma "máquina de performance". A latência média de sub-100ms em um cenário complexo de I/O aninhado reafirma a eficiência do scheduler nativo. No entanto, o alto índice de erros (31%) sugere que o Go saturou os recursos do Sistema Operacional (File Descriptors ou Sockets) muito antes do Java. Para a produção (GCP), será necessário tunar os limites do kernel para suportar a agressividade do Go.

## 🚀 Próximos Passos para o TCC
1. **Ambiente Limpo (GCP):** Repetir este teste em instâncias e2-standard-4 isoladas para eliminar o ruído do Windows.
2. **Resource Monitoring:** Analisar os logs de CPU/Memória exportados pelo Prometheus para correlacionar o custo energético de cada RPS.
3. **OS Tuning:** Aumentar `ulimit` no container do Go para verificar se a taxa de erro cai.

---
*Relatório gerado automaticamente para fins de documentação científica.*
