---
name: liang-quest-planner
description: "DEPRECATED, use liang-queue-add / liang-queue-sweep instead. Same-context campaign planner that consumes brainstorm output, in-session conversation, or both. Extracts locked decisions, fills gaps via adaptive Socratic questioning, writes a plan.md dossier plus lean quest markdown files, and renders an optional free-design plan.html from them when the project setting planner.html is true (body drafted by a configurable body-drafter subagent, CSS assembled by script), with open discussion held on that page. Four phases: decision extraction (with optional gap-fill), decomposition and plan files, open discussion, finalization."
---

# Liang Quest Planner

Same-context, one-shot campaign planner. Consume decisions from the live conversation, produce a `plan.md` dossier and lean quest markdown files — plus an optional free-design `plan.html` render when the project asks for one. Stops at planning artifacts — never executes.

## Core Contract

- **Same-context only.** Reads the live conversation (brainstorm Strategy Report, lite session output, or general chat). Its input is the conversation, never a saved brainstorm file; an orchestrator's brief may still cite files to read from disk (a saga's `inventory.md`, recon docs, predecessor campaigns). Downstream execution flows through `liang-quest-executor` (the planner-native single-context runner).
- **Four phases in order**: (1) decision extraction with optional gap-fill, (2) decomposition and plan files, (3) open discussion, (4) finalization.
- **`.liang/project.yaml` is required.** A missing file triggers the shared first-run interview; `planner.html` decides the surface. See Surface: `planner.html`.
- **`plan.md` is mandatory and holds the "why"**: Decision Summary, per-quest purpose, rationale, difficulty, dependencies, victory conditions, risks, open questions, decision table, and the visual recipe when one was planned. No steps, no code blocks. The executor ignores it.
- **Quest markdowns hold the "how"**: purpose, steps/code blocks, dependencies, and victory conditions. No rationale, tutorial prose, or "why" explanations — `plan.md` carries that context. Victory conditions are the one deliberate overlap; nothing else is duplicated between the two.
- **HTML on** (`planner.html` true): `plan.md` and the quest files land in **Phase 2**, which then renders `plan.html` from them and opens it; Phase 3 discussion happens on the page; Phase 4 writes `manifest.yaml` only.
- **HTML off** (`planner.html` false): **nothing lands until Phase 4.** Phase 2 decomposes in memory and shows a compact quest table in chat, there is no Phase 3, and Phase 4 writes `plan.md` + quest files + `manifest.yaml` in one atomic sequence.
- **`plan.html` is an optional render**, never a source: it is regenerated whole from `plan.md` + the quest files on disk, and never edited in place.
- **Discussion is user-led.** No forced walkthrough.
- **Output layout** is fixed (downstream executors depend on it): one flat folder per campaign holding `plan.md` (required), `plan.html` (optional render), the `quest-NNN-<name>.md` files, and `manifest.yaml`, written last — a folder without it is invisible to the pipeline. Canonical tree: `liang-quest-core/references/campaign/protocol.md` § Canonical: Planner → Executor.
  All flat. No subdirectories. The directory is prefixed with the local generation date and time (`YYYY-MM-DD-HHMM`, 24-hour clock) so same-day campaigns sort in generation order; the slug is lowercase-hyphenated from the Main Quest title.

## Terminology

- **Decision Summary** — compact (~2k token) structured extraction of brainstorm context. All downstream phases work from this, not raw conversation.
- **Campaign** — the folder grouping `plan.md` + quest files + `manifest.yaml`, plus `plan.html` when `planner.html` is true.
- **Quest File** — `quest-NNN-<name>.md`, executor-agnostic.

## Activation

Activate when:
1. User invokes by name (`skill:liang-quest-planner`)
2. As a Next Move option immediately after `liang-brainstorm-relentless` finalizes a Strategy Report
3. After `liang-brainstorm-quick` when the user picks the "Plan first" downstream at lite's Next Move (lite presents this skill and a delegated executor as equal alternatives — Recommended biases by scope-creep signals)
4. From general conversation when explicitly invoked — runs Adaptive Socratic Gap-Fill first

Do not silently activate from generic intent like "plan this." If unclear, ask.

**Quick Mode** activates when the user appends `--quick` (e.g., `skill:liang-quest-planner --quick`) or prefixes with `quick:`. See the Quick Mode section below for the overrides it applies. `--headless` activates Headless Mode (below); it implies `--quick`.

## Surface: `planner.html`

`planner.html` in `.liang/project.yaml` decides whether this run produces a browser page. It is a **required boolean with no default** — there is no `auto` value.

- **`true`** — Phase 2 writes `plan.md` + the quest files, renders `plan.html` from them and opens it; Phase 3 discussion happens on the page; Phase 4 writes `manifest.yaml` only.
- **`false`** — **trust mode**: no HTML, no Phase 3. Phase 2 decomposes in memory and shows a compact quest table in chat; Phase 4 writes `plan.md`, the quest files, and `manifest.yaml`.

Resolve it in this order:

1. **Per-run flag.** `--html` or `--no-html` on the invocation (same convention as `--quick`) overrides the setting for this invocation only and is never written back.
2. **`planner.html` in `.liang/project.yaml`.**
3. **Key absent** — ask the single **Plan render surface** question exactly as worded in `liang-quest-core/references/project/project-yaml.md` § First-Run Interview, then write the answer back as `planner.html: true|false` and proceed (ask once, write back).
4. **File absent** — run the shared first-run interview (`liang-quest-core/references/project/project-yaml.md` § First-Run Interview), which includes that question, then proceed.

Steps 3 and 4 are the only `project.yaml` writes the planner makes, besides the `vcs_artifacts` ask-once write-back (Phase 4 VCS policy).

**Headless hard stop.** Headless mode has no user to answer either question: a missing `project.yaml`, or a present file with no `planner.html` key and no `--html`/`--no-html` flag, stops the run. Report the missing file or key and exit without planning. Never guess the value.

**Mode and surface are independent knobs.** The mode (standard / quick / headless) decides the Phase 1 gates; `planner.html` decides the surface.

## Quick Mode

Opt-in path for fast planning when you'd rather iterate against the plan than gate-walk through brainstorming. Overrides the standard flow:

- **Skip intent confirmation** (Phase 1a).
- **Gap-Fill cap: 2 questions** (down from 5). After that, missing fields stay `unspecified` and the planner proceeds. No graceful exit to `liang-brainstorm-relentless` — quick mode opts you into "plan from what I gave you."
- **Skip the Decision Summary sanity-check gate** (Phase 1c). Display the summary inline, proceed immediately to Phase 2.

Nothing else changes. Quick mode skips nothing in Phase 2: with `planner.html` true it runs the same 2c machinery as standard mode (the body-drafter subagent drafts the body, `assemble_plan.py` validates and assembles) and the same Phase 3; with `planner.html` false it shows the same quest table and goes straight to Phase 4. A user is present in quick mode, so gap-fill still asks its questions.

Standard mode keeps all gates.

## Headless Mode

Opt-in path for orchestrated invocation — another skill or a fresh-context subagent running this planner end-to-end (e.g. `liang-quest-saga-planner` batch mode). Headless is **quick mode + zero questions + the surface the setting resolves to**. Implies every Quick Mode override, plus:

- **Gap-Fill cap: 0.** Missing Decision Summary fields stay unspecified; never ask questions — there is no user to answer them.
- **`planner.html` must already be resolvable.** A missing `project.yaml`, or a missing key with no `--html`/`--no-html` flag, is a hard stop — see Surface.
- **Phase 3 skipped entirely**, even when `planner.html` is true. No open discussion; proceed from Phase 2 directly to Phase 4 finalization.
- **Never open a browser, never spot-check.** With `planner.html` true, Phase 2c still writes the files and renders `plan.html`, and Phase 2d is reduced to announcing its absolute path on a single line — no Playwright, no auto-open. With `planner.html` false, no HTML is produced at all.
- **Phase 4 Next Move is emitted as output text**, never as a question.

Standard and Quick modes are unchanged. `--headless` is the only mode that skips Phase 3 while `planner.html` is true; with `planner.html` false no mode has a Phase 3.

## Phase 1 — Decision Extraction

Phase 1 requires `.liang/project.yaml`. Resolve the surface first (see Surface: `planner.html`): run the shared first-run interview when the file is missing, ask the one question and write it back when only the key is missing, hard-stop in headless mode. The gates below are the standard-mode gates; Quick and Headless override them.

### 1a. Confirm intent

State what the skill will do and confirm the user wants to proceed.

### 1b. Adaptive Socratic Gap-Fill (only if needed)

If the conversation contains a `liang-brainstorm-relentless` Strategy Report (locked-decision table, Main Quest / Victory Conditions / Scope / Risks / Fog of War headings), **skip this**.

Otherwise, identify which Decision Summary fields are missing or under-specified and ask 2–5 focused questions covering only the gaps, batched into a single question round where possible.

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

## Phase 2 — Decomposition and Plan Files

2a runs in every mode and every surface. 2b runs only when `planner.html` is true. 2c has two forms, one per surface. 2d runs only when `planner.html` is true, and is reduced to a path announcement in headless mode.

### 2a. Decompose into quests (in memory)

Identify cohesive, independently-verifiable outcomes. Merge items sharing an outcome; split where one outcome must land before another can be planned. Order by dependency topology. Target 2–8 quests driven by meaningful decomposition, not a target count.

For each quest: title, purpose, numbered steps, code blocks where applicable, dependencies, victory conditions, risks, **difficulty**.

Include code blocks when a quest writes or modifies a file, specifies a structured data format (YAML/JSON), or has a concrete "write this content here" action. Skip them for purely organizational or subjective work. When in doubt, include — over-specifying beats under-specifying for downstream executors.

**Code-block style.** When a code block is Unreal Engine C++ — the detection rule heads `liang-quest-core/references/code-style/ue-cpp.md` — compose it per that contract (canonical). The contract binds the planner's own drafting here, the quest files it writes, the body-drafter brief (2c), and Phase 3 markdown edits.

**Manual-step isolation.** Manual-ness is step-level, but `manual: true` is quest-level and blocks every transitive dependent in a headless sweep. Before flagging a quest manual, check whether its automatable steps (file writes, scene duplication, config wiring) can split into their own auto quest so only the genuinely human steps (in-editor iteration, feel checks, visual judgment) carry the flag. A single manual step buried in an otherwise-auto quest turns the whole downstream chain into human-in-the-loop.

**Provenance-sensitive artifacts.** When reordering around a manual quest (or any late-scheduled quest), check whether downstream quests depend on the quest's *artifact* or on *when it was produced*. Baselines, golden files, and recorded fixtures are provenance-sensitive: a regression baseline captured after the refactor it guards compares the new code against itself and blesses any regression. If such a capture must move later in the chain, the quest must pin it to a commit — capture on a checkout of the pre-change anchor commit, record the hash — or the verification it feeds becomes circular.

**Fact verification.** Every workspace fact a quest asserts is checked against the workspace before the quest is written: counts ("24 racks in one row"), paths and depot state ("`p4 edit` these files"), regexes and the names they must match, measured values (spans, pitches, sizes), file layouts and top-level keys, the existence and signature of functions a step calls. Check by reading — open the file, grep, list the directory, run the VCS query, load the JSON and measure — never by recalling a number from the conversation or a memory note. Record each check in `plan.md` Campaign Notes under `Verified facts` as `fact — how checked`. A fact that cannot be checked from this machine (it lives on another host, or needs a tool that is not here) is written into the step as `assumed: <fact>` so the execute-child knows to verify it first and report a `plan_contradictions` entry rather than build on it. The executor's re-plan path exists for what slips through; it is not a substitute for checking. Unverified numbers in a plan were the cause of every mid-run escalation this rule replaces.

**Difficulty classification.** Tag each quest `easy`, `medium`, or `hard` based on what an executor will actually face. Downstream executors route to different models per `.liang/project.yaml`'s `execution_by_difficulty` mapping, so the field is load-bearing — get it roughly right rather than perfectly right.

Criteria and tie-break rule: `liang-quest-core/references/campaign/difficulty-guide.md` (canonical).

**Decide on a plan visual.** Resolve the policy first: a `--no-visual` flag on the invocation (same convention as `--quick`) forces none, `--visual` forces inclusion; otherwise read `planner.visual` from `.liang/project.yaml` (`auto` when the key is absent): `never` → skip, `always` → include the best-fit type, `auto` → classify per `references/html-design-contract.md` §10 by what the campaign's **main deliverable** is — **UI wireframe** (screens, panels, forms, editor tools, dashboards), **flow/state diagram** (pipelines, subsystems talking, state machines, ability lifecycles, branching logic), **sequence timeline** (behavior over time: animation, camera moves, travel, handshakes, turn phases), or **none** (backend, refactors, migrations, library/API, build/CI). With `planner.html` false there is no page to carry a visual: skip the decision, write no recipe, and omit the Visual line from `plan.md`. Otherwise, include a visual only when it earns its place; **when ambiguous, skip** — adding one in Phase 3 is cheap, removing noise from every plan is not. The plan's own quest dependency ordering is never a trigger (§10). If a visual is planned, write a one-line **visual recipe** naming the type + kit primitives (e.g., "timeline: camera + token tracks over 8 ticks, traveling token, beat strip for confirm→travel→arrive") — 2c records it as `plan.md`'s Visual line, which is where the body subagent reads it. Announce the decision in one sentence either way.

### 2b. Pick an aesthetic direction (`planner.html` true only)

With `planner.html` false there is no page and no skin to pick — skip to 2c.

Read `references/html-design-contract.md` for the catalog. Auto-pick based on the Planning Lens (e.g., *Skill Creation + Pipeline Architecture* → FF-gold or Xenoblade-cosmic; *Narrative + Dialogue* → Persona-blue or Octopath-watercolor; *Profiling + Observability* → NieR-monochrome). A direction supplied by the invoker (a saga's `skin`) wins over the auto-pick. Default to FF-gold when ambiguous. Announce the choice in one sentence and proceed — no question round here. The user can request a different direction during Phase 3 discussion.

### 2c — `planner.html` true: write the files, then render

The files land first; the page is rendered from them. `plan.html` is assembled from three fixed layers — no per-run CSS regeneration, and no model re-types CSS as output in any standard path.

1. **Write `plan.md` and the quest files.** Resolve/create the campaign folder, then write `plan.md` from `references/plan-template.md` and every quest file from `references/quest-template.md` (naming and content rules in Phase 4). `plan.md` carries the "why", the quest files carry the "how"; victory conditions are the only text that appears in both. `manifest.yaml` does **not** land here — it is Phase 4's only write.
2. **Brief the body-drafter subagent to draft the body.** Resolve the drafter model from `.liang/project.yaml` by the `models.body_drafter` chain — model-ID harnesses and tier-alias harnesses each have their own, and an unspawnable step is skipped — exactly as defined in `liang-quest-core/references/project/project-yaml.md` § Model Routing Extensions. Announce the resolved drafter model in one line — naming any step skipped as unspawnable — before spawning. Spawn a general-purpose subagent with the resolved model whose prompt contains **file paths, not transcribed content**: the absolute paths of `plan.md` and every quest file, with the instruction to read them from disk and transcribe them — the Decision Summary is `plan.md`'s Decision Summary section, the quest content is its Quests section plus the quest files, and the visual recipe (when present) is `plan.md`'s Visual line, which the subagent renders and never designs. The prompt also carries the full text of `references/templates/class-contract.md`, plus the full text of `liang-quest-core/references/code-style/ue-cpp.md` whenever any planned code block is UE C++. The subagent writes **body-only HTML** — the content inside `<div class="page">`, masthead through page-footer; no document shell, no `<style>` block, no inline CSS beyond the whitelisted custom properties (step 3) — to `_body.html` inside the campaign folder. Code blocks wrap tokens in §9 span classes; all user-derived content is HTML-escaped.
3. **Assemble + validate via script.** Run:
   `python references/templates/assemble_plan.py <campaign>/_body.html <skin-slug> <campaign>/plan.html --title "<Campaign Title>"`
   Resolve the skin slug from the direction name: lowercase-hyphenated, e.g. *NieR-monochrome* → `nier-monochrome`. The script structurally validates the body (TOC anchors ↔ section IDs bidirectionally, required skeleton classes, difficulty badges in TOC and quest headers, no `<style>`/`<script>`/`<link>`/document-shell tags, no inline styles beyond the whitelisted custom props (`--mock-cols`, `--tl-cols`, `--tl-start`, `--tl-span`), no external assets, at most one plan-visual section), then inlines `base.css` + `skin-<slug>.css` (+ the matching visual kit automatically — `mockup.css` for `ui-mock-section`, `diagram.css` for `diagram-section`, `timeline.css` for `timeline-section`) into one `<style>` block, in that order, and writes the single self-contained `plan.html`. The `.css` files never ship beside the output.
4. **On validation failure** (exit 1, `VALIDATION:` lines on stderr), send the violations back to the same subagent to fix, then re-run the script. After 2 failed retries, the planner writes the body itself and re-runs the script.
5. **On success, delete `_body.html`** — the campaign folder layout is fixed and flat (`plan.md`, `plan.html`, the quest files, and later `manifest.yaml` only).

**Division of labor is fixed.** The planner decides all content in 2a/2b (decomposition, difficulty, visual recipe, aesthetic direction) and records it in `plan.md` + the quest files; the body-drafter subagent only transcribes those files into the contractual skeleton; the script owns CSS assembly and structural validation.

**Fallbacks.** If subagent spawning is unavailable, the planner drafts the body itself from the same files (same body-only contract) and still assembles via the script. If Python is unavailable, fall back to manual assembly as a last resort: read `base.css` + the skin (+ the matching visual kit if the body has a plan-visual section), inline them verbatim into one `<style>` block, and perform the script's structural checks by hand.

**Code blocks must include CSS-only syntax highlighting** per the token-class taxonomy in `references/html-design-contract.md` §9. The token rules live in `base.css`; the palette variables live in the skin. The body generator wraps tokens in `<span>` classes but never generates the CSS rules themselves — they are already in `base.css` and the skin.

Every rendered `plan.html` must contain:
- Hero / masthead: campaign title, slug, date, quest count, planning lens
- Anchor-linked TOC of all quests (anchors must target valid section IDs) — each entry shows the quest's **difficulty badge**
- *(only when Phase 2a planned a visual)* at most one plan-visual section between the TOC and the first quest — `ui-mock-section` UI wireframe, `diagram-section` flow/state diagram, or `timeline-section` sequence timeline — with inline numbered badges + a legend (§10)
- Per-quest sections: title, purpose (1–2 sentences), **difficulty badge**, numbered steps, code blocks with file path labels and syntax highlighting, brief rationale (1–2 sentences), Dependencies + Victory Conditions in a footer strip
- Campaign notes (risks, open questions carried from the Decision Summary)
- Footer with generator attribution + timestamp

### 2c — `planner.html` false: show the quest table

No files land here, and no HTML is produced. Show the user, in chat:

1. The Decision Summary (already shown in 1c — repeat it only when quick or headless mode suppressed that gate).
2. A compact quest table: number, title, difficulty, MANUAL flag, depends-on, one-line purpose.

Then go straight to Phase 4. 2d and Phase 3 do not run.

### 2d. Visual spot-check + auto-open (`planner.html` true, not headless)

After confirming the `plan.html` write succeeded (per `references/html-design-contract.md` §4.4):

1. **Run the Visual Spot-Check** per §4.4 — Playwright screenshot at 375px viewport width only, sampling the longest-content quest, the shortest-content quest, the decisions table, and the plan-visual section when present. `base.css` + every skin have been pre-audited; only content-driven breaks remain. Fix any layout issue surfaced — in `plan.md` or the quest file when the cause is content, then re-render — before showing the user. Skip the screenshot loop silently if Playwright is unavailable. Skipped in headless mode.
2. **Auto-open** `plan.html` in the user's default browser. Do not ask first; do not offer the in-chat-only path. Skipped in headless mode. Per-OS commands:
   - Windows: `cmd //c start "" "<absolute-path>"` (the double-slash escapes `/c` for Git-Bash/MSYS shells)
   - macOS: `open "<absolute-path>"`
   - Linux: `xdg-open "<absolute-path>"`

After the open command runs, announce the absolute path in-chat on a single line so the user can re-open it later. If the open command fails (non-zero exit, no browser handler), announce the path and ask the user to open it manually — do not retry blindly. In headless mode, announce the absolute path and nothing else.

## Phase 3 — Open Discussion (`planner.html` true only)

Runs only when `planner.html` resolved true and the mode is not headless. With `planner.html` false there is no page to discuss against — 2c goes straight to Phase 4. Headless mode skips this phase whatever the surface — see Headless Mode.

User leads. No forced walkthrough or section-by-section review. Proceed to Phase 4 when the user signals readiness ("looks good," "write the quests," "proceed").

**The markdown is the source; the page is a render of it.** For each user turn that produces an agreed change to a quest, decision, victory condition, or any other plan element:

1. **Edit the markdown.** Use the Edit tool on `plan.md` and/or the affected quest file(s). These are planner-authored markdown — no read-before-edit ceremony beyond the Edit tool's own rules. Keep the two consistent: dependencies and victory conditions must agree across `plan.md` and the quest file (difficulty and the MANUAL flag live in `plan.md` only until the manifest is written). UE C++ code blocks edited or added during discussion follow the same code-style contract as Phase 2a.
2. **Re-render once**, whole, through 2c's body-drafter + `assemble_plan.py`. The drafter re-reads the changed files from disk. Never edit `plan.html` in place; every render is a full regeneration from what is on disk.
3. **Announce in one line**: "updated `<files>`, plan.html re-rendered, refresh browser".

One re-render per user turn that changed something — batch the turn's edits, then render once. Chat-only turns (clarifying questions, acknowledgments, anything the user does not agree should land) change nothing and render nothing.

An aesthetic swap is a skin-slug change plus a re-render; nothing in `plan.md` or the quest files moves.

## Phase 4 — Finalization

Reached when the user signals ready, or immediately from 2c when `planner.html` is false, or immediately from 2d in headless mode. What lands here depends on the surface:

- **`planner.html` true** — `plan.md` and the quest files are already on disk from 2c. Confirm they match the final in-memory plan; if a last change slipped in, apply it and re-render once per Phase 3. Then write `manifest.yaml` — the only Phase 4 write.
- **`planner.html` false** — nothing has landed yet. Write `plan.md`, then the quest files, then `manifest.yaml`, in that order, as one atomic sequence.

`plan.md` follows `references/plan-template.md`. Quest files follow `references/quest-template.md` and the naming convention `quest-NNN-<name>.md` (3-digit zero-padded number, lowercase-hyphenated slug from quest title, ~40 char max at word boundary).

Manifest follows the canonical schema in `liang-quest-core/references/campaign/manifest-schema.md` (worked example: `references/manifest-example.yaml`) — includes `schema_version: 4` (campaign manifest schema; distinct from `.liang/project.yaml`'s `schema_version: 1`), `q001`, `q002`, ... IDs, `status: "ready"` at creation, `depends_on` is a list of quest IDs, **`difficulty` is `"easy"`, `"medium"`, or `"hard"`** (per the classification in Phase 2a). Downstream executors consume `difficulty` to route the quest to the right model per `.liang/project.yaml`'s `execution_by_difficulty` mapping — do not omit the field.

For every human-in-editor quest (the ones labeled MANUAL in `plan.md`), also write **`manual: true`** on the quest entry. The batch sweep orchestrator uses it to hold the quest out of headless dispatch instead of failing the campaign; omitting it means an unattended sweep hands editor work to a headless child. Automated quests omit the field entirely. Before writing the flag, re-check Phase 2a's manual-step isolation rule: if a manual quest still contains automatable steps, split it now rather than block its dependents.

Quest markdown rules:
- Include only Purpose, Steps/code blocks, Dependencies, and Victory Conditions.
- Code blocks start with a file path comment (`// file: path/to/file` or `# file: path/to/file`).
- No tutorial prose, rationale, or "why" explanations.

`plan.md` rules:
- Include the Decision Summary, one block per quest (purpose, rationale, difficulty, MANUAL flag, depends-on, victory conditions, file name), and Campaign Notes.
- No steps and no code blocks — those live only in the quest files.
- Difficulty and the MANUAL flag live in `plan.md` and `manifest.yaml`, and the two must agree; the quest file carries neither (see `references/quest-template.md`).
- Victory conditions are repeated verbatim from the quest file so the dossier reads on its own. That overlap is deliberate and is the only one.

### Finalization sequence

1. Verify all content composed in memory. **Fact gate:** no quest is written with `status: "ready"` while a step still asserts a workspace fact that was neither checked (listed under `Verified facts`) nor marked `assumed:`. If Phase 3 edits introduced new facts, check them now.
2. Reuse the campaign folder created in 2c when `planner.html` is true. Otherwise compute/create `campaign-<YYYY-MM-DD>-<HHMM>-<slug>` now.
3. Write, in order: `plan.md` and the quest files (`planner.html` false only — with it true they already landed in 2c), then `manifest.yaml`.
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

Suggestion only. Do not invoke. This is the planner's final action; when an orchestrator invoked the planner, control returns to it.

## Boundaries

The non-obvious hard stops:

1. **One-shot quest writing.** Do not re-plan or update existing quest markdown files in subsequent invocations. (Phase 3 edits to `plan.md` and the quest files are not "re-planning" — they're discussion-mediated refinement within the run that created them, before `manifest.yaml` is written.)
2. **No execution.** Do not run code, install deps, or touch VCS beyond `vcs_artifacts` policy. Read-only inspection for fact verification (opening files, grep, directory listings, `p4 opened` / `p4 files` / `git ls-files`, loading a JSON or USD file to measure it) is not execution and is required by Phase 2a; anything that writes to the workspace is.
3. **No runtime enforcement.** Manifest status and dependency ordering are informational; executors own them.
4. **No secrets, .env, .git, credentials, dependency folders, build outputs, or large binaries** in any generated artifact.
5. **Never writes `plan.html` when `planner.html` is false.** Trust mode produces markdown only — no page, no `_body.html`, no browser.

## Relationship to Other Skills

- **Upstream**: `liang-brainstorm-relentless` (Strategy Report → Next Move); in-session conversation via explicit invocation; `liang-quest-saga-planner` — one handoff per campaign, `--quick` in its same-context loop or `--headless` in a batch subagent, with the Decision Summary arriving in the conversation or the brief
- **Body-drafting subagent** (`planner.html` true only): 2c and every Phase 3 re-render delegate body-only HTML drafting to a general-purpose body-drafter child, which reads `plan.md` and the quest files **from disk** and transcribes them. Its model resolves per `liang-quest-core/references/project/project-yaml.md` § Model Routing Extensions; `references/templates/assemble_plan.py` validates the body and assembles the CSS layers. The planner falls back to drafting the body itself if subagent spawning is unavailable
- **Downstream**: `liang-quest-executor` — the planner-native single-context runner. Sole supported executor for planner output.
- **Shared foundation**: `liang-quest-core` — shared protocol, manifest schema, status transitions, run report.
- **Opt-in from**: `liang-brainstorm-quick` — one of the two same-session downstreams lite offers at finalization (the other is a delegated executor for direct execution). Lite emits no files; this planner reads decisions directly from the live conversation.

## Reference Files

Read before generating, in every run:
- `references/plan-template.md` — `plan.md` dossier skeleton. `plan.md` is required whatever the surface.
- `references/quest-template.md` — quest markdown skeleton
- `references/manifest-example.yaml` — manifest schema example
- `liang-quest-core/references/code-style/ue-cpp.md` — UE C++ code-block style contract; applies whenever planned code is UE C++ (any project, no opt-in)
- `liang-quest-core/references/campaign/difficulty-guide.md` — difficulty criteria and tie-break rule (Phase 2)
- `liang-quest-core/references/campaign/protocol.md` — canonical campaign folder tree and lifecycle
- `liang-quest-core/references/campaign/manifest-schema.md` — canonical manifest schema, including `manual` and the validation rules
- `liang-quest-core/references/project/project-yaml.md` — first-run interview, `planner.html`, body-drafter model chain, VCS artifact policy

If a listed core file is missing, stop and report it.

`planner.html` true only — the render contract:
- `references/html-design-contract.md` — quality contract, eight-direction catalog, CSS guardrails, assembly protocol. **Read before every render.**
- `references/templates/class-contract.md` — fixed body structure + CSS variable interface. The single source of truth for class names, HTML skeleton, and the skin variable contract.
- `references/templates/base.css` — shared structure + all 14 pitfall fixes (§5.1–5.14). Read verbatim at generation time; contains zero hardcoded colors.
- `references/templates/skin-<name>.css` — per-direction palette + motif. Naming convention: `skin-` + lowercase-hyphenated direction slug.
- `references/templates/mockup.css` / `diagram.css` / `timeline.css` — the three conditional plan-visual kits (Layer 4): UI wireframe, flow/state diagram, sequence timeline. Auto-included by `assemble_plan.py` (at most one per plan) when the body contains the matching section class; zero hardcoded colors, consume the skin variables; CSS-only animation with reduced-motion/print fallbacks.
- `references/templates/assemble_plan.py` — deterministic assembler: structurally validates the body (including at most one plan-visual section), inlines `base.css` + skin (+ the matching visual kit when present), writes the self-contained `plan.html`. Always run this instead of inlining CSS by hand.
