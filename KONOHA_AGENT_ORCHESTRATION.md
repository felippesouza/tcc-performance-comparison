# 🥷 Konoha — Agent Orchestration & Self-Auditing Apparatus

> A portable specification for running a multi-agent coding assistant with **delegation ranks**,
> **enforced guardrails**, **calibrated judgement**, and an **anti-treadmill governance ledger**.
>
> Harness-agnostic. Written to be reimplemented on any agentic IDE that supports subagents and
> lifecycle hooks (Claude Code, Antigravity, Cursor, or a hand-rolled loop).

---

## ⚠️ READ THIS FIRST — runtime vs reference

**This file is ~123 KB. Do not load it into an agent's context.**

That warning is not incidental. §14.5 caps the always-loaded memory index at **24 KB** and acts at
67% of it; §1 claim 1 is *"context bloat never errors"*. A 123 KB file loaded as standing
instruction is **~5× the entire index budget** — which would make the specification of the
anti-context-bloat system the single largest context consumer in the apparatus. Splitting it costs
nothing and not splitting it refutes the document.

| Part | What it is | Size | Load it? |
|---|---|---|---|
| **§17 + Appendix cheat sheet** | the operating rules an agent needs *while working* | ~2 KB | ✅ **this is the runtime slice** — put it in the agent's standing instructions |
| **§§1–16** | port documentation: mechanism, thresholds, code, rationale, measured gaps | ~121 KB | ❌ reference. Read it once when building; consult it on demand |
| **§15** | measured failures and what nothing watches | — | ❌ reference, but read it before trusting any number here |

**How to use it:** extract §17 and the Appendix into a short standing-instruction file. Keep this
document in the repo and open it when you are *building or changing* the apparatus — the same
distinction the system draws everywhere else between what is loaded and what is retrieved.

---

## 📌 Resumo (PT-BR)

Este documento descreve, de ponta a ponta, um sistema de orquestração de agentes que resolve
quatro problemas que aparecem quando você usa um assistente de código agêntico de forma séria:

| Problema | Mecanismo |
|---|---|
| O contexto principal incha silenciosamente e nada te avisa | **Ranks + gates de delegação** (§2, §5) |
| O agente relata sucesso sem ter feito o trabalho | **Dever de julgamento + placar de veredito** (§7) |
| A memória vira lixo: notas sem valor, sem procedência, sem prazo | **Barra de qualidade de memória** (§8) |
| Você constrói ferramenta atrás de ferramenta sem provar que serviu | **Ledger de validação externa** (§12) |

O nome vem da hierarquia ninja de Naruto porque o mapeamento é literalmente bom: existe um
orquestrador que delega e julga, especialistas autônomos dentro de escopo estreito, executores sem
julgamento, e uma guarda invisível que pode **bloquear** qualquer um deles — inclusive o orquestrador.

**Por que o corpo está em inglês:** este arquivo é feito para ser *lido por um agente* como
instrução de sistema. Modelos raciocinam com menos atrito semântico em inglês, e o vocabulário
(`blocked`, `overridden`, `degraded`, `falsifier`) precisa casar exatamente com o que o código emite.
O resumo e a instalação ficam em português; a especificação, em inglês.

### Instalação rápida

```bash
# 1. Create the apparatus directory (single source of truth for state)
mkdir -p ~/.agent-graph

# 2. Create the hooks directory for your harness and copy the guardrails (§5)
#    Claude Code:  ~/.claude/hooks/
#    Antigravity:  see §16 for the event mapping

# 3. Seed the three data files
echo '{"_schema":"2.0.0"}'          > ~/.agent-graph/lessons.json
: > ~/.agent-graph/guard-log.jsonl
: > ~/.agent-graph/mission-ledger.jsonl

# 4. Wire the hooks to lifecycle events (§5.1), then verify the watchdog sees them
node ~/.agent-graph/watchdog.mjs --alert
```

Nada aqui depende de rede, API externa ou serviço pago. Todo o estado é arquivo local: JSON,
JSONL e Markdown.

---

## §1 · Design thesis

Five claims the whole system rests on. Each one was learned from a concrete failure, and each
one has a named way to be proven wrong.

**1. Context bloat never errors.** Reading a 3,000-line file inline succeeds. Running `grep -r`
across a repo succeeds. Nothing in the harness reports a problem, and by the time the session
degrades, the cause is fifty tool calls back. *Therefore: the fix cannot be a reminder. It must be
a gate that returns a non-zero exit code.*

**2. A subagent's return is evidence, not truth.** A well-formatted report with real `file:line`
citations disarms scrutiny more effectively than a vague one — the citation proves the line
**exists**, never that it answers the question you asked. *Therefore: sample-verify load-bearing
claims before using a return, every time.*

**3. An instrument that reports good news must be interrogated.** Ask: "what would this look like
if the instrument were broken?" If the answer is "the same", the instrument is not evidence. *This
is the falsifier rule (§9), and it is the single most load-bearing idea in the document.*

**4. Capability built ahead of demand is not progress.** A roster of 46 agents where 25 have never
run is not a capability gap — it is inventory. *Therefore: no new instrument ships without a
falsifiable prediction about real work, recorded before the build (§12).*

**5. Silence is not health.** A guardrail with zero firings is either unnecessary or broken, and
both require action. *Therefore: the guardrails are themselves watched (§6).*

---

## §2 · The rank model

### 2.1 Two independent axes

The most common modelling error is collapsing "which agent do I send" and "do I need permission"
into one dimension. They are orthogonal.

```
Axis 1 — NINJA RANK  = role in the orchestration.   Who plans vs who executes.  → WHO to dispatch
Axis 2 — MISSION RANK = blast radius of the TASK.   Reversibility, reach.       → WHETHER to ask first
```

The source encodes only axis 1. **Mission rank is a property of the task, never of the shinobi** —
a Genin can be *on* an S-rank mission, exactly as in the source material.

**The approval gate lives on axis 2, never on axis 1.** An S-rank mission needs sign-off no matter
how capable the agent is. Conversely, a highly capable agent doing a D-rank lookup needs no gate.

### 2.2 Ninja ranks (axis 1)

Ordered top to bottom. Array position *is* the hierarchy.

| Rank | 日本語 | Kind | Definition |
|---|---|---|---|
| **Daimyō** | 大名 | human | Commissions and funds the missions, approves the irreversible. Above the orchestrator, **outside the executing chain**. This is you. |
| **Hokage** | 火影 | orchestrator | Main thread. Splits the objective into missions, delegates, **then judges the reports** (hallucinations, done-or-not) and forms the final answer. |
| **Jounin** | 上忍 | coordinator | Rank-A coordinator: breaks a large mission into parts, supervises smaller shinobi, guards against infinite loops. |
| **Chuunin** | 中忍 | specialist | Autonomous specialist. Decides alone **inside a narrow scope**; mutation bounded. |
| **Genin** | 下忍 | worker | Executor. No complex judgment — locate, read, parse, fetch, report back. |
| **ANBU** | 暗部 | guardrail | Invisible always-on guard. Answers directly to Hokage-level config, **bypassing the chain**, and **can block**. Not a shinobi with judgment: it forces the STOP, the agent judges at the pause. |
| **Ne** | 根 | watch | Root. Watches the ANBU themselves and reports **directly to the Hokage**. Tracks liveness, bypass rate and self-integrity — because a guardrail that fails silently is worse than an absent one. |

**The `id` values — the foreign key, which is NOT the display name.** Roster records reference a
rank by `id`, and the display label is derived from it, never the reverse:

```js
daimyo · kage · jounin · chuunin · genin · anbu · ne
```

Note `kage` ↔ **Hokage**: the id is the generic rank, the label is the village-specific title. Get
this wrong and every roster record fails to resolve while looking perfectly readable. Array order
**is** the hierarchy — do not sort the table for display without preserving the source order.

Two structural notes for a port:

- **Daimyō, ANBU and Ne sit outside the executing chain.** Daimyō is the human principal; ANBU and
  Ne are code, not agents. In any visualization they should be rendered as ink/structure tones, not
  as members of the same categorical series.
- **The canon inversion in Ne is the design point.** In the source material, Ne answering to Danzō
  instead of the Hokage was the original defect. Here it reports to the Hokage on purpose: the
  watch over the guards must not be owned by the guards.

### 2.3 Mission ranks (axis 2)

Honest note: only the endpoints of this scale are pinned to concrete content in the source system.
Reproduced as-is rather than invented.

| Mission rank | Blast radius | Gate |
|---|---|---|
| **S** | commit, push, force-anything, destructive, outward-facing publish | **Ask the Daimyō.** Always. |
| **A** | large multi-part mission needing coordination and loop-guard | Coordination required; no human sign-off per se |
| **B / C** | bounded mutation inside a narrow, declared scope | None — autonomy inside scope |
| **D** | read, locate, parse, fetch, report | None |

**Enforcement is deliberately absent.** There is no hook blocking "a Genin cannot take an S-rank
mission". The only mechanism is a **declaration ritual**: on dispatch, state role + mission rank
inline —

> `1 Genin [locator] + 1 Chuunin [reviewer], parallel, C-rank.`

Build enforcement only when a trigger actually fires. A rule that has never been violated does not
need a machine.

### 2.4 Who may dispatch — and the structural gap

Dispatch capability is a boolean on the roster record: *can this agent spawn other agents?* In
practice it is derived from the tool grant (does it hold the `Agent`/`Task` tool?).

**The honest shape of a real roster: 4 of 47 records can dispatch — 1 Hokage + 3 Jounin.** Every
specialist and every worker is `dispatch: false`. Read-only exploration agents are typically
*explicitly barred* from spawning ("all tools except Agent"), and fork-style agents are instructed
to execute rather than re-delegate.

> **⚠ THE JOUNIN GAP (verified, recorded, deliberately not filled).**
> Virtually all coordination collapses back onto the Hokage, with **no middle layer providing
> loop-guard**. Building a coordinator layer now would be speculative machinery. The fix — if ever —
> is triggered by a real failure of orchestrator-level coordination, e.g. an agent looping
> unsupervised and burning real work.

This is worth reproducing verbatim in your own port, including the decision not to fix it. A
recorded gap is a design artifact; an unrecorded one is debt.

### 2.5 The independence rule

The orchestrator **must not certify its own work.** Blind scoring is delegated to a separate
judge agent that never sees the orchestrator's reasoning. Rationale, measured: a judge validated
100% on its own calibration lineage scored only ~62% on fresh cases. Self-assessment is not
evidence; it is the shape of evidence.

---

## §3 · Roster-as-data

The roster is a **single exported array**, not scattered configuration. Same treatment as any
other domain entity.

```js
// name    = canonical agent id, exactly as it appears in usage telemetry and in dispatch calls
// clan    = origin (custom = hand-written, others = plugin/kit)
// dispatch= can spawn other agents (holds the Agent/Task tool) → the Jounin capability
// mutates = can Edit/Write
export const ROSTER = [
  { name: 'main-thread', rank: 'kage', clan: 'core', model: 'opus',
    dispatch: true, mutates: true, selfKage: true,
    note: 'The orchestrator itself. Excluded from active/idle counts.' },
  // ...
];
```

Observed fields: `name`, `display`, `rank` (FK into the rank table), `clan`, `model`,
`dispatch: bool`, `mutates: bool`, `note: string`, optional `selfKage: true`.

**There is deliberately no `tools` or `triggers` field.** Tool grants are captured as the two
derived booleans plus prose in `note`; triggers live in each agent's own definition file. Reason:
duplicating the tool list creates a second source of truth that silently rots.

### 3.1 Archetypes (portable roles, not product names)

Port these **roles**, not any specific agent list. Each archetype pairs a rank, a model tier and a
hard output contract — the contract is what makes delegation pay for itself.

| Archetype | Rank | Model tier | Output contract |
|---|---|---|---|
| **locator** | Genin | cheap/fast | `file:line` table only. No analysis, no suggestions. |
| **sweeper** | Genin | inherit | Broad read-only search across many files; returns the conclusion, not the file dumps. |
| **digest** | Genin | cheap/fast | State/WIP recall → fixed-length digest (e.g. 15 lines) instead of reading N files. |
| **doc-reader** | Genin | cheap/fast | Returns only the relevant fields of a large document/record. Never the full payload. |
| **blind-judge** | Genin | strong | Offline scoring of another agent's run against a frozen rubric. Never sees the orchestrator's reasoning. |
| **bounded-editor** | Chuunin | inherit | 1–2 file edits. **Hard-refuses 3+ files — a literal scope cap.** |
| **reviewer** | Chuunin | mid | One line per finding, severity-tagged, no praise, no scope creep. |
| **investigator** | Chuunin | mid | Diagnosis from external data (logs/metrics/traces). Bounded token budget with a declared irreducible core (§11.3). |
| **test-writer** | Chuunin | strong | Tests that assert behaviour at the observable layer. |
| **coordinator** | Jounin | inherit | The only rank that may dispatch. Breaks up large missions, guards loops. |

**Tool grant per archetype.** The roster stores only the two derived booleans (`dispatch`,
`mutates`), because duplicating a full tool list creates a second source of truth that rots. But the
grant itself has to be decided somewhere, so decide it here:

| Archetype | Read | Search | Shell | Edit/Write | Dispatch | External/MCP |
|---|---|---|---|---|---|---|
| locator · doc-reader | ✅ | ✅ | read-only cmds | ❌ | ❌ | ❌ |
| sweeper | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| digest | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| blind-judge | ✅ | ✅ | read-only cmds | ❌ | ❌ | ❌ |
| bounded-editor | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| reviewer | ✅ | ✅ | read-only cmds | ❌ | ❌ | ❌ |
| investigator | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ (its data source) |
| test-writer | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| coordinator | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Two rules that matter more than the grid:

- **`mutates: true` and `dispatch: true` together is the coordinator, and nothing else.** Any other
  archetype holding both is a coordinator you did not mean to create.
- **The scope cap is a prompt rule, not a tool restriction.** `bounded-editor` "hard-refuses 3+
  files" because its definition says so — the tool layer cannot count files across calls. That means
  the cap is **self-enforced and therefore capped at `provavel`** (§9.2), and nothing in §5 enforces
  it. If a 3-file edit slipping through would be expensive for you, the honest answer is a
  PreToolUse counter, not a firmer sentence in the prompt.

**The orchestrator has no archetype row on purpose** — it is not dispatched, so it has no output
contract and no rank-based grant; it holds everything. ANBU and Ne have none because they are code,
not agents. That leaves 3 of the 7 ranks staffed by archetypes, which is the honest shape: the
middle of the hierarchy is where delegation actually happens.

**Model assignment heuristic:** cheap/fast model for mechanical lookup (≤3 tool calls); mid model
for reasoning plus multi-tool orchestration; strong model for authoring, judging and design.
Pick the **role first** — it pins both the tool scope and the model.

> **On the roster numbers quoted throughout this document.** They *do* reconcile, and the
> reconciliation is worth following because it is exactly the kind of thing that looks like an
> inconsistency and is not: **47 records − 1 orchestrator = 46 dispatchable = 16 active + 30 idle.**
> The 47th is the orchestrator itself, which §14.3 excludes from active/idle by design.
>
> The one figure that genuinely does **not** close is in §15-F: 30 idle agents, later split as "3
> hand-written + 23 plugin-owned" = **26**. Those are snapshots taken on different dates, so the gap
> is drift, not arithmetic — flagged here rather than silently reconciled. Treat every roster number
> in this document as *shape*, and check your own census against your own roster.

### 3.2 Pin the alias, not the version ID

If your harness supports family aliases (`opus` / `sonnet` / `haiku`, or the equivalent), pin the
**alias**. An explicit version ID is a frozen snapshot: it silently keeps running the previous
generation after a new one ships, and **it never errors**, so nothing surfaces the drift.

This was established empirically, not from documentation — by grepping the model id recorded on
each request in the local transcripts and observing a clean cutover with zero overlap on the
alias-configured agents. Documentation said the opposite. The measurement settles it.

> Reusable check: grep `"model":"..."` over your newest session transcripts and confirm the old
> generation stops appearing after the cutover date.

### 3.3 Census drift detection

An agent type that appears in real usage but holds no roster record is **census drift** — a new
agent nobody ranked. Surface it loudly:

```
⚠ UNRANKED (in usage, absent from roster): <type>, <type>
```

Do not silently merge unranked types into the totals, and do not silently drop them: report both.

---

## §4 · Delegation rules

### 4.1 When NOT to spawn an agent

```
Do NOT spawn an agent when:
  · the task resolves in ≤ 3 inline tool calls
  · the output would be < 5 lines
  · the answer is in memory or trivially deducible

Overhead is ~15-30s per agent startup. Only worth it when intermediate output is large,
or the task needs specialized tools.
```

### 4.2 When you MUST delegate

STOP before: a large file read, parsing an archive, a broad recursive grep, or an expensive
external query. Ask: *is this a delegable unit (output > ~5 lines, not a direct reasoning step)?*
If yes, dispatch **first**.

> **Rationale worth memorizing:** inline drift bloats context silently and never errors, so
> nothing corrects it mid-session.

Legitimate inline work — the exemptions that keep the rule honest:

- authoring the artifact itself (writing the document *is* the job)
- exact-string reads required to prepare a precise edit
- visual judgment on a rendered output
- a sequenced irreversible mutation where ordering matters
- ≤3 tool calls with <5 lines of output

### 4.3 Orchestration patterns

- **Parallel dispatch.** Independent units go in **one message** as multiple concurrent calls.
  Sequential dispatch of independent work is pure latency.
- **Briefing fast-path.** Pass agent A's output into agent B's prompt as `briefing:` so B skips
  re-querying the same expensive source.
- **Locate before editing.** Dispatch a locator to get exact `file:line` before touching a file.
  This avoids reading whole files inline.
- **⚠ The anti-pattern that motivated the whole gate layer:** delegate, then re-read the same file
  inline anyway. You pay for the isolation and then destroy it. If a locator already returned a
  `file:line` table, **use those lines** — do not re-read the file whole.

### 4.4 One writer per file

**Concurrency must be removed by design, not requested in prose.** Two parallel agents pointed at
one output file with an "append" instruction: the one that finished last wrote non-appendingly and
destroyed 54 records from the other — silently, and it even reported "file created" when the file
was not empty.

Give every parallel writer its **own** output file and concatenate afterwards. If a shared file is
truly unavoidable, require each agent to report the line count before and after.


### 4.5 Lifecycle — one dispatch, end to end

Everything after this section is organized by component. This section is the spine that connects
them. If you read only one section before building, read this one.

### 4.5.1 The trace

```
USER PROMPT
   │
   ├─▶ [router]                    UserPromptSubmit · injects the routing table into context
   │                               non-blocking. Its documented failure (a nudge alone does not
   │                               change behaviour) is WHY the gates below block instead.
   │
   ▼
ORCHESTRATOR decides: delegable? (§4.1 / §4.2)
   │
   ├── NO ──▶ works inline ──▶ [delegation-check] PreToolUse on read/shell/search
   │                              │
   │                              ├─ allowed  → logs `passed`  → tool runs
   │                              ├─ blocked  → logs `blocked` → exit 2, stderr to model
   │                              │             model must delegate or use the escape hatch
   │                              └─ escaped  → logs `overridden` + the stated reason
   │
   └── YES ─▶ dispatch call issued, harness assigns tool_use_id = MISSION ID
                │
                ▼
         [brief-gate]  PreToolUse on the dispatch tool
                │  reads lessons for THIS agent (§11)
                │  ├─ lesson unaddressed → logs `blocked` → exit 2, prints the lesson
                │  │                        orchestrator REWRITES the briefing, re-dispatches
                │  │                        ⚠ the re-dispatch gets a NEW tool_use_id
                │  ├─ `lesson-ok:` present → logs `overridden` + reason
                │  └─ all addressed        → logs `passed`
                │
                └─▶ writes ledger row  { phase: "dispatched", missionId, agent }
                          ▲
                          └── THIS is the ledger's first writer. It is the brief-gate, not
                              judge.mjs — the gate is simply the only component guaranteed to
                              fire on every dispatch, so it carries the ledger write as a
                              secondary duty. State this explicitly or the denominator in
                              §7.6 has no producer.
                │
                ▼
         SUBAGENT RUNS  — exempt from delegation-check (§5.5): it IS the delegation target
                │          not exempt from brief-gate (nested dispatches are recorded)
                ▼
         RETURN ARRIVES
                │
         [judge-return]  PostToolUse on the dispatch tool
                │  ├─ writes ledger row { phase: "returned", missionId, agent }
                │  └─ injects the judgement prompt (§7.8) · logs `intervened`, never `blocked`
                │
                │  ⚠ SYNCHRONOUS RETURNS ONLY. For a background dispatch this fires on the
                │    LAUNCH, not the arrival — see §15-E. The behaviour rule carries it alone.
                ▼
         [patch-watch]  PostToolUse on edit/write — fires only if the turn edited a file.
                │  appends the touched paths to the pending-changes log. Telemetry, never blocks.
                │  Its consumer is doctor check 3a at session close (§5.7).
                ▼
         ORCHESTRATOR samples ONE load-bearing claim (§7.3)  ← the fold (§7.5)
                │
                ▼
         emits a verdict line, then records it:
              node judge.mjs <missionId> <verdict>
                └─▶ writes ledger row { phase: "judged", missionId, verdict }

         ⚠ TWO VERDICT CHANNELS. The spoken verdict line and the recorded one are different
           acts. A verdict emitted in the transcript but never typed into judge.mjs is
           INVISIBLE to coverage. That gap is a large part of why measured coverage is low
           (§15-B) — say so rather than letting the number look like negligence.
                │
                ▼
   IF the verdict is MENOR or MATERIAL:
         author a lesson (§11.0) ──▶ lessons file, keyed by agent
                                      └─▶ the brief-gate above will block the NEXT dispatch
                                          of that agent until the briefing addresses it.
                                          THIS is the loop closing. It is a manual write.
                │
SESSION CLOSE
   ├─▶ [doctor --quiet]  Stop event · REPORTS a blocker (exit 1) if an agent has a defect
   │                     verdict and no active lesson. Exit 1 is not exit 2 — it surfaces,
   │                     it does not veto. See the honesty note in §11.0.
   └─▶ [watchdog --alert] next SessionStart · reports silent, bypassed or degraded gates
```

### 4.5.2 Intra-turn ordering, stated once

Within a single turn the order is fixed by the harness event model, not by the components:

```
UserPromptSubmit → (per tool call) PreToolUse → tool executes → PostToolUse → … → Stop
```

Consequences worth writing down, because they are not obvious:

- `router` fires **once per user turn**; the gates fire **once per tool call**. A turn with
  twelve tool calls fires the router once and `delegation-check` twelve times.
- The vault gate's per-turn scan (§5.3) resets on the next real user message, **not** on each
  tool call — which is why tool results must not be mistaken for turn boundaries.
- `judge-return` and the vault gate never interact: they bind to different events on different
  tools. There is no ordering hazard between them.

### 4.5.3 Cases the happy path hides

| Case | What happens | Why it matters |
|---|---|---|
| **Dispatch blocked by brief-gate** | A `dispatched` row may already exist for the blocked call. The re-dispatch gets a **new** `tool_use_id`. | Orphan `dispatched` rows with no `returned` accumulate. They are correctly excluded from `eligible` (§7.6), so coverage stays honest — but the mission count inflates. Decide this deliberately; do not discover it. |
| **Ledger rotation** | The ledger caps at 2000 lines, rotating oldest-first. | Rotation can drop a `dispatched`/`returned` pair while keeping a later `judged` row, making coverage non-reconcilable. Either window the coverage query or fold before rotating. |
| **Background dispatch** | `judge-return` fires at launch (§15-E). | The injection lands before the return exists. Judgement still has to happen; nothing reminds you. |
| **Hook crashes** | Fails open, logs `error`. | The call proceeds ungated. Only the watchdog surfaces it (§6.3). |
| **Nested dispatch** | `delegation-check` exempts it; `brief-gate` records it as `nested`. | Lessons still apply one level down — that asymmetry is deliberate (§5.5). |

### 4.5.4 Artifact inventory

Every file the running system touches, in one place, because the component sections each mention
their own and none lists them together.

| Path | Written by | Read by | Bounded? |
|---|---|---|---|
| `~/.agent-graph/guard-log.jsonl` | every gate, one line per firing | `watchdog.mjs` | ❌ no rotation — read-capped at 20k lines only |
| `~/.agent-graph/mission-ledger.jsonl` | `brief-gate`, `judge-return`, `judge.mjs` | `judge.mjs`, `quality.mjs` | ✅ 2000 lines, mode `0600` |
| `~/.agent-graph/lessons.json` | **a human, by hand** (§11.0) | `brief-gate`, `doctor.mjs` | n/a |
| `~/.agent-graph/receipts.md` | a human, by hand | `doctor.mjs`, `quality.mjs` | n/a |
| `<vault>/reliability-log.md` — per-agent verdicts **with the finding in prose** (§7.4.1) | a human, by hand | `doctor.mjs` check 6a, `quality.mjs` | append-only, never rewritten |
| `~/.agent-graph/patch-notes.json` — **this is "the changelog"** referred to elsewhere | a human, by hand | `doctor.mjs` (checks 3a/3b) | n/a |
| `~/.agent-graph/pending-changes.jsonl` | **`patch-watch`, automatically** (§5.7) | `doctor.mjs` check 3a | ⚠️ bound it — paths only, mode `0600` |
| `<vault>/*.md` + index | a human / the orchestrator | `vault.mjs` and everything downstream | index capped at 24 KB (§14.5) |
| `trace.json` · `mine.json` · `metrics.json` | their own scripts | the dashboard, `roster.mjs` | derived — safe to delete and regenerate |

> **The four by-hand rows are the system:** lessons, receipts, patch-notes, and the vault. Everything
> else is either telemetry a hook writes or a derived file a script regenerates. If you automate one
> of the four you will have built a different system than this one — those four are exactly where
> judgement enters, and judgement is the thing that cannot be generated.
>
> Note the split this makes visible: `pending-changes.jsonl` is written **by a hook** and read by the
> doctor, whereas `patch-notes.json` is written **by you**. The doctor's job is to compare them —
> what the session *touched* against what you *chose to record* — so collapsing them would remove
> the only check that catches an undocumented change.

---

## §5 · The guardrail layer (ANBU)

Hooks are not agents. A hook has no judgment — **it forces the STOP; the agent supplies the
judgment at the pause.**

### 5.1 Event wiring

| Guardrail | Lifecycle event | Matches | Can block? |
|---|---|---|---|
| `delegation-check` | **PreToolUse** | file-read / shell / search tools | ✅ yes |
| `brief-gate` | **PreToolUse** | agent-dispatch tool | ✅ yes |
| `judge-return` | **PostToolUse** | agent-dispatch tool | ❌ injects only |
| `patch-watch` | **PostToolUse** | edit/write tools | ❌ telemetry only |
| `router` | **UserPromptSubmit** | — | ❌ injects a nudge |
| `watchdog --alert` | **SessionStart** | — | ❌ reports |
| `doctor --quiet` | **Stop** | — | ❌ reports |

**Harness contract required for a port** (§16 maps this to other IDEs):

- hook receives JSON on stdin containing `tool_name`, `tool_input`, `tool_response`,
  `tool_use_id`, `transcript_path`
- **exit code 2 = BLOCK**, and stderr is surfaced to the model
- exit code 0 = allow
- PostToolUse can inject context via stdout
- `tool_use_id` is **stable across the Pre and Post events of the same call** — this is what makes
  the mission ledger possible (§7.6)
- the transcript is JSONL, and tool results appear as `user`-role entries containing
  `tool_result` blocks

### 5.2 The delegation gate — complete logic

**Bind it to these tools.** The matcher is a regex over the harness's tool name; substitute your
harness's own identifiers:

| Gate | Matcher | Fields it reads from `tool_input` |
|---|---|---|
| `delegation-check` | `Read\|Bash\|Grep` | `file_path`, `limit`, `offset` · `command` · `output_mode`, `head_limit` |
| `brief-gate` | `Agent\|Task` | `subagent_type`, `prompt` |
| `judge-return` | `Agent\|Task` | reads `tool_response`, not `tool_input` |

Throughout the code below: `tool = d.tool_name`, `ti = d.tool_input`, `cmd = ti.command`,
`fp = ti.file_path`, `prompt = ti.prompt`, `agent = ti.subagent_type` — all read off the stdin
JSON described in §5.1.

Every terminal path logs to the watchdog **before** exiting.

```js
function allow(reason)      { log({action: 'passed',     reason}); process.exit(0); }
function overridden(detail) { log({action: 'overridden', reason: 'inline-ok',
                                   detail: detail || 'unstated'}); process.exit(0); }
function block(msg, reason) { log({action: 'blocked',    reason});
                              process.stderr.write(msg); process.exit(2); }
```

> **Why the override text is captured verbatim:** an override must carry a *why*. Capturing the
> stated reason means a motiveless bypass shows up as `unstated` instead of blending into the
> counts. An override without a stated motive is indistinguishable from gaming the gate.

Evaluation order: parse stdin (unreadable → allow) → **subagent exemption** → per-tool branch.

#### Branch A — shell commands

Override is checked **first**, so the escape hatch always works:

```js
if (cmd.includes('inline-ok')) overridden(/inline-ok:\s*([^\n]*)/.exec(cmd)?.[1]);

const delegable =
  /(^|[\s;|&(])unzip(\s|$)/.test(cmd) ||
  /(^|[\s;|&(])tar\s+[^|]*(x|--extract)/.test(cmd) ||
  /(^|[\s;|&(])grep\s+-[A-Za-z]*[rR]/.test(cmd) ||
  /(^|[\s;|&(])find\s+[^|]*-exec/.test(cmd);
```

Block message names the delegation targets and the escape hatch:

```
🧭 DELEGATION GATE — this shell op (unzip / tar -x / grep -r / find -exec) dumps large output
into MAIN context. Delegate first → sweeper (unzip/parse) · locator (symbol/grep).
If inline is genuinely necessary (≤3 calls / no agent fits), re-run with
  inline-ok: <reason>   in the command.
```

#### Branch B — file reads, four sub-gates in order

```js
if (ti.limit) allow('bounded');                       // 1. see the warning below
if (!fp) allow('no-path');                            // 2.
if (/\.(png|jpe?g|gif|webp|bmp|svg|pdf|ico|heic)$/i.test(fp)) allow('visual');
if (isVaultRead(fp) && fs.existsSync(fp) && !briefed) block(VAULT_MSG);   // 3. see §5.3
let st; try { st = fs.statSync(fp); } catch { allow('nonexistent'); }     // 4. Write target etc.
if (st.size > 60000) block(SIZE_MSG);
let lines; try { lines = fs.readFileSync(fp,'utf8').split('\n').length; } catch { allow('unreadable'); }
if (lines > 800) block(LINES_MSG);
```

> **⚠ Sub-gate 1 disarms on `limit` ALONE.** `offset` without `limit` does **not** disarm it,
> even though the block messages say "offset+limit" (§15-J logs this as a real defect: a gate whose
> message misdescribes its own mechanism). Implement `limit`, and either fix your messages or fix
> the condition — but know which one you chose.

The three remaining block messages, verbatim — **in a fail-closed gate the message IS the entire
user-facing behaviour**, so an unspecified message is an unspecified gate:

```
SIZE_MSG:
🧭 DELEGATION GATE — unbounded read of a large file (${st.size} bytes) floods MAIN context.
Delegate (sweeper / digest archetype) OR pass offset+limit to read only the range you need.

LINES_MSG:
🧭 DELEGATION GATE — unbounded read of a large file (${lines} lines) floods MAIN context.
Delegate (sweeper / digest archetype) OR pass offset+limit to read only the range you need.

GREP_MSG:
🧭 DELEGATION GATE — broad content search (output_mode:content, no head_limit) can dump many
lines into MAIN context. Delegate → locator archetype, OR narrow it: add head_limit, or use
output_mode:"files_with_matches"/"count".

VAULT_MSG:   ← the fail-closed gate. Its message is the ONLY thing the model sees, so it must
             name both remedies and say why the read is being refused at all.
🧭 DELEGATION GATE — unbounded read of a MEMORY VAULT file. Reading whole memory files to
build a status/WIP picture is the documented drift.
Pick one:
  • dispatch a digest archetype (state recall → digest), or
  • pass a bounded range and read only what you need — if a locator already returned a
    file:line table, USE those lines instead of re-reading the file whole (that exact
    delegate-then-re-read-inline pattern is what made this gate necessary).
```

#### Branch C — structured search

```js
const contentMode = ti.output_mode === 'content';
const noCap       = ti.head_limit == null;
if (contentMode && noCap) block(/* narrow it: add head_limit, or switch output_mode */);
```

No `inline-ok` path here — the escape is to narrow the query, which is always possible.

### 5.3 The vault gate — the subtle one

Size thresholds never fire on memory files, because memory files are 50–320 lines each. The
size-based gate was **structurally blind** to the exact drift it was meant to stop: "read N memory
files to build a status picture". So vault reads are gated on **boundedness, not size**.

```js
const VAULT_RE      = /\/memory\//;                    // adapt to your vault path
const DIGEST_AGENTS = /session-briefer|wip-checker/;   // your digest archetypes
const isVaultRead   = fp => VAULT_RE.test(fp) && /\.md$/i.test(fp);

// BLOCK when: isVaultRead(fp) && fs.existsSync(fp) && !briefedThisTurn()
```

`briefedThisTurn()` scans the **last 400 transcript lines backwards**:

- an **assistant** entry with a dispatch `tool_use` whose `subagent_type` matches a digest
  archetype → `true` (a digest ran this turn — allow the read)
- a **user** entry that is *not* a tool result → `false` (reached the real user message; nothing
  ran this turn). **Tool results arrive as `user` entries and are not turn boundaries** — this
  distinction is load-bearing and easy to get wrong.
- falling off the end of the window → `false` (gate stays ON)
- an exception → `null`, meaning **could not determine**, deliberately distinct from "no digest ran"

```js
// Unreadable transcript → gate stays ON. That is deliberate fail-CLOSED,
// unlike the rest of this file: the escape hatch is always available, so a false
// block costs one retry, never a wedged workflow — whereas fail-open here would
// silently restore the exact drift this gate exists to stop.
```

The `null` case emits a `degraded` telemetry record, computed for **every** qualifying read (not
just vault reads), because v1 conflated "could not check" with "not briefed" and reported it as a
normal block.

Two points the code makes but prose usually leaves implicit — state them or a reimplementer guesses:

- **`degraded` is a telemetry action, not a block.** On a non-vault read the record is written and
  the read proceeds; only `isVaultRead(fp)` reaches the block. The scan runs unconditionally so
  that "the turn context was unreadable" is visible as its own state rather than being discovered
  only when it happens to coincide with a vault read.
- **The vault gate's escape hatch is sub-gate 1, and nothing else.** There is no `inline-ok:` path
  for reads. Because `if (ti.limit) allow()` runs *before* the vault check, passing a bounded range
  is the escape — which is what makes fail-closed defensible: a false block costs one retry with a
  `limit`, never a wedged workflow. If you reorder those sub-gates you silently remove the escape
  hatch and the fail-closed argument collapses with it.

### 5.4 Fail policy, per branch

| Branch | Policy | Why |
|---|---|---|
| shell / read-size / search | **fail-open** | a broken gate must not wedge the workflow |
| vault turn-scan | **fail-closed** | the escape hatch is always available; a false block costs one retry |
| hook itself crashes | **fail-open + `error` telemetry** | *the false-zero class: a broken gate stops gating silently. The watch must see this.* |

### 5.5 The subagent exemption

Each subagent runs with its own transcript file, which is the discriminator:

```js
const tp     = String(d.transcript_path || '');
const nested = tp.includes('/subagents/') || /\/agent-[^/]*\.jsonl$/.test(tp);
```

- **The delegation gate hard-exempts subagents.** The subagent *is* the delegation target; gating
  it would forbid the very behaviour the gate exists to force. Locators and sweepers must grep,
  read and unzip freely.
- **The briefing gate does NOT exempt them — it records `nested` instead.** v1 did exempt nested
  dispatches. It was reverted because *every* defect found in one particularly bad audit happened
  exactly one level down, where the gate had exempted itself.

### 5.6 The briefing gate

The dispatch-time gate that carries **lessons** (§11) into the outgoing prompt. Its design is
counterintuitive and worth copying exactly: **it does not inject text — it blocks the dispatch and
prints the lesson on stderr, forcing the orchestrator to rewrite the briefing itself.**

Rationale: the subagent has no memory across dispatches, and most agents are plugin-owned or
otherwise uneditable. The lesson only arrives if it is *written into the prompt*. Injection would
let the orchestrator ignore it; a block will not.

```js
const applies = (l) => {                    // scope: when does this lesson apply at all?
  const kinds = l.scope?.taskKinds;
  if (!Array.isArray(kinds) || !kinds.length) return true;   // unscoped = always
  return kinds.some(k => new RegExp(k, 'i').test(prompt));
};

const unmet = (l) => {                      // requires: which concepts are missing?
  const reqs = Array.isArray(l.requires) ? l.requires : null;
  if (!reqs) return new RegExp(l.guard || '$^', 'i').test(prompt) ? [] : ['(legacy guard)'];
  return reqs
    .filter(r => !new RegExp((r.any || []).join('|') || '$^', 'i').test(prompt))
    .map(r => r.concept || 'unnamed');
};
```

**Each concept is checked independently**, and the block names *which* one is missing. v1 matched
one lexical regex per lesson, which produced false passes when a word appeared by accident and
false blocks when the briefing addressed the point in other words.

Escape hatch: `lesson-ok: <reason>` in the prompt. The reason is logged.


### 5.7 The two non-blocking guardrails

Both are listed in §5.1 and neither blocks anything. Specified here so they are not mistaken for
decoration.

**`router` — UserPromptSubmit.** Prints the delegation routing table (archetype → trigger) into
context, once per user turn. It exists to make the *choice* visible at the moment the decision is
made, not to enforce it.

> **Its documented failure is the reason the blocking gates exist.** Measured: a per-turn text
> reminder alone did **not** change behaviour — the same drift recurred twice in one session, once
> caught by the human rather than by the system. Keep the router (it costs nothing and makes the
> roster discoverable) but do not count it as a control. This is the cleanest example in the whole
> apparatus of the difference between **salience** and **enforcement**.

**`patch-watch` — PostToolUse on edit/write.** Appends the path of every file the session modified
to a pending-changes log. Pure telemetry: no gate, no injection.

Its consumer is what makes it worth having: **doctor check 3a** compares that log against the
changelog and warns about files that were changed without being recorded. Without it, "what did I
touch this session?" is answerable only by reading the transcript.

Same privacy rule as the mission ledger (§7.6): **paths only — no diffs, no content, no prompt
text.** A telemetry file nobody reads still leaks. Bound it and set restrictive file permissions.

> Note the asymmetry with §5.5: `patch-watch` does **not** check `transcript_path`, so it records
> subagent edits too. That is intentional — a `bounded-editor`'s changes are exactly the ones you
> most want in the pending-changes log, because you did not type them yourself.

---

## §6 · The watch over the watchers (Ne)

**Trigger that produced it (real, not hypothetical):** a detector reported `0 fat lines` for hours
*because it was broken*. The guards blocked things; nothing checked that the guards were alive.

### 6.1 The telemetry logger

One synchronous appended line per firing. No parse, no read-modify-write, no network. **Never
throws** — the whole body is wrapped so that telemetry can never break the guardrail it observes.

```json
{"ts":"2026-08-31T14:28:20.358Z","hook":"brief-gate","tool":"Agent",
 "action":"passed","reason":"no-lessons","detail":"main","agent":"sweeper"}
```

| Field | Meaning |
|---|---|
| `ts` | ISO timestamp |
| `hook` | which guardrail fired |
| `tool` | the tool being gated |
| `action` | validated against the vocabulary below; **anything unrecognised silently becomes `passed`** |
| `reason` | required when action is `overridden` / `degraded` / `error`, else `null` |
| `detail` | override motive (≤120 chars), `main`/`nested`, or the error name |
| `agent` | the dispatched agent, when applicable |

### 6.2 The action vocabulary — the heart of the design

```js
export const ACTIONS = ['blocked', 'intervened', 'passed', 'overridden', 'degraded', 'error'];
```

| Action | Definition |
|---|---|
| `blocked` | The gate stopped the call. Only a PreToolUse hook can do this. |
| `intervened` | Acted without stopping anything (a PostToolUse injection). *It changes what I see, not whether the call runs.* |
| `passed` | Fired, found nothing to act on. **Healthy silence — proof of liveness.** |
| `overridden` | Deliberate bypass. **Requires a reason.** |
| `degraded` | Ran but could **not** enforce fully. *The dangerous middle state: v1 reported these as healthy passes.* |
| `error` | The hook itself failed. **The false-zero class.** |

> Keeping `degraded` and `error` out of the `blocked` bucket is what makes the numbers honest.
> A PostToolUse injection logged as `blocked` inflates the blocked-vs-bypass picture with events
> that never blocked anything.

### 6.3 The three measures

Default window: **14 days**, reading at most the last 20,000 log lines.

```js
const INSTRUMENTED = new Set(['delegation-check', 'brief-gate', 'judge-return']);
const MIN_N = 20; // below this, rates are noise — do not cry wolf on a handful of firings
```

**Only instrumented guards are alertable.** Third-party hooks are listed for visibility but never
alerted on — *an alarm that fires every day for something that will never change is how a watchdog
trains you to ignore it.*

**(1) Liveness** — cross-check the *registered* hooks (scraped from settings) against the hooks
*seen firing* in the log. A registered-but-silent instrumented hook is probably broken.

**(2) Bypass rate** — is the gate becoming theatre?

```js
const fired = v.blocked + v.intervened + v.passed + v.overridden;  // degraded/error excluded
const bypassPct = fired ? Math.round((v.overridden / fired) * 100) : 0;
if (bypassPct >= 30 && fired >= MIN_N) alert(`${hook}: ${bypassPct}% override in ${fired} firings`);
```

**Thresholds: ≥30% override AND ≥20 firings.** A rate computed over 2 events ("50% override!") is
noise wearing a percentage.

**(3) Self-integrity** — four independent alerts, none gated by `MIN_N`:

| Condition | Alert |
|---|---|
| any `error` records | gate may be blind |
| settings unreadable | cross-check OFF — no guard can be detected as silent |
| log unreadable | **blind watch, not clean watch** |
| log mtime stale **> 72h** | logger probably broken (hooks fire every session) |
| zero entries but instrumented guards registered | same as above |
| any `degraded` records | ran without being able to fully enforce |

Closing line of the report, worth keeping:

> ⛔ silence ≠ health: a guard with no firings is either unnecessary OR broken — both require action.

### 6.4 Version normalisation

When two instruments read one log, **they must agree**. Normalise legacy action names on read
(`block`→`blocked`, `pass`→`passed`, `override`→`overridden`), with one exception carrying real
semantics: `block` from the post-return judge becomes **`intervened`**, not `blocked`. Mark
normalised rows `legacy: true` so the migration is visible.

---

## §7 · The judgement layer

### 7.1 The duty

The orchestrator delegates, **then judges the reports**. Missing this is invisible, because a bad
return never errors.

Distinct from offline evaluation: the blind judge is *calibration*; the inline "is this return true
and complete?" call happens on **every dispatch** and belongs to the orchestrator.

### 7.2 Three modes — one correct, two failures

| Mode | Status | Mechanism |
|---|---|---|
| **Redo** | ❌ FAILURE | Agent returned a `file:line` table; the orchestrator re-read 4 whole files anyway. **Paid for the isolation and then destroyed it.** |
| **Accept** | ❌ FAILURE | A checker's report was used to close a permanent record, quoting lines never verified — in the same session that agent had been told "do not accept self-description as proof". Scepticism applied outward, not inward. |
| **Verify a sample** | ✅ CORRECT | Sample-verify. Do not re-do, do not accept. Budget: roughly **one tool call**. |

### 7.3 What counts as load-bearing

Sample-verify anything that:

- goes into a permanent record
- is a **negative** claim ("X is absent", "no such file", "0 results") — cheap to state, expensive
  to be wrong about. Confirm *where it looked*.
- is a commit hash, PR number, ID or timestamp
- is a **count given without a reproduced line**

Three inline dimensions, deliberately coarser than the offline rubric:

```
(a) Do the load-bearing claims check out?  — sample-verify, do not re-do and do not accept.
(b) Did it answer what I actually asked?   — the ask, not an adjacent question it preferred.
                                             True-but-off-target is the dangerous case:
                                             nothing about it looks wrong.
(c) Is it good enough to ACT on?           — a return can be true AND on-target and still be
                                             too shallow or incomplete to use.
```

### 7.4 Verdict vocabulary

```
OK                — answered the ask; sampled claims held.
DEFEITO-MENOR     — usable, but I had to correct or complete something.
DEFEITO-MATERIAL  — would have caused real damage had I accepted it
                    (wrong edit, reverted work, false conclusion written down).
NAO_VERIFICADO    — no verdict. An unchecked return is not evidence of reliability.
```

**Not verified ≠ OK.** A return you did not check counts as nothing.

**The verdict tracks the worst defect, not the average** — a return can be 90% excellent and still
be MATERIAL, because the worst defect is what gets acted on.

**Action threshold:** two `DEFEITO-MATERIAL` on the same agent → re-brief it, or change its model.
Kept explicit so it can be revised against real counts; *without a threshold the judgement is
decorative.* Authority split: re-briefing belongs to the orchestrator; changing a model or retiring
an agent belongs to the Daimyō.

### 7.4.1 The reliability log — why it is NOT the mission ledger

Two records, deliberately not merged, because they answer different questions:

| | Mission ledger (§7.6) | Reliability log |
|---|---|---|
| Shape | JSONL, one row per phase | markdown table, append-only |
| Carries | `{ missionId, agent, phase, verdict }` | date · agent · verdict · **the finding, in prose** |
| Answers | *what fraction of returns did I judge?* | *what was actually wrong, and has it happened before?* |
| Read by | the coverage calculation | you, and the doctor's lost-learning check |
| Privacy | no paths, no prompt text (bounded, `0600`) | prose — so write findings, never payloads |

```markdown
| date | agent | verdict | finding |
|---|---|---|---|
| 2026-08-31 | `locator` | **DEFEITO-MATERIAL** (1/2) | shape: `generated-vs-generator` — reported
hits in the built artifact and missed the generator that produces them. Accepting it would have let
the next regeneration silently revert the edit |
```

Conventions that make it usable a month later:

- **Verdict bolded; `*not verified*` in italics and counted as nothing.** An unchecked return must
  not read as a pass.
- **`(1/2)` tracks progress toward the two-MATERIAL threshold** (§7.4). Without the counter the
  threshold is decorative.
- **Name the defect shape** (`shape: <lesson-id>`) so the log and the lessons file (§11) join on a
  slug rather than on your memory.
- **Append, never rewrite.** The value is the accrual; editing history destroys the only evidence
  that a lesson did or did not hold.

> **Why both.** The ledger gives verdicts a *denominator*; the log gives them *content*. Merge them
> and you get either a JSONL nobody reads prose in, or a markdown table no script can count. The
> cost of keeping both is one extra append per defect.

### 7.5 Where the fold is

> Between **receiving** the report and **using** it. If a report goes straight into a document, an
> edit, or a record without a verdict line, the orchestrator was not judging — it was transcribing.

The defeating failure mode has a name: **scribe drift.** Four dispatches, zero verifications, every
report transcribed straight into a document. And the reason it is so easy:

> **`file:line` proves the line EXISTS, not that it answers the right question.**

A well-formatted report with real citations disarms judgement *more* effectively than a vague one.
Hence two questions, not one: is the claim *true*, and does it answer *the question I actually
asked*.

### 7.6 The mission ledger — giving verdicts a denominator

Two quality indicators sat permanently at `unknown` because verdicts had no denominator. The
harness supplies one: **`tool_use_id` is identical in the Pre and Post events of the same call.**
That is the mission id — ephemeral, per-call, and not an identifier of anything else.

```json
{"ts":"...","phase":"dispatched","missionId":"toolu_01XBu...","agent":"sweeper"}
{"ts":"...","phase":"returned",  "missionId":"toolu_01XBu...","agent":"sweeper"}
{"ts":"...","phase":"judged",    "missionId":"toolu_01XBu...","agent":"sweeper","verdict":"OK"}
```

- `phase` ∈ `dispatched | returned | judged`; `verdict` present only on `judged`
- file mode `0600`, capped at 2000 lines with rotation-on-write
- **Privacy rule:** no prompt text, no session id, no paths. *A ledger nobody reads still leaks.*

**Eligibility rule:** a mission becomes eligible for judgement once it has **returned**.
Dispatched-but-still-running is not a missing judgement — counting it as one would manufacture a
denominator that makes coverage look worse than it is.

```
coverage = judged / eligible      // null when eligible === 0, never 0
```

### 7.7 Why the verdict writer is a CLI, not a hook

> A hook can see that a return **arrived**, never that judgement **happened** — that is the
> difference between pushing and verifying, and inferring a verdict from the presence of text would
> fabricate exactly the number this is meant to make honest.

```bash
node judge.mjs <missionId> <OK|DEFEITO-MENOR|DEFEITO-MATERIAL|NAO_VERIFICADO> [agent]
node judge.mjs --pending      # returned-but-unjudged missions
```

### 7.8 The post-return prompt

A PostToolUse hook that injects the judgement questions. It **pushes, it cannot verify** — and it
says so about itself.

```
⚖️ JUDGE BEFORE USING THIS RETURN (<agent>).
1) is the claim true?  2) does it answer the question I ASKED?  3) is the quality sufficient?
   (3 = can I ACT on this, or is it shallow and I will have to redo it underneath?)
[if the body contains file:line]
   ⚠️ this return cites file:line. That proves the LINE EXISTS — not that it answers
      the right question.
[if the body contains a negative claim: "does not exist" / "no such" / "zero" / "absent"]
   ⚠️ contains a NEGATIVE claim — cheap to assert, expensive to get wrong. Confirm where it looked.
Sample 1 load-bearing claim (whatever supports what you are about to write or record).
Then emit: Verdict: <agent> — OK | DEFEITO-MENOR | DEFEITO-MATERIAL | NAO_VERIFICADO
```

> **`NAO_VERIFICADO` must appear in this list.** §7.4 makes "not verified ≠ OK" load-bearing and the
> verdict CLI accepts the token — but if the one instrument that actually *elicits* verdicts omits
> it, the only way to comply under time pressure is to pick a real verdict you did not earn. The
> escape state has to exist at the moment of choosing, not only in the vocabulary that documents it.

Two content detectors drive the conditional warnings:

```js
const cites   = /[\w./-]+\.(?:mjs|js|ts|kt|java|go|py|md|json|ya?ml|html|swift):\d+/.test(body);
const negates = /\b(does not exist|no such|none|zero |absent|not found)\b/i.test(body);
```

---

## §8 · The memory vault

### 8.1 File format

One fact per file. Frontmatter plus a body.

```markdown
---
name: <short-kebab-case-slug>
description: <one-line summary, used to decide relevance during recall>
metadata:
  type: user | feedback | project | reference
---

<the fact. For feedback/project, follow with **Why:** and **How to apply:** lines.>
<Link related memories with [[their-name]].>
```

| `type` | Holds |
|---|---|
| `user` | who the user is — role, expertise, preferences |
| `feedback` | guidance on *how to work*: corrections and confirmed approaches. **Include the why.** |
| `project` | ongoing work, goals, constraints **not derivable from the code or git history**. Convert relative dates to absolute. |
| `reference` | pointers to external resources (URLs, dashboards, tickets) |

An index file carries **one line per memory** — never memory content:

```markdown
- [Title](file.md) — hook
```

### 8.2 The quality bar — 2 value tests + 5 quality tests

The JSON schema is authoritative; prose companions must not restate the criteria. (This rule
exists because the criteria drifted to 4, 5, 6 and 7 items across different files.)

**Value tests — gates on *existence*. Fail either → do not save.**

| # | Name | Question | Fail means |
|---|---|---|---|
| **V1** | decision-changing | What future decision changes if this is true? | Not a memory — a note. |
| **V2** | named-failure | What goes wrong without it? | Usually state-documentation wearing the clothes of insight. |

Neither is machine-scorable: they require knowing the decision space, and no textual signal is a
proxy for it. **Pretending otherwise would be the exact false-confidence the system exists to
prevent.**

**Quality tests — gates on *readiness*. Fail → unfinished, not wrong: fix it.**

| # | Name | Question |
|---|---|---|
| **Q1** | recall-key | Would a future search FIND this? Does `description` carry the terms search would use? |
| **Q2** | actionable | Does it say what to **do**, not only what is true? |
| **Q3** | provenance | Is it stated **how** the claim was established — verified (and how), inferred, or reported? |
| **Q4** | time-scope | Is the claim typed as principle / tool-fact / world-state, with world-state **dated**? |
| **Q5** | appropriate-source | Is the claim grounded in the source that is **authoritative for its type**? |

Machine score = count of Q1–Q5 that pass, out of 5. Score ≤2 → flagged as weakest.

**Q1 fails silently** — the memory exists but is unreachable. That is the worst failure mode in
the set, because nothing surfaces it.

Q4's three claim kinds:

- **principle** — timeless ("generated is not the generator")
- **tool fact** — true until the tool changes ("`<cmd>` has no `<flag>` subcommand")
- **world state** — needs a date, decays in weeks ("73+ records affected, no monitor")

### 8.3 Q5 — source authority per claim type

Q5's first implementation demanded a `file.kt:123` citation from *every* memory, which mismeasured
roughly half the vault: **a user preference is not grounded in code, and neither is an infra
scope.** The fix was to make the expected source a function of the claim type.

| Claim type | Authoritative source | Signal | Note |
|---|---|---|---|
| `behaviour` | source code + the test that asserts it | `path:line`, or a named test | **Insufficient:** repo `CLAUDE.md`, `.claude/rules/*`, `README` |
| `runtime` | operational source (cloud console, observability platform, deploy config) or a versioned env/profile yml | named resource + where observed + date | Console-only resources: absence from code is **not** absence of the thing |
| `policy` | authoritative documentation, the platform's own spec | link/doc name + date consulted | — |
| `preference` | an explicit statement by the user | date + what was said | Code citation is meaningless here — **this was the original Q5 defect** |
| `principle` | the concrete episode that produced it | the case it came from | Does not decay; needs no date |
| `negative` | a **delimited** search whose scope is stated | the exact command/paths searched | Cheap to assert, expensive to be wrong |

Two supporting rules:

- **Repo docs are a lead, never evidence.** If a claim traces only to a `CLAUDE.md`, mark it
  *inferred* (Q3), not verified.
- **Do not store what is derivable in one command.** Three memories once published a "next
  available test ID" — 288, 292, 325 — and all three collided. **Store the command, not the number.**

### 8.4 Curation

- **Archive, don't delete.** Move resolved incidents and shipped work to an archive file; keep the
  index pointing only at active memories.
- **Never merge memories.** One fact per file. Merging destroys the recall key and the provenance
  of both.
- Recalled memories reflect what was true **when written**. If one names a file, function or flag,
  **verify it still exists** before recommending it.

---

## §9 · The truth scale

A single ordered axis for every claim the system makes, so that different instruments cannot each
invent their own confidence vocabulary.

| Level | EN | Rank | Means | Requires |
|---|---|---|---|---|
| `suposicao` | assumed | 1 | No evidence gathered. Inference, recollection, or someone's assertion taken at face value. | — |
| `provavel` | probable | 2 | Indirect or partial evidence. The artifact exists, or a non-independent party checked it. | evidence |
| `confirmado` | confirmed | 3 | Direct, executable, **reproducible** evidence — **and a declared falsifier.** | evidence + falsifier |
| `refutado` | refuted | 0 | Evidence gathered and it **contradicts** the claim. The only state that is news. | evidence |
| `indeterminado` | indeterminate | — | Could not be established: infra missing, validator unknown, source unreachable. **Not a zero and not a refutation.** | — |

> `suposicao` vs `indeterminado`: in the first, **nobody looked**. In the second, **someone looked
> and could not see.** Collapsing them is how you learn to ignore alarms.

Honesty conditions, worth quoting into your own port:

- `suposicao` is honest **when stated as such**. An assumption declared is useful; *an assumption
  dressed as a finding is the single most damaging thing this system can produce.*
- `provavel` is honest when the **indirectness is named** — "the file exists" is evidence about
  *presence*, not about *behaviour*.
- `confirmado` is honest when **someone else could re-run it and get the same answer.**

### 9.1 The falsifier rule — the load-bearing one

```
A check earns `confirmado` only if you can name the state of the world that would make it FAIL.
If the answer to "how would this look if it were broken?" is "the same", it is not evidence —
it is a ritual that outputs green.
```

This is not abstract. It is exactly how a vault scored 100/100 with ~43 false claims, how a
detector reported 0 problems when there were 92, and how a generator reported a successful build
while emitting a dead application.

A *valid* falsifier names a concrete world-state:

```
"remove or rename the fragment matching /<pattern>/ in <file>"
"the value in <file> stops being <expected>"
"the commit disappears from the history of <ref> (rebase/force-push), or the pattern never existed"
```

### 9.2 Ceilings — claims that can never be promoted

| Ceiling | Rule |
|---|---|
| **Existence → max `provavel`** | A file being present is evidence about presence, not behaviour. The existence check is *capped by design* — the one check that can never earn `verified`. |
| **No falsifier → max `provavel`** | A validator that declares no falsifier is capped, however green it looks. |
| **Self-certification → max `provavel`** | An agent judging its own output, or a script validating the script that produced it, is not independent. |
| **`indeterminado` never promoted, never zero** | Counting "could not check" as "nothing wrong" is the false-zero pattern. |
| **Direction** | **Downgrade is free, promotion is expensive.** Any claim may be lowered at any time; raising one requires the evidence that level demands. |

### 9.3 Cross-vocabulary mapping

Every instrument's private vocabulary maps onto the one axis. Do this in your port or the
vocabularies will drift within a month.

| Instrument | Its terms | → Truth scale |
|---|---|---|
| validators | `declared` / `evidence-present` / `verified` / `degraded` / `failed` | suposicao / provavel / **confirmado only if a falsifier is declared, else provavel** / indeterminado / refutado |
| claim manifest | `agent-only` / `hokage-sample` / `unverifiable` | provavel / confirmado / indeterminado |
| investigator | `CONFIRMED` / `HYPOTHESIS` | confirmado / suposicao **with a named confirmation step** |
| quality indicators | `observed` / `partial` / `unknown` | confirmado / provavel / indeterminado |
| memory Q3 (§8.2) | verified / inferred / reported | confirmado / suposicao / provavel |
| **guardrail actions (§6.2)** | `blocked` `intervened` `passed` | *not truth claims* — these describe what the gate DID, not what is true. Deliberately outside the axis |
| | `overridden` | *not a truth claim*; carries a reason that is itself `suposicao` until checked |
| | `degraded` / `error` | **indeterminado** — the check did not complete |
| **inline verdicts (§7.4)** | `OK` | **provavel** — a sampled check, self-certified, so capped by §9.2 |
| | `DEFEITO-MENOR` / `DEFEITO-MATERIAL` | **refutado** *for the specific claim that failed* — evidence contradicted it |
| | `NAO_VERIFICADO` | **indeterminado** — explicitly not `suposicao`: someone looked and stopped |
| **judge rubric (§10.4)** | `PASS` / `FAIL` | **provavel** — scored against a rubric, not against the world |
| | `UNSCORABLE` | **indeterminado** |
| **lessons (§11.1)** | `outcome: unproven` | **suposicao** — no comparable missions yet |
| | `outcome: holding` / `failed` | **provavel** / **refutado** |
| **ledger verdicts (§12.2)** | `hit` / `half-hit` | **provavel** — a real-world event, judged by the person who predicted it |
| | `miss` / `killed` | **refutado** / *withdrawn, not a truth claim* |
| | `pending` / `treadmill-suspect` | **indeterminado** — the check-by has not arrived, or arrived inconclusive |

> **Two things this expanded table makes visible.** First, several vocabularies are **not truth
> claims at all** — a gate reporting `blocked` says what happened, not what is true, and forcing it
> onto the axis would be a category error. Mapping is not the same as flattening. Second, **every
> self-assessed vocabulary lands at `provavel` or below.** The system contains no mechanism capable
> of producing `confirmado` about its own behaviour; only an audit against an independent source
> does. That is not a defect in the mapping — it is the mapping doing its job.

> **Provenance note:** the `claim manifest`, `investigator` and `quality indicators` rows come from
> the source system's own instruments and are reproduced as *worked examples of the mapping
> discipline*, not as components this document specifies. If you do not build those instruments,
> drop those three rows — the discipline is what ports, not the row set.

---

## §10 · The evaluation layer

Offline, blind scoring of a subagent run against a **frozen** rubric. Separate from §7 (which is
inline and per-dispatch).

### 10.1 Five dimensions, scored 0 / 1 / 2

| # | Dimension | 0 = fail | 1 = partial | 2 = pass |
|---|---|---|---|---|
| **D1** | Groundedness & validated claims | invents facts, OR asserts a finding without validating it against a known control | mostly grounded, 1 unverified claim | every claim traceable to a file or tool result; severity claims verified, not probabilistic |
| **D2** | Brief adherence | answers a different question / ignores stated scope | answers the ask, drifts on a constraint | answers exactly what was dispatched, honors scope |
| **D3** | Tool-correctness | wrong tools / thrash / repeated failing calls | right tools, avoidable retries | minimal correct calls, no thrash |
| **D4** | Completeness of the actual job | required action left undone (a "do X" task where X didn't happen), **even if cleanly reported** | resolves core, misses an edge | fully done |
| **D5** | Clarity & usefulness (**not** raw length) | hard to parse, OR length adds nothing | readable, slightly bloated | clear; every extra line earns its place |

### 10.2 Hard gates

```
Any of these → FAIL, no matter the rest:
  · D1 = 0  — hallucination OR an unvalidated critical claim. Grounding is non-negotiable.
  · D4 = 0 on an action task (build/apply/create/fix) — if the job wasn't actually done,
            it fails regardless of how clean the writeup is.
```

Otherwise assign a holistic **0–10** weighted by family, then **PASS if ≥ 8**.

> Length is **not** penalized per se — only when it hurts clarity or adds nothing (D5). An explicit
> token budget is a signal to **dock**, not an auto-fail, if the extra content is genuinely useful.
> Reward useful proactivity; penalize unexplained bloat.

Agreement with human labels is measured **numerically (±1 on the 0–10 holistic)**, not as a hard
binary — because two 7-vs-8 boundary splits were being counted as total disagreements.

### 10.3 Per-family weights

| Family | Weighted dimensions |
|---|---|
| Locators / sweepers | D1 + D5 |
| Reviewers | **D1** + D2 |
| Builders / test-writers | **D4** + D2 |
| Investigators | D1 + known false-positive patterns |
| General | balanced |

### 10.4 Judge contract

```
Input:  { brief, output, type } + the frozen rubric
Output: { D1..D5: 0|1|2|null, holistic: 0-10|null, verdict: PASS|FAIL|UNSCORABLE,
          gateHit: null|"D1"|"D4", rationale: one line }

UNSCORABLE = the case could not be scored (truncated output, missing brief, wrong artifact).
It is NOT a FAIL. A judge with no way to say "I could not score this" will emit a real
verdict for an unscorable case, and that verdict enters the agreement statistics as if
it were a judgement — which silently corrupts the calibration the rubric depends on.
Count UNSCORABLE cases in their own bucket and report the bucket; never fold them into
the denominator as failures.

Local only — the judge runs in-harness, never sends case content to an external API.
Bias mitigation: don't judge a model with itself; a stronger model judging a weaker one is fine;
randomize batch order; don't reward verbosity.
```

### 10.5 The validation gate — and the overfit trap

```
1. Human labels a held-out set BLIND.
2. Judge scores the same set with the frozen rubric.
3. Require ≥ ~80% agreement within ±1.
```

> **Overfitting guard:** re-scoring the SAME cases the rubric was calibrated on is **fitting, not
> validating**. Expect ~100%, and it is meaningless.

**Recorded numbers, reproduced because they are the honest part:**

- v1 (equal-weight sum) scored **50%** binary agreement against 8 human labels.
- v2 held-out: **6/6 within ±1**, mean abs diff 0.5, **n=6**. Caveats recorded in-file: the judge
  scored after seeing labels (residual anchoring); n=6 is a strong MVP signal, **not** statistical
  proof (full validation ≈15–30 cases).
- A later drift-check exposed the judge as **OVERFIT to its own lineage: fresh-only agreement
  dropped to 62% (8/13 fresh)**, isolated almost entirely to one agent family.

**Conclusion, stated plainly: the judge is usable for spot-checks and is NOT gate-ready.** Do not
wire it into CI. This is the single most important caveat in §10 and it should survive the port.

---

## §11 · Lessons — carrying a defect forward

A subagent has no memory across dispatches. A defect found and not written into the *next*
briefing is a defect that will recur.

### 11.0 Three learning channels, and the write path

The system learns in three separate places. They are **not** redundant, and confusing them is the
most common way to put a fact where nothing will ever read it again.

| Channel | Catches | Read by | Decays? |
|---|---|---|---|
| **Lessons** (§11) | a **recurring defect in a specific agent's output** | the briefing gate, at dispatch time | yes — `reviewAt`, or it becomes ritual |
| **Memory vault** (§8) | a **cross-session fact or working preference** that would otherwise be re-derived or re-litigated | recall, at any time | typed: principle / tool-fact / world-state (§8.2 Q4) |
| **Receipts ledger** (§12) | **apparatus-level treadmill** — building things that move nothing | a human, at `check-by` | no — rows are permanent, verdicts accrue |

The test that separates them: *who needs this next, and when?* A defect the **next dispatch of one
agent** must not repeat → lesson. A fact **any future session** needs → memory. A judgement about
**whether the work was worth doing** → receipt. A fact written into the wrong channel is not
half-useful; it is unreachable.

#### The file is keyed BY AGENT — this is the structural fact everything else depends on

The record schema in §11.1 is what sits *inside* a per-agent array. The top-level keys of the
lessons file **are agent names**:

```json
{
  "_schema": "2.0.0",
  "_comment": "Per-agent lessons as DATA, enforced at dispatch by the briefing gate.",
  "_fields": { "…": "the schema documented in §11.1" },

  "Explore":         [ { "id": "quoted-total-not-recomputed", "…": "…" } ],
  "bounded-editor":  [ { "id": "…" } ],
  "general-purpose": [ { "id": "…" }, { "id": "…" } ]
}
```

Keys beginning with `_` are metadata and must be skipped by consumers. Lookup resolves **the full
agent id first, then the bare name after any `:` prefix**, so a plugin-namespaced agent
(`vendor:agent-name`) picks up lessons filed under either form.

Without this nesting, two things elsewhere in the document are unimplementable — state it here or
they silently break:

- the **per-agent action threshold** (§7.4: two MATERIAL on the same agent), which needs lessons
  grouped by agent;
- **doctor check 6a** (§13.2: an agent with a defect verdict and no active lesson is a blocker),
  which is a join between the reliability log and this file, on agent name.

A flat list of lesson records cannot support either. The agent is the key, not a field.

#### What happens to a defect found on a Tuesday

The write path, stated as plainly as §7.7 states the verdict writer's:

```
1. You judge a return and it is MENOR or MATERIAL.                     (§7.2, one tool call)
2. You emit the verdict line, and record it:  node judge.mjs <missionId> <verdict>
3. You append the verdict to the reliability log.                       ("a defect found and
                                                                         not recorded is lost")
4. YOU WRITE THE LESSON BY HAND into the lessons file, under that agent's key.
5. The next dispatch of that agent is BLOCKED until the briefing addresses it.
```

> **Step 4 is manual, and it is the only manual link left in the loop.** This is deliberate, for
> the same reason the verdict writer is a CLI and not a hook (§7.7): a hook can see that a defect
> *occurred*, never that a **generalizable rule** was extracted from it. Auto-generating a lesson
> from a verdict would manufacture exactly the content this mechanism exists to make honest.
>
> What changed by making it manual-but-surfaced: recording happens **once per defect**, whereas
> remembering to apply it used to be required on **every dispatch**.
>
> **⚠ And be precise about what "enforced" means here, because it is weaker than it sounds.** The
> doctor reports forgetting step 4 as a *blocker* in its own report and exits 1 — but only a
> PreToolUse hook can actually veto anything (exit 2, §5.1). Exit 1 **surfaces** the omission at
> session close; it does not prevent closing. So step 4 is enforced by a **convention plus a loud
> report**, not by a gate.
>
> That distinction matters more than it looks: if you skip step 4 anyway, nothing stops you, and the
> loop silently reverts to "the lesson lives in my head" — which is the original failure. The
> mechanism that *is* hard is downstream: once the lesson exists, the briefing gate **does** block
> (exit 2). Writing it is soft; applying it is hard. Do not let the word "blocker" in a report
> convince you otherwise.

Practical authoring rules, learned the hard way:

- **`id`** is a stable kebab-case slug naming the *defect shape*, not the incident
  (`generated-vs-generator`, not `friday-graph-bug`). The slug is what a future reader greps.
- **`sourceJudgmentId`** — there is no separate judgement id in this system. Use
  `<date>/<short-task-slug>`, and record the `missionId` in the reliability-log row instead. If
  you later want true provenance, the honest fix is to make `judge.mjs` emit an id, **not** to
  invent one at authoring time.
- **Write the `requires` concepts, then test the regex against a real briefing** before trusting
  it — see §11.4. An untested `requires` is a gate that blocks the wrong dispatches.

#### Arbitration when several lessons match

Unscoped lessons apply to every dispatch of their agent, so overlap is normal:

- **All** matching lessons with unmet concepts are reported in one block, not just the first —
  otherwise fixing one reveals the next and each costs a round trip.
- Order them **MATERIAL before MENOR**, then oldest first.
- A single `lesson-ok: <reason>` overrides the whole block, not one lesson. That is a deliberate
  bluntness: per-lesson overrides invite salami-slicing the gate.
- If one agent accumulates more than ~3 active lessons, the briefing is carrying too much and the
  real lever is the agent's definition or model — not a fourth lesson.

#### Honest status of the proving mechanism

`fingerprint`, `recurrence` and `outcome` are **declared but unmechanized** in this system, and the
document would be lying by omission if it implied otherwise:

| Field | Intent | Reality |
|---|---|---|
| `fingerprint` | signature used to detect the same defect recurring | **no component compares it against anything** |
| `recurrence` | count of repeats after the lesson existed — "the only honest measure that it works" | **nothing increments it**; every record reads 0 |
| `outcome` | `unproven → holding` once comparable missions exist | **"comparable" is undefined and uncomputed**; every record reads `unproven` |

So the measured claim "7 active lessons, 0 recurrences" is **0 out of 0** — it is not evidence the
lessons work. Recognizing this is the point: the fields are a *specification of what proof would
require*, and leaving them empty is more honest than filling them with a number nobody computed.

**What closing this actually needs** (and why it is not built): a comparator that, when a new
verdict is recorded, matches the defect against active `fingerprint`s of the same agent and
increments on a hit — plus a definition of "comparable mission" narrow enough to mean something
(same agent **and** same task kind **and** a briefing that carried the lesson). Until missions of
that shape exist in volume, the counter would compute a ratio over ~2 events, which §14.6 already
says is noise wearing a percentage.

### 11.1 Record schema

```json
{
  "id":                "stable slug",
  "sourceJudgmentId":  "the run/judgement this came from — provenance, so a lesson can be re-read against its origin",
  "date":              "when recorded",
  "severity":          "DEFEITO-MENOR | DEFEITO-MATERIAL",
  "scope":             "{ taskKinds: [regex] } — when it applies. Empty/absent = always. Prevents false blocks on unrelated dispatches.",
  "requires":          "[{concept, any:[synonyms]}] — each concept checked INDEPENDENTLY; a block names which one is missing",
  "fingerprint":       "signature of the defect, for detecting RECURRENCE of the same failure",
  "status":            "active | superseded | retired",
  "supersedes":        "id of a lesson this replaces",
  "reviewAt":          "date to re-evaluate; a lesson that never expires becomes ritual",
  "recurrence":        "count of times the SAME defect reappeared after this lesson existed — the only honest measure that it works",
  "outcome":           "unproven | holding | failed",
  "guard":             "legacy v1 regex, kept only as fallback",
  "lesson":            "the prose injected into the briefing"
}
```

Three fields are the difference between a lessons file and a pile of notes:

- **`reviewAt`** — *a lesson that never expires becomes ritual.*
- **`recurrence`** — the **only honest measure** that the lesson works.
- **`outcome`** — stays `unproven` until *comparable* missions exist to compare against.

### 11.2 Worked examples

**A · scoped, MATERIAL, two independent `requires`**

```json
{ "id": "generated-vs-generator",
  "severity": "DEFEITO-MATERIAL",
  "scope": { "taskKinds": ["sweep|locate|grep|search|find"] },
  "requires": [
    { "concept": "distinguish generated from generator",
      "any": ["generat|bundle|minif|build/|artifact"] },
    { "concept": "declare search coverage",
      "any": ["coverage|paths? searched|auditable"] }],
  "fingerprint": "reports hits in a BUILT artifact and misses the versioned source that produces them",
  "lesson": "Sweeping a repo that BUILDS artifacts: it reported hits in the generated HTML and missed the generator that produces them. Accepting that would have let the next regeneration silently revert the whole edit. Require it to label generated-file hits as such AND find the source that produces them, and to declare its search coverage so a negative result is auditable." }
```

**B · unscoped (always applies), single concept, MENOR**

```json
{ "id": "evidence-from-the-wrong-mechanism",
  "severity": "DEFEITO-MENOR",
  "scope": {},
  "requires": [ { "concept": "name the mechanism inspected",
                  "any": ["mechanism|which system|inspect|empiric"] } ],
  "fingerprint": "proves a claim from adjacent tooling rather than the system the question is about",
  "lesson": "It proved a claim about recall by reading the LOCAL graph/metrics tooling, not the harness recall the question was about — right conclusion, wrong mechanism, true only by coincidence. Require that evidence come from the system that actually answers the question, and that it name which system it inspected." }
```

**C · the briefing itself caused the defect**

```json
{ "id": "concurrent-writers-one-file",
  "severity": "DEFEITO-MATERIAL",
  "scope": { "taskKinds": ["append|jsonl|manifest|log|write|output file"] },
  "requires": [ { "concept": "exclusive output file per agent",
                  "any": ["separate file|own output|per-agent file|not shared"] } ],
  "fingerprint": "two parallel agents told to append to one file; the last writer truncates the first's work",
  "lesson": "Two agents were pointed at the same JSONL with an instruction to append. The one that finished last wrote non-appendingly and destroyed 54 records from the other — silently, and it even reported 'file created' when the file was not empty. THE BRIEFING CAUSED THIS: concurrency must be removed by design, not requested in prose. Give every parallel writer its OWN output file and concatenate afterwards." }
```

### 11.3 Precedence inside a briefing

When an agent's instructions contain both quality rules and a token budget, **declare the
precedence explicitly.** A budget sitting beside content rules with no stated ordering gets
resolved by cutting whatever looks structural.

The fix that worked was *not* more emphasis — the spec already said "mandatory" and
"non-negotiable". It was:

1. Declare the budget **subordinate** to the content rules.
2. Name an **irreducible core** that survives any squeeze (e.g. Classification · Confidence ·
   confirmation step · Evidence table ≈ 5 lines).
3. Give an explicit **sacrifice order** for everything else.
4. Ban placeholder statuses (`—`) and bare counts with no reproduced line.

**Named stopping rule, so this cannot become endless prose-polishing:** if the core is dropped a
third time, the constraint is not specification — three spec attempts will have failed — and the
next lever is the agent's **model or tooling**, not more words in its definition.


### 11.4 Test the lesson before trusting it

A lesson is a regex that blocks work. An untested one is worse than no lesson: it blocks the wrong
dispatches, you start reaching for `lesson-ok:`, and the gate becomes theatre — the failure mode
§6.3 measures as bypass rate.

Two failure directions, both real:

- **Too loose** → false blocks. Concrete trap: the matcher applies no word boundaries, so a bare
  `count` matches inside *ac**count*** and *en**count**er*; `state` matches every "state of the…".
  Write the boundaries into the pattern yourself.
- **Too tight** → the lesson never fires and reads as `recurrence: 0`, which looks like success.

Test it as a table of labelled cases, including the **prompt that produced the original defect**
(it must match) and prompts from dispatches that were fine (they must not):

The real pattern, inlined so this is runnable as printed. Note every alternative is anchored —
that is the whole point:

```js
const lesson = {
  id: "quoted-total-not-recomputed",
  scope: { taskKinds: [
    "\\b(digest|resume|status|pending|backlog|tally|summari[sz]e)\\b|\\bcounts?\\b|\\bhow many\\b|\\bcurrent state\\b"
  ]},
  requires: [{
    concept: "recompute totals from the rows, never quote a stated total",
    any: ["recomput|recount|parse the (column|rows|table)|derive the count|count the rows|from the primitive"]
  }],
};

const scope = new RegExp(lesson.scope.taskKinds[0], "i");
const cases = [
  ["SHOULD",     "return a COMPACT resume-state digest"],       // the prompt that caused the defect
  ["SHOULD",     "how many pending rows are in the ledger"],
  ["SHOULD",     "give me the current state of the backlog"],
  ["SHOULD NOT", "extract the guardrail hooks, cite file:line"],
  ["SHOULD NOT", "check the account balance validation logic"], // 'count' inside 'account'
  ["SHOULD NOT", "find where we encounter the retry path"],     // 'count' inside 'encounter'
  ["SHOULD NOT", "locate the OrderDocument class definition"],
];
for (const [expect, prompt] of cases) {
  const hit = scope.test(prompt);
  console.log((expect === "SHOULD") === hit ? "PASS" : "FAIL", expect, "|", prompt);
}

// Both directions of the requires check — a matcher only tested one way is half-tested:
const req = new RegExp(lesson.requires[0].any.join("|"), "i");
console.assert(!req.test("return a digest of pending rows"));            // unmet → gate blocks
console.assert( req.test("recompute it by parsing the verdict column")); // met   → gate passes
```

> **The two `SHOULD NOT` substring cases are the ones that matter.** Drop the `\b` anchors and
> *account* and *encounter* both start matching — the lesson then blocks unrelated dispatches, you
> start reaching for `lesson-ok:`, and within a week the gate is theatre. Run this table after every
> edit to a lesson's regex, not just when you first write it.

### 11.5 Testing the gates themselves

The document's own thesis is that a silent guard is either unnecessary or broken (§1, claim 5). The
watchdog detects a gate that **never fires** — it cannot detect a gate that fires and permits
everything. That second failure is invisible by construction, so it needs a deliberate test.

**Test each gate on both sides.** A gate is only validated when you have seen it *block* something
it should and *pass* something it should not touch:

```bash
# Should BLOCK (expect exit 2)
echo '{"tool_name":"Bash","tool_input":{"command":"grep -r foo ."},"transcript_path":"/tmp/t.jsonl"}' \
  | node delegation-check.mjs; echo "exit=$?"     # expect 2

# Should PASS — bounded read (expect exit 0)
echo '{"tool_name":"Read","tool_input":{"file_path":"/big.md","limit":50},"transcript_path":"/tmp/t.jsonl"}' \
  | node delegation-check.mjs; echo "exit=$?"     # expect 0

# Should PASS — the escape hatch, and the reason must be captured, not just accepted
echo '{"tool_name":"Bash","tool_input":{"command":"grep -r foo . # inline-ok: one-off audit"}}' \
  | node delegation-check.mjs; echo "exit=$?"     # expect 0, and `overridden` in the guard log
```

Three properties worth asserting explicitly, because each one has failed in practice:

1. **The subagent exemption works** — feed a `transcript_path` under the subagent directory and
   confirm the gate allows what it would otherwise block. A gate that accidentally applies to
   subagents forbids the exact behaviour it exists to force.
2. **Fail-closed really is closed** — point `transcript_path` at a nonexistent file and confirm the
   vault gate still blocks (and logs `degraded`), rather than falling open.
3. **The override is recorded, not merely permitted** — assert the guard log gained an `overridden`
   row carrying the stated reason. An override that permits without recording is indistinguishable
   from a gate that was never there.

> Run these after **any** edit to a gate. The whole apparatus rests on gates that block; a gate
> that silently stopped blocking produces no error, no alert, and no symptom until the drift it
> prevented has already happened.

---

## §12 · Governance — the outward-validation ledger

The anti-treadmill mechanism. Without it, an apparatus like this grows forever, because every
addition can be justified by an internal number it raises.

### 12.1 The commit rule

```
A maintenance/improvement change to the apparatus enters ONLY if you can name the downstream
failure it prevents, or the REAL-WORK outcome it moves — never merely the internal number it
raises. Value visible only to the system's own instruments = treadmill candidate until proven
otherwise.
```

**The receipt.** Naming is cheap and the builder is motivated, so *the named outcome must be
checkable later.* If you cannot point to the X that stopped or the Y that moved, the justification
was ritual.

> "Held-out, not calibration" extended to the **justifications themselves**: validation cannot live
> inside the thing being validated — including the reason attached to a change.

**The visibility cut** — the sharpest test in the whole document:

| An instrument **earns** its place | An instrument is **redundant treadmill** |
|---|---|
| when the failure it catches is **silent in the work** — e.g. a retrieval miss: the right memory never surfaces and the transcript looks perfectly clean | when the failure is **self-evident in the work** — e.g. a bad lookup derails you visibly; you do not need an eval to notice |

**The hygiene score is not a goal.** A 0–100 health number exists to keep things from *degrading*.
Do not optimize it. (§15 shows exactly why: it read 100/100 while ~43 claims in the vault were
false.)

### 12.2 The ledger format

```
Rule: every apparatus/meta change gets a row BEFORE the work, naming a falsifiable real-work
outcome it will move — not an internal metric. At `check-by`, mark the verdict against reality.
A streak of miss/unclear/parked = the treadmill alarm (self-evident, no dashboard needed).
```

```markdown
| date | change | falsifiable prediction | check-by | verdict |
|---|---|---|---|---|
```

Why this is genuinely falsifiable, and not self-congratulation:

> This is **predict-then-check = a blind label applied to my own engineering** — predicted *before*
> (so it cannot be post-hoc rationalization), and adjudicated *by the world* (harder than a golden
> label, which is truth-by-fiat).

**Verdict vocabulary**, with the live tally from a real 21-row ledger:

| Verdict | n | Meaning |
|---|---|---|
| `pending` | 10 | the predicted event has not happened yet |
| `treadmill-suspect` | 2 | shipped, but nothing downstream moved |
| `miss` | 2 | the event happened and the prediction did not hold |
| `killed` | 2 | the work was cancelled before shipping — a legitimate, healthy outcome |
| `half-hit` | 1 | partially held; the honest middle |
| `hit` | 1 | held |

Note the `check-by` column also accepts a **real-world event** instead of a date ("next session with
a status question"), and `(n/a)` for a purely inward change.

> **⚠ That tally sums to 18 against a 21-row ledger, and the gap is the lesson.** The three missing
> rows are not missing verdicts — they are rows whose verdict cell **contains a `|` character**
> (inline code such as `` `/\bhit\b/i` ``, or a nested table), which defeats naive
> split-on-pipe column parsing. Reported as-is rather than quietly padded, because this is the
> document's own §15-J defect reproduced live: *a count taken with a fragile instrument and
> published without checking that it reconciles.*
>
> **What to do in your port:** always print the row count next to the tally so a gap is visible
> (`18 of 21 rows parsed`), and treat an unparsed row as `indeterminado` (§9), never as absent.
> A markdown table is a bad database — if the tally matters, either escape pipes on write or keep
> the verdicts in a sidecar JSONL and render the table from it.

> **⚠ Parser caveat, reproduced because it is the kind of bug that inflates your own score:** the
> machine parser matches `hit` with `/\bhit\b/i`, which **also matches `half-hit`**, and counts a
> miss only when bolded. The parser is looser than the vocabulary. If you port the tally, port this
> warning with it.

A row whose `check-by` date has passed while the verdict still reads `pending` must raise a warning
(§13, doctor check 5). Otherwise the ledger silently becomes a to-do list.

### 12.3 The deferred-instruments register

The other half of the mechanism: things explicitly **not** built, each with the named trigger that
would authorize building them. Reproduce this pattern; it is what stops an apparatus from eating
its owner's time.

```markdown
## Deferred instruments — DO NOT build until a named trigger fires

- meta/object time-trend classifier: build only if this ledger shows receipts being SKIPPED or
  GAMED (all-hit but suspicion remains). Trigger, not calendar.

- ~~component utilization / dead-weight~~ → BUILT, trigger fired by an explicit user request for
  per-agent usage visibility. Its receipt row is above; if that row comes back a miss, the feature
  is decoration and should be CUT, not extended.

- hook hard-block (no override): build only if the delegation-gate row comes back GAMED — the main
  thread spam-bypasses via `inline-ok`, oversized limits, or serial bounded reads across many vault
  files. Trigger = the receipt shows override-spam, not the calendar.

- Building any of these now would be the treadmill this ledger exists to catch.
```

### 12.4 Explicitly rejected — do not re-propose

Recorded so the same "improvement" is not re-litigated every few months:

| Rejected | Why |
|---|---|
| Agent frameworks (LangGraph / CrewAI / AutoGen) | The harness already supplies dispatch, isolation and lifecycle hooks. A framework adds a layer that must itself be governed. |
| Hosted tracing (LangSmith / Phoenix) | **The transcript IS the trace.** Structural metadata is already on disk in JSONL. |
| Vector DB + reranker for memory | The vault is ~120 files. Deterministic retrieval (1-hop link graph + metadata filters) beats embeddings at this scale and is auditable. |
| Merging / de-duping memories | Each memory is recalled independently; a fused blob is recalled all-or-nothing. Link them instead. |
| External-API judge | Case content never leaves the machine. |
| Generic "fine-tune the subagents" | Not a falsifiable change. Name the defect and write a lesson (§11). |
| Model-tiering eval | The failure it would detect is **self-evident in the work** — it fails the visibility cut. |

### 12.5 The hardest anti-decision

> **"When do I stop building and just use it."**
> Post-build-out, apparatus work is frozen unless it traces to a named object-level pain.
> One meta session is fine. **Two in a row is already the signal.**

The healthy end-state is a ledger where *every* open row waits on a real-world event — a PR, an
incident, a squeezed brief — and **none waits on code from you.** That is not a stall. That is the
system working.

---

## §13 · Tooling map

Small, single-responsibility scripts over one shared read layer. Every one of them is read-only
unless the name says otherwise.

| Script | Single responsibility | Reads / writes |
|---|---|---|
| `vault.mjs` | **Shared read layer.** Parses the memory vault once: files, frontmatter, `resolve()`, and the link graph (degree, adjacency, edges, broken links). Exists so **no two tools can parse the vault differently.** | reads vault; writes nothing |
| `mem.mjs` | **Retrieval.** Two deterministic tools that complement fuzzy recall: 1-hop neighbourhood (GraphRAG-lite) and metadata self-querying instead of vector similarity. | reads vault; stdout only |
| `trace.mjs` | **Session observability.** *The transcript IS the trace.* Extracts **structural metadata only** — turn counts, tool names, model ids, dispatch types, token usage, timestamps. Never message text, thinking, tool inputs or results. | reads transcripts; writes `trace.json` |
| `mine.mjs` | **Eval case source.** One subagent run = one case (brief + final output). Two deliberately separated content boundaries: `runs` returns metadata only; `show <id>` prints one run's content for human labelling, locally, **never persisted**. | reads subagent transcripts; writes metadata only |
| `metrics.mjs` | **Hygiene.** Counts by type, link degree, orphans, broken links, index drift, index byte budget, description quality, staleness → one 0–100 score. | reads vault; **writes only with an explicit `--write`** |
| `quality.mjs` | **Quality.** Memories against the §8 bar, per-agent verdicts, judgement coverage, the learning axis. | reads vault + logs; stdout |
| `watchdog.mjs` | **The guards themselves** (§6). | reads guard log + settings |
| `doctor.mjs` | **"Can I close the session?"** Registration check (§13.2). | read-only; **exit 1 on any blocker** |
| `validators.mjs` | **Allowlisted verification registry** (§13.3). | code-only assertions |
| `refresh.mjs` | **Continuous verification.** Re-checks derivable claims instead of auditing episodically. | read-only; reports drift, never edits |
| `judge.mjs` | **Verdict writer** (§7.7). | appends to the mission ledger |
| `roster.mjs` | **Roster-as-data + census** (§3). | reads roster + usage telemetry |

> **A command that reads should not write.** An early version wrote its output file on every
> invocation, so *merely looking* at vault health mutated state. Gate writes behind an explicit flag.

### 13.1 Three independent readings, deliberately not merged

```
metrics = HYGIENE (orphans, links, byte budget)
quality = QUALITY (memories vs the bar, verdicts, judgement coverage, learning)
watchdog = the GUARDRAILS themselves

NONE OF THE THREE MEASURES CORRECTNESS.
```

Each is blind to what the others see, **on purpose**. Merging them would let a clean hygiene score
launder a false vault — which is precisely what happened: the hygiene score printed 88/100, then
100/100 after cosmetic fixes, while ~43 claims in that same vault were false.

> A memory can score full marks on hygiene and still be wrong. Only an audit against source
> establishes correctness.

### 13.2 The doctor — registration, not correctness

Motivating defect: five artifacts built in one session were on disk, working, and cited by **no
memory** — invisible to every future session. *A check you have to remember to run by hand is a
check that will not be run*, so bind it to the session-stop event.

Three states it separates:

```
GRAVADO      the file exists                          (automatic)
REGISTRADO   some memory points at it                 (manual — THIS is what fails)
RECUPERÁVEL  recall actually surfaces it              (~52%, see §15-C)
```

| # | Check | Severity |
|---|---|---|
| 1 | Every apparatus file is mentioned in some memory (excluding derived/generated artifacts) | **blocker** |
| 1b | Every hook file is cited — *a guardrail nobody documents is a guardrail someone removes* | **blocker** |
| 2 | Every memory has an index pointer (active or archive index) | **blocker** |
| 3a | Edited files absent from the changelog | warn |
| 3b | A changelog item whose evidence files no longer exist — *broken evidence is worse than none* | **blocker** |
| 4 | A lesson past its `reviewAt` while still `active` | warn |
| 5 | A receipt past `check-by` still marked `pending` | warn |
| 6a | An agent with a recorded defect verdict but **no active lesson** — *lost learning* | **blocker** |
| 6b | A `miss` verdict with no lesson or changelog entry dated after it — *a miss with no consequence* | warn |
| 7 | Guard log missing or older than 3 days — the watch is blind | warn |

Two implementation rules worth stealing:

- **Require a delimited mention, not a substring.** A bare `includes("ne.mjs")` matches inside
  `"mine.mjs"` — a real bug, committed twice in one day, and then reproduced *inside the checker
  built to catch sloppiness*.
- **Compute "today" from the local date, not from `toISOString()`.** UTC shifts every `check-by`
  comparison by a day after ~21:00 in a UTC-3 timezone.

Footer printed on every run, so the tool cannot be mistaken for more than it is:

> *This verifies REGISTRATION (is there a pointer?), not CORRECTNESS (is the content true?).*

### 13.3 The validator registry — no shell, no checks defined in data

```
// NO SHELL, and NO CHECK DEFINED IN DATA.
// v1 let a data file carry {type, file, pattern, expect}. That is an allowlist only halfway:
// the TYPE was allowlisted but the ASSERTION was not — so editing the data file could silently
// change what "verified" means. Point a check at a file that trivially matches and the green
// tick is manufactured.
// Now a data file may carry ONLY a validatorId; every path, regex, ref and expectation lives
// HERE, in code, reviewed like code.
```

**Five states** (the changelog uses four — the same taxonomy minus `degraded`, which is meaningless
for a static record):

```
declared          no validator attached; nothing was checked
evidence-present  the artifact EXISTS. A weak signal, and a PERMANENT CEILING for existence
                  checks: a file being there proves nothing runs. Never promoted to verified.
verified          an assertion about CONTENT or STATE actually executed and held
degraded          the validator could not run (repo absent, binary failed, unknown id).
                  NOT a contradiction — an unknown dressed as a failure is how false alarms
                  train you to ignore alarms.
failed            the validator ran and the world CONTRADICTS the claim  ← the only news
```

Safety properties to reproduce:

- Never `exec` a shell string; pass an **argument array**, and confine every path to an allowlist of
  roots.
- `runValidator` **never throws**. A broken validator reports `degraded`, never a silent pass.
- An **unknown validator id is `degraded`, not `failed`** — a typo is a configuration problem, not
  evidence that the world contradicts the claim.
- Malformed data lines are **rejected and reported**, never skipped in silence.
- Always print the denominator: *"0 contradictions" speaks only about the N that have a validator —
  never about the M that do not.*

### 13.4 Generator-side validation — who validates the generator?

```
// This does. If someone strips the artifact self-check, the changelog entry claiming it exists
// flips to `failed` — the guarantee is not "I remember to keep it", it is a check that breaks
// loudly when the property disappears.
```

Concretely: a generator can exit 0 announcing a successful build **of a dead application**. So the
generator must validate the artifact it emitted (`new Function(src)` compiles without executing and
catches a syntax error in milliseconds) and **refuse to overwrite a working file with a broken
one**. Two registry validators then assert that those two guards still exist.


### 13.5 Operating rhythm — what runs when, and who runs it

A tool with a responsibility and no occasion never runs. Bind what you can to lifecycle events; for
the rest, name the trigger explicitly — **"as needed" means never.**

| When | What | Bound how |
|---|---|---|
| **Session start** | `watchdog --alert` — silent/bypassed/degraded gates | ✅ hook (SessionStart) |
| | eval backlog nudge — unlabelled runs, silent when empty | ✅ hook (SessionStart) |
| **Every dispatch** | sample one claim → verdict → `judge.mjs` | ⚠️ behaviour rule + post-return injection |
| **Every defect verdict** | author the lesson (§11.0 step 4) | ⚠️ manual; *surfaced* at close by doctor 6a (exit 1, not a veto) |
| **Session close** | `doctor --quiet` — registration blockers | ✅ hook (Stop) |
| | `judge.mjs --pending` — returned-but-unjudged | ⚠️ **ritual, name it or it dies** |
| **On demand — triggered, not scheduled** | | |
| before pruning an agent | `roster.mjs` census | operator question |
| after editing a gate | §11.5 two-sided gate test | **mandatory**, not optional |
| after a batch of memory writes | `metrics.mjs` (hygiene) · `quality.mjs` (the bar) | operator question |
| when a runtime claim smells stale | `refresh.mjs` | ⚠️ named "continuous", nothing makes it continuous |
| when you need eval cases | `mine.mjs` · `trace.mjs` | operator question |
| **Weekly-ish, the one that matters** | **adjudicate `check-by` rows** — mark hit/miss against reality | ⚠️ doctor *warns* when a row is overdue; the sitting-down is yours |

**Two rhythms with no owner, called out rather than left implicit:**

- **Index budget.** The always-loaded index is capped at 24 KB and you act at 67% (§14.5). *Who
  trims, and how:* when the warning fires, cut the **longest pointer lines** to ≤120 bytes — a line
  is a pointer, not a summary — and move resolved/shipped entries to the archive index (§8.4). Never
  solve it by deleting memories; the pointer is what makes them findable, and the file is what makes
  them true.
- **Curation.** Archiving has no natural trigger, so use one: when a memory's `status` becomes
  resolved, or when the index crosses its act-line — whichever comes first.

> **`refresh.mjs` is the honest failure of this table.** It is described as continuous verification
> "instead of episodic audit", and nothing schedules it. Either bind it to session start or stop
> calling it continuous. Naming that gap is cheaper than letting the word do work the code does not.

---

## §14 · How the numbers are computed

Reproduce these formulas exactly, or your numbers will not reconcile with anyone else's.

### 14.1 Error rate — **the denominator is tool results, not runs**

```js
errRate = results ? Math.round((errors / results) * 1000) / 10 : 0
// errors  = count of tool_result blocks with is_error === true  (strict === true)
// results = count of all tool_result blocks
// aggregated across all runs of that agent type; 1 decimal percent; 0 when there are no results
```

> Consequence worth internalizing: *"58.8% error"* on an agent means 58.8% of its **tool result
> blocks** carried an error flag — not that 58.8% of its missions failed. A single agent that
> retries a flaky call ten times looks catastrophic; one that fails its only call looks fine.

### 14.2 Tokens per mission

```js
avgTok = n ? Math.round(tok / n) : 0        // tok += usage.input_tokens + usage.output_tokens
```

**Cache-read tokens are tracked separately and excluded** from this average. Match this or the
numbers will not reconcile.

### 14.3 Active / idle

```js
const dispatchable = members.filter(m => !m.selfKage);   // the flag defined in §3
const active       = dispatchable.filter(m => m.runs > 0);
```

> The orchestrator is excluded from active/idle: it is the main thread, never a dispatched run, so
> counting it as "idle" would be a measurement artifact, not a fact about usage.

**There is no recency axis.** Usage files carry no per-type timestamp, so **idle means "never ran",
NOT "not run recently"** — do not let a UI imply recency it cannot back.

Keep `runs` and `dispatches` as two separate numbers. They can legitimately differ; reconciling
them into one invents precision.

### 14.4 Judgement coverage

```js
coverage = eligible ? round(judged / eligible * 1000) / 10 : null   // null, NEVER 0
```

`null` when there is nothing eligible. Reporting 0 there is the false-zero pattern (§15-I).

### 14.5 Index budget

```
MEMORY_BUDGET   = 24 KB     hard cap on the always-loaded index
ACT_LINE        = 67%       act here, not at 95% — so overflow is never discovered AT the cap
PER_LINE_CAP    = 120 bytes "a line is a pointer, not a summary"
```

### 14.6 Rate thresholds

```
MIN_N = 20    below this, rates are noise — do not cry wolf on a handful of firings
```

A rate computed over 2 events ("50% override!") is noise wearing a percentage.

---

## §15 · Known gaps

Reproduced in full, because a spec that only lists what works is marketing. Every gap states what
it is, why it matters, and **what would close it**. All live numbers dated **2026-08-31**.

### 15.0 · Failure-class coverage matrix — what is watching what

The individual gaps below are symptoms. This table is the diagnosis: for each way the system can
fail, which instrument catches it, and — the column that matters — which classes **nothing**
catches. Compiled by collecting every uncovered failure the rest of this document mentions only as
a passing aside.

| Failure class | Caught by | Would falsely report clean | Verdict |
|---|---|---|---|
| Context bloat via bulk ops | `delegation-check` branch A/C | — | ✅ covered |
| Context bloat via whole-vault reads | vault gate (§5.3) | size thresholds — blind to 50–320 line files | ✅ covered, *after* this specific blindness was found |
| A gate stops firing entirely | watchdog liveness (§6.3) | the gate itself — silence looks like health | ✅ covered |
| A gate fires but permits everything | **§11.5 two-sided test — manual, on demand** | watchdog liveness (it sees firings, not correctness) | ⚠️ human-only |
| Subagent output is wrong | orchestrator sample-verify (§7.3) | the return's own formatting; `file:line` disarms scrutiny | ⚠️ human-only, 5.9% applied |
| Same agent defect recurs | briefing gate (§11) | `recurrence` — declared, unmechanized (§11.0) | ⚠️ gate covers, measurement does not |
| Apparatus treadmill | receipts ledger (§12) | any internal metric | ⚠️ human-only, at `check-by` |
| Memory content is FALSE | **nothing** — audit against source only | hygiene score: read 100/100 with ~43 false claims | ❌ **uncovered** (§15-I) |
| Verdict spoken but never recorded | **nothing** | coverage — it counts records, not judgements | ❌ **uncovered** |
| Background return never judged | **nothing** — `judge-return` fires at launch | its own `intervened` count (§15-E) | ❌ **uncovered** |
| Unsupervised agent loop / runaway | **nothing** — the Jounin layer is empty (§2.4) | — | ❌ **uncovered, deliberately** |
| Editor exceeds its file-count cap | **nothing** — the agent polices itself | the agent's own report | ❌ **uncovered**; self-certification caps at `provavel` (§9.2) |
| Mission rank declared but ignored | **nothing** — ritual with no telemetry | — | ❌ **uncovered, deliberately**; but note the trigger that would authorize enforcement can never fire, so "deliberate" here is closer to *stuck* than to *chosen* |
| Model alias silently pinned to an old generation | **nothing** — §3.2: "it never errors, so nothing surfaces the drift" | the agent runs fine on the previous generation | ❌ **uncovered**; closable by grepping recorded model ids after any provider cutover |
| Ledger rotation makes coverage non-reconcilable | **nothing** — §4.5.3 | coverage keeps returning a plausible number | ❌ **uncovered**; closable by windowing the query or folding before rotation |
| An `inline-ok:` reason that is stated but hollow | **nothing** — only a *missing* reason is flagged as `unstated` | the override count, which sees a reason and is satisfied | ❌ **uncovered** |
| A hook crashes mid-check | watchdog `error` action | the tool call itself — it proceeds ungated (fail-open) | ⚠️ detected after the fact, never prevented |
| Prompt injection via subagent-read content | **nothing** | everything — the text looks like a normal finding | ❌ **uncovered** (see below) |
| **The operator's attention budget** | **nothing** | every instrument — each one reports its own health while the *sum* of them is the cost | ❌ **uncovered, and structurally so** (see below) |

> **Read the two ❌ patterns.** First: *every* class where the only instrument is the orchestrator
> judging itself is uncovered in the strict sense — self-certification caps at `provavel` (§9.2),
> so the system's own doctrine says these are unproven, not safe. Second: two of the uncovered
> classes are uncovered **on purpose** — the Jounin coordinator layer and mission-rank enforcement —
> because no trigger has fired. Deliberate absence and unnoticed absence look identical in a table,
> so the Verdict column marks which is which; that distinction is the whole point of building the
> matrix rather than a checklist.
>
> **And watch the failure mode inside the deliberate ones.** "We will build it when the trigger
> fires" is only honest if the trigger *can* fire. Mission-rank compliance has no telemetry, so its
> trigger is unobservable — which makes it indistinguishable from a decision never to build. Where
> you defer on a trigger, check that something is actually watching for it, or write down that
> nothing is.

#### The line with no telemetry: the operator's attention

Count what this system asks of one person: **nine instruments**, **four files written by hand**
(lessons, receipts, patch-notes, the vault), a per-dispatch verdict, and a weekly adjudication
ritual. Hygiene has a score. Quality has five indicators. The guardrails have a watchdog. The
treadmill has a ledger.

**The operator's time is the only line in the budget with no instrument on it at all** — and it is
the one input every other line silently draws from. Every check in this document costs attention to
run and attention to read; nothing anywhere sums that cost, so it can only ever be discovered by
burnout or abandonment, both of which look like "the system stopped being used" rather than "the
system cost more than it returned".

**Do not fix this by measuring it.** A tenth instrument that tracks the cost of nine instruments is
the treadmill in its purest form, and §12.1's visibility cut rejects it: the failure is *self-evident
in the work* — you notice the day it is too much. The correct responses are the cheap ones:

- **Prefer deleting an instrument to adding one.** Every component here should be able to name what
  it would take for it to be removed. Two already do: the claim manifest carried "if never read,
  delete it — do not add fields", and was deleted on exactly that basis; the utilization view
  carried "if its receipt comes back a miss, cut it, do not extend it".
- **Bind checks to lifecycle events, never to discipline** (§13.5). A check you must remember costs
  attention twice: once to run, once to remember.
- **Freeze deliberately.** §12.5's "hardest anti-decision" is a budget rule for attention wearing
  the clothes of a governance rule. The healthy end state is a ledger where every open row waits on
  the world and none waits on your code.

#### The untrusted-input boundary, stated because the document otherwise ignores it

A subagent's return is **text the orchestrator did not write**, and its content is derived from
files, tool output and web pages the subagent read. It then flows into: the post-return regexes
(§7.8), the orchestrator's reasoning, and frequently a permanent record. The escape hatches
`inline-ok:` and `lesson-ok:` are plain-text tokens matched against that same channel.

Consequences to design around, none of which this system currently handles:

- Content a subagent read can contain text shaped like instructions, or like the escape tokens.
  **Treat every return as data to be judged, never as instructions to be followed** — which is,
  conveniently, exactly what §7 already demands for correctness reasons.
- The gates match tokens on the **main thread's own** tool inputs, not on returned content. Keep
  that boundary: if a gate ever reads subagent-returned text to decide whether to block, the gate
  becomes controllable by whatever that agent read.
- The ledger's privacy rule (no prompt text, no paths, no session ids — §7.6) also limits the blast
  radius here: content that is never persisted cannot be replayed out of the logs later.

This is a boundary statement, not a threat model. A real one would enumerate the trust levels of
each input channel and is **not** attempted here — flagged as absent rather than sketched, because
a half-specified security model reads as coverage and is worse than an acknowledged gap.

### A · The blind judge is overfit — NOT gate-ready

Per-set agreement within ±1: **calibration 8/8 · held-out 6/6 · FRESH 6/9 = 67%** (55.6% blind-only).
The blended "87% across all 23 cases" is **inflated** by 14 lineage cases scoring 100%. Honest
signal: **investigator family 50% (3/6), fresh 62% (8/13)** — both under the 80% bar.

**Root cause:** the calibration set contained **zero** cases from the families that now diverge.
**Why it matters:** the eval cannot block a rubric regression, so automated gating stays blocked.
**Closes when:** a fresh set of *new* runs from the diverging families scores ≥80% within ±1 with no
regression on calibration/held-out. **Blocked by:** the golden set sits at 27 of ~30 and needs
human blind labels — *ground truth cannot be fabricated.*

### B · Judgement coverage 5.9%

**14 judged / 237 runs.** The manifest sub-metric is worse: of 106 auditable claims, only **8.5%**
were independently re-verified — `corrected: 74 · confirmed: 22 · superseded: 4 · unverifiable: 6`,
meaning **97 rest on agent verification alone.**

**Why it matters:** one return in twenty gets judged, so the reliability log is a count, not a rate,
and the §7.4 two-MATERIAL threshold can never trigger honestly. **Closes when:** coverage reaches
50% (the threshold that promotes the indicator from `partial` to `observed`).

### C · Recall key at 52%

Live: **Q1 52% · Q2 96% · Q3 67% · Q4 83% · Q5 81%** (n=120).

Q5's jump from 49% to 81% is a **definition change, not an improvement** — it was rewritten to
demand the source authoritative *for the claim type* (§8.3). Q1 is essentially flat.

**Why it matters:** roughly half the vault would not be found by a future search, **and Q1 fails
silently** — the memory simply never surfaces, and nothing reports it.

> **⚠ 2026-08-31 — the Q1 number is measuring the wrong thing, and the defect is one this system
> already fixed once.** The heuristic is
> `` /`|\.(kt|go|ts|js|yml|json)|[a-z]+_[a-z]+|[A-Z][a-z]+[A-Z]|\d{3}\b/.test(desc) && desc.length >= 80 ``
> — it detects whether a description contains an **identifier-shaped token** (backtick, file
> extension, snake_case, CamelCase, three digits), which is a *proxy* for findability, not
> findability.
>
> Measured by claim type: **behaviour 65% · runtime 65% · principle 33% · preference 27%.** Memories
> about code and infrastructure naturally carry identifiers; memories about *how to work* do not.
> **38 of 120 memories are being scored against a test they cannot pass by construction.**
>
> This is precisely the **Q5 v1 defect** (§8.3): Q5 demanded a `file.kt:123` citation from every
> memory and thereby "mismeasured roughly half the vault: a user preference is not grounded in
> code." Q5 was fixed by making the expected source a function of the claim type. **Q1 was never
> given the same treatment**, because the Q5 fix was framed as being about *source authority*
> rather than about *claim-type blindness as a class* — so the sibling criterion kept the bug.
>
> **Consequence for anyone acting on these numbers:** do not optimize Q1. Reaching 100% would mean
> stuffing identifier-shaped tokens into descriptions that have no identifiers, which improves the
> score and not the recall — gaming, by the definition this document uses everywhere else. Judge a
> description by *"are these the words I would actually type when I have this problem?"* and treat
> the score as a weak signal for two of the four claim types.
>
> Empirical note from the session that found this: six worst-scoring descriptions were rewritten as
> symptom-plus-proper-noun recall keys. All six read as materially more findable (author's judgement,
> therefore capped at `provavel` per §9.2); **the score moved on three**, and those three passed
> because they happened to contain `CWE-1390`, `SSHIP-4255` and `BigQueue`. The three that still
> fail are the ones whose subject has no identifier to carry.

**The sharpest instance:** 8 memories score ≤2/5, and one of them is the **governing
outward-validation rule itself, at 1/5.** The rule that authorizes every other change is among the
least recallable files in the vault.

### D · The claim manifest may be pure bureaucracy

106 records written; **no audit has consumed them since.** Its own declared falsifier:

> If the manifest is written once and never read on the next audit, it is bureaucracy — and the
> reply is to **delete it**, not to add fields.

**Closes when:** the next audit *starts from* the manifest instead of from scratch.

### E · The post-return judge misses background returns

Material limitation, found on first real use:

> The hook fires on the `PostToolUse` of the **dispatch**, not on the arrival of the result. For
> agents launched in the **background**, the return arrives through a task notification and **the
> hook does not fire again** — it read the launch confirmation instead, and its negative-claim
> detector even matched text in that confirmation rather than in any finding. On the exact scenario
> that motivated it, it fires early and misses the moment that matters. **It covers synchronous
> dispatches only.**

Confirmed again while this document was being written: four parallel background dispatches produced
four judgement prompts **at launch**, ~70–310 seconds before any result existed.

**Closes when:** the background case is detected and re-injected on the notification path, or the
hook drops to a stop/notification event.

### F · Idle roster — and the correction that matters more than the number

First reading: **16/46 active, 30 never dispatched** — including the digest agent that was skipped
during that very session's own resume. Later split by ownership: **3 idle agents are hand-written,
23 are plugin/kit-owned**, where idleness is a category error rather than neglect.

The durable lesson, which was a **correction of a wrong conclusion**:

> **Low usage of an isolation mechanism is evidence about who dispatches, not about what it is
> worth — check the operator before pruning the tool.**

The row's verdict stays **half-hit**: "dispatch instead of reading inline" is still a miss.

### G · Built ahead of demand — the meta-gap

> The idle numbers are not capability gaps, they are **capability built ahead of demand**. The
> correct move is to STOP building and let real work consume what exists. All open receipts now
> wait on a real-world event; **none waits on code from me.**
>
> Falsifier: *if a future session opens by building another instrument while these rows still say
> pending, that is the treadmill resuming.*

**Status: the register has grown from 8 pending rows to 10, and instruments kept shipping.** By its
own falsifier this row is arguably already a `miss` and is still marked `pending`. Recorded here
rather than quietly re-scored.

### H · Live instrument flags

- **Hygiene reads 100/100 while carrying three warnings that contradict it:** 9 archived memories
  whose claims were corrected but which carry **no supersession marker** (so recall still delivers
  them as truth); **93 index lines over the 120-byte pointer cap**; the index at **70% of budget**
  — past the act-now line. *A perfect score with three open warnings is the shape of a metric that
  is not load-bearing.*
- **Registration doctor: clean.** 0 blockers, 0 warns.
- **Watch: 492 firings / 14 days.** Delegation gate 34 blocked / 410 passed / **12 overrides**;
  briefing gate 8 blocked / 4 overrides; post-return judge 13 interventions.
  **10 registered hooks are SILENT** — under the watch's own rule that *silence ≠ health*, each is
  either unnecessary or broken, and both require action.
  Note: those 12 overrides are the live input to the deferred **hard-block** trigger (§12.3), which
  fires on *override-spam* — **but no threshold has ever been declared, so that trigger is currently
  unfalsifiable.** A deferred instrument whose trigger cannot fire is deferred forever.
- **Learning axis: 7 active lessons · recurrence of the same defect 0 · lessons with a proven
  outcome 0/7.** "Zero recurrences" across **zero comparable missions** is 0/0 wearing a zero's
  clothes. Per-agent sample sizes are tiny (n≤8); *one MATERIAL at n=5 does not distinguish a bad
  agent from a bad briefing.*

### I · Nothing here measures correctness

The load-bearing gap, asserted independently in three places in the source system. Hygiene, quality
and guardrail readings are **all blind to truth**.

**The evidence:** ~43 false claims sat in a vault scoring **100/100**.

**Only an audit against source closes it** — and the instrument built to make that audit repeatable
is gap **D**, still unread.

### J · Small defects found while writing this document

- **The read gate's escape hatch does not match its own message.** Four block messages instruct the
  reader to "pass offset+limit", but the code disarms on `limit` alone: `if (ti.limit) allow();`.
  Passing only `offset` does **not** disarm the gate. Harmless in practice, but it is a message that
  lies about its own mechanism — precisely the class this system claims to hunt.
- **A count taken from line numbers instead of table rows** produced "11 pending" where the ledger
  has **10** in 21 data rows. Caught by a delegated extraction contradicting the orchestrator.
  Logged rather than quietly corrected, per §7.5.

---

## §16 · Porting to another harness

### 16.1 What the harness must provide

| Capability | Used by | Degradation if absent |
|---|---|---|
| **Subagents with isolated context** | everything | The whole model collapses; delegation buys nothing |
| **Pre-tool hook that can BLOCK** (non-zero exit surfaced to the model) | §5 gates | Guardrails become suggestions. **Proven insufficient** — the per-turn text nudge alone failed twice in one session |
| **Post-tool hook that can inject context** | §7.8 | Judgement becomes purely voluntary |
| Session-start / session-stop events | watchdog, doctor | Checks you must remember to run will not be run |
| **Stable call id across pre/post events** | §7.6 ledger | Verdicts lose their denominator; coverage becomes unmeasurable |
| A readable transcript on disk (JSONL) | §5.3 turn scan, §14 metrics | The vault gate cannot detect "a digest already ran this turn"; all usage metrics disappear |
| Per-agent model selection | §3.1 | Everything runs on one tier — workable, more expensive |

### 16.2 Event mapping

| This spec | Claude Code | Generic agentic IDE |
|---|---|---|
| PreToolUse (blocking) | `hooks.PreToolUse[].command`, **exit 2** | a pre-execution middleware that can veto a tool call |
| PostToolUse (injecting) | `hooks.PostToolUse[]`, stdout `additionalContext` | post-execution middleware that can append to the model's context |
| UserPromptSubmit | `hooks.UserPromptSubmit[]` | a prompt preprocessor |
| SessionStart / Stop | `hooks.SessionStart` / `hooks.Stop` | lifecycle callbacks, or a shell wrapper around the session |
| Dispatch a subagent | `Agent(subagent_type, prompt)` | whatever spawns an isolated sub-session |
| Stable call id | `tool_use_id` | any per-call correlation id present in both phases |

**If your target has no blocking hook**, do not simply downgrade to reminders — that is the failure
mode this system already measured. Wrap the tool layer yourself: a thin proxy in front of
file-read / shell / search that applies §5.2 and returns an error the agent must read.

### 16.3 What to rename

Everything in `§3.1` is an **archetype**, not a product. Keep the archetype and its output contract;
throw away the names. The rank vocabulary is worth keeping *because it is memorable* — an
orchestrator that has internalized "I am the Hokage, I judge the reports" behaves differently from
one told "please validate subagent output".

---

## §17 · Minimal viable subset

Do not build all of this. Build it in this order, and stop when the next item has no named trigger.

**Tier 0 — the two that pay for themselves immediately**

1. **The delegation gate** (§5.2). One pre-tool hook. Blocks unbounded reads, recursive greps and
   archive extraction, with an `inline-ok: <reason>` escape that logs the reason. This is the single
   highest-value component, because context bloat never errors.
2. **The verdict habit** (§7.2–7.4). No code at all — a rule that every subagent return gets one
   sampled check and one verdict line before it is used. Costs about one tool call.

**Tier 1 — once you have more than a handful of memories**

3. **The memory format + quality bar** (§8). Frontmatter, one fact per file, the V1/V2 gates. Skip
   the machine scoring at first; the two value tests do most of the work.
4. **The receipts ledger** (§12). A single markdown table. This is what stops you from building
   Tier 2 forever.

**Tier 2 — only after a real failure justifies each one**

5. Telemetry logging + the watchdog (§6) — trigger: *a guardrail failed silently and you found out
   downstream.*
6. Lessons + the briefing gate (§11) — trigger: *the same subagent defect happened twice.*
7. The mission ledger (§7.6) — trigger: *you cannot answer "what fraction of returns did I judge?"*
8. The blind judge + rubric (§10) — trigger: *you need to compare agent quality across many runs,*
   and note §15-A: expect it to be usable for spot-checks and **not** gate-ready.
9. The doctor and validator registry (§13.2–13.3) — trigger: *an artifact you built went missing
   from every record.*

**Never build without a trigger:** anything in §12.3 or §12.4.

---

## Appendix · One-page cheat sheet

```
DISPATCH        state role + mission rank inline:  "1 Genin [locator] + 1 Chuunin [reviewer], C-rank"
                independent units → ONE message, parallel
                one writer per output file, always

DON'T DISPATCH  ≤3 tool calls · <5 lines out · already in memory · you're authoring the artifact

ON RETURN       sample ONE load-bearing claim  → Verdict: <agent> — OK | MENOR | MATERIAL | NAO_VERIFICADO
                load-bearing = permanent record · negative claims · ids/hashes/timestamps ·
                counts with no reproduced line
                file:line proves the LINE EXISTS, not that it answers your question
                2× MATERIAL on one agent → re-brief it or change its model

TRUTH           assumed → probable → confirmed        (confirmed REQUIRES a declared falsifier)
                existence · no-falsifier · self-certification  → all CAPPED at probable
                "could not check" ≠ "checked and found nothing"  → indeterminate, never 0
                downgrade is free, promotion is expensive

MEMORY          V1 what decision changes?   V2 what breaks without it?   ← fail either = don't save
                Q1 findable  Q2 actionable  Q3 provenance  Q4 dated  Q5 right source for the type
                store the command, not the number

BEFORE BUILDING name the downstream failure it prevents · write the receipt row FIRST ·
                if the failure is self-evident in the work, the instrument is treadmill

ALWAYS ASK      "what would this look like if the instrument were broken?"
                same → it is not evidence
```

---

*Derived from a running system, including its measured failures. Every number in §15 is real and
dated. If you port this, port the gaps too — a specification that only describes what works will
teach you the wrong lesson.*
