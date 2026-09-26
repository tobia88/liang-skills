# Recon Stage Briefs

Canonical worker instructions for every recon role, harness-neutral. `{PLACEHOLDERS}` are supplied by the orchestrator at dispatch time. The bundled workflow scripts (`wf-map-breakdown.js`, `wf-compare-verify.js`) embed this same text for briefs 1–9 — when editing one of those here, mirror the change in the scripts. Brief 10 (lite profile) lives only here.

Placeholders used throughout: `{PROTO}` prototype path · `{PREV}` prior-version path · `{OUT}` output folder · `{PROJECT_CONTEXT}` 1–2 paragraphs describing the project and what the prototype is · `{SOURCE_CONTEXT}` source roots, module layout, naming conventions · `{SCOPE_RULE}` what is in/out of comparison scope and when `oos-native` applies · `{LOCKED_DECISIONS}` authoritative decisions with the divergent-never-missing rule · `{HINTS}` prior-knowledge hints, always framed as unverified claims · `{RANGES}` a system's line ranges · `{FEATURES}` a system's numbered checklist · `{ERRORS}` a skeptic's error list.

**Common rules (append to every brief):** the Read tool may render UTF-8 punctuation as mojibake — write proper punctuation, never transcribe mojibake bytes. Read the prototype only in slices of ≤ 1500 lines via offset/limit; never the whole file; never excluded ranges. Explicit adult prose is summarized mechanics-only, never reproduced. Base64/data-URI lines are never read.

---

## 1. Mapper (stage 1)

You produce the definitive CHUNK MAP of `{PROTO}`. Every downstream worker reads only the ranges you assign — an error here poisons the pipeline. `{PROJECT_CONTEXT}`

1. Establish the authoritative line count yourself (count lines, cross-check by reading the file tail). The orchestrator's banner scan seed is a hint and may be wrong or incomplete: `{BANNER_SCAN}`.
2. Rescan for section banners in all comment styles; locate structural boundaries (style/script/markup blocks). Read the file at every boundary you claim — never trust banner-to-banner spans; unbannered drift between sections is common and must be attributed to the right system.
3. Locate base64/data-URI blob lines → excluded ("asset blob").
4. Known already-ported embedded subsystems: `{EXCLUDE_HINTS}`. Find their actual spans, read a few lines at each edge to verify, exclude them; only their bridge/seam code stays in scope as its own system.
5. Group everything in-scope into 12–20 systems (merge styling/markup fragments into the system they serve; split any system that would exceed ~3× the per-system average, at a real code seam).
6. `shared_core`: the load-bearing global spans every breakdown worker must also read (global state, key helpers, boot wiring). Hard cap 800 lines total.
7. Partition law: every line in exactly one bucket (system / shared_core / excluded, boilerplate → excluded); no overlaps; gaps > 20 lines listed in `uncovered` (target zero). Verify the partition arithmetically before returning.
8. Per system: kebab id, title, order (reading order: core/world first, then gameplay systems, then tooling, then boot), one-line purpose, ranges, depends_on best guesses.
9. Write `{OUT}/_chunkmap.json` per the artifact contract, then return the same data.

## 2. Delta scanner (stage 1, optional)

Structural delta `{PREV}` → `{PROTO}`. `{DELTA_CONTEXT}` — material existing only in the current version is the likeliest unported work; spotlight it. Method: banner-scan both files, align sections by title, use banner positions for size estimates, sample-read only new/grown sections (a few hundred lines total). Write `{OUT}/_delta-prev.md` per the artifact contract (≤ ~120 lines). Return: new_systems, grown, unchanged, md_path.

## 3. Breakdown worker (stage 2, one per system)

You own ONE system: `{TITLE}` (id `{ID}`), purpose `{PURPOSE}`, mapper's dependency guess `{DEPENDS}`. All system ids: `{SYSTEM_INDEX}`. `{PROJECT_CONTEXT}`

Read ONLY your ranges `{RANGES}` plus shared core `{SHARED_CORE}` in `{PROTO}`. If an identifier you need is defined elsewhere, grep the prototype for it with a few lines of context — never read other systems' sections wholesale. Never read excluded ranges `{EXCLUDED}`.

Write `{OUT}/{NN}-{ID}.md` exactly per the artifact contract's stage-2 template (frontmatter `status: breakdown`; sections What the prototype does / Data & formulas / UI presentation / Dependencies & integration points / Prototype-only / Open questions). Every claim carries a line ref; constants and formulas verbatim; bulk content data as schema + count + 2–3 representative rows.

Quality bar: this document is the ONLY thing later stages read about your system — the compare stage greps target source against your feature list, and a skeptic will re-read your cited prototype lines; one wrong line ref fails the document. Do NOT compare against target code and do NOT give porting advice — later stages own those.

Return: system, md_path, features (10–25 SHORT atomic capability names covering everything the system observably does — each will be individually assessed, so "stamina ticks down per road segment", not "travel works"), depends_on (refined from evidence), open_questions, warnings (anything that made your read unreliable).

## 4. Compare worker (stage 3, one per system)

`{PROJECT_CONTEXT}` `{SOURCE_CONTEXT}` `{SCOPE_RULE}` `{LOCKED_DECISIONS}` Hints for your system (unverified claims — verify against code, statuses may have drifted): `{HINTS}` `{DELTA_NOTE}`

Read first: your doc `{OUT}/{NN}-{ID}.md` (fully), your checklist `{FEATURES}`, and the delta doc if present. Then investigate the source roots with grep/read — class names, mechanic keywords, synonyms; open headers AND implementations before citing them. Judge by MECHANIC, not medium.

Append to the doc the stage-3 sections per the artifact contract: `## Current state` (orienting paragraph + full `| # | Feature | Status | Evidence | Note |` table, one row per checklist feature in order, six-status vocabulary, evidence rules), `## Missing` (gap clusters), `## Modify (divergent)` (both-sides citations, locked-decision flags). Flip frontmatter to `status: compared`. Do not modify stage-2 sections.

Return: system, status_counts (six integers summing to checklist length), table_rows (short label, status, evidence, note), notable (3–6 sentences a planner most needs), md_updated.

## 5. Skeptic (stage 4, one per system)

Try to FAIL the document `{OUT}/{NN}-{ID}.md`. Default to suspicion; it passes only if it survives three audits. Report only — edit nothing, with one exception where the profile allows worker edits: on a pass verdict, flip the doc's frontmatter to `status: verified` (see brief 7).

- **Audit A, breakdown fidelity** (vs `{PROTO}`, your system's ranges `{RANGES}`): sample ≥ 6 factual claims including ≥ 2 verbatim constants/formulas; read the cited lines; any fabricated/wrong/unverifiable ref = error kind `breakdown`.
- **Audit B, compare validity** (vs the source roots): re-open the citation of EVERY `done` row (cap 8, sampled across files) and confirm the cited code implements the feature, not merely exists. Independently re-search ≥ 2 `missing` rows with alternative names. Check locked-decision conflicts are `divergent` not `missing`, and `oos-native` rows are genuinely out-of-scope-native, not lazy searches. Wrong verdicts = error kind `compare`.
- **Audit C, coverage**: every checklist feature has exactly one table row, same order; stage-3 sections present; frontmatter `status: compared`. Gaps = error kind `coverage`.

Verdict `fail` on any must-fix error (default errors to must-fix unless cosmetic). Return: system, verdict, errors (kind + detail specific enough that a fixer can act without re-deriving), checks_done.

## 6. Fixer (stage 4, failed docs only)

A skeptic found these errors in `{OUT}/{NN}-{ID}.md`: `{ERRORS}`. For each: re-derive the truth yourself (read the prototype lines or grep/read the source) and correct the document — wrong line refs, wrong statuses, wrong citations, missing coverage rows. Corrections strengthen accuracy, never delete inconvenient claims wholesale; a wrong claim is replaced by the cited truth. Keep table/Missing/Modify sections mutually consistent. Touch nothing the errors do not implicate. Return: system, changes, md_updated.

## 7. Re-verifier (stage 4, after a fix)

Check ONLY that each error in `{ERRORS}` is now resolved in `{OUT}/{NN}-{ID}.md` (open the corrected lines/citations; for status changes confirm table + Missing + Modify agree). Edit nothing. Return: system, verdict (pass only if every listed error is resolved), errors (still-unresolved only), checks_done. On pass, the orchestrator (or the worker itself where the profile allows edits) flips frontmatter to `status: verified`; docs that passed the skeptic outright are flipped the same way.

## 8. Consistency checker (stage 5)

Read all system docs plus `_features.json`, `_chunkmap.json`, and the delta doc. Do not edit them; you write exactly one file. Mandates: (1) dependency symmetry across frontmatter and prose; (2) ownership — resolve every overlap candidate (start from the docs' own warnings and open questions) to a single owning doc, flag double-counts that would cause double-porting and orphans documented nowhere; (3) delta traceability — every delta "new" item maps to some doc's feature rows; (4) cross-resolve open questions answered by another doc's content; (5) status sanity — the same underlying mechanic must not carry contradicting statuses across docs. Write `{OUT}/_consistency.md` per the artifact contract (five sections, severities, doc/row references). Return: issues (severity, systems, detail), resolutions, md_path.

## 9. Synthesizer (stage 5, last)

Inputs: every system doc, `_consistency.md`, the delta doc, plus the orchestrator-supplied verify summary `{VERIFY_SUMMARY}` and consistency findings `{CONSISTENCY_ISSUES}`. Write `{OUT}/00-index.md` exactly per the artifact contract's six-section structure, with frontmatter `source_prototype: {PROTO}` and `profile: full` (overwrite a lite index if one is there); its consume section states the planner contract from the artifact contract, including that the folder is a frozen snapshot. Information-dense, ≤ ~250 lines, no filler, no campaign decomposition (downstream owns that). The counts in your status table come from the docs' current tables (post-fix), which are authoritative over any earlier in-band numbers. Return: md_path, headline (one sentence — the single most important fact about the gap), per_system (one status line each).

## 10. Lite synthesizer (lite profile only, replaces stages 3–5)

No workflow script embeds this brief — the orchestrator dispatches it as one worker after the stage-2 duties are done.

Inputs: every system doc in `{OUT}` (all at `status: breakdown`), `_features.json`, `_chunkmap.json`, and the delta doc if present. `{PROJECT_CONTEXT}` No codebase comparison was run and you run none: do not open the target source, do not use the status vocabulary (done/partial/missing/divergent/prototype-only/oos-native), and make no claim about what the codebase already contains. Edit no system doc; you write exactly one file.

Write `{OUT}/00-index.md` exactly per the artifact contract's lite index: frontmatter with `source_prototype: {PROTO}` and `profile: lite`, then the four lite sections — information-dense, ≤ ~150 lines, no filler, no campaign decomposition (downstream owns that). The system table's feature counts come from `_features.json`. In "Seams and open questions", resolve an open question yourself when another doc's content answers it, and say which doc. Return: md_path, headline (one sentence — the single most important fact about what the prototype contains), per_system (one line each).
