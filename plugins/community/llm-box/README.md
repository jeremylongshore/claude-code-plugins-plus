<div align="center">
  <img src="docs/logo.svg" alt="llm-box" width="200" />
  <h1>llm-box</h1>
  <p><strong>Build terminal workflows using plain English</strong></p>
<p>Describe what you want. llm-box generates YAML from patterns and executes it.</p>

  <p>
    <a href="https://github.com/alib8b8/llm-box/releases">
      <img src="https://img.shields.io/github/v/release/alib8b8/llm-box?display_name=tag&include_prereleases&style=flat-square" alt="release" />
    </a>
    <a href="https://golang.org/">
      <img src="https://img.shields.io/badge/Go-1.25+-00ADD8?style=flat-square" alt="Go" />
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="license" />
    </a>
    <a href="https://github.com/alib8b8/llm-box/actions/workflows/release.yml">
      <img src="https://github.com/alib8b8/llm-box/actions/workflows/release.yml/badge.svg" alt="CI status" />
    </a>
  </p>

<p>
  <strong>English</strong> |
  <a href="README.zh-CN.md">中文</a> |
  <a href="README.ru.md">Русский</a> |
  <a href="README.fr.md">Français</a> |
  <a href="README.ja.md">日本語</a> |
  <a href="README.ko.md">한국어</a> |
  <a href="README.es.md">Español</a> |
  <a href="README.ar.md">العربية</a> |
  <a href="README.hi.md">हिन्दी</a>
</p>
</div>

---

## 🚀 Quick Start

Install in 60 seconds:

```bash
# Linux/macOS
curl -sL https://raw.githubusercontent.com/alib8b8/llm-box/main/install.sh -o install.sh
bash install.sh

# Windows
# Download from releases: https://github.com/alib8b8/llm-box/releases/latest
Invoke-WebRequest -Uri "https://github.com/alib8b8/llm-box/releases/latest/download/llm-box-windows-amd64.exe" -OutFile llm-box.exe
```

Create and run your first workflow:

```bash
# Create (pattern-based workflow scaffolding)
llm-box create "fetch Hacker News top stories and save to stories.txt"

# Run
llm-box run hn_workflow.yaml
```

---

## 💡 Why Choose llm-box?

**Not Another AI Chatbot**

Most workflow tools force developers to choose between:

| Approach | Problem |
|----------|---------|
| Complex bash scripts | Hard to read, maintain, share |
| Heavy visual builders | Slow, opaque, require GUI |
| Endless config files | Steep learning curve, verbose syntax |

**llm-box is not an AI assistant — it's a deterministic execution engine.**

- ✅ **Predictable & Auditable** — Workflow steps are deterministic
- ✅ **Local-First** — Your data never leaves your terminal
- ✅ **Transparent & Reproducible** — Same workflow produces same results
- ✅ **MIT Open Source** — No vendor lock-in, no hidden barriers

> 💡 We use AI to understand your intent, but core execution runs on deterministic code.

---

## ✨ Features

- **Terminal First** - Native CLI, works anywhere you have a terminal
- **Plain English Workflows** - Define what you want, not how to do it
- **Single Binary** - Zero dependencies, install and run
- **Workflow Reusability** - Save, version, and share your workflows
- **Multi-LLM Support** - Ollama (local), DeepSeek API (cloud), and more
- **Extensible Node System** - Build custom nodes in any language
- **MIT Licensed** - Open source, use freely
- **Cross Platform** - Linux, macOS, Windows supported
- **Beautiful TUI** - Real-time progress feedback

---

## 🔄 llm-box vs Alternatives

| Feature | llm-box | Dify/n8n | Claude Code | CrewAI |
|---------|---------|----------|-------------|--------|
| **Interface** | Terminal + YAML | Visual GUI | Chat | Code |
| **Execution** | Deterministic | AI-driven | AI autonomous | AI orchestration |
| **Setup** | 60 seconds | Hours | Minutes | Hours |
| **Transparency** | 100% | Medium | Low | Medium |
| **Reproducibility** | 100% | Variable | Variable | Variable |
| **Best For** | Automation | Enterprise apps | Coding | Research |

**Choose llm-box when you need:** repeatable, auditable workflows with AI assistance without losing control.

> 📖 [Full comparison →](docs/comparison.md)

---

## 🎬 Demo

![llm-box demo](docs/demo.svg)

> **Generate your own demo**
> Run `vhs docs/demo.tape` to create a high-quality GIF.

---

## 🔧 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User (Terminal)                      │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Natural Language Parser                   │
│            "Fetch HN stories and summarize"               │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     Task Planner                           │
│         Convert intent into executable steps              │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Execution Engine                          │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌───────────┐ │
│  │fetch_url │ │transform  │ │execute_cmd │ │file_write│ │
│  └──────────┘ └───────────┘ └────────────┘ └───────────┘ │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌───────────┐ │
│  │ollama    │ │deepseek   │ │notify     │ │combine     │ │
│  └──────────┘ └───────────┘ └────────────┘ └───────────┘ │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌───────────┐ │
│  │transform │ │execute    │ │file_write  │ │custom node│ │
│  └──────────┘ └───────────┘ └────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                       Output                              │
│                 (Terminal / File / Notification)         │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
1. **Parser** - Interprets plain English commands
2. **Planner** - Breaks down into steps
3. **Engine** - Executes with dependency management
4. **Nodes** - Built-in and extensible actions
5. **Output** - Formatted results

---

## 📚 10 Real Use Cases

### 1. Daily GitHub Summary

**Goal:** Get an overview of your activity

**Input:**
```bash
llm-box create "fetch my recent GitHub activity and save summary to github-digest.md"
```

**Workflow:**
```yaml
name: GitHub Daily Digest
steps:
  - node: fetch_url
    params:
      url: https://github.com/your-username
  - node: transform
    params:
      operation: extract_repos_and_activity
  - node: file_write
    params:
      path: github-digest.md
```

---

### 2. Research Assistant

**Goal:** Collect and summarize technical docs

**Input:**
```bash
llm-box create "fetch 3 tech blog posts about containerization and save key takeaways"
```

**Workflow:**
```yaml
name: Research Assistant
steps:
  - node: fetch_url
    params:
      url: https://example.com/blog1
  - node: fetch_url
    params:
      url: https://example.com/blog2
  - node: fetch_url
    params:
      url: https://example.com/blog3
  - node: transform
    params:
      operation: combine_and_summarize
  - node: file_write
    params:
      path: research-notes.md
```

---

### 3. Documentation Generator

**Goal:** Auto-generate API docs

**Input:**
```bash
llm-box create "scan my Go project and generate API overview"
```

**Workflow:**
```yaml
name: Docs Generator
steps:
  - node: execute
    params:
      command: find . -name "*.go"
  - node: transform
    params:
      operation: extract_functions_and_types
  - node: file_write
    params:
      path: API.md
```

---

### 4. Log Monitor

**Goal:** Watch logs and notify on errors

**Input:**
```bash
llm-box create "monitor server logs for 5xx errors and alert"
```

**Workflow:**
```yaml
name: Log Monitor
steps:
  - node: execute
    params:
      command: tail -n 100 /var/log/server.log
  - node: transform
    params:
      operation: filter_errors
  - node: notify
    params:
      channel: stdout
```

---

### 5. Release Notes Creator

**Goal:** Generate changelog from commits

**Input:**
```bash
llm-box create "turn git commit history into release notes"
```

**Workflow:**
```yaml
name: Release Notes Generator
steps:
  - node: execute
    params:
      command: git log --oneline --since="2 weeks ago"
  - node: transform
    params:
      operation: group_by_commit_type
  - node: file_write
    params:
      path: RELEASE-NOTES.md
```

---

### 6. Data Collector

**Goal:** Aggregate data from multiple APIs

**Input:**
```bash
llm-box create "fetch weather and stock data, combine into report"
```

**Workflow:**
```yaml
name: Daily Report Generator
steps:
  - node: fetch_url
    params:
      url: https://api.weather.gov/forecast
  - node: fetch_url
    params:
      url: https://api.stock.example.com/quote/ABC
  - node: combine
    params:
      format: markdown
  - node: file_write
    params:
      path: daily-report.md
```

---

### 7. File Organizer

**Goal:** Auto-sort downloads folder

**Input:**
```bash
llm-box create "organize downloads folder by file type"
```

**Workflow:**
```yaml
name: Downloads Organizer
steps:
  - node: execute
    params:
      command: ls -la ~/Downloads
  - node: transform
    params:
      operation: group_by_extension
  - node: execute
    params:
      command: mkdir -p ~/Downloads/images ~/Downloads/documents
  - node: execute
    params:
      command: mv ~/Downloads/*.jpg ~/Downloads/*.png ~/Downloads/images/
```

---

### 8. Content Workflow

**Goal:** Prepare posts for publishing

**Input:**
```bash
llm-box create "take markdown post and generate HTML version"
```

**Workflow:**
```yaml
name: Content Processor
steps:
  - node: fetch_url
    params:
      url: file://post.md
  - node: transform
    params:
      operation: markdown_to_html
  - node: file_write
    params:
      path: post.html
```

---

### 9. DevOps Automation

**Goal:** Deploy with health checks

**Input:**
```bash
llm-box create "build docker image and deploy with health check"
```

**Workflow:**
```yaml
name: Zero Downtime Deploy
steps:
  - node: execute
    params:
      command: docker build -t my-service .
  - node: execute
    params:
      command: docker-compose up -d --no-deps my-service
  - node: execute
    params:
      command: sleep 30 && curl -f http://localhost/health
  - node: notify
    params:
      channel: stdout
```

---

### 10. Team Reporting

**Goal:** Weekly team metrics

**Input:**
```bash
llm-box create "compile weekly issue and commit stats"
```

**Workflow:**
```yaml
name: Team Weekly Report
steps:
  - node: execute
    params:
      command: gh issue list --repo my-org/my-repo --since "1 week ago" --state all
  - node: transform
    params:
      operation: count_by_label
  - node: execute
    params:
      command: git log --author="@my-team.com" --since="1 week ago" --oneline
  - node: file_write
    params:
      path: team-report.md
```

---

## ❓ FAQ

### What makes this different from Bash scripts?
llm-box adds structure, reusability, and a beautiful UI without losing the power of the terminal.

### Do I have to write YAML?
No! Describe what you want in plain English, and llm-box generates the YAML for you.

### Can I extend it?
Yes! Build custom nodes in any language. See [docs/contributing.md](docs/contributing.md).

### Is it production-ready?
v0.1 is early access. v1.0 (stable) is planned for Q3 2026.

### Which platforms are supported?
Linux, macOS, and Windows are fully supported.

### Where can I get help?
Open a [GitHub Discussion](https://github.com/alib8b8/llm-box/discussions) or file an issue.

---

## 🔧 Built-in Utility Nodes

llm-box includes many utility nodes for common tasks:

### file_read
Reads content from a local file.

**Parameters:**
- `path` (required) - Path to the file to read

**Example:**
```yaml
- node: file_read
  params:
    path: "input.txt"
```

### file_write
Writes input content to a file.

**Parameters:**
- `path` (required) - Path to the output file

**Example:**
```yaml
- node: file_write
  params:
    path: "output.txt"
```

### fetch_url
Fetches content from a URL.

**Parameters:**
- `url` (required) - URL to fetch

**Example:**
```yaml
- node: fetch_url
  params:
    url: "https://example.com"
```

### execute
Executes a shell command.

**Parameters:**
- `command` (required) - Command to execute

**Example:**
```yaml
- node: execute
  params:
    command: "ls -la"
```

### transform
Transforms input text (simple text operations).

**Parameters:**
- `operation` - Operation to perform (upper, lower, trim, etc.)

**Example:**
```yaml
- node: transform
  params:
    operation: "upper"
```

### combine
Combines multiple inputs.

### notify
Sends a desktop notification.

### json_parse
Parses JSON and extracts specific fields using dot notation.

**Parameters:**
- `path` (optional) - JSON path to extract (e.g., `user.name`, `items.[0].title`). If omitted, returns formatted JSON.

**Example:**
```yaml
- node: json_parse
  params:
    path: "name"
```

### http_request
Makes HTTP requests to any API endpoint. More flexible than `fetch_url`.

**Parameters:**
- `url` (required) - URL to request
- `method` (optional) - HTTP method (GET, POST, PUT, DELETE, etc.). Default: GET
- `body` (optional) - Request body. Uses step input if not provided
- `content_type` (optional) - Content-Type header. Default: application/json for POST/PUT
- `headers` (optional) - Additional headers, one per line, format: `Key: Value`
- `timeout` (optional) - Request timeout (e.g., `30s`, `2m`). Default: 60s

**Example:**
```yaml
- node: http_request
  params:
    url: "https://api.example.com/data"
    method: "POST"
    content_type: "application/json"
    headers: |
      Authorization: Bearer token123
      X-Custom-Header: value
```

### template_render
Renders a Go template with input data and parameters.

**Parameters:**
- `template` or `template_file` (required) - Template string or path to template file
- Additional params are available as template variables

**Available template functions:** `upper`, `lower`, `title`, `trim`, `split`, `join`, `len`, `replace`

**Example:**
```yaml
- node: template_render
  params:
    template: |
      # Report
      Name: {{ .name }}
      Date: {{ .date }}
    name: "My Report"
    date: "2026-06-29"
```

---

## 🤖 Supported LLMs

llm-box supports multiple LLM providers out of the box:

### DeepSeek (Cloud API)

The `deepseek` node calls DeepSeek's official API. Perfect when you don't want to run models locally.

**Setup:**
```bash
export DEEPSEEK_API_KEY="your-api-key"
```

**Example workflow:**
```yaml
name: DeepSeek Summary
steps:
  - node: fetch_url
    params:
      url: "https://example.com"
  - node: deepseek
    params:
      model: "deepseek-chat"
      system: "You are a helpful assistant that summarizes text concisely."
  - node: file_write
    params:
      path: "summary.txt"
```

**Available models:**
- `deepseek-chat` - General purpose chat model
- `deepseek-coder` - Code generation model
- `deepseek-reasoner` - Reasoning model (R1)

### Coze (Cloud API)

The `coze` node calls ByteDance's Coze API (OpenAI compatible). Great for Chinese language tasks.

**Setup:**
```bash
export COZE_API_KEY="your-api-key"
```

**Example workflow:**
```yaml
name: Coze Summary
steps:
  - node: fetch_url
    params:
      url: "https://example.com"
  - node: coze
    params:
      model: "glm-4"
      system: "You are a helpful assistant that summarizes text concisely."
  - node: file_write
    params:
      path: "summary.txt"
```

**Available models:**
- `glm-4` - General purpose high-performance model
- `glm-4v` - Vision-capable model
- `glm-3-turbo` - Fast and cost-effective model

### Zhipu GLM (Cloud API)

The `glm` node calls Zhipu AI's GLM API (OpenAI compatible). Native Chinese language support.

**Setup:**
```bash
export GLM_API_KEY="your-api-key"
```

**Example workflow:**
```yaml
name: GLM Summary
steps:
  - node: fetch_url
    params:
      url: "https://example.com"
  - node: glm
    params:
      model: "glm-4"
      system: "You are a helpful assistant that summarizes text concisely."
  - node: file_write
    params:
      path: "summary.txt"
```

**Available models:**
- `glm-4` - Flagship model with strong reasoning
- `glm-4v` - Vision language model
- `glm-3-turbo` - Fast, cost-effective option
- `glm-4-plus` - High intelligence, longer context

### Kimi (Cloud API)

The `kimi` node calls Moonshot AI's Kimi API (OpenAI compatible). Known for long context windows.

**Setup:**
```bash
export KIMI_API_KEY="your-api-key"
```

**Example workflow:**
```yaml
name: Kimi Summary
steps:
  - node: fetch_url
    params:
      url: "https://example.com"
  - node: kimi
    params:
      model: "moonshot-v1-8k"
      system: "You are a helpful assistant that summarizes text concisely."
  - node: file_write
    params:
      path: "summary.txt"
```

**Available models:**
- `moonshot-v1-8k` - 8K context, standard
- `moonshot-v1-32k` - 32K context, long documents
- `moonshot-v1-128k` - 128K context, massive files

### MiniMax (Cloud API)

The `minimax` node calls MiniMax's API (OpenAI compatible). Strong Chinese language understanding.

**Setup:**
```bash
export MINIMAX_API_KEY="your-api-key"
```

**Example workflow:**
```yaml
name: MiniMax Summary
steps:
  - node: fetch_url
    params:
      url: "https://example.com"
  - node: minimax
    params:
      model: "abab6.5s-chat"
      system: "You are a helpful assistant that summarizes text concisely."
  - node: file_write
    params:
      path: "summary.txt"
```

**Available models:**
- `abab6.5s-chat` - Fast & balanced
- `abab6.5t-chat` - Text focused
- `abab7-chat` - Latest generation

### Qwen (Cloud API)

The `qwen` node calls Alibaba's Tongyi Qianwen API (OpenAI compatible). Strong ecosystem integration with Alibaba Cloud.

**Setup:**
```bash
export QWEN_API_KEY="your-api-key"
```

**Example workflow:**
```yaml
name: Qwen Summary
steps:
  - node: fetch_url
    params:
      url: "https://example.com"
  - node: qwen
    params:
      model: "qwen-turbo"
      system: "You are a helpful assistant that summarizes text concisely."
  - node: file_write
    params:
      path: "summary.txt"
```

**Available models:**
- `qwen-turbo` - Fast & cost-effective
- `qwen-plus` - Balanced performance
- `qwen-max` - Maximum capability
- `qwen-long` - Long context (10M tokens)
- `qwen-vl-max` - Vision language model

### XVERSE (Cloud API)

The `xverse` node calls XVERSE's API (OpenAI compatible).

**Setup:**
```bash
export XVERSE_API_KEY="your-api-key"
```

**Available models:**
- `XVERSE-7B-Chat` - Lightweight fast model
- `XVERSE-13B-Chat` - Balanced performance
- `XVERSE-65B-Chat` - High capability

### Yi (Lingyiwanwu) (Cloud API)

The `yi` node calls Lingyiwanwu's Yi API (OpenAI compatible).

**Setup:**
```bash
export YI_API_KEY="your-api-key"
```

**Available models:**
- `yi-lightning` - Lightning fast
- `yi-large` - Large high-quality model
- `yi-medium` - Balanced
- `yi-vision` - Vision capability

### Baichuan (Cloud API)

The `baichuan` node calls Baichuan's API (OpenAI compatible).

**Setup:**
```bash
export BAICHUAN_API_KEY="your-api-key"
```

**Available models:**
- `Baichuan4` - Latest flagship model
- `Baichuan3-Turbo` - Fast & cost-effective
- `Baichuan2` - Previous generation

### InternLM (Open-Source) (Cloud API)

The `internlm` node calls Shanghai AI Lab's InternLM API (OpenAI compatible).

**Setup:**
```bash
export INTERNLM_API_KEY="your-api-key"
```

**Available models:**
- `internlm3-latest` - Latest generation
- `internlm2.5-latest` - v2.5 series
- `internlm2-latest` - v2 series
- `internlm-xcomposer` - Vision-language

### Mistral AI (Cloud API)

The `mistral` node calls Mistral AI's API (OpenAI compatible).

**Setup:**
```bash
export MISTRAL_API_KEY="your-api-key"
```

**Example workflow:**
```yaml
name: Mistral Summary
steps:
  - node: fetch_url
    params:
      url: "https://example.com"
  - node: mistral
    params:
      model: "mistral-large-latest"
      system: "You are a helpful assistant that summarizes text concisely."
  - node: file_write
    params:
      path: "mistral_summary.txt"
```

**Available models:**
- `mistral-large-latest` - Latest flagship model
- `mistral-medium-latest` - Balanced performance
- `mistral-small-latest` - Fast & cost-effective
- `open-mistral-nemo` - Open source model

### Xiaomi MiMo (Cloud API)

The `mimo` node calls Xiaomi MiMo's API (OpenAI compatible).

**Setup:**
```bash
export MIMO_API_KEY="your-api-key"
```

**Example workflow:**
```yaml
name: MiMo Summary
steps:
  - node: fetch_url
    params:
      url: "https://example.com"
  - node: mimo
    params:
      model: "mimo-v2.5-pro"
      system: "You are a helpful assistant that summarizes text concisely."
  - node: file_write
    params:
      path: "mimo_summary.txt"
```

**Available models:**
- `mimo-v2.5-pro` - Latest flagship model
- `mimo-v2.5-plus` - Enhanced version
- `mimo-v2.5-lite` - Lightweight version

### IMA Copilot (Cloud API)

The `ima` node connects to IMA Copilot's OpenAI-compatible API endpoint.

**Setup:**
```bash
export IMA_API_KEY="your-api-key"
export IMA_API_BASE="https://your-ima-endpoint/v1"
```

**Example workflow:**
```yaml
name: IMA Copilot Summary
steps:
  - node: fetch_url
    params:
      url: "https://example.com"
  - node: ima
    params:
      model: "gpt-4o"
      system: "You are a helpful assistant that summarizes text concisely."
  - node: file_write
    params:
      path: "summary.txt"
```

**Supported models:**
- `gpt-4o` - High capability
- `gpt-4o-mini` - Fast & cost-effective
- `gpt-4.1` - Latest generation
- `gpt-5` - Most capable

### FastGPT (Knowledge Base Platform)

The `fastgpt` node connects to [FastGPT](https://github.com/labring/FastGPT) knowledge base applications. Perfect for querying enterprise knowledge bases, documentation, and custom datasets.

**Setup:**
```bash
export FASTGPT_API_KEY="your-api-key"
export FASTGPT_BASE_URL="https://your-fastgpt-domain.com/api/v1"
```

**Example workflow:**
```yaml
name: FastGPT Knowledge Query
steps:
  - node: fastgpt
    params:
      app_id: "your-app-id"
      api_key: "your-api-key"
      endpoint: "https://your-fastgpt-domain.com/api/v1"
  - node: file_write
    params:
      path: "answer.txt"
```

**Parameters:**
- `app_id` - FastGPT application ID (required)
- `api_key` - API key (or set `FASTGPT_API_KEY` env var)
- `endpoint` - FastGPT API base URL (or set `FASTGPT_BASE_URL` env var)
- `chat_id` - Conversation ID for context persistence (optional)
- `system` - System prompt (optional)

**💡 Use cases:**
- Query enterprise documentation from the terminal
- Batch process knowledge base queries
- Build automated QA pipelines
- Combine with `file_read` to import local docs into FastGPT via API

### Ollama (Local)

The `ollama` node runs models locally via Ollama. Great for privacy and offline use.

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh -o ollama-install.sh
sh ollama-install.sh

# Pull a model
ollama pull llama3
```

### OpenAI Compatible (Any Provider)

The `openai` node works with **any** API that follows the OpenAI format — SiliconFlow, Together AI, 腾讯混元, and hundreds more.

**Setup:**
```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_BASE="https://api.siliconflow.cn/v1"
```

**Example — SiliconFlow (30+ models):**
```yaml
name: SiliconFlow Summary
steps:
  - node: fetch_url
    params:
      url: "https://example.com"
  - node: openai
    params:
      model: "deepseek-ai/DeepSeek-V3"
      endpoint: "https://api.siliconflow.cn/v1"
      system: "You are a helpful assistant that summarizes text concisely."
  - node: file_write
    params:
      path: "summary.txt"
```

**Example — OpenRouter (200+ models):**
```yaml
name: OpenRouter Summary
steps:
  - node: fetch_url
    params:
      url: "https://example.com"
  - node: openai
    params:
      model: "openai/gpt-4o"
      endpoint: "https://openrouter.ai/api/v1"
      system: "You are a helpful assistant that summarizes text concisely."
  - node: file_write
    params:
      path: "summary.txt"
```

**Setup for OpenRouter:**
```bash
export OPENAI_API_KEY="your-openrouter-api-key"
export OPENAI_API_BASE="https://openrouter.ai/api/v1"
```

**Works with:**
- [OpenRouter](https://openrouter.ai) - 200+ models from top providers
- SiliconFlow (硅基流动) - 30+ models, 0.5元/百万token起
- 腾讯混元 (Hunyuan)
- Together AI
- Anyscale
- Any OpenAI-compatible endpoint

---

## 🗺️ Roadmap

### v0.1 - Initial Release ✓
- [x] Basic workflow creation
- [x] Execution engine
- [x] Built-in nodes (fetch_url, file_write, ollama)
- [x] Terminal UI

### v0.2 - Multi-LLM & Plugin System
- [x] DeepSeek API node support
- [x] Coze API node support
- [x] Zhipu GLM API node support
- [x] Kimi (Moonshot) API node support
- [x] MiniMax API node support
- [x] Qwen (Tongyi Qianwen) API node support
- [x] XVERSE API node support
- [x] Yi (Lingyiwanwu) API node support
- [x] Baichuan API node support
- [x] InternLM (Shanghai AI Lab) API node support
- [x] Mistral AI API node support
- [x] Xiaomi MiMo API node support
- [x] IMA Copilot API node support
- [x] Universal OpenAI-compatible node (any provider)
- [x] More utility nodes: file_read, json_parse, template_render, http_request
- [x] FastGPT knowledge base platform integration
- [ ] Plugin system for custom nodes
- [ ] Workflow template library
- [ ] Workflow sharing via URL

### v0.3 - Team Features
- [ ] Team workflow repository
- [ ] Workflow versioning
- [ ] Cloud sync (optional)

### v0.4 - Enterprise
- [ ] Access control
- [ ] Audit logging
- [ ] Scheduled workflows

### v1.0 - Stable
- [ ] Production readiness
- [ ] Comprehensive docs
- [ ] Long-term support

---

## 🤝 Contributing

We welcome contributors of all skill levels!

### Ways to Contribute
- **Go Developers** - Build new nodes, improve core
- **Documentation** - Improve docs, write tutorials
- **Workflow Designers** - Share your workflows
- **Community Builders** - Help others on Discussions

### Quick Start

```bash
git clone https://github.com/alib8b8/llm-box.git
cd llm-box
go mod download
go test ./...
go build -o llm-box ./cmd/llm-box
./llm-box help
```

See [docs/contributing.md](docs/contributing.md) for guidelines.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for full details.

---

<div align="center">
  <p>If this project helps you, please give it a ⭐</p>
  <p>
    <a href="https://github.com/alib8b8/llm-box/stargazers">
      <img src="https://api.star-history.com/svg?repos=alib8b8/llm-box&type=Timeline" alt="Star History" />
    </a>
  </p>
</div>
