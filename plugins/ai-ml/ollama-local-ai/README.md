# Ollama Local AI

**Free, self-hosted alternative to OpenAI, Anthropic, and paid LLM APIs**

Run powerful AI models locally with zero API costs. Complete privacy, unlimited usage, no subscriptions.

## Why Ollama?

- **💰 Free Forever** - No API keys, no subscriptions, no usage limits
- **🔒 Privacy First** - Your data never leaves your machine
- **⚡ Fast** - Local inference, no network latency
- **🎯 Production Ready** - Used by thousands of developers worldwide
- **🔧 Easy Setup** - One command installation

## Quick Start

```bash
# Install Ollama
/setup-ollama

# Or manually:
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2

# Start using it!
ollama run llama3.2
```

## Available Models

### Code Generation
- **CodeLlama 34B** - Best for code generation
- **Qwen2.5-Coder 32B** - Excellent coding assistant
- **DeepSeek-Coder 33B** - Strong code understanding

### General Purpose
- **Llama 3.2 70B** - Meta's flagship model
- **Mistral 7B** - Fast and efficient
- **Mixtral 8x7B** - High quality reasoning

### Specialized
- **Phi-3 14B** - Microsoft's efficient model
- **Gemma 27B** - Google's open model
- **Command-R 35B** - Cohere's command model

## Replace Paid APIs

### OpenAI GPT-4 → Llama 3.2 70B
```python
# Before (Paid - $0.03/1K tokens)
from openai import OpenAI
client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

# After (Free)
import ollama
response = ollama.chat(
    model="llama3.2",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Anthropic Claude → Mistral
```python
# Before (Paid - $0.015/1K tokens)
from anthropic import Anthropic
client = Anthropic(api_key="sk-ant-...")
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello"}]
)

# After (Free)
import ollama
response = ollama.chat(
    model="mistral",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## System Requirements

**Minimum:**
- 8GB RAM for 7B models
- 16GB RAM for 13B models
- 32GB RAM for 33B+ models

**Recommended:**
- NVIDIA GPU with 8GB+ VRAM (10x faster)
- Apple Silicon (M1/M2/M3) works great
- AMD GPUs supported

## ⚠️ Rate Limits & Resource Constraints

### No API Limits (Local Deployment)

| Constraint Type | Ollama (Local) | Cloud APIs (OpenAI/Anthropic) |
|----------------|----------------|-------------------------------|
| **Daily requests** | ∞ Unlimited | Limited by subscription tier |
| **Rate limiting** | ❌ None | ✅ Yes (RPM/TPM limits) |
| **Registration** | ❌ Not required | ✅ Email + payment required |
| **API keys** | ❌ Not needed | ✅ Required for all requests |
| **IP tracking** | ❌ N/A (local) | ✅ Yes (can get banned) |
| **Data privacy** | ✅ 100% local | ❌ Sent to cloud servers |

### Hardware-Based "Rate Limits"

Unlike API services, Ollama's constraints are **hardware-based**, not usage-based:

#### 1. **Memory Constraints**

| Model Size | RAM Required | Max Concurrent Requests | Notes |
|-----------|--------------|------------------------|--------|
| 7B models | 8GB | 1-2 agents | Basic usage |
| 13B models | 16GB | 1-2 agents | Good quality |
| 33B models | 32GB | 1 agent | High quality |
| 70B models | 64GB+ | 1 agent | Best quality, needs GPU |

**Multiple Agents on Same Machine:**
```python
# With 32GB RAM, you can run:
# - 3-4 agents using 7B models (8GB each)
# - 2 agents using 13B models (16GB each)
# - 1 agent using 33B model (32GB)

# Agent coordination example
from ollama import Client
import asyncio

async def agent_task(agent_name, model):
    client = Client()
    # Ollama automatically queues requests if busy
    response = await client.chat(
        model=model,
        messages=[{"role": "user", "content": f"Task for {agent_name}"}]
    )
    return response

# Run 3 agents concurrently on 32GB machine
tasks = [
    agent_task("agent1", "llama3.2"),  # ~8GB
    agent_task("agent2", "mistral"),   # ~4GB
    agent_task("agent3", "codellama"), # ~7GB
]
results = await asyncio.gather(*tasks)
```

#### 2. **Disk Space Requirements**

| Model | Download Size | Disk Space Required |
|-------|--------------|---------------------|
| Llama 3.2 7B | 4.7 GB | ~5 GB |
| Mistral 7B | 4.1 GB | ~4.5 GB |
| CodeLlama 34B | 19 GB | ~20 GB |
| Llama 3.2 70B | 40 GB | ~45 GB |
| Mixtral 8x7B | 26 GB | ~30 GB |

**Multi-Model Strategy:**
```bash
# Storage planning for 3 agents
ollama pull llama3.2      # 4.7 GB (general purpose)
ollama pull codellama     # 13 GB (code generation)
ollama pull mistral       # 4.1 GB (fast responses)
# Total: ~22 GB disk space
```

#### 3. **Inference Speed "Limits"**

| Hardware | Tokens/Second | Realistic Agents | Notes |
|----------|---------------|------------------|--------|
| **CPU only** | 2-5 tok/s | 1-2 | Slow but free |
| **Apple M1/M2** | 15-25 tok/s | 3-5 | Excellent performance |
| **NVIDIA RTX 3060** | 30-50 tok/s | 5-8 | Good mid-range GPU |
| **NVIDIA RTX 4090** | 80-120 tok/s | 10-15 | High-end GPU |

**Agent Best Practice - Queue Management:**
```python
# Smart request queuing for single GPU
from queue import Queue
import threading

class LocalLLMCoordinator:
    def __init__(self, max_concurrent=3):
        self.queue = Queue()
        self.max_concurrent = max_concurrent
        self.active_requests = 0

    def process_request(self, agent_id, prompt):
        # Wait if too many concurrent requests
        while self.active_requests >= self.max_concurrent:
            time.sleep(0.1)

        self.active_requests += 1
        try:
            response = ollama.chat(
                model='llama3.2',
                messages=[{"role": "user", "content": prompt}]
            )
            return response
        finally:
            self.active_requests -= 1

# Use coordinator for 10 agents on one machine
coordinator = LocalLLMCoordinator(max_concurrent=3)
```

### Registration & Setup Requirements

| Requirement | Status | Details |
|------------|--------|---------|
| **Email signup** | ❌ Not required | No account needed |
| **API key** | ❌ Not required | Runs locally |
| **Payment method** | ❌ Not required | 100% free |
| **Terms acceptance** | ✅ MIT License | Open source, permissive |
| **Installation** | ✅ Required | One command: `curl -fsSL https://ollama.com/install.sh \| sh` |

### Agent Strategies for Single Machine

**Scenario: 10 Agents on One Machine (32GB RAM, NVIDIA RTX 3060)**

```python
# Strategy 1: Shared model pool (most efficient)
class AgentPool:
    def __init__(self):
        self.model = "llama3.2"  # Single model loaded once
        self.cache = {}  # Shared response cache

    async def agent_request(self, agent_id, prompt):
        # Check cache first (avoid redundant inference)
        cache_key = hash(prompt)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Process request
        response = await ollama.chat_async(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

        # Cache for other agents
        self.cache[cache_key] = response
        return response

# 10 agents share one model = ~8GB RAM total
pool = AgentPool()
agents = [Agent(id=i, pool=pool) for i in range(10)]
```

**Strategy 2: Specialized model per task type**
```python
# Allocate different models for different agent types
config = {
    "code_agents": {  # 4 agents
        "model": "codellama",  # 13GB
        "ram": "13GB"
    },
    "chat_agents": {  # 4 agents
        "model": "llama3.2",   # 8GB
        "ram": "8GB"
    },
    "fast_agents": {  # 2 agents
        "model": "mistral",    # 4GB
        "ram": "4GB"
    }
}
# Total: 25GB RAM (fits in 32GB machine)
```

**Strategy 3: Request batching**
```python
# Batch multiple agent requests into one inference call
def batch_agent_requests(agent_prompts):
    combined_prompt = "\n\n".join([
        f"[Agent {i}]: {prompt}"
        for i, prompt in enumerate(agent_prompts)
    ])

    response = ollama.chat(
        model='llama3.2',
        messages=[{"role": "user", "content": combined_prompt}]
    )

    # Parse response for each agent
    return parse_multi_agent_response(response)

# Process 5 agents in one request instead of 5 separate requests
results = batch_agent_requests([
    "What is Python?",
    "What is JavaScript?",
    "What is Rust?",
    "What is Go?",
    "What is TypeScript?"
])
```

### When Hardware Becomes the "Rate Limit"

**Upgrade paths when local resources aren't enough:**

| Your Situation | Solution | Cost |
|----------------|----------|------|
| Need more concurrent agents | Upgrade RAM (16GB → 32GB) | ~$60-150 one-time |
| Slow inference speeds | Add GPU (RTX 3060) | ~$300-400 one-time |
| Multiple machines | Run Ollama on each | $0 (just install) |
| Cloud deployment | Deploy to vast.ai or Runpod | $0.20-0.50/hour |
| Enterprise scale | Self-host on server cluster | $2000-5000 hardware |

**Still cheaper than cloud APIs:**
- OpenAI GPT-4: $30-60/month ongoing
- Anthropic Claude: $15-30/month ongoing
- Local hardware: One-time cost, infinite usage

## Installation

### macOS
```bash
brew install ollama
ollama serve
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
Download from https://ollama.com/download/windows

### Docker
```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

## Usage Examples

### Chat Interface
```bash
ollama run llama3.2
>>> Write a Python function to sort a list
```

### API Server
```python
import requests

response = requests.post('http://localhost:11434/api/generate', json={
    'model': 'llama3.2',
    'prompt': 'Why is the sky blue?'
})

print(response.json()['response'])
```

### Streaming
```python
import ollama

for chunk in ollama.chat(
    model='llama3.2',
    messages=[{'role': 'user', 'content': 'Tell me a story'}],
    stream=True
):
    print(chunk['message']['content'], end='', flush=True)
```

## Performance Comparison

| Model | Speed (tokens/sec) | Quality | Memory |
|-------|-------------------|---------|--------|
| Llama 3.2 7B | 50-100 | Good | 8GB |
| Mistral 7B | 60-120 | Great | 8GB |
| CodeLlama 34B | 20-40 | Excellent | 32GB |
| Llama 3.2 70B | 10-20 | Best | 64GB |

*With GPU acceleration*

## Cost Savings

**Replacing OpenAI GPT-4:**
- Current cost: $0.03/1K input tokens, $0.06/1K output
- 1M tokens/month = $30-60/month
- **Ollama cost: $0** ✓

**Replacing Anthropic Claude:**
- Current cost: $0.015/1K input tokens, $0.075/1K output
- 1M tokens/month = $15-75/month
- **Ollama cost: $0** ✓

## Advanced Configuration

### Custom Models
```bash
# Create Modelfile
FROM llama3.2
PARAMETER temperature 0.7
SYSTEM You are a helpful coding assistant

# Build custom model
ollama create my-assistant -f Modelfile
```

### API Integration
```javascript
// Node.js
const ollama = require('ollama')

const response = await ollama.chat({
  model: 'llama3.2',
  messages: [{ role: 'user', content: 'Hello!' }],
})
```

### Multiple Models
```bash
# Pull multiple models
ollama pull llama3.2
ollama pull mistral
ollama pull codellama

# List installed
ollama list
```

## Troubleshooting

### Model Too Large
```bash
# Use smaller quantized version
ollama pull llama3.2:7b-q4  # 4-bit quantization (4GB)
```

### Slow Performance
```bash
# Check GPU usage
nvidia-smi  # NVIDIA
system_profiler SPDisplaysDataType  # macOS

# Use faster model
ollama pull mistral:7b
```

### Memory Issues
```bash
# Clear old models
ollama rm unused-model

# Use smaller context
ollama run llama3.2 --ctx-size 2048
```

## Resources

- **Official Docs**: https://ollama.com/docs
- **Model Library**: https://ollama.com/library
- **GitHub**: https://github.com/ollama/ollama
- **Discord**: https://discord.gg/ollama

## Related Plugins

- `local-llm-wrapper` - Generic wrapper for all local LLMs
- `ai-sdk-agents` - AI SDK with Ollama support
- `geepers-agents` - 51 agents powered by Ollama

## License

MIT License - Free to use commercially and personally
