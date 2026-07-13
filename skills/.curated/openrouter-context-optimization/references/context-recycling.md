# Context Recycling

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
