# Output Patterns

Reference guide for structuring skill output. Choose based on how strictly the output format matters.

---

## Strict Template

Exact output format — every field, every line defined. Zero creative freedom.

**When to use:** API responses, config files, compliance documents, machine-parseable output.

**Implementation:** Provide the exact template in SKILL.md with all fields labeled.

```markdown
## Output

Generate output in EXACTLY this format:

\```
REPORT: {title}
Date: {YYYY-MM-DD}
Status: {PASS|FAIL|WARN}
Findings: {count}

{findings table}
\```
```

---

## Flexible Template

Defined structure with creative content. Sections are fixed, content within is free-form.

**When to use:** Documentation, READMEs, blog posts, analysis reports.

**Implementation:** Specify required sections and constraints, let Claude fill content.

```markdown
## Output

Include these sections in order:
1. **Summary** (2-3 sentences)
2. **Key Findings** (bulleted list)
3. **Recommendations** (numbered, prioritized)
4. **Next Steps** (actionable items)
```

---

## Examples-Driven

Define behavior through input/output pairs. Claude infers the pattern.

**When to use:** Transformations, formatting, code generation where showing is clearer than telling.

**Implementation:** Provide 3+ diverse examples covering normal and edge cases.

```markdown
## Examples

**Input:** `getUserById(123)`
**Output:** `SELECT * FROM users WHERE id = $1` with params `[123]`

**Input:** `findUsersByName("Alice")`
**Output:** `SELECT * FROM users WHERE name ILIKE $1` with params `['%Alice%']`
```

---

## Visual (HTML Generation)

Generate self-contained HTML pages for rich visual output.

**When to use:** Dashboards, comparison tables, diagrams, interactive reports.

**Implementation:** Specify the visual layout, styling approach, and data structure.

```markdown
## Output

Generate a self-contained HTML file with:
- Inline CSS (no external dependencies)
- Data table with sortable columns
- Color-coded severity indicators
- Print-friendly layout
```

---

## Structured Data

Output as JSON, YAML, or other machine-readable format.

**When to use:** API integrations, config generation, data export, pipeline inputs.

**Implementation:** Provide the exact schema with field types and constraints.

```markdown
## Output

Generate JSON matching this schema:

\```json
{
  "version": "1.0",
  "results": [
    {
      "file": "string",
      "line": "number",
      "severity": "error|warning|info",
      "message": "string"
    }
  ],
  "summary": {
    "total": "number",
    "errors": "number",
    "warnings": "number"
  }
}
\```
```

---

## Choosing a Pattern

| Need | Pattern | Degrees of Freedom |
|------|---------|-------------------|
| Machine-parseable | Strict Template | None |
| Consistent structure | Flexible Template | Medium |
| Pattern inference | Examples-Driven | Medium |
| Rich presentation | Visual (HTML) | High |
| Pipeline integration | Structured Data | None |

**Tip:** Combine patterns when needed. A skill might use Structured Data for the primary output and Visual for a human-readable report.
