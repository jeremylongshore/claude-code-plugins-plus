---
name: bamboohr-hello-world
description: |
  Create a minimal working BambooHR example — fetch employee directory and single employee.
  Use when starting a new BambooHR integration, testing your setup,
  or learning basic BambooHR REST API patterns.
  Trigger with phrases like "bamboohr hello world", "bamboohr example",
  "bamboohr quick start", "simple bamboohr code", "first bamboohr call".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, quickstart]
compatible-with: claude-code
---

# BambooHR Hello World

## Overview

Minimal working examples for the three most common BambooHR API operations: fetch the employee directory, get a single employee by ID, and run a custom report.

## Prerequisites

- Completed `bamboohr-install-auth` setup
- `BAMBOOHR_API_KEY` and `BAMBOOHR_COMPANY_DOMAIN` env vars set

## Instructions

### Step 1: Fetch Employee Directory

```typescript
import 'dotenv/config';

const COMPANY = process.env.BAMBOOHR_COMPANY_DOMAIN!;
const API_KEY = process.env.BAMBOOHR_API_KEY!;
const BASE = `https://api.bamboohr.com/api/gateway.php/${COMPANY}/v1`;
const AUTH = `Basic ${Buffer.from(`${API_KEY}:x`).toString('base64')}`;

// GET /employees/directory — returns all active employees
const dirRes = await fetch(`${BASE}/employees/directory`, {
  headers: { Authorization: AUTH, Accept: 'application/json' },
});
const directory = await dirRes.json();

console.log(`Company has ${directory.employees.length} employees`);
for (const emp of directory.employees.slice(0, 5)) {
  console.log(`  ${emp.displayName} — ${emp.jobTitle} (${emp.department})`);
}
```

**Directory response shape:**

```json
{
  "fields": [
    { "id": "displayName", "type": "text", "name": "Display Name" },
    { "id": "jobTitle", "type": "text", "name": "Job Title" }
  ],
  "employees": [
    {
      "id": "123",
      "displayName": "Jane Smith",
      "firstName": "Jane",
      "lastName": "Smith",
      "jobTitle": "Software Engineer",
      "department": "Engineering",
      "location": "Remote",
      "workEmail": "jane@acme.com",
      "photoUrl": "https://..."
    }
  ]
}
```

### Step 2: Get a Single Employee

```typescript
// GET /employees/{id}/?fields=firstName,lastName,jobTitle,department,hireDate,workEmail
const empRes = await fetch(
  `${BASE}/employees/123/?fields=firstName,lastName,jobTitle,department,hireDate,workEmail,status`,
  { headers: { Authorization: AUTH, Accept: 'application/json' } },
);
const employee = await empRes.json();

console.log(`${employee.firstName} ${employee.lastName}`);
console.log(`  Title: ${employee.jobTitle}`);
console.log(`  Dept:  ${employee.department}`);
console.log(`  Hired: ${employee.hireDate}`);
console.log(`  Email: ${employee.workEmail}`);
```

**Common employee fields you can request:**

| Field | Description |
|-------|-------------|
| `firstName`, `lastName`, `displayName` | Name fields |
| `jobTitle`, `department`, `division` | Position |
| `workEmail`, `homeEmail`, `mobilePhone` | Contact |
| `hireDate`, `originalHireDate` | Dates |
| `status` | `Active` or `Inactive` |
| `employeeNumber`, `location`, `supervisor` | Org data |
| `payRate`, `payType`, `exempt` | Compensation (admin only) |

### Step 3: Run a Custom Report

```typescript
// POST /reports/custom?format=JSON
const reportRes = await fetch(`${BASE}/reports/custom?format=JSON`, {
  method: 'POST',
  headers: {
    Authorization: AUTH,
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  body: JSON.stringify({
    title: 'Hello World Report',
    fields: ['firstName', 'lastName', 'department', 'jobTitle', 'hireDate'],
    filters: {
      lastChanged: { includeNull: 'no', value: '2024-01-01T00:00:00Z' },
    },
  }),
});
const report = await reportRes.json();

console.log(`Report: ${report.title} — ${report.employees.length} rows`);
for (const row of report.employees) {
  console.log(`  ${row.firstName} ${row.lastName} | ${row.department}`);
}
```

### Python Equivalent

```python
import os, requests
from dotenv import load_dotenv

load_dotenv()
COMPANY = os.environ["BAMBOOHR_COMPANY_DOMAIN"]
API_KEY = os.environ["BAMBOOHR_API_KEY"]
BASE = f"https://api.bamboohr.com/api/gateway.php/{COMPANY}/v1"

# Employee directory
r = requests.get(f"{BASE}/employees/directory",
                 auth=(API_KEY, "x"),
                 headers={"Accept": "application/json"})
directory = r.json()
for emp in directory["employees"][:5]:
    print(f"  {emp['displayName']} — {emp['jobTitle']}")

# Single employee
r = requests.get(f"{BASE}/employees/123/",
                 params={"fields": "firstName,lastName,department,hireDate"},
                 auth=(API_KEY, "x"),
                 headers={"Accept": "application/json"})
print(r.json())
```

## Output

- Employee directory listing with names, titles, and departments
- Single employee detail response
- Custom report with filtered results
- Console output confirming working connection

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Bad API key | Check `BAMBOOHR_API_KEY` value |
| 404 Not Found | Wrong employee ID or company domain | Verify ID exists; check `BAMBOOHR_COMPANY_DOMAIN` |
| 400 Bad Request | Invalid field name in request | Check field name list in docs |
| Empty `employees` array | No active employees or permissions | Verify API key has read access |

## Resources

- [BambooHR Field Names Reference](https://documentation.bamboohr.com/docs/list-of-field-names)
- [BambooHR API Technical Overview](https://documentation.bamboohr.com/docs/api-details)

## Next Steps

Proceed to `bamboohr-local-dev-loop` for development workflow setup.
