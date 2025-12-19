---
name: assisting-with-soc2-audit-preparation
description: |
  Automate SOC 2 audit preparation including evidence gathering, control assessment, and compliance gap identification.
  Use when you need to prepare for SOC 2 audits, assess Trust Service Criteria compliance, document security controls, or generate readiness reports.
  Trigger with phrases like "SOC 2 audit preparation", "SOC 2 readiness assessment", "collect SOC 2 evidence", or "Trust Service Criteria compliance".
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash(audit-collect:*), compliance-check:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
## Prerequisites

Before using this skill, ensure:
- Documentation directory accessible in {baseDir}/docs/
- Infrastructure-as-code and configuration files available
- Access to cloud provider logs (AWS CloudTrail, Azure Activity Log, GCP Audit Logs)
- Security policies and procedures documented
- Employee training records available
- Incident response documentation accessible
- Write permissions for audit reports in {baseDir}/soc2-audit/

## Instructions

### 1. Trust Service Criteria Assessment

Evaluate controls across five categories:

**Security (Common Criteria)** - Required for all SOC 2 audits:
- CC1: Control Environment
- CC2: Communication and Information
- CC3: Risk Assessment
- CC4: Monitoring Activities
- CC5: Control Activities
- CC6: Logical and Physical Access Controls
- CC7: System Operations
- CC8: Change Management
- CC9: Risk Mitigation

**Additional Criteria** (Optional):
- Availability
- Processing Integrity
- Confidentiality
- Privacy

### 2. Evidence Collection Phase

**Security Controls Evidence**:
- Access control policies and configurations
- Multi-factor authentication implementation
- Password policy documentation
- Firewall rules and network segmentation
- Encryption at rest and in transit
- Security monitoring and alerting configs

**Operational Evidence**:
- Change management logs
- Backup and recovery procedures
- Disaster recovery testing results
- System monitoring dashboards
- Capacity planning documentation
- Performance metrics

**Policy and Procedure Evidence**:
- Information security policy
- Incident response plan
- Business continuity plan
- Vendor management procedures
- Employee onboarding/offboarding
- Security awareness training records

**System Evidence**:
- System architecture diagrams
- Data flow diagrams
- Asset inventory
- Software bill of materials (SBOM)
- Configuration management database

### 3. Control Effectiveness Testing

For each control point:
- Verify control design (is it properly designed?)
- Test operating effectiveness (is it working as intended?)
- Document test results with screenshots/logs
- Identify gaps or weaknesses
- Recommend remediation actions

### 4. Compliance Gap Analysis

Compare current state against SOC 2 requirements:
- Missing controls (critical gaps)
- Partially implemented controls (needs improvement)
- Improperly documented controls (evidence gaps)
- Ineffective controls (design or operating failures)

### 5. Evidence Documentation

Organize evidence by Trust Service Criteria:
```
{baseDir}/soc2-audit/
├── CC1-control-environment/
│   ├── org-chart.pdf
│   ├── security-policy.md
│   └── training-records.xlsx
├── CC6-access-controls/
│   ├── iam-policies.json
│   ├── mfa-config.yaml
│   └── access-review-logs.csv
├── CC7-system-operations/
│   ├── monitoring-configs/
│   ├── backup-procedures.md
│   └── incident-logs/
└── readiness-report.md
```

### 6. Generate Readiness Report

Create comprehensive SOC 2 readiness assessment with:
- Executive summary with readiness score
- Control-by-control assessment
- Gap analysis with severity ratings
- Remediation roadmap with timelines
- Evidence collection checklist
- Auditor interview preparation guide

## Output

The skill produces:

**Primary Output**: SOC 2 readiness report saved to {baseDir}/soc2-audit/readiness-report-YYYYMMDD.md

**Report Structure**:
```
# SOC 2 Readiness Assessment
Assessment Date: 2024-01-15
Organization: TechCorp Inc.
Audit Type: SOC 2 Type II (Security + Availability)

## Executive Summary
- Overall Readiness: 75% (Needs Improvement)
- Controls Implemented: 28/40 (70%)
- Critical Gaps: 3
- High Priority Items: 8
- Estimated Remediation Time: 8-12 weeks

## Readiness by Trust Service Category

### CC1: Control Environment (80%)
✅ Implemented (4):
- Organizational structure documented
- Security policy established
- Risk assessment framework in place
- Board oversight of security

⚠️ Gaps (1):
- Security role and responsibility matrix incomplete

### CC6: Logical and Physical Access Controls (60%)
✅ Implemented (5):
- Multi-factor authentication enabled
- Role-based access control (RBAC) implemented
- Password policy enforced
- Access review process established
- Visitor access controls in place

❌ Critical Gaps (2):
- No automated user deprovisioning
- Privileged access not logged/monitored

⚠️ High Priority (3):
- Access logs retention < 1 year
- No formal access request workflow
- Physical security cameras not monitored 24/7

### CC7: System Operations (70%)
[Similar breakdown...]

## Critical Gaps Requiring Immediate Action

### 1. Automated User Deprovisioning (CC6.2)
**Current State**: Manual offboarding process
**Risk**: Terminated employees retain system access
**Evidence**: {baseDir}/hr/offboarding-checklist.pdf
**Remediation**:
- Implement automated deprovisioning tied to HR system
- Set up alerts for access not removed within 24 hours
- Estimated effort: 2-3 weeks
**Priority**: CRITICAL

### 2. Privileged Access Monitoring (CC6.7)
**Current State**: No logging of admin actions
**Risk**: Insider threats undetected
**Remediation**:
- Enable audit logging for all admin accounts
- Set up SIEM alerts for privileged actions
- Implement session recording for production access
**Priority**: CRITICAL

### 3. Disaster Recovery Testing (CC7.4)
**Current State**: DR plan exists but never tested
**Risk**: Recovery time objectives may not be achievable
**Remediation**:
- Schedule quarterly DR tests
- Document test results
- Update plan based on test findings
**Priority**: CRITICAL

## Evidence Collection Status

| Control | Evidence Type | Status | Location |
|---------|--------------|--------|----------|
| CC1.1 | Org Chart | ✅ Complete | {baseDir}/soc2-audit/CC1/ |
| CC6.1 | MFA Config | ✅ Complete | {baseDir}/soc2-audit/CC6/ |
| CC6.2 | Offboarding Logs | ❌ Missing | N/A |
| CC7.1 | Monitoring Dashboards | ⚠️ Partial | Need 90-day history |

## Remediation Roadmap

**Weeks 1-2 (Critical Fixes)**:
- Implement automated deprovisioning
- Enable privileged access monitoring
- Begin DR test planning

**Weeks 3-6 (High Priority)**:
- Extend log retention to 1 year
- Implement access request workflow
- Complete initial DR test

**Weeks 7-12 (Medium Priority)**:
- Enhance physical security monitoring
- Improve change management documentation
- Complete second DR test cycle

## Auditor Preparation

**Key Interview Topics**:
- Control environment and tone from the top
- Incident response capabilities
- Change management process
- Access control procedures
- Monitoring and alerting effectiveness

**Suggested Interviewees**:
- CTO/CISO (control environment)
- Security Engineer (technical controls)
- HR Manager (employee lifecycle)
- Operations Lead (monitoring, DR)

## Next Steps

1. Review and approve remediation roadmap
2. Assign owners to each gap remediation
3. Begin evidence collection for completed controls
4. Schedule monthly progress reviews
5. Engage SOC 2 auditor for scoping discussion
```

**Secondary Outputs**:
- Evidence collection checklist (Excel/CSV)
- Control testing templates
- Auditor questionnaire responses
- Gap tracking dashboard (JSON for dashboarding tools)

## Error Handling

**Common Issues and Resolutions**:

1. **Missing Evidence Files**
   - Error: "Cannot locate security policy in {baseDir}/docs/"
   - Resolution: Request document locations from user
   - Fallback: Mark as evidence gap in report

2. **Incomplete Access Logs**
   - Error: "Log retention < SOC 2 requirement (1 year)"
   - Resolution: Note current retention period, flag as gap
   - Remediation: Extend retention, backfill if possible

3. **Undocumented Procedures**
   - Error: "No incident response playbook found"
   - Resolution: Flag as critical gap requiring documentation
   - Assistance: Provide template for creating procedure

4. **Cloud Provider Access Required**
   - Error: "Cannot assess AWS controls without API access"
   - Resolution: Request CloudTrail exports or console screenshots
   - Alternative: Provide manual checklist for cloud controls

5. **Multiple Environments Not Distinguished**
   - Error: "Production and dev configs mixed in {baseDir}/"
   - Resolution: Request environment separation or clear labeling
   - Risk: May audit wrong environment

## Resources

**SOC 2 Framework References**:
- AICPA Trust Service Criteria: https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/trustdataintegritytaskforce.html
- SOC 2 Compliance Checklist: https://secureframe.com/hub/soc-2/checklist

**Control Implementation Guides**:
- CIS Controls: https://www.cisecurity.org/controls/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework

**Compliance Automation Tools**:
- Drata: SOC 2 compliance automation
- Vanta: Continuous compliance monitoring
- Secureframe: Evidence collection platform

**Template Documents**:
- Information Security Policy: {baseDir}/templates/security-policy-template.md
- Incident Response Plan: {baseDir}/templates/incident-response-template.md
- Risk Assessment Template: {baseDir}/templates/risk-assessment-template.xlsx

**Auditor Resources**:
- Find SOC 2 auditors: https://www.aicpa.org/
- SOC 2 vs ISO 27001 comparison
- Type I vs Type II audit differences

**Evidence Examples**:
- Sample SOC 2 control matrix
- Evidence collection best practices
- Auditor interview preparation guide