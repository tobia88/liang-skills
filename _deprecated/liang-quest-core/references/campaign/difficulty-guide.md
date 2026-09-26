# Difficulty Classification Guide

Canonical criteria for tagging quests easy/medium/hard; consumed by liang-quest-planner (quest tagging) and liang-quest-executor (model-routing awareness); the field drives `project.yaml models.execution_by_difficulty` routing downstream.

- **`easy`** — single-file edit, mechanical change, no new abstractions, no cross-system reasoning. Examples: rename a symbol, add a UPROPERTY, swap a literal, write a known struct definition, update a config value.
- **`medium`** — multi-file change, introduces or modifies an abstraction (struct, helper, interface), or requires understanding the call topology of a small subsystem. Examples: refactor a data structure with its call sites, add a new BlueprintNativeEvent and wire it through, restructure a private map's invariants.
- **`hard`** — cross-system reasoning, new architecture, ambiguous integration boundary, or significant verification work. Examples: introduce a new subsystem, redesign a replication boundary, integrate two previously-isolated systems, end-to-end verification quest covering build + playtest + intel.

When in doubt between two levels, pick the higher one — under-classifying routes a quest to a model that may fumble it; over-classifying just spends slightly more on a model that handles it cleanly.

Extracted from liang-quest-planner/SKILL.md § 2a. Decompose into quests (in memory) per dc003.
