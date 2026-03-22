---
name: granola-prod-checklist
description: |
  Production readiness checklist for Granola team and enterprise deployment.
  Use when rolling out Granola to a team, planning enterprise deployment,
  or verifying all configuration is production-ready.
  Trigger: "granola production", "granola rollout", "granola deployment",
  "granola checklist", "granola go-live".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, deployment, enterprise]

---
# Granola Production Checklist

## Overview
Comprehensive pre-launch checklist for deploying Granola to a team or organization. Covers plan selection, security hardening, integration setup, pilot program, and go-live execution.

## Prerequisites
- Budget approved for Granola licenses
- Team size and meeting volume estimated
- IT/security review completed or in progress
- Admin access to Granola workspace

## Instructions

### Phase 1 — Plan & License

- [ ] **Select plan:** Business ($14/user/mo) or Enterprise ($35+/user/mo)
- [ ] **Seat count:** Purchase seats for all target users
- [ ] **Billing:** Annual billing for 10-15% savings, or monthly for flexibility
- [ ] **Contract:** Enterprise agreement signed (if applicable)
- [ ] **SOC 2 report:** Requested and reviewed (available on request from Granola)

### Phase 2 — Security Configuration

- [ ] **SSO enabled:** Okta, Azure AD, or Google Workspace (Enterprise)
- [ ] **SCIM provisioning:** Auto-provision users from IdP groups (Enterprise)
- [ ] **AI training opt-out:** Enabled org-wide (Enterprise: enforced by default)
- [ ] **Sharing defaults:** Set to Private, external sharing disabled or admin-approved
- [ ] **Data retention:** Configured per data type (notes: 1-2yr, transcripts: 90d)
- [ ] **DPA signed:** Data Processing Agreement for GDPR compliance
- [ ] **Session timeout:** Configured for security policy (Enterprise)

### Phase 3 — Integration Setup

| Integration | Configuration | Verification |
|-------------|--------------|--------------|
| Google Calendar or Outlook | Settings > Calendar > Connect | Test meeting shows in Granola |
| Slack | Settings > Integrations > Slack | Post test note to channel |
| Notion | Settings > Integrations > Notion | Share test note creates DB entry |
| HubSpot/Attio/Affinity | Settings > Integrations > CRM | Match test note to CRM contact |
| Zapier (optional) | Connect Granola app in Zapier | Test Zap fires on note creation |
| MCP (optional) | Configure in AI tool settings | Test meeting query in Claude/Cursor |

### Phase 4 — Workspace Configuration

- [ ] **Workspaces created:** Per department/team (Engineering, Sales, Leadership, etc.)
- [ ] **Folders created:** Per meeting type within each workspace
- [ ] **Templates configured:** Default templates per folder/meeting type
- [ ] **Sharing rules:** Per-folder auto-post to Slack channels
- [ ] **User roles assigned:** Admin, Member, Viewer per workspace
- [ ] **Custom recipes created:** Team-specific Granola Chat recipes

### Phase 5 — Pilot Program (2 Weeks)

1. **Select 5-10 pilot users** across different meeting types
2. **Define success metrics:**

| Metric | Target | How to Measure |
|--------|--------|----------------|
| User activation | 100% of pilot | All users capture at least one meeting |
| Meeting capture rate | >70% | Meetings captured / total meetings |
| Note quality rating | 4+/5 | Pilot user survey |
| Support tickets | <2 per user | Track via Slack/email |
| Time saved per meeting | >10 min | Before/after survey |

3. **Collect daily feedback** for the first 3 days, then weekly
4. **Fix issues immediately** — common pilot issues:
   - Audio permission not granted (macOS Screen & System Audio)
   - Calendar not connected to the right account
   - Templates not matching meeting types
   - Users forgetting to type notes (Enhance is better with typed context)

### Phase 6 — Go-Live

**Launch day checklist:**
- [ ] Welcome email sent with setup instructions and support contact
- [ ] Slack channel created: #granola-support
- [ ] Quick-start guide shared (link to `granola-install-auth` + `granola-hello-world`)
- [ ] Calendar consent notice template distributed
- [ ] User access enabled (SSO/SCIM auto-provision or manual invite)
- [ ] IT support team briefed on common troubleshooting steps

**First week monitoring:**
- [ ] Daily adoption check: % of users who captured a meeting
- [ ] Support ticket volume and resolution time
- [ ] Integration health: Slack/Notion/CRM syncs working
- [ ] User feedback collection via survey or Slack poll

### Phase 7 — Post-Launch (Weeks 2-4)

- [ ] Address low-adoption users with 1:1 support
- [ ] Publish internal "tips & tricks" based on power user patterns
- [ ] Review and refine templates based on team feedback
- [ ] Set up recurring reporting (weekly adoption metrics to leadership)
- [ ] Schedule first quarterly access review

## Output
- All security controls configured and verified
- Integrations connected, tested, and documented
- Pilot completed with metrics meeting targets
- Full team onboarded and actively capturing meetings
- Support processes established with documented escalation path

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Low adoption (<50%) | Insufficient training | Run live demo, share video walkthrough |
| SSO login failure | SAML metadata mismatch | Verify ACS URL, Entity ID, and certificate with IdP |
| Calendar not syncing org-wide | OAuth app not approved | IT admin must approve Granola's OAuth in Google/Microsoft admin |
| Audio issues across team | macOS permission prompt dismissed | Send instructions to re-grant Screen & System Audio permission |

## Resources
- [Setup Guide](https://docs.granola.ai/help-center/getting-started/setting-up-granola-for-the-first-time)
- [Enterprise API](https://docs.granola.ai/help-center/sharing/integrations/enterprise-api)
- [Security Standards](https://docs.granola.ai/help-center/consent-security-privacy/our-security-standards)
- [Granola Updates](https://www.granola.ai/updates)

## Next Steps
Proceed to `granola-upgrade-migration` for version upgrade and plan migration guidance.
