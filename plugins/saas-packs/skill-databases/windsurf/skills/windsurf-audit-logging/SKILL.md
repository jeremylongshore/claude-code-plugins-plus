---
name: windsurf-audit-logging
description: |
  Configure AI interaction audit logging for compliance. Activate when users mention
  "audit logging", "compliance logging", "ai interaction logs", "security audit",
  or "activity tracking". Handles compliance and audit configuration.
allowed-tools: Read,Write,Edit,Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Audit Logging

Configure comprehensive audit logging for compliance and security requirements.

## Directory Structure

```
organization-config/
    .windsurf-enterprise/
        audit/
            config/
                logging-config.json      # Audit logging settings
                    # Log levels and categories
                    # Retention periods
                    # Export destinations

                events-config.json       # Event tracking rules
                    # Tracked event types
                    # Sampling rates
                    # Priority levels

            schemas/
                ai-interaction.schema.json   # AI interaction log schema
                    # Request details
                    # Response metadata
                    # Token usage

                file-access.schema.json      # File access log schema
                    # File paths
                    # Action types
                    # User attribution

                auth-event.schema.json       # Authentication log schema
                    # Login events
                    # Session management
                    # Permission changes

            exports/
                siem-integration.json        # SIEM integration config
                    # Connector settings
                    # Field mappings
                    # Filter rules

                s3-export.json               # S3 export configuration
                    # Bucket settings
                    # Encryption options
                    # Lifecycle rules

            reports/
                templates/
                    daily-summary.json       # Daily activity report
                    weekly-audit.json        # Weekly audit report
                    compliance-report.json   # Compliance status report
```

## Audit Features

### Event Categories
- AI interactions (prompts, completions)
- File access and modifications
- Authentication events
- Configuration changes

### Compliance Support
- SOC 2 Type II
- ISO 27001
- HIPAA (with BAA)
- GDPR

## Configuration Steps

1. **Enable Audit Logging**
   - Configure event categories
   - Set retention periods
   - Define log destinations

2. **Set Up Integrations**
   - Connect to SIEM
   - Configure exports
   - Set up alerting

3. **Create Reports**
   - Schedule regular reports
   - Define compliance checks
   - Set up dashboards

## Success Criteria

- All AI interactions logged
- Timestamps and user attribution
- SOC 2 and ISO 27001 compliance satisfied
