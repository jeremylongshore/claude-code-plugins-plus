# Geepers

Multi-agent orchestration system with MCP tools and Claude Code plugin agents.

## Installation

### From PyPI (MCP tools)
```bash
pip install geepers

# With optional dependencies
pip install geepers[all]
pip install geepers[anthropic,openai]
```

### As Claude Code Plugin (agents)
```bash
/plugin add lukeslp/geepers
```

## What's Included

### 43 Specialized Agents

Markdown-defined agents for Claude Code that provide specialized workflows:

| Category | Agents | Purpose |
|----------|--------|---------|
| **Master** | conductor_geepers | Intelligent routing to specialists |
| **Checkpoint** | scout, repo, status, snippets, orchestrator | Session maintenance |
| **Deploy** | caddy, services, validator, orchestrator | Infrastructure |
| **Quality** | a11y, perf, api, deps, critic, orchestrator | Code audits |
| **Fullstack** | db, design, react, orchestrator | End-to-end features |
| **Research** | data, links, diag, citations, orchestrator | Data gathering |
| **Games** | game, gamedev, godot, orchestrator | Game development |
| **Corpus** | corpus, corpus_ux, orchestrator | Linguistics/NLP |
| **Web** | flask, orchestrator | Web applications |
| **Python** | pycli, orchestrator | Python projects |

### 90+ MCP Tools

Six specialized MCP servers expose tools for:

- **geepers-unified** - All tools in one server
- **geepers-providers** - 13 LLM providers (Anthropic, OpenAI, xAI, etc.)
- **geepers-data** - 29+ data sources (Census, arXiv, GitHub, NASA, etc.)
- **geepers-cache** - Redis-backed caching
- **geepers-utility** - Document parsing, citations, TTS
- **geepers-websearch** - Multi-engine web search

## FREE Alternative: Use Ollama for Local LLM

**Want to run geepers without paying for LLM APIs?** Replace Anthropic/OpenAI/xAI with Ollama for $0/month.

### Quick Comparison

| Component | Paid (Cloud APIs) | FREE (Ollama) |
|-----------|-------------------|---------------|
| **LLM Provider** | Anthropic/OpenAI/xAI | Ollama (local) |
| **Monthly Cost** | $50-200/mo | **$0/mo** |
| **Privacy** | Data sent to cloud | 100% local |
| **API Keys** | Required (3+ keys) | None required |
| **Rate Limits** | Yes (varies by tier) | Unlimited |
| **Latency** | 2-5s (network) | 1-3s (local) |

**Savings: $600-2,400/year** for multi-agent orchestration.

### Why Ollama for Geepers?

**Benefits:**
- **Zero Cost:** No API usage fees for 43 agents
- **Privacy:** All 90+ MCP tools run locally
- **Unlimited:** Run as many agent calls as needed
- **Offline:** No internet required after model download
- **GDPR/HIPAA:** Compliant by default (local-only)

**Recommended Models:**
- **llama3.2:7b** - Best for general agents (4GB)
- **mistral:7b** - Fast and efficient (4GB)
- **codellama:13b** - Code-focused agents (7GB)
- **mixtral:8x7b** - Advanced reasoning (26GB)

### Setup Guide

#### 1. Install Ollama

```bash
# macOS
brew install ollama
brew services start ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl start ollama

# Pull model (4GB download)
ollama pull llama3.2
```

See [ollama-local-ai](../../ai-ml/ollama-local-ai/) plugin for detailed setup.

#### 2. Install Geepers with Local LLM Support

```bash
# Install without paid provider dependencies
pip install geepers

# No need for [anthropic,openai] extras!
```

#### 3. Configure Ollama as LLM Provider

Create `~/.geepers/config.yaml`:

```yaml
llm:
  provider: ollama
  base_url: http://localhost:11434
  model: llama3.2
  temperature: 0.7

# No API keys required!
```

#### 4. Update MCP Config

```json
{
  "mcpServers": {
    "geepers": {
      "command": "geepers-unified",
      "env": {
        "GEEPERS_LLM_PROVIDER": "ollama",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "llama3.2"
      }
    }
  }
}
```

### Cost Comparison: 43 Agents

#### Cloud APIs (Anthropic/OpenAI)

```
43 agents × 1000 calls/month × $0.002/call = $86/month
Annual cost: $1,032
```

**Required API Keys:**
- Anthropic Claude API: $50-100/mo
- OpenAI GPT-4: $30-80/mo
- xAI Grok: $20-50/mo
- **Total: $100-230/mo**

#### Ollama (Local LLM)

```
43 agents × unlimited calls/month × $0 = $0/month
Annual cost: $0
```

**Required:**
- Hardware you already own
- One-time model download (4-26GB)
- **Total: $0/mo**

**Savings: $1,200-2,760/year**

### Migration Examples

#### Before (Paid APIs)

```bash
# Install with paid dependencies
pip install geepers[anthropic,openai]

# Set API keys
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export XAI_API_KEY=xai-...
```

**Monthly Cost:** $100-230

#### After (Ollama)

```bash
# Install without paid dependencies
pip install geepers

# Start Ollama (one-time setup)
ollama pull llama3.2
ollama serve

# Configure geepers
export GEEPERS_LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
```

**Monthly Cost:** $0

### Real Use Case: Multi-Agent Session

**Scenario:** Running geepers_orchestrator_checkpoint (5 agent calls per session)

#### Cloud APIs Version
```python
# Using Anthropic Claude
import anthropic

client = anthropic.Anthropic(api_key="sk-ant-...")
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Scout the repo"}]
)
```

**Cost per session:** 5 calls × $0.002 = **$0.01**
**Monthly (100 sessions):** **$1.00**
**Annual:** **$12.00**

#### Ollama Version
```python
# Using local Ollama
import ollama

response = ollama.chat(
    model='llama3.2',
    messages=[{"role": "user", "content": "Scout the repo"}]
)
```

**Cost per session:** 5 calls × $0 = **$0.00**
**Monthly (100 sessions):** **$0.00**
**Annual:** **$0.00**

**Same intelligence, zero cost.**

### Performance Comparison

| Metric | Cloud APIs | Ollama (Local) |
|--------|-----------|----------------|
| **Response Time** | 2-5s | 1-3s (with GPU) |
| **Throughput** | Rate limited | Unlimited |
| **Privacy** | Cloud processed | 100% local |
| **Offline** | ❌ Requires internet | ✅ Works offline |
| **Cost (1M tokens)** | $10-30 | $0 |

### Agent-Specific Recommendations

**Fast Agents (scout, status, snippets):**
```bash
ollama pull llama3.2:7b  # Fast, 4GB
```

**Code Agents (pycli, react, db, flask):**
```bash
ollama pull codellama:13b  # Code-optimized, 7GB
```

**Research Agents (data, citations, corpus):**
```bash
ollama pull mixtral:8x7b  # Advanced reasoning, 26GB
```

**Game Dev Agents (game, godot, gamedev):**
```bash
ollama pull llama3.2:7b  # Balanced, 4GB
```

### When to Use Cloud vs Local

**Use Cloud APIs (Anthropic/OpenAI) if:**
- You need latest GPT-4 Turbo or Claude Opus specifically
- Your hardware has <8GB RAM
- You need real-time web search results
- Budget allows $100-230/month

**Use Ollama (Local LLM) if:**
- You want $1,200-2,760/year savings
- You need privacy/compliance (HIPAA, GDPR, SOC2)
- You have 8GB+ RAM (16GB+ recommended)
- You want unlimited agent calls
- You need offline capability

### Hybrid Approach

**Best of both worlds:** Use Ollama for 90% of calls, cloud APIs for specialized tasks.

```yaml
# ~/.geepers/config.yaml
llm:
  default_provider: ollama  # $0/mo for most calls
  fallback_provider: anthropic  # Only when needed

providers:
  ollama:
    base_url: http://localhost:11434
    model: llama3.2
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-5-sonnet-20241022
```

**Cost Reduction:** ~90% savings ($10-23/mo instead of $100-230/mo)

### Resources

- **Ollama Setup:** Use `/setup-ollama` command from [ollama-local-ai](../../ai-ml/ollama-local-ai/) plugin
- **Ollama Docs:** [ollama.com/docs](https://ollama.com/docs)
- **Geepers Docs:** [github.com/lukeslp/geepers](https://github.com/lukeslp/geepers)
- **Model Library:** [ollama.com/library](https://ollama.com/library)

**Bottom Line:** For 43 specialized agents running locally, Ollama saves $1,200-2,760/year with comparable performance.

---

## Configuration

### Claude Code MCP Config

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "geepers": {
      "command": "geepers-unified"
    }
  }
}
```

### Environment Variables

```bash
# LLM Providers
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
XAI_API_KEY=...

# Data Sources
GITHUB_TOKEN=...
NASA_API_KEY=...
CENSUS_API_KEY=...
```

## Usage

### Using Agents in Claude Code

```
@geepers_scout          # Quick project reconnaissance
@geepers_caddy          # Caddy configuration changes
@geepers_orchestrator_checkpoint  # End-of-session cleanup
```

### Using MCP Tools

Once configured, tools are available via the MCP protocol.

## Development

```bash
# Clone and install in dev mode
git clone https://github.com/lukeslp/geepers
cd geepers
pip install -e .

# Run tests
pytest
```

## License

MIT License - Luke Steuber
