# Implementation Guide

1. Confirm scope (services, systems, period) and applicable SOC 2 criteria.
2. Gather existing controls, policies, and evidence sources.
3. Identify gaps and draft an evidence collection plan.
4. Produce an audit-ready checklist and remediation backlog.

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
${CLAUDE_SKILL_DIR}/soc2-audit/
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