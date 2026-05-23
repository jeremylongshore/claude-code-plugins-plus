# Cascading Router

## Cascading Router

### Try Cheap, Fall Back to Premium

```python
class CascadeRouter:
    """Try cheaper model first, escalate if needed."""

    def __init__(self):
        self.cascade = [
            ("anthropic/claude-3-haiku", self._is_sufficient_simple),
            ("anthropic/claude-3.5-sonnet", self._is_sufficient_complex),
            ("anthropic/claude-3-opus", lambda r: True),  # Final fallback
        ]

    def _is_sufficient_simple(self, response: str) -> bool:
        """Check if simple model response is sufficient."""
        # Too short might mean model struggled
        if len(response) < 50:
            return False
        # Check for uncertainty markers
        uncertainty = ["i'm not sure", "i cannot", "unclear", "don't know"]
        if any(u in response.lower() for u in uncertainty):
            return False
        return True

    def _is_sufficient_complex(self, response: str) -> bool:
        """Check if complex model response is sufficient."""
        if len(response) < 20:
            return False
        return True

    def chat(self, prompt: str, **kwargs):
        """Try models in cascade until sufficient response."""
        for model, is_sufficient in self.cascade:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs
                )
                content = response.choices[0].message.content

                if is_sufficient(content):
                    return response, model

            except Exception:
                continue

        raise Exception("All cascade models failed")

cascade = CascadeRouter()
response, used_model = cascade.chat("What is 2+2?")
```
