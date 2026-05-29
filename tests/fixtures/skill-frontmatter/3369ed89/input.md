---
name: email
description: |
  Interactive email command center for Gmail. Send, search, organize inbox, create auto-filters. Use when user says "email", "inbox", "search sent", "search emails", "filter emails", "organize mail", "send email", "check inbox", "/email".
allowed-tools: 'Read,Write,Edit,Glob,Grep,Bash(node:*),Bash(python*:*),Bash(curl:*),Bash(export:*),Bash(cat:*),Task,AskUserQuestion'
model: opus
version: 3.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---

# Email Command Center

Interactive Gmail management: send, search, organize, filter.

## CRITICAL RULES

1. **NEVER auto-send emails** - Only create drafts or show preview
2. **Human must confirm send** - Use AskUserQuestion before ANY send action
3. **Show full preview first** - Display To, Subject, Body, Attachments before asking to send
4. **Default to draft** - If unclear, save as draft rather than send

## Default Settings

- **Owner Email:** jeremy@intentsolutions.io
- **Default Recipient:** jeremy@intentsolutions.io (when sending to "me" or "myself")

## Team Contacts

- **Pablo:** pablo@intentsolutions.io
- **Ope (Opeyemi Ariyo):** opeyemiariyo@intentsolutions.io
- **Boris Nelkin:** bnelkin@intentsolutions.io

## Overview

When invoked, present the main menu and guide the user through their chosen workflow. This skill operates as an **interactive wizard** - always confirm before taking action.

## Prerequisites

Environment variables (in `~/.env` or project `.env`):

```
GMAIL_USER_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
RESEND_API_KEY=re_xxxxx (optional, for sending)
```

Scripts location: `{baseDir}/scripts/`

## Instructions

### Step 1: Present Main Menu

When the skill is invoked, ALWAYS start by presenting this menu using AskUserQuestion:

```
EMAIL COMMAND CENTER
═══════════════════════════════════════════════════════════════════

What would you like to do?

1. 📤 Send Email - Compose and send with optional attachments
2. 🔍 Search Emails - Find emails by sender, recipient, subject, date
3. 📊 Analyze Inbox - See top senders cluttering your inbox
4. 📁 Organize Emails - Move emails to labeled folders
5. 🔧 Create Auto-Filter - Auto-sort future emails from a sender
6. 📝 Quick Filter - Analyze → Organize → Filter in one flow
```

Use AskUserQuestion with these options to let the user choose.

### Step 2: Execute Chosen Workflow

Based on user selection, follow the appropriate workflow below.

---

## Workflow A: Send Email

### A1. Gather Details

Ask for:

- **To**: Recipient email(s)
- **Subject**: Email subject line
- **Body**: Message content (markdown supported)
- **Attachments**: Optional file paths

### A2. Send Method (Auto-Fallback)

The send script tries **Gmail SMTP** first, then **Resend API** as fallback if SMTP fails.

No action needed - fallback is automatic when `RESEND_API_KEY` is set.

### A3. Generate Attachments (if needed)

For markdown → PDF:

```bash
python3 {baseDir}/scripts/md-to-pdf.py input.md output.pdf
```

For data → XLSX:

```bash
python3 {baseDir}/scripts/create-xlsx.py --data data.json --output output.xlsx
```

### A4. Preview Email (REQUIRED)

**ALWAYS show preview before send:**

```
EMAIL PREVIEW
═══════════════════════════════════════════════════════════════════
To:      recipient@example.com
CC:      (none)
Subject: Your Subject Here

Body:
───────────────────────────────────────────────────────────────────
[Full email body displayed here]
───────────────────────────────────────────────────────────────────

Attachments:
- report.pdf (245 KB)

═══════════════════════════════════════════════════════════════════
```

### A5. Human Confirmation (REQUIRED)

Use AskUserQuestion with options:

- **Send** - Send the email now
- **Edit** - Go back and modify
- **Cancel** - Abort, don't send

**Only proceed to send if user explicitly selects "Send".**

### A6. Send Email (Only After Confirmation)

```bash
# Basic email
node {baseDir}/scripts/send-email.cjs --to "recipient" --subject "Subject" --body "Body"

# With attachment (use --attach or -a, NOT --attachments)
node {baseDir}/scripts/send-email.cjs --to "recipient" --subject "Subject" --body "Body" --attach "/path/to/file.pdf"

# Multiple attachments
node {baseDir}/scripts/send-email.cjs --to "recipient" -s "Subject" -b "Body" -a "file1.pdf" -a "file2.xlsx"
```

**⚠️ IMPORTANT:** The attachment flag is `--attach` or `-a`, NOT `--attachments`

### A7. Confirm Success

Report message ID and delivery status.

---

## Workflow B: Search Emails

Search sent mail, inbox, or all mail by recipient, sender, subject, or date.

### B1. Parse User Intent or Ask

If user provides context (e.g., "search sent to pablo"), extract:

- **Folder**: sent, inbox, or all (default: all)
- **To**: Recipient email
- **From**: Sender email
- **Subject**: Subject text (partial match)
- **Since/Before**: Date range

If unclear, use AskUserQuestion:

```
SEARCH EMAILS
═══════════════════════════════════════════════════════════════════

Where should I search?
- Sent Mail (emails you sent)
- Inbox (emails you received)
- All Mail (everything)
```

Then ask for search criteria:

```
What are you looking for?
- By Recipient (TO:)
- By Sender (FROM:)
- By Subject
- By Date Range
```

### B2. Run Search

```bash
# Search sent mail to a specific person
node {baseDir}/scripts/search-emails.cjs --folder sent --to "pablo@intentsolutions.io"

# Search inbox from a sender
node {baseDir}/scripts/search-emails.cjs --folder inbox --from "notifications@github.com"

# Search by subject in all mail
node {baseDir}/scripts/search-emails.cjs --folder all --subject "meeting"

# Search with date range
node {baseDir}/scripts/search-emails.cjs --to "pablo@example.com" --since 2025-01-01

# Limit results and output JSON too
node {baseDir}/scripts/search-emails.cjs --to "pablo@example.com" --limit 20 --json
```

**Flags:**
| Flag | Short | Description |
|------|-------|-------------|
| `--folder` | `-f` | sent, inbox, all (default: all) |
| `--to` | `-t` | Recipient email |
| `--from` | `-r` | Sender email |
| `--subject` | `-s` | Subject text (partial match) |
| `--since` | | Emails since YYYY-MM-DD |
| `--before` | | Emails before YYYY-MM-DD |
| `--limit` | `-l` | Max results (default: 50) |
| `--output` | `-o` | Output path (default: /tmp/email-search-results.md) |
| `--json` | | Also output JSON file |

### B3. Present Results

Read the output file and present to user:

```bash
cat /tmp/email-search-results.md
```

Show summary first, then offer to show full emails or specific ones.

### B4. Follow-up Actions

After showing results, offer:

- Show specific email in full
- Export to different format
- Compose reply to one of the emails
- Return to main menu

---

## Workflow C: Analyze Inbox

### C1. Load Environment

```bash
export GMAIL_USER_EMAIL=$(grep GMAIL_USER_EMAIL ~/.env | cut -d= -f2)
export GMAIL_APP_PASSWORD=$(grep GMAIL_APP_PASSWORD ~/.env | cut -d= -f2 | tr -d ' ')
```

### C2. Run Analysis

```bash
node {baseDir}/scripts/analyze-inbox.cjs
```

### C3. Present Results

Show top 25 senders in a table format:

```
INBOX: [count] messages

| Count | Sender | Suggested Action |
|-------|--------|------------------|
| 99 | sender@example.com | Filter → Vendors/Example |
```

### C4. Offer Next Steps

Ask if user wants to:

- Filter specific senders
- Do a Quick Filter (bulk organize)
- Return to main menu

---

## Workflow D: Organize Emails

### D1. Get Filter Details

Ask user for:

- **Sender email**: Who to filter (e.g., `notifications@linkedin.com`)
- **Label name**: Where to move (e.g., `Social/LinkedIn`)

### D2. Create Organize Script

Write a temporary script to `{baseDir}/scripts/temp-organize.cjs`:

```javascript
const Imap = require('imap');
const imap = new Imap({
  user: process.env.GMAIL_USER_EMAIL,
  password: process.env.GMAIL_APP_PASSWORD,
  host: 'imap.gmail.com',
  port: 993,
  tls: true,
  tlsOptions: { rejectUnauthorized: false },
});

const LABEL = '[LABEL_NAME]';
const FROM = '[SENDER_EMAIL]';

imap.once('ready', () => {
  imap.addBox(LABEL, () => {
    imap.openBox('INBOX', false, (err, box) => {
      if (err) {
        imap.end();
        return;
      }
      imap.search([['FROM', FROM]], (err, results) => {
        if (!results || !results.length) {
          console.log(LABEL + ': 0 emails found');
          imap.end();
          return;
        }
        imap.move(results, LABEL, () => {
          console.log(LABEL + ': ✓ ' + results.length + ' emails moved');
          imap.end();
        });
      });
    });
  });
});

imap.once('error', (err) => console.error('Error:', err.message));
imap.connect();
```

### D3. Execute

```bash
node {baseDir}/scripts/temp-organize.cjs
```

### D4. Report Results

Show how many emails were moved.

### D5. Offer Auto-Filter

Ask if user wants to create an auto-filter for future emails from this sender.

---

## Workflow E: Create Auto-Filter

### E1. Get Filter Details

Ask for:

- **Sender email**: Which sender to filter
- **Label name**: Destination label
- **Skip inbox**: Yes/No (default: Yes)

### E2. Check OAuth Token

Check if `{baseDir}/scripts/gmail-oauth-token.json` exists.

If not, guide through OAuth:

1. Generate auth URL
2. User visits URL, authorizes
3. User pastes code from redirect URL
4. Exchange code for token

### E3. Create Filter Script

Write to `{baseDir}/scripts/temp-filter.cjs`:

```javascript
const { google } = require('googleapis');
const fs = require('fs');

const oauth2Client = new google.auth.OAuth2(
  process.env.GMAIL_CLIENT_ID,
  process.env.GMAIL_CLIENT_SECRET,
  'http://localhost:3333/oauth/callback',
);

const tokens = JSON.parse(fs.readFileSync('{baseDir}/scripts/gmail-oauth-token.json'));
oauth2Client.setCredentials(tokens);
const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

async function run() {
  // Get or create label
  const labels = await gmail.users.labels.list({ userId: 'me' });
  let label = labels.data.labels.find((l) => l.name === '[LABEL_NAME]');

  if (!label) {
    const created = await gmail.users.labels.create({
      userId: 'me',
      requestBody: {
        name: '[LABEL_NAME]',
        labelListVisibility: 'labelShow',
        messageListVisibility: 'show',
      },
    });
    label = created.data;
  }

  // Create filter
  try {
    await gmail.users.settings.filters.create({
      userId: 'me',
      requestBody: {
        criteria: { from: '[SENDER_EMAIL]' },
        action: { addLabelIds: [label.id], removeLabelIds: ['INBOX'] },
      },
    });
    console.log('✓ Filter created: [SENDER_EMAIL] → [LABEL_NAME]');
  } catch (err) {
    if (err.message.includes('already exists')) {
      console.log('✓ Filter already exists');
    } else {
      console.error('Error:', err.message);
    }
  }
}

run();
```

### E4. Execute

```bash
node {baseDir}/scripts/temp-filter.cjs
```

### E5. Confirm

Report filter creation success.

---

## Workflow F: Quick Filter (Recommended)

This is the power workflow - analyze, organize, and filter in one go.

### F1. Analyze

Run inbox analysis (Workflow C).

### F2. Select Senders

Present top clutter and let user select which to filter using AskUserQuestion with multiSelect.

### F3. Batch Process

For each selected sender:

1. Create label (derive from sender domain/name)
2. Move existing emails
3. Create auto-filter

### F4. Summary

Show final report:

```
QUICK FILTER COMPLETE
═══════════════════════════════════════════════════════════════════

Organized:
- LinkedIn (81 emails) → Social/LinkedIn ✓
- Coursera (49 emails) → Learning/Coursera ✓
- NVIDIA (29 emails) → Newsletters/NVIDIA ✓

Inbox: 1061 → 902 messages
Auto-filters: 3 created

Future emails from these senders will skip your inbox.
```

---

## Output Format

Always provide clear, formatted output:

**Success:**

```
✓ [Action completed]
  - Detail 1
  - Detail 2
```

**Error:**

```
✗ [Action failed]
  Reason: [explanation]
  Fix: [suggestion]
```

**Summary tables** for bulk operations.

---

## Error Handling

| Error               | Cause                     | Solution                               |
| ------------------- | ------------------------- | -------------------------------------- |
| SMTP auth failed    | Bad app password          | Auto-fallback to Resend if API key set |
| Resend failed       | Bad API key or rate limit | Check RESEND_API_KEY in .env           |
| IMAP auth failed    | Bad app password          | Check GMAIL_APP_PASSWORD in .env       |
| OAuth token missing | Never authorized          | Run OAuth flow (Workflow D)            |
| OAuth token expired | Token stale               | Delete token file, re-authorize        |
| Label exists        | Already created           | Continue (not an error)                |
| Filter exists       | Already created           | Continue (not an error)                |

**Automatic Fallback Chain:**

```
SMTP (Gmail) → Resend API → Error
```

If SMTP fails and RESEND_API_KEY is set, Resend is tried automatically.

---

## Examples

### Example 1: Search sent emails (natural language)

```
User: /email search sent to pablo
Assistant: [Runs: search-emails.cjs --folder sent --to pablo@intentsolutions.io]
         [Shows 29 emails found, presents summary]
```

### Example 2: Search with date range

```
User: /email search from github since january
Assistant: [Runs: search-emails.cjs --from notifications@github.com --since 2026-01-01]
```

### Example 3: Quick inbox cleanup

```
User: /email
Assistant: [Shows menu]
User: Quick Filter
Assistant: [Analyzes inbox, shows top senders]
User: [Selects LinkedIn, Coursera, NVIDIA]
Assistant: [Organizes 159 emails, creates 3 filters]
```

### Example 4: Send with attachment

```
User: /email send the audit report to shelly@example.com
Assistant: [Converts to PDF, sends via Resend, confirms delivery]
```

### Example 5: Check inbox clutter

```
User: what's cluttering my inbox
Assistant: [Runs analysis, shows top 25 senders with counts]
```

---

## Resources

- `{baseDir}/scripts/search-emails.cjs` - Search emails by to/from/subject/date
- `{baseDir}/scripts/analyze-inbox.cjs` - Analyze inbox senders
- `{baseDir}/scripts/send-email.cjs` - Send via SMTP
- `{baseDir}/scripts/md-to-pdf.py` - Convert markdown to PDF
- `{baseDir}/scripts/create-xlsx.py` - Generate spreadsheets
- `{baseDir}/references/email-guide.md` - Detailed documentation
