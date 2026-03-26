---
name: ring:interview-me
description: Proactive requirements gathering through structured user interview
argument-hint: "[topic]"
---

Surface ambiguities and gather requirements BEFORE implementation begins. This command inverts the typical flow: instead of you anticipating what Claude might misunderstand, Claude proactively interviews you to build a complete picture.

## Usage

```
/ring:interview-me [topic]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `topic` | No | The feature, task, or area to gather requirements for. If omitted, Claude analyzes current context. |

## Examples

### Before Starting a Feature
```
/ring:interview-me user notifications
```
Claude interviews you about notification types, delivery channels, preferences, etc.

### When Claude Seems Confused
```
/ring:interview-me
```
Claude analyzes the current conversation and surfaces its uncertainties.

### Before Architecture Decisions
```
/ring:interview-me database migration strategy
```
Claude gathers constraints, timelines, compatibility requirements, etc.

## What Happens

1. **Context Analysis** - Claude analyzes the task/topic and identifies ambiguities
2. **Question Clustering** - Questions are grouped by priority (blocking → architecture → behavior → preference)
3. **Structured Interview** - Claude asks questions using structured choices (2-4 options each)
4. **Understanding Summary** - Claude presents a "Validated Understanding" document
5. **Confirmation** - You confirm or correct, then Claude proceeds with implementation

## Question Budget

- **Maximum 4 questions per round** (AskUserQuestion tool limit)
- **Maximum 3 rounds** (respects your time)
- **Fewer is better** - Claude should explore before asking

## Output: Validated Understanding

After the interview, Claude presents:

```markdown
## Validated Understanding

### What We're Building
[1-2 sentence summary]

### Key Decisions Made
| Decision | Choice | Rationale |
|----------|--------|-----------|

### Constraints Confirmed
- [List of constraints]

### Out of Scope (Explicit)
- [Things we're NOT doing]
```

You must explicitly confirm this before Claude proceeds.

## When to Use This Command

| Scenario | Use /ring:interview-me? |
|----------|-------------------|
| Starting a new feature with vague requirements | ✅ Yes |
| Claude made wrong assumptions previously | ✅ Yes |
| Multiple valid approaches, unclear which to pick | ✅ Yes |
| Architecture decisions without clear direction | ✅ Yes |
| Simple bug fix with clear reproduction | ❌ No |
| Following an existing detailed plan | ❌ No |
| Single clarifying question needed | ❌ No (just ask) |

## Related Commands/Skills

| Command/Skill | Relationship |
|---------------|--------------|
| `ring:doubt-triggered-questions` pattern | For single questions during work |
| `/ring:brainstorm` | Use AFTER interview to explore solutions |
| `/ring:write-plan` | Use AFTER interview to create implementation plan |

## Troubleshooting

### "Too many questions"
Claude should explore the codebase before asking. If you're being bombarded with questions, tell Claude to "explore first, then ask only what you can't figure out."

### "Questions are too vague"
Good questions have 2-4 concrete options with descriptions. If you're getting open-ended questions, ask Claude to "provide specific options."

### "Claude keeps asking about things I already said"
Remind Claude to re-read the conversation. The interview should build on what's already known, not repeat it.

### "I want Claude to just decide"
Say "use your judgment" or "pick whatever fits best." Claude will make a choice and document the assumption.

---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: ring:interviewing-user
```

The skill contains the complete workflow with:
- Context analysis methodology
- Question clustering by priority
- Structured interview patterns
- Validated Understanding template
- Auto-trigger conditions
