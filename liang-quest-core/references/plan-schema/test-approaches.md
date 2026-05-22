# Test Approaches Registry — `.liang/test-approaches.yaml`

Source of truth for the test-approaches.yaml registry schema. Project-global registry mapping quest types to test/validation approaches. Created by tacticians; read by executors. Both TDD and general tacticians consume this schema.

## Location

```
<workspace-root>/.liang/test-approaches.yaml
```

## Automatable Entry

```yaml
quest_types:
  <quest-type-slug>:
    framework: string              # e.g. "jest", "pytest", "catch2"
    test_command: string           # e.g. "npm test", "pytest tests/"
    test_file_pattern: string      # e.g. "**/*.test.ts"
```

## Verify-Only Entry

```yaml
quest_types:
  <quest-type-slug>:
    verify_only: true
    verify_hint: string            # guidance for hybrid verification
```

## Rules

- Quest type slugs are open-ended (user-defined).
- Each entry uses exactly one shape.
- The `verify_only` flag distinguishes shapes; absence implies automatable.
- The file is optional. When absent, pipeline falls back to all-TDD behavior.

## Validation Rules

- `quest_types` is the required top-level key.
- Each quest type slug must be unique within the file.
- Slugs follow family conventions: lowercase, hyphen-separated, ASCII only.
- Automatable entries require all three fields: `framework`, `test_command`, `test_file_pattern`.
- Verify-only entries require `verify_only: true` and `verify_hint`.
- Mixed shapes within a single entry are invalid.

## Cross-References

- See `tdd-cycles.md` for TDD-specific readiness gate behavior that consumes registry entries.
- See `general-steps.md` for general workflow registry-informed verification (planned).
