---
name: klingai-compliance-review
description: |
  Conduct compliance reviews for Kling AI integrations. Use when preparing for audits,
  ensuring regulatory compliance, or reviewing security posture. Trigger with phrases like
  'klingai compliance', 'kling ai audit prep', 'klingai security review', 'video generation compliance'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Compliance Review

## Overview

This skill provides compliance review frameworks, security checklists, and audit preparation guides for Kling AI integrations to meet regulatory and organizational requirements.

## Prerequisites

- Kling AI integration in production
- Understanding of applicable regulations
- Access to system documentation

## Instructions

Follow these steps for compliance review:

1. **Identify Requirements**: Determine applicable regulations
2. **Assess Current State**: Audit existing implementation
3. **Gap Analysis**: Identify compliance gaps
4. **Remediate Issues**: Fix identified problems
5. **Document Evidence**: Prepare audit materials

## Compliance Frameworks

```
Applicable Regulations by Industry:

GENERAL:
- GDPR (EU data protection)
- CCPA (California privacy)
- SOC 2 (security controls)

FINANCIAL:
- PCI DSS (payment data)
- SOX (financial reporting)
- FINRA (financial services)

HEALTHCARE:
- HIPAA (health information)
- HITECH (health IT)

GOVERNMENT:
- FedRAMP (federal cloud)
- NIST 800-53 (security controls)
- ITAR (export controls)

AI-SPECIFIC:
- EU AI Act (AI regulation)
- NIST AI RMF (AI risk management)
```

## Compliance Checker

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"
    NEEDS_REVIEW = "needs_review"

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class ComplianceControl:
    id: str
    framework: str
    category: str
    requirement: str
    description: str
    status: ComplianceStatus = ComplianceStatus.NEEDS_REVIEW
    evidence: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    remediation: Optional[str] = None
    severity: Severity = Severity.MEDIUM

@dataclass
class ComplianceReport:
    report_id: str
    generated_at: str
    framework: str
    controls: List[ComplianceControl]
    summary: Dict

class KlingAIComplianceChecker:
    """Compliance checking for Kling AI integrations."""

    def __init__(self):
        self.controls: List[ComplianceControl] = []
        self._initialize_controls()

    def _initialize_controls(self):
        """Initialize compliance controls."""
        # Data Protection Controls
        self.controls.extend([
            ComplianceControl(
                id="DP-001",
                framework="GDPR",
                category="Data Protection",
                requirement="Data Minimization",
                description="Only collect and process data necessary for video generation",
                severity=Severity.HIGH
            ),
            ComplianceControl(
                id="DP-002",
                framework="GDPR",
                category="Data Protection",
                requirement="Data Retention",
                description="Define and enforce retention periods for prompts and videos",
                severity=Severity.HIGH
            ),
            ComplianceControl(
                id="DP-003",
                framework="GDPR",
                category="Data Protection",
                requirement="Right to Erasure",
                description="Ability to delete user data upon request",
                severity=Severity.CRITICAL
            ),
        ])

        # Security Controls
        self.controls.extend([
            ComplianceControl(
                id="SEC-001",
                framework="SOC2",
                category="Security",
                requirement="API Key Management",
                description="Secure storage and rotation of API keys",
                severity=Severity.CRITICAL
            ),
            ComplianceControl(
                id="SEC-002",
                framework="SOC2",
                category="Security",
                requirement="Encryption in Transit",
                description="All API calls use HTTPS/TLS",
                severity=Severity.CRITICAL
            ),
            ComplianceControl(
                id="SEC-003",
                framework="SOC2",
                category="Security",
                requirement="Access Control",
                description="Role-based access to video generation",
                severity=Severity.HIGH
            ),
            ComplianceControl(
                id="SEC-004",
                framework="SOC2",
                category="Security",
                requirement="Audit Logging",
                description="Comprehensive logging of all operations",
                severity=Severity.HIGH
            ),
        ])

        # AI Ethics Controls
        self.controls.extend([
            ComplianceControl(
                id="AI-001",
                framework="AI Ethics",
                category="AI Governance",
                requirement="Content Policy",
                description="Implement content filtering for harmful outputs",
                severity=Severity.HIGH
            ),
            ComplianceControl(
                id="AI-002",
                framework="AI Ethics",
                category="AI Governance",
                requirement="Transparency",
                description="Disclose AI-generated content to users",
                severity=Severity.MEDIUM
            ),
            ComplianceControl(
                id="AI-003",
                framework="AI Ethics",
                category="AI Governance",
                requirement="Human Oversight",
                description="Human review process for flagged content",
                severity=Severity.MEDIUM
            ),
        ])

        # Operational Controls
        self.controls.extend([
            ComplianceControl(
                id="OPS-001",
                framework="SOC2",
                category="Operations",
                requirement="Incident Response",
                description="Documented incident response procedures",
                severity=Severity.HIGH
            ),
            ComplianceControl(
                id="OPS-002",
                framework="SOC2",
                category="Operations",
                requirement="Change Management",
                description="Controlled deployment process",
                severity=Severity.MEDIUM
            ),
            ComplianceControl(
                id="OPS-003",
                framework="SOC2",
                category="Operations",
                requirement="Backup & Recovery",
                description="Data backup and recovery procedures",
                severity=Severity.HIGH
            ),
        ])

    def assess_control(
        self,
        control_id: str,
        status: ComplianceStatus,
        evidence: List[str] = None,
        findings: List[str] = None,
        remediation: str = None
    ):
        """Assess a specific control."""
        for control in self.controls:
            if control.id == control_id:
                control.status = status
                if evidence:
                    control.evidence = evidence
                if findings:
                    control.findings = findings
                if remediation:
                    control.remediation = remediation
                return

        raise ValueError(f"Control not found: {control_id}")

    def generate_report(self, framework: str = None) -> ComplianceReport:
        """Generate compliance report."""
        import uuid

        controls = self.controls
        if framework:
            controls = [c for c in controls if c.framework == framework]

        # Calculate summary
        total = len(controls)
        compliant = len([c for c in controls if c.status == ComplianceStatus.COMPLIANT])
        non_compliant = len([c for c in controls if c.status == ComplianceStatus.NON_COMPLIANT])
        partial = len([c for c in controls if c.status == ComplianceStatus.PARTIAL])

        critical_issues = len([
            c for c in controls
            if c.status == ComplianceStatus.NON_COMPLIANT and c.severity == Severity.CRITICAL
        ])

        return ComplianceReport(
            report_id=str(uuid.uuid4())[:8],
            generated_at=datetime.utcnow().isoformat(),
            framework=framework or "All",
            controls=controls,
            summary={
                "total_controls": total,
                "compliant": compliant,
                "non_compliant": non_compliant,
                "partial": partial,
                "compliance_rate": round(compliant / total * 100, 1) if total > 0 else 0,
                "critical_issues": critical_issues,
                "audit_ready": critical_issues == 0 and non_compliant == 0
            }
        )

    def get_remediation_plan(self) -> List[Dict]:
        """Get prioritized remediation plan."""
        non_compliant = [
            c for c in self.controls
            if c.status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIAL]
        ]

        # Sort by severity
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4
        }

        sorted_controls = sorted(
            non_compliant,
            key=lambda c: severity_order[c.severity]
        )

        return [
            {
                "priority": i + 1,
                "control_id": c.id,
                "requirement": c.requirement,
                "severity": c.severity.value,
                "status": c.status.value,
                "findings": c.findings,
                "remediation": c.remediation or "Define remediation steps"
            }
            for i, c in enumerate(sorted_controls)
        ]

# Usage
checker = KlingAIComplianceChecker()

# Perform assessments
checker.assess_control(
    "SEC-001",
    ComplianceStatus.COMPLIANT,
    evidence=["API keys stored in AWS Secrets Manager", "Key rotation every 90 days"],
)

checker.assess_control(
    "SEC-002",
    ComplianceStatus.COMPLIANT,
    evidence=["All endpoints use HTTPS", "TLS 1.3 enforced"]
)

checker.assess_control(
    "DP-002",
    ComplianceStatus.NON_COMPLIANT,
    findings=["No defined retention policy for generated videos"],
    remediation="Implement 30-day retention policy with auto-deletion"
)

checker.assess_control(
    "AI-001",
    ComplianceStatus.PARTIAL,
    evidence=["Basic content filter implemented"],
    findings=["Filter doesn't cover all prohibited categories"],
    remediation="Expand content filter to include all policy categories"
)

# Generate report
report = checker.generate_report()
print(f"Compliance Rate: {report.summary['compliance_rate']}%")
print(f"Audit Ready: {report.summary['audit_ready']}")

# Get remediation plan
plan = checker.get_remediation_plan()
for item in plan:
    print(f"{item['priority']}. [{item['severity']}] {item['control_id']}: {item['requirement']}")
```

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

## Output

Successful execution produces:
- Compliance assessment report
- Gap analysis findings
- Prioritized remediation plan
- Audit-ready documentation

## Error Handling

Common errors and solutions:
1. **Missing Evidence**: Document all controls
2. **Unclear Status**: Clarify assessment criteria
3. **Outdated Assessment**: Regular review schedule

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [SOC 2 Compliance](https://www.aicpa.org/soc)
- [GDPR Requirements](https://gdpr.eu/)
- [NIST AI Risk Management](https://www.nist.gov/itl/ai-risk-management-framework)
- [AI Ethics Guidelines](https://www.oecd.ai/en/ai-principles)
