---
name: together-core-workflow-a
description: |
  Together AI core workflow a for inference, fine-tuning, and model deployment.
  Use when working with Together AI's OpenAI-compatible API.
  Trigger: "together core workflow a".
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, inference, together]
compatible-with: claude-code
---

# Together AI Core Workflow A

## Overview

Fine-tune open-source models on your data with Together AI's fine-tuning API.

## Instructions

### Step 1: Prepare Training Data (JSONL)

```python
import json

# Format: one JSON object per line with messages array
training_data = [
    {"messages": [
        {"role": "system", "content": "You are a customer support agent."},
        {"role": "user", "content": "How do I reset my password?"},
        {"role": "assistant", "content": "Go to Settings > Security > Reset Password."},
    ]},
    {"messages": [
        {"role": "user", "content": "What are your business hours?"},
        {"role": "assistant", "content": "We're open Monday-Friday, 9 AM - 5 PM EST."},
    ]},
]

with open("training.jsonl", "w") as f:
    for item in training_data:
        f.write(json.dumps(item) + "\n")
```

### Step 2: Upload Training File

```python
from together import Together
client = Together()

# Upload file
file = client.files.upload(file="training.jsonl")
print(f"File ID: {file.id}")
```

### Step 3: Create Fine-Tuning Job

```python
job = client.fine_tuning.create(
    training_file=file.id,
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    n_epochs=3,
    learning_rate=1e-5,
    batch_size=4,
    suffix="my-support-bot",
)
print(f"Job ID: {job.id}, Status: {job.status}")
```

### Step 4: Monitor Training

```python
import time

while True:
    status = client.fine_tuning.retrieve(job.id)
    print(f"Status: {status.status}, Step: {status.training_steps_completed}")
    if status.status in ("completed", "failed", "cancelled"):
        break
    time.sleep(30)

if status.status == "completed":
    print(f"Fine-tuned model: {status.fine_tuned_model}")
```

### Step 5: Use Fine-Tuned Model

```python
response = client.chat.completions.create(
    model=status.fine_tuned_model,  # Your custom model ID
    messages=[{"role": "user", "content": "How do I cancel my subscription?"}],
)
print(response.choices[0].message.content)
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid JSONL | Wrong format | Each line must be valid JSON with messages array |
| Training OOM | Batch size too large | Reduce batch_size |
| Job failed | Data quality issue | Check training file format |

## Resources

- [Fine-Tuning Guide](https://docs.together.ai/docs/fine-tuning-quickstart)
- [Supported Models](https://docs.together.ai/docs/fine-tuning-models)
- [Fine-Tuning Python](https://docs.together.ai/docs/fine-tuning-python)

## Next Steps

For batch inference and dedicated endpoints, see `together-core-workflow-b`.
