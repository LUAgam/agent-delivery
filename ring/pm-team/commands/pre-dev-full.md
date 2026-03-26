---
name: ring:pre-dev-full
description: Complete 10-gate pre-dev workflow for large features (>=2 days)
argument-hint: "[feature-name]"
---

Run the **Full Track** pre-development workflow (10 gates) for a feature.

## When to Use

This track is for features that have ANY of:
- Take >=2 days to implement
- Add new external dependencies (APIs, databases, libraries)
- Create new data models or entities
- Require multi-service integration
- Use new architecture patterns
- Require team collaboration

**If feature is simple (<2 days, existing patterns), use `/ring:pre-dev-feature` instead.**

## What It Does

Orchestrates 10 sequential gates with human approval at each:

| Gate | Purpose | Output |
|------|---------|--------|
| 0 | Research (4 parallel agents) | research.md |
| 1 | PRD + UX Validation | prd.md, ux-criteria.md |
| 2 | Feature Map + UX Design | feature-map.md, user-flows.md, wireframes/ |
| 2.5 | Design Validation (if UI) | design-validation.md |
| 3 | TRD | trd.md |
| 4 | API Design | api-design.md |
| 5 | Data Model | data-model.md |
| 6 | Dependency Map | dependency-map.md |
| 7 | Task Breakdown | tasks.md |
| 8 | Subtask Creation | subtasks.md |
| 9 | Delivery Planning | delivery-roadmap.md, .json |

All artifacts saved to `docs/pre-dev/<feature-name>/`.

## MANDATORY: Load Full Skill

**This command delegates to the `ring:pre-dev-full` skill which contains the complete 10-gate orchestration logic.**

```
Use Skill tool: ring-pm-team:pre-dev-full
```

Pass all arguments: $@
