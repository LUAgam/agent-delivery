---
name: ring:diagram
description: Generate Mermaid diagrams and open them in mermaid.live
argument-hint: "[description-or-topic]"
---

Generate Mermaid diagrams from a description or codebase context and open them as shareable mermaid.live URLs in the browser. Supports all Mermaid diagram types including flowcharts, sequence diagrams, ER diagrams, class diagrams, state machines, Gantt charts, and more.

## Usage

```
/ring:diagram [description-or-topic]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `description-or-topic` | No | What to diagram. Can be a topic, system name, or brief description (e.g., "auth flow", "database schema", "CI/CD pipeline"). If omitted, describe what you want in the conversation. |

## Options

Options are passed through to the skill:

| Option | Description |
|--------|-------------|
| `--theme` | Mermaid theme: `default`, `dark`, `forest`, `neutral` |
| `--view` | Open in view-only mode (no editor panel) |
| `--rough` | Hand-drawn sketchy style (nice for presentations) |

## Examples

### Architecture Flowchart
```
/ring:diagram microservices architecture for the payment system
```
Generates a flowchart showing service boundaries, communication patterns, and data flow.

### Database Schema
```
/ring:diagram ER diagram for the user and orders domain
```
Produces an entity-relationship diagram with tables, relationships, and cardinality.

### Sequence Diagram with Options
```
/ring:diagram OAuth2 login flow --theme dark --rough
```
Creates a hand-drawn-style sequence diagram of the OAuth2 flow with dark theme.

## Process

1. **Determines diagram type** -- picks the best Mermaid diagram type for the request (flowchart, sequence, ER, class, state, gantt, etc.)
2. **Writes Mermaid code** -- generates clean, well-structured Mermaid syntax
3. **Encodes and opens in browser** -- uses the bundled encoder to produce a mermaid.live URL and opens it
4. **Reports back** -- tells you what was generated, why that diagram type was chosen, and gives you the shareable URL

The resulting mermaid.live URL is permanent (the diagram state is encoded in the URL itself) and can be edited interactively in the browser.

## Related Commands/Skills

| Command/Skill | Relationship |
|---------------|--------------|
| `ring:visual-explainer` | Use for rich, branded HTML visualizations with Lerian styling |
| `/ring:md-to-html` | Use to convert a full markdown document into a styled HTML page with diagrams |
| `/ring:brainstorm` | Use before diagramming to refine a design concept |
| `/ring:explore-codebase` | Use to understand architecture before diagramming it |

## When NOT to Use

- You need a rich, branded, or styled HTML page -- use `ring:visual-explainer` or `/ring:md-to-html`
- You need to edit an existing diagram file -- just edit the Mermaid source directly
- You need a non-Mermaid format (PNG, SVG export) -- use mermaid.live's built-in export after opening

---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: ring:drawing-diagrams
```

The skill contains the complete workflow with:
- Diagram type selection matrix
- Full Mermaid syntax reference and best practices
- Encoder script invocation (Python 3, no dependencies)
- Design guidelines for readable, focused diagrams
