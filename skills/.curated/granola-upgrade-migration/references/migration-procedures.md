# Granola Migration Procedures

## App Version Update Methods

### macOS via Homebrew

```bash
brew update
brew upgrade --cask granola

# Verify update
defaults read /Applications/Granola.app/Contents/Info.plist CFBundleShortVersionString
```

### Update Troubleshooting

**Issue: Update fails to install**

1. Quit Granola completely
2. Delete ~/Library/Caches/Granola
3. Redownload installer from granola.ai/download
4. Run installer as admin

**Issue: App crashes after update**

1. Clear preferences (backup first)
2. Re-authenticate
3. Contact support if issue persists

## Plan Upgrade Details

### Free to Pro

1. Settings > Account > Subscription
2. Click "Upgrade to Pro"
3. Enter payment information and confirm
4. Immediate access to: unlimited meetings, longer recording, all integrations, custom templates

### Pro to Business

1. Settings > Account > Subscription
2. Click "Upgrade to Business"
3. Set initial team size and complete payment
4. Configure workspace settings
5. Gains: team workspaces, admin controls, SSO, audit logs, priority support

### Business to Enterprise

1. Contact sales@granola.ai
2. Discuss custom requirements
3. Custom agreement and dedicated onboarding
4. Enterprise features: custom limits, SLA guarantees, on-premise option

## Downgrade Considerations

Before downgrading:

- [ ] Export data exceeding new plan limits
- [ ] Document current integrations
- [ ] Notify team members
- [ ] Review feature dependencies

Data handling on downgrade:

- Notes preserved (read-only if over limit)
- Integrations disconnected
- Team access removed
- Templates kept but locked
- Downgrade takes effect at next billing cycle

## Data Export and Import

### Complete Data Export

1. Settings > Data > Export
2. Select "All Data"
3. Choose format: Markdown (readable), JSON (complete), or PDF (archival)
4. Wait for export generation
5. Download zip file and verify contents

### Import Limitations

- No direct import between accounts
- Manual recreation of templates required
- Integrations must be reconfigured
- Workaround: export as Markdown, import to Notion, reference in new account

### Workspace Migration

1. Export notes from personal account
2. Join team workspace
3. Share or recreate important notes
4. Transfer integrations manually
5. Update calendar connections

## Version Compatibility

### Before Major Updates

Check: release notes at granola.ai/updates, breaking changes section, integration compatibility, minimum system requirements

Prepare: backup current data, document custom settings, note integration configs, plan rollback if needed

### Rollback Procedure (macOS)

1. Download previous version from granola.ai/downloads/archive
2. Quit Granola
3. Move current app to trash
4. Install previous version
5. Report issue to support (account data is cloud-synced, app version does not affect stored data)

## Enterprise Migration from Other Tools

### From Otter.ai/Fireflies/Other

**Phase 1 (Week 1):** Export all meeting notes, transcripts, and audio from existing tool. Document integrations used.

**Phase 2 (Week 1-2):** Configure Granola workspace, set up integrations, create templates, train team.

**Phase 3 (Week 2-4):** Run both tools in parallel. Compare quality, identify gaps, adjust configuration.

**Phase 4 (Week 5):** Disable old tool, full switch to Granola, monitor closely, support team actively.
