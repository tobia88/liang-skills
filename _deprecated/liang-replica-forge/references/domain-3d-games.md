# Domain: 3D games — designed, not yet validated

Status: **untested** — no full run has exercised this path yet. The pipeline
(research → synthesis → verify loop) is domain-agnostic and stands; the
guidance below is reasoned extrapolation from the 2D run. The first real 3D
run should update this file with what it learns.

## The medium decision comes first (intake)

Pure vanilla WebGL in one file is a brutal discriminator — most models will
burn the session on boilerplate. Three options, decided at intake and written
into PART 0:

1. **Vendor one library** (recommended default): permit exactly one inlined
   3D library (e.g. a minified Three.js pasted into the file). Keeps
   single-file + zero-network; grows file size. Declare it in **PART 0 rule 2**
   as the medium's exception — that is the binding statement, because rule 1
   otherwise bans it — and note it in the README for the user's audit trail.
2. **Vanilla WebGL**: maximum discrimination, high risk the benchmark
   measures boilerplate stamina instead of game-building. Only for testing
   top-tier models, with scope cut hard.
3. **Relaxed medium**: an html + one .js lib file pair. Weakens the
   paste-and-run elegance; last resort.

## What counts as a dependency that would do the spec's job for you

This is the domain fill for §0 rule 1's dependency ban
(`deliverable-blueprint.md`): game engines, physics engines, rendering
frameworks, audio synthesis libraries, and sprite/asset packs — whether
vendored, fetched, or reproduced from memory. **Exception:** if intake chose
the "vendor one library" medium option above, that single declared library is
the medium (state it in PART 0 rule 2), not a banned dependency under rule 1 —
it draws triangles; it does not simulate physics, author levels, synthesize
audio, or supply art. The ban still reaches a physics engine, an audio
synthesis library, any second or alternate rendering library, a full game
engine, and anything else that would simulate the physics, render the scene,
synthesize the audio, or supply the art *for* the builder. It does not reach
vanilla canvas/WebGL/DOM/WebAudio APIs or the small helper functions the
builder writes itself.

## Style must be geometry-cheap and rule-encodable

The restyle guard is stricter in 3D: the style must be executable with
procedural/primitive geometry and simple materials, because the tested model
ships no asset files. Good families: low-poly flat-shaded, PSX-era (vertex
snapping, affine-texture wobble, dithered fog), wireframe/tron, cel-shaded
with hard ramp lighting, voxel. Encode as: palette + material rules (flat vs
ramp shading, specular bans), polygon budgets per object class, fog/distance
treatment, and named post effects with bounds. Refuse photoreal at intake.

## Spec deltas vs 2D

- **Camera is a first-class section** — research slice, spec section, and
  verifier criteria of its own: follow distance/height/lag (numbers),
  collision policy (whisker/spring behavior in words a builder can
  implement), pitch limits, lock-on rules if any, FOV baseline + event kicks,
  and the input-mapping statement (camera-relative movement, who owns yaw).
  A 3D game with a bad camera fails regardless of everything else.
- **Movement math still derives on paper**: jump apex/reach from takeoff
  velocity and gravity works identically in 3D; add air-control authority,
  slope/step limits, and (if present) the traversal verb's envelope (dash
  distance, grapple/glide reach) — then gate the spatial layout with it,
  same pattern as 2D.
- **Spatial beat map replaces the side-scroller beat map**: numbered beats as
  connected spaces described by landmark, approximate dimensions, height
  deltas, and sightlines ("from the gate, the tower is visible 40 units
  ahead-left; the route to it requires two 6-unit ledge pulls"). State the
  navigation rule (landmark visibility) explicitly — blind models can't
  see your mental level.
- **Encounter staging**: arena dimensions vs enemy counts vs player movement
  envelope — the gating-math equivalent for combat spaces.

## Verifier roster deltas

Insert a **Camera & control verifier** (or fold into V1 with ~4 dedicated
rows: follow/lag numbers implemented, collision never clips walls, lock-on
rules, FOV events). V5 gains perf rows: draw-call/instancing hygiene,
polygon budget respected, no per-frame allocations in the render loop.

## Scope: cut harder than feels right

A 3D slice costs more per minute of play. Target 2–4 minutes: one connected
space chain (3–5 beats), one skill ramp, one arena climax. If the 2D slice
was "the opening 5 minutes," the 3D slice is "the opening encounter chain."
The blind verifier's scope-realism check (hunt item 6) is the tripwire —
take its FAIL seriously rather than negotiating with it.
