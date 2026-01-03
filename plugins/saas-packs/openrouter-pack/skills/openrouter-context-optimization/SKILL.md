---
name: openrouter-context-optimization
description: |
  Optimize context window usage and token efficiency. Use when managing costs or hitting context limits. Trigger with phrases like 'openrouter context', 'openrouter tokens', 'reduce tokens', 'context window'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Context Optimization

## Overview

This skill covers techniques for efficient context management including truncation, summarization, and token optimization.

## Prerequisites

- OpenRouter integration
- Understanding of token-based pricing

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill covers techniques for efficient context management including truncation, summarization, and token optimization.

## Prerequisites

- OpenRouter integration
- Understanding of token-based pricing

## Token Estimation

### Basic Token Counter
```python
def estimate_tokens(text: str) -> int:
    """Rough token estimate (4 chars = 1 token for English)."""
    return len(text) // 4

def estimate_message_tokens(messages: list) -> int:
    """Estimate tokens for message array."""
    # Base overhead per message
    overhead_per_message = 4

    total = 0
    for message in messages:
        total += overhead_per_message
        total += estimate_tokens(message.get("content", ""))
        if message.get("name"):
            total += estimate_tokens(message["name"])

    return total + 3  # Reply priming tokens
```

### Tiktoken for Accuracy
```python
import tiktoken

def count_tokens_precise(text: str, model: str = "gpt-4") -> int:
    """Precise token count using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))

def count_message_tokens_precise(messages: list, model: str = "gpt-4") -> int:
    """Precise token count for messages."""
    encoding = tiktoken.get_encoding("cl100k_base")

    tokens_per_message = 3
    tokens_per_name = 1

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name

    num_tokens += 3  # Reply priming
    return num_tokens
```

## Context Truncation

### Smart Truncation
```python
class ContextManager:
    """Manage context window efficiently."""

    def __init__(self, max_tokens: int):
        self.max_tokens = max_tokens

    def truncate_messages(
        self,
        messages: list,
        reserve_for_response: int = 1000
    ) -> list:
        """Truncate messages to fit context window."""
        available = self.max_tokens - reserve_for_response

        # Always keep system message and last user message
        system_messages = [m for m in messages if m["role"] == "system"]
        other_messages = [m for m in messages if m["role"] != "system"]

        # Calculate system message tokens
        system_tokens = sum(
            estimate_tokens(m["content"])
            for m in system_messages
        )

        remaining = available - system_tokens

        # Truncate from oldest, keeping recent
        truncated = []
        current_tokens = 0

        for message in reversed(other_messages):
            msg_tokens = estimate_tokens(message["content"])
            if current_tokens + msg_tokens <= remaining:
                truncated.insert(0, message)
                current_tokens += msg_tokens
            else:
                break

        return system_messages + truncated

    def summarize_if_needed(
        self,
        messages: list,
        threshold: float = 0.8
    ) -> list:
        """Summarize old messages if context is getting full."""
        current_tokens = estimate_message_tokens(messages)

        if current_tokens < self.max_tokens * threshold:
            return messages

        # Need to summarize
        return self._summarize_history(messages)

    def _summarize_history(self, messages: list) -> list:
        """Summarize conversation history."""
        # Keep system and recent messages
        system = [m for m in messages if m["role"] == "system"]
        recent = messages[-4:]  # Keep last 2 exchanges

        # Summarize the rest
        to_summarize = [
            m for m in messages
            if m not in system and m not in recent
        ]

        if not to_summarize:
            return messages

        # Create summary
        summary_prompt = "Summarize this conversation history concisely:\n\n"
        for m in to_summarize:
            summary_prompt += f"{m['role']}: {m['content'][:500]}\n"

        summary_response = client.chat.completions.create(
            model="anthropic/claude-3-haiku",  # Cheap model for summary
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=500
        )

        summary = summary_response.choices[0].message.content

        return system + [
            {"role": "system", "content": f"Previous conversation summary: {summary}"}
        ] + recent

context_mgr = ContextManager(max_tokens=128000)
```

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

## Model-Specific Optimization

### Context Windows by Model
```python
CONTEXT_WINDOWS = {
    "anthropic/claude-3-opus": 200000,
    "anthropic/claude-3.5-sonnet": 200000,
    "anthropic/claude-3-haiku": 200000,
    "openai/gpt-4-turbo": 128000,
    "openai/gpt-4": 8192,
    "openai/gpt-4-32k": 32768,
    "openai/gpt-3.5-turbo": 16385,
    "meta-llama/llama-3.1-70b-instruct": 131000,
}

def select_model_for_context(context_tokens: int) -> str:
    """Select cheapest model that fits context."""
    # Sort by cost (approximate)
    model_costs = [
        ("anthropic/claude-3-haiku", 200000, 0.001),
        ("openai/gpt-3.5-turbo", 16385, 0.002),
        ("meta-llama/llama-3.1-70b-instruct", 131000, 0.001),
        ("anthropic/claude-3.5-sonnet", 200000, 0.018),
        ("openai/gpt-4-turbo", 128000, 0.030),
    ]

    for model, max_ctx, cost in model_costs:
        if context_tokens <= max_ctx * 0.9:  # Leave 10% headroom
            return model

    return "anthropic/claude-3.5-sonnet"  # Fallback to large context
```

## Response Length Control

### Optimal max_tokens
```python
def calculate_optimal_max_tokens(
    prompt_tokens: int,
    model: str,
    expected_response: str = "medium"
) -> int:
    """Calculate optimal max_tokens setting."""
    context_limit = CONTEXT_WINDOWS.get(model, 128000)
    available = context_limit - prompt_tokens

    response_sizes = {
        "short": 100,
        "medium": 500,
        "long": 2000,
        "very_long": 4000
    }

    desired = response_sizes.get(expected_response, 500)
    return min(desired, available - 100)

def chat_with_optimal_tokens(
    prompt: str,
    model: str,
    expected_length: str = "medium"
):
    prompt_tokens = estimate_tokens(prompt)
    max_tokens = calculate_optimal_max_tokens(
        prompt_tokens, model, expected_length
    )

    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
```

## Context Recycling

### Reuse Common Context
```python
class ContextCache:
    """Cache and reuse common context patterns."""

    def __init__(self):
        self.system_prompts = {}
        self.example_sets = {}

    def register_system_prompt(self, name: str, prompt: str):
        """Register a reusable system prompt."""
        self.system_prompts[name] = {
            "content": optimize_system_prompt(prompt),
            "tokens": estimate_tokens(prompt)
        }

    def register_examples(self, name: str, examples: list):
        """Register reusable example set."""
        messages = []
        for ex in examples:
            messages.append({"role": "user", "content": ex["input"]})
            messages.append({"role": "assistant", "content": ex["output"]})

        self.example_sets[name] = {
            "messages": messages,
            "tokens": sum(estimate_tokens(m["content"]) for m in messages)
        }

    def build_messages(
        self,
        prompt: str,
        system_name: str = None,
        examples_name: str = None
    ) -> tuple[list, int]:
        """Build messages using cached components."""
        messages = []
        total_tokens = 0

        if system_name and system_name in self.system_prompts:
            sp = self.system_prompts[system_name]
            messages.append({"role": "system", "content": sp["content"]})
            total_tokens += sp["tokens"]

        if examples_name and examples_name in self.example_sets:
            es = self.example_sets[examples_name]
            messages.extend(es["messages"])
            total_tokens += es["tokens"]

        messages.append({"role": "user", "content": prompt})
        total_tokens += estimate_tokens(prompt)

        return messages, total_tokens

context_cache = ContextCache()
context_cache.register_system_prompt(
    "code_review",
    "You are a code reviewer. Be concise and focus on important issues."
)
```

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
