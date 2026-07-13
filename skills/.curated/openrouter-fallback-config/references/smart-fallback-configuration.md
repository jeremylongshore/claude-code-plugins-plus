# Smart Fallback Configuration

## Smart Fallback Configuration

### Fallback Manager Class

```python
import time
from dataclasses import dataclass
from typing import Optional, Dict, List

@dataclass
class ModelConfig:
    id: str
    priority: int = 0
    max_retries: int = 2
    timeout: float = 30.0
    disable_duration: float = 300.0  # 5 minutes

class FallbackManager:
    def __init__(self, models: List[ModelConfig]):
        self.models = sorted(models, key=lambda m: m.priority)
        self.disabled: Dict[str, float] = {}  # model_id -> disable_until

    def is_available(self, model_id: str) -> bool:
        if model_id not in self.disabled:
            return True
        return time.time() > self.disabled[model_id]

    def disable(self, model_id: str, duration: float = 300.0):
        self.disabled[model_id] = time.time() + duration

    def get_available_models(self) -> List[ModelConfig]:
        return [m for m in self.models if self.is_available(m.id)]

    def chat(self, prompt: str, **kwargs):
        available = self.get_available_models()

        if not available:
            # Reset disabled models if all are down
            self.disabled.clear()
            available = self.models

        for model_config in available:
            for attempt in range(model_config.max_retries):
                try:
                    return client.chat.completions.create(
                        model=model_config.id,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=model_config.timeout,
                        **kwargs
                    )
                except Exception as e:
                    if attempt == model_config.max_retries - 1:
                        self.disable(model_config.id, model_config.disable_duration)
                    continue

        raise Exception("All models exhausted")

# Usage
fallback = FallbackManager([
    ModelConfig("anthropic/claude-3.5-sonnet", priority=1),
    ModelConfig("openai/gpt-4-turbo", priority=2),
    ModelConfig("meta-llama/llama-3.1-70b-instruct", priority=3),
])
```
