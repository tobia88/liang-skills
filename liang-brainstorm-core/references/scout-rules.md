# Project Scout Rules

Shared project scouting rules for all liang-brainstorm-* skills.

## Timing

- Minimal scout at startup.
- Bounded lens-specific scout after the planning lens is confirmed.
- Summarize the scout briefly before using it heavily.

## Allowed by Default

Only inspect lightweight, relevant, small text context:

- top-level file/folder listing
- `README.md`, `README.*`
- small docs/design files relevant to the confirmed lens
- project metadata such as `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `composer.json`, `pom.xml`, `*.csproj`
- skill files such as `SKILL.md`, `.pi/skills/`, `.agents/skills/`
- obvious engine/project config for game projects when small and text-based

## Avoid by Default

Do not inspect:

- `.env`, `.env.*`
- credentials, tokens, secrets, keys
- `*.pem`, `*.key`, `id_rsa*`
- `.git/`, `node_modules/`, `vendor/`
- `dist/`, `build/`, `target/`, `out/`, `coverage/`
- caches/temp folders
- large binaries/assets
- broad source dumps
- old reports in `.liang/brainstorm-reports/` unless explicitly requested

If deeper inspection seems necessary, ask first.

## Report Context Rule

In the final HTML, include only:

- a short `Scouted Project Context` summary
- referenced paths inspected

Do not dump file contents by default.

Source: extracted from liang-relentless-brainstorm/SKILL.md Project Scout
Rules section (lines 162-204) per dc001. Full extraction per dc002 —
includes timing, allowed/avoided paths, and report context rule. Variant
skills may override or skip individual sections as needed.
