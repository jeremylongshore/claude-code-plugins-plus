# klingai-hello-world

> Create first video generation with a simple example

## Directory Structure

```
klingai-hello-world/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    └── 🐍 first_video.py          # Python hello world video generation
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with step-by-step first video guide |
| `first_video.py` | 🐍 Python | Minimal example for generating first AI video |

## Summary

**Category:** onboarding
**Target Audience:** Developer new to Kling AI
**Trigger Phrases:** `klingai hello world`, `kling ai first video`, `klingai quickstart`, `test klingai`

### What This Skill Does

This skill provides a quick-start guide for generating your first AI video with Kling AI. It covers:

- Minimal code example for text-to-video generation
- Understanding async job submission and polling
- Retrieving and downloading generated video
- Verifying successful API integration

### Technical Success Criteria

- Successfully generate and retrieve a test video
- Understanding of job submission and status polling pattern
- Video URL retrieved and downloadable

### Business Success Criteria

- Quick validation of API integration readiness
- Developer confidence in Kling AI capabilities
- Foundation for more complex video generation

## Related Skills

- `klingai-install-auth` - Required auth setup before hello world
- `klingai-text-to-video` - Advanced text-to-video techniques
- `klingai-model-catalog` - Understanding model options
