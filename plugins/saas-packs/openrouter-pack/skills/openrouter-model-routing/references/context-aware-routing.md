# Context-Aware Routing

## Context-Aware Routing

### Conversation History Router

```python
class ConversationRouter:
    """Route based on conversation state."""

    def __init__(self):
        self.turn_count = 0
        self.complexity_score = 0

    def route(self, messages: list) -> str:
        self.turn_count = len([m for m in messages if m["role"] == "user"])

        # Analyze conversation complexity
        total_length = sum(len(m["content"]) for m in messages)
        has_code = any("```" in m["content"] for m in messages)
        question_count = sum(
            m["content"].count("?")
            for m in messages if m["role"] == "user"
        )

        # Simple: short conversation, no code, few questions
        if total_length < 1000 and not has_code and question_count <= 2:
            return "anthropic/claude-3-haiku"

        # Complex: long conversation or code
        if total_length > 10000 or has_code:
            return "anthropic/claude-3.5-sonnet"

        # Medium: default
        return "openai/gpt-4-turbo"

conv_router = ConversationRouter()

def chat_multi_turn(messages: list, **kwargs):
    model = conv_router.route(messages)
    return client.chat.completions.create(
        model=model,
        messages=messages,
        **kwargs
    )
```
