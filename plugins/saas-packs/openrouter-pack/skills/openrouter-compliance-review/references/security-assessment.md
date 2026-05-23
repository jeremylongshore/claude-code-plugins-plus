# Security Assessment

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
