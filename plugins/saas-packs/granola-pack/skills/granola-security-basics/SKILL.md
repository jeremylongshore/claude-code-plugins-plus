---
name: granola-security-basics
description: |
  Security best practices for Granola meeting data.
  Use when implementing security controls, reviewing data handling,
  or ensuring compliance with security policies.
  Trigger with phrases like "granola security", "granola privacy",
  "granola data protection", "secure granola", "granola compliance".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Security Basics

## Overview
Implement security best practices for protecting meeting data in Granola.

## Data Flow & Security

### How Granola Handles Data
```
Audio Capture (Local Device)
        ↓
Encrypted Transmission (TLS 1.3)
        ↓
Processing Server (Transient)
        ↓
Encrypted Storage (AES-256)  # 256 bytes
        ↓
Access via App (Auth Required)
```

### Key Security Features
| Feature | Status | Details |
|---------|--------|---------|
| Encryption at rest | Yes | AES-256 |
| Encryption in transit | Yes | TLS 1.3 |
| SOC 2 Type II | Yes | Certified |
| GDPR compliant | Yes | EU data options |
| Audio retention | Configurable | Delete after processing |

## Access Control Best Practices

### Personal Account Security
```markdown
## Checklist
- [ ] Use strong unique password
- [ ] Enable 2FA (two-factor authentication)
- [ ] Review connected apps regularly
- [ ] Log out from shared devices
- [ ] Use SSO if available (Business/Enterprise)
```

### Sharing Permissions
| Share Level | Access | Use Case |
|-------------|--------|----------|
| Private | Owner only | Sensitive meetings |
| Team | Workspace members | Internal meetings |
| Link (View) | Anyone with link | Read-only sharing |
| Link (Edit) | Anyone with link | Collaborative notes |

### Configure Sharing Defaults
```
Settings > Privacy > Default Sharing
- New meetings: Private (recommended)
- Auto-share with attendees: Off (for sensitive meetings)
- External sharing: Disabled (for compliance)
```

## Sensitive Meeting Handling

### Pre-Meeting
```markdown
## Sensitive Meeting Checklist
- [ ] Disable auto-recording
- [ ] Confirm attendee list
- [ ] Review sharing settings
- [ ] Check for screen share visibility
- [ ] Consider using "Off the Record" mode
```

### During Meeting
- Announce recording to all participants
- Pause recording for sensitive discussions
- Avoid displaying sensitive documents on screen

### Post-Meeting
- Review notes before sharing
- Redact sensitive information
- Use private sharing link
- Set expiration on shared links

## Data Retention & Deletion

### Retention Settings
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

### Manual Deletion
```markdown
## Delete Meeting Data

1. Open meeting in Granola
2. Click ... menu > Delete
3. Confirm deletion
4. Note: Deletion is permanent

## Bulk Deletion
1. Settings > Data
2. Export data (backup)
3. Select date range
4. Click "Delete meetings in range"
```

### Export & Portability
```markdown
## Data Export Options

Formats:
- Markdown (.md)
- PDF
- Word (.docx)
- JSON (full data)

Export includes:
- Meeting notes
- Transcripts
- Action items
- Metadata

Does NOT include:
- Raw audio files
- AI model data
```

## Compliance Considerations

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

## Team Security (Business Plans)

### Admin Controls
```markdown
## Available Controls
- [ ] Enforce SSO login
- [ ] Set password policies
- [ ] Manage user permissions
- [ ] View audit logs
- [ ] Control external sharing
- [ ] Enforce 2FA
- [ ] IP allowlisting
```

### Audit Logging
```
Available Events:
- User login/logout
- Meeting recorded
- Notes shared
- Data exported
- Settings changed
- User added/removed
```

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

## Resources
- [Granola Security](https://granola.ai/security)
- [Privacy Policy](https://granola.ai/privacy)
- [Trust Center](https://granola.ai/trust)

## Next Steps
Proceed to `granola-prod-checklist` for production deployment preparation.

## Prerequisites

- Access to the security environment or API
- Required CLI tools installed and authenticated
- Familiarity with security concepts and terminology

## Instructions

1. Assess the current state of the security configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with security |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply granola security basics to a standard project setup with default configuration options.

**Advanced scenario**: Customize granola security basics for production environments with multiple constraints and team-specific requirements.