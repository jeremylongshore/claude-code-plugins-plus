---
name: klingai-compliance-review
description: |
  Security and compliance review framework for Kling AI integrations. Use when preparing for
  audits or reviewing security posture. Trigger with phrases like 'klingai compliance',
  'kling ai security review', 'klingai audit prep', 'video generation compliance'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, compliance, security]

---
# Kling AI Compliance Review

## Overview

Security and compliance assessment framework for Kling AI integrations. Covers data handling, credential management, content policy, privacy, and regulatory considerations.

## Data Flow Assessment

```
User Prompt → [Your App] → [Kling AI API] → [Kling GPU Cluster]
                                                     ↓
[Your CDN] ← download ← [Kling CDN (temporary URL)] ← Generated Video
```

### Data Residency

| Data | Location | Retention |
|------|----------|-----------|
| Prompts | Sent to Kling servers (China/global) | Processing only |
| Generated videos | Kling CDN (temporary URLs) | ~24-72 hours |
| API keys | Your infrastructure | You control |
| Audit logs | Your infrastructure | You control |

## Security Checklist

### Credential Security
- [ ] AK/SK stored in secrets manager (not env files, not code)
- [ ] Keys rotated quarterly
- [ ] Separate keys per environment
- [ ] JWT tokens never logged
- [ ] Access key prefix logged (first 8 chars only)

```python
# Safe logging pattern
def safe_log_key(access_key: str) -> str:
    return access_key[:8] + "..." + access_key[-4:]
```

### Network Security
- [ ] All API calls over HTTPS (enforced by base URL)
- [ ] Webhook endpoints use HTTPS with valid TLS cert
- [ ] Network egress rules allow `api.klingai.com:443`
- [ ] No API keys in query strings (Bearer token in header only)

### Input Validation
- [ ] Prompt length validated (<= 2500 chars)
- [ ] Image URLs validated before sending
- [ ] User input sanitized against injection
- [ ] Content policy pre-filtering active

### Output Handling
- [ ] Kling CDN URLs treated as temporary
- [ ] Videos downloaded and stored on your infrastructure
- [ ] Generated content scanned before serving to end users
- [ ] Video metadata stripped of sensitive info before public delivery

## Privacy Assessment

| Question | Consideration |
|----------|--------------|
| Do prompts contain PII? | Filter PII before sending to API |
| Do images contain faces? | Check consent requirements (GDPR Art. 6) |
| Are generated videos stored? | Define retention policy |
| Who has access to generated content? | RBAC on storage layer |
| Cross-border data transfer? | Kling API servers may be in China |

## GDPR Considerations

```python
class GDPRCompliantClient:
    """Kling client with GDPR data handling."""

    def __init__(self, base_client, audit_logger):
        self.client = base_client
        self.audit = audit_logger

    def text_to_video(self, prompt: str, data_subject_id: str = None, **kwargs):
        # Log processing activity (GDPR Art. 30)
        self.audit.log("processing_activity", "system", {
            "purpose": "video_generation",
            "data_subject": data_subject_id,
            "legal_basis": "legitimate_interest",
            "data_categories": ["text_prompt"],
            "recipients": ["klingai_api"],
        })

        return self.client.text_to_video(prompt, **kwargs)

    def handle_deletion_request(self, data_subject_id: str):
        """Handle GDPR right to erasure (Art. 17)."""
        # Delete stored videos associated with the data subject
        # Delete audit logs referencing the data subject
        # Note: cannot delete data already sent to Kling API
        self.audit.log("deletion_request", "system", {
            "data_subject": data_subject_id,
            "action": "processed",
        })
```

## Automated Compliance Check

```python
def run_compliance_check(config: dict) -> dict:
    """Run automated compliance checks against configuration."""
    checks = []

    # Check credential storage
    if config.get("key_source") == "environment":
        checks.append(("WARN", "credentials", "Using env vars; prefer secrets manager"))
    elif config.get("key_source") == "secrets_manager":
        checks.append(("PASS", "credentials", "Using secrets manager"))

    # Check TLS
    if config.get("base_url", "").startswith("https://"):
        checks.append(("PASS", "tls", "HTTPS enforced"))
    else:
        checks.append(("FAIL", "tls", "Not using HTTPS"))

    # Check content filtering
    if config.get("content_filter_enabled"):
        checks.append(("PASS", "content_filter", "Pre-submission filtering active"))
    else:
        checks.append(("WARN", "content_filter", "No pre-submission content filtering"))

    # Check audit logging
    if config.get("audit_logging"):
        checks.append(("PASS", "audit", "Audit logging enabled"))
    else:
        checks.append(("FAIL", "audit", "No audit logging"))

    # Print report
    for status, area, message in checks:
        icon = {"PASS": "OK", "WARN": "!!", "FAIL": "XX"}[status]
        print(f"  [{icon}] {area}: {message}")

    return {
        "passed": sum(1 for s, _, _ in checks if s == "PASS"),
        "warnings": sum(1 for s, _, _ in checks if s == "WARN"),
        "failed": sum(1 for s, _, _ in checks if s == "FAIL"),
    }
```

## Resources

- [Kling AI Terms of Service](https://app.klingai.com/global/dev/document-api/protocols/paidServiceProtocol)
- [Developer Portal](https://app.klingai.com/global/dev)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
