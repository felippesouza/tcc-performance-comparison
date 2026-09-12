# Konoha + RPI+R — V2
## Novo fluxo de trabalho dentro de um Konoha já existente e operacional

> **Objetivo:** orientar o Codex responsável pelo Konoha do trabalho a incorporar o RPI+R como um **novo fluxo de trabalho dentro do Konoha**, sem reconstruir, duplicar ou substituir os mecanismos que já existem.
>
> **Contexto:** este Konoha já nasceu no ambiente de trabalho, está em uso e possui uma infraestrutura própria de orquestração, governança, observabilidade e dashboard. O RPI+R deve ser assimilado a essa implementação existente.
>
> **Regra principal:** o objetivo não é criar "um Konoha + RPI+R" como dois sistemas separados. O objetivo é fazer o **Konoha ganhar o fluxo RPI+R**, reutilizando a infraestrutura existente sempre que possível.

---
# Ajuste V3 — Konoha do trabalho como infraestrutura madura

Esta versão incorpora uma observação importante sobre a implementação real do Konoha do trabalho: ele já possui uma camada operacional e de observabilidade significativamente mais madura do que um Harness inicial.

O Konoha existente já apresenta, entre outros elementos observáveis:

- Grafo de memória/conhecimento;
- Métricas de uso e execução;
- Qualidade e indicadores de verificação;
- Uso de ferramentas e subagentes;
- erros por ferramenta;
- sessões, tokens e thinking blocks;
- dispatches de subagentes;
- qualidade de memória, recall e proveniência;
- vereditos e julgamento;
- sinais de aprendizado;
- WIP;
- Patch Notes;
- regras, ranks, delegation e outros elementos de governança.

Portanto, a integração do RPI+R deve partir de uma premissa ainda mais forte:

> **O Konoha já é a infraestrutura operacional. O RPI+R é um novo workflow que roda sobre essa infraestrutura.**

O objetivo não é reproduzir no RPI+R aquilo que o Konoha já sabe observar, governar ou exibir.

A relação desejada é:

```text
                    KONOHA
        infraestrutura + governança
                 + observabilidade
                         │
                         │
                         ▼
                      RPI+R
             workflow de mudança
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Research         Plan       Implement
                                          │
                                          ▼
                                       Review
```

O RPI+R deve consumir os mecanismos existentes do Konoha sempre que possível.

---

---

# 1. Visão central

O RPI+R deve ser entendido como um **workflow de desenvolvimento** que passa a existir dentro do Konoha.

Ele não é:

- um novo Harness;
- um segundo sistema de orchestration;
- um novo dashboard;
- um novo sistema de telemetry;
- um novo judge;
- uma infraestrutura paralela.

A separação conceitual é:

```text
KONOHA
→ sistema de orquestração e governança

RPI+R
→ fluxo de trabalho para conduzir uma mudança
```

Em termos simples:

> **Konoha controla como os agentes trabalham.**
>
> **RPI+R define como uma mudança atravessa o processo de Research → Plan → Implement → Review.**

---

# 2. O que já existe no Konoha

O Konoha existente deve ser tratado como a implementação de referência.

A imagem atual do dashboard demonstra que ele já possui uma superfície operacional própria, com perspectivas como:

```text
Grafo
Métricas
Qualidade
Uso
Konoha
Patch Notes
```

Portanto, **não criar outro dashboard para RPI+R**.

O RPI+R deve aproveitar o dashboard existente caso, no futuro, algum estado do workflow precise ser exposto visualmente.

Isso é diferente de criar uma nova interface.

---

# 3. Modelo mental correto

O modelo desejado é:

```text
                         KONOHA
                sistema já existente
                           │
           ┌───────────────┴───────────────┐
           │                               │
    infraestrutura                     workflows
           │                               │
    ┌──────┼───────────┐              ┌────┴─────┐
    │      │           │              │          │
  ranks delegation   judge          outros     RPI+R
         gates       telemetry                   │
         lessons    watchdog                     │
         doctor                                  │
         dashboard                               │
                                                 │
                                      Research → Plan
                                                 ↓
                                      Implement → Review
```

A intenção é que o RPI+R seja **mais um fluxo que utiliza o Konoha**, e não uma plataforma paralela que passa a competir com ele.

---

# 4. Por que essa integração faz sentido

O Konoha já responde perguntas operacionais como:

- Quem pode executar?
- Quando deve delegar?
- Qual agente pode receber a tarefa?
- Qual escopo foi autorizado?
- Um gate deve bloquear?
- O retorno precisa ser julgado?
- O que aconteceu durante a operação?
- Há sinais de problema recorrente?

O RPI+R acrescenta perguntas sobre o **ciclo da mudança**:

- O problema foi pesquisado?
- Quais fatos foram encontrados?
- Quais decisões foram tomadas?
- Qual fatia está liberada?
- Quais critérios precisam ser atendidos?
- A implementação terminou?
- A Review aprovou?
- O que precisa ser corrigido?
- Qual é a próxima fatia?

Portanto:

```text
Konoha
→ governança da execução

RPI+R
→ governança do fluxo da mudança
```

---

# 5. Arquitetura conceitual

A arquitetura desejada é:

```text
                         VOCÊ
                          │
                  direção / decisão
                          │
                          ▼
                 ┌─────────────────┐
                 │      KONOHA     │
                 │                 │
                 │ Orchestration   │
                 │ Ranks           │
                 │ Delegation      │
                 │ Gates           │
                 │ Judge           │
                 │ Telemetry       │
                 │ Lessons         │
                 │ Watchdog/Doctor │
                 │ Dashboard       │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │      RPI+R      │
                 │                 │
                 │ Research        │
                 │ Plan            │
                 │ Implement       │
                 │ Review          │
                 └────────┬────────┘
                          │
                          ▼
                 trabalho no repositório
```

**Importante:** essa figura é conceitual. A implementação real deve respeitar a arquitetura e os pontos de extensão já existentes no Konoha.

---

# 6. Papéis complementares: Konoha, RPI+R, skills e humano

A integração deve preservar uma divisão clara de responsabilidades.

> **Konoha fornece a infraestrutura, governança e observabilidade.**
>
> **RPI+R organiza o fluxo de trabalho da mudança.**
>
> **As skills operacionalizam cada etapa com foco em qualidade e velocidade.**
>
> **O humano mantém a direção, as decisões e o julgamento final.**

O modelo mental é:

```text
                         VOCÊ
                 direção + julgamento
                         │
                         ▼
                       RPI+R
                  fluxo de trabalho
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Research         Plan        Implement
          │              │              │
          └──────────────┴──────────────┘
                         │
                         ▼
                       Review
                         │
                         ▼
                    decisão humana
```

As skills tornam cada etapa concreta:

```text
rpi-research
    → reduz incerteza

rpi-plan
    → transforma entendimento em plano executável

rpi-implement
    → executa uma fatia com escopo controlado

rpi-review
    → verifica se a entrega realmente atende ao combinado
```

Enquanto isso, o Konoha fornece o ambiente governado no qual essas etapas acontecem:

```text
                         RPI+R
                           │
                           ▼
                    ┌──────────────┐
                    │    KONOHA    │
                    │              │
                    │ delegation   │
                    │ ranks        │
                    │ gates        │
                    │ judge        │
                    │ telemetry    │
                    │ quality      │
                    │ memory       │
                    │ dashboard    │
                    └──────┬───────┘
                           │
                           ▼
                     agentes / Codex
```

## Objetivo da combinação

O objetivo não é simplesmente aumentar a autonomia do agente.

É aumentar **velocidade e qualidade simultaneamente**, mantendo o controle humano sobre as decisões importantes.

A divisão de responsabilidades pode ser resumida como:

```text
Velocidade
    → capacidade de execução da IA

Qualidade
    → processo + skills + validação

Direção
    → humano

Governança
    → Konoha

Fluxo da mudança
    → RPI+R
```

Ou, de forma ainda mais direta:

> **Velocidade vem da IA. Qualidade vem do processo. Direção vem de você. Konoha conecta e governa tudo.**

O sistema deve, portanto, evitar dois extremos:

```text
Pouca governança
→ agente rápido, mas difícil de controlar/verificar

Governança excessiva
→ processo seguro, mas lento e burocrático
```

O objetivo do RPI+R dentro do Konoha é encontrar um equilíbrio operacional:

```text
                    VELOCIDADE
                         ▲
                         │
                         │     IA executa
                         │     rapidamente
                         │
                         │
                         └──────────────►
                              QUALIDADE
                         processo verifica
```

As skills devem reduzir o custo de coordenação e aumentar a previsibilidade da execução, sem transformar cada tarefa em um processo burocrático.

O humano não precisa microgerenciar cada chamada de ferramenta. O sistema deve permitir autonomia **dentro de limites claros**, reservando a intervenção humana para direção, decisões, liberações e julgamentos que realmente importam.

---

# 7. As quatro skills

O RPI+R possui quatro skills:

```text
rpi-research
rpi-plan
rpi-implement
rpi-review
```

Elas devem ser entendidas como **interfaces de entrada para o workflow**, não como novos mecanismos de infraestrutura.

A especificação determina que sejam skills explícitas:

```yaml
allow_implicit_invocation: false
```

A passagem entre etapas deve continuar sendo intencional e controlada.

---

# 8. Research dentro do Konoha

`rpi-research` reduz incerteza.

Deve:

1. descobrir stack e convenções;
2. investigar implementações semelhantes;
3. identificar contratos e integrações;
4. identificar riscos;
5. separar fatos, inferências e hipóteses;
6. registrar questões que exigem decisão humana.

Não deve:

- escolher silenciosamente a solução final;
- implementar código de produção;
- esconder incertezas.

## Relação com a infraestrutura existente

Se o Konoha já possui delegation/ranks, Research deve utilizá-los.

Exemplo conceitual:

```text
Konoha
   │
   ├── agente de stack
   ├── agente de domínio
   └── agente de integração
          │
          ▼
      evidências
          │
          ▼
     orquestrador
          │
          ▼
      research.md
```

Subagentes continuam sendo evidência, não fonte final de verdade.

---

# 9. Plan dentro do Konoha

`rpi-plan` converte as evidências em decisões explícitas.

Produz, quando aplicável:

```text
research.md
      ↓
rfc.md
      +
status.md
```

A RFC deve estabelecer:

- contexto;
- problema;
- objetivos;
- não-objetivos;
- perfil técnico;
- estado atual;
- proposta;
- decisões;
- alternativas;
- invariantes;
- compatibilidade/migração;
- riscos;
- critérios de aceitação;
- plano de execução.

O plano deve dividir o trabalho em **fatias pequenas, dependentes e verificáveis**.

A RFC não significa autorização para executar o épico inteiro.

---

# 10. Implement dentro do Konoha

`rpi-implement` executa somente a fatia liberada.

Antes de alterar código:

```text
RFC
+
status
+
instruções locais
+
estado do Git
+
review anterior, se houver
```

Depois:

```text
implementação
      ↓
testes/validações
      ↓
evidências
      ↓
Aguardando Review
```

A skill não inicia automaticamente a próxima fatia.

Isso é importante porque o RPI+R define a passagem entre fatias como um ponto de controle.

---

# 11. Review dentro do Konoha

`rpi-review` verifica se a fatia realmente cumpriu seu contrato.

Entrada:

```text
RFC
+
fatia
+
invariantes
+
Definition of Done
+
status
+
diff
+
testes/validações
```

Ordem:

```text
Fatia / invariantes / DoD
        ↓
Critérios de aceitação
        ↓
Diff
        ↓
Testes e validações
        ↓
Lacunas
```

A Review não deve corrigir código.

Ela deve produzir:

```text
Aprovado
Aprovado com observações
Requer correção
```

---

# 12. Judge existente + Review

O Konoha já possui o conceito de julgamento independente.

Portanto, antes de criar qualquer mecanismo novo, verificar se o judge existente consegue suportar o contrato necessário para o RPI+R.

Modelo:

```text
Implementação
      ↓
evidências
      ↓
Review / Judge
      ↓
veredito
      ↓
┌───────────────┬─────────────────┐
│ aprovado      │ correção        │
▼               ▼                 │
próxima fatia   Implement limitado │
                │                 │
                └──────► Review ──┘
```

Não criar um segundo judge apenas para dar um nome diferente ao mesmo mecanismo.

---

# 13. Máquina de estados

O RPI+R introduz um estado explícito para cada fatia:

```text
Não iniciada
      ↓
Em implementação
      ↓
Aguardando review
      ↓
Aprovada
```

Correção:

```text
Aguardando review
      ↓
Correção solicitada
      ↓
Em implementação
      ↓
Aguardando review
      ↓
Aprovada
```

Também:

```text
Bloqueada
```

quando existir dependência ou decisão pendente.

A conclusão é:

```text
Escopo entregue
+
Critérios atendidos
+
Testes/validações
+
Invariantes respeitados
+
Review aprovada
=
FATIA CONCLUÍDA
```

---

# 14. Estado não deve duplicar infraestrutura sem necessidade

A especificação usa `status.md` como memória operacional.

Porém, no Konoha existente, primeiro verificar se já existe um mecanismo equivalente.

O requisito funcional é:

> conseguir saber o estado atual, a próxima ação, as evidências, as decisões e as pendências.

A implementação pode aproveitar mecanismos já existentes.

Não criar uma segunda infraestrutura de estado apenas para reproduzir algo que o Konoha já possui.

Se `status.md` for necessário para manter o contrato do RPI+R, ele pode ser introduzido de maneira integrada e mínima.

---

# 15. Delegation

RPI+R não substitui a política de delegação do Konoha.

A relação deve ser:

```text
RPI+R
→ informa fase + fatia + objetivo + restrições

Konoha
→ aplica ranks + delegation + gates + autorização
```

Exemplo:

```text
RPI+R:
"Executar Research da Fatia 01."

        ↓

Konoha:
"Qual agente pode executar?"
"É necessário delegar?"
"Qual escopo?"
"Qual brief?"
"Quais permissões?"
```

Isso mantém o Konoha como autoridade operacional.

---

# 16. Um único responsável por escrita

Para uma fatia:

```text
1 responsável por escrita
+
subagentes read-only quando necessário
```

O objetivo é evitar:

- conflitos;
- alterações concorrentes;
- responsabilidade difusa;
- worktrees inconsistentes.

Se o Konoha já possuir uma regra equivalente, reutilizá-la.

---

# 17. RPI+R consumindo a observabilidade existente

A infraestrutura de observabilidade do Konoha deve continuar sendo a fonte operacional para acompanhar o comportamento das execuções.

O RPI+R não deve criar uma segunda camada de logs ou métricas apenas para representar seu workflow.

A relação conceitual é:

```text
Konoha
│
├── execução
├── agents
├── tools
├── subagents
├── gates
├── judge
├── telemetry
├── quality
└── memory
        │
        ▼
      RPI+R
        │
        ├── fase atual
        ├── fatia atual
        ├── critérios
        ├── evidências
        ├── review
        └── decisão de avanço
```

Assim, uma execução de RPI+R pode produzir sinais que já são capturados pelo Konoha.

Por exemplo:

```text
RPI Research
    ↓
delegação de agente
    ↓
tool calls
    ↓
leituras
    ↓
evidências
    ↓
Plan
```

O Konoha continua observando a execução.

O RPI+R utiliza essas evidências para decidir o avanço do workflow.

Isso evita a criação de um sistema paralelo de observabilidade.

## Evolução futura do dashboard

Caso, depois do uso real, exista uma necessidade operacional de visualizar:

- RFC ativa;
- fase atual;
- fatia em execução;
- aguardando Review;
- bloqueios;
- histórico de Reviews;

a evolução preferencial é **estender o dashboard existente do Konoha**.

Não criar um "RPI+R Dashboard" separado.

A necessidade deve ser demonstrada pelo uso real antes da implementação.

---

# 18. O dashboard atual continua sendo o dashboard do Konoha

**Não criar um dashboard RPI+R.**

O dashboard existente já possui:

```text
Grafo
Métricas
Qualidade
Uso
Konoha
Patch Notes
```

Ele deve continuar sendo a superfície visual principal.

Se futuramente surgir uma necessidade real de visualizar:

```text
RFCs
fatias
estado
reviews
```

isso deve ser avaliado como **uma possível evolução do dashboard existente**, e não como uma nova aplicação/dashboard.

A necessidade precisa surgir do uso real.

---

# 19. Telemetry

RPI+R não deve criar um segundo sistema de telemetry.

Primeiro identificar:

```text
O que Konoha já mede?
```

Depois:

```text
O que RPI+R precisa saber?
```

Se houver interseção:

```text
reutilizar
```

Se houver lacuna:

```text
avaliar extensão mínima
```

Somente criar infraestrutura nova se houver uma necessidade concreta.

---

# 20. LangSmith — possível complemento futuro

LangSmith não deve ser tratado como requisito do RPI+R.

Se houver interesse futuro em instrumentação detalhada de execuções de agentes, ele pode ser avaliado como uma ferramenta complementar de tracing/evaluation.

Conceitualmente:

```text
Konoha
→ governa e orquestra

RPI+R
→ conduz o workflow

LangSmith
→ pode observar detalhadamente execuções
```

Mas isso deve ser tratado como **avaliação futura**, não como parte necessária da primeira integração.

O Konoha não deve depender de uma plataforma externa para funcionar.

---

# 21. O papel do humano

O RPI+R não deve eliminar o controle humano.

O modelo é:

```text
Humano
   ↓
direção
   ↓
Research
   ↓
Plan
   ↓
liberação
   ↓
Implement
   ↓
Review
   ↓
aprovação
   ↓
próxima fatia
```

A IA possui autonomia dentro da fatia atual.

O humano controla a direção entre fases e fatias.

---

# 22. O principal risco: duplicação

O maior risco da integração não é falta de funcionalidades.

É criar funcionalidades que o Konoha já possui.

Evitar:

```text
Konoha
 ├── delegation
 ├── judge
 └── telemetry

RPI+R
 ├── nova delegation
 ├── novo judge
 └── nova telemetry
```

O resultado desejado é:

```text
Konoha
 ├── delegation ─────────┐
 ├── judge ──────────────┤
 ├── telemetry ──────────┤
 ├── ranks ──────────────┤
 ├── dashboard ──────────┤
 │                       │
 └───────────────► RPI+R │
                     │   │
               Research  │
               Plan      │
               Implement │
               Review    │
```

---

# 23. O segundo risco: treadmill

Não transformar a integração em:

```text
RPI+R
 ↓
novo sistema
 ↓
novo agente
 ↓
novo monitor
 ↓
novo dashboard
 ↓
monitor do monitor
```

O próprio Konoha deve continuar obedecendo à regra:

> **Não construir capacidade antes de existir demanda observada.**

Antes de adicionar qualquer mecanismo:

1. Qual problema real estamos resolvendo?
2. Existe evidência?
3. O Konoha atual não resolve?
4. Podemos reutilizar algo?
5. Como verificaremos que a mudança funcionou?

Se não houver resposta convincente:

```text
NÃO IMPLEMENTAR AINDA
```

---

# 24. Estratégia de integração

Não começar criando as quatro skills imediatamente dentro do repositório de trabalho sem estudar o sistema.

A sequência recomendada é:

## Fase 1 — Research de integração

Mapear o Konoha existente:

- arquitetura;
- agentes;
- ranks;
- delegation;
- gates;
- judge;
- telemetry;
- lessons;
- watchdog;
- doctor;
- estado/persistência;
- dashboard;
- testes;
- validações;
- pontos de extensão.

Depois mapear o RPI+R:

```text
RPI+R
   ↓
capacidade existente?
   ├── Sim → reutilizar
   ├── Parcial → adaptar
   └── Não → avaliar criação
```

## Fase 2 — Gap analysis

Produzir uma análise semelhante a:

```text
| Capacidade RPI+R | Situação no Konoha | Decisão |
|---|---|---|
| Research | ... | ... |
| Plan | ... | ... |
| Implement por fatia | ... | ... |
| Review | ... | ... |
| Estado | ... | ... |
| Retomada | ... | ... |
| Delegação | ... | reutilizar/adaptar |
| Judge | ... | reutilizar/adaptar |
| Telemetry | ... | reutilizar/adaptar |
| Dashboard | existente | não criar outro |
```

A tabela real deve ser preenchida pelo Codex após investigar o repositório.

## Fase 3 — Plan

Somente depois do Research e gap analysis criar a RFC da integração.

## Fase 4 — Implement

Implementar a menor mudança necessária.

## Fase 5 — Review

Validar a integração contra:

- comportamento existente;
- contratos;
- invariantes;
- testes;
- escopo da RFC.

## Fase 6 — Uso real

Usar o RPI+R em atividades reais.

Somente problemas observados no uso devem motivar novas melhorias.

---

# 25. Critérios de sucesso

A integração será bem-sucedida quando:

1. o Konoha continuar funcionando como antes;
2. RPI+R estiver disponível como um novo fluxo de trabalho;
3. Research → Plan → Implement → Review puder ser executado de forma controlada;
4. cada fatia possuir estado explícito;
5. Review puder bloquear avanço;
6. correções puderem ser limitadas aos achados;
7. delegation/ranks/gates existentes continuarem prevalecendo;
8. o estado puder ser retomado sem depender da conversa;
9. não houver duplicação desnecessária de infraestrutura;
10. o dashboard existente continuar sendo a superfície visual principal;
11. novas capacidades forem justificadas por problemas reais;
12. o próprio RPI+R puder ser usado para evoluir o Konoha.

---

# 26. Princípios finais

1. **O Konoha existente é a fonte de verdade arquitetural.**
2. **RPI+R é um novo workflow dentro do Konoha.**
3. **Não reconstruir o Konoha.**
4. **Não criar um segundo Harness.**
5. **Reutilizar antes de criar.**
6. **Preservar ranks, delegation, gates, judge, telemetry, lessons e watchdog existentes.**
7. **Não criar outro dashboard.**
8. **Research vem antes de decisões de integração.**
9. **Gap analysis vem antes da implementação.**
10. **Implement executar somente uma fatia liberada.**
11. **Review independente é condição de conclusão.**
12. **Um único responsável por escrita por fatia/worktree.**
13. **O humano controla a direção entre fases e fatias.**
14. **Estado operacional não deve depender da conversa.**
15. **Novas capacidades devem nascer de problemas observados.**
16. **LangSmith, se considerado, é complemento de observabilidade/evaluation, não requisito.**
17. **O próprio Konoha deve evoluir usando o RPI+R.**

---

# 27. Instrução final para o Codex

**Não implemente o RPI+R baseado apenas neste documento.**

Este documento define a intenção arquitetural.

A primeira ação deve ser:

```text
RESEARCH
  ↓
entender profundamente o Konoha existente
  ↓
mapear cada requisito do RPI+R
  ↓
identificar equivalentes já existentes
  ↓
identificar gaps reais
  ↓
propor a menor integração necessária
  ↓
PLAN
  ↓
implementar somente após decisão/liberação
```

O objetivo final não é:

> "Adicionar um RPI+R ao lado do Konoha."

É:

> **"Fazer o Konoha existente ganhar o fluxo de trabalho RPI+R, utilizando sua infraestrutura operacional, de governança e de observabilidade atual, e adicionando somente aquilo que realmente estiver faltando."**

A integração deve parecer, para o usuário, uma nova capacidade natural do Konoha — e não dois sistemas colados um ao outro.
