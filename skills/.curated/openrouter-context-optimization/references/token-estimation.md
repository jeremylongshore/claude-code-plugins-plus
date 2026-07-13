# Token Estimation

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
