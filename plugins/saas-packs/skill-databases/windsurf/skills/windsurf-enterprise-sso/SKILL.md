---
name: windsurf-enterprise-sso
description: |
  Configure enterprise SSO integration for Windsurf. Activate when users mention
  "sso configuration", "single sign-on", "enterprise authentication", "saml setup",
  or "identity provider". Handles enterprise identity integration.
allowed-tools: Read,Write,Edit,Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Enterprise SSO

Configure enterprise SSO integration for secure team authentication.

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

## SSO Features

### Supported Providers
- SAML 2.0 identity providers
- OIDC/OAuth 2.0 providers
- Okta, Azure AD, Google Workspace
- Custom enterprise IdPs

### Security Features
- Multi-factor authentication support
- Session management
- Audit logging
- Just-in-time provisioning

## Configuration Steps

1. **Prepare Identity Provider**
   - Create application registration
   - Configure redirect URIs
   - Set up attribute mappings

2. **Configure Windsurf SSO**
   - Enter IdP metadata
   - Map user attributes
   - Configure group sync

3. **Test and Enable**
   - Test with pilot users
   - Verify MFA flow
   - Enable for organization

## Success Criteria

- SSO authentication functional
- MFA enabled and working
- Audit logging active
- Compliance requirements met
