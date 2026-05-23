# Model Selection Criteria

## Model Selection Criteria

### By Task Type

```
Code generation:
  1. anthropic/claude-3.5-sonnet
  2. openai/gpt-4-turbo
  3. deepseek/deepseek-coder

Creative writing:
  1. anthropic/claude-3-opus
  2. openai/gpt-4
  3. meta-llama/llama-3.1-70b-instruct

Analysis/Reasoning:
  1. anthropic/claude-3-opus
  2. openai/gpt-4-turbo
  3. anthropic/claude-3.5-sonnet

Quick tasks:
  1. anthropic/claude-3-haiku
  2. openai/gpt-3.5-turbo
  3. mistralai/mistral-7b-instruct
```

### By Context Length

```
< 4K tokens:   Any model
4K - 16K:      gpt-3.5-turbo-16k, most models
16K - 32K:     gpt-4-32k, claude-3 models
32K - 128K:    gpt-4-turbo, gemini-pro-1.5
128K - 200K:   claude-3-opus, claude-3.5-sonnet
```

### By Cost (per 1M tokens)

```
Budget (< $1):
  - meta-llama/llama-3.1-8b-instruct
  - mistralai/mistral-7b-instruct

Mid-range ($1-5):
  - anthropic/claude-3-haiku
  - openai/gpt-3.5-turbo
  - meta-llama/llama-3.1-70b-instruct

Premium ($5-30):
  - anthropic/claude-3.5-sonnet
  - openai/gpt-4-turbo
  - anthropic/claude-3-sonnet

Enterprise ($30+):
  - anthropic/claude-3-opus
  - openai/gpt-4
  - meta-llama/llama-3.1-405b-instruct
```
