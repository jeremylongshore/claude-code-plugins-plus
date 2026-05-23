# Efficient Message Patterns

## Efficient Message Patterns

### Minimal Messages

```python
def create_minimal_request(
    prompt: str,
    system: str = None,
    examples: list = None
) -> list:
    """Create minimal message structure."""
    messages = []

    # Concise system prompt
    if system:
        messages.append({
            "role": "system",
            "content": optimize_system_prompt(system)
        })

    # Include only necessary examples
    if examples:
        # Limit to 2 examples max
        for ex in examples[:2]:
            messages.append({"role": "user", "content": ex["input"]})
            messages.append({"role": "assistant", "content": ex["output"]})

    messages.append({"role": "user", "content": prompt})
    return messages
```

### Batch Similar Requests

```python
def batch_prompts(prompts: list, max_batch_tokens: int = 4000) -> list:
    """Batch multiple prompts into single requests."""
    batches = []
    current_batch = []
    current_tokens = 0

    for i, prompt in enumerate(prompts):
        prompt_tokens = estimate_tokens(prompt)

        if current_tokens + prompt_tokens > max_batch_tokens and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0

        current_batch.append({"index": i, "prompt": prompt})
        current_tokens += prompt_tokens

    if current_batch:
        batches.append(current_batch)

    return batches

def execute_batch(batch: list, model: str) -> list:
    """Execute a batch of prompts."""
    combined_prompt = "Answer each numbered question:\n\n"
    for item in batch:
        combined_prompt += f"{item['index'] + 1}. {item['prompt']}\n\n"

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": combined_prompt}]
    )

    # Parse responses (simplified)
    return response.choices[0].message.content
```
