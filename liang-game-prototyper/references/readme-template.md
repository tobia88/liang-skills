# Prototype README Template

Every prototype folder gets a `README.md` in this shape. Write it *before* the code —
it is the design brief. Keep each section to a few lines; the README should be readable
in under a minute.

```markdown
# <Prototype Name>

> <one-line pitch — what you do in it>

**Created:** 2026-06-11 15:32 · **Status:** playable
<!-- Status: playable | wip | parked. Add "Forked from: <folder>" line when forked. -->

## Design question

<The ONE thing this prototype exists to find out, phrased as a question.
e.g. "Does a grapple on a 2s cooldown feel better than unlimited swinging?">

## How to run

Open `index.html` in a browser.
<!-- If a CDN library is used: "Needs internet on first load (three.js via CDN)." -->

## Controls

| Key | Action |
|-----|--------|
| A/D or ←/→ | move |
| Space | <mechanic> |
| R | restart |
| ` | toggle debug HUD |

## Tuning notes

<Living notes from feel iteration. Which CONFIG values are load-bearing, what range
felt good, what felt wrong and why. e.g. "grappleCooldown below 1.5s trivializes gaps;
2.0 felt deliberate.">

## Shared assets used

- `../shared_assets/player-mech-32.svg` — player
<!-- "None (all shapes drawn in code)" if none. -->

## Later

<Ideas deliberately cut to keep the prototype to one mechanic. This list is where
scope creep goes to wait.>

## Changelog

- 2026-06-11 15:32 — created: <one-line summary of initial build>
<!-- One line per iteration pass, appended at the bottom:
- 2026-06-12 10:05 — dash punchier: dashSpeed 600→900, cooldown 1.2→0.6 -->
```

Rules:

- **Changelog** gets one line per iteration pass with a timestamp and the concrete
  change — including the CONFIG before→after values when the change was tuning. This is
  the prototype's memory across sessions.
- **Tuning notes** record *conclusions*; the changelog records *events*. Don't duplicate.
- When forking, copy the README, add the `Forked from:` line, reset the changelog to a
  single "forked: <why>" entry, and add a "forked to" note in the parent's changelog.
