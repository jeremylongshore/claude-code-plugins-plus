# Prompt Optimization

## Prompt Optimization

### Compress Prompts

```python
def compress_prompt(prompt: str, max_tokens: int) -> str:
    """Compress prompt to fit within token limit."""
    current_tokens = estimate_tokens(prompt)

    if current_tokens <= max_tokens:
        return prompt

    # Strategy 1: Remove redundant whitespace
    compressed = " ".join(prompt.split())

    if estimate_tokens(compressed) <= max_tokens:
        return compressed

    # Strategy 2: Truncate with ellipsis
    target_chars = max_tokens * 4 - 20
    compressed = prompt[:target_chars] + "... [truncated]"

    return compressed

def optimize_system_prompt(prompt: str) -> str:
    """Optimize system prompt for token efficiency."""
    # Remove unnecessary formatting
    lines = prompt.strip().split('\n')
    optimized_lines = []

    for line in lines:
        # Skip empty lines and excessive formatting
        stripped = line.strip()
        if stripped and not stripped.startswith('#' * 3):
            optimized_lines.append(stripped)

    return '\n'.join(optimized_lines)
```

### Context Compression

```python
def compress_context(
    context: str,
    max_tokens: int,
    preserve_ratio: float = 0.5
) -> str:
    """Compress context while preserving key information."""
    current_tokens = estimate_tokens(context)

    if current_tokens <= max_tokens:
        return context

    # Split into chunks
    paragraphs = context.split('\n\n')

    if len(paragraphs) == 1:
        # Single block - truncate from middle
        char_limit = max_tokens * 4
        half = char_limit // 2
        return context[:half] + "\n[...content omitted...]\n" + context[-half:]

    # Multiple paragraphs - keep first and last, summarize middle
    preserve_count = max(2, int(len(paragraphs) * preserve_ratio))
    keep_start = preserve_count // 2
    keep_end = preserve_count - keep_start

    kept = paragraphs[:keep_start] + ["[...additional context omitted...]"] + paragraphs[-keep_end:]
    return '\n\n'.join(kept)
```
