# Granola Security Controls Reference

## Data Flow & Security Architecture

```
Audio Capture (Local Device)
        ↓
Encrypted Transmission (TLS 1.3)
        ↓
Processing Server (Transient)
        ↓
Encrypted Storage (AES-256)
        ↓
Access via App (Auth Required)
```

## Key Security Features

| Feature | Status | Details |
|---------|--------|---------|
| Encryption at rest | Yes | AES-256 |
| Encryption in transit | Yes | TLS 1.3 |
| SOC 2 Type II | Yes | Certified |
| GDPR compliant | Yes | EU data options |
| Audio retention | Configurable | Delete after processing |

## Sharing Permissions Matrix

| Share Level | Access | Use Case |
|-------------|--------|----------|
| Private | Owner only | Sensitive meetings |
| Team | Workspace members | Internal meetings |
| Link (View) | Anyone with link | Read-only sharing |
| Link (Edit) | Anyone with link | Collaborative notes |

## Sensitive Meeting Protocol

### Pre-Meeting

- [ ] Disable auto-recording
- [ ] Confirm attendee list
- [ ] Review sharing settings
- [ ] Check for screen share visibility
- [ ] Consider using "Off the Record" mode

### During Meeting

- Announce recording to all participants
- Pause recording for sensitive discussions
- Avoid displaying sensitive documents on screen

### Post-Meeting

- Review notes before sharing
- Redact sensitive information
- Use private sharing link
- Set expiration on shared links

## Data Retention Settings

```
Settings > Privacy > Data Retention

Options:
- Keep forever (default)
- Delete audio after 30 days
- Delete audio after 7 days
- Delete audio immediately after processing

Recommendation: Delete audio after processing
(Notes are retained, raw audio is deleted)
```

## Data Export Options

Formats: Markdown (.md), PDF, Word (.docx), JSON (full data)

Export includes: Meeting notes, transcripts, action items, metadata

Does NOT include: Raw audio files, AI model data

## Compliance Reference

### GDPR (EU Users)

| Requirement | Granola Support |
|-------------|-----------------|
| Right to access | Data export available |
| Right to delete | Full deletion option |
| Data portability | JSON export |
| Consent | Recording notifications |
| DPA available | Yes (Business plans) |

### HIPAA (Healthcare)

- Standard plans: Not HIPAA compliant
- Enterprise: BAA available on request
- Recommendation: Use only for non-PHI meetings

### SOC 2 Type II

- Granola is SOC 2 Type II certified
- Audit reports available for Enterprise customers
- Covers security, availability, confidentiality

## Team Security Controls (Business Plans)

- [ ] Enforce SSO login
- [ ] Set password policies
- [ ] Manage user permissions
- [ ] View audit logs
- [ ] Control external sharing
- [ ] Enforce 2FA
- [ ] IP allowlisting

## Audit Logging Events

- User login/logout
- Meeting recorded
- Notes shared
- Data exported
- Settings changed
- User added/removed

## Security Incident Response

### If Account Compromised

1. Immediately change password
2. Revoke all sessions (Settings > Security > Sign out everywhere)
3. Review recent activity
4. Check shared notes
5. Enable 2FA if not already
6. Contact support if data exposed

### Reporting Security Issues

- Email: security@granola.ai
- Include: Detailed description, steps to reproduce
- Response: Within 24 hours
