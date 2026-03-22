---
name: finta-install-auth
description: |
  Set up Finta fundraising CRM account and configure integrations.
  Use when onboarding to Finta, connecting email/calendar,
  or configuring investor pipeline automation.
  Trigger with phrases like "install finta", "setup finta",
  "finta onboarding", "configure finta crm".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, fundraising-crm, investor-management, finta]
compatible-with: claude-code
---

# Finta Install & Auth

## Overview

Set up Finta fundraising CRM at trustfinta.com. Finta is a UI-first platform for managing fundraising pipelines, investor relationships, and deal rooms. Integration is via email/calendar sync and the Finta web app -- there is no public REST API.

## Prerequisites

- Finta account at https://www.trustfinta.com
- Gmail or Outlook email for sync
- Google Calendar or Outlook Calendar

## Instructions

### Step 1: Create Account

1. Sign up at https://www.trustfinta.com
2. Complete onboarding wizard with company details
3. Select your fundraising stage (Pre-seed, Seed, Series A, etc.)

### Step 2: Connect Email

Finta syncs with Gmail and Outlook to automatically track investor communications:

1. Go to **Settings** > **Integrations**
2. Click **Connect Gmail** or **Connect Outlook**
3. Grant read access for email tracking
4. Finta will auto-detect investor conversations and update pipeline stages

### Step 3: Connect Calendar

1. Go to **Settings** > **Integrations**
2. Click **Connect Google Calendar** or **Connect Outlook Calendar**
3. Meetings with investors will auto-log to the pipeline

### Step 4: Import Existing Investors

- **CSV Import**: Upload a spreadsheet with investor name, firm, email, stage
- **Manual Entry**: Add investors one by one in the Pipeline view
- **Aurora AI**: Let Finta's AI prospect matching find relevant investors

### Step 5: Configure Pipeline Stages

Default stages (customizable):
1. Researching
2. Reaching Out
3. Intro Meeting
4. Follow-up
5. Due Diligence
6. Term Sheet
7. Closed

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Email sync not working | OAuth expired | Reconnect in Settings > Integrations |
| Calendar events missing | Wrong calendar selected | Select correct calendar |
| CSV import fails | Wrong format | Use Finta template CSV |
| Duplicate investors | Re-import | Merge duplicates in UI |

## Resources

- [Finta Website](https://www.trustfinta.com)
- [Finta Blog](https://www.trustfinta.com/blog)
- [Finta for Serial Entrepreneurs](https://www.trustfinta.com/blog/finta-for-serial-entrepreneurs-fundraising)

## Next Steps

Proceed to `finta-hello-world` to set up your first fundraise pipeline.
