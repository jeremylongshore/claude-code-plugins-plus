# Skill Creator

Create and validate production-grade agent skills aligned with the 2026 AgentSkills.io spec and Anthropic best practices. Includes a 100-point marketplace grading rubric.

## Features

- **Create mode**: Build complete skill packages from scratch with interactive wizard
- **Validate mode**: Grade existing skills against the Intent Solutions 100-point rubric
- **Auto-fix**: Automatically apply improvements to boost marketplace scores
- **Eval-driven**: Built-in evaluation framework for testing skill quality

## Install

```bash
ccpi install skill-creator
```

Or copy the `skills/skill-creator/` directory to `~/.claude/skills/` for standalone use.

## Usage

```
/skill-creator              # Interactive skill creation
/skill-creator validate     # Grade an existing skill
```

## What's Included

| Directory | Purpose |
|-----------|---------|
| `skills/skill-creator/SKILL.md` | Main skill (works standalone) |
| `references/` | 6 spec documents (frontmatter, validation rules, workflows, etc.) |
| `scripts/validate-skill.py` | Automated validation + 100-point grading |
| `templates/skill-template.md` | SKILL.md skeleton for new skills |

## Grading Rubric (100 points)

| Pillar | Max Points |
|--------|-----------|
| Progressive Disclosure | 30 |
| Ease of Use | 25 |
| Utility | 20 |
| Spec Compliance | 15 |
| Writing Style | 10 |
| Modifiers | +/-5 |

Grade scale: A (90+), B (80-89), C (70-79), D (60-69), F (<60)

## Author

Jeremy Longshore ([@jeremylongshore](https://github.com/jeremylongshore))

## License

MIT
