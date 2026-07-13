# Try Different Models

## Try Different Models

### OpenAI Models

```python
# GPT-4 Turbo
response = client.chat.completions.create(
    model="openai/gpt-4-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)

# GPT-4o
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Anthropic Models

```python
# Claude 3.5 Sonnet
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Claude 3 Opus
response = client.chat.completions.create(
    model="anthropic/claude-3-opus",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Open Source Models

```python
# Llama 3.1 70B
response = client.chat.completions.create(
    model="meta-llama/llama-3.1-70b-instruct",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Mixtral
response = client.chat.completions.create(
    model="mistralai/mixtral-8x7b-instruct",
    messages=[{"role": "user", "content": "Hello!"}]
)
```
