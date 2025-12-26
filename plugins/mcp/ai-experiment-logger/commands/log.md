---
name: log
description: Log a new AI experiment with terminal report
shortcut: loge
---
# Log AI Experiment

When the user runs `/log-exp` or `/log`, help them log a new AI experiment by gathering the following information:

## Required Information

1. **AI Tool Used** - e.g., "ChatGPT o1-preview", "Claude Sonnet 3.5", "Gemini Pro"
2. **Prompt/Query** - What they asked the AI
3. **Result Summary** - Brief summary of the AI's response
4. **Effectiveness Rating** - 1 (poor) to 5 (excellent)
5. **Tags** (optional) - Comma-separated tags like "code-generation, python, debugging"
6. **Date** (optional) - Defaults to now if not provided

## Process

1. Ask for the information conversationally (don't make it feel like a form)
2. Once you have all required info, use the `log_experiment` MCP tool
3. Display a formatted terminal report showing:
   - ✅ Success confirmation
   - 📊 Experiment ID
   - 🤖 AI Tool
   - ⭐ Rating
   - 🏷️  Tags
   - 📅 Date/Time

## Example Interaction

```
User: /log-exp