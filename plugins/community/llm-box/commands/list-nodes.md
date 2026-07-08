---
name: list-nodes
description: List all available workflow nodes
usage: /llm-box:list-nodes
---

# List Nodes

Show all available workflow nodes with descriptions.

## Usage

```
/llm-box:list-nodes
```

## What it does

Displays a categorized list of all available workflow nodes:
- Utility nodes (fetch_url, http_request, file_read, file_write, etc.)
- LLM nodes (ollama, deepseek, openai, qwen, glm, kimi, etc.)
- Control nodes (condition, call)

## Output

Each node is shown with:
- Name
- Description
- Available parameters

## Example output

```
Utility Nodes:
  fetch_url      - Fetch content from a URL
  http_request   - Full HTTP client
  file_read      - Read file contents
  file_write     - Write content to a file

LLM Nodes:
  ollama         - Local models via Ollama
  openai         - OpenAI-compatible APIs
  deepseek       - DeepSeek API

Control Nodes:
  condition      - Conditional execution
  call           - Call another workflow
```