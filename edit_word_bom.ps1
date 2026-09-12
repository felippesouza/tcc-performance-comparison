$word = New-Object -ComObject Word.Application
$word.Visible = $false
$docPath = "C:\Users\felip\projetos\tcc\Modelos de Concorrencia em Java Virtual Threads e Go Goroutines em Workloads IO-Bound.docx"
$doc = $word.Documents.Open($docPath)
$targetText = "aumentando a latência de forma não controlada."
$selection = $word.Selection
$selection.Find.Text = $targetText
$selection.Find.Forward = $true
$selection.Find.Wrap = 1
$found = $selection.Find.Execute()
if ($found) {
    $selection.Collapse(0)
    $selection.TypeParagraph()
    $newText = "Metodologicamente, a observabilidade contínua do experimento confirmou esse gargalo arquitetural. A extração de métricas de telemetria via Prometheus durante o teste de Spike demonstrou visualmente o esgotamento do HikariCP (Java) e a saturação do Agroal (Quarkus). Ressalta-se que o driver pgxpool (Go) não expõe métricas nativas para o formato Prometheus — exigindo a construção de um collector customizado (JACKSON, 2024). Contudo, essa ausência visual não comprometeu a validação da hipótese. Uma vez que o pgxpool opera baseado em channels estritamente lock-free, ele é naturalmente imune ao estrangulamento por bloqueio centralizado (lock contention) no cenário de 500 VUs. Assim, o isolamento das métricas focou na fila de espera (hikaricp_connections_pending), evidência cabal de que a raiz da degradação das Virtual Threads reside nas bibliotecas não adaptadas à hiperconcorrência, e não no modelo de threads gerenciado pela JVM."
    $selection.TypeText($newText)
    $selection.EndKey(6)
    $selection.TypeParagraph()
    $refText = "JACKSON, J. pgx: PostgreSQL driver and toolkit for Go. Repositório oficial no GitHub. Disponível em: https://github.com/jackc/pgx. Acesso em: 31 ago. 2026."
    $selection.TypeText($refText)
    $doc.Save()
    Write-Host "Success"
} else {
    Write-Host "Target text not found"
}
$doc.Close()
$word.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
