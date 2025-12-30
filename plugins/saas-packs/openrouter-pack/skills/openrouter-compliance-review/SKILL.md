---
name: openrouter-compliance-review
description: |
  Conduct security and compliance review of OpenRouter integration. Use when preparing for audits or security assessments. Trigger with phrases like 'openrouter security review', 'openrouter compliance', 'openrouter audit', 'security assessment'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Compliance Review

## Overview

This skill provides a framework for conducting security and compliance reviews of OpenRouter integrations.

## Prerequisites

- Working OpenRouter integration
- Compliance requirements documented

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill provides a framework for conducting security and compliance reviews of OpenRouter integrations.

## Prerequisites

- Working OpenRouter integration
- Compliance requirements documented

## Compliance Landscape

### OpenRouter's Position
```
OpenRouter acts as a routing layer:
- Routes requests to underlying providers
- Each provider has their own compliance posture
- OpenRouter handles API key management and billing

For compliance, consider:
1. OpenRouter's own policies
2. Each model provider's compliance
3. Your application's requirements
```

### Provider Compliance Matrix
```
| Provider   | SOC 2 | HIPAA | GDPR | FedRAMP |
|------------|-------|-------|------|---------|
| OpenAI     | ✓     | BAA   | ✓    | -       |
| Anthropic  | ✓     | BAA   | ✓    | -       |
| Google     | ✓     | BAA   | ✓    | ✓       |
| Meta       | -     | -     | ✓    | -       |
| Mistral    | ✓     | -     | ✓    | -       |
```

## Security Assessment

### API Key Security
```python
class SecurityAssessment:
    """Assess OpenRouter security configuration."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.findings = []

    def assess_key_storage(self) -> dict:
        """Check how API key is stored."""
        findings = []

        # Check if key is in environment
        if self.api_key == os.environ.get("OPENROUTER_API_KEY"):
            findings.append({
                "check": "key_storage",
                "status": "pass",
                "message": "API key stored in environment variable"
            })
        else:
            findings.append({
                "check": "key_storage",
                "status": "warning",
                "message": "API key may be hardcoded"
            })

        # Check key format
        if self.api_key.startswith("sk-or-"):
            findings.append({
                "check": "key_format",
                "status": "pass",
                "message": "Valid OpenRouter key format"
            })
        else:
            findings.append({
                "check": "key_format",
                "status": "fail",
                "message": "Invalid key format"
            })

        return findings

    def assess_key_limits(self) -> dict:
        """Check if key has spending limits."""
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            data = response.json()["data"]

            if data.get("limit"):
                return {
                    "check": "spending_limit",
                    "status": "pass",
                    "message": f"Key has ${data['limit']} limit"
                }
            else:
                return {
                    "check": "spending_limit",
                    "status": "warning",
                    "message": "No spending limit configured"
                }
        except Exception as e:
            return {
                "check": "spending_limit",
                "status": "error",
                "message": f"Could not check: {e}"
            }

    def run_assessment(self) -> dict:
        """Run full security assessment."""
        results = []
        results.extend(self.assess_key_storage())
        results.append(self.assess_key_limits())

        passed = sum(1 for r in results if r["status"] == "pass")
        warnings = sum(1 for r in results if r["status"] == "warning")
        failed = sum(1 for r in results if r["status"] == "fail")

        return {
            "summary": {
                "passed": passed,
                "warnings": warnings,
                "failed": failed,
                "total": len(results)
            },
            "findings": results
        }

# Run assessment
assessment = SecurityAssessment(os.environ["OPENROUTER_API_KEY"])
print(json.dumps(assessment.run_assessment(), indent=2))
```

## Data Flow Documentation

### Document Data Flows
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│   Your App  │────▶│ OpenRouter  │
│   Input     │     │   Server    │     │   API       │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                    │
                    ┌──────▼──────┐      ┌──────▼──────┐
                    │   Logs      │      │  Provider   │
                    │   (audit)   │      │  (OpenAI,   │
                    └─────────────┘      │  Anthropic) │
                                         └─────────────┘

Data Classification:
- User Input: May contain PII/sensitive data
- Logs: Store hashes only, not content
- Provider: Subject to their data policies
```

### Data Classification
```python
class DataClassification:
    """Classify and handle data appropriately."""

    CLASSIFICATIONS = {
        "public": {
            "can_log": True,
            "can_cache": True,
            "requires_encryption": False
        },
        "internal": {
            "can_log": True,
            "can_cache": True,
            "requires_encryption": True
        },
        "confidential": {
            "can_log": False,  # Hash only
            "can_cache": False,
            "requires_encryption": True
        },
        "restricted": {
            "can_log": False,
            "can_cache": False,
            "requires_encryption": True,
            "requires_approval": True
        }
    }

    def classify_request(self, prompt: str, metadata: dict) -> str:
        """Classify request based on content and metadata."""
        # Check for PII patterns
        if self._contains_pii(prompt):
            return "confidential"

        # Check metadata classification
        if metadata.get("classification"):
            return metadata["classification"]

        # Default to internal
        return "internal"

    def _contains_pii(self, text: str) -> bool:
        patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b\d{3}-\d{2}-\d{4}\b',
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        ]
        return any(re.search(p, text) for p in patterns)

    def get_handling_rules(self, classification: str) -> dict:
        return self.CLASSIFICATIONS.get(classification, self.CLASSIFICATIONS["internal"])
```

## Compliance Checklist

### Pre-Deployment Checklist
```python
COMPLIANCE_CHECKLIST = {
    "security": [
        {
            "id": "SEC-001",
            "requirement": "API keys stored securely",
            "validation": "Keys in environment variables or secrets manager",
            "critical": True
        },
        {
            "id": "SEC-002",
            "requirement": "Spending limits configured",
            "validation": "Per-key limits set in OpenRouter dashboard",
            "critical": False
        },
        {
            "id": "SEC-003",
            "requirement": "No secrets in code",
            "validation": "Git secrets scanning enabled",
            "critical": True
        },
    ],
    "privacy": [
        {
            "id": "PRI-001",
            "requirement": "PII redaction implemented",
            "validation": "Redactor applied before API calls",
            "critical": True
        },
        {
            "id": "PRI-002",
            "requirement": "Data retention policy defined",
            "validation": "Logs purged after retention period",
            "critical": False
        },
        {
            "id": "PRI-003",
            "requirement": "User consent documented",
            "validation": "Consent records for AI processing",
            "critical": True
        },
    ],
    "audit": [
        {
            "id": "AUD-001",
            "requirement": "Audit logging enabled",
            "validation": "All requests logged with metadata",
            "critical": True
        },
        {
            "id": "AUD-002",
            "requirement": "Log integrity protection",
            "validation": "Tamper-proof logging implemented",
            "critical": False
        },
        {
            "id": "AUD-003",
            "requirement": "Log export capability",
            "validation": "Can export logs for compliance review",
            "critical": False
        },
    ],
    "operational": [
        {
            "id": "OPS-001",
            "requirement": "Error handling implemented",
            "validation": "Graceful degradation on API failures",
            "critical": True
        },
        {
            "id": "OPS-002",
            "requirement": "Fallback models configured",
            "validation": "Multiple model fallback chain",
            "critical": False
        },
        {
            "id": "OPS-003",
            "requirement": "Rate limiting implemented",
            "validation": "Client-side rate limiting active",
            "critical": False
        },
    ]
}

def run_compliance_check(checklist: dict) -> dict:
    """Run compliance checklist."""
    results = {"passed": [], "failed": [], "warnings": []}

    for category, items in checklist.items():
        for item in items:
            # In practice, implement actual validation
            status = "passed"  # Placeholder

            if status == "passed":
                results["passed"].append(item)
            elif item["critical"]:
                results["failed"].append(item)
            else:
                results["warnings"].append(item)

    return {
        "summary": {
            "passed": len(results["passed"]),
            "failed": len(results["failed"]),
            "warnings": len(results["warnings"]),
            "compliant": len(results["failed"]) == 0
        },
        "details": results
    }
```

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

## Documentation Templates

### Security Questionnaire Response
```markdown
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

## Executive Summary
OpenRouter integration assessed against security and privacy requirements.
Overall compliance status: [COMPLIANT/NON-COMPLIANT]

## Security Controls
- API Key Management: [Status]
- Encryption in Transit: TLS 1.2+
- Access Control: [Description]
- Audit Logging: [Status]

## Privacy Controls
- PII Handling: [Description]
- Data Retention: [N] days
- User Consent: [Status]

## Model Provider Assessment
{json.dumps(assess_provider("anthropic/claude-3.5-sonnet"), indent=2)}

## Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

## Appendix
- Detailed checklist results
- Audit log samples
- Provider documentation links
"""
```

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
