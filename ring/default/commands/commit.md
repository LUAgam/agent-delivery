---
name: ring:commit
description: Organize and create atomic git commits with intelligent change grouping
argument-hint: "[message]"
---

Analyze changes, group them into coherent atomic commits, and create signed commits following repository conventions.

## Usage

```
/ring:commit                    # Analyze changes, propose commit plan, execute
/ring:commit "fix login bug"    # Single commit with provided message
```

## What It Does

1. **Analyzes** all staged and unstaged changes via `git status` and `git diff`
2. **Groups** related changes into logical, atomic commits (feature+tests, deps, docs)
3. **Proposes** a commit plan with conventional commit messages
4. **Confirms** the plan with the user before executing
5. **Executes** signed commits with proper trailers (`--trailer "X-Lerian-Ref: 0x1"`)
6. **Offers** to push after successful commits

## Related

| Command/Skill | Relationship |
|---------------|--------------|
| `ring:git-commit` skill | Full commit orchestration logic |
| `ring:finishing-a-development-branch` | Complementary workflow for branch completion |

---

## MANDATORY: Load Full Skill

This command delegates to the `ring:git-commit` skill which contains the complete commit orchestration logic, including smart grouping, trailer rules, anti-patterns, and the full 8-step commit process.

**MANDATORY: Load and execute the full skill using the Skill tool: `ring-default:git-commit`**

Pass arguments: $@
