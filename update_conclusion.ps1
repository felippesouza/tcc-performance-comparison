$word = New-Object -ComObject Word.Application
$word.Visible = $false
$docPath = "C:\Users\felip\projetos\tcc\Modelos de Concorrencia em Java Virtual Threads e Go Goroutines em Workloads IO-Bound.docx"
$doc = $word.Documents.Open($docPath)
$selection = $word.Selection
$selection.Find.Text = "A pesquisa conclui de maneira definitiva"
$selection.Find.Forward = $true
$selection.Find.Wrap = 1
$found = $selection.Find.Execute()
if ($found) {
    $selection.Expand(4)
    $newText = "A pesquisa conclui de maneira definitiva que os modelos de concorrência impactam severamente a resiliência de workloads I/O-bound em produção. Em ambientes estáveis de concorrência moderada, as Virtual Threads do Java (Project Loom) provaram ter superado a lacuna histórica de escalabilidade da linguagem, maximizando o throughput e, sob o aquecimento ideal do JIT Compiler, chegando a superar o desempenho absoluto do Go. No entanto, a arquitetura moderna baseada em Kubernetes (Serverless/Elástica) exige rápida estabilização frente a choques de tráfego. Neste contexto de elasticidade (Spike), o Java ainda decai criticamente devido a gargalos em bibliotecas legadas de sincronização (ex: pool HikariCP) e penalidades do Cold-Start. O ecossistema Go (Goroutines e canais lock-free), aliado à sua compilação AOT nativa, provou ser inquestionavelmente mais elástico e economicamente sustentável (FinOps), consumindo frações da memória exigida pela JVM (75 MB vs 733 MB) para suportar cargas absolutas superiores, sendo a solução ideal para Gateways de Pagamento."
    $selection.TypeText($newText)
    Write-Host "Success"
} else {
    Write-Host "Text not found"
}
$doc.Save()
$doc.Close()
$word.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
