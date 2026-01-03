---
name: cursor-compliance-audit
description: |
  Compliance and security auditing for Cursor usage. Triggers on "cursor compliance",
  "cursor audit", "cursor security review", "cursor soc2", "cursor gdpr".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Compliance & Security Audit

## Compliance Overview

### Cursor's Compliance Status
```
Cursor maintains:
- SOC 2 Type II certification
- GDPR compliance
- CCPA compliance
- Enterprise security controls

Review latest:
- cursor.com/security
- cursor.com/privacy
- cursor.com/compliance
```

### Your Responsibilities
```
As a customer, you're responsible for:
- User access management
- Data classification
- Policy enforcement
- Training and awareness
- Incident response
- Regular audits
```

## Security Audit Checklist

### Access Control Audit
```
[ ] User accounts reviewed (quarterly)
[ ] Inactive accounts disabled
[ ] Role assignments appropriate
[ ] Admin access minimized
[ ] SSO enforced (if applicable)
[ ] 2FA/MFA enabled
[ ] API keys rotated
[ ] Access logs reviewed
```

### Data Protection Audit
```
[ ] Privacy Mode configured appropriately
[ ] .cursorignore covers sensitive files
[ ] Credentials not in code
[ ] Secrets in environment variables
[ ] Data classification documented
[ ] Retention policies defined
[ ] Encryption verified
```

### Configuration Audit
```
[ ] .cursorrules reviewed
[ ] Indexing exclusions verified
[ ] Telemetry settings confirmed
[ ] Network settings secure
[ ] Extension security reviewed
[ ] Update policy defined
```

## Compliance by Framework

### SOC 2 Considerations

#### Trust Service Criteria
```
Security:
[ ] Access controls documented
[ ] Authentication mechanisms verified
[ ] Security monitoring in place
[ ] Incident response plan exists

Availability:
[ ] Backup procedures defined
[ ] Recovery plan tested
[ ] SLA understood

Confidentiality:
[ ] Data classification applied
[ ] Privacy Mode used appropriately
[ ] Encryption in transit/at rest

Privacy:
[ ] Data usage documented
[ ] Consent mechanisms clear
[ ] Deletion procedures defined
```

#### Evidence Collection
```
Document for auditors:

Access Logs:
- User login history
- Admin actions
- API key usage

Configuration:
- .cursorrules content
- .cursorignore content
- Privacy settings

Policies:
- Acceptable use policy
- Data handling procedures
- Incident response plan
```

### GDPR Considerations

#### Data Processing
```
Document:
- What data is processed
- Legal basis for processing
- Data retention periods
- Third-party processors (AI providers)

Cursor processes:
- Email (account)
- Usage data (analytics)
- Code snippets (AI processing)
```

#### Data Subject Rights
```
Ensure capability to:

Right to Access:
[ ] Export user data
[ ] Provide processing info

Right to Rectification:
[ ] Update user information
[ ] Correct inaccuracies

Right to Erasure:
[ ] Delete user accounts
[ ] Remove associated data

Right to Portability:
[ ] Export in readable format
[ ] Transfer to another provider
```

#### Documentation Requirements
```
Maintain:
- Records of processing activities
- Data protection impact assessment
- Privacy policy
- Data processing agreements
- Consent records (if applicable)
```

### HIPAA Considerations

#### For Healthcare Organizations
```
If processing PHI:

Technical Safeguards:
[ ] Privacy Mode REQUIRED
[ ] Exclude PHI from indexing
[ ] Audit logs enabled
[ ] Access controls strict

Administrative Safeguards:
[ ] Policies documented
[ ] Training completed
[ ] Risk assessment done
[ ] BAA in place (if required)

Physical Safeguards:
[ ] Workstation security
[ ] Device controls
```

#### Recommended Configuration
```yaml
# .cursorrules for HIPAA
hipaa-compliance: true

rules:
  - Never include PHI in prompts
  - Privacy Mode required
  - No patient data in code
  - Audit all access

exclusions:
  - patient-data/
  - medical-records/
  - *.phi.*
```

## Audit Procedures

### Quarterly Security Review
```
Week 1: Access Audit
- Review all user accounts
- Verify role assignments
- Check for unused accounts
- Review admin access

Week 2: Configuration Audit
- Review .cursorrules
- Check .cursorignore
- Verify privacy settings
- Review API keys

Week 3: Data Audit
- Check for exposed secrets
- Verify data classification
- Review data flows
- Check retention compliance

Week 4: Documentation
- Update policies
- Record findings
- Plan remediation
- Report to stakeholders
```

### Annual Compliance Review
```
Comprehensive review:

1. Policy Review
   - Update acceptable use policy
   - Review data handling procedures
   - Update incident response plan

2. Risk Assessment
   - Identify new risks
   - Evaluate existing controls
   - Prioritize improvements

3. Training Assessment
   - Review training effectiveness
   - Update training materials
   - Conduct refresher training

4. Vendor Review
   - Review Cursor's compliance
   - Check AI provider compliance
   - Update risk register

5. Documentation Update
   - Update all policies
   - Document changes
   - Archive old versions
```

## Audit Tools

### Automated Scanning
```bash
# Scan for secrets in codebase
git secrets --scan

# Check for exposed credentials
trufflehog filesystem --directory=.

# Review git history for secrets
git log --all --full-history -- "*.env"
```

### Configuration Verification
```bash
# Verify .cursorignore covers sensitive files
cat .cursorignore | grep -E "(env|secret|key|credential)"

# Check for sensitive files not excluded
find . -name "*.env*" -o -name "*.key" -o -name "*secret*" \
  | grep -v node_modules

# List files being indexed
# (Check Cursor index status in UI)
```

### Access Log Analysis
```
Review in Admin Dashboard:
- User login patterns
- Unusual access times
- Failed login attempts
- Admin action log
```

## Remediation

### Common Findings

#### Finding: Secrets in Code
```
Severity: High

Remediation:
1. Remove secrets immediately
2. Rotate affected credentials
3. Update .cursorignore
4. Scan for other instances
5. Implement pre-commit hooks
```

#### Finding: Stale Accounts
```
Severity: Medium

Remediation:
1. Identify inactive accounts
2. Confirm with managers
3. Disable accounts
4. Document removal
5. Set up regular review
```

#### Finding: Missing Documentation
```
Severity: Low-Medium

Remediation:
1. Create missing policies
2. Document configurations
3. Train team on policies
4. Schedule regular updates
```

## Audit Reporting

### Report Template
```markdown
# Cursor Security Audit Report

Date: [DATE]
Auditor: [NAME]
Scope: [SCOPE]

## Executive Summary
[High-level findings and risk assessment]

## Findings

### Critical
[List critical findings]

### High
[List high-priority findings]

### Medium
[List medium-priority findings]

### Low
[List low-priority findings]

## Remediation Plan
[Timeline and actions]

## Recommendations
[Long-term improvements]

## Next Audit
[Scheduled date and scope]
```

### Stakeholder Communication
```
Report distribution:
- Security team: Full report
- IT management: Summary + actions
- Executives: Executive summary
- Compliance: Relevant sections

Frequency:
- Quarterly: Summary update
- Annually: Full audit report
- Ad-hoc: Incident reports
```
