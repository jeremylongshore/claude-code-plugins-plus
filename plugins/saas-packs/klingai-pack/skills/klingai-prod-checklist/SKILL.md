---
name: klingai-prod-checklist
description: |
  Pre-launch production readiness checklist for Kling AI. Use when preparing to deploy video
  generation to production. Trigger with phrases like 'klingai production', 'kling ai go-live',
  'klingai launch checklist', 'deploy klingai'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Production Checklist

## Overview

This skill provides a comprehensive checklist covering security, monitoring, error handling, and operational readiness for production Kling AI deployments.

## Prerequisites

- Working Kling AI integration
- Production infrastructure ready
- Monitoring systems configured

## Instructions

Follow these steps to prepare for production:

1. **Security Review**: Audit credentials and access
2. **Error Handling**: Verify all error paths
3. **Monitoring Setup**: Configure observability
4. **Performance Testing**: Validate under load
5. **Documentation**: Complete runbooks

## Production Checklist

### Security

```
[ ] API Key Management
    [ ] API keys stored in secrets manager (not env vars in prod)
    [ ] Separate keys for dev/staging/prod
    [ ] Key rotation process documented
    [ ] Keys have appropriate credit limits
    [ ] No keys in source code or logs

[ ] Access Control
    [ ] Least privilege access to production keys
    [ ] Audit log of key access
    [ ] Key revocation process tested
    [ ] MFA enabled on Kling AI account

[ ] Data Protection
    [ ] PII handling policy defined
    [ ] Prompts don't contain sensitive data
    [ ] Video output access controlled
    [ ] Data retention policy implemented
```

### Error Handling

```
[ ] HTTP Errors
    [ ] 401 - Authentication errors handled
    [ ] 400 - Validation errors with user feedback
    [ ] 429 - Rate limiting with backoff
    [ ] 500 - Server errors with retry
    [ ] Timeout - Generation timeout handling

[ ] Business Errors
    [ ] Content policy violations handled gracefully
    [ ] Insufficient credits notification
    [ ] Generation failure recovery
    [ ] Partial failure handling for batches

[ ] Error Reporting
    [ ] Errors logged with context
    [ ] Alert thresholds configured
    [ ] Error rate dashboards
    [ ] On-call escalation path
```

### Monitoring

```
[ ] Metrics
    [ ] Request rate (RPM)
    [ ] Error rate by type
    [ ] Latency percentiles (p50, p95, p99)
    [ ] Credit consumption rate
    [ ] Active job count
    [ ] Queue depth (if applicable)

[ ] Alerts
    [ ] High error rate (>5%)
    [ ] Low credit balance (<20%)
    [ ] High latency (>2x baseline)
    [ ] Job failure spike
    [ ] Rate limit breaches

[ ] Dashboards
    [ ] Real-time operations view
    [ ] Cost tracking
    [ ] Job status overview
    [ ] Historical trends
```

### Performance

```
[ ] Load Testing
    [ ] Tested at expected peak load
    [ ] Tested at 2x peak (headroom)
    [ ] Response times acceptable
    [ ] No memory leaks under load

[ ] Scalability
    [ ] Horizontal scaling tested
    [ ] Database connections pooled
    [ ] Caching strategy implemented
    [ ] CDN for video delivery

[ ] Reliability
    [ ] Fallback models configured
    [ ] Circuit breaker implemented
    [ ] Graceful degradation tested
    [ ] Recovery procedures validated
```

### Operations

```
[ ] Documentation
    [ ] API integration documented
    [ ] Runbook for common issues
    [ ] Incident response plan
    [ ] Rollback procedure

[ ] Deployment
    [ ] Blue-green or canary deployment
    [ ] Feature flags for new functionality
    [ ] Quick rollback capability
    [ ] Configuration management

[ ] Support
    [ ] Support contact documented
    [ ] Escalation path defined
    [ ] SLA expectations set
    [ ] Status page monitoring
```

## Automated Checklist Validator

```python
import os
import requests
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    severity: str  # critical, warning, info

def run_production_checks() -> List[CheckResult]:
    """Run automated production readiness checks."""
    results = []

    # Check 1: API Key configured
    api_key = os.environ.get("KLINGAI_API_KEY")
    results.append(CheckResult(
        name="API Key Configuration",
        passed=bool(api_key),
        message="API key is set" if api_key else "KLINGAI_API_KEY not set",
        severity="critical"
    ))

    # Check 2: API connectivity
    if api_key:
        try:
            response = requests.get(
                "https://api.klingai.com/v1/account",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            results.append(CheckResult(
                name="API Connectivity",
                passed=response.status_code == 200,
                message=f"API responded with {response.status_code}",
                severity="critical"
            ))

            # Check 3: Credit balance
            if response.status_code == 200:
                data = response.json()
                credits = data.get("credits", 0)
                results.append(CheckResult(
                    name="Credit Balance",
                    passed=credits > 100,
                    message=f"Credits: {credits}",
                    severity="warning" if credits > 0 else "critical"
                ))
        except Exception as e:
            results.append(CheckResult(
                name="API Connectivity",
                passed=False,
                message=f"Connection failed: {e}",
                severity="critical"
            ))

    # Check 4: Environment variables
    required_vars = ["KLINGAI_API_KEY"]
    optional_vars = ["KLINGAI_WEBHOOK_URL", "KLINGAI_TIMEOUT"]

    for var in required_vars:
        results.append(CheckResult(
            name=f"Env: {var}",
            passed=bool(os.environ.get(var)),
            message="Set" if os.environ.get(var) else "Missing",
            severity="critical"
        ))

    for var in optional_vars:
        results.append(CheckResult(
            name=f"Env: {var}",
            passed=bool(os.environ.get(var)),
            message="Set" if os.environ.get(var) else "Not set (optional)",
            severity="info"
        ))

    return results

def print_checklist_report(results: List[CheckResult]):
    """Print formatted checklist report."""
    print("\n" + "="*60)
    print("KLING AI PRODUCTION READINESS REPORT")
    print("="*60 + "\n")

    critical_pass = sum(1 for r in results if r.severity == "critical" and r.passed)
    critical_total = sum(1 for r in results if r.severity == "critical")

    for result in results:
        icon = "✅" if result.passed else "❌"
        severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[result.severity]
        print(f"{icon} {severity_icon} {result.name}: {result.message}")

    print("\n" + "-"*60)
    print(f"Critical Checks: {critical_pass}/{critical_total} passed")

    if critical_pass < critical_total:
        print("\n⚠️  NOT READY FOR PRODUCTION")
        print("Address all critical issues before deployment.")
    else:
        print("\n✅ READY FOR PRODUCTION")
        print("All critical checks passed.")

# Run checks
if __name__ == "__main__":
    results = run_production_checks()
    print_checklist_report(results)
```

## Pre-Deployment Script

```bash
#!/bin/bash
# pre-deploy-check.sh

echo "Running Kling AI pre-deployment checks..."

# Check API key
if [ -z "$KLINGAI_API_KEY" ]; then
    echo "❌ KLINGAI_API_KEY not set"
    exit 1
fi

# Test API connectivity
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $KLINGAI_API_KEY" \
    https://api.klingai.com/v1/account)

if [ "$STATUS" != "200" ]; then
    echo "❌ API connectivity failed (HTTP $STATUS)"
    exit 1
fi

echo "✅ All pre-deployment checks passed"
exit 0
```

## Output

Successful execution produces:
- Comprehensive readiness report
- Pass/fail status for each check
- Clear action items for failures
- Production approval status

## Error Handling

Common errors and solutions:
1. **API Key Invalid**: Regenerate and update secrets
2. **Low Credits**: Purchase credits before launch
3. **Network Issues**: Verify firewall and DNS

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Best Practices](https://docs.klingai.com/best-practices)
- [Production Deployment Guide](https://docs.klingai.com/deployment)
- [SRE Checklist](https://sre.google/sre-book/service-best-practices/)
