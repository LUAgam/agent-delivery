---
description: Start a stage-harness workflow for a feature
argument-hint: [feature-name]
allowed-tools: Bash(python3:*), Read
---

# /harness-start

Initialize the stage-harness workspace for a feature and set it as the active workflow.

## Steps

1. Resolve the feature name:
   - If `$ARGUMENTS` is present, use it.
   - Otherwise, ask the user for a short feature name in kebab-case.
2. Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/harness_state.py" init --feature "$ARGUMENTS"
```

3. Read the JSON output and summarize:
   - feature name
   - current stage
   - state file path
   - missing artifacts for the current stage

## Expected behavior

- Creates `.harness/global-config.json` if missing
- Creates `.harness/features/<feature>/state.json`
- Marks the feature as active in `.harness/active-feature.txt`
- Leaves the workflow at `CLARIFY`

## Follow-up guidance

After initialization, instruct the user or orchestrator to create:
- `.harness/features/<feature>/artifacts/clarification-notes.md`

Then use `/harness-status` or `/harness-advance`.

## Gate behavior in this minimal version

- The Stop hook is intentionally permissive for `CLARIFY`, `SPEC`, `PLAN`, and `EXECUTE`.
- Hard blocking is only enforced once the workflow reaches `VERIFY`, `FIX`, or `DONE`.
- Stage transitions are still enforced by `/harness-advance`, which remains the authoritative gate for moving forward.
