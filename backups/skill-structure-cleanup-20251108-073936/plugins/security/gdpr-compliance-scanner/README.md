# GDPR Compliance Scanner Plugin

Scan applications and data systems for GDPR compliance with comprehensive checks for data protection, privacy rights, and regulatory requirements.

## Features

- **Data Protection Checks** - Encryption, anonymization, pseudonymization
- **Privacy Rights Verification** - Right to access, erasure, portability
- **Consent Management** - Cookie consent, data processing agreements
- **Data Processing Records** - Article 30 compliance
- **Breach Notification** - Incident response readiness
- **DPO Requirements** - Data Protection Officer duties

## Installation

```bash
/plugin install gdpr-compliance-scanner@claude-code-plugins-plus
```

## Usage

```bash
/scan-gdpr
# Or shortcut
/gdpr
```

## GDPR Compliance Areas

### 1. Lawful Basis for Processing (Article 6)
- Consent obtained properly
- Contract necessity documented
- Legitimate interests balanced
- Legal obligations met
- Vital interests protected
- Public task authority

### 2. Data Subject Rights (Articles 12-23)
- Right to be informed
- Right of access
- Right to rectification
- Right to erasure ("right to be forgotten")
- Right to restriction of processing
- Right to data portability
- Right to object
- Rights related to automated decision making

### 3. Data Protection by Design (Article 25)
- Privacy by default settings
- Data minimization
- Purpose limitation
- Storage limitation
- Integrity and confidentiality

### 4. Security Measures (Article 32)
- Encryption of personal data
- Pseudonymization where possible
- Regular security testing
- Incident response procedures
- Access controls
- Data backup and recovery

### 5. Data Protection Impact Assessment (Article 35)
- High-risk processing identified
- DPIA conducted for high-risk activities
- Consultation with DPO
- Mitigation measures implemented

### 6. International Data Transfers (Chapter V)
- Adequacy decisions verified
- Standard contractual clauses in place
- Binding corporate rules (if applicable)
- Derogations documented

## Example Report

```
GDPR COMPLIANCE SCAN REPORT
============================
Organization: Example Corp
Date: 2025-10-11
Compliance Score: 78% (Needs Improvement)

COMPLIANCE SUMMARY
------------------
 Data Protection Principles - 85%
 Data Subject Rights - 70%
 Security Measures - 90%
 Documentation - 65%
 Breach Procedures - 80%

CRITICAL GAPS
-------------

1. Right to Data Portability Not Implemented
   Article: 20
   Risk: HIGH
   Issue: No mechanism for users to export their data

   Required Implementation:
   - API endpoint: GET /api/user/{id}/export
   - Response format: JSON or CSV
   - Include all personal data
   - Deliver within 30 days

   Code Example:
   app.get('/api/user/:id/export', auth, async (req, res) => {
       const userData = await db.getUserData(req.params.id);
       res.json({
           personal_info: userData.profile,
           activities: userData.activities,
           preferences: userData.preferences
       });
   });

2. Cookie Consent Banner Missing
   Article: 6(1)(a), Recital 32
   Risk: HIGH
   Issue: Cookies set without explicit consent

   Required Implementation:
   - Implement cookie consent banner
   - Granular consent options
   - Easy withdrawal of consent
   - Record consent choices

3. Data Processing Records Incomplete
   Article: 30
   Risk: MEDIUM
   Issue: Missing comprehensive processing records

   Required Documentation:
   - Purpose of processing
   - Categories of data subjects
   - Categories of personal data
   - Recipients of data
   - International transfers
   - Retention periods
   - Security measures

RECOMMENDATIONS
---------------

Priority 1 (Immediate - 0-30 days):
1. Implement data portability API (40 hours)
2. Deploy cookie consent solution (16 hours)
3. Document all processing activities (24 hours)
4. Update privacy policy (8 hours)

Priority 2 (Short-term - 1-3 months):
5. Conduct Data Protection Impact Assessment (40 hours)
6. Implement automated data deletion (32 hours)
7. Create data breach response procedures (16 hours)
8. Train staff on GDPR requirements (8 hours)

Priority 3 (Medium-term - 3-6 months):
9. Appoint Data Protection Officer (ongoing)
10. Review and update data processing agreements (40 hours)
11. Implement privacy by design in new features (ongoing)
```

## Compliance Checklist

### Lawful Processing
- [ ] Lawful basis identified for each processing activity
- [ ] Consent mechanisms implemented where required
- [ ] Consent withdrawal easy and accessible
- [ ] Processing records maintained (Article 30)

### Transparency
- [ ] Privacy policy clear and accessible
- [ ] Data collection purposes explained
- [ ] Third-party data sharing disclosed
- [ ] Retention periods specified

### Data Subject Rights
- [ ] Access request process documented
- [ ] Data portability export functionality
- [ ] Deletion request mechanism
- [ ] Objection handling process
- [ ] Response within 30 days guaranteed

### Security
- [ ] Personal data encrypted at rest
- [ ] Personal data encrypted in transit
- [ ] Access controls implemented
- [ ] Regular security audits conducted
- [ ] Breach notification procedures (72 hours)

### Accountability
- [ ] Data Protection Officer appointed (if required)
- [ ] Processing records maintained
- [ ] DPIAs conducted for high-risk processing
- [ ] Data processing agreements with processors
- [ ] Regular compliance audits

## Penalties for Non-Compliance

GDPR violations can result in:
- Up to €20 million or 4% of global annual revenue (whichever is higher)
- Reputational damage
- Loss of customer trust
- Legal action from data subjects

## Best Practices

1. **Privacy by Design**
   - Consider privacy from project inception
   - Minimize data collection
   - Provide privacy-friendly defaults

2. **Regular Audits**
   - Quarterly compliance reviews
   - Annual DPIA updates
   - Continuous monitoring

3. **Documentation**
   - Maintain comprehensive records
   - Document all processing activities
   - Keep consent records

4. **Training**
   - Regular GDPR training for all staff
   - Specialized training for developers
   - DPO training and certification

5. **Incident Response**
   - 72-hour breach notification procedures
   - Incident response team
   - Regular drills and testing

## Requirements

- Access to application code and databases
- Privacy policy and legal documentation
- Data processing agreements
- User consent records

## License

MIT License - See LICENSE file for details
