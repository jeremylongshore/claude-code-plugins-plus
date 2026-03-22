---
name: bamboohr-core-workflow-b
description: |
  Execute BambooHR secondary workflows: time off requests, PTO balances,
  benefits administration, and employee files/photos.
  Use when managing time off, checking PTO balances, handling benefits data,
  or working with employee documents in BambooHR.
  Trigger with phrases like "bamboohr time off", "bamboohr PTO", "bamboohr benefits",
  "bamboohr vacation", "bamboohr files", "bamboohr leave request".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, timeoff, benefits]
compatible-with: claude-code
---

# BambooHR Core Workflow B — Time Off, Benefits & Files

## Overview

Secondary BambooHR workflows covering time off requests, PTO balance tracking, employee file management, photos, goals, and training records.

## Prerequisites

- Completed `bamboohr-install-auth` setup
- `BambooHRClient` from `bamboohr-sdk-patterns`
- API key with time-off and files permissions

## Instructions

### Step 1: List Time Off Requests

```typescript
// GET /time_off/requests/?start=YYYY-MM-DD&end=YYYY-MM-DD
const requests = await client.request<any[]>(
  'GET',
  `/time_off/requests/?start=2026-03-01&end=2026-03-31&status=approved`,
);

for (const req of requests) {
  console.log(`${req.employeeId}: ${req.start} to ${req.end} (${req.type.name})`);
  console.log(`  Status: ${req.status.status} | ${req.amount.amount} ${req.amount.unit}`);
}
```

**Time off request response shape:**

```json
[
  {
    "id": "100",
    "employeeId": "123",
    "status": { "status": "approved", "lastChanged": "2026-03-15" },
    "name": "Jane Smith",
    "start": "2026-03-20",
    "end": "2026-03-22",
    "type": { "id": "1", "name": "Vacation" },
    "amount": { "unit": "days", "amount": "3" },
    "notes": { "employee": "Spring break trip", "manager": "" },
    "dates": {
      "2026-03-20": "1", "2026-03-21": "1", "2026-03-22": "1"
    }
  }
]
```

### Step 2: Create a Time Off Request

```typescript
// PUT /employees/{id}/time_off/request
await fetch(`${BASE}/employees/123/time_off/request`, {
  method: 'PUT',
  headers: { Authorization: AUTH, 'Content-Type': 'application/json' },
  body: JSON.stringify({
    status: 'requested',
    start: '2026-04-15',
    end: '2026-04-18',
    timeOffTypeId: 1, // 1 = Vacation, varies by company
    amount: 4,
    notes: { employee: 'Family vacation' },
    dates: {
      '2026-04-15': '1',
      '2026-04-16': '1',
      '2026-04-17': '1',
      '2026-04-18': '1',
    },
    previousRequest: 0,
  }),
});
```

### Step 3: Approve or Deny a Request

```typescript
// PUT /time_off/requests/{requestId}/status
await fetch(`${BASE}/time_off/requests/100/status`, {
  method: 'PUT',
  headers: { Authorization: AUTH, 'Content-Type': 'application/json' },
  body: JSON.stringify({
    status: 'approved', // or 'denied', 'canceled'
    note: 'Approved. Enjoy your trip!',
  }),
});
```

### Step 4: Check PTO Balances (Estimated Future Balances)

```typescript
// GET /employees/{id}/time_off/calculator?end=YYYY-MM-DD
const balances = await client.request<any>(
  'GET',
  `/employees/123/time_off/calculator?end=2026-12-31`,
);

// Returns balances for each time off type
for (const [typeId, balance] of Object.entries(balances)) {
  const b = balance as any;
  console.log(`${b.name}: ${b.balance} days remaining (accruing ${b.accrualRate}/period)`);
}
```

### Step 5: Get Time Off Policies and Types

```typescript
// GET /meta/time_off/types — list all time off types
const types = await client.request<Record<string, any>>(
  'GET', '/meta/time_off/types',
);

for (const [id, type] of Object.entries(types)) {
  console.log(`Type ${id}: ${(type as any).name}`);
}

// GET /time_off/policies — list all time off policies
const policies = await client.request<any[]>('GET', '/meta/time_off/policies');
for (const policy of policies) {
  console.log(`Policy: ${policy.name} (${policy.type})`);
}
```

### Step 6: Employee Files

```typescript
// GET /employees/{id}/files/view — list all files for an employee
const files = await client.request<{ categories: any[] }>(
  'GET', `/employees/123/files/view`,
);

for (const category of files.categories) {
  console.log(`Category: ${category.name}`);
  for (const file of category.files || []) {
    console.log(`  ${file.name} (${file.originalFileName}) — ${file.createdDate}`);
  }
}

// GET /employees/{id}/files/{fileId}/ — download a specific file
// Returns binary file content
const fileRes = await fetch(`${BASE}/employees/123/files/42/`, {
  headers: { Authorization: AUTH },
});
const fileBuffer = await fileRes.arrayBuffer();

// POST /employees/{id}/files — upload a new file
const formData = new FormData();
formData.append('file', new Blob([fileContent]), 'offer-letter.pdf');
formData.append('fileName', 'Offer Letter 2026');
formData.append('category', 'Unsigned Documents');

await fetch(`${BASE}/employees/123/files`, {
  method: 'POST',
  headers: { Authorization: AUTH },
  body: formData,
});
```

### Step 7: Employee Photos

```typescript
// GET /employees/{id}/photo/small — get employee photo (small, medium, large, original)
const photoRes = await fetch(`${BASE}/employees/123/photo/small`, {
  headers: { Authorization: AUTH },
});
// Returns image binary (JPEG/PNG)

// POST /employees/{id}/photo — upload a new photo
const photoForm = new FormData();
photoForm.append('file', photoBlob, 'headshot.jpg');
await fetch(`${BASE}/employees/123/photo`, {
  method: 'POST',
  headers: { Authorization: AUTH },
  body: photoForm,
});
```

### Step 8: Goals and Training

```typescript
// GET /v1/performance/employees/{id}/goals — list goals for an employee
const goals = await client.request<{ goals: any[] }>(
  'GET', `/v1/performance/employees/123/goals`,
);

for (const goal of goals.goals) {
  console.log(`${goal.title} — ${goal.percentComplete}% (${goal.status})`);
}

// GET /training/record/{employeeId} — get training records
const training = await client.request<any[]>(
  'GET', `/training/record/123`,
);

for (const record of training) {
  console.log(`${record.type}: completed ${record.completedDate}`);
}
```

## Output

- Time off requests listed, created, and approved/denied
- PTO balances and accrual rates retrieved
- Employee files listed, downloaded, and uploaded
- Photos fetched and updated
- Goals and training records accessed

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 400 on time off create | Missing required date fields | Include `start`, `end`, `dates` object |
| 403 on file download | Key lacks file access | Use API key with file permissions |
| 404 on time off type | Invalid `timeOffTypeId` | Fetch valid types from `/meta/time_off/types` |
| 409 on overlapping request | Existing request for same dates | Check existing requests first |

## Enterprise Considerations

- **Audit compliance**: Time off changes are logged — check audit trail for SOX/HIPAA
- **Bulk time off**: Use the custom report endpoint with time-off fields for bulk exports
- **Holiday calendars**: BambooHR manages company holidays separately from PTO; query via the Who's Out calendar
- **File retention**: BambooHR stores files indefinitely; implement your own retention policies for downloads

## Resources

- [BambooHR Time Off API](https://documentation.bamboohr.com/reference/time-off)
- [BambooHR Time Off Policies](https://documentation.bamboohr.com/reference/get-time-off-policies)
- [BambooHR Photos API](https://documentation.bamboohr.com/reference/photos)
- [BambooHR Goals API](https://documentation.bamboohr.com/reference/list-goals)

## Next Steps

For common errors and debugging, see `bamboohr-common-errors`.
