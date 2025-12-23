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
