---
name: granola-upgrade-migration
description: |
  Upgrade Granola versions and migrate between plans.
  Use when upgrading app versions, changing subscription plans,
  or migrating data between Granola accounts.
  Trigger with phrases like "upgrade granola", "granola migration",
  "granola new version", "change granola plan", "granola update".
allowed-tools: Read, Write, Edit, Bash(brew:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Guide for upgrading Granola versions and migrating between subscription plans.

## App Version Upgrades

### Check Current Version
```bash
# macOS - Check installed version
defaults read /Applications/Granola.app/Contents/Info.plist CFBundleShortVersionString

# Or in Granola app:
# Menu > About Granola
```

### Auto-Update Settings
```
Granola > Preferences > General
- Check for updates automatically: Enabled (recommended)
- Download updates in background: Enabled
- Notify before installing: Your preference
```

### Manual Update Process
```bash
# macOS via Homebrew
brew update
brew upgrade --cask granola

# Or download directly
open https://granola.ai/download

# Verify update
defaults read /Applications/Granola.app/Contents/Info.plist CFBundleShortVersionString
```

### Update Troubleshooting
```markdown
## Common Update Issues

Issue: Update fails to install
Solution:
1. Quit Granola completely
2. Delete ~/Library/Caches/Granola
3. Redownload installer
4. Run installer as admin

Issue: App crashes after update
Solution:
1. Clear preferences (backup first)
2. Re-authenticate
3. Contact support if persists
```

## Plan Migrations

### Upgrade Path
```
Free → Pro → Business → Enterprise

Upgrade includes:
- Immediate access to new features
- No data loss
- Prorated billing
- Increased limits take effect immediately
```

### Upgrading Plans

#### Free to Pro
```markdown
## Upgrade Steps
1. Settings > Account > Subscription
2. Click "Upgrade to Pro"
3. Enter payment information
4. Confirm subscription
5. Immediate access to Pro features

Benefits Gained:
- Unlimited meetings
- Longer recording duration
- All integrations
- Custom templates
- Priority processing
```

#### Pro to Business
```markdown
## Upgrade Steps
1. Settings > Account > Subscription
2. Click "Upgrade to Business"
3. Set initial team size
4. Complete payment
5. Configure workspace settings

Benefits Gained:
- Team workspaces
- Admin controls
- SSO support
- Audit logs
- Priority support
```

#### Business to Enterprise
```markdown
## Enterprise Migration
1. Contact sales@granola.ai
2. Discuss requirements
3. Custom agreement
4. Dedicated onboarding
5. Migration support

Enterprise Features:
- Custom limits
- Dedicated support
- SLA guarantees
- On-premise option
- Custom integrations
```

### Downgrade Considerations
```markdown
## Downgrading Plans

Before downgrading:
- [ ] Export data exceeding new limits
- [ ] Document current integrations
- [ ] Notify team members
- [ ] Review feature dependencies

Data Handling:
- Notes preserved (read-only if over limit)
- Integrations disconnected
- Team access removed
- Templates kept but locked

Timeline:
- Downgrade at next billing cycle
- Access maintained until then
- No prorated refunds typically
```

## Data Migration

### Export All Data
```markdown
## Complete Data Export

1. Settings > Data > Export
2. Select "All Data"
3. Choose format:
   - Markdown (readable)
   - JSON (complete)
   - PDF (archival)
4. Wait for export generation
5. Download zip file
6. Verify contents
```

### Import to New Account
```markdown
## Limitations
- No direct import between accounts
- Manual recreation of templates required
- Integrations must be reconfigured

Workaround:
1. Export as Markdown
2. Import to Notion/other tool
3. Reference in new account
```

### Workspace Migration
```markdown
## Move Between Workspaces

Scenario: Moving from personal to team workspace

Steps:
1. Export notes from personal account
2. Join team workspace
3. Share/recreate important notes
4. Transfer integrations manually
5. Update calendar connections
```

## Version Compatibility

### Breaking Changes Awareness
```markdown
## Before Major Updates

Check:
- Release notes at granola.ai/updates
- Breaking changes section
- Integration compatibility
- Minimum system requirements

Prepare:
- Backup current data
- Document custom settings
- Note integration configs
- Plan rollback if needed
```

### Rollback Procedure
```markdown
## If Update Causes Issues

macOS:
1. Download previous version from granola.ai/downloads/archive
2. Quit Granola
3. Move current app to trash
4. Install previous version
5. Report issue to support

Note: Account data is cloud-synced,
app version doesn't affect stored data
```

## Enterprise Migration Checklist

### From Other Tools to Granola
```markdown
## Migration from Otter.ai/Fireflies/Other

Phase 1: Data Export (Week 1)
- [ ] Export all meeting notes
- [ ] Export transcripts
- [ ] Download audio (if needed)
- [ ] Document integrations used

Phase 2: Granola Setup (Week 1-2)
- [ ] Configure Granola workspace
- [ ] Set up integrations
- [ ] Create templates
- [ ] Train team

Phase 3: Parallel Running (Week 2-4)
- [ ] Run both tools
- [ ] Compare quality
- [ ] Identify gaps
- [ ] Adjust configuration

Phase 4: Cutover (Week 5)
- [ ] Disable old tool
- [ ] Full switch to Granola
- [ ] Monitor closely
- [ ] Support team actively
```

## Resources
- [Granola Updates](https://granola.ai/updates)
- [Pricing & Plans](https://granola.ai/pricing)
- [Migration Support](https://granola.ai/help/migration)

## Next Steps
Proceed to `granola-ci-integration` for CI/CD workflow integration.

## Prerequisites

- Access to the migration environment or API
- Required CLI tools installed and authenticated
- Familiarity with migration concepts and terminology

## Instructions

1. Assess the current state of the migration configuration
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
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with migration |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply granola upgrade migration to a standard project setup with default configuration options.

**Advanced scenario**: Customize granola upgrade migration for production environments with multiple constraints and team-specific requirements.