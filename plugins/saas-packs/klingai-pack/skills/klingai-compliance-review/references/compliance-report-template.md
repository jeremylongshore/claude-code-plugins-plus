# Compliance Report Template

## Compliance Report Template

```python
def generate_compliance_document(report: ComplianceReport) -> str:
    """Generate formatted compliance document."""

    doc = f"""
================================================================================
                    KLING AI COMPLIANCE ASSESSMENT REPORT
================================================================================

Report ID: {report.report_id}
Generated: {report.generated_at}
Framework: {report.framework}

EXECUTIVE SUMMARY
-----------------
Total Controls Assessed: {report.summary['total_controls']}
Compliance Rate: {report.summary['compliance_rate']}%

Status Breakdown:
  - Compliant: {report.summary['compliant']}
  - Non-Compliant: {report.summary['non_compliant']}
  - Partial: {report.summary['partial']}
  - Critical Issues: {report.summary['critical_issues']}

Audit Ready: {'YES' if report.summary['audit_ready'] else 'NO - Action Required'}

DETAILED FINDINGS
-----------------
"""

    for control in report.controls:
        status_icon = {
            ComplianceStatus.COMPLIANT: "[PASS]",
            ComplianceStatus.NON_COMPLIANT: "[FAIL]",
            ComplianceStatus.PARTIAL: "[PARTIAL]",
            ComplianceStatus.NEEDS_REVIEW: "[REVIEW]",
            ComplianceStatus.NOT_APPLICABLE: "[N/A]"
        }[control.status]

        doc += f"""
{control.id}: {control.requirement} {status_icon}
Category: {control.category}
Severity: {control.severity.value.upper()}
Description: {control.description}
"""

        if control.evidence:
            doc += "Evidence:\n"
            for e in control.evidence:
                doc += f"  - {e}\n"

        if control.findings:
            doc += "Findings:\n"
            for f in control.findings:
                doc += f"  - {f}\n"

        if control.remediation:
            doc += f"Remediation: {control.remediation}\n"

        doc += "-" * 40 + "\n"

    doc += """
================================================================================
                              END OF REPORT
================================================================================
"""

    return doc

# Generate document
doc = generate_compliance_document(report)
print(doc)

# Save to file
with open("compliance_report.txt", "w") as f:
    f.write(doc)
```
