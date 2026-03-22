---
name: granola-upgrade-migration
description: |
  Upgrade Granola app versions and migrate between subscription plans.
  Use when upgrading the desktop app, changing from free to paid plans,
  downgrading with data preservation, or resolving update issues.
  Trigger: "upgrade granola", "granola update", "change granola plan",
  "granola new version", "granola downgrade".
allowed-tools: Read, Write, Edit, Bash(brew:*), Bash(defaults:*), Bash(rm:*), Bash(open:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, migration, upgrade]

---
# Granola Upgrade & Migration

## Overview
Manage Granola desktop app updates and subscription plan changes. Granola auto-updates by default, but manual intervention may be needed for major versions or plan migrations that affect feature access.

## Prerequisites
- Current Granola version info (Granola menu > About, or check via CLI)
- Admin access for organization-level plan changes
- Data backup awareness before downgrading

## Instructions

### Step 1 — Check Current Version

```bash
# macOS — read version from app bundle
defaults read /Applications/Granola.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null || echo "Check Granola > About Granola"
```

Check for available updates: Granola menu bar icon > Check for Updates, or visit [granola.ai/updates](https://www.granola.ai/updates) for the changelog.

### Step 2 — Update the Desktop App

**Auto-update (recommended):**
Granola checks for updates automatically and downloads in the background. Enable at:
```
Granola > Preferences > General > Check for updates automatically: On
```

**Manual update via Homebrew (macOS):**
```bash
brew update && brew upgrade --cask granola
```

**Manual download:**
Download latest from [granola.ai/download](https://www.granola.ai/download). Close Granola, install over the existing version. Settings and data are preserved.

### Step 3 — Handle Update Issues

If Granola crashes or behaves incorrectly after updating:

```bash
# Clear caches (preserves your data and authentication)
rm -rf ~/Library/Caches/Granola

# If that doesn't help, reset preferences (you'll need to re-authenticate)
defaults delete ai.granola.app 2>/dev/null

# Nuclear option — full reinstall
brew uninstall --cask granola 2>/dev/null
rm -rf ~/Library/Caches/Granola
rm -rf ~/Library/Preferences/ai.granola.app.plist
brew install --cask granola
```

Your meeting data is stored server-side and in the local cache (`~/Library/Application Support/Granola/cache-v3.json`). Reinstalling does not delete your notes.

### Step 4 — Upgrade Subscription Plan

```
Settings (avatar bottom-left) > Account > Subscription > Upgrade

Upgrade paths:
  Basic (Free) → Business ($14/user/mo): Immediate, prorated
  Business → Enterprise ($35+/user/mo): Contact sales

What changes on upgrade:
  Basic → Business:
    + Unlimited meetings (was 25 lifetime)
    + Unlimited history (was 14 days)
    + Slack, Notion, CRM integrations
    + Zapier automation
    + MCP (AI agent integration)
    + Team shared folders
    + Custom templates
    + Public API access

  Business → Enterprise:
    + SSO (Okta, Azure AD, Google Workspace)
    + SCIM auto-provisioning
    + Enforced AI training opt-out
    + Usage analytics dashboard
    + Full Enterprise API
    + Custom data retention policies
    + Dedicated account manager
```

### Step 5 — Downgrade with Data Preservation

Before downgrading, understand what you lose:

| Downgrading From | Losing | Action Before Downgrade |
|-----------------|--------|----------------------|
| Business → Basic | Integrations disconnect, history limited to 14 days | Export all notes, save integration configs |
| Enterprise → Business | SSO, SCIM, custom retention, analytics | Reconfigure authentication, manual user provisioning |

**Pre-downgrade checklist:**
1. Notify team members of the change
2. Export critical notes (there is no bulk export — share important notes to Notion or copy individually)
3. Document active integration configurations
4. Save any custom templates and recipes
5. Verify API consumers are prepared for access loss

**Important:** Downgrading does not delete your data. Notes remain accessible within the new plan's limits (e.g., Basic only shows last 14 days, but data is preserved if you re-upgrade).

### Step 6 — Manage Team Seats

```
Settings > Team > Manage Seats

Add seats:
  - Invite by email or enable SSO auto-provisioning
  - New seats are prorated for the billing period

Remove seats:
  - Deactivate user in Settings > Team
  - User loses access but their shared notes remain
  - Seat count reduces on next billing cycle

Reassign seats:
  - Deactivate departing user
  - Invite replacement user
  - No additional charge (same seat count)
```

## Plan Migration Matrix

| From | To | Billing Impact | Data Impact | Action Required |
|------|----|---------------|-------------|-----------------|
| Basic | Business | $14/user/mo starts immediately | Full history restored | Connect integrations |
| Basic | Enterprise | Contact sales for pricing | Full history restored | SSO/SCIM setup |
| Business | Enterprise | Price difference, prorated | No data change | Configure SSO/SCIM |
| Enterprise | Business | Price reduction, immediate | Retain data, lose SSO/SCIM | Reconfigure auth |
| Business | Basic | Free, immediate | History limited to 14 days | Export critical data |
| Any | Annual billing | 10-15% savings | No data change | Confirm in Billing |

## Output
- Granola updated to latest version
- Subscription plan changed with feature access verified
- Team seats managed (added/removed/reassigned)
- Data preserved through any plan change

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Update fails to install | Corrupted download or cache | Clear caches, reinstall: `brew reinstall --cask granola` |
| App crashes after update | Stale preferences | Delete prefs: `defaults delete ai.granola.app` |
| Payment fails on upgrade | Expired card | Update payment method in Settings > Billing |
| Features missing after upgrade | Cache not refreshed | Log out and log back in to refresh entitlements |
| SSO stops working after downgrade | Enterprise feature removed | Switch to Google/Microsoft social login |

## Resources
- [Granola Updates & Changelog](https://www.granola.ai/updates)
- [Pricing Plans](https://www.granola.ai/pricing)
- [Pricing FAQ](https://www.granola.ai/docs/docs/FAQs/granola-plans-faq)
- [Download](https://www.granola.ai/download)

## Next Steps
Proceed to `granola-ci-integration` for automated meeting-to-dev-tool workflows.
