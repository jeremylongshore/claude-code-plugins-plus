---
name: procore-core-workflow-a
description: |
  Procore core workflow a — construction management platform integration.
  Use when working with Procore API for project management, RFIs, or submittals.
  Trigger with phrases like "procore core workflow a", "procore-core-workflow-a".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, procore, construction, project-management]
compatible-with: claude-code, codex, openclaw
---

# Procore Core Workflow A

## Overview
Build a complete RFI workflow: create, assign, respond, track, and close RFIs using the Procore API.

## Prerequisites
- Completed `procore-hello-world` with project access

## Instructions

### Step 1: Create RFI with Full Details
```python
rfi_data = {
    "rfi": {
        "subject": "HVAC duct routing — Level 2 conflict",
        "question_body": "The HVAC ducts conflict with structural beams at grid B-4. Need routing alternatives.",
        "assignee_id": 11111,
        "rfi_manager_id": 22222,
        "due_date": "2026-04-15",
        "priority": "high",
        "cost_impact": "yes",
        "schedule_impact": "yes",
    }
}
rfi = requests.post(
    f"{BASE}/projects/{project_id}/rfis",
    headers={**headers, "Content-Type": "application/json"},
    json=rfi_data,
)
rfi_id = rfi.json()["id"]
```

### Step 2: Add Response to RFI
```python
response = requests.post(
    f"{BASE}/projects/{project_id}/rfis/{rfi_id}/responses",
    headers={**headers, "Content-Type": "application/json"},
    json={
        "response": {
            "body": "Route ducts below beam using 8-inch offset. See attached drawing.",
        }
    },
)
```

### Step 3: Track RFI Status
```python
rfi_detail = requests.get(f"{BASE}/projects/{project_id}/rfis/{rfi_id}", headers=headers)
data = rfi_detail.json()
print(f"RFI #{data['number']}: {data['status']['name']}")
print(f"  Days open: {data.get('days_open', 0)}")
print(f"  Responses: {len(data.get('responses', []))}")
```

### Step 4: Close RFI
```python
requests.patch(
    f"{BASE}/projects/{project_id}/rfis/{rfi_id}",
    headers={**headers, "Content-Type": "application/json"},
    json={"rfi": {"status": "closed"}},
)
```

## Output
- RFI created with full metadata (priority, impacts, due date)
- Responses added to RFI thread
- Status tracked through lifecycle
- RFI closed upon resolution

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `422 Invalid assignee` | User not on project | Verify user is a project member |
| `403 Cannot close` | Not RFI manager | Only RFI manager can close |
| Missing responses | RFI in draft status | Distribute RFI first |

## Resources
- [RFIs API](https://developers.procore.com/reference/rest/rfis)
- [Procore Developers](https://developers.procore.com/)

## Next Steps
Submittal workflow: `procore-core-workflow-b`
