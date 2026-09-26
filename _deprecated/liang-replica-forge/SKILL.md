---
name: liang-replica-forge
description: >-
  DEPRECATED, retired skill.
  Factory for verified, anonymized replication-benchmark prompts. Runs a
  research → synthesis → clean-context verify loop that turns any existing
  game (2D or 3D) or piece of software into one paste-ready prompt.md that an
  AI model must build from alone — no web access, target never named — so
  different models can be benchmarked on the same replication task. Use this
  whenever the user wants to create a prompt that replicates, clones,
  duplicates, or rebuilds an existing game or app for model testing; mentions
  a "replication prompt", "clone benchmark", "duplicate this game/software as
  a test", or comparing AI models by making them build the same target; or
  wants another verification round run on an existing bundle under
  .liang/prompts/. Trigger even if they only say "make a prompt like the
  KUNAI/WIREBLADE one for some other target".
---

# Replica Forge

Manufacture a **verified, anonymized replication-benchmark prompt**: a single
markdown document that makes a search-banned AI model rebuild a real game or
piece of software as a polished, playable/usable artifact — without ever
learning what the target is. The prompt is the *instrument*; models are the
*subjects*; the user compares both the built artifacts and the honesty of the
build reports.

This skill is harness-portable. It runs in Claude Code (subagent
orchestration), in Pi (sequential + fresh one-shot CLI processes), or in plain
chat (written passes). See **Harness ladder** below — every phase states what
to do at each tier.

## What you produce

```
.liang/prompts/<real-target-slug>-replication/     (in the active workspace)
├── prompt.md          # THE deliverable — self-contained, paste-ready
├── research/          # NN-<slice>.md ground truth, per-claim source URLs
├── verification/      # round-N.md verdict + disposition reports
└── README.md          # usage, declared deviations, version log, verification status
```

The folder is named for the REAL target (it is the user's audit trail); only
`prompt.md`'s contents use the codename. Record absolute paths in every
verifier prompt and in your working notes — spawned verifiers and one-shot
processes do not inherit your working directory. Because the folder name gives
the target away, the blind verifier never receives a bundle path: it reads a
neutral copy of the spec at a neutral path (`references/verify-phase.md` §3.0).

`prompt.md` is the only file the tested model ever sees. Everything else exists
so the *user* can audit the ground truth later and so future editors don't
"fix" intentional choices.

## Principles (read these as design law)

1. **The prompt's consumer is blind.** It will be pasted, alone, into a model
   with no web access and no other context. Every authoring decision answers
   one question: *could a strong model produce a top-notch, on-target result
   from this text alone?* Nothing may depend on recognizing the target.
2. **Anonymize to break recall.** Rename every proper noun — title, heroes,
   villains, places, currencies — so the model can't lean on training-data
   memory of the target. Renaming fails when the *mechanics themselves* are
   the recognizable part, so apply this test in every domain, games included:
   would a competent model reading PART 2 with all names stripped still be
   able to name the target from the mechanics alone? (A kanban board with
   draggable cards *is* Trello; a one-button descent down a shaft on gun-boots
   *is* Downwell.) If yes, anonymization is **declared-futile** — say so at
   intake and don't pretend otherwise. What changes then: keep the renames
   anyway (a codename still stops the tested model quoting the original), the
   README declares that this benchmark now measures **fidelity-to-spec vs.
   generic-clone drift**, and every PART 3 criterion must cite the spec's own
   numbers rather than the target's reputation, so that drifting to the
   generic version fails the criteria. See `references/domain-software.md`.
3. **Style must be rule-encodable.** "Akira style" is useless to a blind
   model; a 12-hex palette + cel-shading rules + sprite-stepping rates is
   executable. At intake, push back on any requested look that can't be
   written as rules (photoreal, "cinematic") and steer toward encodable
   families: cel, flat, pixel, vector, low-poly, wireframe, terminal.
4. **Sources or it didn't happen.** Every research claim carries the URLs
   actually consulted, preserved in `research/`. The user audits these later;
   fabricated or homepage-level citations poison the whole bundle.
5. **Synthesis is yours alone.** Never delegate spec-writing to a subagent.
   One author must hold the entire spec to keep every number consistent with
   every other number. Subagents get the two ends — research and verification
   — never the middle.
6. **Derive the impossible-to-playtest math.** The tested model can't tune by
   playing before it builds. So the spec must do the tuning on paper: derive
   movement/geometry/state math (jump reach vs. gap widths, workflow
   preconditions vs. UI states) and write the results into the spec as law,
   with the derivation shown. Internal consistency is what the blind verifier
   will attack first.
7. **The deliverable embeds its own build-verify loop.** One-shot builds
   plateau. `prompt.md` PART 3 forces the tested model to loop
   build → verify → fix using verbatim verifier prompts + criteria tables it
   carries inside itself, at whatever capability tier its harness supports.
   The printed verdict tables double as honesty artifacts the user compares
   across models.
8. **Keep a declared-deviations ledger.** Every intentional difference from
   the real target (restyle, renames, slice cuts, invented tuning,
   embellishments) is listed in the README *and* pasted into the fidelity
   verifiers' preamble, growing each round. Skip this and verifiers re-flag
   the same intentions forever — and future editors "fix" them.
   **But know what the ledger costs you:** declaring a deviation switches off
   every downstream check on the research beneath it. Fidelity is told not to
   flag it; the blind verifier only asks whether it is *executable*, never
   whether it is *true*. In the reference run, the restyle slice was the only
   one that shipped with content-farm sources, precisely because it was the one
   nothing re-examined. Treat "this slice backs a declared deviation" as a
   reason for more care at research time (§2.5 vetting), not less.

## Phase 0 — Intake

Settle these with the user before any research (they may think out loud;
don't start until locked):

- **Target**: real name + what makes it *distinctive* — the thing the
  benchmark must reproduce or it isn't this target.
- **Domain**: `2d-game` | `3d-game` | `software` → read the matching
  `references/domain-*.md` now. 2D games are the proven path; the other two
  files say what changes and what's untested.
- **Slice**: what's inside the vertical slice (e.g. opening-through-first-boss;
  one core workflow end-to-end) and the definition of done.
- **Medium**: default is one self-contained HTML file, zero network requests
  at runtime, everything inlined. 3D may vendor one library — a declared
  knob, see the domain file.
- **Style**: faithful, or a deliberate restyle (apply principle 3).
- **Anonymization strength**: full rename / partial / declared-futile — run
  principle 2's test to decide; it applies in every domain, not just software.
- **Verify budget**: rounds cap (default 3), verifier roster adjustments. A
  cap of 1 has no clean exit — read the Phase 3 loop rules before agreeing.
- **Output location**: default
  `.liang/prompts/<real-target-slug>-replication/`.
- **Cost disclosure (mandatory gate — do not start Phase 1 without it)**: in
  one message, tell the user the tier you will run at, the number of researcher
  calls, the number of verifier calls per round × the rounds cap, which model
  each will use, and the resulting expected token/spend range for THIS run from
  the table in **Cost & scaling**. If the harness bills per call at a model you
  cannot downgrade (common on CLI harnesses), say that too — it is the single
  biggest driver of the bill. Then get an explicit go-ahead, or a scaled-down
  configuration.

Write the locked decisions down as a short target brief in your working notes
— several later templates interpolate from it.

## Phase 1 — Research (5–7 slices; parallel and cheap where the harness allows)

Decompose the target into 5–7 research slices (menus per domain in
`references/research-phase.md`; one slice is always the *look itself*,
researched as implementable rules, not vibes — whether you are restyling the
target OR running faithful on a target whose visual identity is load-bearing:
a bounded palette, a resolution grid, a signature silhouette rule. If the user
names the look as the reason the target is worth replicating, it gets its own
slice even at the 4-slice floor). Each researcher:

- gets a role preamble + its slice brief (templates in
  `references/research-phase.md`),
- must verify against real sources — store pages, official docs, wikis,
  professional reviews, developer interviews — not memory,
- returns structured findings: atomic claims, implementation-relevant detail,
  confidence (high = official or 2+ agreeing sources), per-claim URLs.

Save each slice to `research/NN-<slice>.md` **immediately** as results land
(format in the reference file). Cheap/fast models suffice wherever you can
choose one (Tier A `model:` option, Tier B model flag) — the schema and source
discipline do the quality work, and the verify loop catches what research gets
wrong. At Tier C you are the researcher and no cheaper option exists; that
changes the cost shape (see **Cost & scaling**) but not the discipline.
Without fan-out, follow `references/research-phase.md` §6 step by step — it is
the mechanism that replaces the schema enforcement you lose.

## Phase 2 — Synthesis (you, in main context)

Read every research file, then write `prompt.md` yourself following
`references/deliverable-blueprint.md` section by section:

- **PART 0** — rules of engagement (full isolation — no browsing by any
  tool/skill/plugin/MCP server, no pre-existing skills/plugins/templates/
  assets, no dependency that would do the spec's job for you (pull the
  exact ban from the matching `domain-*.md`; never hardcode "no engines or
  frameworks" here — that's wrong for software, and for 3D's
  vendor-one-library option) — medium + zero network, no one-shotting, no
  questions, honest reporting + an Isolation Declaration).
- **PART 1** — mission: deliverable, slice scope, definition of done (tied to
  the CRIT criteria + minimum rounds), and 3–5 *design-intent* bullets
  distilled from reviewer language — the soul of the target in feel terms.
- **PART 2** — the full specification. Section list per domain is in the
  domain file. The numbers doctrine applies: every feel demand gets a number;
  every number is consistent with every other; gating math is derived inline.
- **PART 3** — the embedded build-verify protocol: loop diagram, stop
  conditions, capability ladder, clean-context rule, 4–6 verifier roles with
  **verbatim prompts + criteria tables**, iteration report template. Every
  criterion must reference only things PART 2 actually defines, with matching
  numbers — an unsatisfiable criterion fails every model you test (this
  exact defect was the reference run's first critical).

Finish with the anonymization pass: search your draft for every real proper
noun from the target brief; also purge identifying quotes, title cards, and
slogans. Start the declared-deviations ledger now.

## Phase 3 — Verify loop (clean contexts, until zero criticals)

Default roster per round — templates, schema, and dispatch details in
`references/verify-phase.md`:

- **2 fidelity verifiers** (web access, mid-tier model): independently
  research the real target and diff the spec against reality, split by focus
  (games: mechanics/systems vs. content/story/tone; software: behavior/data
  vs. UX/content). They receive the ground-truth identity and the
  deviations ledger.
- **1 blind buildability verifier** (no web, strongest model available, high
  effort): never told what the target is; judges only whether *this text
  alone* reliably produces a great result — ambiguity, contradictions,
  gating-math errors, missing values, unexecutable art direction, QA-protocol
  executability, scope realism, omissions.

The model/effort words above are Tier A vocabulary. At Tier B, route them with
your CLI's model flag; at Tier C no routing exists at all. Read
`references/verify-phase.md` §4 and tell the user which of these three roles
you can actually run at strength BEFORE the round starts — not after.

Before every blind dispatch, at every tier, run the isolation steps in
`references/verify-phase.md` §3.0: the blind verifier gets a neutral copy of
`prompt.md` at a neutral path, never the bundle path and never the bundle
directory.

Each returns pass/fail + discrepancies (critical/minor, with exact correction
text). Then disposition every finding: **fixed** (prefer applying the
verifier's own correction text verbatim — it's usually better than a
paraphrase) / **kept as declared deviation** (add to ledger + fidelity
preamble) / **rejected with reason**. Write `verification/round-N.md` with
verdict table + dispositions; bump the prompt version.

**If the fidelity verifier has no web access** (common at Tier C, possible at
Tier B): a fidelity pass from memory is not fidelity verification. Do this, in
order:

1. Ask the user whether ANY harness they can reach (a browser, another chat
   with search, the Pi CLI) can run the two fidelity prompts. Running them
   elsewhere and pasting the JSON verdict back is legitimate and preferred.
2. If not, run a **recall-based fidelity pass** and label it as such: same
   prompt, but replace "Independently research the real target using web
   search/fetch tools" with "Answer from your own knowledge of the target; set
   `sources` to [] and prefix every `what` with `RECALL:`". Cap every such
   finding at `minor` unless it contradicts something the user personally
   confirmed.
3. Record in `verification/round-N.md` AND the README: "Fidelity verified from
   model recall only — no sources consulted. `research/` remains the only
   sourced ground truth in this bundle."

Principle 4 still binds `research/`: if research also ran with no web access,
the bundle is NOT deliverable as a verified benchmark. Stop, tell the user,
and offer either an unverified draft carrying a banner at the top of the README
("UNSOURCED DRAFT — no web access at authoring time") or a pause until a
web-capable harness is available.

Loop rules:

- **Stop** when a full round returns zero criticals from all verifiers, or at
  the rounds cap (then deliver anyway, declaring residuals in the README).
- **A cap of 1 has no clean exit.** You will always exit at the cap, and every
  fix you apply after that round ships **unverified** — precisely how the
  reference run's round-2 critical was born. Say this at intake before
  spending, label those fixes as unverified residuals in both
  `verification/round-1.md` and the README, and offer the opt-in blind-only
  re-run described in `references/verify-phase.md` §7. Never run it without an
  explicit yes.
- **Blind always re-verifies in full** — recompute the math, don't diff-check.
  Every fix is new surface: the reference run's round-2 critical was
  *introduced by a round-1 fix*.
- Fidelity may scope down to changed sections once it has passed clean twice.
- The blind verifier is never cut from a round. In the reference run it found
  100% of the criticals.

## Phase 4 — Bundle & deliver

Write `README.md`: how to use the prompt (paste wholesale; what the embedded
protocol makes the tested model do; compare artifact + verdict tables),
verification status quoting the final verdicts, the declared-deviations list
("intentional, do not fix"), and a version log of what each round changed.
Deliver `prompt.md` to the user. Suggest a memory/project note if the harness
keeps one.

## Harness ladder (for running this factory)

- **Tier A — subagent orchestration available** (Claude Code): fan research out
  in parallel; dispatch each verifier as a fresh clean-context subagent, after
  performing the isolation steps in `references/verify-phase.md` §3.0. If — and
  only if — you are using the Workflow tool, use the script templates in the
  reference files, and beware one Workflow-specific gotcha: `args` may arrive
  JSON-stringified, so embed literals (paths, round numbers) in the script
  rather than passing them via `args`. This gotcha does not apply at Tier B/C.
- **Tier B — CLI, no subagents** (Pi): prefer to spawn each research slice as
  its own fresh one-shot process on a **cheap/fast model** — `pi -p --model
  <cheap-model> "<preamble + slice brief>"` — writing its `research/NN-*.md`
  file before launching the next. This keeps the cheap-researcher cost routing
  that Tier A gets from `model: 'haiku'`, and keeps Phase 1 out of your own
  context. Only if per-process model selection is unavailable (check `pi -p
  --help` first) do you run the slices sequentially yourself with web tools,
  same schema discipline — and if so, tell the user at intake that research is
  running on the session model and will cost several times more than the Tier
  A path. For verification, always spawn fresh one-shot processes so each
  verifier gets a genuinely clean context, isolated per `verify-phase.md` §3.0
  and pointed at absolute paths. If spawning fails twice, drop to Tier C.
- **Tier C — no orchestration (universal floor)**. Two sub-cases; decide which
  you are in at intake and say so to the user out loud:
  - **C1 — chat WITH file read/write** (IDE assistant, chat with a filesystem
    tool): run everything sequentially; the bundle is still written to disk
    exactly as specified. Verification = separate explicit written passes;
    before each pass actually re-read `prompt.md` from disk, and for the blind
    pass read nothing else from the bundle.
  - **C2 — pure chat, NO file access**: the bundle becomes a sequence of chat
    messages. Emit each bundle file as its own fenced block, prefixed with the
    exact path the user should save it to
    (`.liang/prompts/<slug>/research/01-<slice>.md`, …), one message per file,
    **immediately as it is produced** — never batched at the end. Because you
    cannot re-read from disk, each verification pass must QUOTE the spec
    section it is judging back into the pass before judging it; that quoting is
    the substitute for re-reading, and it is what stops you grading your memory
    of the spec instead of the spec. State in the README: "Produced at Tier C2
    — no file system; verification passes were written single-context by the
    author, and no file was ever re-read."

  At C2, Phase 4 "deliver" means: post `prompt.md` as one fenced block with its
  save path, then list the other bundle files the user must save from the
  earlier messages, in order. Say plainly that nothing was written to disk.

  In both sub-cases run each pass per `references/verify-phase.md` §8: adopt
  the role, hunt to falsify before writing the verdict, one role per pass, fill
  the schema honestly. Record in the README that verification ran at Tier C
  (rigor differs).

Whatever the tier: verifiers judge the actual spec text — the file on disk, or
at C2 the passage quoted into the pass — never your memory of it, and they
never see your synthesis reasoning.

## Cost & scaling

Say these numbers to the user at the Phase 0 gate, BEFORE spending anything.

Reference run (KUNAI → WIREBLADE, **Tier A**): 6 researchers ≈300k tokens +
150–320k per verify round; 3 rounds ≈ **1.06M subagent tokens** total, zero
criticals at close. Per-role bands from that run, for estimating your own:
~40–60k subagent tokens per cheap researcher slice; ~60–90k per web fidelity
verifier; ~120–180k for the blind verifier at high effort.

| Tier | What you actually pay for | Shape vs. the Tier A figure |
|---|---|---|
| A | Subagent tokens; cheap researchers; parallel | 1× (~1.06M, mostly cheap-model) |
| B | One fresh process per researcher/verifier (6 research + 3 per round = 15 calls at cap 3), each at the harness's default model — often with no cheap tier available | similar token count at a **higher price per token**; count the calls and multiply by your harness's per-call cost before quoting |
| C | Your own main context, re-read every pass, no parallelism | fewest tokens, most wall-clock; the real risk is context exhaustion mid-loop, not money |

Scale-down levers, in the order you should offer them:

1. Rounds cap 3 → 2 (saves a whole round; never go below 1).
2. Research slices 6 → 4 (the minimum; merge them in the fixed order below).
3. Cheaper researcher model — Tier A `model:` option, Tier B the CLI's model
   flag. **At Tier C this lever does not exist; say so rather than implying
   it.**
4. Scoped fidelity re-runs once fidelity has passed clean twice
   (`references/verify-phase.md` §7).
5. Narrow the slice at intake — the cheapest lever of all, and the one users
   forget to consider.

**When you compress below 5 slices, merge in this fixed order** (so every run
of this skill covers the same ground):

1. First merge **story/tone/UI/juice** into the **presentation/style** slice.
2. Then merge **weapons/abilities/progression** into **enemies & bosses**
   (both are content rosters).
3. Never merge **core mechanics & movement feel** or **world structure & level
   design** into anything — they carry the physics table and the derived
   gating math, which is where the blind verifier finds most criticals.

At 4 slices the set is therefore: (1) core mechanics & feel, (2) world
structure & level design, (3) content roster: enemies, bosses, weapons,
progression, (4) presentation: style-as-rules, HUD, juice, audio, tone. Tell
the user which slice absorbed which, and expect the merged content roster to
be the spec's thinnest section.

Post the arithmetic to the user **before dispatching the first researcher** and
wait for a go-ahead — it is the last cheap moment to change slice count, rounds
cap, or roster. Name what the chosen economy buys and what it costs (which
slice merged into which, which fixes will ship unverified). **Never** economize
on the blind verifier: it is one call per round and it found 100% of the
criticals in the reference run.

## The worked example

`references/example-wireblade/` holds a complete, verified output: the KUNAI
(TurtleBlaze, 2020) replication prompt with an Akira-restyle twist
(`example-prompt.md`), its README with 9 declared deviations
(`example-readme.md`), and a mid-loop verification round showing a critical
being caught and dispositioned (`example-verification-round.md`). When unsure
what "good" looks like at any phase, open the corresponding part of the
example before improvising.
