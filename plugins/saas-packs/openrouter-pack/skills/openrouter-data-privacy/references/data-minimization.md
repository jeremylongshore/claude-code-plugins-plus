# Data Minimization

## Data Minimization

### Prompt Cleaning

```python
def clean_prompt(prompt: str) -> str:
    """Remove unnecessary data from prompts."""
    # Remove base64 encoded data
    prompt = re.sub(r'data:[^;]+;base64,[A-Za-z0-9+/]+=*', '[DATA_REMOVED]', prompt)

    # Truncate very long strings that might be data
    lines = prompt.split('\n')
    cleaned_lines = []
    for line in lines:
        if len(line) > 1000:
            cleaned_lines.append(line[:1000] + '... [TRUNCATED]')
        else:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)
```

### Minimal Context

```python
def create_minimal_prompt(
    question: str,
    context: str,
    max_context_chars: int = 10000
) -> str:
    """Create prompt with minimal necessary context."""
    # Truncate context if needed
    if len(context) > max_context_chars:
        context = context[:max_context_chars] + "\n[Context truncated]"

    return f"""Answer the following question using only the provided context.
Do not use any information beyond what is given.

Context:
{context}

Question: {question}

Answer:"""
```
