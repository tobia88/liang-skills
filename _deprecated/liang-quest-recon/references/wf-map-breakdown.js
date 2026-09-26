// liang-quest-recon — stage 1-2 workflow (Claude Code profile).
// Invoke: Workflow({ scriptPath: "<this file>", args: {...} })
//
// args:
//   protoPath      (required) absolute path to the prototype file
//   outDir         (required) absolute path to the breakdown output folder
//   projectContext (required) 1-2 paragraphs: the project, what the prototype is, why it is being broken down
//   bannerScan     (recommended) orchestrator's section/banner scan seed "line: title | ..." — the mapper treats it as a hint
//   protoPrevPath  (optional) prior prototype version for the structural delta; null/absent skips the delta agent
//   deltaContext   (optional) context for the delta agent: what the prior version fed, what is already executed
//   excludeHints   (optional) known already-ported embedded subsystems to fence off (only their bridge stays in scope)
//   models         (optional) { map, delta, breakdown } — resolved by the orchestrator from project.yaml; an absent key means no model override (harness default)
//   efforts        (optional) { map, delta, breakdown } — default high/medium/medium
//
// Returns: { systems, shared_core, excluded_spans, uncoveredLines, docs (with per-system feature
// arrays — the orchestrator assembles _features.json from these), failedBreakdowns, delta, mapperNotes }.
// Keep this script's prompts in sync with references/stage-briefs.md.

export const meta = {
  name: 'recon-map-breakdown',
  description: 'Recon stages 1-2: chunk-map the prototype into systems, write one breakdown .md per system, optional prior-version delta',
  phases: [
    { title: 'Map', detail: 'chunk map + optional structural delta' },
    { title: 'Breakdown', detail: 'one breakdown doc per system, line-ref discipline' },
  ],
}

if (!args || !args.protoPath || !args.outDir || !args.projectContext) {
  throw new Error('recon-map-breakdown requires args: protoPath, outDir, projectContext (plus optional bannerScan, protoPrevPath, deltaContext, excludeHints, models, efforts)')
}

const PROTO = args.protoPath
const OUT = args.outDir
const M = args.models || {}
// No default model lives here: an unresolved role is spawned without a model override (harness default).
const opt = (o, m) => (m ? { ...o, model: m } : o)
const E = Object.assign({ map: 'high', delta: 'medium', breakdown: 'medium' }, args.efforts || {})
const EXCLUDE_HINTS = args.excludeHints || 'None known — but stay alert for embedded previously-ported subsystems and base64 asset blobs.'
const BANNER_SCAN = args.bannerScan || '(none provided — do a full scan yourself)'

const CTX = `${args.projectContext}

You are one stage of a multi-agent recon pipeline turning the prototype file ${PROTO} into verified breakdown documents that a port-planning skill consumes. Be precise and complete within your brief; never guess — every factual claim must be traceable to a line number. Note: the Read tool may render some UTF-8 punctuation as mojibake; that is a display artifact — write proper punctuation in your outputs and never transcribe mojibake bytes. Explicit adult prose, if present, is summarized mechanics-only and never reproduced. Never read base64/data-URI lines.`

const RANGE = { type: 'object', required: ['start', 'end'], properties: { start: { type: 'integer' }, end: { type: 'integer' } } }
const MAP_SCHEMA = {
  type: 'object', required: ['total_lines', 'systems', 'shared_core', 'excluded'],
  properties: {
    total_lines: { type: 'integer' },
    systems: { type: 'array', items: { type: 'object', required: ['id', 'title', 'order', 'purpose', 'ranges', 'depends_on'], properties: {
      id: { type: 'string' }, title: { type: 'string' }, order: { type: 'integer' }, purpose: { type: 'string' },
      ranges: { type: 'array', items: RANGE }, depends_on: { type: 'array', items: { type: 'string' } } } } },
    shared_core: { type: 'array', items: { type: 'object', required: ['start', 'end', 'label'], properties: { start: { type: 'integer' }, end: { type: 'integer' }, label: { type: 'string' } } } },
    excluded: { type: 'array', items: { type: 'object', required: ['start', 'end', 'reason'], properties: { start: { type: 'integer' }, end: { type: 'integer' }, reason: { type: 'string' } } } },
    uncovered: { type: 'array', items: RANGE },
    notes: { type: 'string' },
  },
}
const DOC_SCHEMA = {
  type: 'object', required: ['system', 'md_path', 'features'],
  properties: {
    system: { type: 'string' }, md_path: { type: 'string' },
    features: { type: 'array', items: { type: 'string' } },
    depends_on: { type: 'array', items: { type: 'string' } },
    open_questions: { type: 'array', items: { type: 'string' } },
    warnings: { type: 'array', items: { type: 'string' } },
  },
}
const DELTA_SCHEMA = {
  type: 'object', required: ['new_systems', 'grown', 'unchanged', 'md_path'],
  properties: {
    new_systems: { type: 'array', items: { type: 'string' } }, grown: { type: 'array', items: { type: 'string' } },
    unchanged: { type: 'array', items: { type: 'string' } }, md_path: { type: 'string' },
  },
}

phase('Map')

const deltaP = args.protoPrevPath
  ? agent(`${CTX}

Task: structural delta between two prototype versions — ${args.protoPrevPath} (prior) vs ${PROTO} (current). ${args.deltaContext || ''} Material that exists only in the current version is the likeliest source of unported work; spotlight it.

Method: scan both files for section banner comments (grab trailing context lines to read titles). Align sections by title; use banner line positions to estimate per-section size and growth. For sections new or substantially grown, sample-read small slices (a few hundred lines total across all samples) to characterize WHAT was added — do not deep-read. Never read either file end to end; skip base64 blob lines entirely.

Write ${OUT}/_delta-prev.md with sections: "New in current", "Substantially grown" (rough old->new size), "Roughly unchanged", "Notes for the compare stage" (one paragraph: which systems should be presumed to have existing target-code counterparts vs fresh). Keep it under ~120 lines.

Return JSON: new_systems (section titles new in current), grown, unchanged, md_path.`,
    opt({ label: 'delta:prev', phase: 'Map', schema: DELTA_SCHEMA, effort: E.delta }, M.delta))
  : Promise.resolve(null)

const chunkmap = await agent(`${CTX}

Task: produce the definitive CHUNK MAP of ${PROTO}. Every downstream agent reads only the line ranges you assign, so an error here poisons the whole pipeline. Work carefully and verify by reading the file at the boundaries you claim.

Orchestrator's banner scan seed (a HINT — it may be wrong or incomplete; you are authoritative): ${BANNER_SCAN}

Steps:
1. Establish the authoritative total line count yourself (count lines with a shell tool, cross-check by reading the file tail with the Read tool).
2. Rescan for section banners in all comment styles; locate structural boundaries (style/script/markup blocks). Unbannered drift between sections is common — verify by reading, not by trusting banner-to-banner spans, and attribute drift to the right system.
3. Locate base64/data-URI asset blob lines; they go into "excluded" with reason "asset blob".
4. Known already-ported embedded subsystems: ${EXCLUDE_HINTS} Find their actual spans, read a few lines at each edge to verify the boundaries, and exclude them — only their bridge/seam code stays in scope as its own system.
5. Group everything in-scope into 12-20 SYSTEMS. Merge each styling/markup fragment into the system it serves; split any system that would exceed roughly 3x the per-system average, at a real code seam. Explain notable grouping calls in notes.
6. shared_core: the load-bearing global spans EVERY breakdown agent must also read (global state, key helpers, boot wiring, load-bearing design tokens). HARD CAP: 800 lines total.
7. Partition discipline: system ranges must not overlap each other, shared_core, or excluded. Head/boilerplate and trivial glue go into excluded with reason "boilerplate". Every line 1..total_lines lands in exactly one bucket; list leftover gaps larger than 20 lines in "uncovered" (aim for zero). Verify the partition arithmetically before returning.
8. Per system: kebab-case id, title, order (reading order: core/world first, then gameplay systems, then tooling, then boot), one-line purpose, ranges, depends_on best guesses.
9. Write the complete map as pretty-printed JSON to ${OUT}/_chunkmap.json (writing the file creates the folder). Then return the exact same data per the output schema.`,
  opt({ label: 'map:chunk-map', phase: 'Map', schema: MAP_SCHEMA, effort: E.map }, M.map))

if (!chunkmap.systems || chunkmap.systems.length < 6 || chunkmap.systems.length > 30) {
  throw new Error('Mapper returned implausible system count: ' + (chunkmap.systems ? chunkmap.systems.length : 'none'))
}
chunkmap.systems.sort((a, b) => a.order - b.order).forEach((s, i) => {
  s.order = i + 1
  s.id = s.id.toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '')
})
log('Chunk map: ' + chunkmap.systems.length + ' systems over ' + chunkmap.total_lines + ' lines: ' + chunkmap.systems.map(s => s.id).join(', '))

const uncoveredLines = (chunkmap.uncovered || []).reduce((a, r) => a + (r.end - r.start + 1), 0)
if (uncoveredLines > 500) log('WARNING: ' + uncoveredLines + ' lines uncovered by the chunk map')
const overlapWarnings = []
for (const s of chunkmap.systems) {
  for (const r of s.ranges) {
    for (const x of (chunkmap.excluded || [])) {
      if (r.start <= x.end && x.start <= r.end) overlapWarnings.push(s.id + ' ' + r.start + '-' + r.end + ' overlaps excluded ' + x.start + '-' + x.end)
    }
  }
}
if (overlapWarnings.length) log('WARNING system/excluded overlaps: ' + overlapWarnings.join('; '))

phase('Breakdown')

const coreDesc = chunkmap.shared_core.map(r => r.start + '-' + r.end + ' (' + r.label + ')').join(', ')
const exclDesc = (chunkmap.excluded || []).filter(x => (x.end - x.start) > 5).map(r => r.start + '-' + r.end).join(', ')
const sysIndex = chunkmap.systems.map(s => s.id + ' (' + s.title + ')').join(', ')

function breakdownPrompt(s) {
  const nn = String(s.order).padStart(2, '0')
  const mdPath = OUT + '/' + nn + '-' + s.id + '.md'
  const ranges = s.ranges.map(r => r.start + '-' + r.end).join(', ')
  return `${CTX}

You own ONE system of the prototype: "${s.title}" (id: ${s.id}). Purpose per the chunk map: ${s.purpose}. Mapper's dependency guess: ${JSON.stringify(s.depends_on)}. All system ids in the pipeline: ${sysIndex}.

Your assigned line ranges in ${PROTO}: ${ranges}
Shared-core ranges you should ALSO read (global state, helpers, boot): ${coreDesc}

Reading rules:
- Read ONLY your ranges plus shared core, using Read with offset/limit in slices of at most 1500 lines. NEVER read the whole file.
- NEVER read excluded ranges (already-ported embedded subsystems, asset blobs, boilerplate): ${exclDesc}
- If an identifier you need is defined outside your ranges, grep the prototype for it with a few lines of context rather than reading other systems' sections wholesale.

Write ${mdPath} with EXACTLY this structure:

---
system: ${s.id}
title: ${s.title}
prototype_lines: "${ranges}"
depends_on: [refine the mapper guess from actual evidence]
status: breakdown
---

## What the prototype does
Behavior-complete description, prose plus bullets. Every claim carries a line ref like (L4620) or (L4620-4655).

## Data & formulas
Data schemas field-by-field (use tables). Constants, tuning values, and formulas VERBATIM with line refs. For bulk content data (dialogue rows, entry lists, stock lists) document the SCHEMA plus row count plus 2-3 representative rows — never transcribe every row.

## UI / presentation
Layout, widgets, interaction affordances, and presentation-encoded behavior worth preserving as intent (animations, states). Skip pure cosmetics.

## Dependencies & integration points
What this system reads/writes of shared state; events, functions, or handoffs to other systems — name their system ids from the list above.

## Prototype-only
Debug chrome, page plumbing, embedded-asset handling, medium-specific workarounds that should NOT be ported.

## Open questions
Ambiguities a port planner must resolve. Empty section is fine.

Quality bar: this document is the ONLY thing later pipeline stages read about your system — the compare stage will grep target source against your feature list, and a skeptic agent will spot-check your line refs against the raw file; a wrong or unverifiable line ref fails the whole document. Completeness of observable features and data matters more than prose polish. Do NOT compare against target code and do NOT give porting advice — that is a later stage's job.

Return JSON: system (${s.id}), md_path, features (10-25 SHORT atomic capability names covering everything the system observably does — each one will be individually assessed against the target codebase, so "stamina ticks down per road segment" not "travel works"), depends_on (refined), open_questions, warnings (anything that made your read unreliable).`
}

const docs = await parallel(chunkmap.systems.map(s => () =>
  agent(breakdownPrompt(s), opt({ label: 'breakdown:' + s.id, phase: 'Breakdown', schema: DOC_SCHEMA, effort: E.breakdown }, M.breakdown))))

const okDocs = docs.filter(Boolean)
const failed = chunkmap.systems.filter((s, i) => !docs[i]).map(s => s.id)
if (failed.length) log('FAILED breakdown agents: ' + failed.join(', '))
log('Breakdown complete: ' + okDocs.length + '/' + chunkmap.systems.length + ' docs written')

const delta = await deltaP

return {
  systems: chunkmap.systems.map(s => ({ order: s.order, id: s.id, title: s.title, ranges: s.ranges })),
  shared_core: chunkmap.shared_core,
  excluded_spans: (chunkmap.excluded || []).filter(x => (x.end - x.start) > 100),
  uncoveredLines,
  docs: okDocs.map(d => ({ system: d.system, md_path: d.md_path, featureCount: (d.features || []).length, features: d.features, depends_on: d.depends_on, open_questions: d.open_questions, warnings: d.warnings })),
  failedBreakdowns: failed,
  delta,
  mapperNotes: chunkmap.notes || '',
}
