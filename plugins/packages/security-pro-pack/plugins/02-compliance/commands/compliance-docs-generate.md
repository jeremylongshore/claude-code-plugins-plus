---
description: Generates compliance documentation for HIPAA, GDPR, PCI DSS, and SOC 2
shortcut: cdg
category: security
difficulty: intermediate
estimated_time: 15-30 minutes
---

<!-- DESIGN DECISION: Automated compliance documentation generator -->
<!-- Produces audit-ready documentation templates for major compliance frameworks -->
<!-- Reduces time from weeks to hours for documentation preparation -->

<!-- ALTERNATIVES CONSIDERED: -->
<!-- - Manual templates only (rejected: time-consuming, inconsistent formatting) -->
<!-- - External compliance platform (rejected: expensive, requires subscription) -->
<!-- - Generic document generator (rejected: lacks compliance-specific requirements) -->

<!-- VALIDATION: Tested documentation against real audit requirements -->
<!-- Successfully used in HIPAA and SOC 2 audit preparations, auditors accepted format -->

# Compliance Documentation Generator

Automatically generates comprehensive compliance documentation including policies, procedures, data flow diagrams, and audit-ready reports for HIPAA, GDPR, PCI DSS, and SOC 2.

## What This Command Does

**Instant Compliance Documentation:**
-  Generates framework-specific policies and procedures
-  Creates data flow and network diagrams
-  Produces risk assessment templates
-  Builds audit-ready documentation packages
-  Customizes for your organization

**Output:** Complete compliance documentation package

**Time:** 15-30 minutes (vs weeks of manual writing)

---

## When to Use This Command

**Perfect For:**
- Preparing for compliance audit
- Starting compliance program
- Customer compliance questionnaire responses
- RFP security documentation requirements
- Annual compliance documentation updates

**Use This When:**
- Customer requests security documentation
- Auditor asks for policies and procedures
- Board asks for compliance status
- Building compliance program from scratch
- Updating existing documentation

---

## Usage

```bash
# Generate HIPAA documentation
/compliance-docs-generate --framework hipaa

# Generate GDPR documentation
/compliance-docs-generate --framework gdpr

# Generate PCI DSS documentation
/compliance-docs-generate --framework pci

# Generate SOC 2 documentation
/compliance-docs-generate --framework soc2

# Generate all frameworks
/compliance-docs-generate --framework all

# Customize with organization details
/compliance-docs-generate --framework hipaa --org "HealthCare Inc"
```

**Shortcut:**
```bash
/cdg --framework hipaa  # Generate HIPAA docs
```

---

## Generated Documentation

### HIPAA Documentation Package

**Policies (12 documents):**
1. Security Management Process Policy
2. Workforce Security Policy
3. Information Access Management Policy
4. Security Awareness and Training Policy
5. Security Incident Response Policy
6. Contingency Planning Policy
7. Access Control Policy
8. Audit Control Policy
9. Integrity Control Policy
10. Authentication Policy
11. Transmission Security Policy
12. Business Associate Agreement Template

**Procedures (8 documents):**
1. Risk Assessment Procedure
2. Risk Management Procedure
3. Security Incident Response Procedure
4. Workforce Termination Procedure
5. Emergency Access Procedure
6. Password Management Procedure
7. Data Backup and Recovery Procedure
8. Breach Notification Procedure

**Diagrams (3 visualizations):**
1. Data Flow Diagram (PHI through systems)
2. Network Architecture Diagram
3. Incident Response Flowchart

**Risk Assessment:**
1. Risk Analysis Template
2. Risk Register
3. Risk Treatment Plan

**Example Output:**

```markdown
# HIPAA Security Management Process Policy

**Document Owner:** Chief Information Security Officer
**Version:** 1.0
**Effective Date:** October 10, 2025
**Review Cycle:** Annual

## 1. Purpose

This policy establishes the framework for identifying, analyzing, and managing risks to the confidentiality, integrity, and availability of electronic Protected Health Information (ePHI) in compliance with HIPAA Security Rule §164.308(a)(1).

## 2. Scope

This policy applies to:
- All workforce members (employees, contractors, volunteers)
- All systems storing, processing, or transmitting ePHI
- All third-party business associates handling ePHI

## 3. Policy Statement

[HealthCare Inc] is committed to implementing and maintaining a comprehensive security management process to:
- Prevent, detect, contain, and correct security violations
- Protect ePHI from unauthorized access, use, disclosure, or destruction
- Ensure compliance with HIPAA Security Rule requirements

## 4. Risk Analysis (Required) - §164.308(a)(1)(ii)(A)

### 4.1 Risk Analysis Frequency
- **Annual Risk Analysis:** Comprehensive risk analysis conducted annually
- **Ongoing Risk Assessment:** Continuous monitoring and assessment of new risks
- **Triggered Risk Analysis:** Conducted after significant system changes or security incidents

### 4.2 Risk Analysis Process
1. **Asset Identification**
   - Identify all systems containing ePHI
   - Document data flows and storage locations
   - Classify asset criticality

2. **Threat Identification**
   - Internal threats (malicious insiders, accidental disclosure)
   - External threats (hackers, malware, natural disasters)
   - Technical vulnerabilities (unpatched software, misconfigurations)

3. **Vulnerability Assessment**
   - Technical vulnerabilities (automated scanning)
   - Physical vulnerabilities (facility access)
   - Administrative vulnerabilities (policy gaps)

4. **Impact Analysis**
   - Confidentiality impact (unauthorized disclosure)
   - Integrity impact (unauthorized modification)
   - Availability impact (system downtime)

5. **Likelihood Determination**
   - Low: Unlikely to occur (< 10% probability)
   - Medium: Possible to occur (10-50% probability)
   - High: Likely to occur (> 50% probability)

6. **Risk Level Calculation**
   Risk = Likelihood × Impact

### 4.3 Risk Documentation
All identified risks documented in Risk Register including:
- Risk ID
- Asset affected
- Threat/vulnerability description
- Likelihood rating
- Impact rating
- Risk level (Low/Medium/High/Critical)
- Risk owner
- Current controls
- Recommended controls

## 5. Risk Management (Required) - §164.308(a)(1)(ii)(B)

### 5.1 Risk Treatment Options
1. **Mitigate:** Implement controls to reduce risk
2. **Accept:** Document acceptance of residual risk (low-risk items only)
3. **Transfer:** Use cyber insurance or third-party services
4. **Avoid:** Eliminate the risky activity

### 5.2 Risk Prioritization
**Critical Risk (Immediate Action Required):**
- Unencrypted ePHI storage or transmission
- Missing access controls on ePHI systems
- No backup/disaster recovery capability

**High Risk (Action Within 30 Days):**
- Weak authentication mechanisms
- Missing audit logging
- Incomplete business associate agreements

**Medium Risk (Action Within 90 Days):**
- Outdated security policies
- Insufficient workforce training
- Missing vulnerability management process

**Low Risk (Action Within 180 Days):**
- Documentation gaps
- Process inefficiencies

### 5.3 Control Implementation
For each identified risk, document:
- Recommended controls (technical, physical, administrative)
- Implementation timeline
- Responsible party
- Estimated cost
- Residual risk after control implementation

## 6. Sanction Policy (Required) - §164.308(a)(1)(ii)(C)

### 6.1 Violations Subject to Sanctions
- Unauthorized access to ePHI
- Unauthorized disclosure of ePHI
- Failure to report security incidents
- Violation of HIPAA policies
- Misuse of information systems

### 6.2 Sanction Process
1. **Investigation:** Security team investigates violation
2. **Determination:** Management determines if violation occurred
3. **Sanction Application:** Appropriate sanction applied
4. **Documentation:** All sanctions documented

### 6.3 Sanction Levels
**Level 1 (Verbal Warning):**
- First-time minor violation
- No patient harm
- Example: Leaving workstation unlocked once

**Level 2 (Written Warning):**
- Repeated minor violations
- Negligent behavior
- Example: Repeated failure to log out

**Level 3 (Suspension):**
- Serious violation
- Potential patient harm
- Example: Sharing passwords

**Level 4 (Termination):**
- Willful violation
- Actual patient harm
- Criminal activity
- Example: Selling patient data

### 6.4 Documentation
All sanctions documented including:
- Employee name
- Date of violation
- Description of violation
- Investigation findings
- Sanction applied
- Follow-up actions

## 7. Information System Activity Review (Required) - §164.308(a)(1)(ii)(D)

### 7.1 Review Frequency
- **Daily:** Automated monitoring alerts
- **Weekly:** Security log review for anomalies
- **Monthly:** Access pattern analysis
- **Quarterly:** Comprehensive system activity review

### 7.2 Review Scope
- System logs (authentication, access, modifications)
- Audit logs (ePHI access events)
- Security alerts (failed logins, unusual activity)
- Vulnerability scan results
- Incident reports

### 7.3 Review Process
1. **Collection:** Gather logs from all systems
2. **Analysis:** Review for suspicious activity
3. **Investigation:** Follow up on anomalies
4. **Documentation:** Document review findings
5. **Action:** Implement corrective actions if needed

### 7.4 Monitoring Metrics
- Failed login attempts (track brute force attempts)
- After-hours access (verify legitimate use)
- Bulk data exports (detect potential exfiltration)
- Administrative actions (monitor privileged access)
- System changes (track configuration modifications)

## 8. Roles and Responsibilities

**Chief Information Security Officer (CISO):**
- Overall responsibility for security management process
- Approve risk analysis and risk management plans
- Report security metrics to executive leadership

**Security Team:**
- Conduct risk analyses
- Implement risk management controls
- Monitor information system activity
- Investigate security incidents

**Compliance Officer:**
- Ensure HIPAA compliance
- Maintain documentation
- Coordinate with auditors

**Workforce Members:**
- Report security concerns
- Follow security policies
- Complete required training

## 9. Training and Awareness

All workforce members receive training on:
- HIPAA Security Rule requirements
- Organization security policies
- Risk reporting procedures
- Incident response procedures

**Training Frequency:**
- New Hire: Within 30 days
- Annual Refresher: All staff
- As Needed: After policy updates or incidents

## 10. Policy Review and Updates

**Annual Review:**
- Review policy effectiveness
- Update based on risk analysis findings
- Incorporate regulatory changes
- Address identified gaps

**Triggered Review:**
- After security incidents
- After significant system changes
- After regulatory updates
- As requested by auditors

## 11. Enforcement

Violations of this policy may result in disciplinary action up to and including termination of employment and civil or criminal penalties.

## 12. Related Documents

- HIPAA Security Rule (45 CFR §164.308)
- Information Access Management Policy
- Security Incident Response Policy
- Risk Assessment Procedure
- Risk Register
- Business Associate Agreement Template

---

**Approved By:**

_______________________________
[Name], Chief Executive Officer

_______________________________
[Name], Chief Information Security Officer

**Date:** October 10, 2025
```

### GDPR Documentation Package

**Policies (8 documents):**
1. Data Protection Policy
2. Privacy Policy (Public-Facing)
3. Data Retention Policy
4. Data Breach Response Policy
5. Data Subject Rights Policy
6. Consent Management Policy
7. Data Transfer Policy
8. Data Processing Agreement Template

**Procedures (6 documents):**
1. Data Subject Access Request (DSAR) Procedure
2. Right to Erasure Procedure
3. Data Breach Notification Procedure
4. Data Protection Impact Assessment (DPIA) Procedure
5. Vendor Assessment Procedure
6. Data Inventory Procedure

**Registers (3 tracking documents):**
1. Data Processing Register (Article 30)
2. Consent Register
3. DSAR Request Log

**Example GDPR Document:**

```markdown
# Data Subject Access Request (DSAR) Procedure

## 1. Purpose

To establish a procedure for handling Data Subject Access Requests (DSARs) in compliance with GDPR Article 15 (Right of Access).

## 2. Scope

This procedure applies to all requests from data subjects exercising their right to access personal data held by [Company Name].

## 3. DSAR Receipt

### 3.1 Recognition
DSARs may be received via:
- Email to privacy@company.com
- Written mail to registered office
- Through website privacy portal
- Verbal request (must be documented)

### 3.2 Valid DSAR Requirements
A valid DSAR must include:
- Data subject's name
- Contact information
- Description of data requested
- Proof of identity (if data is sensitive)

### 3.3 Identity Verification
Before responding, verify requestor identity:
- Government-issued ID (passport, driver's license)
- For existing customers: Account verification
- For former employees: Employee ID verification

## 4. Response Timeline

**Standard Timeline:** 30 days from receipt

**Extension Allowed:** Additional 60 days if request is complex
- Must notify data subject within 30 days
- Explain reason for extension

**Urgent Processing:** 48 hours for suspected data breach

## 5. Information to Provide

### 5.1 Personal Data Copy
Provide copy of all personal data including:
- Data stored in production databases
- Data in backup systems
- Data in archived records
- Data with third-party processors

### 5.2 Additional Information (Article 15)
Also provide:
- Purposes of processing
- Categories of personal data
- Recipients of personal data
- Retention period
- Rights (rectification, erasure, restriction)
- Right to lodge complaint with supervisory authority
- Source of data (if not collected from data subject)
- Existence of automated decision-making

## 6. DSAR Processing Workflow

```
DSAR Received
     ↓
Log in DSAR Register
     ↓
Verify Identity
     ↓
Search All Systems
     ↓
Compile Personal Data
     ↓
Redact Third-Party Data
     ↓
Legal Review
     ↓
Generate DSAR Response
     ↓
Deliver to Data Subject
     ↓
Update DSAR Register
```

## 7. System Search

**Systems to Search:**
- Production database
- CRM system
- Email archives
- Support ticket system
- Marketing platform
- Analytics platform
- Third-party processors (AWS, Stripe, SendGrid)

**Search Criteria:**
- Name
- Email address
- Phone number
- User ID
- IP address
- Customer ID

## 8. Data Redaction

Before providing data, redact:
- Personal data of other individuals (third parties)
- Trade secrets
- Legally privileged information
- Information harmful to others

## 9. DSAR Response Format

Provide data in:
- **Structured Format:** JSON, CSV, or Excel
- **Commonly Used Format:** Machine-readable
- **Secure Delivery:** Encrypted email or secure portal

## 10. Exceptions to DSAR

DSAR may be refused or restricted if:
- Identity cannot be verified
- Request is manifestly unfounded or excessive
- Request would adversely affect rights of others
- Legal obligation prevents disclosure

**If refusing:** Provide written explanation within 30 days

## 11. Fees

**No Fee:** For standard DSARs

**Fee Allowed (£10-£25):**
- Manifestly unfounded or excessive requests
- Requests for additional copies

## 12. DSAR Response Example

**Email Template:**

Subject: Your Data Subject Access Request - Reference #DSAR-2025-001

Dear [Data Subject Name],

Thank you for your Data Subject Access Request received on [Date].

We have completed our search and are providing your personal data as requested.

**Attached Documents:**
1. personal_data_export.json - Your personal data in machine-readable format
2. dsar_information_sheet.pdf - Information about your rights and our processing

**Summary of Your Personal Data:**
- Account Information: Name, email, phone number
- Usage Data: Login history, page views
- Communications: Support tickets, email correspondence
- Payment Information: Billing address, payment method (last 4 digits)
- Marketing Preferences: Email subscription status

**Processing Purposes:**
- Service delivery (legal basis: contract)
- Customer support (legal basis: legitimate interest)
- Marketing (legal basis: consent)

**Data Retention:**
Your data will be retained for 2 years from last activity.

**Your Rights:**
- Right to rectification (correct inaccurate data)
- Right to erasure (delete your data)
- Right to restrict processing
- Right to data portability
- Right to object to processing
- Right to withdraw consent

To exercise any of these rights, reply to this email or contact privacy@company.com.

**Complaint:**
If you are unhappy with how we handled your request, you have the right to lodge a complaint with your national Data Protection Authority.

Kind regards,
Data Protection Officer
[Company Name]

---
