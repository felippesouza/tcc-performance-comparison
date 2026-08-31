# 🥷 Konoha — Agent Orchestration & Self-Auditing Apparatus

> A portable specification for running a multi-agent coding assistant with **delegation ranks**,
> **enforced guardrails**, **calibrated judgement**, and an **anti-treadmill governance ledger**.
>
> Harness-agnostic. Written to be reimplemented on any agentic IDE that supports subagents and
> lifecycle hooks (Claude Code, Antigravity, Cursor, or a hand-rolled loop).

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
| **investigator** | Chuunin | mid | Diagnosis from external data (logs/metrics/traces). Bounded token budget with a declared irreducible core (§11.2). |
| **test-writer** | Chuunin | strong | Tests that assert behaviour at the observable layer. |
| **coordinator** | Jounin | inherit | The only rank that may dispatch. Breaks up large missions, guards loops. |

**Model assignment heuristic:** cheap/fast model for mechanical lookup (≤3 tool calls); mid model
for reasoning plus multi-tool orchestration; strong model for authoring, judging and design.
Pick the **role first** — it pins both the tool scope and the model.

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
  the mission ledger possible (§7.4)
- the transcript is JSONL, and tool results appear as `user`-role entries containing
  `tool_result` blocks

### 5.2 The delegation gate — complete logic

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

1. **Bounded read** → allow.
2. **No path** → allow. **Binary/visual** (`png|jpe?g|gif|webp|bmp|svg|pdf|ico|heic`) → allow;
   visual content is not text bloat.
3. **Vault gate** (see 5.3).
4. **Size**: `> 60000` bytes → block. **Line count**: `> 800` lines → block. A stat/read failure
   → allow (the target may be a file about to be written).

#### Branch C — structured search

```js
const contentMode = input.output_mode === 'content';
const noCap       = input.head_limit == null;
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
Then emit: Verdict: <agent> — OK | DEFEITO-MENOR | DEFEITO-MATERIAL
```

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
| memory Q3 | verified / inferred / reported | confirmado / suposicao / provavel |

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
Output: { D1..D5: 0|1|2, holistic: 0-10, verdict: PASS|FAIL,
          gateHit: null|"D1"|"D4", rationale: one line }

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
  dropped to ~60%**, isolated almost entirely to one agent family.

**Conclusion, stated plainly: the judge is usable for spot-checks and is NOT gate-ready.** Do not
wire it into CI. This is the single most important caveat in §10 and it should survive the port.

---

## §11 · Lessons — carrying a defect forward

A subagent has no memory across dispatches. A defect found and not written into the *next*
briefing is a defect that will recur.

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
| `doctor.mjs` | **"Can I close the session?"** Registration check (§13.1). | read-only; **exit 1 on any blocker** |
| `validators.mjs` | **Allowlisted verification registry** (§13.2). | code-only assertions |
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
const dispatchable = members.filter(m => !m.selfOrchestrator);
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
  reader to "pass offset+limit", but the code disarms on `limit` alone: `if (input.limit) allow();`.
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

ON RETURN       sample ONE load-bearing claim  → Verdict: <agent> — OK | MENOR | MATERIAL
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
