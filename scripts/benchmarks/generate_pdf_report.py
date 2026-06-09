# -*- coding: utf-8 -*-
import os
import subprocess
import sys

# ─────────────────────────────────────────────────────────────
# Conteúdo HTML seguindo estritamente as regras do template USP/Esalq
# ─────────────────────────────────────────────────────────────

HTML_CONTENT = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Resultados Preliminares TCC USP ESALQ</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Times+New+Roman&family=Inter:wght@400;500;600;700&display=swap');
        
        @page {
            size: A4;
            margin: 2.5cm 2.5cm 2.5cm 2.5cm;
            @bottom-right {
                content: counter(page);
                font-family: "Times New Roman", Times, serif;
                font-size: 10pt;
            }
        }
        
        body {
            font-family: "Times New Roman", Times, serif;
            color: #1a202c;
            line-height: 1.5;
            font-size: 11pt;
            margin: 0;
            padding: 0;
        }
        
        /* Cabeçalho do Artigo */
        .title-container {
            text-align: center;
            margin-top: 0.5cm;
            margin-bottom: 0.8cm;
        }
        
        .article-title {
            font-size: 16pt;
            font-weight: bold;
            text-transform: uppercase;
            line-height: 1.3;
            margin-bottom: 20px;
        }
        
        .authors {
            font-size: 11.5pt;
            margin-bottom: 40px;
        }
        
        .author-name {
            font-weight: 500;
        }
        
        /* Rodapé de afiliação na primeira página */
        .affiliations {
            font-size: 9pt;
            line-height: 1.4;
            border-top: 1px solid #cbd5e0;
            padding-top: 8px;
            margin-top: 50px;
            margin-bottom: 20px;
        }
        
        /* Seções */
        .section-title {
            font-size: 12pt;
            font-weight: bold;
            text-transform: uppercase;
            margin-top: 24px;
            margin-bottom: 12px;
            border-bottom: 1px solid #1a202c;
            padding-bottom: 4px;
        }
        
        .subsection-title {
            font-size: 11pt;
            font-weight: bold;
            margin-top: 16px;
            margin-bottom: 8px;
        }
        
        p {
            margin-top: 0;
            margin-bottom: 12px;
            text-indent: 1.25cm;
            text-align: justify;
        }
        
        .no-indent {
            text-indent: 0;
        }
        
        ul, ol {
            margin-top: 0;
            margin-bottom: 12px;
            padding-left: 2cm;
            text-align: justify;
        }
        
        li {
            margin-bottom: 4px;
        }
        
        /* Sumário / Resumo */
        .abstract-container {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 15px;
            margin-bottom: 25px;
        }
        
        .abstract-title {
            font-weight: bold;
            text-transform: uppercase;
            font-size: 11pt;
            margin-bottom: 8px;
            text-align: center;
        }
        
        .abstract-text {
            font-size: 10pt;
            text-indent: 0;
            text-align: justify;
        }
        
        .keywords {
            font-size: 10pt;
            margin-top: 10px;
            font-weight: bold;
        }
        
        .keywords-value {
            font-weight: normal;
        }
        
        /* Tabelas */
        .table-wrapper {
            margin-top: 15px;
            margin-bottom: 20px;
            page-break-inside: avoid;
        }
        
        .table-title {
            font-size: 9.5pt;
            font-weight: bold;
            margin-bottom: 6px;
            text-align: left;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 9pt;
        }
        
        th {
            border-top: 2px solid #000;
            border-bottom: 1px solid #000;
            padding: 6px 8px;
            font-weight: bold;
            text-align: left;
        }
        
        td {
            border-bottom: 1px solid #e2e8f0;
            padding: 6px 8px;
        }
        
        .table-footer {
            border-top: 2px solid #000;
        }
        
        .badge {
            font-weight: bold;
        }
        
        /* Quebra de página */
        .page-break {
            page-break-before: always;
        }
    </style>
</head>
<body>

    <!-- CABEÇALHO DA PRIMEIRA PÁGINA -->
    <div class="title-container">
        <div class="article-title">
            Modelos de Concorrência Java Virtual Threads e Go Goroutines em Workloads I/O-Bound
        </div>
        <div class="authors">
            <span class="author-name">Felippe Gustavo de Souza e Silva¹*</span>; 
            <span class="author-name">Prof. Marcos Jardel Henriques²</span>
        </div>
    </div>

    <!-- SUMÁRIO EXECUTIVO -->
    <div class="abstract-container">
        <div class="abstract-title">Resumo</div>
        <div class="abstract-text">
            Este trabalho apresenta uma análise comparativa preliminar de modelos de concorrência voltados a workloads I/O-bound, avaliando o desempenho de Java 25 (com Virtual Threads sob o Project Loom), Go 1.25 (com Goroutines nativas) e Quarkus Native (com OS Threads tradicionais 1:1) sob carga controlada. Os testes locais foram realizados em um processador Apple M4 utilizando o runtime Colima/Linux e a ferramenta k6 para simulação de carga de um Gateway de Pagamentos, integrado com banco de dados PostgreSQL, Redis para cache de idempotência e uma API externa simulando latências de 200 a 500ms. Os resultados demonstram equivalência de throughput e latência média até 200 VUs. No cenário de spike com 500 VUs, Go e Quarkus Native mantiveram o throughput máximo de ~650 req/s, enquanto Java apresentou degradação devido à contenção de lock interna no pool HikariCP. O footprint de memória do Go se manteve o mais eficiente (32 a 78 MB), seguido pelo Quarkus Native (55 a 464 MB) e por fim a JVM Java (789 a 1.935 MB).
        </div>
        <div class="keywords">
            Palavras-chave: <span class="keywords-value">Virtual Threads; Goroutines; Concorrência; Benchmark; I/O-Bound.</span>
        </div>
    </div>

    <!-- INTRODUÇÃO -->
    <div class="section-title">Introdução</div>
    <p>
        O desenvolvimento de sistemas corporativos modernos, em especial gateways de processamento de pagamentos, é caracterizado por cargas de trabalho predominantemente limitadas por operações de entrada e saída (I/O-bound). Tais sistemas dependem de chamadas frequentes a bancos de dados relacionais para escrita de transações, acessos a caches distribuídos para validação de idempotência e requisições HTTP para adquirentes financeiras externas de processamento de cartões de crédito. Historicamente, runtimes tradicionais utilizavam um modelo de concorrência baseado em mapeamento de threads de sistema operacional (1:1), em que cada requisição em trânsito bloqueava fisicamente uma thread de hardware. Sob alta concorrência, esse modelo consome recursos de memória expressivos devido à alocação estática de memória de pilha (stack) para cada thread.
    </p>
    <p>
        Para contornar o limite de escalabilidade das threads de SO, surgiram modelos de concorrência leve baseados no agendamento cooperativo em espaço de usuário (M:N). O runtime do Go implementou Goroutines desde sua concepção, em que milhares de tarefas leves são mapeadas em um pool enxuto de threads físicas. Em contrapartida, o ecossistema Java recentemente introduziu as Virtual Threads (Project Loom) no Java 21, evoluindo no Java 25 com o JEP 491, o qual mitigou o pinning de carrier threads ao lidar com blocos sincronizados. Surge, contudo, a necessidade de isolar se as disparidades históricas de consumo de memória decorrem do paradigma de threading ou do overhead do próprio runtime da JVM.
    </p>
    <p>
        O objetivo deste trabalho é comparar empiricamente o desempenho, o footprint de memória e a elasticidade sob carga limite dos modelos de concorrência M:N de Java 25 (Virtual Threads) e Go 1.25 (Goroutines), utilizando o Quarkus Native (OS Threads 1:1) como baseline de contraste para isolar o consumo de recursos da JVM e os impactos do bloqueio direto de threads.
    </p>

    <!-- METODOLOGIA -->
    <div class="section-title">Metodologia</div>
    
    <div class="subsection-title">Arquitetura da Solução e Local</div>
    <p>
        Construiu-se um Gateway de Pagamentos modular seguindo os conceitos de Clean Architecture. A lógica de negócio consistiu no recebimento de uma requisição de pagamento, na validação de sua duplicidade em cache, na persistência temporária com status pendente em banco de dados, no envio para processamento em adquirente externa e na atualização final da transação. 
    </p>
    <p>
        O ambiente experimental foi montado em um processador Apple M4 (4 vCPUs, 8 GB RAM) sobre o Colima/Linux em modo nativo ARM64, isolando-se recursos em contêineres Docker. Utilizou-se o PostgreSQL 16 (limite de 300 conexões) montado sobre <code>emptyDir</code> para simular a escrita e o Redis 7 para o cache de idempotência. Desenvolveu-se um simulador da API de adquirente em Go, programado para injetar latências uniformes de 200ms a 500ms por request.
    </p>

    <div class="page-break"></div>

    <div class="subsection-title">Protocolo de Isolamento Científico</div>
    <p>
        Definiu-se um protocolo rigoroso para garantir a isolabilidade estatística e evitar cache hits espúrios de testes sequenciais. Antes de cada rodada de simulação de carga, realizou-se a limpeza completa do cache Redis por meio do comando <code>redis-cli FLUSHALL</code>. O gerador de carga (ferramenta k6) foi programado para injetar chaves únicas por meio do header HTTP <code>X-Idempotency-Key</code> mapeado como <code>k6-vu${__VU}-iter${__ITER}</code>, forçando todas as conexões a percorrerem o fluxo completo de I/O de banco e chamada externa.
    </p>

    <div class="subsection-title">Modelos de Concorrência e Runtimes</div>
    <p>
        Configuraram-se três runtimes de teste sob premissas equivalentes de pool de conexões (200 conexões ativas):
    </p>
    <ol>
        <li><strong>Java 25:</strong> Compilado com OpenJDK 25, utilizando Spring Boot 3.5 com suporte nativo a Virtual Threads ativado (<code>spring.threads.virtual.enabled=true</code>), pool HikariCP (200 conexões) e Garbage Collector ZGC Generational.</li>
        <li><strong>Go 1.25:</strong> Desenvolvido com framework Gin, utilizando Goroutines nativas, driver <code>pgxpool</code> (200 conexões) e Garbage Collector padrão do Go.</li>
        <li><strong>Quarkus Native:</strong> Desenvolvido com Quarkus 3.15.1, compilado estaticamente em binário nativo via GraalVM Mandrel. Configurou-se pool Agroal (200 conexões), pool de cliente REST (600 conexões) e pool de threads do SO (600 threads).</li>
    </ol>
    <p>
        Executaram-se três cenários de teste controlados por round (três rodadas por cenário): **Baseline** (20 VUs, 2 minutos), **Stress** (200 VUs, ~2 minutos) e **Spike** (500 VUs, 1 minuto). O consumo de memória RAM do processo ativo foi coletado a cada 1 segundo por meio de scripts de estatística de sistema operacional.
    </p>

    <!-- RESULTADOS PRELIMINARES -->
    <div class="section-title">Resultados Preliminares</div>

    <div class="subsection-title">Desempenho e Latência sob Carga Moderada (Baseline &amp; Stress)</div>
    <p>
        Nas rodadas iniciais de 20 VUs e 200 VUs, observou-se uma convergência estatística quase perfeita entre os três modelos de concorrência concorrentes. A latência média manteve-se na faixa de 352ms a 358ms, correspondendo exatamente à média da latência de rede externa do simulador. O throughput das requisições atingiu ~24 req/s no baseline e ~342 req/s no teste de estresse para todos os backends, com taxa de erro em 0,00%, confirmando que até o limite físico de conexões de banco de dados, o paradigma de concorrência não influi no desempenho da entrega.
    </p>

    <div class="table-wrapper">
        <div class="table-title">Tabela 1. Resultados consolidados para o cenário de estresse (200 VUs)</div>
        <table>
            <thead>
                <tr>
                    <th>Backend</th>
                    <th>Latência Média</th>
                    <th>Mediana p50</th>
                    <th>Percentil p95</th>
                    <th>Throughput</th>
                    <th>RPS</th>
                    <th>Erros</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="badge">Java 25 (Virtual Threads)</span></td>
                    <td>353,4 ms &plusmn; 0,5</td>
                    <td>353,4 ms &plusmn; 0,6</td>
                    <td>488,4 ms &plusmn; 0,3</td>
                    <td>37.554 req</td>
                    <td>342,0 req/s</td>
                    <td>0,00%</td>
                </tr>
                <tr>
                    <td><span class="badge">Go 1.25 (Goroutines)</span></td>
                    <td>351,6 ms &plusmn; 0,2</td>
                    <td>351,8 ms &plusmn; 0,1</td>
                    <td>486,3 ms &plusmn; 0,3</td>
                    <td>37.702 req</td>
                    <td>343,4 req/s</td>
                    <td>0,00%</td>
                </tr>
                <tr>
                    <td><span class="badge">Quarkus Native (OS Threads)</span></td>
                    <td>353,5 ms &plusmn; 0,6</td>
                    <td>353,3 ms &plusmn; 0,8</td>
                    <td>488,5 ms &plusmn; 0,4</td>
                    <td>37.545 req</td>
                    <td>341,8 req/s</td>
                    <td>0,00%</td>
                </tr>
            </tbody>
            <tfoot>
                <tr class="table-footer"><td colspan="7">Nota: Valores representam média &plusmn; desvio padrão para N=3 rodadas experimentais.</td></tr>
            </tfoot>
        </table>
    </div>

    <div class="subsection-title">Comportamento de Elasticidade sob Carga Extrema (Spike)</div>
    <p>
        No cenário de spike (500 VUs concorrentes disputando 200 conexões de banco de dados), observou-se a divergência dos runtimes. Go e Quarkus mantiveram a performance estável de vazão máxima, entregando ~650 RPS com latência média estável de ~353ms (p95 de ~488ms). Em contraste, o Java sofreu severa degradação, limitando-se a 362 RPS com latência média dobrada para 723,8ms (p95 de 917,8ms).
    </p>
    <p>
        O monitoramento interno da JVM confirmou que a degradação do Java não decorreu de bloqueio de carrier threads (zero eventos registrados com JEP 491). A causa raiz identificada foi a contenção de lock interna do pool de conexões **HikariCP**, que utiliza o bloco sincronizado (<code>synchronized</code>) como ponto único de serialização de controle das conexões ativas e em espera. Sob 500 Virtual Threads em concorrência extrema por conexões de banco, essa serialização gerou gargalo cumulativo de enfileiramento. Go (com pgxpool usando canais concorrentes lock-free) e Quarkus Native (com pool Agroal reestruturado) mantiveram a entrega sem pontos de serialização crítica.
    </p>

    <div class="page-break"></div>

    <div class="table-wrapper">
        <div class="table-title">Tabela 2. Resultados consolidados para o cenário de spike (500 VUs)</div>
        <table>
            <thead>
                <tr>
                    <th>Backend</th>
                    <th>Latência Média</th>
                    <th>Mediana p50</th>
                    <th>Percentil p95</th>
                    <th>Throughput</th>
                    <th>RPS</th>
                    <th>Erros</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="badge">Java 25 (Virtual Threads)</span></td>
                    <td>723,8 ms &plusmn; 3,1</td>
                    <td>748,9 ms &plusmn; 3,0</td>
                    <td>917,8 ms &plusmn; 3,1</td>
                    <td>21.610 req</td>
                    <td>362,3 req/s</td>
                    <td>0,00%</td>
                </tr>
                <tr>
                    <td><span class="badge">Go 1.25 (Goroutines)</span></td>
                    <td>353,6 ms &plusmn; 2,6</td>
                    <td>353,3 ms &plusmn; 2,6</td>
                    <td>488,4 ms &plusmn; 1,6</td>
                    <td>39.176 req</td>
                    <td>655,3 req/s</td>
                    <td>0,14%</td>
                </tr>
                <tr>
                    <td><span class="badge">Quarkus Native (OS Threads)</span></td>
                    <td>360,2 ms &plusmn; 5,2</td>
                    <td>360,0 ms &plusmn; 3,8</td>
                    <td>495,2 ms &plusmn; 5,0</td>
                    <td>38.607 req</td>
                    <td>646,3 req/s</td>
                    <td>0,50%</td>
                </tr>
            </tbody>
            <tfoot>
                <tr class="table-footer"><td colspan="7">Nota: Valores representam média &plusmn; desvio padrão para N=3 rodadas experimentais.</td></tr>
            </tfoot>
        </table>
    </div>

    <div class="subsection-title">Footprint de Memória RAM (JVM vs Binário Nativo)</div>
    <p>
        As medições de consumo de memória RAM RSS (Resident Set Size) permitiram isolar cientificamente as causas do consumo de hardware:
    </p>
    <ol>
        <li>O **Java em modo JVM** consumiu de 789 MB (Baseline) a 1.935 MB (Spike), devido ao overhead de inicialização, áreas de controle como Metaspace (estruturas de classe Spring) e do mecanismo de compilação dinâmica JIT.</li>
        <li>O **Quarkus Native (AOT)** validou que o consumo de memória do ecossistema Java provém majoritariamente da JVM e não da linguagem, apresentando consumo inicial de apenas 55,5 MB. Sob spike (500 VUs com 600 threads alocadas), o consumo subiu para 463,8 MB devido ao custo de stack fixo das threads do sistema operacional 1:1 (~512KB por stack ativado).</li>
        <li>O **Go 1.25** demonstrou a maior eficiência de memória, consumindo apenas 32,4 MB em baseline e subindo a no máximo 78,1 MB no pico de carga (500 VUs), tirando proveito da stack dinâmica inicial de ~2KB por Goroutine concorrente.</li>
    </ol>

    <!-- CONCLUSÃO -->
    <div class="section-title">Conclusão(ões) ou Considerações Finais</div>
    <p>
        Os resultados preliminares comprovam que Java Virtual Threads e Go Goroutines entregam desempenho equivalente em throughput e latência em cargas moderadas de trabalho I/O-bound. Contudo, em situações de concorrência extrema e disputas por pools finitos, a maturidade de bloqueio concorrente nas bibliotecas de ecossistema (como o HikariCP no Java) torna-se o principal fator limitador, e não o runtime do Loom em si. A compilação nativa em Quarkus comprovou que a linguagem Java é competitiva em memória se isolada da JVM, porém evidenciou o custo do modelo tradicional 1:1 de threads sob alta simultaneidade em comparação com a stack enxuta e dinâmica das Goroutines em Go. Os testes subsequentes em ambiente de nuvem GKE estenderão essas análises sob a ótica econômica de custo operacional real por RPS.
    </p>

    <!-- AGRADECIMENTOS -->
    <div class="section-title">Agradecimentos</div>
    <p class="no-indent">
        O autor agradece ao Prof. Marcos Jardel Henriques pela orientação acadêmica e pelo apoio técnico fornecido nas revisões dos relatórios de benchmarks locais e nos planos de testes do ambiente em nuvem.
    </p>

    <!-- REFERÊNCIAS -->
    <div class="section-title">Referências</div>
    <ol class="no-indent" style="list-style-type: none; padding-left: 0;">
        <li style="margin-bottom: 8px; text-indent: -1cm; padding-left: 1cm;">GO CORE TEAM. <strong>Go Runtime Scheduler</strong>. Versão 1.25. Disponível em: &lt;https://go.dev&gt;. Acesso em: 10 mar. 2026.</li>
        <li style="margin-bottom: 8px; text-indent: -1cm; padding-left: 1cm;">ORACLE. <strong>JEP 491: Key Platform Threads in synchronized</strong>. Java Development Kit (JDK) 25. Redwood City: Oracle Corporation, 2026.</li>
        <li style="margin-bottom: 8px; text-indent: -1cm; padding-left: 1cm;">RED HAT. <strong>Quarkus - GraalVM Mandrel Native Integration</strong>. Versão 3.15.1. Raleigh: Red Hat Inc., 2025.</li>
        <li style="margin-bottom: 8px; text-indent: -1cm; padding-left: 1cm;">SPRING TEAM. <strong>Spring Boot 3.5: Virtual Threads Configuration Guide</strong>. Palo Alto: VMware Tanzu, 2026.</li>
    </ol>

    <!-- AFILIAÇÕES DE RODAPÉ (PRIMEIRA PÁGINA) -->
    <div class="affiliations">
        ¹ Especializando em Engenharia da Computação. USP/Esalq, Piracicaba - SP. *E-mail autor correspondente: felippe-gustavo@hotmail.com<br>
        ² Doutor em Engenharia de Software. Orientador USP/Esalq, Piracicaba - SP. E-mail: marcos.henriques@usp.br
    </div>

</body>
</html>
"""

def generate_pdf():
    # Caminhos absolutos
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tcc_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))
    
    local_bench_dir = os.path.join(tcc_dir, "results", "local_benchmarks")
    if not os.path.exists(local_bench_dir):
        os.makedirs(local_bench_dir)
        
    html_path = os.path.join(local_bench_dir, "report_temp.html")
    pdf_path = os.path.join(local_bench_dir, "TCC_RESULTADOS_PRELIMINAR_TESE.pdf")
    
    # Escreve o arquivo HTML temporário
    print(f"Escrevendo arquivo HTML em: {html_path}")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
        
    # Caminho padrão do Microsoft Edge no Windows
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    if not os.path.exists(edge_path):
        print(f"Erro: O executavel do Edge nao foi encontrado em {edge_path}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Chamando o Edge para compilar o HTML em PDF...")
    # Executa o Edge headless para imprimir como PDF
    cmd = [
        edge_path,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={pdf_path}",
        html_path
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\nPDF gerado com sucesso!")
        print(f"Caminho do PDF: {pdf_path}")
    except Exception as e:
        print(f"Erro ao compilar o PDF via Edge: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Limpa o HTML temporário
        if os.path.exists(html_path):
            os.remove(html_path)

if __name__ == "__main__":
    generate_pdf()
