# klingai-ci-integration

> Integrate Kling AI video generation into CI/CD pipelines

## Directory Structure

```
klingai-ci-integration/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 📄 github-actions.yml      # GitHub Actions workflow
    ├── 📄 gitlab-ci.yml           # GitLab CI configuration
    └── 🐍 ci_helper.py            # CI helper utilities
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with CI/CD integration guide |
| `github-actions.yml` | 📄 YAML | GitHub Actions workflow template |
| `gitlab-ci.yml` | 📄 YAML | GitLab CI pipeline template |
| `ci_helper.py` | 🐍 Python | Helper functions for CI environments |

## Summary

**Category:** cicd
**Target Audience:** DevOps engineer
**Trigger Phrases:** `klingai ci`, `kling ai github actions`, `klingai gitlab`, `automate klingai`

### What This Skill Does

This skill integrates Kling AI video generation into CI/CD pipelines. It covers:

- GitHub Actions workflow configuration
- GitLab CI pipeline setup
- Secrets management in CI
- Artifact handling for generated videos
- Caching strategies for efficiency
- Pipeline triggers and scheduling

### Technical Success Criteria

- Automated video generation in CI pipeline
- Secrets properly managed
- Artifacts stored and accessible

### Business Success Criteria

- Streamlined content production workflow
- Automated video generation on demand
- Consistent output quality

## Related Skills

- `klingai-storage-integration` - Store CI-generated videos
- `klingai-webhook-config` - CI notifications
- `klingai-batch-processing` - Batch CI jobs
