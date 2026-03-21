# Skill Output Patterns

Reference for structuring skill output. Source: Anthropic best practices.

---

## Template Pattern

Generate output from predefined templates with variable substitution.

### Strict Template (Low Degrees of Freedom)

Use when output format must be exact (API payloads, config files, compliance docs).

```markdown
## Instructions

Generate output using this exact template:

```json
{
  "name": "{project_name}",
  "version": "{version}",
  "scripts": {
    "build": "{build_command}",
    "test": "{test_command}"
  }
}
```

Replace placeholders with gathered values. Do not add extra fields.
```

### Flexible Template (Medium Degrees of Freedom)

Use when structure is defined but content is creative.

```markdown
## Instructions

Generate a report following this structure:

# {Title}

## Summary
{2-3 sentence executive summary}

## Findings
{Detailed findings - use tables, lists, or prose as appropriate}

## Recommendations
{Prioritized list of action items}

Adapt section depth to the complexity of findings.
```

---

## Examples Pattern

Provide input/output pairs that demonstrate expected behavior.

### Inline Examples

```markdown
## Examples

### Simple case
**Input**: `/skill-name auth.py`
**Output**:
```
auth.py: 3 issues found
  Line 15: SQL injection risk in query builder
  Line 42: Hardcoded credential detected
  Line 89: Missing input validation
```

### Complex case
**Input**: `/skill-name --deep src/`
**Output**:
```
Deep scan: 12 files, 7 issues
  CRITICAL (2): sql-injection, hardcoded-secret
  WARNING (3): missing-validation, weak-hash, cors-wildcard
  INFO (2): deprecated-api, unused-import
```
```

### When to Use

- Always include at least 1 example
- Show both simple and complex cases
- Show edge cases (empty input, errors)
- Examples teach Claude the expected output format better than rules

---

## Visual Output Pattern

Generate HTML artifacts for rich visual output.

```markdown
## Instructions

### Step 1: Gather Data
Collect the metrics and data points needed.

### Step 2: Generate HTML Report
Create a self-contained HTML file with:
- Inline CSS (no external dependencies)
- Responsive layout
- Data tables with sorting
- Charts if applicable (use inline SVG)

### Step 3: Write Output
Save to `{output_path}/report.html`

Example HTML structure:
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: system-ui; max-width: 900px; margin: 0 auto; padding: 2rem; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 8px; border: 1px solid #ddd; text-align: left; }
    .critical { color: #dc3545; }
    .warning { color: #ffc107; }
    .pass { color: #28a745; }
  </style>
</head>
<body>
  <h1>{Report Title}</h1>
  <!-- Content here -->
</body>
</html>
```
```

### When to Use

- Dashboards and reports
- Documentation previews
- Visual diffs or comparisons
- Any output that benefits from formatting beyond plain text

---

## Structured Data Pattern

Output structured data (JSON, YAML, CSV) for programmatic consumption.

```markdown
## Output Format

Results are written as JSON to `{output_path}/results.json`:

```json
{
  "scan_date": "2025-01-15",
  "files_scanned": 42,
  "issues": [
    {
      "file": "auth.py",
      "line": 15,
      "severity": "critical",
      "rule": "sql-injection",
      "message": "Unsanitized input in SQL query"
    }
  ],
  "summary": {
    "critical": 2,
    "warning": 5,
    "info": 3
  }
}
```

Additionally, a human-readable summary is printed to the conversation.
```

---

## Choosing Output Patterns

| If the output is... | Use |
|---------------------|-----|
| Exact format required | Strict Template |
| Structured but flexible | Flexible Template |
| Best shown by example | Examples Pattern |
| Rich/visual | Visual Output (HTML) |
| Machine-readable | Structured Data (JSON/YAML) |
| Multiple audiences | Combine: JSON file + conversation summary |
