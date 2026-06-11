# Step Envelope Format

Load when authoring or reading step envelopes. Each parsed quest `.md` step produces one executor-generated `step-<sid>.md` step envelope in `.run/<quest-id>/`. The `.md` extension provides both human-readable Markdown rendering and machine-readable fenced YAML blocks for the child contract.

**Schema — source of truth:** `liang-quest-core/references/execution/child-contracts.md` Planner-Native sections.

| Section | Contract | Writer |
|---------|----------|--------|
| `input` | Execute-Child Input YAML | Executor before spawn |
| `output` | Execute-Child Output YAML | Child on completion |
| `re_plan` | Re-Plan-Child Output YAML | Re-plan-child on retry 2+ |
| `verification` | quest-level VC results block | Executor after §7d VC verification |

## Mode-Specific I/O

| Mode | Input fenced YAML | Output fenced YAML | Re-plan fenced YAML |
|------|-------------------|---------------------|----------------------|
| **Pi CLI** | Executor writes before spawning child | Child writes on completion | Re-plan-child writes |
| **Claude** | Omitted in-flight (context delivered in-memory); executor writes a transcript after the fact | Executor writes from in-memory output | Executor writes from in-memory re-plan output |
| **Batch** | Batch script writes before spawning child | Child writes on completion | Re-plan-child writes |

In `--claude` mode the executor back-fills the input section as a transcript after dispatch and writes output and verification sections from the in-memory results — full envelope parity with Pi CLI mode for the run report.

Source: extracted from liang-quest-executor/SKILL.md Step Envelope Format section.
