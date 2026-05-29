---
name: liang-quest-planner
description: "Same-context campaign planner that consumes brainstorm output, in-session conversation, or both. Extracts locked decisions, fills gaps via adaptive Socratic questioning, generates a free-design HTML plan (delegating to frontend-design when available), runs open discussion, and writes lean quest markdown files. Four phases: decision extraction (with optional gap-fill), HTML generation, open discussion, quest markdown writing."
---

# Liang Quest Planner

Same-context, one-shot campaign planner. Consume decisions from the live conversation, produce a free-design HTML plan and lean quest markdown files. Stops at planning artifacts — never executes.

## Core Contract

- **Same-context only.** Reads the live conversation (brainstorm Strategy Report, lite session output, or general chat). Does not accept file paths or read saved brainstorms. Downstream execution flows through `liang-quest-executor` (the planner-native single-context runner).
- **Four phases in order**: (1) decision extraction with optional gap-fill, (2) HTML generation, (3) open discussion, (4) quest markdown writing.
- **HTML is editable during Phase 3.** Discussion updates land in `plan.html` (edit-in-place by default, full regen on structural changes). User refreshes browser manually to see changes.
- **Discussion is user-led.** No forced walkthrough.
- **Quest markdowns + manifest land only at Phase 4 finalization.** Never written during open discussion.
- **Quest markdowns are "do" docs**: steps + code blocks only, no prose. HTML is the "why" doc.
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
3. After `liang-brainstorm-quick` when the user picks the "Plan first" downstream at lite's Next Move (lite presents this skill and an in-session sonnet subagent as equal alternatives — Recommended biases by scope-creep signals)
4. From general conversation when explicitly invoked — runs Adaptive Socratic Gap-Fill first

Do not silently activate from generic intent like "plan this." If unclear, ask.

**Quick Mode** activates when the user appends `--quick` (e.g., `skill:liang-quest-planner --quick`) or prefixes with `quick:`. See the Quick Mode section below for the overrides it applies.

## Quick Mode

Opt-in path for fast planning when you'd rather iterate against the HTML than gate-walk through brainstorming. Overrides the standard flow:

- **Skip intent confirmation** (Phase 1a).
- **Gap-Fill cap: 2 questions** (down from 5). After that, missing fields stay `unspecified` and the planner proceeds. No graceful exit to `liang-brainstorm-relentless` — quick mode opts you into "plan from what I gave you."
- **Skip the Decision Summary sanity-check gate** (Phase 1c). Display the summary inline, proceed immediately to Phase 2.
- **Assemble layers** (Phase 2c). Render the fixed body per `class-contract.md`, read `base.css` + the chosen `skin-*.css` (+ `mockup.css` if the campaign is UI-bearing), inline them into one `<style>` block. Still skip the `frontend-design:frontend-design` delegation — the planner owns the structure it writes, so it can edit faithfully during Phase 3.

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

- **`easy`** — single-file edit, mechanical change, no new abstractions, no cross-system reasoning. Examples: rename a symbol, add a UPROPERTY, swap a literal, write a known struct definition, update a config value.
- **`medium`** — multi-file change, introduces or modifies an abstraction (struct, helper, interface), or requires understanding the call topology of a small subsystem. Examples: refactor a data structure with its call sites, add a new BlueprintNativeEvent and wire it through, restructure a private map's invariants.
- **`hard`** — cross-system reasoning, new architecture, ambiguous integration boundary, or significant verification work. Examples: introduce a new subsystem, redesign a replication boundary, integrate two previously-isolated systems, end-to-end verification quest covering build + playtest + intel.

When in doubt between two levels, pick the higher one — under-classifying routes a quest to a model that may fumble it; over-classifying just spends slightly more on a model that handles it cleanly.

**Decide on a UI wireframe.** Detect whether the campaign is UI-bearing per `references/html-design-contract.md` §10.1 (editor tools, panels, app screens, dashboards, HUDs, forms, CLIs with structured output — *not* backend, data, refactor, or library work). If it is, plan a single skin-matched **UI Layout Wireframe** composed from the `mockup.css` kit, to sit between the TOC and the first quest. Announce the choice in one sentence. When ambiguous, lean toward including a lightweight mockup.

### 2b. Pick an aesthetic direction

Read `references/html-design-contract.md` for the catalog. Auto-pick based on the Planning Lens (e.g., *Skill Creation + Pipeline Architecture* → FF-gold or Xenoblade-cosmic; *Narrative + Dialogue* → Persona-blue or Octopath-watercolor; *Profiling + Observability* → NieR-monochrome). Default to FF-gold when ambiguous. Announce the choice in one sentence and proceed — no question round here. The user can request a different direction during Phase 3 discussion.

### 2c. Assemble the HTML (layered)

The planner assembles `plan.html` from three fixed layers — no per-run CSS regeneration.

1. **Render the fixed-body HTML** per `references/templates/class-contract.md` — the variable per-campaign content (masthead, TOC, quest sections, notes, footer). The HTML structure and class names are identical regardless of which aesthetic direction is chosen. No `<style>` block, no inline CSS, no palette selection in the body markup. For UI-bearing campaigns (per 2a / §10), also render the one `ui-mock-section` between the TOC and `<main class="quests">`, composed from the `mockup.css` primitives the UI needs.
2. **Read the CSS layers** — `references/templates/base.css` (all structure + all 14 pitfall fixes, zero hardcoded colors) and `references/templates/skin-<direction>.css` (the `:root` variable block + motif rules for the chosen direction). Resolve the skin filename from the direction name: lowercase-hyphenated, e.g. *NieR-monochrome* → `skin-nier-monochrome.css`. **If a wireframe is present**, also read `references/templates/mockup.css` (zero hardcoded colors; consumes the skin variables).
3. **Inline into one `<style>` block** — `base.css` first, then the skin, then `mockup.css` **only if** a wireframe was composed. The CSS cascade is deliberate: skins override nothing structural, only variables and optional motif rules; `mockup.css` adds only wireframe classes driven by the same skin variables.
4. **Write the single self-contained `plan.html`** to the campaign folder. The contract's `self_contained` and `no_external_deps` clauses are satisfied by inlining; the `.css` files never ship beside the output.

**Delegation scope (optional).** If `frontend-design:frontend-design` is available, it may be invoked **only** for body-content generation — generating the fixed-structure HTML skeleton per `class-contract.md`. CSS is never delegated; the planner always reads and inlines `base.css` + the chosen skin itself. If `frontend-design` is unavailable or fails, the planner generates the body inline.

**Code blocks must include CSS-only syntax highlighting** per the token-class taxonomy in `references/html-design-contract.md` §9. The token rules live in `base.css`; the palette variables live in the skin. The planner wraps tokens in `<span>` classes but never generates the CSS rules themselves — they are already in `base.css` and the skin.

Every `plan.html` must contain:
- Hero / masthead: campaign title, slug, date, quest count, planning lens
- Anchor-linked TOC of all quests (anchors must target valid section IDs) — each entry shows the quest's **difficulty badge**
- *(UI-bearing campaigns only)* one `ui-mock-section` UI Layout Wireframe between the TOC and the first quest, with inline numbered badges + a legend (§10)
- Per-quest sections: title, purpose (1–2 sentences), **difficulty badge**, numbered steps, code blocks with file path labels and syntax highlighting, brief rationale (1–2 sentences), Dependencies + Victory Conditions in a footer strip
- Campaign notes (risks, open questions carried from the Decision Summary)
- Footer with generator attribution + timestamp

### 2d. Visual spot-check + auto-open

After confirming the file write succeeded (per `references/html-design-contract.md` §4.4):

1. **Run the Visual Spot-Check** per §4.4 — Playwright screenshot at 375px viewport width only, sampling the longest-content quest, the shortest-content quest, and the decisions table. `base.css` + every skin have been pre-audited; only content-driven breaks remain. Fix any layout issue surfaced in-place before showing the user. Skip the screenshot loop silently if Playwright is unavailable.
2. **Auto-open** `plan.html` in the user's default browser. Do not ask first; do not offer the in-chat-only path. Per-OS commands:
   - Windows: `cmd //c start "" "<absolute-path>"` (the double-slash escapes `/c` for Git-Bash/MSYS shells)
   - macOS: `open "<absolute-path>"`
   - Linux: `xdg-open "<absolute-path>"`

After the open command runs, announce the absolute path in-chat on a single line so the user can re-open it later. If the open command fails (non-zero exit, no browser handler), announce the path and ask the user to open it manually — do not retry blindly.

## Phase 3 — Open Discussion

User leads. No forced walkthrough or section-by-section review. Proceed to Phase 4 when the user signals readiness ("looks good," "write the quests," "proceed").

When discussion produces a substantive change to a quest, decision, victory condition, or other plan element, **update `plan.html` on disk to reflect it**:

- **Edit-in-place** (default) — use the Edit tool to modify only the affected section. Fast turns, preserves overall structure, preserves anchor IDs (the TOC's contract with the body). Preserve HTML escaping for all user-derived content.
- **Full regen** — rewrite the whole file when the change is structural (re-decomposition, quest count change, aesthetic swap, sweeping rationale rewrite). Slower but always self-consistent.
- The model picks based on change size. When uncertain, prefer edit-in-place — drift across small edits is recoverable; an unnecessary full regen burns generation cost.

After updating, announce in-chat what changed in one line ("Updated quest 3 victory conditions — refresh browser to see") so the user knows to refresh.

Cosmetic chat (clarifying questions, acknowledgments) does not trigger updates — only changes the user agrees should land in the plan.

## Phase 4 — Quest Markdown Writing

When the user signals ready, write all artifacts atomically.

Quest files follow `references/quest-template.md` and the naming convention `quest-NNN-<name>.md` (3-digit zero-padded number, lowercase-hyphenated slug from quest title, ~40 char max at word boundary).

Manifest follows `references/manifest-example.yaml` — `q001`, `q002`, ... IDs, `status: "ready"` at creation, `depends_on` is a list of quest IDs, **`difficulty` is `"easy"`, `"medium"`, or `"hard"`** (per the classification in Phase 2a). Downstream executors consume `difficulty` to route the quest to the right model per `.liang/project.yaml`'s `execution_by_difficulty` mapping — do not omit the field.

Quest markdown rules:
- Steps + code blocks only. No tutorial prose, rationale, or "why."
- Code blocks start with a file path comment (`// file: path/to/file` or `# file: path/to/file`)
- Victory conditions as a checklist

### Finalization sequence

1. Verify all content composed in memory
2. Compute campaign slug from Main Quest title (lowercase, hyphenated, ≤50 chars at word boundary), then prefix it with the local generation timestamp `<YYYY-MM-DD>-<HHMM>` (24-hour clock). Full directory name: `campaign-<YYYY-MM-DD>-<HHMM>-<slug>`.
3. Create `.liang/campaigns/campaign-<YYYY-MM-DD>-<HHMM>-<slug>/`. The date+time prefix makes same-day collisions almost impossible; on the rare exact-minute + identical-slug clash, suffix `-2`, `-3`, etc.
4. Write quest files, then `manifest.yaml` (`plan.html` already landed in Phase 2)
5. If any write fails partway, abort and report which paths landed and which didn't
6. Tell the user the saved path

### VCS policy

Read `vcs_artifacts.planning` from `.liang/project.yaml`:
- `"ignore"` — apply VCS ignore rules silently
- `"commit"` — leave trackable, suggest adding to VCS
- `"ask"` (or absent) — ask the user; write the choice back to `project.yaml`

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
- **Soft delegation (optional)**: `frontend-design:frontend-design` may be invoked for body-content generation only (the fixed HTML skeleton per `class-contract.md`). CSS assembly is never delegated — the planner always reads and inlines `base.css` + the chosen skin itself. Fall back to inline body generation if unavailable
- **Downstream**: `liang-quest-executor` — the planner-native single-context runner. Sole supported executor for planner output.
- **Shared foundation**: `liang-quest-core` — shared protocol, manifest schema, status transitions, run report.
- **Opt-in from**: `liang-brainstorm-quick` — one of the two same-session downstreams lite offers at finalization (the other is an in-session sonnet subagent for direct execution). Lite emits no files; this planner reads decisions directly from the live conversation.

## Reference Files

Read before generating:
- `references/html-design-contract.md` — quality contract, eight-direction catalog, CSS guardrails, assembly protocol. **Read before every HTML generation.**
- `references/templates/class-contract.md` — fixed body structure + CSS variable interface. The single source of truth for class names, HTML skeleton, and the skin variable contract.
- `references/templates/base.css` — shared structure + all 14 pitfall fixes (§5.1–5.14). Read verbatim at generation time; contains zero hardcoded colors.
- `references/templates/skin-<name>.css` — per-direction palette + motif. Naming convention: `skin-` + lowercase-hyphenated direction slug.
- `references/templates/mockup.css` — generic UI-wireframe kit (conditional Layer 4). Read only when composing a wireframe for a UI-bearing campaign (§10); zero hardcoded colors, consumes the skin variables.
- `references/quest-template.md` — quest markdown skeleton
- `references/manifest-example.yaml` — manifest schema example
