---
name: stage-flow
description: Minimal stage-machine guidance for the stage-harness plugin. Use when starting, checking, advancing, or rolling back the workflow.
---

# Stage flow

This skill defines the minimal workflow shipped in the first implementation of `stage-harness`.

## Goal

Provide a working skeleton for Iter-0 and Iter-1 from `coding/ITERATION-PLAN.md`:

- keep feature state in `.harness/features/<feature>/state.json`
- expose a stable stage machine
- block stage exits when required artifacts are missing
- allow manual advance and rollback

## Stage sequence

The current minimal sequence is:

```text
CLARIFY -> SPEC -> PLAN -> EXECUTE -> VERIFY -> DONE
```

`FIX` is reserved for later iterations and can be reached by manual rollback or future verify handling.

## Required artifacts by stage

### CLARIFY

- `.harness/features/<feature>/artifacts/clarification-notes.md`

### SPEC

- `PRD.md`
- `SDD.md`
- `TASKS.json`
- `TASKS.md`

The validator accepts either:

- `.harness/features/<feature>/artifacts/*`
- `.shipspec/planning/<feature>/*`

### PLAN

- `bridge-spec.md`
- `claude-plan.md`
- `claude-plan-tdd.md`
- `sections/index.md`

The validator accepts either:

- `.harness/features/<feature>/artifacts/*`
- `.shipspec/planning/<feature>/*`

### EXECUTE

- `.harness/features/<feature>/artifacts/implementation-summary.md`

### VERIFY

- `.harness/features/<feature>/councils/review-report.md`
- `.harness/features/<feature>/councils/test-report.md`
- `.harness/features/<feature>/councils/verification.json`

### DONE

- `.harness/features/<feature>/artifacts/release-notes.md`
- `.harness/features/<feature>/artifacts/delivery-summary.md`
- `.harness/features/<feature>/artifacts/learning-candidates.md`

## Operating rules

1. Use `/harness-start` to initialize a feature.
2. Use `/harness-status` before stage transitions.
3. Use `/harness-advance` only after the current stage validates.
4. If a stage is blocked, create or fix artifacts first.
5. If the workflow drifted, use `/harness-rollback`.

## Notes

- This first version intentionally keeps CLARIFY, SPEC, PLAN, EXECUTE, and VERIFY implementation lightweight.
- Real component integrations (Superpowers, ShipSpec, deep-plan, deep-implement, Ring) are deferred to later iterations.
