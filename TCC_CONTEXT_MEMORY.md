# 🧠 Memory — TCC Felippe Gustavo (Sessão 16/06/2026)

## Contexto Acadêmico

| Campo | Valor |
|---|---|
| **Curso** | MBA em Engenharia de Software — USP/Esalq |
| **Turmas** | 251 / 252 |
| **Estudante** | Felippe Gustavo de Souza e Silva |
| **Orientador** | Prof. Marcos Jardel Henriques |
| **E-mail estudante** | felippe-gustavo@hotmail.com |
| **E-mail orientador** | marcos.henriques@usp.br |
| **Contato TCC** | tccsoftware@mbauspesalq.com |

## Identificação Institucional (Folha de Rosto)

```
¹ Especializando em Engenharia de Software.
  Instituto de Ciências Matemáticas e de Computação da Universidade de São Paulo (ICMC/USP).
  Centro de Pesquisa, Inovação e Difusão do Centro de Ciências Matemáticas Aplicadas à Indústria (CEPID-CeMEAI).
  Av. Trab. São Carlense, 400 — Parque Arnold Schmidt; 13566-590 São Carlos, SP, Brasil.
  *Autor correspondente: felippe-gustavo@hotmail.com

² Doutor em Estatística. Orientador USP/Esalq, Piracicaba — SP.
  E-mail: marcos.henriques@usp.br
```

---

## Arquivos do TCC

```
results/local_benchmarks/
  ├── TCC_RESULTADOS_PRELIMINAR_TESE.pdf   ← versão original entregue ao orientador
  ├── TCC_RELATORIO_PRELIMINAR_LOCAL.pdf   ← relatório de benchmark local
  ├── TCC_RESULTADOS_CORRIGIDOS.docx       ← versão corrigida (ENTREGA PRÓXIMA ETAPA)
  └── gera_tcc.py                          ← script Python que gera o .docx
```

### Como regenerar o DOCX após edições
```powershell
C:\python\python.exe "results\local_benchmarks\gera_tcc.py"
```

### Manual de normas
```
C:\Users\felip\Downloads\Manual de Instruções e Normas para Trabalhos de Conclusão de Curso (251, 252).pdf
```

---

## Correções aplicadas (feedback do orientador — 16/06/2026)

### Página inicial
- Endereço completo: ICMC/USP + CEPID-CeMEAI + Av. São Carlense, 400

### Introdução — 3 referências inseridas + parágrafo final de estrutura
| Citação | Papel |
|---|---|
| Goetz et al. (2006) — *Java Concurrency in Practice* | Contextualiza modelo 1:1 de threads |
| Pike (2012) — Go Concurrency Patterns | Fundamenta Goroutines |
| Xu et al. (2021) — ACM TIT | Benchmark de microsserviços I/O-bound |

### Metodologia — 4 subtítulos, 7 referências
| Subtítulo | Referências |
|---|---|
| Arquitetura da Solução e Ambiente Experimental | Martin (2017) |
| Protocolo de Isolamento Científico | Iosup et al. (2011), Grafana Labs (2024) |
| Modelos de Concorrência e Configuração dos Runtimes | Pressler e Bateman (2023), Pike (2012), Red Hat (2025) |
| Cenários de Teste e Métricas Coletadas | Jain (1991) |

### Resultados e Discussão
- Renomeado de "Resultados" para "Resultados e Discussão"
- Tabela 1 e Tabela 2 com título e `Fonte: O próprio autor`
- 4 parágrafos de discussão: Xu et al. (2021), Curino et al. (2020), Arora et al. (2023)

### Referências — de 4 para 14 (formato USP/Esalq)

---

## Resultados Científicos

### Cenário Stress — 200 VUs

| Backend | Latência Média | p95 | RPS | Erros |
|---|---|---|---|---|
| Java 25 (Virtual Threads) | 353,4 ms ± 0,5 | 488,4 ms ± 0,3 | 342,0 | 0,00% |
| Go 1.25 (Goroutines) | 351,6 ms ± 0,2 | 486,3 ms ± 0,3 | 343,4 | 0,00% |
| Quarkus Native (OS Threads) | 353,5 ms ± 0,6 | 488,5 ms ± 0,4 | 341,8 | 0,00% |

### Cenário Spike — 500 VUs

| Backend | Latência Média | p95 | RPS | Erros |
|---|---|---|---|---|
| Java 25 (Virtual Threads) | 723,8 ms ± 3,1 | 917,8 ms ± 3,1 | 362,3 | 0,00% |
| Go 1.25 (Goroutines) | 353,6 ms ± 2,6 | 488,4 ms ± 1,6 | 655,3 | 0,14% |
| Quarkus Native (OS Threads) | 360,2 ms ± 5,2 | 495,2 ms ± 5,0 | 646,3 | 0,50% |

### Memória RAM (RSS)

| Runtime | Baseline | Spike |
|---|---|---|
| Java JVM | 789 MB | 1.935 MB |
| Quarkus Native (AOT) | 55,5 MB | 463,8 MB |
| Go 1.25 | 32,4 MB | 78,1 MB |

### Causa raiz da degradação do Java no Spike
- **NÃO** foi pinning de carrier threads (JEP 491 — zero eventos registrados)
- **FOI** contenção de lock interno do **HikariCP** (`synchronized`) sob 500 VTs disputando 200 conexões

---

## Pendências para a Versão Final

1. **Gráficos/figuras** — inserir com `Figura N.` + `Fonte: Resultados originais da pesquisa`
2. **Resultados GKE** — executar testes em nuvem e adicionar análise de custo por RPS
3. **Verificar referências** de Arora et al. (2023) e Xu et al. (2021) — confirmar vol/num/páginas
4. **Abstract em inglês** (opcional, mas recomendado)
5. **Checklist final** do manual (pp. 56–57) — verificar 21 itens antes de submeter no MBX

---

## Normas USP/Esalq aplicadas (Manual pp. 34–45)

- Fonte Arial 11, espaçamento 1,5, recuo 1,25 cm, margens 2,5 cm
- Tabelas: título acima, fonte abaixo
- Citações: estilo `autor, ano`, apenas indiretas
- Referências: formato `Autor. Ano. Título. Periódico vol(num): págs.`
- Introdução: máx. 2 páginas; objetivo no último parágrafo
- Metodologia: tempo pretérito perfeito, forma impessoal
- Resultados e Discussão: subtítulos iguais aos da Metodologia
