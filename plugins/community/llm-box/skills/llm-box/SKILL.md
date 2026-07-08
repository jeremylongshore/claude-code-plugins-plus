---
name: workflow
description: Generate and execute terminal workflows using llm-box. Use when the user wants to automate multi-step terminal tasks, chain commands, fetch URLs, process data, create reusable pipelines, or build CI/CD-like automation locally.
invocation: both
---

# llm-box Workflow Skill

## When to Use

Use this skill when the user wants to:

- **Automate multi-step terminal tasks** — fetching data, processing it, saving results
- **Create reusable pipelines** — workflows that can be run repeatedly
- **Chain commands** — where output of one step feeds into the next
- **Batch process data** — transform, filter, combine multiple data sources
- **Integrate LLMs into automation** — use Ollama, DeepSeek, or OpenAI-compatible models
- **Replace fragile bash scripts** — with structured, auditable YAML workflows

## How llm-box Works

```
Plain English description → YAML workflow → Execute with progress
```

llm-box generates a YAML workflow file from a natural language description.
The workflow is deterministic and reproducible — same workflow always produces
the same result. Users can edit the YAML by hand if they want to tweak things.

## Quick Reference

### CLI Commands

```bash
# Generate a workflow from plain English
llm-box create "<description>"

# Run a workflow file
llm-box run <workflow.yaml>

# List all available nodes
llm-box list

# Validate a workflow file without running
llm-box validate <workflow.yaml>

# Run in safe mode (disables execute node)
llm-box --safe-mode run <workflow.yaml>

# Dry run (show steps without executing)
llm-box --dry-run run <workflow.yaml>
```

### Available Nodes

**Utility Nodes:**
| Node | Description |
|------|-------------|
| `fetch_url` | Fetch content from a URL (with SSRF protection) |
| `http_request` | Full HTTP client — any method, headers, body |
| `file_read` | Read file contents |
| `file_write` | Write content to a file |
| `execute` | Run shell commands (configurable allowlist) |
| `json_parse` | Extract fields from JSON using dot notation |
| `template_render` | Render Go templates with variables |
| `transform` | Transform text (uppercase, lowercase, trim, replace, regex) |
| `combine` | Merge multiple inputs into one |
| `notify` | Print or send notifications |

**LLM Nodes:**
| Node | Provider |
|------|----------|
| `ollama` | Local models via Ollama |
| `deepseek` | DeepSeek API |
| `openai` | OpenAI-compatible |
| `qwen` | Alibaba Qwen |
| `glm` | Zhipu GLM |
| `kimi` | Moonshot Kimi |
| `mistral` | Mistral AI |
| `yi` | 01.AI Yi |

**Control Nodes:**
| Node | Description |
|------|-------------|
| `condition` | Conditional execution based on expression |
| `call` | Call another workflow file (nested) |

## YAML Workflow Structure

```yaml
name: my-workflow
description: What this workflow does
vars:
  api_key: "your-api-key"
steps:
  - node: fetch_url
    params:
      url: "https://api.example.com/data"
  - node: json_parse
    params:
      path: "result.items.[0].name"
  - node: file_write
    params:
      path: "output.txt"
  - node: notify
    condition: "{{.output}} != ''"
    params:
      message: "Done!"
```

### Step Features

- **`condition`**: Go template expression, step runs only if true
- **`retry`**: Number of retries on failure
- **`delay`**: Delay between retries (e.g., "2s", "1m")
- **`parallel`**: Run multiple steps concurrently
- **`_timeout`**: Per-step timeout (e.g., "30s")

## Workflow Generation Guidelines

When generating a workflow for the user:

1. **Identify the steps** — break the task into discrete operations
2. **Choose the right nodes** — prefer specific nodes over `execute` when possible
3. **Chain with variables** — use `{{.steps[N].output}}` to reference previous outputs
4. **Add error handling** — use `condition` and `retry` where appropriate
5. **Keep it readable** — add a `description` field, use meaningful step names

### Common Patterns

**Fetch and Save:**
```yaml
steps:
  - node: fetch_url
    params:
      url: "https://example.com/data"
  - node: file_write
    params:
      path: "data.txt"
```

**Fetch, Parse, and Summarize:**
```yaml
steps:
  - node: fetch_url
    params:
      url: "https://example.com/article"
  - node: ollama
    params:
      model: "llama3"
      prompt: "Summarize: {{.steps[0].output}}"
  - node: file_write
    params:
      path: "summary.md"
```

**Multi-source Aggregation:**
```yaml
steps:
  - parallel:
      - node: fetch_url
        params:
          url: "https://api1.example.com"
      - node: fetch_url
        params:
          url: "https://api2.example.com"
  - node: combine
    params:
      separator: "\n"
  - node: ollama
    params:
      model: "llama3"
      prompt: "Analyze: {{.steps[1].output}}"
```

## Security Notes

- Built-in SSRF protection (URL validation, DNS rebinding checks)
- Path traversal protection (sandboxed paths, symlink resolution)
- Command injection prevention (shell metachar filtering, optional allowlist)
- Resource limits (file size, response body, step count, timeouts)
- Safe mode disables the `execute` node entirely

## Installation

```bash
# Linux/macOS
curl -sL https://raw.githubusercontent.com/alib8b8/llm-box/main/install.sh -o install.sh
bash install.sh

# Or via Go
go install github.com/alib8b8/llm-box/cmd/llm-box@latest
```