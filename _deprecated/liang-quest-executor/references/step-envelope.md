# Step Envelope Format

Load when authoring or reading step envelopes. Each parsed quest `.md` step produces one executor-generated `step-<sid>.md` step envelope in `.run/<quest-id>/`. The `.md` extension provides both human-readable Markdown rendering and machine-readable fenced YAML blocks for the child contract.

**Schema — source of truth:** `liang-quest-core/references/execution/child-contracts.md` Planner-Native sections.

| Section | Contract | Writer |
|---------|----------|--------|
| `input` | Execute-Child Input YAML | Executor before spawn |
| `output` | Execute-Child Output YAML | Child on completion |
| `re_plan` | Re-Plan-Child Output YAML | Re-plan-child on retry 2+ |
| `verification` | quest-level VC results block | Executor after §7d VC verification |
| `usage` | per-attempt token/cost records harvested from pinned child session files | Executor after each child exit |

## Mode-Specific I/O

| Mode | Input fenced YAML | Output fenced YAML | Re-plan fenced YAML | Usage fenced YAML |
|------|-------------------|---------------------|----------------------|--------------------|
| **Pi CLI** | Executor writes before spawning child | Child writes on completion | Re-plan-child writes | Executor writes after harvest |
| **Claude** | Omitted in-flight (context delivered in-memory); executor writes a transcript after the fact | Executor writes from in-memory output | Executor writes from in-memory re-plan output | Omitted (no usage data available) |
| **Batch** | Batch script writes before spawning child | Child writes on completion | Re-plan-child writes | Batch script writes after harvest |

In `--claude` mode the executor back-fills the input section as a transcript after dispatch and writes output and verification sections from the in-memory results — full envelope parity with Pi CLI mode for the run report, except `usage` (no usage data crosses the subagent boundary).

## Usage Harvest (Pi CLI / batch)

Every spawned child gets a pinned session file: pass `--session .run/<quest-id>/sessions/<label>.jsonl` at spawn, with labels `step-<sid>-a<attempt>` (execute), `replan-<sid>-a<attempt>` (re-plan), `verify-vc<n>` (verify). After the child exits — including on error or timeout; partial sessions still carry usage — parse the session JSONL:

1. Take every line whose `message.role` is `assistant` and which carries a `message.usage` record.
2. Map fields: `usage.input` → `input_tokens`, `usage.output` → `output_tokens`, `usage.cacheRead` → `cache_read_tokens`, `usage.cacheWrite` → `cache_write_tokens`, `usage.cost.total` → `cost_usd`.
3. Sum across messages into one attempt entry (schema: `liang-quest-core/references/execution/child-contracts.md § Usage Section`) and append it to the envelope's `usage` section (execute/re-plan children) or hold it for the quest rollup only (verify children).

If the session file is missing or unparseable, skip the entry and surface the gap in the run report — never write zeros. This harvest reads session files only; child stdout/stderr stays off-limits for structured data (Boundary #10).

Source: extracted from liang-quest-executor/SKILL.md Step Envelope Format section.
