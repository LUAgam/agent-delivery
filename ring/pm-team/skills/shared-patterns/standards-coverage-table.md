# Standards Coverage Table Pattern

This file defines the MANDATORY output format for agents comparing designs against Ring product design standards. It ensures every section in the standards is explicitly checked and reported.

---

## ⛔ CRITICAL: All Sections Are Required

**This is NON-NEGOTIABLE. Every section listed in the Agent → Standards Section Index below MUST be checked.**

| Rule                                          | Enforcement                                                                             |
| --------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Every section MUST be checked**             | No exceptions. No skipping.                                                             |
| **Every section MUST appear in output table** | Missing row = INCOMPLETE output                                                         |
| **Subsections are INCLUDED**                  | If "Accessibility Requirements" is listed, all content (WCAG, checklist) MUST be checked |
| **N/A requires explicit reason**              | Cannot mark N/A without justification                                                   |

**If you skip any section → Your output is REJECTED. Start over.**

**If you invent section names → Your output is REJECTED. Start over.**

---

## ⛔ CRITICAL: Section Names Are Not Negotiable

**You MUST use the EXACT section names from this file. You CANNOT:**

| FORBIDDEN         | Example                                          | Why Wrong              |
| ----------------- | ------------------------------------------------ | ---------------------- |
| Invent names      | "Design Quality", "UX Compliance"                | Not in coverage table  |
| Rename sections   | "Wireframes" instead of "Wireframe Format"       | Breaks traceability    |
| Merge sections    | "Accessibility & Responsive"                     | Each section = one row |
| Use abbreviations | "A11y" instead of "Accessibility Requirements"   | Must match exactly     |
| Skip sections     | Omitting "ASCII Prototypes"                      | Mark N/A instead       |

**Your output table section names MUST match the "Section to Check" column below EXACTLY.**

---

## Why This Pattern Exists

**Problem:** Agents might skip sections from standards files, either by:

- Only checking "main" sections
- Assuming some sections don't apply
- Not enumerating all sections systematically
- Skipping subsections (e.g., checking WCAG but skipping responsive breakpoints)

**Solution:** Require a completeness table that MUST list every section from the standards file with explicit status. All content within each section MUST be evaluated.

---

## MANDATORY: Standards Coverage Table

### ⛔ HARD GATE: Before Outputting Findings

**You MUST output a Standards Coverage Table that enumerates every section from the standards file.**

**REQUIRED: When checking a section, you MUST check all subsections and patterns within it.**

| Section                    | What MUST Be Checked                                                    |
| -------------------------- | ----------------------------------------------------------------------- |
| UX Research Methods        | Primary research methods and documentation format                       |
| Problem Validation         | Problem statement format and evidence requirements                      |
| Wireframe Format           | YAML structure, component types, state variations, responsive behavior  |
| Accessibility Requirements | WCAG 2.1 AA compliance and accessibility checklist                      |

### Process

1. **Parse the standards file** - Extract all `## Section` headers from product-design.md
2. **Count sections** - Record total number of sections found (13)
3. **For each section** - Determine status and evidence
4. **Output table** - MUST have one row per section
5. **Verify completeness** - Table row count MUST equal section count

### Output Format

```markdown
## Standards Coverage Table

**Standards File:** product-design.md
**Total Sections Found:** 13
**Table Rows:** 13 (MUST match)

| #   | Section (from standards) | Status       | Evidence            |
| --- | ------------------------ | ------------ | ------------------- |
| 1   | {Section 1 header}       | ✅/⚠️/❌/N/A | file:line or reason |
| 2   | {Section 2 header}       | ✅/⚠️/❌/N/A | file:line or reason |
| ... | ...                      | ...          | ...                 |
| 13  | {Section 13 header}      | ✅/⚠️/❌/N/A | file:line or reason |

**Completeness Verification:**

- Sections in standards: 13
- Rows in table: 13
- Status: ✅ Complete / ❌ Incomplete
```

### Status Legend

| Status           | Meaning                            | When to Use                          |
| ---------------- | ---------------------------------- | ------------------------------------ |
| ✅ Compliant     | Design follows this standard       | Design matches expected pattern      |
| ⚠️ Partial       | Some compliance, needs improvement | Partially addressed or minor gaps    |
| ❌ Non-Compliant | Does not follow standard           | Missing or incorrect specification   |
| N/A              | Not applicable to this feature     | Standard doesn't apply (with reason) |

---

## Anti-Rationalization Table

| Rationalization                                   | Why It's WRONG                                                         | Required Action                                   |
| ------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------- |
| "I checked the important sections"                | You don't decide importance. All sections MUST be checked.             | **List every section in table**                   |
| "Some sections obviously don't apply"             | Report them as N/A with reason. Never skip silently.                   | **Include in table with N/A status**              |
| "The table would be too long"                     | Completeness > brevity. Every section MUST be visible.                 | **Output full table regardless of length**        |
| "I already mentioned these in findings"           | Findings ≠ Coverage table. Both are REQUIRED.                          | **Output table BEFORE detailed findings**         |
| "Feature has no UI so design standards don't apply" | Non-UI features still need problem validation, personas, JTBD.        | **Check all 13 sections, mark N/A with reason**   |
| "Only checking what exists in design spec"        | Standards define what SHOULD exist. Missing = Non-Compliant.           | **Report missing specs as ❌ Non-Compliant**      |
| "My section name is clearer"                      | Consistency > clarity. Coverage table names are the contract.          | **Use EXACT names from coverage table**           |
| "I combined related sections for brevity"         | Each section = one row. Merging loses traceability.                    | **One row per section, no merging**               |
| "I added a useful section like 'Visual Design'"   | You don't decide sections. Coverage table does.                        | **Only output sections from coverage table**      |

---

## Completeness Check (SELF-VERIFICATION)

**Before submitting output, verify:**

```text
1. Did I extract all 13 ## headers from product-design.md?   [ ]
2. Does my table have exactly 13 rows?                        [ ]
3. Does every row have a status (✅/⚠️/❌/N/A)?               [ ]
4. Does every ⚠️/❌ have evidence (file:line)?                [ ]
5. Does every N/A have a reason?                              [ ]

If any checkbox is unchecked → FIX before submitting.
```

---

## Integration with Findings

**Order of output:**

1. **Standards Coverage Table** (this pattern) - Shows completeness
2. **Detailed Findings** - Only for ⚠️ Partial and ❌ Non-Compliant items

The Coverage Table ensures nothing is skipped. The Detailed Findings provide actionable information for gaps.

---

## Agent → Standards Section Index

**IMPORTANT:** When updating product-design.md, you MUST also update the corresponding section index below.

**Meta-sections (EXCLUDED from agent checks):**
Standards files may contain these meta-sections that are not counted in section indexes:

- `## Checklist` - Pre-submission checklist for designers

These sections describe HOW to use the standards, not WHAT the standards are.

### ring:product-designer → product-design.md

| #   | Section to Check             | Anchor                                       | Key Subsections                                                              |
| --- | ---------------------------- | -------------------------------------------- | ---------------------------------------------------------------------------- |
| 1   | UX Research Methods          | `#ux-research-methods`                       | Primary research methods, documentation format                               |
| 2   | Problem Validation           | `#problem-validation`                        | Problem statement format, evidence requirements, validation status           |
| 3   | Persona Creation             | `#persona-creation`                          | Persona template, demographics, goals, pain points, minimum 2-3 personas    |
| 4   | Jobs to Be Done              | `#jobs-to-be-done`                           | JTBD statement format, functional/emotional/social jobs                      |
| 5   | User Flow Notation           | `#user-flow-notation`                        | Mermaid flowchart standard, happy/error/alternative paths                    |
| 6   | Wireframe Format             | `#wireframe-format`                          | YAML structure, component hierarchy, state variations, responsive behavior   |
| 7   | ASCII Prototypes             | `#ascii-prototypes`                          | **MANDATORY** visual ASCII representation, notation reference, layout types  |
| 8   | UI States                    | `#ui-states`                                 | Default, loading, empty, error, success, disabled states                     |
| 9   | UX Acceptance Criteria       | `#ux-acceptance-criteria`                    | Functional, usability, accessibility, responsive, performance criteria       |
| 10  | Accessibility Requirements   | `#accessibility-requirements`                | **WCAG 2.1 AA (MANDATORY)**, contrast ratios, keyboard nav, touch targets   |
| 11  | Responsive Design            | `#responsive-design`                         | Breakpoints (xs-2xl), mobile-first principles, responsive behavior template |
| 12  | Interaction Patterns         | `#interaction-patterns`                      | Standard interactions, animation guidelines, feedback patterns               |
| 13  | Forbidden Patterns           | `#forbidden-patterns`                        | UX anti-patterns, design debt categories                                     |

---

## How Agents Reference This Pattern

Agents MUST include this in their Standards Compliance section:

```markdown
## Standards Compliance Output (Conditional)

**Detection:** Prompt contains `**MODE: ANALYSIS only**`

**When triggered, you MUST:**

1. Output Standards Coverage Table per [shared-patterns/standards-coverage-table.md](../skills/shared-patterns/standards-coverage-table.md)
2. Then output detailed findings for ⚠️/❌ items

See [shared-patterns/standards-coverage-table.md](../skills/shared-patterns/standards-coverage-table.md) for:

- Table format
- Status legend
- Anti-rationalization rules
- Completeness verification checklist
```

---

## Maintenance Instructions

**When you add/modify a section in product-design.md:**

1. Edit `pm-team/docs/standards/product-design.md` - Add your new `## Section Name`
2. Update the `## Table of Contents` in the same file
3. Edit THIS file - Add the section to the ring:product-designer table above
4. Verify row count matches section count (currently 13)

**Anti-Rationalization:**

| Rationalization                   | Why It's WRONG                                     | Required Action                      |
| --------------------------------- | -------------------------------------------------- | ------------------------------------ |
| "I'll update the index later"     | Later = never. Sync drift causes missed checks.    | **Update BOTH files in same commit** |
| "The section is minor"            | Minor ≠ optional. All sections must be indexed.    | **Add to index regardless of size**  |
| "Agents parse dynamically anyway" | Index is the explicit contract. Dynamic is backup. | **Index is source of truth**         |
