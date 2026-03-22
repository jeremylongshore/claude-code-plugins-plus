---
name: remofirst-core-workflow-b
description: |
  RemoFirst core workflow b — global HR, EOR, and payroll platform integration.
  Use when working with RemoFirst for global employment, payroll, or compliance.
  Trigger with phrases like "remofirst core workflow b", "remofirst-core-workflow-b", "global HR API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, remofirst, hr, eor, payroll, global-employment]
compatible-with: claude-code, codex, openclaw
---

# RemoFirst Core Workflow B

## Overview
Payroll workflow: process payroll runs, manage benefits, handle multi-currency payments, and generate invoices.

## Prerequisites
- Completed `remofirst-core-workflow-a` (employee onboarding)

## Instructions

### Step 1: Get Payroll Summary
```python
payroll = client.get("/payroll", params={
    "month": "2026-03",
    "country_code": "GB",
})
print(f"Payroll for {payroll['period']}:")
print(f"  Employees: {payroll['employee_count']}")
print(f"  Total gross: {payroll['currency']} {payroll['total_gross']}")
print(f"  Total employer cost: {payroll['currency']} {payroll['total_employer_cost']}")
```

### Step 2: Review Employee Payslip
```python
payslip = client.get(f"/employees/{employee_id}/payslips", params={"month": "2026-03"})
print(f"Gross: {payslip['gross_salary']}")
print(f"Deductions: {payslip['total_deductions']}")
print(f"  Tax: {payslip['income_tax']}")
print(f"  National Insurance: {payslip['social_security']}")
print(f"Net pay: {payslip['net_salary']}")
```

### Step 3: Manage Benefits
```python
benefits = client.get(f"/employees/{employee_id}/benefits")
for benefit in benefits:
    print(f"  {benefit['type']}: {benefit['provider']} — {benefit['status']}")
    # Types: health_insurance, pension, dental, vision

# Add benefit
client.post(f"/employees/{employee_id}/benefits", {
    "type": "health_insurance",
    "plan": "premium",
    "start_date": "2026-04-01",
})
```

### Step 4: Generate Invoice
```python
invoice = client.get("/invoices/current")
print(f"Invoice #{invoice['number']}")
print(f"  Period: {invoice['period']}")
print(f"  Total: {invoice['currency']} {invoice['total']}")
print(f"  Due date: {invoice['due_date']}")
```

## Output
- Payroll summary with gross/net calculations
- Employee payslips with tax breakdowns
- Benefits enrollment and management
- Invoice generation and tracking

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Payroll not ready | Missing employee data | Complete onboarding first |
| Currency mismatch | Wrong country payroll | Check country_code filter |
| Benefits unavailable | Country not supported | Check country benefit options |

## Resources
- [RemoFirst Payroll](https://www.remofirst.com/solutions/finance)
- [Global Payroll Guide](https://www.remofirst.com/post/beginners-guide-to-global-payroll)

## Next Steps
Error handling: `remofirst-common-errors`
