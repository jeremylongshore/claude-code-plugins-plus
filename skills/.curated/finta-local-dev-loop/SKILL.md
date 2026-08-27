---
name: finta-local-dev-loop
description: 'Set up Finta workflow automation and data export for local analysis.

  Use when building fundraising reports, exporting pipeline data,

  or automating investor outreach workflows.

  Trigger with phrases like "finta workflow", "finta automation",

  "finta data export", "finta reporting".

  '
allowed-tools: Read, Write, Edit, Bash(python3:*), Grep
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- fundraising-crm
- investor-management
- finta
compatibility: Designed for Claude Code
---
# Finta Local Dev Loop

## Overview

Finta is primarily UI-driven without a public API. For local automation, use CSV exports from Finta combined with Python scripts for analysis, reporting, and integration with other tools.

## Prerequisites

- An approved, minimal CSV export; use a sandbox or de-identified copy for development.
- Python with the required analysis packages installed in an isolated project environment.
- A local directory excluded from version control for raw exports and generated reports.

## Instructions

### Export Pipeline Data

1. In Finta, go to **Pipeline** > **Export** > **CSV**
2. Save as `pipeline-export.csv`

### Analyze Fundraise Pipeline

```python
import pandas as pd
from datetime import datetime

# Load Finta export
df = pd.read_csv("pipeline-export.csv")

# Pipeline summary
summary = df.groupby("Stage").agg(
    count=("Name", "count"),
    avg_check=("Check Size", "mean"),
).reset_index()

print("Pipeline Summary:")
print(summary.to_string(index=False))

# Conversion rates
stages = ["Researching", "Reaching Out", "Intro Meeting", "Follow-up", "Due Diligence", "Term Sheet", "Closed"]
for i in range(len(stages) - 1):
    current = len(df[df["Stage"] == stages[i]])
    next_stage = len(df[df["Stage"] == stages[i+1]])
    rate = (next_stage / current * 100) if current > 0 else 0
    print(f"  {stages[i]} -> {stages[i+1]}: {rate:.0f}%")
```

### Weekly Pipeline Report

```python
def generate_weekly_report(df: pd.DataFrame) -> str:
    total = len(df)
    active = len(df[df["Stage"].isin(["Intro Meeting", "Follow-up", "Due Diligence"])])
    term_sheets = len(df[df["Stage"] == "Term Sheet"])
    closed = len(df[df["Stage"] == "Closed"])

    return f"""
Fundraise Pipeline Report ({datetime.now().strftime('%Y-%m-%d')})
==================================================
Total investors: {total}
Active conversations: {active}
Term sheets: {term_sheets}
Closed: {closed}
"""
```

## Output

Generate a local, access-controlled summary containing aggregate stage counts, conversion rates, and an explicit export timestamp. Keep the original CSV separate from the report and avoid including investor names, email addresses, document links, or exact financial terms unless the approved audience requires them.

## Error Handling

- Stop if the export is missing the expected columns; inspect the header and map fields deliberately rather than guessing.
- Treat malformed dates and blank stage values as review items, not zero values. Emit their row count without copying source records into logs.
- If a report is unexpectedly empty or unusually large, compare the export time and filter criteria before sharing it.
- Delete local raw copies using the organization’s approved retention process after the analysis purpose ends.

## Examples

Run the analysis on a synthetic CSV with three invented rows first. Confirm that the report contains only aggregate counts, then repeat with the approved export in a protected local directory. Share the generated summary through the authorized workspace rather than committing either file to the repository.

## Resources

- [Finta Website](https://www.trustfinta.com)

## Next Steps

See `finta-sdk-patterns` for integration patterns.
