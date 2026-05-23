# Directory Structure

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
