# Alignment-First Protocol

Shared brainstorming contract for all liang-brainstorm-* skills. Defines the two
stages every brainstorm follows: open **Alignment** to build a shared understanding,
then **Crystallization** where the structured slots (Main Quest, Victory Conditions,
Scope, Boss Board) precipitate from that understanding as proposed drafts — never
elicited cold.

## Principle

Structured slots are **synthesized outputs of alignment, not elicited inputs.** Do
not ask the user to pick a Main Quest / Victory Condition / Scope from cold options
before a shared understanding exists — front-loading a slot anchors the session on a
guess. Build the shared read first; let the slots fall out of it.

## Stage 1 — Alignment

Goal: the model and the user reach the same mental model of the problem before any
slot is named.

- **Format stays ABCD** (per `question-cadence.md`) — the 4-option cadence is a
  *thinking scaffold*, concrete things to react to, not a blank prompt.
- **Content is exploratory, not committal.** Alignment questions probe understanding
  ("how do you read the core problem?", "what's the real itch?", "which framing is
  closest?"). **No slot is locked in this stage.**
- **Bidirectional.** The model puts its *own* read on the table as options — surfacing
  assumptions, tensions, and framings the user may not have named. Alignment is
  reconciliation, not interrogation.
- **Still relentless.** Challenge vagueness, name contradictions, surface gaps — but
  as exploration, not as a gate the user must pass.

## The Alignment Gate (exit)

Alignment ends **only when the user says so** ("lock it in" or equivalent).

- **User-driven.** The model never auto-advances into crystallization.
- **Soft nudge.** When the model judges the read has converged it MAY offer: "I think
  we're aligned on X — lock it in, or keep drilling?" That is a push, not a transition;
  the user keeps the trigger.

## Stage 2 — Crystallization

Now the slots are named — as **drafts the model proposes from the alignment
discussion**, for the user to confirm or adjust.

- Propose each slot as a synthesized draft: "From our discussion, the Main Quest is
  '…' — right? Adjust if it's off."
- Use ABCD **alternatives only where a genuine fork exists** — not to re-elicit what
  alignment already settled.
- Relentless challenge on risk and contradiction lives here, as before.

## Forms — full vs collapsed

The host skill selects the form by its identity:

- **Full form** — a distinct Alignment stage with the user-driven gate and soft nudge,
  then a Crystallization stage. For depth-oriented sessions.
- **Collapsed form** — Alignment compresses to a single read-back turn: "My read: X so
  that Y, scoped to Z. Right?" One confirm, then proceed. Downstream questions still
  run as **synthesis-confirm drafts**, not cold asks. For fast/short sessions.

Source: authored for the alignment-first redesign per dc008. Consumed by
liang-brainstorm-relentless (full form) and liang-brainstorm-quick (collapsed form).
