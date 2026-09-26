# Run Plan

Plan the sweep before running anything. Read every `ready` task side by side with the project rules, then decide order, what runs together, and which model runs each task.

- **Order:** start from folder-name order and `after:`. Add the dependencies the fields miss: one task needing another's output, or two tasks changing the same thing. Treat each like an `after:`. When unsure, pick the likelier order and run the pair in sequence. When two tasks' Decisions contradict, block the later one for the user.
- **Together:** run tasks at the same time only when you judge they cannot interfere through shared files, tools one process holds, builds, or version-control state. When in doubt, run them in sequence.
- **Model:** give each task the cheapest model you expect to pass every Done When check within the project rules. A Decision naming a model wins. The orchestrator stays on the strongest model. If the runtime cannot choose models per child, run everything on the default and say so.
- **Step up once:** when a task on a cheaper model blocks because its work did not pass, not for an outside reason, re-run it once from `Next:` on a stronger model before leaving it `blocked`.
- **Held tasks:** a task that depends on a blocked task waits. It stays `ready`; the report lists it as waiting on that task.
- **Record:** write the plan and a one-line reason for each call into the run report. List inferred dependencies there as suggested `after:` lines; never write `after:` yourself.
