# Phase 3 — Verify loop: prompts, schema, rounds, dispositions

## Contents
1. The verdict schema (+ harness portability of the return channel)
2. Fidelity verifier template (common preamble + focus splits)
3. Isolation before dispatch (§3.0) · blind buildability verifier template
4. Model & effort routing
5. Round procedure and bookkeeping
6. Dispositions and the deviations ledger
7. Stop conditions and re-verify scoping
8. Tier A: Workflow script template · Tier B/C procedures

---

## 1. The verdict schema

```js
const VERIFY_SCHEMA = {
  type: 'object',
  required: ['verdict', 'discrepancies', 'notes'],
  properties: {
    verdict: { type: 'string', enum: ['pass', 'fail'], description: 'fail if any critical discrepancy exists' },
    discrepancies: {
      type: 'array',
      items: {
        type: 'object',
        required: ['severity', 'what', 'correction'],
        properties: {
          severity: { type: 'string', enum: ['critical', 'minor'] },
          what: { type: 'string', description: 'The problem, quoting or citing the spec section/line concerned' },
          correction: { type: 'string', description: 'Concrete replacement or added text that would fix it' },
          sources: { type: 'array', items: { type: 'string' }, description: 'URLs supporting the correction (fidelity verifiers only)' },
        },
      },
    },
    notes: { type: 'string', description: 'Overall assessment, 2-5 sentences' },
  },
}
```

The `correction` field is the loop's engine: demand *exact replacement text*,
not advice. You will usually apply it verbatim — verifiers writing their own
fix text produce better prose than your paraphrase of their complaint.

**Harness portability of this schema.** `schema:` is a Tier A (Workflow/agent)
mechanism. The line `Return ONLY via the structured output schema.` at the end
of the §2 and §3 templates is a SLOT, not literal text — substitute it before
the prompt leaves your context:

- **Tier A**: keep the line, and pass `schema: VERIFY_SCHEMA` on the agent call.
- **Tier B/C**: replace the line with exactly this:

  ```
  Return your answer as ONE fenced ```json block and nothing else, matching
  exactly this shape:
  {"verdict":"pass|fail",
   "discrepancies":[{"severity":"critical|minor","what":"...",
                     "correction":"...","sources":["url"]}],
   "notes":"..."}
  No prose before or after the block. verdict=fail if any critical.
  ```

  Tier B: parse that block out of stdout. If it does not parse, re-run the
  verifier ONCE with "Your last answer was not valid JSON. Return only the JSON
  block." prepended, then hand the raw stdout to the user. **Never hand-fill a
  verdict you did not actually receive** — a fabricated verdict row is worse
  than a missing round.

The same slot rule applies to tool names. `WebSearch` / `WebFetch` /
`ToolSearch` are Claude Code names; outside it, say "use whatever web search and
page-fetch tools this session exposes — list your available tools first if
unsure". Never leave a tool name in a prompt that will run outside the harness
that defines it.

## 2. Fidelity verifier template

Fidelity verifiers get web access and the ground truth. Common preamble
(interpolate `{...}`; the deviations ledger grows every round):

```
ROLE: clean-context fidelity verifier.
Read the file at: {ABSOLUTE_PROMPT_PATH}
(If that exact path fails, it is at {RELATIVE_PATH} relative to {WORKSPACE}.)
It is a replication spec that deliberately never names the real {game/product}
it replicates. GROUND TRUTH: the real target is {REAL_TITLE} ({developer/vendor},
{year}, {platforms}).
Independently research the real target using web search/fetch tools (load
them via ToolSearch first if they appear deferred). Do NOT trust the spec;
verify it against reality. Check the spec claim-by-claim within your focus area.
INTENTIONAL DEVIATIONS — do NOT flag any of these:
{numbered deviations ledger: restyle, renames, slice scope, invented tuning
("judge tuning DIRECTIONALLY only"), "PART 3 is test-harness machinery, not
content — ignore it for fidelity", plus every deviation accepted in previous
rounds, each described concretely}
FLAG AS CRITICAL: a spec element that contradicts the real target's core
identity; an invented core mechanic/behavior the real target does not have; a
missing element essential to the real target's core loop within the slice.
FLAG AS MINOR: small drift in flavor, staging, or emphasis.
For every discrepancy: quote the spec passage, give exact correction text,
and cite source URLs you actually consulted.
Return ONLY via the structured output schema. verdict=fail if any critical
discrepancy.
```

Append one **focus block** per verifier:

- **Games — mechanics & systems**: "YOUR FOCUS: mechanics and systems
  fidelity. Verify: {enumerate the slice's core mechanics with their spec'd
  behaviors — movement verbs, combat verbs, health/economy rules, enemy
  behaviors, boss patterns and phases}."
- **Games — content, story & tone**: "YOUR FOCUS: content, structure, story
  and tone fidelity. Verify: {premise, protagonist characterization, NPC
  flavor, collectibles, tone words critics used, opening progression
  structure, boss identity/staging, presentation beats}."
- **Software — behavior & data**: workflows step-by-step, object model,
  state transitions, validation rules, shortcuts.
- **Software — UX, content & visual**: layout, navigation, microcopy voice,
  empty/edge states, visual system.
- **Games — presentation & style** (use in place of "content, story & tone"
  when the target is story-light or its look is the identity): "YOUR FOCUS:
  presentation fidelity. Verify: {the palette table and colour-role discipline
  against documented palettes; resolution/aspect and sprite proportions;
  animation stepping; HUD content and placement; juice inventory; audio
  character and composer credit; results/death screen; the tone words critics
  actually used}." When you use this split, confirm the mechanics verifier's
  focus block explicitly absorbs progression, economy, and level-generation
  rules so nothing falls between the two.

Writing the focus enumerations concretely (naming the specific behaviors to
check) is what makes fidelity verification sharp — a bare "check mechanics"
returns generic praise.

## 3.0 Isolation before dispatch — do this before EVERY blind dispatch, at every tier

The blind verifier must not learn the target. Three leaks are easy to ship:

1. **The path names the target.** `.liang/prompts/kunai-replication/prompt.md`
   tells the verifier the answer before it reads a line. Copy the current
   `prompt.md` to a neutral path with a neutral filename and give the verifier
   only that: `<tmp>/spec-under-review-r<N>.md`, regenerated each round.
   Never interpolate the bundle path into `{ABSOLUTE_PROMPT_PATH}` for the
   blind role, and drop the `{RELATIVE_PATH} relative to {WORKSPACE}` fallback
   line from the blind prompt entirely.
2. **The bundle directory is radioactive.** `README.md`, `research/`, and
   `verification/` all name the real target. Never give the blind verifier a
   directory — only the single neutral file — and append to its prompt:
   "Do not list, open, or read any file other than the one named above."
3. **Harness memory leaks.** A fresh subagent or a `pi -p` process usually
   still auto-loads project/user memory (CLAUDE.md, AGENTS.md, MEMORY.md) from
   its working directory, and if you have ever noted this project there, it
   names the target. Launch blind verifiers from a directory outside the
   workspace, or with project-instruction/memory loading disabled, and put the
   neutral copy there too.

Fidelity verifiers are exempt — they are given the ground truth on purpose.
If your harness cannot guarantee 1–3, say so in `verification/round-N.md` and
in the README: "blind verification ran with possible target exposure; its
verdict is weaker evidence than the reference run's."

This is not a portability nicety. The reference run leaked leak #1 — its blind
verifier was told to read a path containing the target's name while being
instructed not to identify the target.

## 3. Blind buildability verifier template

The blind verifier simulates the prompt's actual consumer. It is the star of
the loop — in the reference run it found every critical. Never cut it.

```
ROLE: blind buildability verifier.
Read the file at: {ABSOLUTE_NEUTRAL_COPY_PATH}
Do not list, open, or read any file other than the one named above.
This document will be pasted, alone, to various AI models that have NO web
access and no other context. Each must produce {the deliverable, e.g. "a
playable 2D HTML game"} from this text alone. Your job is to judge whether
THIS TEXT ALONE reliably produces a {playable/usable}, complete, great-looking
result.
HARD RULES: Do NOT use web search or fetch tools. Do NOT try to identify
which real {game/product} this might be; even if you think you recognize it,
that is irrelevant — judge ONLY the self-sufficiency and internal coherence
of the document.
HUNT FOR:
(1) Ambiguity: any instruction a diligent implementer could reasonably
    interpret two ways that materially changes the result.
(2) Contradictions: numbers vs described feel; criteria tables vs spec
    sections; {domain gating math — see below}. Verify every criteria-table
    row references only things the spec actually defines, with matching numbers.
(3) Missing values: anywhere "feel" matters but no number or rule is given.
(4) Unexecutable {art/visual} direction: demands an AI cannot act on without
    external references, or that conflict with each other or the medium.
(5) QA protocol executability: can a chat-only model with no execution
    actually follow the embedded protocol as written? Are the verifier
    prompts truly self-contained? Are stop conditions unambiguous?
(6) Scope realism: is this buildable to the stated quality bar by a strong
    AI in one working session? If a section is disproportionately expensive
    vs its value, say so.
(7) Omissions: anything a {deliverable} of this shape needs that the spec
    forgot entirely ({e.g. camera rules, win/lose flow, edge cases}).
SEVERITY: critical = likely to cause a broken, unusable, visually wrong, or
protocol-unfollowable result; minor = polish drift.
For every discrepancy: quote the offending passage (or name the gap), and
give the exact corrected/added text.
Return ONLY via the structured output schema. verdict=fail if any critical
discrepancy. In notes, include your overall verdict on whether you would bet
on a strong AI producing a top-notch result from this document alone.
```

Domain gating math to name explicitly in (2):

- **2D game**: jump distances, gap widths, ability range/angles vs stated
  level geometry — can the mandatory route be traversed? Can forbidden
  shortcuts actually be prevented?
- **3D game**: traversal reach vs spatial layout, camera sightlines vs
  landmark navigation, encounter space vs enemy counts.
- **Software**: workflow closure — does every state have an exit? Do
  preconditions for each step exist in the spec? Can the demo/seed data
  exercise every specified behavior?

## 4. Model & effort routing

The routing IS the method: a cheap blind verifier finds nothing, and top-tier
fidelity verifiers just burn money. Route explicitly at every tier, and record
the model that ACTUALLY ran in `verification/round-N.md` — "unknown" is an
acceptable entry, a blank is not.

- **Fidelity**: mid-tier model with web access, two of them, different focuses,
  parallel where possible (reference run: Sonnet).
  - Tier A: `model: 'sonnet'` on the agent call.
  - Tier B: the harness's model flag on the one-shot call (e.g.
    `pi -p --model <mid-tier> …`). If your CLI has no model flag, tell the user
    and note it in round-N.md.
  - Tier C: no routing exists — you are the model. Note that.
- **Blind**: the strongest model available, highest reasoning effort, no web
  (reference run: the session's own top model at high effort). Same-family
  self-verification is fine — the clean context does the isolation.
  - Tier A: `effort: 'high'` plus the strongest `model` available.
  - Tier B: pass the strongest model flag the CLI exposes; **do not let it
    default** — the default is usually the cheap one.
  - Tier C: you cannot upgrade the model, so buy rigor with procedure instead —
    run the blind pass FIRST, in a fresh message, before reopening any research
    file, and require yourself to quote each passage before judging it.
- **Researchers**: cheapest capable model at Tier A/B; at Tier C, you.

If you cannot honour the blind-verifier routing at your tier, tell the user
BEFORE the round runs, not after.

## 5. Round procedure and bookkeeping

1. Dispatch all of the round's verifiers in parallel against the current
   `prompt.md` on disk.
2. Collect schema'd results. Tabulate: verifier | verdict | #critical | #minor.
3. Disposition every finding (§6). Apply fixes to `prompt.md`; bump its
   version header (v1 → v2 → ...).
4. Write `verification/round-N.md`: header (round, spec version, which
   verifiers ran and their models), verdict table, then a findings table with
   per-finding disposition. In the final round add a ledger table across all
   rounds (round | spec version | each verifier's verdict | criticals
   found → fixed).
5. Announce the round's outcome briefly to the user (if interactive), then
   either loop or stop per §7.

## 6. Dispositions and the deviations ledger

Every finding gets exactly one of:

- **Fixed** — apply the verifier's `correction` text, verbatim where it
  fits. Note where it landed.
- **Kept, declared** — the spec is intentionally different from reality.
  Add a concrete entry to the deviations ledger (README + fidelity preamble
  for all future rounds). This is how restyles, slice cuts, and deliberate
  embellishments survive without being re-flagged forever.
- **Rejected** — the verifier is wrong (rare; usually a misread). Record why.

Never silently drop a finding: the disposition tables are what make the
bundle auditable later.

## 7. Stop conditions and re-verify scoping

- **Stop clean**: a full round returns zero criticals across all verifiers.
- **Stop at cap**: rounds cap reached (default 3) — deliver anyway; declare
  every residual finding in the README.
- **Cap of 1 is a special case.** With one round there is no clean exit: you
  will always exit at the cap, and every fix you apply afterwards ships
  **unverified** — which is precisely how the reference run's round-2 critical
  was born. Say this to the user at intake, before spending; label the fixes as
  unverified residuals in both `verification/round-1.md` and the README; and
  offer one opt-in blind-only re-run (a single agent, no fidelity verifiers) if
  any round-1 critical landed in the physics table, the derived gating math, or
  the PART 3 criteria tables. Do not run it without an explicit yes.
- **Blind re-verifies in full every round** — re-derive the math from
  scratch, re-check every criteria table. Fixes are new surface: the
  reference run's round-2 critical (an untraversable level gate) was
  introduced by a round-1 fix that looked obviously safe.
- **Fidelity may scope down** to the sections changed since its last pass,
  but only after it has passed with zero findings twice; a scoped pass that
  finds nothing does not reset that streak.

## 8. Tier A: Workflow script template · Tier B/C procedures

> **Tier A only.** The script below is a Claude Code Workflow and runs only
> under that tool — it is not JavaScript you can execute with node, and the
> `phase()` / `agent()` / `parallel()` calls exist nowhere else. If your harness
> has no Workflow tool, skip this section entirely and go to the Tier B/C
> instructions below it.

Claude Code Workflow skeleton (literals, not `args` — stringification gotcha):

```js
export const meta = {
  name: '<slug>-verify-r<N>',
  description: 'Round <N> clean-context verification of the <target> replication prompt',
  phases: [{ title: 'Verify', detail: '2 fidelity (web) + 1 blind (no web, high effort)' }],
}
const VERIFY_SCHEMA = { /* §1 */ }
const PROMPT_PATH = '<absolute path literal>'
const FIDELITY_COMMON = `...` // §2 with current deviations ledger pasted in
const FOCUS_A = `...`; const FOCUS_B = `...`
const BLIND_PROMPT = `...`    // §3

phase('Verify')
const results = await parallel([
  () => agent([FIDELITY_COMMON, FOCUS_A].join('\n\n'), { label: 'r<N>:fidelity-a', model: 'sonnet', schema: VERIFY_SCHEMA, phase: 'Verify' }),
  () => agent([FIDELITY_COMMON, FOCUS_B].join('\n\n'), { label: 'r<N>:fidelity-b', model: 'sonnet', schema: VERIFY_SCHEMA, phase: 'Verify' }),
  () => agent(BLIND_PROMPT, { label: 'r<N>:blind', model: '<strongest model available to this harness, e.g. opus>', effort: 'high', schema: VERIFY_SCHEMA, phase: 'Verify' }),
])
return { round: <N>, fidelityA: results[0], fidelityB: results[1], blind: results[2] }
```

**Always pass the blind verifier's `model` explicitly.** Omitting it makes the
agent inherit the orchestrating session's model — which silently downgrades the
blind verifier to a cheap model whenever you are not already running on the top
model. This is the one place in the skill where an omitted option costs you the
finding that matters most. If you do not know the top model's alias in this
harness, ask the user rather than defaulting.

**Tier B (Pi or any one-shot CLI)** — mechanics, because "spawn a fresh
process" hides three failure modes:

1. **Never inline a multi-hundred-line prompt as a shell argument.** Quoting,
   newlines, backticks and Windows command-length limits will truncate or
   mangle it silently. Write the prompt to a file and feed it:
   `pi -p "$(cat <tmp>/r<N>-blind.txt)"`, or the harness's `--prompt-file`
   equivalent if it has one. Keep the file — it is part of the audit trail.
2. **Launch from OUTSIDE the bundle directory** (see §3.0) and point the
   verifier at the neutral spec copy by absolute path. Confirm the process can
   actually read that path before you trust a thin or empty verdict; a verifier
   that failed to open the file will often still return a confident "pass".
3. **Collect one JSON block from stdout** per §1's Tier B/C return format. One
   re-ask on malformed JSON, then hand the raw stdout to the user rather than
   inventing a verdict.

Run the three sequentially if parallel processes are awkward — sequence costs
wall-clock, not rigor. **If spawning fails twice, drop to Tier C and record
"Tier C fallback" in round-N.md.** Do not quietly run the verifier prompts in
your own context and call the result clean-context verification: your context
authored the spec, and that is the one thing these prompts assume it did not.

**Tier C (no orchestration)**: each verifier is a separate, explicit written
pass. The contamination is real — you wrote the thing you are grading — so the
substitute for a clean context is procedure, not good intentions:

- **Order**: run the blind pass FIRST, before you reopen `research/`, the
  README, the deviations ledger, or your synthesis notes in this session.
- **Re-read, don't recall**: open `prompt.md` from disk (Tier C1) or quote the
  section into the pass (Tier C2) before judging it. A judgement with no quoted
  passage is not a judgement — delete it and redo it.
- **Falsify first**: for each criterion, write the failure case you hunted for
  BEFORE you write the verdict. A "pass" with no hunt recorded is a skipped
  check, and skipped checks are how a bundle ships an unsatisfiable criterion.
- **One role per pass**, in its own clearly-labeled section, and complete that
  role's §1 JSON block before starting the next. Never let a later role's
  knowledge back-edit an earlier verdict.
- **Never fewer than 2 full rounds**, whatever the early verdicts say.
- Note the tier in `verification/round-N.md` and in the README: Tier C
  verification is real but weaker — the author is grading their own work.
