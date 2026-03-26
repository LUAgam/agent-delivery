---
name: ring:migrate-v4
description: Analyze Go service for lib-commons v2/v3 patterns and generate visual migration report + tasks for ring:dev-cycle
argument-hint: "[path] [--tasks] [--execute]"
---

Analyze a Go service for lib-commons v2/v3 usage and generate a visual migration report with tasks for ring:dev-cycle.

## ⛔ PRE-EXECUTION CHECK (EXECUTE FIRST)

**Before loading the skill, you MUST check:**

```
Does go.mod exist and contain lib-commons?
├── go.mod exists AND contains "lib-commons/v2" or "lib-commons/v3" → Load skill: ring:dev-migrate-v4
├── go.mod exists AND contains "lib-commons/v4" → Report: "Already on v4. Run /ring:dev-refactor for compliance check."
├── go.mod exists but NO lib-commons → Report: "No lib-commons dependency. Nothing to migrate."
└── No go.mod → Report: "Not a Go project. This skill only applies to Go services."
```

## Usage

```
/ring:migrate-v4                     # Analyze current directory, visual report only
/ring:migrate-v4 --tasks             # Also generate tasks.md for ring:dev-cycle
/ring:migrate-v4 --execute           # Generate tasks AND hand off to ring:dev-cycle
/ring:migrate-v4 /path/to/service    # Analyze specific path
```

## Flags

| Flag | Description |
|------|-------------|
| `--tasks` | Generate `migration-v4-tasks.md` compatible with `ring:dev-cycle` |
| `--execute` | Generate tasks AND automatically dispatch `ring:dev-cycle` to execute migration |
| `--dry-run` | Show analysis only, no file generation |

## Process

1. Scans `go.mod` for current lib-commons version
2. Finds ALL v2/v3 patterns across the codebase (imports, logging, config, bootstrap, telemetry, etc.)
3. Maps each finding to the v4 equivalent from Ring standards
4. Generates interactive HTML migration report (opened in browser)
5. Optionally generates `tasks.md` in `ring:dev-cycle` format
6. Optionally dispatches `ring:dev-cycle` to execute all migration tasks through gates

## Output

- **Visual report**: `~/.agent/diagrams/{service-name}-v4-migration.html`
- **Tasks file**: `docs/pre-dev/{service-name}/migration-v4-tasks.md` (with `--tasks` or `--execute`)
- **Dev cycle**: Automatic handoff to `ring:dev-cycle` (with `--execute`)

## Related Commands

| Command | When to Use |
|---------|-------------|
| `/ring:dev-refactor` | General standards compliance (not migration-specific) |
| `/ring:dev-cycle` | Execute migration tasks after this skill generates them |
| `/ring:migrate-v4 --execute` | Shortcut: generate + execute in one command |

## Prerequisites

- Go project with `go.mod`
- `lib-commons/v2` or `lib-commons/v3` as dependency
- `docs/PROJECT_RULES.md` recommended (not blocking)

## MANDATORY: Load Full Skill

```
Use Skill tool: ring:dev-migrate-v4
```
