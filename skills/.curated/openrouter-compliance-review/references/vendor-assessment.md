# Vendor Assessment

## Vendor Assessment

### Provider Security Review

```python
def assess_provider(model: str) -> dict:
    """Assess security posture of model provider."""
    provider = model.split("/")[0]

    assessments = {
        "openai": {
            "provider": "OpenAI",
            "soc2": True,
            "hipaa_baa": True,
            "gdpr": True,
            "data_retention": "30 days (abuse monitoring)",
            "training_opt_out": "API data not used for training",
            "encryption": "TLS 1.2+, AES-256 at rest"
        },
        "anthropic": {
            "provider": "Anthropic",
            "soc2": True,
            "hipaa_baa": True,
            "gdpr": True,
            "data_retention": "Short-term safety only",
            "training_opt_out": "API data not used for training",
            "encryption": "TLS 1.2+, AES-256 at rest"
        },
        "meta-llama": {
            "provider": "Meta (via inference provider)",
            "soc2": "Varies by provider",
            "hipaa_baa": False,
            "gdpr": True,
            "data_retention": "Varies by provider",
            "training_opt_out": "Model is open source",
            "encryption": "Varies by provider"
        }
    }

    return assessments.get(provider, {
        "provider": provider,
        "note": "Review provider documentation for compliance details"
    })
```
