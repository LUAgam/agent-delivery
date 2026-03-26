---
name: ring:dev-status
description: Check the status of the current development cycle
argument-hint: ""
---

Check the status of the current development cycle.

## Usage

```
/ring:dev-status
```

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: ring:cycle-management with mode=status
```

The skill contains the complete workflow with:
- State file discovery across dev-cycle and dev-refactor paths
- Cycle metrics: ID, start time, task counts, current gate
- Assertiveness score computation
- Elapsed time calculation
