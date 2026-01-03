---
name: windsurf-code-privacy
description: |
  Configure code privacy and data retention policies. Activate when users mention
  "code privacy", "data retention", "privacy settings", "data governance",
  or "gdpr compliance". Handles privacy and data protection configuration.
allowed-tools: Read,Write,Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Code Privacy

Configure code privacy and data retention policies for regulatory compliance.

## Directory Structure

```
organization-config/
    .windsurf-enterprise/
        privacy/
            config/
                privacy-settings.json        # Global privacy configuration
                    # Data transmission rules
                    # Local processing preferences
                    # Consent requirements

                retention-policy.json        # Data retention rules
                    # Retention periods by data type
                    # Deletion schedules
                    # Archive procedures

                consent-settings.json        # Consent management
                    # Required consents
                    # Opt-out options
                    # Preference storage

            exclusions/
                sensitive-patterns.json      # Sensitive content patterns
                    # Secret detection patterns
                    # PII patterns
                    # Proprietary code markers

                excluded-paths.json          # Excluded directories
                    # Paths never sent to AI
                    # Local-only processing
                    # Offline mode paths

            regional/
                eu-gdpr.json                 # GDPR compliance settings
                    # Data residency requirements
                    # Right to deletion
                    # Processing agreements

                us-ccpa.json                 # CCPA compliance settings
                    # Consumer rights
                    # Opt-out mechanisms
                    # Disclosure requirements

            documentation/
                privacy-policy.md            # User-facing policy
                    # Data collection practices
                    # Usage purposes
                    # User rights

                dpa-template.md              # Data processing agreement
                    # Legal requirements
                    # Subprocessor lists
                    # Security measures
```

## Privacy Features

### Data Protection
- End-to-end encryption
- Local processing options
- Selective code exclusion
- Audit trail maintenance

### Compliance
- GDPR compliance tools
- CCPA support
- Data residency options
- Right to deletion

## Configuration Steps

1. **Configure Data Handling**
   - Set transmission policies
   - Define retention periods
   - Configure encryption

2. **Set Up Exclusions**
   - Define sensitive patterns
   - Exclude specific paths
   - Mark proprietary code

3. **Enable Compliance**
   - Configure regional settings
   - Set up consent management
   - Document policies

## Success Criteria

- Code never transmitted without consent
- Configurable retention active
- GDPR/CCPA requirements met
