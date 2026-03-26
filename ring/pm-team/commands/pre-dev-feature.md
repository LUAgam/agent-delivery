---
name: ring:pre-dev-feature
description: Lightweight 5-gate pre-dev workflow for small features (<2 days)
argument-hint: "[feature-name]"
---

Run the **Small Track** pre-development workflow (5 gates) for a feature.

## When to Use

This track is for features that:
- Take <2 days to implement
- Use existing architecture patterns
- Don't add new external dependencies
- Don't create new data models/entities
- Don't require multi-service integration
- Can be completed by a single developer

**If any of the above are false, use `/ring:pre-dev-full` instead.**

## What It Does

Orchestrates 5 sequential gates with human approval at each:

| Gate | Purpose | Output |
|------|---------|--------|
| 0 | Research (4 parallel agents) | research.md |
| 1 | PRD + UX Validation + Wireframes | prd.md, ux-criteria.md, wireframes/ |
| 1.5 | Design Validation (if UI) | design-validation.md |
| 2 | TRD (skips Feature Map) | trd.md |
| 3 | Task Breakdown (skips API/Data/Deps) | tasks.md |
| 4 | Delivery Planning | delivery-roadmap.md, .json |

All artifacts saved to `docs/pre-dev/<feature-name>/`.

## MANDATORY: Load Full Skill

**This command delegates to the `ring:pre-dev-feature` skill which contains the complete 5-gate orchestration logic.**

```
Use Skill tool: ring-pm-team:pre-dev-feature
```

Pass all arguments: $@
