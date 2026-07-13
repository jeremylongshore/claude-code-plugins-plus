# Context Optimization Examples

## Python — Token Counting and Conversation Pruning

```python
import os
import tiktoken
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens for a given text using tiktoken."""
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")  # fallback
    return len(enc.encode(text))

def count_message_tokens(messages: list[dict]) -> int:
    """Count total tokens across all messages."""
    total = 0
    for msg in messages:
        total += 4  # message overhead tokens
        total += count_tokens(msg.get("content", ""))
    total += 2  # reply priming
    return total

def prune_conversation(messages: list[dict], max_tokens: int = 3000,
                       keep_system: bool = True) -> list[dict]:
    """Remove oldest messages to stay within token budget."""
    if not messages:
        return messages

    pruned = list(messages)
    system_msgs = [m for m in pruned if m["role"] == "system"] if keep_system else []
    non_system = [m for m in pruned if m["role"] != "system"]

    while count_message_tokens(system_msgs + non_system) > max_tokens and len(non_system) > 1:
        non_system.pop(0)  # remove oldest non-system message

    result = system_msgs + non_system
    if len(result) < len(messages):
        print(f"[Pruned] {len(messages)} -> {len(result)} messages "
              f"({count_message_tokens(result)} tokens)")
    return result

# Example: Multi-turn chat with pruning
conversation = [
    {"role": "system", "content": "You are a helpful coding assistant."},
]

prompts = [
    "What is a Python decorator?",
    "Show me an example of a decorator.",
    "How do I chain multiple decorators?",
    "What about class-based decorators?",
    "Explain functools.wraps.",
]

for prompt in prompts:
    conversation.append({"role": "user", "content": prompt})
    conversation = prune_conversation(conversation, max_tokens=2000)

    response = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=conversation,
        max_tokens=300,
    )

    reply = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": reply})
    print(f"Q: {prompt[:50]}...")
    print(f"Tokens: {response.usage.total_tokens}\n")
```

## TypeScript — Context Budget Calculator

```typescript
function estimateTokens(text: string): number {
  // Rough estimate: 1 token ≈ 4 characters for English text
  return Math.ceil(text.length / 4);
}

interface ContextBudget {
  modelLimit: number;
  systemTokens: number;
  maxResponseTokens: number;
  availableForHistory: number;
}

function calculateBudget(
  systemPrompt: string,
  maxResponseTokens: number,
  modelContextLimit: number
): ContextBudget {
  const systemTokens = estimateTokens(systemPrompt);
  const available = modelContextLimit - systemTokens - maxResponseTokens;

  return {
    modelLimit: modelContextLimit,
    systemTokens,
    maxResponseTokens,
    availableForHistory: Math.max(0, available),
  };
}

// Example: GPT-3.5 Turbo with 16K context
const budget = calculateBudget(
  "You are a helpful assistant specialized in TypeScript.",
  500,  // max response tokens
  16384 // model context limit
);

console.log(`Model limit: ${budget.modelLimit}`);
console.log(`System prompt: ${budget.systemTokens} tokens`);
console.log(`Reserved for response: ${budget.maxResponseTokens}`);
console.log(`Available for conversation: ${budget.availableForHistory}`);
// Available for conversation: ~15,870 tokens
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
