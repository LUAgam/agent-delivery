---
name: ring:release-guide
description: Generate an Ops Update Guide from git diff between two refs
---

Generate an internal Operations-facing update/migration guide based on git diff analysis.

## Usage

```
/ring:release-guide
```

This command invokes the `ring:release-guide-info` skill, which will interactively collect all required information:
- Base ref (starting point)
- Target ref (ending point)
- Version (optional, auto-detected from tags)
- Language (en, pt-br, or both)
- Execution mode

## Output

The skill generates:
1. **Preview summary** - Shows configuration and change counts
2. **User confirmation** - Waits for approval before writing
3. **Release guide file(s)** - Written to `notes/releases/`

## Related

| Command/Skill | Relationship |
|---------------|--------------|
| `ring:release-guide-info` skill | Full workflow with all options |
| `/ring:commit` | Use after release guide to commit changes |
| `ring:finishing-a-development-branch` | Complementary workflow for branch completion |

---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: ring:release-guide-info
```

The skill contains the complete workflow with:
- Tag auto-detection and version resolution
- Commit log analysis for context
- Dual language support (English/Portuguese)
- Preview step before saving
- Anti-rationalization table
- Quality checklist
