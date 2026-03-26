---
name: ring:create-handoff
description: Create a handoff document capturing current session state, with automatic context-clear and resume via Plan Mode
user_invocable: true
allowed-tools:
  - Skill
arguments:
  - name: session-name
    description: Short name for the session/feature (e.g., "auth-refactor")
    required: false
  - name: description
    description: Brief description of current work
    required: false
---

# /ring:create-handoff Command

Creates a comprehensive handoff document that captures the current session's context, progress, decisions, and next steps. Uses Plan Mode for seamless context-clear and resume.

## Usage

```
/ring:create-handoff [session-name] [description]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `session-name` | No | Short identifier for the session (defaults to feature/task name) |
| `description` | No | Brief description of current state |

## What It Does

1. Gathers context from conversation history (completed work, decisions, open items)
2. Saves an archival copy to `docs/handoffs/{session-name}/{timestamp}_{description}.md`
3. Enters Plan Mode and writes the handoff as the active plan
4. Exits Plan Mode, presenting native "clear context and continue implementing" options
5. User can seamlessly resume in a fresh context with the handoff loaded as their plan

This command delegates to the `ring:session-handoff` skill which contains the complete handoff creation logic, execution protocol, handoff template, and anti-rationalization table.

---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: ring-default:session-handoff
```

The skill contains the complete workflow with:
- 6-step execution protocol (gather, archive, plan mode enter, write, exit, confirm)
- Full handoff document template (11 sections)
- Anti-rationalization table
- Plan Mode integration for seamless context-clear and resume
