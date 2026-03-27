---
description: Advance the active feature to the next workflow stage when gate checks pass
argument-hint: [feature-name]
allowed-tools: Bash(python3:*), Read
---

# Harness Advance

Advance the active feature through the stage machine:

```text
CLARIFY -> SPEC -> PLAN -> EXECUTE -> VERIFY -> DONE
```

## Rules

1. Resolve the target feature:
   - If `$ARGUMENTS` is present, use it.
   - Otherwise advance the active feature in `.harness/active-feature.txt`.
2. Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/harness_state.py" advance ${ARGUMENTS:+--feature "$ARGUMENTS"}
```

3. Show:
   - previous stage
   - new current stage
   - recorded artifact paths captured into history
4. If the command fails because artifacts are missing, tell the user which gate failed and recommend running `/harness-status`.

## Notes

- This command is intentionally strict. It should not use `--force` in normal operation.
- The Stop hook reuses the same validation core, but only hard-blocks later exit-gated stages (`VERIFY`, `FIX`, `DONE`) in this minimal implementation.
