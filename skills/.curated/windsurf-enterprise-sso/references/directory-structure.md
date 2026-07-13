# Directory Structure

## Directory Structure

```
organization-config/
    .windsurf-enterprise/
        sso/
            config.json                  # SSO configuration
                # Identity provider settings
                # SAML/OIDC configuration
                # Attribute mappings

            providers/
                okta.json                # Okta configuration
                    # Application ID
                    # Domain settings
                    # Group mappings

                azure-ad.json            # Azure AD configuration
                    # Tenant ID
                    # Client configuration
                    # Role assignments

                google-workspace.json    # Google Workspace config
                    # Domain verification
                    # User provisioning
                    # Group sync settings

            certificates/
                README.md                # Certificate management guide
                    # Certificate requirements
                    # Rotation procedures
                    # Backup protocols

        policies/
            access-policy.json           # Access control rules
                # Role definitions
                # Permission sets
                # Group mappings

            session-policy.json          # Session management
                # Timeout settings
                # Concurrent session limits
                # Re-authentication triggers

        audit/
            auth-logs/
                README.md                # Audit log documentation
                    # Log format
                    # Retention policy
                    # Export procedures
```
