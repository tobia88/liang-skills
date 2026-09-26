# Domain: 2D games — the proven path

Status: **validated end-to-end** by the reference run (KUNAI → WIREBLADE,
2026-08: 3 verification rounds, zero criticals at close, blind verifier's
verdict: "I would bet on a strong AI producing a top-notch, playable, on-look
result from this text alone").

## Scope calibration

A 4–7 minute vertical slice (opening-through-first-boss shaped) sits at the
**upper edge of one working session** for a strong model — that is a feature:
the benchmark should discriminate. Don't grow past it. A slice needs: the
core traversal/combat loop complete, one taught-by-geometry skill ramp, one
"money shot" showcasing the art direction, one boss or climax encounter, and
a real ending (victory screen + results), so finished-ness itself becomes
measurable.

## What carried the most weight (in observed verification)

1. **The physics table + derived gating math.** Movement params (speeds,
   accelerations, two-case gravity, jump takeoff, variable-jump clamp,
   terminal fall, coyote, buffer) plus derived reach ("≈229 px raw / ≈260 px
   practical") that the level section then cites as its gating rule. The
   blind verifier recomputed all of it every round — two of the three rounds'
   worth of criticals/minors clustered here. Show the derivation.
2. **Teach-by-geometry beats.** Each new verb gets a beat whose geometry
   makes the verb the obvious solution (a pit wider than jump reach with a
   pogo target mid-air; a chasm with anchor nodes). Specify the teaching
   geometry numerically — this is where fix-induced regressions happen, so
   expect the blind verifier to stress it.
3. **The expressive channel.** If the hero has a signature expressive element
   (the example's tablet-face emotes), enumerate states, triggers, AND an
   overlap-priority rule with hold durations. Ambiguity here was a repeated
   minor-findings source.
4. **Edge-rule paragraphs.** Respawn state (HP, what resets, what persists),
   pause semantics (which clocks freeze), input suppression in special states
   (what W/S mean while attached to a rope). Cheap to write, repeatedly
   flagged when missing.
5. **Juice checklist as mandatory.** Hitstop/shake/squash/particles/flow
   rewards with numbers, framed "all mandatory" — this is what separates
   "works" from "top-notch looking" in the built results.

## Verifier roster (games default)

V1 Gameplay & feel (~10 rows) · V2 Level design (~8, incl. the gating-math
row and a walk-the-level-data instruction) · V3 Art direction (~10, palette /
cel or pixel discipline / animation stepping / parallax / post) · V4 Audio
(~5, synthesized-only + autoplay gate) · V5 Code quality & performance (~8,
single-file / no-network / fixed timestep / 60fps hygiene / chrome works).

## Medium

One self-contained HTML file, zero runtime network, everything inlined,
audio synthesized (WebAudio) — no vendored libraries needed at this scale;
canvas + vanilla JS is fully sufficient and keeps the discriminating power.

## What counts as a dependency that would do the spec's job for you

This is the domain fill for §0 rule 1's dependency ban
(`deliverable-blueprint.md`): game engines, physics engines, rendering
frameworks, audio synthesis libraries, and sprite/asset packs — whether
vendored, fetched, or reproduced from memory. It reaches anything that would
simulate the physics, render the scene, synthesize the audio, or supply the
art *for* the builder. It does not reach vanilla canvas/DOM/WebAudio APIs or
the small helper functions
(collision checks, easing curves, a tiny synth voice) the builder writes
itself — those are the job, not a shortcut around it.

## Art styles that encode well for 2D

Cel/anime (palette + tone counts + stepping + post), pixel-art (resolution
grid + palette + dither rules), flat-vector, terminal/monochrome. The
example's Akira bible (`example-wireblade/example-prompt.md` §2.12) is the
model: palette table with reserved colors, restraint rule, character vs
background density split, stepped animation rates, named post effects with
intensity bounds and a "reads as aged film, never Instagram filter" test.
