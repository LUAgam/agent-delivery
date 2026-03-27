---
description: Show the active stage-harness feature state and gate readiness
argument-hint: [feature-name]
allowed-tools: Bash(python3:*), Read
---

# /harness-status

Show the current feature, stage, and gate readiness.

## Steps

1. Resolve the requested feature name:
   - If `$ARGUMENTS` is present, use it as the feature name.
   - Otherwise, inspect the active feature recorded by the plugin.

2. Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/harness_state.py" status ${ARGUMENTS:+--feature "$ARGUMENTS"} --allow-missing
```

3. Parse the JSON result and summarize:
   - active feature
   - current stage
   - whether the current stage passes validation
   - missing artifacts, if any
   - important directories (`.harness/features/<feature>`, `.shipspec/planning/<feature>`)

4. If no active feature exists, instruct the user to run `/harness-start [feature-name]`.
