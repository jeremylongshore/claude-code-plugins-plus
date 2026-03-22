---
name: remofirst-prod-checklist
description: |
  RemoFirst prod checklist — global HR, EOR, and payroll platform integration.
  Use when working with RemoFirst for global employment, payroll, or compliance.
  Trigger with phrases like "remofirst prod checklist", "remofirst-prod-checklist", "global HR API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, remofirst, hr, eor, payroll, global-employment]
compatible-with: claude-code, codex, openclaw
---

# RemoFirst Prod Checklist

## Overview
Implementation patterns for RemoFirst prod checklist — global HR and EOR platform integration.

## Prerequisites
- Completed `remofirst-install-auth` setup

## Instructions

### Step 1: API Pattern
```python
client = RemoFirstClient()
employees = client.get("/employees", params={"page_size": 10})
print(f"Employees: {len(employees['data'])}")
```

## Output
- RemoFirst integration for prod checklist

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Contact RemoFirst support |
| 429 Rate Limited | Too many requests | Implement backoff |
| 422 Validation Error | Missing required field | Check API documentation |

## Resources
- [RemoFirst](https://www.remofirst.com)

## Next Steps
See related RemoFirst skills for more workflows.
