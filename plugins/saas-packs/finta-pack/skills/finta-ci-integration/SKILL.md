---
name: finta-ci-integration
description: |
  Automate Finta data export and reporting in CI pipelines.
  Trigger with phrases like "finta CI", "finta automated reporting".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, fundraising-crm, investor-management, finta]
compatible-with: claude-code
---

# Finta CI Integration

## Automated Pipeline Reporting

Since Finta lacks a public API, use scheduled CSV exports with cron jobs:

```bash
#!/bin/bash
# weekly-report.sh - Run via cron: 0 9 * * 1
cd /opt/finta-reports

# Process latest export (manually placed or synced)
python3 generate_report.py --input pipeline-export.csv --output reports/weekly.html

# Send via email
python3 send_report.py --to "team@company.com" --file reports/weekly.html
```

## Zapier-Based Automation

Use Zapier/Make to trigger on Finta pipeline events:
1. Trigger: Finta stage change
2. Action: Post to Slack, update Google Sheet, or create task

## Next Steps

For deployment, see `finta-deploy-integration`.
