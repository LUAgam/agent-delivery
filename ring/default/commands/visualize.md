---
name: ring:visualize
description: Generate beautiful, self-contained HTML pages that visually explain systems, code, and data
argument-hint: "[topic-or-description]"
---

Generate a self-contained, Lerian-branded HTML page that visually explains a system, codebase, data set, or technical concept. Outputs styled diagrams, tables, architecture overviews, diff reviews, and more -- opened directly in the browser.

## Usage

```
/ring:visualize [topic-or-description]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `topic-or-description` | Yes | What to visualize. Can be a system name, a file path, a concept, or a description of what you want to see (e.g., "auth service architecture", "compare REST vs gRPC", "diff of last refactor") |

## Examples

### Architecture Overview
```
/ring:visualize payment service architecture
```
Generates a branded HTML page with a system diagram showing components, data flow, and dependencies of the payment service.

### Data Comparison Table
```
/ring:visualize compare deployment strategies: blue-green vs canary vs rolling
```
Produces a styled comparison table with pros, cons, and use cases for each strategy -- rendered in the browser instead of a hard-to-read ASCII table.

### Code Diff Review
```
/ring:visualize diff review of the auth module refactor
```
Creates an interactive code diff page using `@pierre/diffs` with syntax highlighting, severity badges, and a sidebar TOC for each finding.

## Process

When you run this command:

1. **Think** -- determines the audience, diagram type, and visual aesthetic (editorial, blueprint, neon dashboard, etc.)
2. **Structure** -- reads the mandatory Lerian standard template (`standard.html`) and the diagram-specific reference template (architecture, data-table, mermaid-flowchart, or code-diff)
3. **Style** -- applies the Lerian brand foundation (Inter font, sunglow accent, zinc neutrals) with diagram-specific customizations on top
4. **Deliver** -- writes the self-contained HTML file to `~/.agent/diagrams/` and opens it in the browser

Supported visualization types include: architecture overviews, flowcharts, sequence diagrams, ER/schema diagrams, state machines, mind maps, data tables, timelines, dashboards, and code diff reviews.

## Related Commands/Skills

| Command/Skill | Relationship |
|---------------|--------------|
| `ring:drawing-diagrams` | Lightweight alternative -- generates shareable mermaid.live URLs instead of full HTML pages |
| `/ring:md-to-html` | Converts an existing markdown file into a styled HTML page using the same visual engine |
| `ring:visual-explainer` | The full skill powering this command |

## When NOT to Use

- Data fits in a small table (2 columns, 3 rows) -- just render it inline
- You only need a quick, shareable Mermaid link -- use `ring:drawing-diagrams` instead
- The user explicitly asks for plain markdown output

---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: ring:visual-explainer
```

The skill contains the complete workflow with:
- Standard template loading and brand compliance
- Diagram type selection and rendering approach matrix
- Reference file reading requirements per diagram type
- Quality checks and overflow protection
- AI-generated illustration support (via surf-cli)
