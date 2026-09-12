import win32com.client
import os

doc_path = r"C:\Users\felip\projetos\tcc\Modelos de Concorrencia em Java Virtual Threads e Go Goroutines em Workloads IO-Bound.docx"
word = win32com.client.Dispatch("Word.Application")
word.Visible = False

try:
    doc = word.Documents.Open(doc_path)
    selection = word.Selection
    
    target_text = "aumentando a latência de forma não controlada."
    selection.Find.Text = target_text
    selection.Find.Forward = True
    selection.Find.Wrap = 1 # wdFindContinue
    found = selection.Find.Execute()
    
    if found:
        selection.Collapse(0) # wdCollapseEnd
        selection.TypeParagraph()
        
        new_text = "Metodologicamente, a observabilidade contínua do experimento confirmou esse gargalo arquitetural. A extração de métricas de telemetria via Prometheus durante o teste de Spike demonstrou visualmente o esgotamento do HikariCP (Java) e a saturação do Agroal (Quarkus). Ressalta-se que o driver pgxpool (Go) não expõe métricas nativas para o formato Prometheus — exigindo a construção de um collector customizado (JACKSON, 2024). Contudo, essa ausência visual não comprometeu a validação da hipótese. Uma vez que o pgxpool opera baseado em channels estritamente lock-free, ele é naturalmente imune ao estrangulamento por bloqueio centralizado (lock contention) no cenário de 500 VUs. Assim, o isolamento das métricas focou na fila de espera (hikaricp_connections_pending), evidência cabal de que a raiz da degradação das Virtual Threads reside nas bibliotecas não adaptadas à hiperconcorrência, e não no modelo de threads gerenciado pela JVM."
        selection.TypeText(new_text)
        
        # Go to end of document
        selection.EndKey(6) # wdStory = 6
        selection.TypeParagraph()
        ref_text = "JACKSON, J. pgx: PostgreSQL driver and toolkit for Go. Repositório oficial no GitHub. Disponível em: https://github.com/jackc/pgx. Acesso em: 31 ago. 2026."
        selection.TypeText(ref_text)
        
        doc.Save()
        print("Success")
    else:
        print("Target text not found")
        
    doc.Close()
except Exception as e:
    print(f"Error: {e}")
finally:
    word.Quit()
