---
name: finta-deploy-integration
description: |
  Deploy Finta integrations and reporting dashboards.
  Trigger with phrases like "deploy finta", "finta dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, fundraising-crm, investor-management, finta]
compatible-with: claude-code
---

# Finta Deploy Integration

## Google Sheets Dashboard

Sync Finta data to Google Sheets for live dashboards:

1. Export CSV from Finta weekly
2. Upload to Google Sheets (or use Zapier auto-sync)
3. Build charts: pipeline funnel, stage distribution, timeline

## Slack Notifications

Use Zapier to post pipeline updates to Slack:
- New investor added -> #fundraising channel
- Stage change -> thread update
- Deal closed -> celebration notification

## Resources

- [Finta Website](https://www.trustfinta.com)

## Next Steps

For event automation, see `finta-webhooks-events`.
