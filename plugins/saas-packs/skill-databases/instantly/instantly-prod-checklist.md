# instantly-prod-checklist

> Validate all requirements before production deployment to prevent launch issues

## Directory Structure

```
instantly-prod-checklist/
├── SKILL.md
└── examples/
    ├── preflight_check.py
    ├── checklist.md
    ├── validation_suite.py
    └── approval_gate.sh
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Production readiness checklist and validation procedures |
| preflight_check.py | Python | Automated preflight validation before deployment |
| checklist.md | Markdown | Manual verification checklist for production |
| validation_suite.py | Python | Complete validation test suite |
| approval_gate.sh | Shell | Deployment approval gate with required checks |

## Summary

**Category:** CI/CD
**Target Audience:** Release managers preparing production deployments
**Trigger Phrases:** "instantly production checklist", "ready for production instantly", "pre-launch validation", "instantly go-live checklist", "production readiness instantly"
**Definition of Success (Technical):** All checklist items pass automated validation
**Definition of Success (Business):** Zero production incidents from preventable issues
**Production:** true
**Version:** 1.0.0
**License:** MIT
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
