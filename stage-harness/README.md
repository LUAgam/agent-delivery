# stage-harness

`stage-harness` is a new Claude Code plugin skeleton that implements the first practical slice of the plan in `coding/ITERATION-PLAN.md`.

## Scope of this first implementation

This version intentionally targets the smallest useful workflow surface:

- plugin skeleton and manifest
- persistent workflow state in `.harness/`
- minimal stage machine
- SessionStart / Stop / UserPromptSubmit hooks
- slash commands to start, inspect, advance, and roll back a feature workflow
- minimal agents and one shared skill for stage guidance

It does **not** yet integrate the full external component chain:

- Superpowers
- ShipSpec
- deep-plan
- deep-implement
- Ring
- ECC
- aio-reflect

Those are planned for later iterations after the orchestration skeleton is stable.

## Directory layout

```text
stage-harness/
├── .claude-plugin/plugin.json
├── commands/
├── agents/
├── skills/
├── hooks/
├── scripts/
├── templates/
└── README.md
```

Runtime state is stored in the project root:

```text
.harness/
├── global-config.json
├── active-feature.txt
└── features/<feature>/
    ├── state.json
    ├── artifacts/
    ├── councils/
    ├── decision-bundles/
    ├── sessions/
    └── trace/
```

## Current stage machine

```text
CLARIFY -> SPEC -> PLAN -> EXECUTE -> VERIFY -> DONE
```

The minimal gate rules are implemented in `scripts/harness_state.py` and reused by:

- `/harness-status`
- `/harness-advance`
- `/harness-rollback`
- `hooks/stage-init.sh`
- `hooks/stage-gate-check.sh`
- `hooks/stage-reminder.sh`

Current Stop-hook behavior is intentionally scoped:

- `CLARIFY`, `SPEC`, `PLAN`, and `EXECUTE` are allowed to pause while artifacts are still being created
- hard Stop blocking is applied to `VERIFY` and `DONE`, where the workflow is expected to be exit-gated
- repeated Stop-trigger continuations are ignored when the hook payload marks `stop_hook_active=true`

## Quick manual verification

Initialize a feature:

```bash
python3 stage-harness/scripts/harness_state.py init --feature hello-world-api
```

Inspect status:

```bash
python3 stage-harness/scripts/harness_state.py status
```

Validate the current stage:

```bash
python3 stage-harness/scripts/harness_state.py validate
```

Advance once the required artifact exists:

```bash
python3 stage-harness/scripts/harness_state.py advance
```

## Iteration mapping

This implementation primarily covers:

- Iter-0.4 create plugin skeleton
- Iter-0.5 state template
- Iter-0.6 minimal stage-init behavior
- Iter-1.1 stage-flow skill
- Iter-1.2 `/harness-start`
- Iter-1.3 `/harness-status`
- Iter-1.4 `/harness-advance`
- Iter-1.10 `stage-gate-check.sh`

The remaining Iter-1 items still require inline artifact-generation prompts and an end-to-end sample feature run.
