# The Complete Guide to Building Skills for Claude

> Source: Anthropic official guide (January 2026)

---

## Introduction

A **skill** is a set of instructions — packaged as a simple folder — that teaches Claude how to handle specific tasks or workflows. Instead of re-explaining your preferences, processes, and domain expertise in every conversation, skills let you teach Claude once and benefit every time.

Skills work well for repeatable workflows: generating frontend designs from specs, conducting research with consistent methodology, creating documents that follow your team's style guide, or orchestrating multi-step processes.

**What you'll learn:**

- Technical requirements and best practices for skill structure
- Patterns for standalone skills and MCP-enhanced workflows
- How to test, iterate, and distribute your skills

**Two Paths Through This Guide:**

- Building standalone skills → Focus on Fundamentals, Planning and Design, categories 1–2
- Enhancing an MCP integration → Focus on "Skills + MCP" section and category 3

---

## Chapter 1: Fundamentals

### What is a skill?

A skill is a folder containing:

- **SKILL.md** (required): Instructions in Markdown with YAML frontmatter
- **scripts/** (optional): Executable code (Python, Bash, etc.)
- **references/** (optional): Documentation loaded as needed
- **assets/** (optional): Templates, fonts, icons used in output

### Core design principles

#### Progressive Disclosure

Skills use a three-level system:

- **First level (YAML frontmatter):** Always loaded in the system prompt. Provides just enough for Claude to know when to use the skill.
- **Second level (SKILL.md body):** Loaded when Claude thinks the skill is relevant. Contains full instructions.
- **Third level (Linked files):** Additional files in the skill directory that Claude navigates only as needed.

This minimizes token usage while maintaining specialized expertise.

#### Composability

Claude can load multiple skills simultaneously. Your skill should work well alongside others.

#### Portability

Skills work identically across Claude.ai, Claude Code, and API — create once, works everywhere.

### Skills + MCP: The kitchen analogy

| MCP (Connectivity) | Skills (Knowledge) |
|---|---|
| Connects Claude to your service | Teaches Claude how to use it effectively |
| Provides real-time data access and tool invocation | Captures workflows and best practices |
| **What** Claude can do | **How** Claude should do it |

**Without skills:** Users connect MCP but don't know what to do. Support tickets. Inconsistent results.  
**With skills:** Pre-built workflows activate automatically. Best practices embedded. Lower learning curve.

---

## Chapter 2: Planning and Design

### Start with use cases

Before writing any code, identify 2–3 concrete use cases your skill should enable.

**Good use case definition:**

```
Use Case: Project Sprint Planning
Trigger: User says "help me plan this sprint" or "create sprint tasks"
Steps:
  1. Fetch current project status from Linear (via MCP)
  2. Analyze team velocity and capacity
  3. Suggest task prioritization
  4. Create tasks in Linear with proper labels and estimates
Result: Fully planned sprint with tasks created
```

**Ask yourself:**

- What does a user want to accomplish?
- What multi-step workflows does this require?
- Which tools are needed (built-in or MCP)?
- What domain knowledge or best practices should be embedded?

### Common skill use case categories

#### Category 1: Document & Asset Creation

For creating consistent, high-quality output: documents, presentations, apps, designs, code, etc.

*Example: frontend-design skill*

**Key techniques:**

- Embedded style guides and brand standards
- Template structures for consistent output
- Quality checklists before finalizing
- No external tools required — uses Claude's built-in capabilities

#### Category 2: Workflow Automation

For multi-step processes that benefit from consistent methodology.

*Example: skill-creator skill*

**Key techniques:**

- Step-by-step workflow with validation gates
- Templates for common structures
- Built-in review and improvement suggestions
- Iterative refinement loops

#### Category 3: MCP Enhancement

For workflow guidance on top of MCP tool access.

*Example: sentry-code-review skill*

**Key techniques:**

- Coordinates multiple MCP calls in sequence
- Embeds domain expertise
- Provides context users would otherwise need to specify
- Error handling for common MCP issues

### Define success criteria

**Quantitative metrics (aspirational targets):**

- Skill triggers on 90% of relevant queries
- Completes workflow in expected number of tool calls
- 0 failed API calls per workflow

**Qualitative metrics:**

- Users don't need to prompt Claude about next steps
- Workflows complete without user correction
- Consistent results across sessions
- New user can accomplish the task on first try

### Technical requirements

#### File structure

```
your-skill-name/
├── SKILL.md              # Required
├── scripts/              # Optional — executable code
│   ├── process_data.py
│   └── validate.sh
├── references/           # Optional — documentation
│   ├── api-guide.md
│   └── examples/
└── assets/               # Optional — templates, etc.
    └── report-template.md
```

#### Critical rules

- `SKILL.md` must be exactly that (case-sensitive)
- Skill folder: kebab-case (`notion-project-setup` ✅, no spaces, no underscores, no capitals)
- No `README.md` inside the skill folder — all docs go in SKILL.md or references/

### YAML frontmatter: The most important part

**Minimal required format:**

```yaml
---
name: your-skill-name
description: What it does. Use when user asks to [specific phrases].
---
```

#### Field requirements

**`name`** (required):
- kebab-case only, no spaces or capitals, should match folder name

**`description`** (required):
- **MUST include BOTH:** what the skill does + when to use it (trigger conditions)
- Under 1024 characters
- No XML tags (< or >)
- Include specific phrases users might say
- Mention file types if relevant

**`license`** (optional): MIT, Apache-2.0, etc.

**`compatibility`** (optional, 1–500 chars): environment requirements, required packages, network needs

**`metadata`** (optional):
```yaml
metadata:
    author: ProjectHub
    version: 1.0.0
    mcp-server: projecthub
```

#### Security restrictions

- No XML angle brackets (< >) in frontmatter
- Skills with "claude" or "anthropic" in name are reserved

### Writing effective descriptions

**Structure:** `[What it does] + [When to use it] + [Key capabilities]`

**Good examples:**

```yaml
# Specific and actionable
description: Analyzes Figma design files and generates developer handoff documentation. Use when user uploads .fig files, asks for "design specs", "component documentation", or "design-to-code handoff".

# Includes trigger phrases
description: Manages Linear project workflows including sprint planning, task creation, and status tracking. Use when user mentions "sprint", "Linear tasks", "project planning", or asks to "create tickets".
```

**Bad examples:**

```yaml
# Too vague
description: Helps with projects.

# Missing triggers
description: Creates sophisticated multi-page documentation systems.
```

### Writing the main instructions

**Recommended structure:**

```markdown
---
name: your-skill
description: [...]
---

# Your Skill Name

## Instructions

### Step 1: [First Major Step]
Clear explanation of what happens.

```bash
python scripts/fetch_data.py --project-id PROJECT_ID
Expected output: [describe what success looks like]
```

### Examples

**Example 1: [common scenario]**

User says: "Set up a new marketing campaign"

Actions:
1. Fetch existing campaigns via MCP
2. Create new campaign with provided parameters

Result: Campaign created with confirmation link

### Troubleshooting

**Error: [Common error message]**
**Cause:** [Why it happens]
**Solution:** [How to fix]
```

#### Best practices for instructions

**Be specific and actionable:**

```
✅ Run `python scripts/validate.py --input {filename}`.
   If validation fails, common issues:
   - Missing required fields
   - Invalid date formats (use YYYY-MM-DD)

❌ Validate the data before proceeding.
```

**Include error handling:**

```markdown
## Common Issues

### MCP Connection Failed
If you see "Connection refused":
1. Verify MCP server is running
2. Confirm API key is valid
3. Try reconnecting
```

**Use progressive disclosure:** Keep SKILL.md focused on core instructions. Move detailed docs to `references/` and link to them.

---

## Chapter 3: Testing and Iteration

Three levels of rigor:

- **Manual testing in Claude.ai** — Fast iteration, no setup
- **Scripted testing in Claude Code** — Automated, repeatable
- **Programmatic testing via Skills API** — Full evaluation suites

> **Pro Tip:** Iterate on a single challenging task until Claude succeeds, then extract the winning approach into a skill. Faster signal than broad testing.

### Test areas

#### 1. Triggering tests

```
Should trigger:
- "Help me set up a new ProjectHub workspace"
- "I need to create a project in ProjectHub"

Should NOT trigger:
- "What's the weather in San Francisco?"
- "Help me write Python code"
```

#### 2. Functional tests

```
Test: Create project with 5 tasks
Given: Project name "Q4 Planning", 5 task descriptions
Then:
  - Project created
  - 5 tasks created with correct properties
  - No API errors
```

#### 3. Performance comparison

Compare with/without skill:
- Number of back-and-forth messages
- Failed API calls
- Tokens consumed
- Time to completion

### Iteration based on feedback

| Signal | Cause | Solution |
|---|---|---|
| Skill doesn't load automatically | Undertriggering | Add more keywords/phrases to description |
| Skill loads for unrelated queries | Overtriggering | Add negative triggers, be more specific |
| Inconsistent results or failures | Execution issues | Improve instructions, add error handling |

---

## Chapter 4: Distribution and Sharing

### How users get skills

1. Download the skill folder
2. Zip the folder
3. Upload to Claude.ai via Settings > Capabilities > Skills
4. Or place in Claude Code skills directory

Organization-level: Admins can deploy skills workspace-wide with automatic updates.

### An open standard

Skills are published as an open standard. Like MCP, they should be portable across tools and platforms.

### Recommended approach

1. **Host on GitHub** — public repo, clear README (separate from skill folder), example usage with screenshots
2. **Document in your MCP repo** — link to skills, explain the value of using both together
3. **Create an installation guide**

**Installation guide example:**

```
1. Clone repo: git clone https://github.com/yourcompany/skills
2. Open Claude.ai > Settings > Skills > Upload skill
3. Select the skill folder (zipped)
4. Toggle on the skill and ensure MCP is connected
5. Test: "Set up a new project in [Your Service]"
```

### Positioning your skill

Focus on outcomes, not features:

```
✅ "The ProjectHub skill enables teams to set up complete project workspaces
   in seconds instead of spending 30 minutes on manual setup."

❌ "The ProjectHub skill is a folder containing YAML frontmatter and
   Markdown instructions that calls our MCP server tools."
```

---

## Chapter 5: Patterns and Troubleshooting

### Problem-first vs. Tool-first

- **Problem-first:** User describes outcome → skill orchestrates the right MCP calls
- **Tool-first:** User has MCP connected → skill provides expertise and best practices

### Pattern 1: Sequential Workflow Orchestration

Use when: Users need multi-step processes in a specific order.

```markdown
## Workflow: Onboard New Customer

### Step 1: Create Account
Call MCP tool: `create_customer`
Parameters: name, email, company

### Step 2: Setup Payment
Call MCP tool: `setup_payment_method`
Wait for: payment method verification

### Step 3: Create Subscription
Call MCP tool: `create_subscription`
Parameters: plan_id, customer_id (from Step 1)
```

**Key techniques:** explicit step ordering, dependencies, validation at each stage, rollback instructions.

### Pattern 2: Multi-MCP Coordination

Use when: Workflows span multiple services.

```markdown
### Phase 1: Design Export (Figma MCP)
### Phase 2: Asset Storage (Drive MCP)
### Phase 3: Task Creation (Linear MCP)
### Phase 4: Notification (Slack MCP)
```

**Key techniques:** clear phase separation, data passing between MCPs, centralized error handling.

### Pattern 3: Iterative Refinement

Use when: Output quality improves with iteration.

```markdown
## Iterative Report Creation

### Initial Draft → Quality Check → Refinement Loop → Finalization

# Quality Check:
# - Run validation script
# - Identify missing sections, formatting issues, data errors
# Repeat until quality threshold met
```

### Pattern 4: Context-Aware Tool Selection

Use when: Same outcome, different tools depending on context.

```markdown
## Smart File Storage

### Decision Tree
- Large files (>10MB): cloud storage MCP
- Collaborative docs: Notion/Docs MCP
- Code files: GitHub MCP
- Temporary: local storage
```

### Pattern 5: Domain-Specific Intelligence

Use when: Your skill adds specialized knowledge beyond tool access.

```markdown
## Payment Processing with Compliance

### Before Processing (Compliance Check)
1. Fetch transaction details via MCP
2. Apply compliance rules (sanctions, jurisdiction, risk level)
3. Document compliance decision

IF compliance passed:
    Process transaction
ELSE:
    Flag for review, create compliance case

### Audit Trail
Log all checks, record decisions, generate audit report
```

### Troubleshooting

#### Skill won't upload

**"Could not find SKILL.md"** → File not named exactly SKILL.md (case-sensitive)

**"Invalid frontmatter"** → YAML formatting issue
```yaml
# Wrong — missing delimiters
name: my-skill

# Correct
---
name: my-skill
description: Does things
---
```

**"Invalid skill name"** → Name has spaces or capitals
```yaml
# Wrong
name: My Cool Skill
# Correct
name: my-cool-skill
```

#### Skill doesn't trigger

Quick checklist:
- Is the description too generic?
- Does it include trigger phrases users would actually say?
- Does it mention relevant file types?

**Debug:** Ask Claude: "When would you use the [skill name] skill?" → It quotes the description back. Adjust accordingly.

#### Skill triggers too often

Add negative triggers:
```yaml
description: Advanced data analysis for CSV files. Use for statistical modeling,
regression, clustering. Do NOT use for simple data exploration (use data-viz skill).
```

#### MCP connection issues

1. Verify MCP server is connected (Settings > Extensions)
2. Check authentication — API keys valid, OAuth tokens refreshed
3. Test MCP independently without the skill first
4. Verify tool names (case-sensitive)

#### Instructions not followed

Common causes:
- Instructions too verbose → use bullet points, move details to references/
- Critical instructions buried → put them at top, use `## Critical:` headers
- Ambiguous language → be explicit with `CRITICAL:` and numbered steps
- Model "laziness" → add explicit encouragement in **user prompts** (more effective than in SKILL.md)

#### Large context issues

- Keep SKILL.md under 5,000 words
- Move detailed docs to `references/`
- Evaluate if too many skills are enabled simultaneously (consider >20–50 as a threshold)

---

## Chapter 6: Resources and References

**Anthropic official docs:**

- [Best Practices Guide](https://docs.anthropic.com)
- [Skills Documentation](https://docs.anthropic.com)
- [API Reference](https://docs.anthropic.com/api)
- [MCP Documentation](https://modelcontextprotocol.io)

**Example skills:**

- GitHub: `anthropics/skills` — official Anthropic-created skills to customize

**Tools:**

- `skill-creator` skill — built into Claude.ai and Claude Code; generates skills from descriptions, reviews and recommends improvements
- Use: "Help me build a skill using skill-creator"

**Community:**

- Claude Developers Discord: community forums for technical questions
- Bug reports: `anthropics/skills/issues` on GitHub
