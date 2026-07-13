# Implementation Template

Standard implementation guide for all marketplace skills. Every references/implementation.md MUST follow this format.

---

```markdown
# {Skill Name} — Implementation Guide

## How the Skill Works

{3-5 numbered steps describing the skill's internal workflow from invocation to output.}

## Project/File Structure

\`\`\`
{Directory tree showing what the skill creates, reads, or manages}
\`\`\`

## Core Patterns

{Explain the main technical patterns used. Code blocks showing real implementations.}

## Configuration Reference

| Setting | Required | Default | Purpose |
|---------|----------|---------|---------|
| {env var or config key} | {Yes/No} | {value} | {what it controls} |

## Testing Strategy

{How to validate the skill's output — commands to run, what to check, pass/fail criteria.}

## Deployment Pipeline

{If applicable: local dev → staging → production flow with commands at each stage.}
```

Rules:

- Write from the perspective of how this specific skill works, not generic patterns
- Include real commands, real API calls, real config values
- Keep under 200 lines — this is a reference, not a textbook
