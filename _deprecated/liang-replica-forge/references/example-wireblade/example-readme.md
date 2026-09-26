# KUNAI Replication Prompt Bundle

A benchmark prompt for testing whether an AI model can replicate **KUNAI** (TurtleBlaze, 2020) as a top-notch-looking 2D HTML game — **without knowing what the game is and without web access**. The game is fully anonymized inside the prompt ("WIREBLADE", hero "SLATE", villain "KERNEL", boss "THE SCRAP WARDEN"), so models can't lean on training-data recall of the title; everything needed to build it is encoded in the spec itself.

## How to use

1. Copy the **entire contents of [`prompt.md`](prompt.md)** into the target model — plain chat, Pi, Claude Code, any harness. Nothing else. (The doc itself forbids the model from using web search.)
2. The prompt carries its own QA protocol (PART 3): the model must loop build → self-verify with 5 embedded verifier roles (gameplay, level design, art, audio, code) → fix → re-verify, and print a verdict table per iteration. A capability ladder makes this work everywhere: subagents (Tier A) → fresh one-shot CLI sessions, e.g. `pi -p` / `claude -p` (Tier B) → written self-audit rounds (Tier C, universal floor).
3. Compare models on **two artifacts**: the game itself, and the printed iteration reports / verdict tables (rigor + honesty are part of the test). Verification runs on the *same model* being tested, by design; an optional pinned-judge scoring pass over all finished games can be done separately afterward.

## Bundle layout

| Path | What |
|---|---|
| `prompt.md` | **The deliverable** — paste this (v5, verified) |
| `research/01–05 …` | Ground-truth facts about the real KUNAI, per-claim source URLs (6 Haiku researchers, web) |
| `research/06-art-direction-akira.md` | The Akira / 90s mecha anime style research the art bible was built from |
| `verification/round-1..3.md` | Clean-context verification reports + fix dispositions per round |

## Verification status (loop closed 2026-08-14)

3 rounds of clean-context verification: 2 Sonnet fidelity verifiers independently web-researching the real game and diffing the spec, plus a Fable blind buildability verifier (no web) re-deriving the math and stress-testing the QA protocol.

- **Fidelity — mechanics:** PASS, final pass with **zero** findings ("matches the Scrap Warden point-for-point… often near-verbatim").
- **Fidelity — content/story/tone:** PASS, final scoped pass with **zero** findings; tone matches near-verbatim ("gratifying crunch", "juicy exploding robots").
- **Blind — buildability:** PASS with zero criticals; closing note: *"I would bet on a strong AI producing a top-notch, playable, on-look result from this text alone."*
- The loop caught and fixed 2 criticals along the way (an unsatisfiable verifier criterion in v1; an untraversable level gate introduced in v2) plus ~30 minors.

## Declared deviations from the real game (intentional, do not "fix")

1. **Art style**: Akira-type 90s mecha anime cel look replaces the real game's minimal pixel-art / muted palette (the user's chosen twist).
2. **Anonymization**: every proper noun renamed.
3. **Vertical slice**: opening-through-first-boss only; later abilities (double jump, shuriken, SMGs, rocket launcher, shop, map) intentionally absent.
4. **Invented tuning numbers**: the real game publishes none; values are designed to match its documented feel (floaty, momentum-preserving).
5. **Boss phase-2 escalation** (debris rain, faster telegraphs): unattested embellishment for a better capability test.
6. **Deflect-only turret pulled forward** from mid-game into the slice (teaches the deflect verb; the mechanic itself is attested early).
7. **PING's rest stop placed pre-boss** (real game introduces the IT-bot after the first boss) — breather-before-climax pacing.
8. **Kunai acquired before the city reveal** (real game walks the city katana-only first) — fronts the traversal toy so the parallax money-shot showcases swinging.
9. Unverified-but-plausible: reflected bullets damaging the boss through its shield (extends the game's own deflect-bypasses-armor pattern).

## Version log

- **v1** — synthesis from research.
- **v2** — round 1: fixed phantom-Gunner critical (Gunner became a real, *more faithful* enemy), 11 blind minors, softened uncorroborated mind-upload premise, added boss-kill hat, scrap-raft platform.
- **v3** — round 2: fixed untraversable pogo-pit critical, 8 ambiguity closures, boss gained its attested signature scythe.
- **v4** — round 3: 6 polish minors applied verbatim from the passing blind report (7th emote, chest accounting, hitbox size, face priority, crumble timing, Jump-held note).
- **v5** — isolation hardening: rule 1 expanded from a bare no-web-search line into a full isolation clause (no browsing by any tool/skill/plugin/MCP server, no pre-existing skills/plugins/templates/assets, no pre-session code/assets, no game engines/physics engines/rendering frameworks); rule 5 now requires an Isolation Declaration (every tool/skill/plugin/MCP server the environment made available, whether it was used, and for what, plus the PART 3 tier actually run); PART 3.2 states that verification passes inherit the same isolation constraints.

## Skill-ification note

Planned future shape: `prompt.md` → SKILL.md body; `research/` → `references/`; the PART 3 protocol can be lifted by a Pi driver skill that enforces the loop externally (ralph-style) for uniform cross-model runs.

---

*Produced by a research → synthesis → clean-context-verify loop: 6 Haiku researchers (per-claim sources), Fable synthesis, 3 verification rounds (2× Sonnet fidelity w/ web, 1× Fable blind @ high effort). ~1.06M subagent tokens total.*
