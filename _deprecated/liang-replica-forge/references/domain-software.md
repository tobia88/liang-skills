# Domain: software — designed, not yet validated

Status: **untested** — no full run has exercised this path yet. The pipeline
stands unchanged; the deltas below are reasoned extrapolation. The first real
software run should update this file.

Software is in one way the *easier* domain: behavior, layouts, data models,
and shortcuts specify better in text than game feel does, and functional
correctness is objectively checkable. The hard parts move elsewhere —
anonymization and drift.

## The anonymization honesty check (intake)

Describe a kanban board with draggable cards and every model knows it's
Trello, whatever you rename. Decide at intake which situation you're in:

- **Hideable target** (niche tools, internal-style apps, obscure utilities):
  full anonymization works; proceed as with games.
- **Iconic target**: renaming can't blind the model. Reframe the benchmark
  explicitly: the test measures **fidelity-to-THIS-spec vs. drift toward the
  generic training-data clone**. Still anonymize (it keeps the tested model
  from web-recall framing and keeps reports comparable), but write the spec
  and criteria to make drift *measurable*: collect the specific details where
  the real target differs from the generic version of its category — exact
  field names, quirky rules, signature interactions, characteristic
  microcopy — and spec them precisely. Verifier criteria then check those
  details by name; that's where models reveal whether they read the spec or
  pattern-matched the genre. Declare the reframing in the README.

## What counts as a dependency that would do the spec's job for you

Needs judgment here, not a copy of the games answer. Banning application
frameworks outright would be absurd — a Trello replica built in React is
not cheating; React doesn't know what a card or a board is. The line is
behavioral: a dependency is forbidden under §0 rule 1 when it implements
the *replicated* behavior itself, not the general substrate around it — an
off-the-shelf kanban-board component when the kanban board IS the target, a
drop-in rich-text editor when the editor IS the target, a pre-built
calendar/scheduler widget when scheduling IS the target. Test it by asking:
would this dependency let the builder skip writing the thing PART 2 actually
specifies? If yes, it's banned even though it's "just a library." General
substrate — UI frameworks, routers, state stores, date/string utilities,
generic button/modal/input component kits — is fine.

## Spec deltas vs games

- **Object model first.** Entities, fields (names + types), relationships,
  lifecycle states, and state-transition rules come before any UI section —
  everything else references them. This is the software equivalent of the
  physics table: the thing every other number must stay consistent with.
- **Workflows as precondition → steps → resulting state.** Each core workflow
  end-to-end, each step naming the UI element it touches and the state it
  mutates. The blind verifier's gating-math analogue is **workflow closure**:
  every state reachable, every state exitable, preconditions defined,
  no orphan screens.
- **Seeded demo data, exactly.** The delivered artifact must be explorable
  the second it opens: spec the actual seed records (names, values, counts —
  in the app's fictional universe) such that every specified behavior is
  exercisable with them. Empty-state behavior gets its own rules.
- **Local-only rule.** Networked/multi-user features collide with
  zero-runtime-network: slice them to local semantics — in-memory or
  localStorage state, a simulated second user if collaboration is core
  (scripted, labeled as simulation). Declare as a deviation.
- **Edge rules are the fidelity carrier**: validation messages, limits,
  conflict behavior, undo depth, keyboard shortcuts, drag semantics — the
  details that make it *this* product rather than the category. Spend spec
  budget here; it's what the drift criteria check.
- **Visual system as tokens**: spacing scale, type scale, color tokens with
  roles, radius/elevation rules, motion durations/easings. Same
  rule-encodable discipline as game art bibles; ban "generic bootstrap/admin
  template" by name and by rules.
- **Microcopy voice**: 3–5 example strings in the product's voice
  (anonymized), plus tone rules. Products are recognizable by how they speak.

## Verifier roster (software default)

- V1 Workflows & behavior (~10 rows; walk each workflow, trace handlers)
- V2 Data model & state (~8; entities/fields/transitions as spec'd; seed data
  present and sufficient; refresh/persistence semantics)
- V3 Visual system & UX (~8; token discipline, layout regions, responsive
  rules, empty states, NOT-generic checks)
- V4 Edge rules & resilience (~6; validation, limits, undo, shortcut table,
  conflict/simulated-collab behavior)
- V5 Code quality (~6; single-file/no-network, no uncaught errors through
  all workflows, state management sanity, performance on the seed volume)

Audio usually drops entirely; if the target has signature sounds, fold 1–2
rows into V3.

## Embedded QA upgrade: real functional checks

Unlike game feel, workflow assertions can be near-programmatic. In PART 3's
optional smoke checks, have the tested model script its own workflow
walkthroughs where its harness can execute (create record → assert state →
complete workflow → assert result), and keep the written verifier tables as
the floor for chat-only tiers.
