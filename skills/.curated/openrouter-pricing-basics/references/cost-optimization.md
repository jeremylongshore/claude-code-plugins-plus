# Cost Optimization

## Cost Optimization

### Model Selection Strategy

```
Task Type → Recommended Model → Cost

Simple Q&A:
  claude-3-haiku      $0.001/request

Code completion:
  llama-3.1-70b       $0.001/request

Complex analysis:
  gpt-4-turbo         $0.03/request

Final review:
  claude-3-opus       $0.10/request
```

### Token Optimization

```python
# Reduce prompt tokens
- Remove unnecessary context
- Use concise system prompts
- Summarize long conversations

# Reduce completion tokens
- Set appropriate max_tokens
- Use stop sequences
- Request concise responses
```

### Caching Strategy

```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_completion(prompt_hash: str, model: str):
    # Cache repeated identical requests
    return client.chat.completions.create(...)

def chat_with_cache(prompt: str, model: str):
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    return cached_completion(prompt_hash, model)
```
