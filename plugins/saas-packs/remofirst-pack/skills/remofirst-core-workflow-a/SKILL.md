---
name: remofirst-core-workflow-a
description: |
  RemoFirst core workflow a — global HR, EOR, and payroll platform integration.
  Use when working with RemoFirst for global employment, payroll, or compliance.
  Trigger with phrases like "remofirst core workflow a", "remofirst-core-workflow-a", "global HR API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, remofirst, hr, eor, payroll, global-employment]
compatible-with: claude-code, codex, openclaw
---

# RemoFirst Core Workflow A

## Overview
Employee onboarding workflow: create employee records, manage documents, handle country-specific compliance requirements.

## Prerequisites
- Completed `remofirst-install-auth`

## Instructions

### Step 1: Create Employee Record
```python
employee = client.post("/employees", {
    "first_name": "Alice",
    "last_name": "Johnson",
    "email": "alice@company.com",
    "country_code": "GB",  # United Kingdom
    "job_title": "Senior Engineer",
    "start_date": "2026-05-01",
    "salary": {
        "amount": 85000,
        "currency": "GBP",
        "frequency": "annual",
    },
    "employment_type": "full_time",
})
print(f"Employee created: {employee['id']}")
```

### Step 2: Check Country Requirements
```python
# Get country-specific onboarding requirements
requirements = client.get(f"/countries/GB/requirements")
for req in requirements["documents"]:
    print(f"  Required: {req['name']} — {req['description']}")
    # Examples: Passport, National Insurance Number, Bank Details, P45
```

### Step 3: Submit Onboarding Documents
```python
# Upload required documents
client.post(f"/employees/{employee['id']}/documents", {
    "document_type": "passport",
    "file_url": "https://secure-storage.com/passport.pdf",
    "expiry_date": "2030-12-31",
})
```

### Step 4: Track Onboarding Status
```python
status = client.get(f"/employees/{employee['id']}/onboarding")
print(f"Onboarding status: {status['status']}")  # pending, in_progress, completed
for step in status["steps"]:
    print(f"  {step['name']}: {step['status']}")
```

## Output
- Employee record created with salary and country
- Country-specific requirements checked
- Documents uploaded for compliance
- Onboarding progress tracked

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `422 Invalid country` | Unsupported country code | Check supported countries list |
| `422 Missing required field` | Country-specific field missing | Check country requirements first |
| Onboarding stuck | Missing documents | Upload all required documents |

## Resources
- [RemoFirst](https://www.remofirst.com)
- [Global Employment](https://www.remofirst.com/solutions/human-resources)

## Next Steps
Payroll workflow: `remofirst-core-workflow-b`
