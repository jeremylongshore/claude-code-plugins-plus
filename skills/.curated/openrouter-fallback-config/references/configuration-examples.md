# Configuration Examples

## Configuration Examples

### YAML Configuration

```yaml
# fallback-config.yaml
fallback:
  default_chain:
    - anthropic/claude-3.5-sonnet
    - openai/gpt-4-turbo
    - meta-llama/llama-3.1-70b-instruct

  task_chains:
    coding:
      - anthropic/claude-3.5-sonnet
      - deepseek/deepseek-coder
    fast:
      - anthropic/claude-3-haiku
      - openai/gpt-3.5-turbo

  settings:
    max_retries_per_model: 2
    disable_duration_seconds: 300
    health_window_minutes: 10
    skip_threshold: 0.3
```

### Load Configuration

```python
import yaml

def load_fallback_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)

config = load_fallback_config("fallback-config.yaml")
default_chain = config["fallback"]["default_chain"]
```
