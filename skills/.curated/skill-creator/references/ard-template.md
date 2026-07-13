# ARD Template

Standard Architecture Requirements Document for all marketplace skills. Every ARD.md MUST follow this exact structure. No sections added, no sections removed.

---

```markdown
# ARD: {Skill Name}

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

{Where does this skill fit? What systems/services does it interact with? Include a simple text diagram if helpful.}

## Data Flow

1. **Input**: {What the skill receives — user request, files, context}
2. **Processing**: {What happens — steps, transformations, API calls}
3. **Output**: {What the skill produces — files, reports, deployments}

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| {What was decided} | {What was chosen} | {Why this over alternatives} |
| {What was decided} | {What was chosen} | {Why} |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| {tool from allowed-tools} | {Why this skill uses it} |
| {tool} | {Purpose} |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| {Category of error} | {How it's detected} | {What the skill does about it} |
| {Category} | {Detection} | {Recovery} |

## Extension Points

- {How users can customize or extend this skill's behavior}
- {Integration points with other skills or tools}
```
