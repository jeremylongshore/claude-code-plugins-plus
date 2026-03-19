# Validation Rules — 100-Point Rubric

Detailed sub-criteria for the Intent Solutions 100-point grading system.

---

## Grade Scale

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 90-100 | Production-ready |
| B | 80-89 | Good, minor improvements |
| C | 70-79 | Adequate, has gaps |
| D | 60-69 | Needs significant work |
| F | <60 | Major revision required |

---

## Pillar 1: Progressive Disclosure (30 pts)

### Token Economy (10 pts)
- 10 pts: SKILL.md body ≤150 lines
- 7 pts: 151-300 lines
- 4 pts: 301-500 lines
- 0 pts: >500 lines

### Layered Structure (10 pts)
- 10 pts: Has `references/` directory with markdown files
- 8 pts: No references needed (skill ≤100 lines)
- 4 pts: No references but skill is 100-200 lines
- 3 pts: `references/` exists but empty
- 0 pts: No references and skill >200 lines

### Reference Depth (5 pts)
- 5 pts: References are flat (no nested subdirectories)
- 2 pts: Has nested directories in `references/`
- 5 pts: N/A (no references directory)

### Navigation Signals (5 pts)
- 5 pts: Short file (≤100 lines) OR ≥7 section headers
- 4 pts: 4-6 section headers (>100 lines)
- 2 pts: 2-3 section headers (>100 lines)
- 0 pts: 0-1 section headers (>100 lines)

---

## Pillar 2: Ease of Use (25 pts)

### Metadata Quality (10 pts)
- +2: Has `name`
- +3: Has `description` ≥50 chars
- +2: Has `version`
- +2: Has `allowed-tools`
- +1: Has `author` with email

### Discoverability (6 pts)
- +3: Description contains "Use when"
- +3: Description contains "Trigger with" or "Trigger phrase"

### Terminology Consistency (4 pts)
- -2: `name` differs from folder name
- -1: Inconsistent casing in description (ALL CAPS words >3 chars)

### Workflow Clarity (5 pts)
- +3: Has numbered steps in body
- +2: Has ≥5 section headers
- +1: Has 3-4 section headers

---

## Pillar 3: Utility (20 pts)

### Problem Solving Power (8 pts)
- +4: Has `## Overview` section with >50 chars
- +2: Has `## Prerequisites` section
- +2: Has `## Output` section

### Degrees of Freedom (5 pts)
- +2: Mentions options/configuration/parameters
- +2: Shows alternatives/multiple approaches
- +1: Mentions extensibility/customization

### Feedback Loops (4 pts)
- +2: Has `## Error Handling` section
- +1: Mentions validation/verification
- +1: Mentions troubleshooting/debugging

### Examples & Templates (3 pts)
- +2: Has `## Examples` section or labeled examples
- +1: Has ≥2 code blocks

---

## Pillar 4: Spec Compliance (15 pts)

### Frontmatter Validity (5 pts)
- 5 pts baseline, -1 per missing required field (max -4)
- Required: name, description, allowed-tools, version, author, license

### Name Conventions (4 pts)
- -2: Not kebab-case
- -1: Name >64 characters
- -1: Name doesn't match folder

### Description Quality (4 pts)
- -2: Too short (<50 chars)
- -2: Too long (>1024 chars)
- -1: Uses first person ("I can")
- -1: Uses second person ("You should")

### Optional Fields (2 pts)
- -1: Invalid `model` value

---

## Pillar 5: Writing Style (10 pts)

### Voice & Tense (4 pts)
- -2: No imperative verbs in numbered steps

### Objectivity (3 pts)
- -1: "you should/can/will" in body
- -1: "I can/will" in body

### Conciseness (3 pts)
- -2: >3000 words
- -1: >2000 words
- -1: >400 lines

---

## Modifiers (+/-5 pts)

### Bonuses
- +1: Gerund-style name (ends in `-ing`)
- +1: Grep-friendly structure (≥7 section headers)
- +2: ≥3 labeled examples
- +1: Resources section with ≥2 external links

### Penalties
- -2: First/second person in description
- -1: XML-like tags in body
- -1: TOC wastes tokens (use clear section headers instead)

### Relative Markdown Links
- Validator checks that relative markdown links (e.g., `[ref](reference.md)`, `[api](references/api.md)`) point to existing files
- Links to URLs (`https://...`) are ignored
- Broken relative links produce a warning

### DCI Bonus
- +1: Uses dynamic context injection (`` !`command` `` directives)

---

## Structural Advisors (Enterprise Tier)

INFO-level suggestions emitted after grading. Not scored — purely advisory.

| Advisor | Trigger | Suggestion |
|---------|---------|------------|
| Split to Commands | 3+ kebab-case `## op-name` sections, no `commands/` | Split into individual `commands/*.md` |
| Offload to References | Sections >20 lines (Output, Error Handling, etc.), no `references/` | Move to `references/` with relative link |
| DCI Opportunities | File checks, git ops, or tool detection without DCI | Add `` !`command` `` directives |
