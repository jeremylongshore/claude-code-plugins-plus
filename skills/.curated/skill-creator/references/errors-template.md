# Errors Template

Standard troubleshooting reference for all marketplace skills. Every references/errors.md MUST follow this format.

---

```markdown
# {Skill Name} — Common Errors

## {Error Category 1}

| Error | Cause | Fix |
|-------|-------|-----|
| {Error message or symptom} | {Root cause} | {Specific fix command or action} |
| {Error} | {Cause} | {Fix} |

## {Error Category 2}

| Error | Cause | Fix |
|-------|-------|-----|
| {Error} | {Cause} | {Fix} |
```

Categories should match the skill's domain. Examples:

- For GCP skills: Authentication Errors, API Errors, Deployment Errors, Quota Errors
- For database skills: Connection Errors, Query Errors, Permission Errors, Data Errors
- For CI/CD skills: Build Errors, Deploy Errors, Configuration Errors, Permission Errors
