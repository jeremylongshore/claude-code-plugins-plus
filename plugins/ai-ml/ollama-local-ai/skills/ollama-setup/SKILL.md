---
name: ollama-setup
description: |
  Auto-configure Ollama when user needs local LLM deployment, free AI alternatives,
  or wants to eliminate OpenAI/Anthropic API costs. Trigger phrases: "install ollama",
  "local AI", "free LLM", "self-hosted AI", "replace OpenAI", "no API costs"
allowed-tools: Read, Write, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Ollama Setup Skill

## Purpose

Automatically detect when users need local AI deployment and guide them through Ollama installation. Eliminates paid API dependencies.

## Activation Triggers

- "install ollama"
- "local AI models"
- "free alternative to OpenAI"
- "self-hosted LLM"
- "run AI locally"
- "eliminate API costs"
- "privacy-first AI"
- "offline AI models"

## Skill Workflow

### 1. Detect Need for Local AI

When user mentions:
- High API costs
- Privacy concerns
- Offline requirements
- OpenAI/Anthropic alternatives
- Self-hosted infrastructure

**→ Activate this skill**

### 2. Assess System Requirements

```bash
# Check OS
uname -s

# Check available memory
free -h  # Linux
vm_stat  # macOS

# Check GPU
nvidia-smi  # NVIDIA
system_profiler SPDisplaysDataType  # macOS
```

### 3. Recommend Appropriate Models

**8GB RAM:**
- llama3.2:7b (4GB)
- mistral:7b (4GB)
- phi3:14b (8GB)

**16GB RAM:**
- codellama:13b (7GB)
- mixtral:8x7b (26GB quantized)

**32GB+ RAM:**
- llama3.2:70b (40GB)
- codellama:34b (20GB)

### 4. Installation Process

**macOS:**
```bash
brew install ollama
brew services start ollama
ollama pull llama3.2
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl start ollama
ollama pull llama3.2
```

**Docker:**
```bash
docker run -d \\
  -v ollama:/root/.ollama \\
  -p 11434:11434 \\
  --name ollama \\
  ollama/ollama

docker exec -it ollama ollama pull llama3.2
```

### 5. Verify Installation

```bash
ollama list
ollama run llama3.2 "Say hello"
curl http://localhost:11434/api/tags
```

### 6. Integration Examples

**Python:**
```python
import ollama

response = ollama.chat(
    model='llama3.2',
    messages=[{'role': 'user', 'content': 'Hello!'}]
)
print(response['message']['content'])
```

**Node.js:**
```javascript
const ollama = require('ollama')

const response = await ollama.chat({
  model: 'llama3.2',
  messages: [{ role: 'user', content: 'Hello!' }]
})
```

**cURL:**
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Hello!"
}'
```

## Common Use Cases

### Replace OpenAI
```python
# Before (Paid)
from openai import OpenAI
client = OpenAI(api_key="...")

# After (Free)
import ollama
response = ollama.chat(model='llama3.2', ...)
```

### Replace Anthropic Claude
```python
# Before (Paid)
from anthropic import Anthropic
client = Anthropic(api_key="...")

# After (Free)
import ollama
response = ollama.chat(model='mistral', ...)
```

### Code Generation
```bash
ollama pull codellama
ollama run codellama "Write a Python REST API"
```

## Cost Comparison

**OpenAI GPT-4:**
- Input: $0.03/1K tokens
- Output: $0.06/1K tokens
- 1M tokens/month = $30-60

**Ollama:**
- Setup: Free
- Usage: $0 (hardware you already own)
- Savings: $30-60/month ✓

## Performance Expectations

**With GPU (NVIDIA/Metal):**
- 7B models: 50-100 tokens/sec
- 13B models: 30-60 tokens/sec
- 34B models: 20-40 tokens/sec

**CPU Only:**
- 7B models: 10-20 tokens/sec
- 13B models: 5-10 tokens/sec
- 34B models: 2-5 tokens/sec

## Troubleshooting

### Out of Memory
```bash
# Use quantized models
ollama pull llama3.2:7b-q4  # 4-bit (smaller)
```

### Slow Performance
```bash
# Use smaller model
ollama pull mistral:7b  # Faster than 70B
```

### Model Not Found
```bash
# Pull model first
ollama pull llama3.2
ollama list  # Verify
```

## Success Metrics

After skill execution, user should have:
- ✅ Ollama installed and running
- ✅ At least one model downloaded
- ✅ Successful test inference
- ✅ Integration code examples
- ✅ Zero ongoing API costs

## Privacy Benefits

- Data never leaves local machine
- No API keys required
- No usage tracking
- GDPR/HIPAA compliant (local only)
- Offline capable

## When NOT to Use This Skill

- User needs latest GPT-4 specifically
- User has <8GB RAM
- User needs real-time updates (like web search)
- User wants Claude Code itself (requires Anthropic API)

## Related Skills

- `local-llm-wrapper` - Generic local LLM integration
- `ai-sdk-agents` - AI SDK with Ollama support
- `privacy-first-ai` - Privacy-focused AI workflows
