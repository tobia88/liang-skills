---
name: liang-quest-planner
description: "Same-context campaign planner that consumes brainstorm output, in-session conversation, or both. Extracts locked decisions, fills gaps via adaptive Socratic questioning, generates a free-design HTML plan (body drafted by a configurable body-drafter subagent, CSS assembled by script), runs open discussion, and writes lean quest markdown files. Four phases: decision extraction (with optional gap-fill), HTML generation, open discussion, quest markdown writing."
---

# Liang Quest Planner

Same-context, one-shot campaign planner. Consume decisions from the live conversation, produce a free-design HTML plan and lean quest markdown files. Stops at planning artifacts — never executes.

## Core Contract

- **Same-context only.** Reads the live conversation (brainstorm Strategy Report, lite session output, or general chat). Does not accept file paths or read saved brainstorms. Downstream execution flows through `liang-quest-executor` (the planner-native single-context runner).
- **Four phases in order**: (1) decision extraction with optional gap-fill, (2) HTML generation, (3) open discussion, (4) quest markdown writing.
- **HTML is editable during Phase 3.** Discussion updates land in `plan.html` (edit-in-place by default, full regen on structural changes). User refreshes browser manually to see changes.
- **Discussion is user-led.** No forced walkthrough.
- **Quest markdowns + manifest land only at Phase 4 finalization.** Never written during open discussion.
- **Quest markdowns are lean executable docs**: purpose, steps/code blocks, dependencies, and victory conditions. No rationale, tutorial prose, or "why" explanations; HTML carries that context.
- **Output layout** is fixed (downstream executors depend on it):
  ```
  .liang/campaigns/campaign-<YYYY-MM-DD>-<HHMM>-<slug>/
    plan.html
    quest-001-<name>.md
    quest-002-<name>.md
    manifest.yaml
  ```
  All flat. No subdirectories. The directory is prefixed with the local generation date and time (`YYYY-MM-DD-HHMM`, 24-hour clock) so same-day campaigns sort in generation order; the slug is lowercase-hyphenated from the Main Quest title.

## Terminology

- **Decision Summary** — compact (~2k token) structured extraction of brainstorm context. All downstream phases work from this, not raw conversation.
- **Campaign** — the folder grouping `plan.html` + quest files + `manifest.yaml`.
- **Quest File** — `quest-NNN-<name>.md`, executor-agnostic.

## Activation

Activate when:
1. User invokes by name (`skill:liang-quest-planner`)
2. As a Next Move option immediately after `liang-brainstorm-relentless` finalizes a Strategy Report
3. After `liang-brainstorm-quick` when the user picks the "Plan first" downstream at lite's Next Move (lite presents this skill and a delegated executor as equal alternatives — Recommended biases by scope-creep signals)
4. From general conversation when explicitly invoked — runs Adaptive Socratic Gap-Fill first

Do not silently activate from generic intent like "plan this." If unclear, ask.

**Quick Mode** activates when the user appends `--quick` (e.g., `skill:liang-quest-planner --quick`) or prefixes with `quick:`. See the Quick Mode section below for the overrides it applies.

## Quick Mode

Opt-in path for fast planning when you'd rather iterate against the HTML than gate-walk through brainstorming. Overrides the standard flow:

- **Skip intent confirmation** (Phase 1a).
- **Gap-Fill cap: 2 questions** (down from 5). After that, missing fields stay `unspecified` and the planner proceeds. No graceful exit to `liang-brainstorm-relentless` — quick mode opts you into "plan from what I gave you."
- **Skip the Decision Summary sanity-check gate** (Phase 1c). Display the summary inline, proceed immediately to Phase 2.
- **Same Phase 2c machinery as standard mode** — the body-drafter subagent drafts the body, `assemble_plan.py` validates and assembles. Quick mode skips nothing here: the body structure is pinned by `class-contract.md`, so the planner can still edit faithfully during Phase 3 by reading the affected section back first.

Standard mode keeps all gates. The iterative-HTML behavior in Phase 3 applies to both modes.

## Phase 1 — Decision Extraction

### 1a. Confirm intent

State what the skill will do and confirm the user wants to proceed.

### 1b. Adaptive Socratic Gap-Fill (only if needed)

If the conversation contains a `liang-brainstorm-relentless` Strategy Report (locked-decision table, Main Quest / Victory Conditions / Scope / Risks / Fog of War headings), **skip this**.

Otherwise, identify which Decision Summary fields are missing or under-specified and ask 2–5 focused questions covering only the gaps, batched in a single `AskUserQuestion` call where possible.

- **Hard cap: 5 questions.** If more would be needed, suggest the user run `liang-brainstorm-relentless` first and exit gracefully.
- Never re-ask anything the conversation already covers. Never re-validate locked decisions.
- If the user skips a field, mark it "unspecified" — they can correct during the sanity check.

### 1c. Build and present the Decision Summary

Produce a structured summary with these fields:

1. **Main Quest** — goal + core problem (2-3 sentences)
2. **Planning Lens** — the lens that drove the brainstorm
3. **Target User**
4. **Locked Decisions** — for each: short label, chosen path, key tradeoff, confidence (Low / Medium / Medium-high / High)
5. **Victory Conditions**
6. **Scope Boundary** — in-scope items and non-goals
7. **Risks** — with mitigations
8. **Open Questions / Fog of War**
9. **Decision Table** — Path | Status (Recommended / Rejected / Deferred) | Reason

~2k tokens is guidance, not a cap. Present to the user as a sanity check. If they correct anything, update and re-present. Proceed only after confirmation.

## Phase 2 — HTML Generation

### 2a. Decompose into quests (in memory)

Identify cohesive, independently-verifiable outcomes. Merge items sharing an outcome; split where one outcome must land before another can be planned. Order by dependency topology. Target 2–8 quests driven by meaningful decomposition, not a target count.

For each quest: title, purpose, numbered steps, code blocks where applicable, dependencies, victory conditions, risks, **difficulty**.

Include code blocks when a quest writes or modifies a file, specifies a structured data format (YAML/JSON), or has a concrete "write this content here" action. Skip them for purely organizational or subjective work. When in doubt, include — over-specifying beats under-specifying for downstream executors.

**Difficulty classification.** Tag each quest `easy`, `medium`, or `hard` based on what an executor will actually face. Downstream executors route to different models per `.liang/project.yaml`'s `execution_by_difficulty` mapping, so the field is load-bearing — get it roughly right rather than perfectly right.

Criteria and tie-break rule: `liang-quest-core/references/campaign/difficulty-guide.md` (canonical).

**Decide on a plan visual.** Resolve the policy first: a `--no-visual` flag on the invocation (same convention as `--quick`) forces none, `--visual` forces inclusion; otherwise read `planner.visual` from `.liang/project.yaml` (`auto` when the key or file is absent — never block on it): `never` → skip, `always` → include the best-fit type, `auto` → classify per `references/html-design-contract.md` §10 by what the campaign's **main deliverable** is — **UI wireframe** (screens, panels, forms, editor tools, dashboards), **flow/state diagram** (pipelines, subsystems talking, state machines, ability lifecycles, branching logic), **sequence timeline** (behavior over time: animation, camera moves, travel, handshakes, turn phases), or **none** (backend, refactors, migrations, library/API, build/CI). Include a visual only when it earns its place; **when ambiguous, skip** — adding one in Phase 3 is cheap, removing noise from every plan is not. The plan's own quest dependency ordering is never a trigger (§10). If a visual is planned, write a one-line **visual recipe** naming the type + kit primitives (e.g., "timeline: camera + token tracks over 8 ticks, traveling token, beat strip for confirm→travel→arrive") — Phase 2c hands the recipe to the body subagent verbatim. Announce the decision in one sentence either way.

### 2b. Pick an aesthetic direction

Read `references/html-design-contract.md` for the catalog. Auto-pick based on the Planning Lens (e.g., *Skill Creation + Pipeline Architecture* → FF-gold or Xenoblade-cosmic; *Narrative + Dialogue* → Persona-blue or Octopath-watercolor; *Profiling + Observability* → NieR-monochrome). Default to FF-gold when ambiguous. Announce the choice in one sentence and proceed — no question round here. The user can request a different direction during Phase 3 discussion.

### 2c. Assemble the HTML (subagent body + script assembly)

`plan.html` is assembled from three fixed layers — no per-run CSS regeneration, and no model re-types CSS as output in any standard path.

1. **Brief the body-drafter subagent to draft the body.** Resolve the drafter model from `.liang/project.yaml`: `models.body_drafter` → `models.execution_by_difficulty.medium` → harness default. If `project.yaml` is missing, use the harness default silently — never block planning on it, and never write the file. Spawn a general-purpose subagent with the resolved model whose prompt contains: the Decision Summary, the full 2a quest decomposition (titles, purposes, steps, code blocks, dependencies, victory conditions, difficulties), the visual recipe from 2a (only when a plan visual was planned — the subagent renders the recipe, it never designs one), and the full text of `references/templates/class-contract.md`. The subagent writes **body-only HTML** — the content inside `<div class="page">`, masthead through page-footer; no document shell, no `<style>` block, no inline CSS beyond the `--mock-cols` exception — to `_body.html` inside the campaign folder (resolve/create the folder first). Code blocks wrap tokens in §9 span classes; all user-derived content is HTML-escaped.
2. **Assemble + validate via script.** Run:
   `python references/templates/assemble_plan.py <campaign>/_body.html <skin-slug> <campaign>/plan.html --title "<Campaign Title>"`
   Resolve the skin slug from the direction name: lowercase-hyphenated, e.g. *NieR-monochrome* → `nier-monochrome`. The script structurally validates the body (TOC anchors ↔ section IDs bidirectionally, required skeleton classes, difficulty badges in TOC and quest headers, no `<style>`/`<script>`/`<link>`/document-shell tags, no inline styles beyond the whitelisted custom props (`--mock-cols`, `--tl-cols`, `--tl-start`, `--tl-span`), no external assets, at most one plan-visual section), then inlines `base.css` + `skin-<slug>.css` (+ the matching visual kit automatically — `mockup.css` for `ui-mock-section`, `diagram.css` for `diagram-section`, `timeline.css` for `timeline-section`) into one `<style>` block, in that order, and writes the single self-contained `plan.html`. The `.css` files never ship beside the output.
3. **On validation failure** (exit 1, `VALIDATION:` lines on stderr), send the violations back to the same subagent to fix, then re-run the script. After 2 failed retries, the planner writes the body itself and re-runs the script.
4. **On success, delete `_body.html`** — the campaign folder layout is fixed and flat (`plan.html`, quest files, `manifest.yaml` only).

**Division of labor is fixed.** The planner decides all content in 2a/2b (decomposition, difficulty, visual recipe, aesthetic direction); the body-drafter subagent only transcribes that plan into the contractual skeleton; the script owns CSS assembly and structural validation.

**Fallbacks.** If subagent spawning is unavailable, the planner drafts the body itself (same body-only contract) and still assembles via the script. If Python is unavailable, fall back to manual assembly as a last resort: read `base.css` + the skin (+ the matching visual kit if the body has a plan-visual section), inline them verbatim into one `<style>` block, and perform the script's structural checks by hand.

**Code blocks must include CSS-only syntax highlighting** per the token-class taxonomy in `references/html-design-contract.md` §9. The token rules live in `base.css`; the palette variables live in the skin. The body generator wraps tokens in `<span>` classes but never generates the CSS rules themselves — they are already in `base.css` and the skin.

Every `plan.html` must contain:
- Hero / masthead: campaign title, slug, date, quest count, planning lens
- Anchor-linked TOC of all quests (anchors must target valid section IDs) — each entry shows the quest's **difficulty badge**
- *(only when Phase 2a planned a visual)* at most one plan-visual section between the TOC and the first quest — `ui-mock-section` UI wireframe, `diagram-section` flow/state diagram, or `timeline-section` sequence timeline — with inline numbered badges + a legend (§10)
- Per-quest sections: title, purpose (1–2 sentences), **difficulty badge**, numbered steps, code blocks with file path labels and syntax highlighting, brief rationale (1–2 sentences), Dependencies + Victory Conditions in a footer strip
- Campaign notes (risks, open questions carried from the Decision Summary)
- Footer with generator attribution + timestamp

### 2d. Visual spot-check + auto-open

After confirming the file write succeeded (per `references/html-design-contract.md` §4.4):

1. **Run the Visual Spot-Check** per §4.4 — Playwright screenshot at 375px viewport width only, sampling the longest-content quest, the shortest-content quest, the decisions table, and the plan-visual section when present. `base.css` + every skin have been pre-audited; only content-driven breaks remain. Fix any layout issue surfaced in-place before showing the user. Skip the screenshot loop silently if Playwright is unavailable.
2. **Auto-open** `plan.html` in the user's default browser. Do not ask first; do not offer the in-chat-only path. Per-OS commands:
   - Windows: `cmd //c start "" "<absolute-path>"` (the double-slash escapes `/c` for Git-Bash/MSYS shells)
   - macOS: `open "<absolute-path>"`
   - Linux: `xdg-open "<absolute-path>"`

After the open command runs, announce the absolute path in-chat on a single line so the user can re-open it later. If the open command fails (non-zero exit, no browser handler), announce the path and ask the user to open it manually — do not retry blindly.

## Phase 3 — Open Discussion

User leads. No forced walkthrough or section-by-section review. Proceed to Phase 4 when the user signals readiness ("looks good," "write the quests," "proceed").

When discussion produces a substantive change to a quest, decision, victory condition, or other plan element, **update `plan.html` on disk to reflect it**:

- **Edit-in-place** (default) — use the Edit tool to modify only the affected section. Read the affected section from `plan.html` first — the body was drafted by the subagent, so never edit from memory. Fast turns, preserves overall structure, preserves anchor IDs (the TOC's contract with the body). Preserve HTML escaping for all user-derived content.
- **Full regen** — when the change is structural (re-decomposition, quest count change, aesthetic swap, sweeping rationale rewrite), route through the same Phase 2c machinery: re-brief the body-drafter subagent (same model resolution as Phase 2c) with the updated decomposition, re-run `assemble_plan.py` (same skin unless the user requested an aesthetic swap). Slower but always self-consistent.
- The model picks based on change size. When uncertain, prefer edit-in-place — drift across small edits is recoverable; an unnecessary full regen burns a subagent round-trip.

After updating, announce in-chat what changed in one line ("Updated quest 3 victory conditions — refresh browser to see") so the user knows to refresh.

Cosmetic chat (clarifying questions, acknowledgments) does not trigger updates — only changes the user agrees should land in the plan.

## Phase 4 — Quest Markdown Writing

When the user signals ready, write quest markdowns and `manifest.yaml` atomically.

Quest files follow `references/quest-template.md` and the naming convention `quest-NNN-<name>.md` (3-digit zero-padded number, lowercase-hyphenated slug from quest title, ~40 char max at word boundary).

Manifest follows `references/manifest-example.yaml` — includes `schema_version: 4` (campaign manifest schema; distinct from `.liang/project.yaml`'s `schema_version: 1`), `q001`, `q002`, ... IDs, `status: "ready"` at creation, `depends_on` is a list of quest IDs, **`difficulty` is `"easy"`, `"medium"`, or `"hard"`** (per the classification in Phase 2a). Downstream executors consume `difficulty` to route the quest to the right model per `.liang/project.yaml`'s `execution_by_difficulty` mapping — do not omit the field.

Quest markdown rules:
- Include only Purpose, Steps/code blocks, Dependencies, and Victory Conditions.
- Code blocks start with a file path comment (`// file: path/to/file` or `# file: path/to/file`).
- No tutorial prose, rationale, or "why" explanations.

### Finalization sequence

1. Verify all content composed in memory.
2. Reuse the campaign folder created for `plan.html` in Phase 2. If missing, compute/create `campaign-<YYYY-MM-DD>-<HHMM>-<slug>` now.
3. Write quest files, then `manifest.yaml` (`plan.html` already landed in Phase 2).
4. If any write fails partway, abort and report which paths landed and which didn't.
5. Tell the user the saved path.

### VCS policy

Read `vcs_artifacts.planning` from `.liang/project.yaml`, then follow the canonical
semantics (including ask → write-back) per
`liang-quest-core/references/project/project-yaml.md § VCS Artifact Policy (optional)`.

### Next Move

After writing, suggest the compatible executor as a copy-pasteable command using the literal campaign path:

```
skill:liang-quest-executor .liang/campaigns/campaign-<YYYY-MM-DD>-<HHMM>-<slug>
```

Suggestion only. Do not invoke. This is the final interaction of the session.

## Boundaries

The non-obvious hard stops:

1. **One-shot quest writing.** Do not re-plan or update existing quest markdown files in subsequent invocations. (Iterative HTML edits during Phase 3 are not "re-planning" — they're discussion-mediated refinement before quest files are written.)
2. **No execution.** Do not run code, install deps, or touch VCS beyond `vcs_artifacts` policy.
3. **No runtime enforcement.** Manifest status and dependency ordering are informational; executors own them.
4. **No secrets, .env, .git, credentials, dependency folders, build outputs, or large binaries** in any generated artifact.

## Relationship to Other Skills

- **Upstream**: `liang-brainstorm-relentless` (Strategy Report → Next Move); in-session conversation via explicit invocation
- **Body-drafting subagent**: Phase 2c (and Phase 3 full regens) delegate body-only HTML drafting to a general-purpose body-drafter child whose model resolves from `.liang/project.yaml` (`models.body_drafter` → `execution_by_difficulty.medium` → harness default); `references/templates/assemble_plan.py` validates the body and assembles the CSS layers. The planner falls back to drafting the body itself if subagent spawning is unavailable
- **Downstream**: `liang-quest-executor` — the planner-native single-context runner. Sole supported executor for planner output.
- **Shared foundation**: `liang-quest-core` — shared protocol, manifest schema, status transitions, run report.
- **Opt-in from**: `liang-brainstorm-quick` — one of the two same-session downstreams lite offers at finalization (the other is a delegated executor for direct execution). Lite emits no files; this planner reads decisions directly from the live conversation.

## Reference Files

Read before generating:
- `references/html-design-contract.md` — quality contract, eight-direction catalog, CSS guardrails, assembly protocol. **Read before every HTML generation.**
- `references/templates/class-contract.md` — fixed body structure + CSS variable interface. The single source of truth for class names, HTML skeleton, and the skin variable contract.
- `references/templates/base.css` — shared structure + all 14 pitfall fixes (§5.1–5.14). Read verbatim at generation time; contains zero hardcoded colors.
- `references/templates/skin-<name>.css` — per-direction palette + motif. Naming convention: `skin-` + lowercase-hyphenated direction slug.
- `references/templates/mockup.css` / `diagram.css` / `timeline.css` — the three conditional plan-visual kits (Layer 4): UI wireframe, flow/state diagram, sequence timeline. Auto-included by `assemble_plan.py` (at most one per plan) when the body contains the matching section class; zero hardcoded colors, consume the skin variables; CSS-only animation with reduced-motion/print fallbacks.
- `references/templates/assemble_plan.py` — deterministic assembler: structurally validates the body (including at most one plan-visual section), inlines `base.css` + skin (+ the matching visual kit when present), writes the self-contained `plan.html`. Always run this instead of inlining CSS by hand.
- `references/quest-template.md` — quest markdown skeleton
- `references/manifest-example.yaml` — manifest schema example
