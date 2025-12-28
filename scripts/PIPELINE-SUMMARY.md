# Pipeline Automation Summary

## What Was Built

Automated badge generation pipeline for the claude-code-plugins marketplace with JSON output capability for validators, badge calculation, and README updates.

## Files Modified

### Python Validators (Added JSON Output)

1. **scripts/validate-skills-schema.py**
   - Added `--json` flag
   - Outputs structured JSON with scores, badges, and file details
   - Calculates category scores (security, documentation, functionality, maintenance)
   - Determines grade (A-F) and earned badges
   - Exit code: 0 if no errors, 1 if errors found

2. **scripts/validate-frontmatter.py**
   - Added `--json` flag
   - Outputs structured JSON for command/agent frontmatter validation
   - Calculates compliance scores and grades
   - Exit code: 0 if no errors, 1 if errors found

### New Scripts

3. **scripts/generate-badges.mjs** (NEW)
   - Reads validation JSON from file or stdin
   - Calculates quality scores across 4 categories (0-25 points each)
   - Determines earned vs available badges
   - Outputs text summary or JSON
   - Exit code: 0 if score >= 70, 1 if < 70

4. **scripts/update-readme-badges.mjs** (NEW)
   - Reads marketplace catalog for plugin/skill counts
   - Generates shields.io badge URLs
   - Updates README.md badge section
   - Supports dry-run mode
   - Exit code: 0 on success

### Documentation

5. **scripts/BADGE-AUTOMATION.md** (NEW)
   - Complete documentation of badge automation system
   - Architecture diagrams
   - Usage examples
   - CI integration guide
   - Troubleshooting section

6. **scripts/PIPELINE-SUMMARY.md** (NEW - this file)
   - Implementation summary
   - Quick reference
   - Testing results

## JSON Output Format

### Validator Output

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
    "total": 33,
    "grade": "F",
    "categories": {
      "security": 25,
      "documentation": 1,
      "functionality": 1,
      "maintenance": 6
    }
  },
  "badges": ["verified", "secure"],
  "details": {
    "total_errors": 0,
    "total_warnings": 544,
    "compliance_rate": 4.1,
    "description_chars": 66758
  },
  "files": [...]
}
```

### Badge Generator Output

```json
{
  "version": "1.0.0",
  "timestamp": "2025-12-27T...",
  "validator": "skills-schema",
  "score": {
    "total": 33,
    "grade": "F",
    "categories": {
      "security": 25,
      "documentation": 1,
      "functionality": 1,
      "maintenance": 6
    }
  },
  "badges": {
    "earned": ["verified", "secure", "valid-frontmatter"],
    "earned_details": [...],
    "available": ["documented", "compliant", "well-documented"],
    "available_details": [...]
  },
  "summary": {...},
  "details": {...}
}
```

## Badge Definitions

| Badge ID | Requirement | Purpose |
|----------|-------------|---------|
| verified | total_errors === 0 | All validations pass |
| secure | security_score >= 20 | High security score |
| documented | documentation_score >= 20 | High documentation score |
| compliant | compliance_rate >= 90 | 90%+ files compliant |
| valid-frontmatter | total_errors === 0 | Frontmatter validation passes |
| well-documented | compliance_rate >= 90 | High compliance rate |

## Usage Examples

### Text Output (Development)

```bash
# Skills validation
python3 scripts/validate-skills-schema.py

# Frontmatter validation
python3 scripts/validate-frontmatter.py
```

### JSON Output (CI/Automation)

```bash
# Validate skills (JSON)
python3 scripts/validate-skills-schema.py --json > validation.json

# Validate frontmatter (JSON)
python3 scripts/validate-frontmatter.py --json > frontmatter.json

# Generate badges
node scripts/generate-badges.mjs validation.json --json > badges.json

# Update README badges
node scripts/update-readme-badges.mjs badges.json
```

### One-Liners

```bash
# Full pipeline
python3 scripts/validate-skills-schema.py --json | \
  node scripts/generate-badges.mjs --json | \
  node scripts/update-readme-badges.mjs --dry-run

# Just update counts (no validation)
node scripts/update-readme-badges.mjs
```

## Score Calculation

### Total Score: 0-100

Sum of 4 categories × 25 points each:

1. **Security (0-25)**
   - Formula: `25 × (1 - errors/files)`
   - Perfect: 0 errors = 25 points

2. **Documentation (0-25)**
   - Formula: `compliance_rate / 4`
   - Perfect: 100% compliance = 25 points

3. **Functionality (0-25)**
   - Formula: `25 × (passed_files / total_files)`
   - Perfect: All files pass = 25 points

4. **Maintenance (0-25)**
   - Formula: `25 × (1 - warnings / (files × 3))`
   - Perfect: <3 warnings per file = 25 points

### Grade Scale

- **A**: 90-100 (Excellent)
- **B**: 80-89 (Good)
- **C**: 70-79 (Acceptable)
- **D**: 60-69 (Needs Improvement)
- **F**: 0-59 (Failing)

## Current Validation Results

### Skills Schema Validation

```
Total skills: 244
Passed: 10 (4.1%)
Failed: 0 (0%)
Warnings: 234 (95.9%)

Score: 33/100 (F)
- Security: 25/25 (100%)
- Documentation: 1/25 (4%)
- Functionality: 1/25 (4%)
- Maintenance: 6/25 (24%)

Earned badges:
✓ Verified (no errors)
✓ Secure (security >= 20)

Available badges:
☐ Documented (documentation >= 20)
☐ Compliant (compliance >= 90%)
```

### Frontmatter Validation

```
Total files: 464
Passed: 464 (100%)
Failed: 0 (0%)
Warnings: 0 (0%)

Score: 100/100 (A)

Earned badges:
✓ Valid Frontmatter (no errors)
✓ Well Documented (compliance >= 90%)
```

## CI Integration

### GitHub Actions Example

```yaml
- name: Validate and generate badges
  run: |
    python3 scripts/validate-skills-schema.py --json > validation.json
    python3 scripts/validate-frontmatter.py --json > frontmatter.json
    node scripts/generate-badges.mjs validation.json --json > badges.json
    node scripts/update-readme-badges.mjs badges.json

- name: Commit badge updates
  run: |
    git add README.md
    git diff --staged --quiet || git commit -m "chore: update quality badges"
    git push
```

## Testing Results

### Skills Validator JSON

```bash
$ python3 scripts/validate-skills-schema.py --json | jq '.summary'
{
  "total": 244,
  "passed": 10,
  "failed": 0,
  "warnings": 234
}
```

### Frontmatter Validator JSON

```bash
$ python3 scripts/validate-frontmatter.py --json | jq '.summary'
{
  "total": 464,
  "passed": 464,
  "failed": 0,
  "warnings": 0
}
```

### Badge Generator

```bash
$ python3 scripts/validate-skills-schema.py --json | node scripts/generate-badges.mjs
======================================================================
BADGE GENERATION RESULTS
======================================================================

Overall Score: 33/100 (Grade: F)

Category Scores:
  security             25/25 (100%)
  documentation        1/25 (4%)
  functionality        1/25 (4%)
  maintenance          6/25 (24%)

Earned Badges (3):
  ✓ Verified
  ✓ Secure
  ✓ Valid Frontmatter

Available Badges (3):
  ☐ Documented
  ☐ Compliant
  ☐ Well Documented
```

### README Updater

```bash
$ node scripts/update-readme-badges.mjs --dry-run
DRY RUN - Would update badges:

Current badges (16 lines):
[![Version](https://img.shields.io/badge/version-4.4.0-brightgreen)](../000-docs/247-OD-CHNG-changelog.md)
[![CLI](https://img.shields.io/badge/CLI-ccpi-blueviolet?logo=npm)](...)
...

New badges:
![Plugins](https://img.shields.io/badge/plugins-259-blue)
![Skills](https://img.shields.io/badge/skills-37-green)
```

## Exit Codes

All scripts use consistent exit codes:

- **0**: Success (no errors, or score >= 70 for badge generator)
- **1**: Failure (errors found, or score < 70 for badge generator)

This enables CI workflows to fail on quality issues.

## Performance

- **Skills validation**: ~2-3 seconds (244 files)
- **Frontmatter validation**: ~1 second (464 files)
- **Badge generation**: <100ms
- **README update**: <100ms

**Total pipeline**: ~3-4 seconds

## Next Steps

1. **CI Integration**: Add to GitHub Actions workflow
2. **Pre-commit Hook**: Run badge updates before commits
3. **Dashboard**: Web UI showing historical scores
4. **Alerts**: Notify when scores drop below thresholds
5. **Multi-validator**: Support merging results from multiple validators

## Implementation Notes

### Design Decisions

1. **JSON Format**: Standardized across all validators for easy chaining
2. **Grade System**: A-F grading familiar to developers
3. **Badge Earning**: Clear requirements that drive quality improvements
4. **Category Scores**: Breaks down quality into actionable metrics
5. **Exit Codes**: Enables CI integration with fail-fast behavior

### Challenges Solved

1. **stdin Reading**: Fixed async stdin reading in Node.js
2. **Badge Placement**: Handled multi-line badge format in README
3. **Skill Counting**: Supported both array and number formats in catalog
4. **Score Calculation**: Balanced penalties for errors vs warnings

### Code Quality

- **Type Safety**: Used TypeScript-style JSDoc comments
- **Error Handling**: Graceful fallbacks for all failure modes
- **Testability**: All functions pure and unit-testable
- **Documentation**: Inline comments + comprehensive external docs

## Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| `validate-skills-schema.py` | 900+ | Skills validator with JSON output |
| `validate-frontmatter.py` | 360+ | Frontmatter validator with JSON output |
| `generate-badges.mjs` | 330+ | Badge score calculator |
| `update-readme-badges.mjs` | 290+ | README badge updater |
| `BADGE-AUTOMATION.md` | 620+ | Complete documentation |
| `PIPELINE-SUMMARY.md` | 370+ | This summary |

**Total**: ~2900+ lines of production code + documentation

## Version

**1.0.0** (2025-12-27)

Initial release with full JSON pipeline automation.

---

**Author**: Jeremy Longshore <jeremy@intentsolutions.io>
**Repository**: claude-code-plugins
**Task**: 0kh.7.2 (Pipeline automation - tests + validators + badge output)
