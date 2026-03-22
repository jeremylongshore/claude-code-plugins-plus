---
name: bamboohr-core-workflow-a
description: |
  Execute BambooHR primary workflows: employee CRUD, directory sync, and custom reports.
  Use when managing employees, syncing employee data to external systems,
  or building HR data pipelines with BambooHR.
  Trigger with phrases like "bamboohr employees", "bamboohr employee management",
  "sync bamboohr directory", "bamboohr custom report", "add employee bamboohr".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, employees, reports]
compatible-with: claude-code
---

# BambooHR Core Workflow A — Employee Management & Reports

## Overview

Primary BambooHR workflows: CRUD operations on employees, directory sync to external systems, custom reports, and table data (job history, compensation, emergency contacts).

## Prerequisites

- Completed `bamboohr-install-auth` setup
- `BambooHRClient` from `bamboohr-sdk-patterns`
- API key with appropriate permissions (read or read+write)

## Instructions

### Step 1: Add a New Employee

```typescript
// POST /employees/ — minimum: firstName + lastName
const newEmpRes = await fetch(`${BASE}/employees/`, {
  method: 'POST',
  headers: { Authorization: AUTH, 'Content-Type': 'application/json' },
  body: JSON.stringify({
    firstName: 'Sarah',
    lastName: 'Chen',
    department: 'Engineering',
    jobTitle: 'Backend Engineer',
    workEmail: 'sarah.chen@acmecorp.com',
    hireDate: '2026-04-01',
    location: 'San Francisco',
    status: 'Active',
  }),
});

// New employee ID is in the Location header
const locationHeader = newEmpRes.headers.get('Location');
// e.g., "https://api.bamboohr.com/.../v1/employees/456"
const newId = locationHeader?.split('/').pop();
console.log(`Created employee ID: ${newId}`);
```

### Step 2: Update Employee Fields

```typescript
// POST /employees/{id}/ — only send fields you want to change
await fetch(`${BASE}/employees/${newId}/`, {
  method: 'POST',
  headers: { Authorization: AUTH, 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jobTitle: 'Senior Backend Engineer',
    department: 'Platform Engineering',
  }),
});
```

**Fields that trigger position history changes:** `jobTitle`, `department`, `division`, `location`, `reportsTo`. Updating these creates a new row in the employee's position history table.

### Step 3: Directory Sync to External System

```typescript
interface SyncResult {
  created: number;
  updated: number;
  deactivated: number;
  errors: string[];
}

async function syncBambooHRDirectory(
  onSync: (emp: BambooEmployee, action: string) => Promise<void>,
): Promise<SyncResult> {
  const result: SyncResult = { created: 0, updated: 0, deactivated: 0, errors: [] };

  // Fetch full directory
  const { employees } = await client.getDirectory();

  // Use the "changed since" endpoint for incremental sync
  // GET /employees/changed/?since=2026-03-20T00:00:00Z
  const changedRes = await client.request<Record<string, { lastChanged: string }>>(
    'GET', `/employees/changed/?since=${lastSyncTimestamp}`,
  );

  for (const [empId, meta] of Object.entries(changedRes.employees || {})) {
    try {
      const emp = await client.getEmployee(empId, [
        'firstName', 'lastName', 'workEmail', 'department',
        'jobTitle', 'status', 'hireDate', 'terminationDate',
      ]);

      const action = emp.terminationDate ? 'deactivated' : emp.status === 'Active' ? 'updated' : 'created';
      await onSync(emp as any, action);
      result[action as keyof SyncResult]++;
    } catch (err) {
      result.errors.push(`Employee ${empId}: ${(err as Error).message}`);
    }
  }

  return result;
}
```

### Step 4: Custom Reports

```typescript
// POST /reports/custom?format=JSON — pull arbitrary field combinations
const headcountReport = await client.customReport(
  ['department', 'division', 'jobTitle', 'hireDate', 'status', 'location'],
  { lastChanged: { includeNull: 'no', value: '2025-01-01T00:00:00Z' } },
);

// Aggregate by department
const deptCounts = new Map<string, number>();
for (const emp of headcountReport.employees) {
  const dept = emp.department || 'Unassigned';
  deptCounts.set(dept, (deptCounts.get(dept) || 0) + 1);
}

console.log('Headcount by Department:');
for (const [dept, count] of [...deptCounts.entries()].sort((a, b) => b[1] - a[1])) {
  console.log(`  ${dept}: ${count}`);
}
```

### Step 5: Saved Reports

```typescript
// GET /reports/{reportId}?format=JSON — run a saved report from BambooHR
const savedReport = await client.request<{
  title: string;
  employees: Record<string, string>[];
}>('GET', '/reports/42?format=JSON');

console.log(`Report: ${savedReport.title}`);
for (const row of savedReport.employees) {
  console.log(row);
}
```

### Step 6: Employee Table Data

BambooHR stores structured data in "tables" — each employee has rows in tables like `jobInfo`, `employmentStatus`, `compensation`, `emergencyContacts`.

```typescript
// GET /employees/{id}/tables/{tableName} — read table rows
const jobHistory = await client.getTableRows(123, 'jobInfo');
// Returns array: [{ date, jobTitle, department, division, location, reportsTo }, ...]

const compensation = await client.getTableRows(123, 'compensation');
// Returns: [{ startDate, rate, type, reason, comment }, ...]

const emergencyContacts = await client.getTableRows(123, 'emergencyContacts');
// Returns: [{ name, relationship, phone, email }, ...]

// POST /employees/{id}/tables/{tableName} — add a new row
await client.addTableRow(123, 'emergencyContacts', {
  name: 'John Smith',
  relationship: 'Spouse',
  phone: '555-0100',
  email: 'john@example.com',
});
```

**Available table names:**

| Table | Description |
|-------|-------------|
| `jobInfo` | Job title, department, division, location changes |
| `employmentStatus` | Hire date, termination date, status changes |
| `compensation` | Pay rate, pay type, pay schedule changes |
| `emergencyContacts` | Emergency contact records |
| `dependents` | Employee dependents |
| `customTable_*` | Custom tables created in BambooHR admin |

## Output

- New employees created with auto-assigned IDs
- Employee fields updated with position history tracking
- Directory sync with incremental change detection
- Custom and saved reports with aggregation
- Table data CRUD for job history, compensation, contacts

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 400 on employee create | Missing `firstName` or `lastName` | Both are required |
| 403 on compensation tables | API key lacks access | Need admin-level API key |
| 409 on duplicate | Same `employeeNumber` exists | Use unique employee numbers |
| Empty `changed` response | No changes since timestamp | Normal — nothing to sync |

## Resources

- [BambooHR Create Employee](https://documentation.bamboohr.com/reference/add-employee-2)
- [BambooHR Table Fields](https://documentation.bamboohr.com/docs/table-name-fields)
- [BambooHR Field Names](https://documentation.bamboohr.com/docs/list-of-field-names)

## Next Steps

For time off and benefits workflows, see `bamboohr-core-workflow-b`.
