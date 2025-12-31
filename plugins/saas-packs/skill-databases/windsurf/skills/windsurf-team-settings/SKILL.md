---
name: windsurf-team-settings
description: |
  Manage team-wide Windsurf settings and AI policies. Activate when users mention
  "team settings", "organization config", "team policies", "shared settings",
  or "team standardization". Handles team configuration management.
allowed-tools: Read,Write,Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Team Settings

Manage team-wide settings and AI policies for consistent developer experience.

## Directory Structure

```
organization-config/
    .windsurf-team/
        settings/
            global-settings.json         # Organization-wide defaults
                # Editor preferences
                # AI behavior settings
                # Feature toggles

            team-overrides/
                engineering.json         # Engineering team settings
                    # Development preferences
                    # Tool integrations
                    # Language configurations

                security.json            # Security team settings
                    # Restricted features
                    # Audit requirements
                    # Compliance settings

        policies/
            ai-usage-policy.json         # AI feature policies
                # Allowed AI features
                # Data handling rules
                # Usage restrictions

            code-sharing-policy.json     # Code sharing rules
                # Snippet sharing permissions
                # External tool integrations
                # Repository access

            tool-approval.json           # Approved tool list
                # Approved extensions
                # Blocked extensions
                # Pending review

        templates/
            new-member-settings.json     # Onboarding defaults
                # Initial configuration
                # Required extensions
                # Training resources

            project-settings.json        # Project template
                # Standard configurations
                # Recommended structure
                # Quality requirements
```

## Team Features

### Centralized Management
- Organization-wide defaults
- Team-specific overrides
- Role-based settings
- Version-controlled configuration

### Policy Enforcement
- AI usage policies
- Data handling rules
- Tool approval workflows
- Compliance requirements

## Configuration Steps

1. **Define Organization Defaults**
   - Set baseline configuration
   - Enable required features
   - Disable restricted features

2. **Create Team Overrides**
   - Customize per team needs
   - Document exceptions
   - Set approval workflows

3. **Deploy and Monitor**
   - Push settings to all members
   - Track compliance
   - Gather feedback

## Success Criteria

- Settings synchronized within 5 minutes
- Consistent experience across team
- 40% reduction in support tickets
