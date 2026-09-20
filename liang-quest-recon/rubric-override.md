# Rubric Override

liang-quest-recon is a pipeline/protocol skill with an intentional non-workflow shape: its H2 sections mirror the five-stage pipeline (Stages, Invocation, Pre-Flight, Model Routing, Execution Profiles, Reliability Invariants, Resume, Downstream Handoff) rather than the canonical workflow layout. The canonical-section checks are disabled per the rubric's own guidance for intentionally-shaped skills.

## Disable
- L1-02
- L1-03

## Additional Checks
| ID | Check | Severity | Fixable | Intent |
|----|-------|----------|---------|--------|
| X-01 | Briefs/scripts sync | critical | no | The worker instructions in `references/stage-briefs.md` and the prompt text embedded in `references/wf-map-breakdown.js` / `references/wf-compare-verify.js` must agree on rules, gates, statuses, and output contracts. Flag any semantic drift (a rule present in one and absent or contradicted in the other); report-only — reconciliation needs a human/agent decision about which side is right. |
| X-02 | Artifact contract authority | advisory | no | Any statement in SKILL.md or stage-briefs.md about file formats, statuses, or gates must not contradict `references/artifacts.md` (the declared authority on conflict). |
