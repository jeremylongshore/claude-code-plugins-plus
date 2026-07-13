# Openrouter Integration Security Questionnaire

## OpenRouter Integration Security Questionnaire

### Data Handling

Q: How is data transmitted to OpenRouter?
A: All data transmitted via TLS 1.2+ encrypted HTTPS connections.

Q: Is data encrypted at rest?
A: OpenRouter routes to providers who implement encryption at rest.
   Specific implementation varies by provider (OpenAI, Anthropic, etc.)

Q: Is data used for model training?
A: Major providers (OpenAI, Anthropic) do not use API data for training.
   Review each provider's current policy for confirmation.

### Access Control

Q: How are API keys secured?
A: Keys stored in [secrets manager/environment variables].
   Per-key spending limits configured.
   Keys rotated [frequency].

Q: Who has access to the integration?
A: Access controlled via [mechanism].
   [N] users with access, documented in [location].

### Audit & Compliance

Q: Is request/response logging implemented?
A: Yes, audit logging captures metadata and content hashes.
   Full content not logged for privacy.

Q: What is the data retention period?
A: Logs retained for [N] days per retention policy.
   Automatic archival after [N] days.

```

### Compliance Report Template
```python
def generate_compliance_report() -> str:
    """Generate compliance report for stakeholders."""
    return f"""
# OpenRouter Compliance Report
Generated: {datetime.utcnow().isoformat()}
