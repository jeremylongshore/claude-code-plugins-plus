---
name: klingai-usage-analytics
description: |
  Build usage analytics and reporting for Kling AI. Use when tracking generation patterns,
  analyzing costs, or creating dashboards. Trigger with phrases like 'klingai analytics',
  'kling ai usage report', 'klingai metrics', 'video generation stats'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Klingai Usage Analytics

## Overview

This skill shows how to build comprehensive usage analytics including generation metrics, cost analysis, trend reporting, and visualization dashboards for Kling AI.

## Prerequisites

- Kling AI API key configured
- Usage data collection in place
- Python 3.8+ with pandas/matplotlib (optional)

## Instructions

Follow these steps for analytics:

1. **Collect Data**: Capture usage events
2. **Aggregate Metrics**: Calculate key metrics
3. **Generate Reports**: Create usage reports
4. **Visualize Data**: Build dashboards
5. **Set Up Alerts**: Anomaly detection

## Output

Successful execution produces:
- Usage summary statistics
- Daily breakdown reports
- Top user analysis
- Anomaly detection alerts
- Exportable CSV data

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Dashboard](https://console.klingai.com/usage)
- [pandas Documentation](https://pandas.pydata.org/)
- [Data Visualization](https://matplotlib.org/)
