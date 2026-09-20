# Verification round 2 — prompt.md v2

> Workflow `kunai-verify-r2` run wf_4b26a2c2-f51 · 2026-08-14
> Verifiers: fidelity-mechanics (Sonnet, web), fidelity-content (Sonnet, web), blind-buildability (Fable, high effort, no web)

## Verdicts

| Verifier | Verdict | Critical | Minor |
|---|---|---|---|
| Fidelity — mechanics & systems | **PASS** | 0 | **0** |
| Fidelity — content, story & tone | **PASS** | 0 | 3 |
| Blind — buildability | **FAIL** | 1 | 8 |

Fidelity-mechanics returned a clean sheet against ~20 independent sources: "the first boss … matches the Scrap Warden point-for-point," momentum-preserving release confirmed near-verbatim, and the v2 scrap-raft addition matched the real fight's summoned-platform mechanic.

## Findings & dispositions

### Blind (buildability)

| # | Sev | Finding | Disposition (v3) |
|---|---|---|---|
| B1 | **CRIT** | Beat-2 pogo pit untraversable as written: ledge ≥180 px up vs max pogo rise ≈90 px from a Gnat 60 px below the edge (a regression introduced by the round-1 fix). Every faithful builder would fail CRIT criterion L3 | **Fixed** — pit redesigned horizontal per the verifier's own text: 300 px wide (> 260 px practical jump reach), far ledge level with takeoff, stationary mid-pit Gnat (explicit special-placement note), pogo grants ~90 px rise + 0.64 s airtime ≈ +190 px — provably crossable; L3 updated to match |
| B2 | minor | L3 cited a 220 px threshold defined nowhere in the spec | **Fixed** — L3 rewritten in terms of the real numbers (≥340 required / <300 forbidden / ≤260 bypass check) |
| B3 | minor | Boss HP bar top-of-screen (§2.10) vs bottom-center (§2.14) | **Fixed** — §2.10 now defers to §2.14 (bottom-center) |
| B4 | minor | Ambiguous whether reflected bullets hurt the invulnerable boss | **Fixed** — reflected bullets damage the boss at any time, through the shield; slashes/pogos only in windows |
| B5 | minor | Summon arithmetic could exceed its own max-3 cap | **Fixed** — summon count = min(2 [P2: 3], 3 − adds alive) |
| B6 | minor | Respawn HP and world-reset rules unstated (could respawn at 0 HP under the no-healing rule) | **Fixed** — respawn restores full 6 HP; enemies/crumbling ledges reset; chests/volts/hats persist; boss resets to full/phase 1 |
| B7 | minor | Red-reservation rule conflicted with red volts and red checkpoint flags (A7 could fail literal builds) | **Fixed** — signal red #E12120 reserved; volt red-orange #FF3B30 declared a distinct exempt hue; checkpoint flags now flip to #FF3B30 |
| B8 | minor | Pogo "refreshes air control" undefined (air control is never limited) | **Fixed** — replaced with "resets vertical velocity to −520 px/s and re-arms the down-slash" |
| B9 | minor | Grounded-attached kunai behavior undefined (fire while running is a common state) | **Fixed** — grounded firing allowed; run with slack rope; reel-past-taut lifts into pendulum; jump transitions into swing |

Blind verifier's overall note: core jump math now internally consistent, criteria denominators match, art direction executable without references, QA ladder followable by chat-only models. Scope judged "at the upper edge of one working session" — an accepted property of the test (it's meant to discriminate strong models).

### Fidelity — content

| # | Sev | Finding | Disposition (v3) |
|---|---|---|---|
| C1 | minor | The real first boss is repeatedly identified by its **scythe** ("that sickle-wielding meanie"); Scrap Warden had no melee weapon | **Fixed** — Warden now drags a massive salvaged scythe (signature silhouette), leads swoops with it, and its edge ignites signal-red in phase 2 |
| C2 | minor | The IT-bot (real: Earl) is first met AFTER the first boss in the real game; spec stages PING + save beacon pre-boss | **Kept, declared** — deliberate slice pacing (breather + full heal before the climax); standalone healing save points do exist pre-boss in the real game |
| C3 | minor | Real order: katana-only walk through the ruined city first, kunai acquired later (in the factory area where the boss also lives); spec grants kunai before the city reveal | **Kept, declared** — deliberate slice pacing: front-loads the traversal toy so the exterior money-shot showcases swinging (better test of the art + movement combo) |

## Outcome

v2 → v3 with 10 applied fixes and 2 new declared deviations (4 total). Round 3 (final): blind re-verify + scoped fidelity-content re-check of the boss changes launched against v3. Fidelity-mechanics not re-run — it double-passed (0 findings on v2) and no v3 change touches its domain except the scythe, which implements fidelity's own sourced correction.
