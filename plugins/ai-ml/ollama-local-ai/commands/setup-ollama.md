---
name: setup-ollama
description: Install and configure Ollama for local AI models
model: sonnet
---

# Setup Ollama - Local AI Installation

I'll help you install and configure Ollama for free, local AI model deployment.

## Step 1: Detect Operating System

Let me check your system:

```bash
uname -s
```

## Step 2: Install Ollama

### For macOS:
```bash
# Using Homebrew (recommended)
brew install ollama

# Start Ollama service
brew services start ollama
```

### For Linux:
```bash
# Official installation script
curl -fsSL https://ollama.com/install.sh | sh

# Start service
sudo systemctl start ollama
sudo systemctl enable ollama
```

### For Windows:
Download installer from: https://ollama.com/download/windows

## Step 3: Verify Installation

```bash
ollama --version
```

## Step 4: Pull Recommended Models

```bash
# General purpose (4GB)
ollama pull llama3.2

# Code generation (20GB)
ollama pull codellama

# Fast and efficient (4GB)
ollama pull mistral
```

## Step 5: Test Model

```bash
# Interactive chat
ollama run llama3.2

# Or quick test
echo "Write a hello world in Python" | ollama run llama3.2
```

## Step 6: Configure API Access

Ollama runs on `http://localhost:11434` by default.

Test the API:
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Why is the sky blue?"
}'
```

## Optional: GPU Acceleration

### NVIDIA GPU:
```bash
# Check GPU availability
nvidia-smi

# Ollama automatically uses CUDA if available
```

### Apple Silicon:
```bash
# Metal acceleration is automatic on M1/M2/M3
```

## Next Steps

1. ✅ Ollama installed and running
2. ✅ Models downloaded
3. ✅ API tested

You can now use Ollama in your projects:
- Python: `pip install ollama`
- Node.js: `npm install ollama`
- Direct API calls to `http://localhost:11434`

**Cost savings:** You just eliminated $30-200/month in API fees! 🎉

Need help integrating Ollama into your project? Ask me!
