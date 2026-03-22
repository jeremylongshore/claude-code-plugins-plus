---
name: procore-core-workflow-b
description: |
  Procore core workflow b — construction management platform integration.
  Use when working with Procore API for project management, RFIs, or submittals.
  Trigger with phrases like "procore core workflow b", "procore-core-workflow-b".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, procore, construction, project-management]
compatible-with: claude-code, codex, openclaw
---

# Procore Core Workflow B

## Overview
Build a submittal workflow: create submittals, assign reviewers, track approvals, and manage the review cycle.

## Prerequisites
- Completed `procore-core-workflow-a` (RFIs)

## Instructions

### Step 1: Create Submittal
```python
submittal = requests.post(
    f"{BASE}/projects/{project_id}/submittals",
    headers={**headers, "Content-Type": "application/json"},
    json={
        "submittal": {
            "title": "Concrete mix design — Foundation",
            "specification_section": "03 30 00",
            "description": "Concrete mix design for foundation pour, 4000 PSI.",
            "received_from_id": 33333,  # Subcontractor
            "approver_id": 44444,        # Project engineer
            "due_date": "2026-04-20",
        }
    },
)
submittal_id = submittal.json()["id"]
print(f"Submittal #{submittal.json()['number']} created")
```

### Step 2: Update Submittal Status
```python
# Approve the submittal
requests.patch(
    f"{BASE}/projects/{project_id}/submittals/{submittal_id}",
    headers={**headers, "Content-Type": "application/json"},
    json={"submittal": {"status_id": 2}},  # 2 = Approved
)
```

### Step 3: List Submittals with Filters
```python
# Get all pending submittals
pending = requests.get(
    f"{BASE}/projects/{project_id}/submittals",
    headers=headers,
    params={"filters[status_id]": 1},  # 1 = Open/Pending
)
for s in pending.json():
    print(f"  #{s['number']}: {s['title']} — Due: {s['due_date']}")
```

## Output
- Submittals created with specification sections
- Review workflow with approve/reject
- Filtered submittal listing

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `422 Missing approver` | Required field | Set approver_id |
| `403 Cannot approve` | Not the approver | Only assigned approver can approve |

## Resources
- [Submittals API](https://developers.procore.com/reference/rest/submittals)
- [Procore Developers](https://developers.procore.com/)

## Next Steps
Handle events: `procore-webhooks-events`
