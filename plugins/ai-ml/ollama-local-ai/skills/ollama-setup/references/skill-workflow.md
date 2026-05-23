# Skill Workflow

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
