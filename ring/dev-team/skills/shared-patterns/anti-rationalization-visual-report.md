# Anti-Rationalization: Visual Change Report Generation

**MANDATORY: Visual HTML report MUST be generated before any user approval checkpoint.**

| Rationalization | Why It's Wrong | Required Action |
|-----------------|----------------|-----------------|
| "User can read the markdown output" | Markdown requires mental parsing. HTML provides visual severity, diffs, and interactive navigation. | **Generate HTML report** |
| "Too many findings for HTML" | Large reports benefit more from visual structure, not less. Collapsible sections handle scale. | **Generate HTML report** |
| "Template read slows execution" | Template patterns ensure consistent output quality. Skipping produces inconsistent HTML. | **Read template before generating** |
| "Report is informational, not blocking" | Report informs the approval decision. Skipping degrades decision quality. | **Generate before presenting approval question** |
| "Headless environment, no browser" | Still generate and save the file. User can open it later or transfer it. | **Generate and save; skip open command only if no display** |
| "Previous report already covers this" | Each checkpoint is independent. New data may have changed. | **Generate fresh report at each checkpoint** |
