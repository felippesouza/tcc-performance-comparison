# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
section = doc.sections[0]
section.top_margin = Cm(2.5)
section.bottom_margin = Cm(2.5)
section.left_margin = Cm(2.5)
section.right_margin = Cm(2.5)
section.page_width = Cm(21)
section.page_height = Cm(29.7)

def add_paragraph(doc, text='', bold=False, italic=False, size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, font='Arial', first_line_indent=1.25, space_before=0, space_after=0):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    if first_line_indent: pf.first_line_indent = Cm(first_line_indent)
    if space_before: pf.space_before = Pt(space_before)
    if space_after: pf.space_after = Pt(space_after)
    pf.line_spacing = Pt(size * 1.5)
    if text:
        run = p.add_run(text)
        run.bold, run.italic, run.font.name, run.font.size = bold, italic, font, Pt(size)
    return p

def add_heading(doc, text, size=11, font='Arial'):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.first_line_indent, pf.space_before, pf.space_after, pf.line_spacing = Cm(0), Pt(11), Pt(0), Pt(11 * 1.5)
    run = p.add_run(text)
    run.bold, run.font.name, run.font.size = True, font, Pt(size)
    return p

def add_subheading(doc, text, size=11, font='Arial'):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.first_line_indent, pf.space_before, pf.space_after, pf.line_spacing = Cm(1.25), Pt(6), Pt(0), Pt(size * 1.5)
    run = p.add_run(text)
    run.bold, run.font.name, run.font.size = True, font, Pt(size)
    return p

def add_table_data(doc, title, headers, rows):
    p_h = doc.add_paragraph()
    p_h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p_h.paragraph_format
    pf.first_line_indent, pf.space_before, pf.space_after = Cm(0), Pt(8), Pt(4)
    run = p_h.add_run(title)
    run.font.name, run.font.size = 'Arial', Pt(11)
    
    table = doc.add_table(rows=len(rows)+1, cols=len(headers))
    table.style = 'Table Grid'
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.paragraphs[0].runs[0].bold, cell.paragraphs[0].runs[0].font.name, cell.paragraphs[0].runs[0].font.size = True, 'Arial', Pt(10)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.cell(i+1, j)
            cell.text = str(val)
            if cell.paragraphs[0].runs:
                cell.paragraphs[0].runs[0].font.name, cell.paragraphs[0].runs[0].font.size = 'Arial', Pt(10)
                
    p_f = doc.add_paragraph()
    p_f.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf_f = p_f.paragraph_format
    pf_f.first_line_indent, pf_f.space_before, pf_f.space_after = Cm(0), Pt(2), Pt(8)
    r_f = p_f.add_run('Fonte: O próprio autor')
    r_f.font.name, r_f.font.size = 'Arial', Pt(11)

# CAPA
p_titulo = doc.add_paragraph()
p_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_titulo.paragraph_format.space_after = Pt(6)
run = p_titulo.add_run('MODELOS DE CONCORRÊNCIA EM JAVA VIRTUAL THREADS E GO GOROUTINES EM WORKLOADS IO-BOUND')
run.bold, run.font.name, run.font.size = True, 'Arial', Pt(12)

p_aut = doc.add_paragraph()
p_aut.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_aut.paragraph_format.space_before, p_aut.paragraph_format.space_after = Pt(6), Pt(4)
r1 = p_aut.add_run('Felippe Gustavo de Souza e Silva')
r1.font.name, r1.font.size = 'Arial', Pt(11)
r_s1 = p_aut.add_run('1*')
r_s1.font.name, r_s1.font.size, r_s1.font.superscript = 'Arial', Pt(9), True
r_sep = p_aut.add_run('; Prof. Marcos Jardel Henriques')
r_sep.font.name, r_sep.font.size = 'Arial', Pt(11)
r_s2 = p_aut.add_run('2')
r_s2.font.name, r_s2.font.size, r_s2.font.superscript = 'Arial', Pt(9), True

p_e = doc.add_paragraph()
p_e.alignment, p_e.paragraph_format.space_before = WD_ALIGN_PARAGRAPH.LEFT, Pt(4)
r_e1 = p_e.add_run('1 Especializando em Engenharia de Software (ICMC/USP). felippe-gustavo@hotmail.com\n2 Doutor em Estatística. Orientador USP/Esalq.')
r_e1.font.name, r_e1.font.size = 'Arial', Pt(9)

add_heading(doc, 'Resumo')
add_paragraph(doc, 'Este trabalho apresenta uma análise comparativa quantitativa rigorosa entre modelos de concorrência em workloads I/O-bound: Java 25 (Virtual Threads), Go 1.25 (Goroutines) e Quarkus Native (OS Threads). A pesquisa cruzou dados de uma Fase 1 (ambiente local ARM64) e uma Fase 2 (Nuvem GKE X86_64) simulando um Gateway de Pagamentos. Os resultados comprovam empiricamente a superioridade do Java no processamento de carga contínua aquecida (Stress 200 VUs) atingindo 290 RPS com latência p95 de 670ms. No entanto, sob choques abruptos (Spike 500 VUs), a arquitetura Ahead-of-Time do Go provou-se inigualável, entregando 274 RPS enquanto o Java decaiu para 144 RPS com latências extremas devido à contenção de lock no pool de banco. No critério FinOps, o consumo de RAM do Go (75 MB pico) representa uma economia colossal comparado à JVM (733 MB), consagrando-o como a solução ótima para nuvem elástica.', first_line_indent=0)

doc.add_page_break()
add_heading(doc, 'Introdução')
add_paragraph(doc, 'A avaliação de arquiteturas Cloud-Native requer precisão matemática sobre latência de cauda e uso de memória. Sistemas I/O-bound sofrem limitações inerentes aos bloqueios de rede e banco de dados. Este estudo confronta as recentes Virtual Threads do Java 25 com o modelo estabelecido de Goroutines em Go, utilizando Quarkus Native como baseline metodológico.')

add_heading(doc, 'Metodologia (Fase 1 e Fase 2)')
add_paragraph(doc, 'As execuções foram divididas em ambiente de hardware Apple M4 (Fase Local) e cluster gerenciado Google Kubernetes Engine GKE (Fase Nuvem). Garantiu-se rigor científico purgando caches do Redis (FLUSHALL) a cada nova iteração e isolando os pods de estresse K6 na mesma rede virtual.')

add_heading(doc, 'Resultados e Discussão')
add_subheading(doc, 'Fase 1: Ambiente Local (ARM64)')
add_paragraph(doc, 'Os resultados no processador Apple M4 estabeleceram o limite estrutural dos frameworks sem latência de internet, evidenciando o colapso do Java sob tráfego excessivo (Spike) decorrente do lock no HikariCP.')

add_table_data(doc, 'Tabela 1. Resultados Locais (Apple M4) - Cenário STRESS (200 VUs)',
    ['Backend', 'Latência Média', 'Latência p95', 'Throughput RPS', 'Erros'],
    [
        ['Java (Virtual Threads)', '353,4 ms', '488,4 ms', '342,0 req/s', '0,00%'],
        ['Go (Goroutines)', '351,6 ms', '486,3 ms', '343,4 req/s', '0,00%'],
        ['Quarkus (OS Threads)', '353,5 ms', '488,5 ms', '341,8 req/s', '0,00%']
    ]
)

add_table_data(doc, 'Tabela 2. Resultados Locais (Apple M4) - Cenário SPIKE (500 VUs)',
    ['Backend', 'Latência Média', 'Latência p95', 'Throughput RPS', 'Erros'],
    [
        ['Java (Virtual Threads)', '723,8 ms', '917,8 ms', '362,3 req/s', '0,00%'],
        ['Go (Goroutines)', '353,6 ms', '488,4 ms', '655,3 req/s', '0,14%'],
        ['Quarkus (OS Threads)', '360,2 ms', '495,2 ms', '646,3 req/s', '0,50%']
    ]
)

add_subheading(doc, 'Fase 2: Ambiente em Nuvem (Google Kubernetes Engine)')
add_paragraph(doc, 'A migração para a nuvem revelou a eficácia do JIT Compiler do Java sob carga aquecida (Stress), mas expôs de forma drástica o seu déficit elástico no *Cold-Start* (Spike).')

add_table_data(doc, 'Tabela 3. Resultados Nuvem (GKE) - Cenário STRESS (200 VUs contínuos)',
    ['Backend', 'Latência Média', 'Latência p95', 'Throughput RPS', 'Erros'],
    [
        ['Java (Virtual Threads)', '435,7 ms', '670,5 ms', '290,0 req/s', '0,00%'],
        ['Go (Goroutines)', '486,5 ms', '1095,1 ms', '263,8 req/s', '0,00%'],
        ['Quarkus (OS Threads)', '979,5 ms', '1650,1 ms', '142,6 req/s', '0,00%']
    ]
)

add_table_data(doc, 'Tabela 4. Resultados Nuvem (GKE) - Cenário SPIKE (500 VUs imediatos)',
    ['Backend', 'Latência Média', 'Latência p95', 'Throughput RPS', 'Erros'],
    [
        ['Java (Virtual Threads)', '1997,8 ms', '4208,9 ms', '144,0 req/s', '0,00%'],
        ['Go (Goroutines)', '975,4 ms', '1365,0 ms', '274,4 req/s', '0,00%'],
        ['Quarkus (OS Threads)', '1555,6 ms', '2286,0 ms', '180,9 req/s', '0,00%']
    ]
)

add_subheading(doc, 'FinOps e Densidade de Memória')
add_paragraph(doc, 'A métrica vital para dimensionamento econômico na nuvem é o footprint de RAM (RSS). A tabela a seguir quantifica o custo computacional exigido para sustentar o cenário extremo (Spike). A discrepância entre as stacks demonstra o benefício inquestionável do modelo AOT do Go.')

add_table_data(doc, 'Tabela 5. Consumo Físico de RAM no cluster GKE (FinOps)',
    ['Backend', 'RAM Média', 'RAM Pico Máximo', 'Vantagem do Go vs Concorrente'],
    [
        ['Java (Virtual Threads)', '668 MB', '733 MB', 'Go consome 89% a menos de RAM no pico'],
        ['Go (Goroutines)', '43 MB', '75 MB', '--- Baseline Ótimo ---'],
        ['Quarkus (OS Threads)', '163 MB', '305 MB', 'Go consome 75% a menos de RAM no pico']
    ]
)

add_heading(doc, 'Conclusão')
add_paragraph(doc, 'Os dados extraídos em ambiente GKE isolado comprovam que o Java 25 maximiza o throughput em operações de estresse estável, mas falha gravemente no quesito elasticidade. A contenção no driver de banco (HikariCP) e os altos custos da JVM (733 MB RAM, P95 > 4s) tornam a linguagem vulnerável a choques de rede. O ecossistema Go (Goroutines e pgxpool) mostrou-se inigualável para cargas dinâmicas em Serverless/K8s, estabilizando 274 RPS no Spike com míseros 75 MB de RAM. Conclui-se que o Go oferece a melhor equação FinOps para arquiteturas contemporâneas de meios de pagamento.')

output_path = r'C:\Users\felip\projetos\tcc\Modelos de Concorrencia em Java Virtual Threads e Go Goroutines em Workloads IO-Bound.docx'
doc.save(output_path)
print(f'Documento final gerado!')
