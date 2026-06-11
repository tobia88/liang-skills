# Dialogue Hub

Shared interaction pattern for list-type questions in liang-brainstorm-* skills —
questions where the answer is a *set of independent items each needing its own
decision*, not a single pick. Canonical use: Boss Board (risks) and Fog of War
(unknowns). Lifts per-item alignment out of a single lumped posture.

## When to use the hub

Use the hub when a question surfaces 2+ items that can each take a *different*
disposition (mitigate this risk, accept that one; resolve this unknown, defer
that one). Do NOT use it for single-decision questions — those keep the plain
4-option cadence from `question-cadence.md`.

## Shape

The hub is hub-and-spoke, themed as a dialogue menu:

1. **Analysis-led lead-in.** First present the material items (the scouted risks
   or unknowns), each with a one-line read. The hub is how the user *acts on*
   that analysis — it does not replace it.
2. **Drop into the menu.** List every item with a live status marker, then offer
   the three verbs:

   ```text
   Boss Board — choose a topic:
     1. Race survives fix         [undecided]
     2. Sync-resolve hitch        [undecided]
     3. Command rename breakage   [undecided]

     Examine <n>  — drill that item for deeper analysis, then return here
     Decide  <n>  — set the disposition for that item only
     Done         — finish (records any [undecided] item as unresolved)
   ```

3. **Loop** until the user picks `Done`.

## Examine — progressive deepening

Each `Examine <n>` buys *new* information on a deepening ladder; it never repeats
the prior drill. Suggested ladder (host skill may adapt):

- Drill 1 — sharpened likelihood / impact (or, for unknowns, why it's uncertain)
- Drill 2 — concrete repro / evidence / where it bites
- Drill 3 — mitigation (or resolution) cost + alternatives
- Drill 4+ — second-order effects, edge cases, interactions with other items

After each drill, return to the menu. The status marker is unchanged by
examining — only `Decide` changes it.

## Decide — analysis-generated micro-question

`Decide <n>` is not a fixed verb list. It is a tailored micro-question for *that
item*, generated from its analysis, carrying the full cadence from
`question-cadence.md`: bespoke options + **Recommended / Tradeoff / Confidence**.

```text
Decide 3 — Command rename breakage
  A. Grep + update all refs, then rename clean
  B. Keep the old name as a deprecated alias beside the new one
  C. Accept the breakage — fix refs as they surface

  Recommended: B — zero friction for muscle memory, trivial cost.
  Tradeoff:    Two names linger until a cleanup pass.
  Confidence:  Medium-high.
```

On answer, mark the row `[decided: <short posture>]` and return to the menu.

## Status rendering

- `[undecided]` — no disposition set yet.
- `[decided: <posture>]` — short label of the chosen disposition.

## Done guard (soft)

`Done` is allowed even with items still `[undecided]`. It does not hard-block.
Each undecided item is recorded as `unresolved` in the finalization report rather
than silently dropped, so the gap is visible.

## Drill budget

Drilling is **unbounded by default**. A host skill MAY impose a cap by parameter
(e.g. a generous re-enter limit) if its identity depends on bounded sessions.
Deciding an item is always free and never capped. Examining never spends a host
skill's Pushback Budget — that budget challenges the user's *answers* and is
orthogonal to drilling.

## Report capture — per-item, light trail

The finalization artifact records one row per item: the item, its chosen posture,
and a one-line drill note (e.g. `(drilled 2x)`). It does NOT dump the full Examine
transcript — keep the *why* without the wall of text.

```text
Boss Board:
  Race   -> Mitigate (drilled 2x)
  Hitch  -> Accept
  Rename -> Alias the old command
```

Source: authored per the Q4/Q5 dialogue-hub redesign. Consumed by
liang-brainstorm-quick (Q4 Boss Board, Q5 Fog of War). liang-brainstorm-relentless
may adopt it; if so it may set a drill cap via the host-skill parameter above.
