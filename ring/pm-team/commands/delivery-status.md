---
name: ring:delivery-status
description: Track delivery progress against roadmap with evidence-based analysis
argument-hint: "[feature-name or roadmap-path]"
---

I'm running **Delivery Status Tracking** to analyze actual progress against your delivery roadmap.

## What This Command Does

Analyzes your repository to provide evidence-based status reporting:
- 📊 **Actual vs Planned**: Compare real progress with delivery roadmap dates
- 🔍 **Scope Validation**: Verify task completion via specialized code analysis
- 🚨 **Risk Alerts**: Identify delays, blockers, and critical path issues
- 📈 **Insights**: Velocity trends, quality patterns, review time analysis
- 🎯 **Evidence-Based**: Every metric backed by GitHub data (commits, PRs, branches)

## Required Inputs

This command will ask you for:

1. **Repository** - Which repo to analyze (org/repo format)
2. **Delivery Roadmap** - Path/link/content of delivery-roadmap.md
3. **Tasks File** - Path/link/content of tasks.md (REQUIRED)
4. **Subtasks File** (Optional) - For detailed scope analysis
5. **Current Date** (Optional) - Defaults to today, supports DD/MM/YYYY or YYYY-MM-DD

## Analysis Approach

### Comprehensive Repository Scan
- ✅ **ALL branches** (not just main)
- ✅ **ALL commits** (entire history)
- ✅ **ALL PRs** (open, closed, merged)
- ✅ **ALL releases** (version history)

### Intelligent Task Matching
1. **Pattern matching** (fast): Branch names, commit messages, PR titles
2. **Semantic analysis** (accurate): Specialized agents compare scope vs code

### Specialized Agent Dispatch
- **Go projects** → `ring:backend-engineer-golang`
- **Frontend projects** → `ring:frontend-engineer`
- **Full-stack** → Multiple agents per task type
- **Unknown** → `ring:codebase-explorer`

## Output

**File:** `docs/pre-dev/{feature-name}/delivery-status-{YYYY-MM-DD}.md`

**Contains:**
- Executive summary (progress %, variance, health)
- Task-by-task breakdown (status, evidence, scope analysis)
- Alerts (critical path delays, blockers, risks)
- Insights (velocity trends, bug rate, review time, code patterns)
- Evidence index (GitHub links to all analyzed data)

## Usage Examples

**Basic usage:**
```
/ring:delivery-status
→ Prompts for repository, roadmap, tasks
→ Analyzes and generates status report
```

**With feature name:**
```
/ring:delivery-status auth-system
→ Auto-finds docs/pre-dev/auth-system/delivery-roadmap.md
→ Auto-finds docs/pre-dev/auth-system/tasks.md
→ Prompts only for repository
```

**With custom date:**
```
/ring:delivery-status
→ Prompts for inputs
→ Asks for date: "15/03/2026" (Brazilian) or "2026-03-15" (ISO)
→ Calculates variance as of that date
```

## When to Run

- ✅ **Weekly checkpoints** - Regular progress tracking
- ✅ **Sprint/cycle end** - Period retrospective with data
- ✅ **Before stakeholder meeting** - Evidence-based status update
- ✅ **When roadmap deviates** - Understand actual vs planned
- ✅ **Critical path concerns** - Verify delays and impact

## Remember

- This analysis **requires time** (5-15 minutes for thorough scan)
- Uses **specialized agents** for accurate scope validation
- Provides **evidence links** - every metric is verifiable
- **Semantic analysis** ensures hidden work is found
- Report is **versioned** - compare multiple status reports to see trends

---

## MANDATORY: Skill Orchestration

**This command orchestrates the delivery status tracking skill.**

Use Skill tool: `ring:delivery-status-tracking`

The skill contains:
- Input gathering workflow (flexible sources)
- Repository scan logic (ALL branches, commits, PRs, releases)
- Task matching strategies (pattern + semantic)
- Specialized agent dispatch (per project type)
- Completion calculation (scope-based via agents)
- Report generation (markdown with evidence)

Do not skip semantic analysis for speed. Accuracy > velocity.
