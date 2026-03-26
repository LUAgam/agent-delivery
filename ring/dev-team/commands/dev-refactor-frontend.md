---
name: ring:dev-refactor-frontend
description: Analyze existing frontend codebase against standards and execute refactoring through ring:dev-cycle-frontend
argument-hint: "[path] [options] [prompt]"
---

Analyze existing frontend codebase against standards and execute refactoring through ring:dev-cycle-frontend.

## PRE-EXECUTION CHECK (EXECUTE FIRST)

**Before loading the skill, you MUST check:**

```
Does docs/PROJECT_RULES.md exist in the target project?
+-- YES -> Load skill: ring:dev-refactor-frontend
+-- NO  -> Output blocker below and STOP
```

**If file does not exist, output this EXACT response:**

```markdown
## HARD BLOCK: PROJECT_RULES.md Not Found

**Status:** BLOCKED - Cannot proceed

### Required Action
Create `docs/PROJECT_RULES.md` with your project's:
- Architecture patterns
- Code conventions
- Testing requirements
- DevOps standards

Then re-run `/ring:dev-refactor-frontend`.
```

**DO NOT:**
- Use "default" or "industry" standards
- Infer standards from existing code
- Proceed with partial analysis
- Offer to create the file

---

## Usage

```
/ring:dev-refactor-frontend [path] [options] [prompt]
/ring:dev-refactor-frontend [prompt]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | No | Directory to analyze (default: current project root) |
| `prompt` | No | Direct instruction for refactoring focus (no quotes needed) |

## Options

| Option | Description | Example |
|--------|-------------|---------|
| `--standards PATH` | Custom standards file | `--standards docs/MY_PROJECT_RULES.md` |
| `--analyze-only` | Generate report without executing | `--analyze-only` |
| `--critical-only` | Limit execution/output to Critical and High (analysis still tracks all) | `--critical-only` |
| `--dry-run` | Show what would be analyzed | `--dry-run` |

## Examples

```bash
# Direct prompt - focus refactoring on specific area
/ring:dev-refactor-frontend Focus on accessibility compliance and WCAG AA violations

# Direct prompt - another example
/ring:dev-refactor-frontend Check component patterns against sindarian-ui and remove shadcn duplicates

# Analyze entire frontend project and refactor
/ring:dev-refactor-frontend

# Analyze specific directory
/ring:dev-refactor-frontend src/components

# Analyze with performance focus
/ring:dev-refactor-frontend src/ Focus on Core Web Vitals and bundle size optimization

# Analysis only (no execution)
/ring:dev-refactor-frontend --analyze-only

# Only fix critical issues
/ring:dev-refactor-frontend --critical-only

# Use custom standards with focus
/ring:dev-refactor-frontend --standards docs/team-standards.md Prioritize testing gaps
```

## Workflow

**See skill `ring:dev-refactor-frontend` for the complete workflow with TodoWrite template.**

The skill defines all steps including: frontend stack detection, UI library mode detection, ring:codebase-explorer dispatch, individual agent reports, finding mapping, gate escape detection, and artifact generation.

## Analysis Dimensions

**All seven dimensions are MANDATORY for analysis/tracking. The `--critical-only` flag filters execution/output only.**

| Dimension | What's Checked | Standards Reference |
|-----------|----------------|---------------------|
| **Component Architecture** | React patterns, App Router, Server vs Client components | `frontend.md` sections 1-3 |
| **UI Library Compliance** | sindarian-ui usage, duplication check | `frontend.md` section 14 |
| **Styling & Design** | Typography, animations, CSS patterns | `frontend.md` sections 5-7 |
| **Accessibility** | WCAG 2.1 AA, semantic HTML, keyboard, ARIA | `frontend/testing-accessibility.md` |
| **Testing** | Unit coverage, visual snapshots, E2E, performance | `frontend/testing-*.md` |
| **Performance** | Core Web Vitals, Lighthouse, bundle, server components | `frontend/testing-performance.md` |
| **DevOps** | Dockerfile, docker-compose, Nginx, CI/CD | `devops.md` |

**Analysis vs Execution:**
- **Analysis (always):** All seven dimensions analyzed, all severities (Critical, High, Medium, Low) tracked
- **Execution (filterable):** `--critical-only` limits execution/prioritization to Critical and High severity issues

Example: `/ring:dev-refactor-frontend --critical-only` analyzes all issues but only executes fixes for Critical and High.

## Output

**Timestamp format:** `{timestamp}` = `YYYY-MM-DDTHH:MM:SS` (e.g., `2026-02-10T15:30:00`)

**Codebase Report** (`docs/ring:dev-refactor-frontend/{timestamp}/codebase-report.md`):
- Project architecture and structure analysis
- Component patterns and library usage

**Agent Reports** (`docs/ring:dev-refactor-frontend/{timestamp}/reports/`):
- Individual analysis from each dispatched agent (5-7 agents)
- Standards Coverage Tables per agent

**Findings** (`docs/ring:dev-refactor-frontend/{timestamp}/findings.md`):
- All findings with severity, category, file:line references
- Gate escape detection (maps to 9-gate frontend cycle)

**Tasks File** (`docs/ring:dev-refactor-frontend/{timestamp}/tasks.md`):
- 1:1 mapped REFACTOR-XXX tasks from findings
- Compatible with ring:dev-cycle-frontend execution

## Severity Levels (all ARE MANDATORY)

| Level | Description | Priority | Tracking |
|-------|-------------|----------|----------|
| **Critical** | Accessibility violations, security risks, production crashes | Fix immediately | **MANDATORY** |
| **High** | Architecture violations, major performance regressions | Fix in current sprint | **MANDATORY** |
| **Medium** | Convention violations, moderate testing gaps | Fix in next sprint | **MANDATORY** |
| **Low** | Style issues, minor optimization opportunities | Fix when capacity | **MANDATORY** |

**all severities are MANDATORY to track and fix. Low is not Optional. Low = Lower priority, still required.**

## Prerequisites

1. **PROJECT_RULES.md (MANDATORY)**: `docs/PROJECT_RULES.md` MUST exist - no defaults, no fallback
2. **Frontend project**: `package.json` with React/Next.js in dependencies (redirects to `ring:dev-refactor` otherwise)
3. **Git repository**: Project should be under version control
4. **Readable codebase**: Access to source files

**If PROJECT_RULES.md does not exist:** This command will output a blocker message and terminate.
**If not a frontend project:** This command will redirect to `/ring:dev-refactor`.

## Related Commands

| Command | Description |
|---------|-------------|
| `/ring:dev-cycle-frontend` | Execute frontend development cycle (used after analysis) |
| `/ring:dev-refactor` | Analyze backend/general codebase (use for non-frontend) |
| `/ring:pre-dev-feature` | Plan new features (use instead for greenfield) |
| `/ring:codereview` | Manual code review (ring:dev-cycle-frontend includes this) |

---

## MANDATORY: Load Full Skill

**After PROJECT_RULES.md check passes, load the skill:**

```
Use Skill tool: ring:dev-refactor-frontend
```

The skill contains the complete analysis workflow with:
- Anti-rationalization tables for codebase exploration
- Mandatory use of `ring:codebase-explorer` (not Bash/Explore)
- Standards coverage table requirements
- Frontend-specific gate escape detection (9-gate cycle)
- Finding -> Task mapping gates
- Full agent dispatch prompts with `**MODE: ANALYSIS only**`
- Handoff to `ring:dev-cycle-frontend` (not `ring:dev-cycle`)

## Execution Context

Pass the following context to the skill:

| Parameter | Value |
|-----------|-------|
| `path` | First argument if it's a directory path (default: project root) |
| `prompt` | Remaining text after path and options (direct instruction for focus) |
| `--standards` | If provided, custom standards file path |
| `--analyze-only` | If provided, skip ring:dev-cycle-frontend execution |
| `--critical-only` | If provided, filter to Critical/High only |
| `--dry-run` | If provided, show what would be analyzed |

**Argument Parsing:**
- If first argument is a path (contains `/` or is a known directory) -> treat as path
- If first argument is an option (`--*`) -> no path specified
- Remaining non-option text -> prompt (refactoring focus)

## User Approval (MANDATORY)

**Before executing ring:dev-cycle-frontend, you MUST ask:**

```yaml
AskUserQuestion:
  questions:
    - question: "Review frontend refactoring plan. How to proceed?"
      header: "Approval"
      options:
        - label: "Approve all"
          description: "Proceed to ring:dev-cycle-frontend execution"
        - label: "Critical only"
          description: "Execute only Critical/High tasks"
        - label: "Cancel"
          description: "Keep analysis, skip execution"
```

## Quick Reference

See skill `ring:dev-refactor-frontend` for full details. Key rules:

- **All agents dispatch in parallel** - Single message, multiple Task calls
- **MODE: ANALYSIS only** - Agents analyze, they DO NOT implement
- **Save artifacts** to `docs/ring:dev-refactor-frontend/{timestamp}/`
- **Get user approval** before executing ring:dev-cycle-frontend
- **Handoff**: `ring:dev-cycle-frontend docs/ring:dev-refactor-frontend/{timestamp}/tasks.md`
