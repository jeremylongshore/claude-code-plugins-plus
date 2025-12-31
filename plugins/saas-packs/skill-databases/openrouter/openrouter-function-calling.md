# openrouter-function-calling

> Implement function calling and tool use with OpenRouter models

## Directory Structure

```
openrouter-function-calling/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 tool_definitions.py     # Tool/function schema definitions
    ├── 🐍 function_executor.py    # Function call execution handler
    └── ⚙️ tools_config.yaml       # Available tools configuration
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with function calling patterns |
| `tool_definitions.py` | 🐍 Python | JSON Schema tool definitions |
| `function_executor.py` | 🐍 Python | Safe function execution with validation |
| `tools_config.yaml` | ⚙️ YAML | Tool registry and access controls |

## Summary

**Category:** advanced
**Target Audience:** Developer building agents
**Trigger Phrases:** `openrouter function calling`, `openrouter tools`, `openrouter agents`, `openrouter structured output`

### What This Skill Does

This skill teaches function calling with OpenRouter models:

- Tool/function schema definitions (JSON Schema)
- Function call request handling
- Result formatting and return
- Error handling for invalid calls
- Multi-turn function calling conversations
- Model compatibility considerations

### Technical Success Criteria

- Functions called correctly with valid arguments
- Error handling for invalid or missing parameters
- Tool results properly formatted and returned

### Business Success Criteria

- Enable sophisticated AI-powered automation
- Reduce manual processing through agent workflows
- Build capable AI agents with tool access

## Related Skills

- `openrouter-model-catalog` - Model function calling support
- `openrouter-streaming-setup` - Streaming with tool calls
- `openrouter-context-optimization` - Context with tool results
