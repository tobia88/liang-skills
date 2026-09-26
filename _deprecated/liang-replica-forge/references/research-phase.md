# Phase 1 — Research: slices, prompts, schema, file format

## Contents
1. Slice decomposition menus (per domain)
2. Researcher prompt templates (preamble + brief pattern)
2.5 Source vetting & finding quality (these rules go IN the prompt)
3. The research schema
4. Research file format (`research/NN-<slice>.md`)
5. Tier A: Claude Code Workflow script template
6. Tier B/C: sequential research

---

## 1. Slice decomposition menus

Pick 5–7 slices. One researcher per slice, each blind to the others. One slice
is always the *look itself* — researched as implementable rules (hex values,
shading/stepping/geometry rules), never vibes. That holds when you are
restyling the target AND when you are running faithful on a target whose visual
identity is load-bearing (a bounded palette, a resolution grid, a signature
silhouette): if the user names the look as a reason the target is worth
replicating, it earns a slice even at the 4-slice floor. Adapt names to the
target; these are starting menus, not law.

**2D game** (proven in the reference run):
1. Core mechanics & movement feel (incl. reviewer "feel" testimony)
2. World structure & level design (zones, gating, checkpoints, geometry motifs)
3. Weapons/abilities, upgrades & progression (esp. first-hour acquisition order)
4. Enemies & bosses (behaviors, patterns, phases, staging)
5. Story, tone, UI & game-feel juice (premise, humor, HUD, shake/hitstop/particles)
6. Style as implementable rules — mandatory on restyle runs, and on faithful
   runs whose look is identity-critical

**3D game** (untested — see `domain-3d-games.md`):
1. Core mechanics & movement feel **+ camera behavior** (camera is its own axis:
   follow distance/lag, collision, lock-on, FOV events)
2. Spatial/level design (landmarks, sightlines, verticality, encounter spaces)
3. Combat/ability systems & progression
4. Enemies & encounter design
5. Story, tone, presentation & juice
6. Style as rules — mandatory on restyle runs, and on faithful runs whose look
   is identity-critical; must be a low-geometry-cost family (low-poly,
   flat-shaded, PSX-era, wireframe)

**Software** (untested — see `domain-software.md`):
1. Core workflows end-to-end (the verbs users actually perform, step by step)
2. Data model & objects (entities, fields, relationships, lifecycle states)
3. UX: layout, navigation, interactions, keyboard shortcuts
4. Edge behaviors & rules (validation, limits, conflicts, undo, empty states)
5. Visual system (spacing, type, color tokens, iconography, motion)
6. Onboarding, microcopy & tone

## 2. Researcher prompt templates

Every researcher prompt = **role preamble** + **slice brief**, joined by a
blank line. Two preamble families below; interpolate `{...}` from the target
brief.

**Tool-name portability — read before pasting any prompt below.** The templates
name Claude Code's tools. That sentence is a SLOT, not literal text: substitute
it for the harness that will actually run the researcher.

- Tier A (Claude Code): "Use WebSearch and WebFetch to research. If those tools
  appear deferred in your environment, load them via ToolSearch first."
- Tier B (Pi or any other CLI): "Use whatever web search and page-fetch tools
  this session exposes — list your available tools first if unsure — to
  research."
- Tier C / unknown harness: "Use whatever web search and page-fetch capability
  you have. If you have NONE, say so explicitly in `summary`, mark every
  finding `confidence: "low"`, and leave `sources` empty rather than inventing
  URLs."

Never leave a tool name in a prompt that will run outside the harness that
defines it. The same substitution applies to the fidelity preamble in
`verify-phase.md` §2.

### Game-target preamble

```
ROLE: web researcher gathering facts for a game-replication specification.
TARGET GAME: "{REAL_TITLE}" — {one-line identification: genre, developer,
publisher, release year, platforms, protagonist}.
Use WebSearch and WebFetch to research. If those tools appear deferred in
your environment, load them via ToolSearch first. Do NOT answer from memory
alone — verify against real sources: the store page, official
developer/publisher pages, wikis, reviews from real outlets, developer
interviews, and gameplay breakdowns.
Cross-check important claims across 2 or more sources when possible.
OUTPUT RULES: return via the structured output schema only (Tier B/C: return
ONE fenced json block matching the schema shape, and nothing else). Each
finding is one atomic claim, concrete enough that a developer could implement
from it. Aim for 10–20 findings. No padding, no marketing fluff.
SOURCE RULES — these bind the findings themselves, not just your notes:
- Open every page you cite. Attach a URL to a claim only if you can quote the
  exact sentence or figure on that page that states it. "The page is about the
  right topic" is not a citation; if that is all you can confirm, either find a
  source that states the fact directly, or mark it "estimated/inferred, not
  directly sourced in the cited page" and cap confidence at low.
- Check what a domain IS before citing it. Reject AI-companion / roleplay /
  persona pages ("chat with…", "talk to your fav…"), auto-generated lore pages,
  and content farms however wiki-like they look — read the site's own
  About/footer when the domain is unfamiliar. They are frequently
  self-contradictory and are not equivalent to an edited wiki or a published
  article.
- Never cite a forum index, subreddit front page, wiki root, or store landing
  page when a specific thread, section, or article containing the fact is
  obtainable — on forums and wikis it almost always is.
- If the same URL would back more than 3 of your findings, either record which
  heading/paragraph of that page supports each claim, or add a claim-specific
  corroborating source. One URL carrying a whole slice is a sign the slice is
  under-researched, not a sign of strong sourcing.
- confidence: high requires 2 independent sources (different domain AND outlet)
  stating the same specific fact. One source caps you at medium — the target's
  own official store/developer page may count as primary, but label it
  "primary source, single-sourced". If two of your own cited sources disagree
  with each other or with the claim as worded, you may not use high: split the
  finding to show the disagreement, drop it, or cap at low with a note naming
  the disagreeing URL and quoting what it says instead.
- One claim = one falsifiable fact. If the sentence needs "and" to join two
  facts that could independently be true or false, split it into two findings,
  each with its own sources and confidence.
- Do not log a finding whose content is only reviewer praise ("tight",
  "near-perfect", "adrenaline-fuelled") unless it is paired with the concrete
  mechanic, number, or sequence that produced that impression. Pure praise
  belongs in `summary` — where feel testimony is wanted; `findings` is for
  implementable facts.
- Before finishing, merge near-duplicate findings that state the same fact from
  two angles. Two entries for one fact is not two data points.
```

The SOURCE RULES block is not optional decoration — it is the enforcement
described in §2.5. Keep it verbatim in every researcher prompt, including the
style and software preambles below.

### Style preamble (restyle runs)

```
ROLE: art-direction researcher. You are researching an ART STYLE, not a game.
TARGET STYLE: {style identification with canonical works, e.g. "the look of
Katsuhiro Otomo's AKIRA (1988) and adjacent late-80s/90s retro-futurist
mecha anime"}.
Use WebSearch and WebFetch (load via ToolSearch if deferred). Prefer
art-analysis articles, animation/design breakdowns, palette analyses, staff
interviews, credible video-essay writeups.
GOAL: extract direction that is IMPLEMENTABLE in {the target medium} by an AI
that cannot look anything up. Vague vibes are useless — every finding must
translate to a rule, a value, or a technique.
Cover: {palette families with approximate hex values marked as estimates;
shading/line rules; background/environment treatment; animation or motion
principles; FX conventions; typography/UI flavor; iconic motifs}.
OUTPUT RULES: (same as game preamble; aim 12–20 findings.)
```

### Software-target preamble

Adapt the game preamble: identify the product (vendor, launch year, platform,
pricing tier if relevant); point sources at official docs, help centers,
changelogs, professional reviews, comparison articles, and public design
teardowns; findings must be concrete enough to implement (exact button
placements, field names, state transitions, shortcut keys).

### Slice briefs

2–6 lines: "YOUR SLICE: <name>." + a dense dig-into list of the specific
questions this slice must answer (see the menus above; the reference run's
briefs are visible in `example-wireblade/example-readme.md`'s research
description). For feel-critical slices, explicitly request reviewer/developer
*testimony language* — it feeds PART 1's design-intent bullets.

## 2.5 Source vetting & finding quality (these rules go IN the prompt)

The schema can force a `sources` array to be non-empty. It cannot force the URL
to be real, to be the kind of thing a source should be, or to actually contain
the fact — and a cheap researcher will fill any field you demand. In a live
test of these templates, three Haiku researchers returned 46 findings with
near-perfect formal compliance, and an audit that actually fetched the pages
found:

- an AI roleplay-chatbot platform's auto-generated lore page cited as though it
  were an edited wiki — internally self-contradictory, disagreeing with every
  corroborated source, and carrying two structural claims by itself;
- a `confidence: high` finding one of whose own cited sources said the opposite;
- three URLs attached to claims their pages do not contain (right topic, silent
  on the specific fact);
- one slice citing a single Steam guide for all twelve of its findings, which
  is exactly what let the mismatch above hide;
- a bare forum index cited where deep links were demonstrably reachable in the
  same research pass.

None of that is detectable downstream: the fidelity verifiers check the spec
against reality, not the research files against their own citations. So vetting
has to happen inside the researcher's own prompt — **a rule the researcher
never sees cannot bind it.** The SOURCE RULES block in §2 is that enforcement.

**When results land, spend a minute per slice on these three checks** before
writing the file:

1. **Domain sanity.** Scan `sources_consulted` for anything you don't
   recognise, and open it. Chatbot/persona/AI-lore pages and content farms get
   their findings deleted, not downgraded.
2. **Monoculture.** If one URL appears in most of a slice's findings, the slice
   is under-researched — re-dispatch it asking for claim-specific corroboration.
3. **High-confidence spot-check.** Fetch the sources behind two or three
   `confidence: high` findings the spec will actually depend on (physics
   numbers, structural facts, palette values). This is cheap, and it is the only
   place a fabricated citation gets caught before it becomes a spec number.

Findings you delete or downgrade here are not a loss. An unsourced claim that
reaches PART 2 comes back as a blind-verifier recomputation or a fidelity flag
one round later, at much higher cost.

## 3. The research schema

Use structured output where the harness supports it; otherwise instruct the
researcher to emit exactly this JSON shape in a fenced block.

```js
const RESEARCH_SCHEMA = {
  type: 'object',
  required: ['slice', 'summary', 'findings', 'sources_consulted'],
  properties: {
    slice: { type: 'string' },
    summary: { type: 'string', description: '2-4 sentence overview of what was learned' },
    findings: {
      type: 'array',
      minItems: 6,
      items: {
        type: 'object',
        required: ['claim', 'detail', 'confidence', 'sources'],
        properties: {
          claim: { type: 'string', description: 'One atomic, concrete fact stated in a single sentence' },
          detail: { type: 'string', description: 'Implementation-relevant specifics (numbers, behaviors, sequences), 1-4 sentences' },
          confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
          sources: { type: 'array', minItems: 1, items: { type: 'string' }, description: 'URLs actually consulted for THIS specific claim' },
        },
      },
    },
    sources_consulted: {
      type: 'array',
      items: {
        type: 'object',
        required: ['url', 'title'],
        properties: {
          url: { type: 'string' },
          title: { type: 'string' },
          covered: { type: 'string', description: 'What this source contributed' },
        },
      },
    },
  },
}
```

## 4. Research file format

Write `research/NN-<slice-slug>.md` for each slice **as soon as its result
lands** — don't batch at the end (a crashed session loses unbatched results).

```markdown
# NN — <Slice name>

> Researcher: <model> · <date> · <run/workflow id if any>

<summary paragraph>

## Findings

### F1 — <claim sentence> `[confidence]`
<detail>
Sources: <url> · <url>

### F2 — ...

## Sources consulted
- <url> — <title> — <what it contributed>
```

## 5. Tier A: Claude Code Workflow script template

> **Tier A only.** The script below is a Claude Code Workflow and runs only
> under that tool — it is not JavaScript you can execute with node, and the
> `phase()` / `agent()` / `parallel()` calls exist nowhere else. If your harness
> has no Workflow tool, skip this section entirely and go to §6.

Adapt this skeleton (from the reference run). Embed all target-specific
strings as literals — **do not pass them via `args`** (they may arrive
JSON-stringified).

```js
export const meta = {
  name: '<slug>-research',
  description: 'Parallel web research: <target> facts with per-claim sources, for an anonymized replication prompt',
  phases: [{ title: 'Research', detail: '<N> researchers, one slice each, per-claim source URLs' }],
}

const RESEARCH_SCHEMA = { /* as §3 */ }
const PREAMBLE = `...`          // §2, interpolated by you at authoring time
const SLICES = [
  { key: 'r1:<slug>', slice: '<name>', preamble: PREAMBLE, brief: `YOUR SLICE: ...` },
  // ...
]

phase('Research')
log('Fanning out ' + SLICES.length + ' researchers')
const results = await parallel(
  SLICES.map((s) => () =>
    agent([s.preamble, s.brief].join('\n\n'),
      { label: s.key, model: 'haiku', schema: RESEARCH_SCHEMA, phase: 'Research' }))
)
const packaged = SLICES.map((s, i) => ({ key: s.key, slice: s.slice, data: results[i] }))
const missing = packaged.filter((p) => !p.data).map((p) => p.key)
if (missing.length) log('WARNING: no result from: ' + missing.join(', '))
return packaged
```

After the workflow returns, write the `research/` files from the returned
data (note: some harnesses nest the value — check for a `result` property
before assuming the shape).

## 6. Tier B/C: sequential research

At Tier B, prefer spawning each slice as its own fresh one-shot process on a
cheap model (`pi -p --model <cheap-model> "<preamble + slice brief>"`) — that
keeps the cost routing and keeps Phase 1 out of your context. What follows is
for when per-process model selection is unavailable, or when you are at Tier C
and you are the researcher.

Run the same slices one at a time with whatever web tools the harness has.
Sequencing costs wall-clock, not quality — but only if the source discipline
survives a long session, and "keep it in mind" is not a mechanism. Per slice,
in this order, no shortcuts:

1. **Search/fetch FIRST.** Do not write a single finding before you have
   actually opened at least two sources for this slice.
2. **Write the §3 JSON block** for the slice, verbatim shape, into your working
   notes — including `sources` per claim. This step is not optional at Tier
   B/C; it is what stops the drift into essay-with-a-bibliography.
3. **Self-check the block before rendering**, against §2.5: any finding with an
   empty `sources` array is deleted, or demoted to `confidence: "low"` with
   `sources: ["MEMORY — unsourced"]`. Any URL you did not actually open is
   deleted. Fabricated or homepage-level citations poison the bundle
   (principle 4) and NOTHING downstream detects them.
4. **Render and save NOW** into `research/NN-<slice>.md` (§4 format), before
   starting the next slice. At Tier C2 (no file system), emit it as its own
   chat message with its save path.
5. Only then start the next slice, and do not carry slice N's sources into
   slice N+1's findings.
