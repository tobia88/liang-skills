---
name: liang-game-prototyper
description: Build small playable HTML game prototypes to test game ideas and mechanics fast. Creates a self-contained index.html (vanilla JS + Canvas) plus a README brief in the active workspace's `.liang/prototypes/YYMMDD-HHMM_<name>/`, reusing generated assets from the shared pool at `.liang/prototypes/shared_assets/`. Use whenever the user wants to prototype, mock up, or playtest a game idea, mechanic, or feel experiment in the browser — "prototype this game", "make a quick playable version", "test this jump/dash/grapple mechanic", "game jam idea", or any request for a small browser game to try something out. Also use to iterate on an existing prototype in `.liang/prototypes/` ("make the jump floatier", "add enemies to the platformer").
---

# Liang Game Prototyper

Turn a game idea into a small playable browser prototype, fast. A prototype exists to
answer one design question ("does this grapple feel good?") with the least code that can
answer it — mechanics first, polish never.

## Output Contract

All artifacts live under the **active workspace's** `.liang/prototypes/`:

```
.liang/prototypes/
├── shared_assets/                  # cross-prototype asset pool
│   ├── catalog.md                  # one row per asset — always read before generating
│   └── *.svg / *.png / *.wav ...
└── YYMMDD-HHMM_<kebab-name>/       # one folder per prototype
    ├── index.html                  # the playable prototype, self-contained
    └── README.md                   # design brief + controls + tuning log
```

- Timestamp is **local system time at creation** (get it from the system clock, e.g.
  `date` / `Get-Date`), format `YYMMDD-HHMM`. Name is 2–4 kebab-case words derived from
  the core mechanic, e.g. `260611-1532_grapple-platformer`.
- Never write prototype artifacts anywhere else — not the repo root, not this skill's
  directory.

## Control Flow

### 1. Classify the request

- **Iterate** — the user refers to an existing prototype ("the platformer from
  yesterday", "make the dash punchier"). List `.liang/prototypes/` and match by name and
  README content. Edit **in place**; append a README changelog entry. If more than one
  folder plausibly matches, ask which one.
- **Fork** — the user wants a variant while keeping the original ("try a version
  where...", "keep the old one"). Copy the folder to a new timestamped folder and note
  the lineage in both READMEs.
- **New** — everything else.

### 2. Set up directories

Ensure `.liang/prototypes/` and `.liang/prototypes/shared_assets/` exist; create
`catalog.md` with an empty table if missing. (`.liang/.gitignore` already keeps
artifacts out of version control — do not commit them.)

### 3. Scope the brief

Distill the idea into: **core mechanic**, **design question**, **controls**,
**win/lose condition** (or "sandbox"). Cut scope aggressively — one screen, one
mechanic. If the idea is big, build the riskiest or most novel mechanic first and record
everything cut in the README's "Later" list. Do not pause for sign-off; the README *is*
the brief.

### 4. Check the asset pool

Read `shared_assets/catalog.md`. Reuse any asset that fits, adapting in code (scale,
tint, flip) rather than generating a near-duplicate. Protocol, catalog format, and
`file://` loading constraints: `references/shared-assets.md`.

### 5. Build

Write `README.md` first (template: `references/readme-template.md`), then `index.html`
following the skeleton and patterns in `references/html-template.md`. Any new asset
files go into the shared pool with a catalog row added in the same step.

### 6. Verify

Run the pre-flight checklist at the bottom of `references/html-template.md` against your
own code. If the session has a browser, headless runtime, or JS syntax checker
available, use it — but do not depend on one existing.

### 7. Hand off

Report in chat: the path to open in a browser, a controls table, the design question to
evaluate while playing, and the top 3 `CONFIG` tunables to experiment with (with their
current values).

## Build Rules

- **Single self-contained `index.html`** — inline CSS and JS, vanilla JavaScript,
  Canvas 2D. No build step, no npm, no frameworks for 2D work.
- A **CDN library is allowed only when the idea genuinely needs it** (3D → Three.js,
  serious physics → a physics lib). Record the network dependency in the README.
- **All tunables in one `CONFIG` object** at the top of the script, each commented with
  units. Feel iteration happens here, not scattered through the code.
- Every prototype ships the built-ins from the skeleton: clamped delta-time loop,
  `R` to restart, backquote (`` ` ``) debug HUD, fixed logical resolution scaled to the
  window.

## Shared Asset Pool

Reuse before generate. Reference pool files via the relative path
`../shared_assets/<file>`; load only with `Image()` / `Audio()` element objects — never
`fetch()`/XHR, which fail on `file://`. New files get descriptive kebab-case names
(SVG-first for sprites) and an immediate catalog row. Never mutate or delete an existing
pool asset — other prototypes reference it; add a `-v2` file instead. Full protocol:
`references/shared-assets.md`.

## Iteration

- Edit `index.html` in place. Each pass updates the README: a changelog line
  (timestamp + what changed) and the tuning notes (which `CONFIG` values moved, what
  felt better or worse).
- A large direction change ("what if it's top-down instead?") → offer a fork rather than
  silently overwriting a playable state.

## Boundaries

- Never write outside `.liang/prototypes/`.
- Never delete prototype folders; never mutate or delete shared pool assets in place.
- Never commit `.liang/` artifacts to version control.
- One prototype tests one mechanic. Extra ideas go to the README "Later" list, not into
  the code.
- Keep the prototype openable by double-clicking `index.html` — no local server
  requirement, no ES module files, no `fetch()`.

## Reference Files

- `references/html-template.md` — index.html skeleton, loop/input/HUD/audio patterns,
  pre-flight verification checklist.
- `references/shared-assets.md` — pool protocol, catalog format, asset generation and
  naming rules.
- `references/readme-template.md` — README brief template with changelog format.
