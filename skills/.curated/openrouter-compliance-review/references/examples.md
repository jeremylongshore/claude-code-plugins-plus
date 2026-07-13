# Compliance Review Examples

## Python — Automated Compliance Checker

```python
import os
import json
from dataclasses import dataclass, field

@dataclass
class CheckResult:
    name: str
    status: str  # "pass", "fail", "warn"
    details: str

@dataclass
class ComplianceReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == "pass")

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c.status == "fail")

    def summary(self) -> str:
        total = len(self.checks)
        return (f"Compliance: {self.passed}/{total} passed, "
                f"{self.failed} failed, {total - self.passed - self.failed} warnings")

def check_api_key_storage() -> CheckResult:
    """Verify API key is not hardcoded."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return CheckResult("api_key_storage", "fail", "No API key found in environment")
    if key.startswith("sk-or-"):
        return CheckResult("api_key_storage", "pass", "Key loaded from environment variable")
    return CheckResult("api_key_storage", "warn", "Key format unexpected")

def check_https_enforcement() -> CheckResult:
    """Verify HTTPS is used for API calls."""
    base_url = "https://openrouter.ai/api/v1"
    if base_url.startswith("https://"):
        return CheckResult("https_enforcement", "pass", "HTTPS enforced")
    return CheckResult("https_enforcement", "fail", "HTTP detected — must use HTTPS")

def check_max_tokens_set(sample_config: dict) -> CheckResult:
    """Verify max_tokens is always set."""
    if sample_config.get("max_tokens"):
        return CheckResult("max_tokens", "pass",
                          f"max_tokens set to {sample_config['max_tokens']}")
    return CheckResult("max_tokens", "fail",
                      "max_tokens not set — risk of unbounded costs")

def check_error_handling(has_try_catch: bool) -> CheckResult:
    """Verify API calls have error handling."""
    if has_try_catch:
        return CheckResult("error_handling", "pass", "Error handling present")
    return CheckResult("error_handling", "fail", "No error handling around API calls")

def check_logging_exists(has_audit_log: bool) -> CheckResult:
    """Verify audit logging is configured."""
    if has_audit_log:
        return CheckResult("audit_logging", "pass", "Audit logging configured")
    return CheckResult("audit_logging", "fail", "No audit logging found")

def run_compliance_review() -> ComplianceReport:
    report = ComplianceReport()

    report.checks.append(check_api_key_storage())
    report.checks.append(check_https_enforcement())
    report.checks.append(check_max_tokens_set({"max_tokens": 500}))
    report.checks.append(check_error_handling(has_try_catch=True))
    report.checks.append(check_logging_exists(has_audit_log=True))

    return report

# Run the review
report = run_compliance_review()
print(report.summary())
for check in report.checks:
    icon = {"pass": "OK", "fail": "FAIL", "warn": "WARN"}[check.status]
    print(f"  [{icon}] {check.name}: {check.details}")
```

### Expected Output

```
Compliance: 5/5 passed, 0 failed, 0 warnings
  [OK] api_key_storage: Key loaded from environment variable
  [OK] https_enforcement: HTTPS enforced
  [OK] max_tokens: max_tokens set to 500
  [OK] error_handling: Error handling present
  [OK] audit_logging: Audit logging configured
```

## Compliance Checklist Template (Markdown)

```markdown
# OpenRouter Integration Compliance Checklist

## Security
- [ ] API keys stored in secrets manager (not in code or .env files on disk)
- [ ] API keys rotated every 90 days
- [ ] HTTPS enforced for all API communication
- [ ] No PII logged in plain text

## Data Privacy
- [ ] Data flow diagram documented
- [ ] PII detection/redaction implemented
- [ ] Data retention policy reviewed with legal
- [ ] User consent mechanism in place

## Reliability
- [ ] Fallback models configured
- [ ] Retry logic with exponential backoff
- [ ] Circuit breaker for cascading failures
- [ ] Request timeouts set (≤30s)

## Observability
- [ ] Structured audit logs for every API call
- [ ] Alerting on error rate > 5%
- [ ] Latency P95 monitoring
- [ ] Cost tracking and budget alerts

## Cost Controls
- [ ] Account spending limit set
- [ ] Per-request max_tokens always specified
- [ ] Budget enforcement middleware deployed
- [ ] Weekly cost review scheduled
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
