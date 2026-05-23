# Model Selection By Task

## Model Selection by Task

### Completions (Tab)

```
Recommended: GPT-3.5 Turbo or Cursor-small
- Fast response time critical
- Context window usually sufficient
- Cost effective for high volume

Settings:
{
  "cursor.completion.model": "gpt-3.5-turbo"
}
```

### Chat

```
Task-based selection:

Quick questions → GPT-3.5 Turbo
Code review → GPT-4 Turbo
Explanations → Claude 3.5 Sonnet
Complex architecture → GPT-4 or Claude Opus
Debugging → GPT-4 Turbo (large context)
```

### Composer

```
Recommended: GPT-4 Turbo or Claude 3.5 Sonnet
- Multi-file edits need accuracy
- Large context for project understanding
- Quality over speed

Settings:
{
  "cursor.composer.model": "gpt-4-turbo"
}
```
