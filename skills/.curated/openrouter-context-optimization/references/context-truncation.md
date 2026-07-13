# Context Truncation

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
