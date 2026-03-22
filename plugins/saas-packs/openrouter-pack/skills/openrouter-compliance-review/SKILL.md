---
name: openrouter-compliance-review
description: |
  Review OpenRouter integration for regulatory compliance (SOC2, GDPR, HIPAA). Use when preparing for audits, evaluating data handling, or documenting compliance posture. Triggers: 'openrouter compliance', 'openrouter gdpr', 'openrouter soc2', 'openrouter data residency'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, compliance, security, governance]

---
# OpenRouter Compliance Review

## Overview

OpenRouter is a proxy that routes requests to upstream providers (OpenAI, Anthropic, Google, etc.). Compliance depends on both OpenRouter's data handling and the selected provider's policies. Key considerations: data transit through OpenRouter infrastructure, provider-specific data retention, model selection for regulated data, and audit trail requirements.

## Compliance Checklist

```python
COMPLIANCE_CHECKLIST = {
    "data_handling": [
        "Verify OpenRouter does NOT train on your data (confirmed in their privacy policy)",
        "Confirm provider-level data policies (OpenAI, Anthropic, Google each differ)",
        "Document data flow: your app -> OpenRouter -> provider -> OpenRouter -> your app",
        "Identify if prompts contain PII, PHI, or regulated data",
        "Implement PII redaction before sending to API",
    ],
    "access_control": [
        "Use per-service API keys (not shared keys)",
        "Set credit limits per key to isolate blast radius",
        "Rotate keys on a 90-day schedule",
        "Store keys in secrets manager (not .env files in repos)",
        "Enable management keys for programmatic key provisioning",
    ],
    "audit_trail": [
        "Log every API call with generation_id, model, user_id, cost",
        "Hash prompts (SHA-256) instead of logging raw content",
        "Retain audit logs per regulation (90d operational, 7yr financial)",
        "Ship logs to append-only storage (S3, immutable DB)",
    ],
    "provider_selection": [
        "Route regulated data only to compliant providers",
        "Use provider routing to exclude non-compliant providers",
        "Document which models are approved for which data classifications",
        "Test that fallback routing doesn't route to unapproved providers",
    ],
}
```

## Provider Routing for Compliance

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

# Route ONLY to specific providers (e.g., Anthropic for SOC2)
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Analyze this contract..."}],
    max_tokens=2048,
    extra_body={
        "provider": {
            "order": ["Anthropic"],        # Only Anthropic's infrastructure
            "allow_fallbacks": False,       # Do NOT fall back to other providers
        },
    },
)

# Verify which provider actually served the request
print(f"Served by: {response.model}")  # Should match anthropic/claude-3.5-sonnet
```

## Data Classification Matrix

| Classification | Allowed Providers | Controls |
|---------------|-------------------|----------|
| Public | Any (including `:free`) | Standard logging |
| Internal | Tier 1 (OpenAI, Anthropic, Google) | Audit logging, key limits |
| Confidential | Anthropic, OpenAI (API-only) | PII redaction, no free models |
| Restricted/PHI | BYOK only or self-hosted | Full audit, encryption at rest |

## BYOK for Data Sovereignty

```python
# Bring Your Own Key -- requests go directly to provider
# OpenRouter acts as router only; data doesn't persist on OpenRouter
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Process this..."}],
    max_tokens=1024,
    extra_body={
        "provider": {
            "order": ["OpenAI"],
            "allow_fallbacks": False,
        },
    },
    # With BYOK, configure your provider key in OpenRouter dashboard
    # Data flows: your app -> OpenRouter (routing only) -> OpenAI (your account)
)
```

## Compliance Audit Script

```bash
#!/bin/bash
echo "=== OpenRouter Compliance Audit ==="

# 1. Verify API key has credit limit set
echo "1. Key configuration:"
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | \
  jq '{label: .data.label, limit: .data.limit, is_free_tier: .data.is_free_tier}'

# 2. Check if using free tier (not suitable for regulated data)
IS_FREE=$(curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq -r '.data.is_free_tier')
[ "$IS_FREE" = "true" ] && echo "WARNING: Free tier. Not suitable for regulated data."

# 3. Scan for hardcoded keys in source
FOUND=$(grep -r "sk-or-v1-" --include="*.py" --include="*.ts" --include="*.js" . 2>/dev/null | grep -v node_modules | wc -l)
echo "Hardcoded keys found: $FOUND"
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Request routed to unapproved provider | `allow_fallbacks: true` (default) | Set `allow_fallbacks: false` with explicit `order` |
| Key exposed in logs | Raw API key logged | Add PII redaction for `sk-or-v1-*` pattern |
| No audit trail for request | Logging middleware bypassed | Make audit logging a required wrapper |
| Free model used for regulated data | No model allowlist | Implement model allowlist in client wrapper |

## Enterprise Considerations

- OpenRouter does not train on API data, but upstream providers may have different terms for API vs consumer use
- Use `provider.order` + `allow_fallbacks: false` to guarantee data only flows to approved providers
- BYOK eliminates OpenRouter as a data processor for inference (routing metadata still transits)
- Document the data flow diagram for auditors: client -> OpenRouter (routing) -> provider (inference)
- Implement client-side PII redaction as defense-in-depth
- Consider self-hosted or VPC deployments for restricted/PHI data

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Privacy Policy](https://openrouter.ai/privacy) | [Provider Routing](https://openrouter.ai/docs/features/provider-routing)
