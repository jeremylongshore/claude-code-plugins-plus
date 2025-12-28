# Badge Automation System

Automated badge generation from validation results for README.md and CI workflows.

## Overview

This system consists of three components:

1. **Validators with JSON output** - Python scripts that validate plugins/skills and output structured JSON
2. **Badge generator** - Node.js script that calculates scores and determines earned badges
3. **README updater** - Node.js script that updates README.md with new badges

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Validation Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  validate-skills-schema.py --json                               │
│  validate-frontmatter.py --json                                 │
│                                                                   │
│  Output: JSON with errors, warnings, compliance metrics          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Badge Generation Layer                      │
├─────────────────────────────────────────────────────────────────┤
│  generate-badges.mjs                                            │
│                                                                   │
│  - Calculates category scores (security, docs, func, maint)     │
│  - Determines overall grade (A-F)                               │
│  - Evaluates badge requirements                                 │
│  - Returns earned + available badges                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      README Update Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  update-readme-badges.mjs                                       │
│                                                                   │
│  - Reads marketplace catalog for counts                         │
│  - Generates shields.io badge URLs                              │
│  - Updates README.md badge section                              │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Standalone Usage

```bash
# Just update plugin/skill counts (no validation)
node scripts/update-readme-badges.mjs

# Preview without writing
node scripts/update-readme-badges.mjs --dry-run
```

### Full Pipeline (Validation → Badges → README)

```bash
# Step 1: Validate and generate JSON
python3 scripts/validate-skills-schema.py --json > /tmp/validation.json

# Step 2: Generate badge data
node scripts/generate-badges.mjs /tmp/validation.json --json > /tmp/badges.json

# Step 3: Update README
node scripts/update-readme-badges.mjs /tmp/badges.json
```

### One-Liner (Development)

```bash
# Using files (recommended for debugging)
python3 scripts/validate-skills-schema.py --json > /tmp/v.json && \
  node scripts/generate-badges.mjs /tmp/v.json --json > /tmp/b.json && \
  node scripts/update-readme-badges.mjs /tmp/b.json --dry-run
```

## Validators with JSON Output

### validate-skills-schema.py

Validates SKILL.md files against 2025 schema.

```bash
# Text output (default)
python3 scripts/validate-skills-schema.py

# JSON output for automation
python3 scripts/validate-skills-schema.py --json

# Verbose mode
python3 scripts/validate-skills-schema.py --verbose

# Fail on warnings (strict mode)
python3 scripts/validate-skills-schema.py --fail-on-warn
```

**JSON Output Format:**

```json
{
  "version": "1.0.0",
  "timestamp": "2025-12-27T...",
  "validator": "skills-schema",
  "summary": {
    "total": 244,
    "passed": 10,
    "failed": 0,
    "warnings": 234
  },
  "score": {
    "total": 87,
    "grade": "B",
    "categories": {
      "security": 23,
      "documentation": 22,
      "functionality": 21,
      "maintenance": 21
    }
  },
  "badges": ["verified", "secure", "documented"],
  "details": {
    "total_errors": 0,
    "total_warnings": 15,
    "compliance_rate": 89.5,
    "description_chars": 12450
  },
  "files": [
    {
      "file": "plugins/category/plugin/skills/skill/SKILL.md",
      "errors": [],
      "warnings": ["..."],
      "fatal": null,
      "word_count": 1200,
      "line_count": 300,
      "description_length": 150
    }
  ]
}
```

### validate-frontmatter.py

Validates YAML frontmatter in command/agent files.

```bash
# Text output (default)
python3 scripts/validate-frontmatter.py

# JSON output for automation
python3 scripts/validate-frontmatter.py --json
```

**JSON Output Format:**

```json
{
  "version": "1.0.0",
  "timestamp": "2025-12-27T...",
  "validator": "frontmatter",
  "summary": {
    "total": 45,
    "passed": 42,
    "failed": 0,
    "warnings": 3
  },
  "score": {
    "total": 95,
    "grade": "A"
  },
  "badges": ["valid-frontmatter", "well-documented"],
  "details": {
    "total_errors": 0,
    "total_warnings": 3,
    "compliance_rate": 100.0
  },
  "files": [...]
}
```

## Badge Generator

Calculates quality scores and determines earned badges.

### Usage

```bash
# From file
node scripts/generate-badges.mjs validation-results.json

# From stdin (pipe)
python3 scripts/validate-skills-schema.py --json | \
  node scripts/generate-badges.mjs

# JSON output
node scripts/generate-badges.mjs results.json --json

# Help
node scripts/generate-badges.mjs --help
```

### Badge Definitions

| Badge ID | Name | Requirement |
|----------|------|-------------|
| `verified` | Verified | All validations pass (0 errors) |
| `secure` | Secure | Security score >= 20/25 |
| `documented` | Documented | Documentation score >= 20/25 |
| `compliant` | Compliant | 90%+ files fully compliant |
| `valid-frontmatter` | Valid Frontmatter | Frontmatter validation passes |
| `well-documented` | Well Documented | Compliance rate >= 90% |

### Score Calculation

**Total Score: 0-100 (sum of 4 categories × 25 points each)**

1. **Security (0-25)**: Based on error rate
   - Formula: `25 × (1 - errors/files)`
   - Perfect: 0 errors = 25 points

2. **Documentation (0-25)**: Based on compliance rate
   - Formula: `compliance_rate / 4`
   - Perfect: 100% compliance = 25 points

3. **Functionality (0-25)**: Based on passed files
   - Formula: `25 × (passed_files / total_files)`
   - Perfect: All files pass = 25 points

4. **Maintenance (0-25)**: Based on warning rate
   - Formula: `25 × (1 - warnings / (files × 3))`
   - Perfect: <3 warnings per file = 25 points

**Grade Scale:**
- A: 90-100
- B: 80-89
- C: 70-79
- D: 60-69
- F: 0-59

### Output Format

**Text Output (default):**

```
======================================================================
BADGE GENERATION RESULTS
======================================================================

Overall Score: 87/100 (Grade: B)

Category Scores:
  security             25/25 (100%)
  documentation        22/25 (88%)
  functionality        21/25 (84%)
  maintenance          19/25 (76%)

Earned Badges (3):
  ✓ Verified
    All validations pass with no errors
  ✓ Secure
    Security score >= 20/25
  ✓ Documented
    Documentation score >= 20/25

Available Badges (1):
  ☐ Compliant
    90%+ of files fully compliant
    Requirement: compliance_rate >= 90

Validation Summary:
  Total files: 244
  Passed: 220
  Failed: 0
  Warnings: 24
  Compliance rate: 90.2%

======================================================================
```

**JSON Output (--json):**

```json
{
  "version": "1.0.0",
  "timestamp": "2025-12-27T...",
  "validator": "skills-schema",
  "score": {
    "total": 87,
    "grade": "B",
    "categories": {
      "security": 25,
      "documentation": 22,
      "functionality": 21,
      "maintenance": 19
    }
  },
  "badges": {
    "earned": ["verified", "secure", "documented"],
    "earned_details": [...],
    "available": ["compliant"],
    "available_details": [...]
  },
  "summary": {
    "total": 244,
    "passed": 220,
    "failed": 0,
    "warnings": 24
  },
  "details": {
    "total_errors": 0,
    "total_warnings": 24,
    "compliance_rate": 90.2
  }
}
```

## README Badge Updater

Updates README.md with current plugin/skill counts and quality badges.

### Usage

```bash
# Update using marketplace catalog only
node scripts/update-readme-badges.mjs

# Update with validation results
node scripts/update-readme-badges.mjs /tmp/badges.json

# Preview changes without writing
node scripts/update-readme-badges.mjs --dry-run

# Help
node scripts/update-readme-badges.mjs --help
```

### Badge Generation

Creates shields.io badges:

1. **Plugin Count** (from marketplace catalog)
   ```
   ![Plugins](https://img.shields.io/badge/plugins-259-blue)
   ```

2. **Skill Count** (from marketplace catalog)
   ```
   ![Skills](https://img.shields.io/badge/skills-241-green)
   ```

3. **Compliance Rate** (from validation results)
   ```
   ![Compliance](https://img.shields.io/badge/compliance-90%25-brightgreen)
   ```
   - Color: green (≥90%), yellow (≥70%), red (<70%)

4. **Quality Score** (from validation results)
   ```
   ![Quality](https://img.shields.io/badge/quality-87%2F100%20(B)-brightgreen)
   ```
   - Color: green (≥90%), yellow (≥70%), red (<70%)

5. **Individual Badges** (from validation results)
   ```
   ![Verified](https://img.shields.io/badge/verified-✓-brightgreen)
   ![Secure](https://img.shields.io/badge/secure-✓-brightgreen)
   ![Documented](https://img.shields.io/badge/documented-✗-lightgrey)
   ```

### README Format

The script looks for existing shields.io badges in README.md and replaces them.

**Expected format:**
```markdown
[![Badge1](https://img.shields.io/badge/...)](...)
[![Badge2](https://img.shields.io/badge/...)](...)
[![Badge3](https://img.shields.io/badge/...)](...)
```

## CI Integration

### GitHub Actions Workflow

```yaml
name: Update Quality Badges

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # Daily

jobs:
  update-badges:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Python dependencies
        run: pip install pyyaml

      - name: Validate plugins
        run: |
          python3 scripts/validate-skills-schema.py --json > validation.json
          python3 scripts/validate-frontmatter.py --json > frontmatter.json

      - name: Generate badges
        run: |
          node scripts/generate-badges.mjs validation.json --json > badges.json

      - name: Update README badges
        run: |
          node scripts/update-readme-badges.mjs badges.json

      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add README.md
          git diff --staged --quiet || git commit -m "chore: update quality badges"
          git push
```

## Testing

### Test Validators

```bash
# Test skills validator
python3 scripts/validate-skills-schema.py --json | jq '.summary'

# Test frontmatter validator
python3 scripts/validate-frontmatter.py --json | jq '.summary'
```

### Test Badge Generator

```bash
# Generate sample validation data
echo '{
  "validator": "skills-schema",
  "summary": {"total": 100, "passed": 90, "failed": 0, "warnings": 10},
  "score": {"total": 85, "grade": "B", "categories": {"security": 25, "documentation": 20, "functionality": 22, "maintenance": 18}},
  "details": {"total_errors": 0, "total_warnings": 10, "compliance_rate": 90}
}' | node scripts/generate-badges.mjs
```

### Test README Updater

```bash
# Dry run (no changes)
node scripts/update-readme-badges.mjs --dry-run

# Dry run with validation data
node scripts/update-readme-badges.mjs /tmp/badges.json --dry-run
```

## Troubleshooting

### "Invalid JSON input"

The validators must output valid JSON. Check stderr:

```bash
python3 scripts/validate-skills-schema.py --json 2>&1 | jq .
```

### "Could not find badges section in README.md"

The script looks for shields.io badge URLs. Ensure README.md has badges in this format:

```markdown
[![Badge](https://img.shields.io/badge/...)](...)
```

### Skill count is NaN

Check marketplace catalog structure:

```bash
jq '.plugins[0].components.skills' .claude-plugin/marketplace.extended.json
```

Should be a number or array, not null/undefined.

### Badge generator exit code 1

Exit code 1 means score < 70 (failing grade). This is intentional for CI workflows.

```bash
node scripts/generate-badges.mjs results.json
echo $?  # 0 if score >= 70, 1 if < 70
```

## Files

### Scripts

- `scripts/validate-skills-schema.py` - Skills validator with JSON output
- `scripts/validate-frontmatter.py` - Frontmatter validator with JSON output
- `scripts/generate-badges.mjs` - Badge score calculator
- `scripts/update-readme-badges.mjs` - README badge updater
- `scripts/BADGE-AUTOMATION.md` - This documentation

### Data Files

- `.claude-plugin/marketplace.extended.json` - Plugin/skill counts source
- `/tmp/validation.json` - Validation results (temporary)
- `/tmp/badges.json` - Badge data (temporary)

## Development

### Adding New Badges

1. Define badge in `generate-badges.mjs`:

```javascript
const BADGE_DEFINITIONS = {
  'new-badge': {
    name: 'New Badge',
    description: 'Description of requirement',
    requirement: 'score >= 80',  // JavaScript expression
  },
};
```

2. Add badge template in `update-readme-badges.mjs`:

```javascript
const BADGE_TEMPLATES = {
  newBadge: (earned) => {
    if (earned) {
      return `![New Badge](https://img.shields.io/badge/new_badge-✓-brightgreen)`;
    } else {
      return `![New Badge](https://img.shields.io/badge/new_badge-✗-lightgrey)`;
    }
  },
};
```

### Adding New Validators

1. Create validator script with `--json` flag support
2. Output JSON matching this schema:

```json
{
  "version": "1.0.0",
  "timestamp": "ISO-8601",
  "validator": "unique-name",
  "summary": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0
  },
  "score": {
    "total": 0,
    "grade": "A-F"
  },
  "details": {
    "total_errors": 0,
    "total_warnings": 0,
    "compliance_rate": 0.0
  },
  "files": []
}
```

3. Test with badge generator:

```bash
your-validator --json | node scripts/generate-badges.mjs
```

## Version History

- **1.0.0** (2025-12-27) - Initial release
  - JSON output for validators
  - Badge generation system
  - README updater
  - Full CI integration support
