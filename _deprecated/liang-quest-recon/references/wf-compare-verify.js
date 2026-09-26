// liang-quest-recon — stage 3-5 workflow (Claude Code profile).
// Invoke AFTER assembling _features.json: Workflow({ scriptPath: "<this file>", args: {...} })
//
// args:
//   protoPath       (required) absolute path to the prototype file
//   outDir          (required) breakdown output folder (holds the NN-*.md docs)
//   projectContext  (required) 1-2 paragraphs: project + prototype description
//   sourceContext   (required) source roots, module layout, naming conventions for the compare search
//   scopeRule       (required) what is in/out of comparison scope and when 'oos-native' applies
//   lockedDecisions (required) authoritative decisions superseding the prototype ('none' if none)
//   systems         (required) [{ id, title, ranges, features:[...], hints }] assembled from _features.json
//                   (order = array order, must match the NN- file numbering)
//   hintsPreamble   (optional) framing for campaign hints (always: unverified claims, verify against code)
//   deltaNote       (optional) one paragraph pointing at the delta doc and what it implies
//   today           (optional) date string stamped into 00-index.md frontmatter
//   pipelineNote    (optional) run-identifier text for the index frontmatter
//   excludedSpans   (optional) the chunk map's excluded ranges, as text — workers never read them
//   models          (optional) { compare, verify, fix, cross, synthesis } — resolved by the orchestrator from
//                   project.yaml; an absent key means no model override (harness default)
//   efforts         (optional) { compare, verify, fix, cross, synthesis } — default high/high/medium/high/high
//
// Returns: { perSystem, lostSystems, consistencyIssues, consistencyPath, indexPath, headline, perSystemLines }.
// Keep this script's prompts in sync with references/stage-briefs.md.

export const meta = {
  name: 'recon-compare-verify',
  description: 'Recon stages 3-5: per-feature compare vs target source, skeptic verify + one fix round per doc, cross-doc consistency, 00-index.md synthesis',
  phases: [
    { title: 'Compare', detail: 'per-feature status vs target source' },
    { title: 'Verify', detail: 'skeptic audit of line refs + verdicts per doc' },
    { title: 'Fix', detail: 'revision round for failed docs + re-verify' },
    { title: 'Cross', detail: 'cross-doc consistency + 00-index.md synthesis' },
  ],
}

if (!args || !args.protoPath || !args.outDir || !args.projectContext || !args.sourceContext || !args.scopeRule || !args.lockedDecisions || !Array.isArray(args.systems) || !args.systems.length) {
  throw new Error('recon-compare-verify requires args: protoPath, outDir, projectContext, sourceContext, scopeRule, lockedDecisions, systems[] (plus optional excludedSpans, hintsPreamble, deltaNote, today, pipelineNote, models, efforts)')
}

const PROTO = args.protoPath
const OUT = args.outDir
const SYSTEMS = args.systems
const M = args.models || {}
// No default model lives here: an unresolved role is spawned without a model override (harness default).
const opt = (o, m) => (m ? { ...o, model: m } : o)
const E = Object.assign({ compare: 'high', verify: 'high', fix: 'medium', cross: 'high', synthesis: 'high' }, args.efforts || {})
const TODAY = args.today || 'unknown-date'

const VOCAB = `STATUS VOCABULARY (assign exactly one per feature):
- done: the target code substantially implements the mechanic (cite the core implementation file:line).
- partial: a counterpart exists but meaningful prototype behavior is absent (cite what exists; name what is absent).
- missing: no counterpart found after an honest search including alternative names/synonyms (note the searches you ran).
- divergent: a counterpart exists but deliberately differs (cite both sides; flag if it matches a locked decision).
- prototype-only: exists to serve the prototype medium itself (page chrome, local persistence, debug harness) and should not be ported.
- oos-native: the feature's natural home is a layer the scope rule excludes; not assessed — never use this as an escape hatch for a lazy search.
LOCKED-DECISION RULE: a feature conflicting with a locked decision is "divergent" with a locked-decision note, never "missing" — decisions supersede the prototype.
EVIDENCE RULES: every done/partial/divergent verdict cites at least one repo-relative path:line you actually opened — a skeptic will re-open every citation and fail the document on any citation that does not support its verdict. Judge by MECHANIC, not medium. Compare against the current on-disk state of the source. Where the code is ahead of the prototype, note it as "ahead", not a gap. Explicit prose in the prototype is assessed mechanics-only and never reproduced.`

// stage-briefs.md "Common rules (append to every brief)"
const COMMON = `COMMON RULES: the Read tool may render UTF-8 punctuation as mojibake — write proper punctuation, never transcribe mojibake bytes. Read the prototype only in slices of at most 1500 lines via offset/limit; never the whole file; never these excluded ranges: ${args.excludedSpans || '(none listed — see _chunkmap.json "excluded")'}. Explicit adult prose is summarized mechanics-only, never reproduced. Base64/data-URI lines are never read.`

const CTX = `${args.projectContext}

You are one stage of a multi-agent recon pipeline that turned the prototype ${PROTO} into per-system breakdown docs under ${OUT}, now being compared against the target codebase.

TARGET SOURCE: ${args.sourceContext}

SCOPE RULE: ${args.scopeRule}

LOCKED DECISIONS (authoritative over the prototype): ${args.lockedDecisions}

${VOCAB}

${COMMON}`

const HINTS_PRE = args.hintsPreamble || 'Hints below are UNVERIFIED CLAIMS from prior planning memory — verify every one against the code; recorded campaign statuses may have drifted in either direction.'
const DELTA_NOTE = args.deltaNote || ''

const CMP_SCHEMA = {
  type: 'object', required: ['system', 'status_counts', 'table_rows', 'notable', 'md_updated'],
  properties: {
    system: { type: 'string' },
    status_counts: { type: 'object', required: ['done', 'partial', 'missing', 'divergent', 'prototype_only', 'oos_native'], properties: {
      done: { type: 'integer' }, partial: { type: 'integer' }, missing: { type: 'integer' }, divergent: { type: 'integer' }, prototype_only: { type: 'integer' }, oos_native: { type: 'integer' } } },
    table_rows: { type: 'array', items: { type: 'object', required: ['feature', 'status', 'evidence'], properties: {
      feature: { type: 'string' }, status: { type: 'string', enum: ['done', 'partial', 'missing', 'divergent', 'prototype-only', 'oos-native'] }, evidence: { type: 'string' }, note: { type: 'string' } } } },
    notable: { type: 'array', items: { type: 'string' } },
    md_updated: { type: 'boolean' },
  },
}
const VER_SCHEMA = {
  type: 'object', required: ['system', 'verdict', 'errors', 'checks_done'],
  properties: {
    system: { type: 'string' },
    verdict: { type: 'string', enum: ['pass', 'fail'] },
    errors: { type: 'array', items: { type: 'object', required: ['kind', 'detail'], properties: {
      kind: { type: 'string', enum: ['breakdown', 'compare', 'coverage'] }, detail: { type: 'string' }, must_fix: { type: 'boolean' } } } },
    checks_done: { type: 'integer' },
  },
}
const FIX_SCHEMA = {
  type: 'object', required: ['system', 'changes', 'md_updated'],
  properties: { system: { type: 'string' }, changes: { type: 'array', items: { type: 'string' } }, md_updated: { type: 'boolean' } },
}
const CON_SCHEMA = {
  type: 'object', required: ['issues', 'md_path'],
  properties: {
    issues: { type: 'array', items: { type: 'object', required: ['severity', 'systems', 'detail'], properties: {
      severity: { type: 'string', enum: ['info', 'warn', 'error'] }, systems: { type: 'array', items: { type: 'string' } }, detail: { type: 'string' } } } },
    resolutions: { type: 'array', items: { type: 'string' } },
    md_path: { type: 'string' },
  },
}
const SYN_SCHEMA = {
  type: 'object', required: ['md_path', 'headline'],
  properties: { md_path: { type: 'string' }, headline: { type: 'string' }, per_system: { type: 'array', items: { type: 'object', properties: { system: { type: 'string' }, status_line: { type: 'string' } } } } },
}

function nn(i) { return String(i + 1).padStart(2, '0') }
function checklist(s) { return s.features.map((f, j) => (j + 1) + '. ' + f).join('\n') }

function comparePrompt(s, i) {
  const md = OUT + '/' + nn(i) + '-' + s.id + '.md'
  return `${CTX}

${HINTS_PRE}
Hints for YOUR system (${s.id}): ${s.hints || 'none recorded'}
${DELTA_NOTE}

You own the compare pass for system "${s.title}" (id: ${s.id}).

Read first: ${md} (fully — the verified breakdown doc for your system), and the delta doc under ${OUT} if present. Your EXACT assessment checklist (assess every feature, in this order, exactly one status each):
${checklist(s)}

Investigate the target source with grep/read — class names, mechanic keywords, synonyms; open headers AND implementations before citing them.

APPEND to ${md} (do not modify existing sections except the frontmatter status field):

## Current state
One orienting paragraph: which modules/classes cover this system and how far they go. Add a short "ahead of prototype" note where the code exceeds the prototype.
Then the full assessment table:
| # | Feature | Status | Evidence | Note |
One row per checklist feature, same order and numbering as above.

## Missing
The missing features grouped into coherent gap clusters a planner could turn into work items (bullets, reference row numbers).

## Modify (divergent)
One bullet per divergent feature: prototype behavior (with its existing line ref from the doc) vs code behavior (file:line), and whether it matches a locked decision.

Finally change the frontmatter "status: breakdown" line to "status: compared".

Return JSON: system, status_counts (six integers, must sum to the checklist length), table_rows (feature = shortened row label, status, evidence, note), notable (3-6 sentences: the findings a planner most needs), md_updated.`
}

function verifyPrompt(s, i) {
  const md = OUT + '/' + nn(i) + '-' + s.id + '.md'
  return `${CTX}

You are the SKEPTIC for system "${s.title}" (id: ${s.id}). Your job is to try to FAIL the document ${md}. Default to suspicion; it passes only if it survives all three audits. Edit nothing — with ONE exception: if your final verdict is pass, change the doc's frontmatter "status: compared" line to "status: verified" (your only permitted edit).

Audit A — breakdown fidelity (against the prototype ${PROTO}; this system's line ranges: ${s.ranges}):
Sample at least 6 factual claims from the doc's breakdown sections, including at least 2 verbatim constants/formulas from "Data & formulas". Read the cited prototype lines (offset/limit slices; never the whole file) and confirm each claim. Any fabricated, wrong, or unverifiable line ref = error kind "breakdown".

Audit B — compare validity (against the target source):
From the "Current state" table: re-open the citation of EVERY "done" row (cap 8 — if more, sample 8 across different files) and confirm the cited code actually implements the feature, not merely exists. Independently re-search at least 2 "missing" rows using alternative names/synonyms the compare agent may not have tried. Check that any feature conflicting with the locked decisions is marked divergent, not missing. Check "oos-native" rows are genuinely out-of-scope-native per the scope rule, not lazy searches. Wrong verdicts = error kind "compare".

Audit C — coverage:
Every feature in this checklist has exactly one table row, same order:
${checklist(s)}
The doc has Current state / Missing / Modify sections and frontmatter "status: compared". Gaps = error kind "coverage".

Verdict "fail" if any error with must_fix true (default must_fix to true unless the issue is cosmetic). Return JSON: system, verdict, errors (kind, detail — specific enough that a fixer can act without re-deriving: include the row/claim and what you found instead), checks_done (total individual checks performed).`
}

function fixPrompt(s, i, errors) {
  const md = OUT + '/' + nn(i) + '-' + s.id + '.md'
  return `${CTX}

You are the FIXER for the document ${md} (system "${s.title}"). A skeptic audited it and found these errors:
${JSON.stringify(errors, null, 2)}

For each error: re-derive the truth yourself (read the prototype ${PROTO} at the relevant lines, or grep/read the target source) and correct the document — fix wrong line refs, wrong statuses in the assessment table (keep the six-status vocabulary and evidence rules), wrong evidence citations, and missing coverage rows. Corrections must strengthen accuracy, never delete inconvenient claims wholesale; if a claim was simply wrong, replace it with what is actually true and cite it. Update the Missing / Modify sections if a status change moves a feature between them. Do not touch sections the errors do not implicate.

Return JSON: system, changes (one string per correction made), md_updated.`
}

function reverifyPrompt(s, i, errors) {
  const md = OUT + '/' + nn(i) + '-' + s.id + '.md'
  return `${COMMON}

You are re-auditing the document ${md} (system "${s.title}", prototype ${PROTO}) after a fixer addressed these previously-found errors:
${JSON.stringify(errors, null, 2)}

Check ONLY that each listed error is now actually resolved in the document (open the corrected lines/citations and confirm; for status changes confirm the table, Missing, and Modify sections are consistent). If every listed error is resolved, change the doc's frontmatter status line to "status: verified" (your only permitted edit); otherwise edit nothing. Return JSON: system, verdict (pass if every listed error is resolved, else fail), errors (only the still-unresolved ones), checks_done.`
}

const rows = await pipeline(
  SYSTEMS,
  (s, _o, i) => agent(comparePrompt(s, i), opt({ label: 'compare:' + s.id, phase: 'Compare', schema: CMP_SCHEMA, effort: E.compare }, M.compare)),
  (cmp, s, i) => {
    if (!cmp) return null
    return agent(verifyPrompt(s, i), opt({ label: 'verify:' + s.id, phase: 'Verify', schema: VER_SCHEMA, effort: E.verify }, M.verify))
      .then(ver => ({ cmp, ver }))
  },
  async (pv, s, i) => {
    if (!pv) return null
    if (!pv.ver) return { ...pv, finalVerdict: 'unverified', fixed: false }
    if (pv.ver.verdict === 'pass') return { ...pv, finalVerdict: 'pass', fixed: false }
    log('Doc failed verify, fixing: ' + s.id + ' (' + pv.ver.errors.length + ' errors)')
    const fix = await agent(fixPrompt(s, i, pv.ver.errors), opt({ label: 'fix:' + s.id, phase: 'Fix', schema: FIX_SCHEMA, effort: E.fix }, M.fix))
    const rv = await agent(reverifyPrompt(s, i, pv.ver.errors), opt({ label: 'reverify:' + s.id, phase: 'Fix', schema: VER_SCHEMA, effort: E.verify }, M.fix))
    return { ...pv, fixed: true, fixChanges: fix ? fix.changes : [], finalVerdict: rv ? rv.verdict : 'unverified', residualErrors: rv ? rv.errors : [] }
  }
)

const settled = rows.filter(Boolean)
const failedSystems = SYSTEMS.filter((s, i) => !rows[i]).map(s => s.id)
if (failedSystems.length) log('Pipeline lost systems (agent errors): ' + failedSystems.join(', '))
const summary = settled.map(r => ({
  system: r.cmp.system,
  verdict: r.finalVerdict,
  fixed: !!r.fixed,
  residual: (r.residualErrors || []).length,
  counts: r.cmp.status_counts,
  notable: r.cmp.notable,
}))
log('Compare+verify settled: ' + settled.length + '/' + SYSTEMS.length + '; verdicts: ' + summary.map(x => x.system + '=' + x.verdict).join(', '))

const consistency = await agent(`${CTX}

You are the cross-document consistency and completeness checker for the breakdown folder ${OUT}. Read all NN-*.md docs (they now include per-feature status tables), plus _features.json, _chunkmap.json, and the delta doc if present. Do NOT edit the system docs — you write exactly one new file.

Mandates:
1. Dependency symmetry: frontmatter depends_on and "Dependencies & integration points" sections must agree pairwise (if A says it hands off to B, B should acknowledge the seam). List asymmetries.
2. Ownership overlaps: start from the candidates the docs themselves flagged in their warnings and open questions (mechanics documented near a range boundary, helpers used across systems, panes dispatched from one system but owned by another). For each: name the single owning doc and confirm the mechanic is verdicted exactly once somewhere (not lost, not doubled). Flag any double-count that would cause double-porting and any orphan documented nowhere.
3. Delta completeness: every "new in current" item in the delta doc must be traceable to at least one feature row in some doc — name the doc for each, flag orphans.
4. Cross-resolvable open questions: where one doc's "Open questions" is answered by another doc's content, record the resolution.
5. Status sanity: statuses for the SAME underlying mechanic referenced from two docs must not contradict.

Write ${OUT}/_consistency.md with sections mirroring the five mandates (concise, actionable, reference docs by NN-id and rows by number). Return JSON: issues (severity info|warn|error, systems, detail), resolutions (open questions you resolved), md_path.`,
  opt({ label: 'cross:consistency', phase: 'Cross', schema: CON_SCHEMA, effort: E.cross }, M.cross))

const synthOpts = opt({ label: 'cross:synthesis', phase: 'Cross', schema: SYN_SCHEMA, effort: E.synthesis }, M.synthesis)

const synthesis = await agent(`${CTX}
${DELTA_NOTE}

You are the SYNTHESIS agent — the last stage of the pipeline. The folder ${OUT} contains the verified per-system docs (NN-*.md with per-feature status tables), _features.json, _chunkmap.json, the delta doc if present, and _consistency.md. The per-system verify outcomes were: ${JSON.stringify(summary.map(x => ({ system: x.system, verdict: x.verdict, fixed: x.fixed, residual: x.residual, counts: x.counts })))}.
Consistency findings: ${JSON.stringify((consistency && consistency.issues) || [])}.

Read _consistency.md and every NN-*.md (at minimum: frontmatter, Current state paragraph + table, Missing, Modify). Then write ${OUT}/00-index.md (overwrite any existing one — a lite index left by an earlier lite run is stale, not a source) — the single entry point the planning skills (and the user) read first. Structure:

---
title: <prototype name> Breakdown Index
source_prototype: ${PROTO}
profile: full
generated: ${TODAY}
pipeline: ${args.pipelineNote || 'liang-quest-recon'}
---

# Executive summary
The port gap in one tight page: what the prototype contains, what the target codebase already covers, where the big holes are, where the code is ahead of the prototype. Written for someone deciding the next few campaigns — but do NOT decompose into campaigns; that is the saga planner's job downstream.

# System status table
| # | System | Doc | Features | done | partial | missing | divergent | proto-only | oos-native | Verify |
One row per system, numbers from the docs' CURRENT tables (post-fix — authoritative over the in-band summary above if they differ; say so when they do), Verify column pass/fail(+residual count)/unverified. Add a totals row.

# Locked-decision divergences
The features across all docs marked divergent because of a locked decision, gathered in one place, framed "respect, don't re-litigate". Note earlier locked architecture that also drives divergences.

# Cross-cutting seams
The shared-state ownership map in target-codebase terms (prototype global state -> owning class/subsystem -> built/partial/no-owner), the ownership resolutions from _consistency.md worth a planner's attention, and unresolved warn/error consistency issues.

# Open questions rollup
Deduplicated open questions that survive cross-resolution, grouped by system, each tagged [design] (needs a decision) vs [code] (needs archaeology).

# How to consume this folder
Reading order; what _features.json/_chunkmap.json are; and one paragraph telling downstream planners (liang-quest-saga-planner, or a single liang-quest-planner run) to treat THIS FOLDER (not the raw prototype) as their source, with per-doc line refs available for drill-down. State the planner contract: work is the Missing sections, the Modify sections minus rows flagged as locked decisions, and the absent behavior each partial row's note names; divergent rows that follow a locked decision, prototype-only and oos-native rows are NOT work; build on code that is ahead of the prototype; the folder is a frozen snapshot that consumers never edit.

Keep it under ~250 lines, information-dense, no filler. Return JSON: md_path, headline (one sentence: the single most important fact about the gap), per_system (system + one-line status_line each).`, synthOpts)

return {
  perSystem: summary,
  lostSystems: failedSystems,
  consistencyIssues: (consistency && consistency.issues) || [],
  consistencyPath: consistency ? consistency.md_path : null,
  indexPath: synthesis ? synthesis.md_path : null,
  headline: synthesis ? synthesis.headline : null,
  perSystemLines: synthesis ? synthesis.per_system : [],
}
