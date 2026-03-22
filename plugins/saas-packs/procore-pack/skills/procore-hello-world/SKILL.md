---
name: procore-hello-world
description: |
  Procore hello world — construction management platform integration.
  Use when working with Procore API for project management, RFIs, or submittals.
  Trigger with phrases like "procore hello world", "procore-hello-world".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, procore, construction, project-management]
compatible-with: claude-code, codex, openclaw
---

# Procore Hello World

## Overview
List companies and projects, then create your first RFI using the Procore REST API.

## Prerequisites
- Completed `procore-install-auth` with valid access token

## Instructions

### Step 1: List Projects
```python
company_id = 12345  # From install-auth step
projects = requests.get(
    f"https://api.procore.com/rest/v1.0/projects?company_id={company_id}",
    headers=headers,
)
for p in projects.json():
    print(f"Project: {p['name']} (ID: {p['id']})")
```

### Step 2: Create an RFI
```python
project_id = 67890
rfi = requests.post(
    f"https://api.procore.com/rest/v1.0/projects/{project_id}/rfis",
    headers={**headers, "Content-Type": "application/json"},
    json={
        "rfi": {
            "subject": "Structural beam specification clarification",
            "question_body": "Please confirm the steel grade for beams on Level 3.",
            "assignee_id": 11111,  # User ID of the person to respond
        }
    },
)
rfi.raise_for_status()
print(f"RFI created: #{rfi.json()['number']} — {rfi.json()['subject']}")
```

### Step 3: List Submittals
```python
submittals = requests.get(
    f"https://api.procore.com/rest/v1.0/projects/{project_id}/submittals",
    headers=headers,
)
for s in submittals.json():
    print(f"Submittal #{s['number']}: {s['title']} — Status: {s['status']['name']}")
```

## Output
- Listed companies and projects
- Created an RFI with subject and assignee
- Listed submittals with status

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `404 Project not found` | Wrong project_id | List projects first |
| `422 Missing subject` | Required field | Include subject in RFI |
| `403 Forbidden` | No project access | Check user permissions |

## Resources
- [Procore REST API](https://developers.procore.com/reference/rest)
- [RFIs API](https://developers.procore.com/reference/rest/rfis)

## Next Steps
Full RFI workflow: `procore-core-workflow-a`
