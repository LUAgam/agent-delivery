---
name: ring:delivery-report
description: Generate visual executive presentation of squad deliveries from Git repository analysis
argument-hint: "[options]"
---

Generate visual executive presentation of squad deliveries (engineering, product, design) by analyzing Git repositories and extracting business value from technical changes.

## Usage

```
/delivery-report [options]
```

## Options

| Option | Required | Description | Example |
|--------|----------|-------------|---------|
| `--start-date` | Yes | Period start date | `--start-date 2026-01-12` |
| `--end-date` | Yes | Period end date | `--end-date 2026-01-31` |
| `--repos` | Yes | Comma-separated repositories (org/repo format) | `--repos "LerianStudio/midaz,LerianStudio/console"` |
| `--context` | No | Additional business context | `--context "Focus on Product Console launch"` |
| `--visual` | No | Visual identity (default: lerian) | `--visual lerian` or `ring` or `custom` |

## Repository Format

**Two supported formats:**

### Format 1: org/repo (RECOMMENDED)
```bash
--repos "LerianStudio/midaz,LerianStudio/product-console"
```
- Standard GitHub format
- Clear organization ownership
- Works for any organization

### Format 2: Full URLs (ALTERNATIVE)
```bash
--repos "https://github.com/LerianStudio/midaz,https://github.com/LerianStudio/product-console"
```
- Convenient when copying from browser
- Supports other Git hosts (GitLab, Bitbucket)
- Agent automatically extracts org/repo

**Invalid formats:**
- ❌ `midaz` (missing organization)
- ❌ `org/repo/subdir` (too many slashes)

**Error message example:**
```
ERROR: Invalid repository format: "midaz"
Use: org/repo (e.g., LerianStudio/midaz)
Or: Full URL (e.g., https://github.com/LerianStudio/midaz)
```

## Visual Identity Options

| Option | Description | Use Case |
|--------|-------------|----------|
| `lerian` | Lerian Studio branding (default) | Internal Lerian reports |
| `ring` | Ring neutral corporate style | Public/neutral branding |
| `custom` | User-provided color scheme | Client-specific branding |

**If `--visual custom` is selected, command will prompt for:**
- Background color (hex)
- Primary text color (hex)
- Secondary text color (hex)
- Accent color (hex)
- Font family

## Examples

### Basic Usage (Lerian branding)
```bash
/delivery-report \
  --start-date 2026-01-12 \
  --end-date 2026-01-31 \
  --repos "LerianStudio/midaz,LerianStudio/product-console"
```

### With Business Context
```bash
/delivery-report \
  --start-date 2026-01-01 \
  --end-date 2026-01-31 \
  --repos "LerianStudio/midaz,LerianStudio/product-console,LerianStudio/api-gateway" \
  --context "Q1 focus on security compliance and customer portal"
```

### Using Full URLs (alternative)
```bash
/delivery-report \
  --start-date 2026-01-12 \
  --end-date 2026-01-31 \
  --repos "https://github.com/LerianStudio/midaz,https://github.com/LerianStudio/product-console"
```

### Ring Neutral Branding
```bash
/delivery-report \
  --start-date 2026-01-12 \
  --end-date 2026-01-31 \
  --repos "LerianStudio/midaz" \
  --visual ring
```

### Custom Branding
```bash
/delivery-report \
  --start-date 2026-01-12 \
  --end-date 2026-01-31 \
  --repos "ClientOrg/client-app" \
  --visual custom
# Will prompt for colors and font
```

## Output

**Generated Files:**
- `docs/pmo/delivery-reports/{end-date}/delivery-report-{end-date}.html`
- `docs/pmo/delivery-reports/{end-date}/analysis-data.md` (raw data)
- `docs/pmo/delivery-reports/{end-date}/business-value.md` (extracted insights)

**HTML Report Includes:**
- Cover slide with key metrics
- Executive summary
- Deliveries by product/theme
- Next steps (based on active branches)
- Self-contained HTML (no external dependencies)
- Print-to-PDF ready

## Differences from /executive-summary

| Aspect | /delivery-report | /executive-summary |
|--------|------------------|-------------------|
| **Focus** | Squad deliveries (eng+product) | Portfolio/project status (PMO) |
| **Data Source** | Git repositories (tags, PRs, commits) | PMO data (RAG, SPI, CPI) |
| **Output** | Visual HTML slides | Markdown dashboard |
| **Metrics** | Releases, PRs, commits, velocity | Project status, budget, resources |
| **Audience** | Engineering/product executives | Portfolio executives |

**Use /delivery-report for:** "What did the squad deliver?"
**Use /executive-summary for:** "How is the portfolio doing?"

## Prerequisites

**Required Tools:**
- Git installed and configured
- GitHub CLI (`gh`) authenticated: `gh auth login`
- Repository access (clone permissions)

**Verify Setup:**
```bash
git --version              # Should show git version
gh auth status             # Should show "Logged in to github.com"
```

## Related Commands

| Command | Description | When to Use |
|---------|-------------|-------------|
| `/executive-summary` | Portfolio status report | For PMO/project status |
| `/portfolio-review` | Full portfolio review | Strategic portfolio analysis |
| `/dependency-analysis` | Cross-project dependencies | Dependency mapping |

---

## MANDATORY: Load Full Skill

**This command MUST load the delivery-reporting skill for complete workflow execution.**

```
Use Skill tool: ring:delivery-reporting
```

The skill contains the complete reporting workflow with:
- Input collection
- Repository analysis
- Business value extraction
- Slide generation
- Quality validation

## Execution Flow

### Step 1: Parse Arguments and Collect Inputs

```
1. Parse command-line arguments
2. Validate required arguments (start-date, end-date, repos)
3. If --visual custom, prompt for color scheme:
   - Background color (hex)
   - Primary text color (hex)
   - Secondary text color (hex)
   - Accent color (hex)
   - Font family
4. If visual identity not specified, use lerian (default)
```

### Step 2: Dispatch Delivery Reporter Agent

```
Task tool:
  subagent_type: "ring:delivery-reporter"
  prompt: |
    Create delivery report for period {start_date} to {end_date}.

    Repositories: {repo_list}
    Business context: {context}
    Visual identity: {visual_identity}

    {If custom, include custom_colors}

    Analyze Git repositories, extract business value, and generate
    HTML slide presentation following delivery-reporting skill workflow.
```

### Step 3: Verify Prerequisites

Before dispatching agent, verify:

```bash
# Check Git
if ! command -v git &> /dev/null; then
  ERROR: Git not installed. Install: https://git-scm.com/
fi

# Check GitHub CLI
if ! command -v gh &> /dev/null; then
  ERROR: GitHub CLI not installed. Install: https://cli.github.com/
fi

# Check gh auth
if ! gh auth status &> /dev/null; then
  ERROR: GitHub CLI not authenticated. Run: gh auth login
fi
```

### Step 4: Validate Output

After agent completes, verify:

```
1. HTML file exists at expected location
2. HTML renders properly in browser
3. Print-to-PDF works (test Ctrl+P / Cmd+P)
4. All requested repositories were analyzed
5. Metrics are present and non-zero (or explained if zero)
```

## Anti-Rationalization

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Skip visual identity, use default" | Branding matters. Always ask or use explicit default. | **Prompt for visual identity** |
| "Repos are optional, can skip" | Cannot analyze without repositories. | **Repos are REQUIRED** |
| "Git/gh not needed, can estimate" | Accurate data requires Git/gh. No estimates. | **Verify prerequisites** |
| "Skip HTML generation, markdown is fine" | HTML slides are the differentiator. | **Generate full HTML** |

## Error Handling

### Repository Not Found

```
ERROR: Repository not accessible
Repository: [repo-name]
Action: Verify repository name and access permissions
```

### No Data in Period

```
WARNING: No activity found
Period: {start_date} to {end_date}
Repositories: {repo_list}
Action: Verify date range or extend period
```

### GitHub CLI Not Authenticated

```
ERROR: GitHub CLI not authenticated
Command: gh auth login
Action: Authenticate and retry
```

### Custom Colors Missing

```
ERROR: Custom visual identity selected but colors missing
Required: background, text_primary, text_secondary, accent, font_family
Action: Provide all 5 values
```

## Output Format

### HTML Report Structure

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Delivery Report - [Period]</title>
  <style>/* Inline CSS with selected visual identity */</style>
</head>
<body>
  <div class="slide cover">
    <!-- Key metrics: New Products, Releases, PRs, Commits -->
    <!-- Agility metric: Releases per day -->
  </div>

  <div class="slide summary">
    <!-- Executive summary paragraph -->
    <!-- 3-4 main highlights -->
  </div>

  <div class="slide deliveries">
    <!-- Grouped by product/theme -->
    <!-- Business value statements -->
  </div>

  <div class="slide next-steps">
    <!-- Based on active branches -->
    <!-- 2-3 upcoming initiatives -->
  </div>

  <div class="slide closing">
    <!-- Thank you / Questions -->
  </div>
</body>
</html>
```

### Markdown Analysis Files

**analysis-data.md:**
```markdown
# Repository Analysis - {period}

## Repository: midaz

### Tags/Releases
- v1.2.1 (2026-01-15) - Bug fixes
- v1.2.0 (2026-01-10) - Feature release

### PRs Merged (count: 23)
1. #123 - Add OAuth support
2. #124 - Fix authentication bug
...

### Commits: 87

### Active Branches
- feature/payment-gateway (12 commits ahead)
- fix/performance-issue (3 commits ahead)
```

**business-value.md:**
```markdown
# Business Value Extraction - {period}

## Midaz Core

### Security Enhancements
**Technical:** Added OAuth 2.0 support
**Business Value:** Enhanced security compliance, protecting customer data from unauthorized access
**Impact:** 500+ clients now have stronger authentication

### Performance Improvements
**Technical:** Implemented Redis caching
**Business Value:** API response time improved by 40%, enhancing user experience
**Impact:** Faster page loads for all users
```

## Quality Standards

Report MUST meet these standards:

- [ ] All metrics are accurate (no estimates)
- [ ] Business value extracted for major deliveries
- [ ] No technical jargon in executive summary
- [ ] Visual identity applied correctly
- [ ] HTML is self-contained (no external deps)
- [ ] Print-to-PDF works properly
- [ ] Next steps identified from active branches
- [ ] Period and repositories clearly stated

**If any checkbox fails → Report quality is insufficient. Fix before delivery.**

## Performance Expectations

| Repositories | Expected Duration |
|--------------|-------------------|
| 1-2 repos | 5-10 minutes |
| 3-5 repos | 15-30 minutes |
| 6-7 repos | 30-60 minutes |
| 8+ repos | 40-80 minutes |

**Large repository analysis takes time. Be patient and let agent complete full analysis.**
