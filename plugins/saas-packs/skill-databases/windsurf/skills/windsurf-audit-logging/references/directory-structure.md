# Directory Structure

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
