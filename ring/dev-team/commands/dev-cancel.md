---
name: ring:dev-cancel
description: Cancel the current development cycle
argument-hint: "[--force]"
---

Cancel the current development cycle.

## Usage

```
/ring:dev-cancel [--force]
```

| Option | Description |
|--------|-------------|
| `--force` | Cancel without confirmation |

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: ring:cycle-management with mode=cancel
```

Pass through any arguments (e.g., `--force`) to the skill.

The skill contains the complete workflow with:
- Confirmation prompt (unless `--force`)
- State preservation for potential resume
- Cycle status update to `cancelled`
- Partial feedback report generation
