# Why-Comment Doctrine

Reference for the comment pass (Execution Flow step 4c). The test for every
comment this skill writes: **does it state a purpose, rule, or constraint the
code cannot show?** If the code already says it, the comment is noise.

## What to write

### Doc comments on constants and tunables

Every named constant and exported tunable gets a doc comment answering: what
does this knob control, and what happens at its extremes? Units and reference
frames belong here (degrees vs radians, seconds vs frames, world vs local).

```gdscript
## Window after a swing reverses direction during which a press still
## counts as a valid push; the push is rejected once this runs out.
const DURATION_TO_ACCEPT_SWING := 0.85
```

Bad — restates the declaration:

```gdscript
## The duration to accept a swing.
const DURATION_TO_ACCEPT_SWING := 0.85
```

### Doc comments on state variables

State variables document their *role in the mechanism*, not their type: what
the value tracks, when it changes, and which decision reads it.

```gdscript
## True when the last swing ended without a push, so gravity is scaled up
## to pull the sphere back toward hanging down.
var _is_recovering := false
```

### Rule comments at decision points

A branch that encodes a design rule gets a comment stating the rule and its
reason — especially rejection paths, whose purpose is invisible in the code.

```gdscript
# Reject a push that fights the current motion -- only a push that agrees
# with the existing swing may land, so a mistimed key can't reverse it.
if push_alignment >= 0.0:
```

### Non-obvious implementation choices

When a simpler-looking alternative exists and was deliberately not used, say
why, or the next reader will "simplify" it back.

```gdscript
# Re-derive velocity from actual displacement rather than projecting out
# the radial component -- that's what keeps the constraint from leaking
# or adding energy.
_sphere_velocity = (sphere.global_position - prev_position) / delta
```

### Flagging reserved declarations

An unused declaration that plausibly serves a planned feature is flagged, not
deleted (SKILL.md Boundaries rule 3). The flag names what it is reserved for,
so a later pass can judge whether the plan still exists:

```gdscript
## Currently unused -- reserved for a future recover-easing curve; recovery
## is presently a flat gravity multiplier (RECOVER_GRAVITY_SCALE).
@export var recover_curve: Curve
```

## What never to write

- **Edit narration:** "Renamed from dir_to_anchor", "Changed to fix readability".
  Comments describe the code that exists, not the diff that produced it.
- **Line restatement:** "Add gravity to velocity" above `velocity.y += gravity * delta`.
- **Reviewer reassurance:** "This is correct because...", "Safe to do since...".
  Justifications belong in the report, not the file.
- **Scaffold residue:** auto-generated stubs like "Called every frame." on
  `_process`, or "Replace with function body." placeholders — delete on sight.
- **Invented intent:** if history and code do not evidence *why* something is
  there, do not guess in a comment; raise it as an open question in the report.

## Density and idiom

- Match the file. A sparsely commented file gets comments at decision points
  and declarations, not a comment per line. Never make comments the majority
  of a function body.
- Use the language's doc-comment form for declarations and the plain form for
  in-body rules:

| Language | Declaration docs | In-body rules |
|----------|-----------------|---------------|
| GDScript | `##` | `#` |
| C# | `///` XML or plain `///` | `//` |
| C++ | `/** */` or `//` per project style | `//` |
| Python | docstrings (`"""`) | `#` |
| JS/TS | JSDoc `/** */` | `//` |

- Doc comments go *above* the declaration, wrapped at the file's prevailing
  line width. Trailing same-line comments only where the file already uses them.
