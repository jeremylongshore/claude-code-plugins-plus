# Compliance By Framework

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
