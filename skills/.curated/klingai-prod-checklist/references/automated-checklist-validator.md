# Automated Checklist Validator

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
