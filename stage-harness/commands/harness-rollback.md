---
description: Roll back the active feature to a previous stage
argument-hint: [stage-name]
allowed-tools: Bash(python3:*), Read
---

# /harness-rollback

Roll the active feature back to a prior stage when a gate fails, a plan drifts, or a human decision requires rework.

## Usage

- `/harness-rollback` -> roll back to the last completed stage
- `/harness-rollback PLAN` -> roll back directly to `PLAN`

## Steps

1. Determine the rollback target:
   - If `$ARGUMENTS` is empty, use the last completed stage from history.
   - If `$ARGUMENTS` is set, treat it as the explicit target stage.
2. Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/harness_state.py" rollback --to-stage "$ARGUMENTS"
```

3. Read the JSON response and summarize:
   - previous stage
   - new current stage
   - rollback count
4. Tell the user which artifacts should be updated before re-advancing.

## Notes

- This command only rolls back the stage state. It does not modify git history.
- Use it when execution drift invalidates the current stage contract.
