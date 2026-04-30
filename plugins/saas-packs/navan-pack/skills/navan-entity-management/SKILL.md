---
name: navan-entity-management
description: 'Manage Navan users, departments, cost centers, and approval chains via
  API and SCIM provisioning.

  Use when onboarding departments, integrating identity providers, or auditing user
  access.

  Trigger with "navan entity management", "navan user management", "navan SCIM setup".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan — Entity Management

## Overview

This skill covers organizational entity management in Navan: users, departments, cost centers, and approval chains. Navan supports two approaches for user lifecycle management — the REST API with GET /get_users for querying and auditing, and SCIM 2.0 provisioning for automated sync with identity providers like Okta, Entra ID (Azure AD), and OneLogin. Travel policies are assigned at the department level, and approval chains support multi-level routing based on expense thresholds and trip types. This skill is essential for organizations managing 100+ travelers.

## Prerequisites

- Navan account with admin-level API credentials (see `navan-install-auth`)
- OAuth 2.0 token with admin scope
- For SCIM: Okta, Entra ID, or OneLogin with SCIM 2.0 support
- For SSO: SAML 2.0 or Google Workspace configured in Navan Admin
- Environment variables: `NAVAN_CLIENT_ID`, `NAVAN_CLIENT_SECRET`, `NAVAN_BASE_URL`

## Instructions

### Step 1: Authenticate and Retrieve Booking Data

```typescript
const tokenRes = await fetch(`${process.env.NAVAN_BASE_URL}/ta-auth/oauth/token`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: process.env.NAVAN_CLIENT_ID!,
    client_secret: process.env.NAVAN_CLIENT_SECRET!,
  }),
});
const { access_token } = await tokenRes.json();
const headers = { Authorization: `Bearer ${access_token}` };

// GET /v1/bookings — retrieve bookings (records in .data array)
const bookingsRes = await fetch(
  `${process.env.NAVAN_BASE_URL}/v1/bookings?page=0&size=50`,
  { headers }
);
const { data: bookings } = await bookingsRes.json();

// Extract unique users from booking data
const users = [...new Map(bookings.map((b: any) => [b.traveler_email, b])).values()];

users.forEach((user: any) => {
  console.log(`${user.email} | Role: ${user.role} | Dept: ${user.department}`);
  console.log(`  Cost Center: ${user.cost_center} | Manager: ${user.manager_email}`);
  console.log(`  Travel Policy: ${user.travel_policy_name}`);
});
```

### Step 2: Audit User Access and Roles

```typescript
// Build an access audit report
interface UserAudit {
  email: string;
  role: string;
  department: string;
  hasManagerAssigned: boolean;
  hasCostCenter: boolean;
  hasTravelPolicy: boolean;
}

const audit: UserAudit[] = users.map((u: any) => ({
  email: u.email,
  role: u.role,
  department: u.department ?? 'UNASSIGNED',
  hasManagerAssigned: Boolean(u.manager_email),
  hasCostCenter: Boolean(u.cost_center),
  hasTravelPolicy: Boolean(u.travel_policy_name),
}));

// Flag users missing required configuration
const incomplete = audit.filter(
  u => !u.hasManagerAssigned || !u.hasCostCenter || !u.hasTravelPolicy
);
console.log(`\nUsers with incomplete setup: ${incomplete.length}/${audit.length}`);
incomplete.forEach(u => {
  const missing = [];
  if (!u.hasManagerAssigned) missing.push('manager');
  if (!u.hasCostCenter) missing.push('cost_center');
  if (!u.hasTravelPolicy) missing.push('travel_policy');
  console.log(`  ${u.email}: missing ${missing.join(', ')}`);
});
```

### Step 3: Configure SCIM Provisioning (Okta)

SCIM 2.0 enables automated user lifecycle management. Configure in the Navan admin console:

1. Navigate to Admin > Travel admin > Settings > Identity Provider
2. Select "SCIM 2.0" as the provisioning method
3. Copy the SCIM endpoint URL and bearer token

In Okta:
1. Add the Navan application from the OIN catalog
2. Configure provisioning with the SCIM endpoint URL
3. Enable: Create Users, Update User Attributes, Deactivate Users
4. Map attributes: `userName`, `email`, `department`, `costCenter`, `manager`

```bash
# Test SCIM endpoint connectivity (replace with your SCIM URL and token)
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${NAVAN_SCIM_TOKEN}" \
  "${NAVAN_SCIM_URL}/Users?count=1"
# Expected: 200
```

### Step 4: Configure SCIM Provisioning (Entra ID)

For Microsoft Entra ID (formerly Azure AD):

1. In Entra ID portal, add Navan as an Enterprise Application
2. Under Provisioning, set mode to "Automatic"
3. Enter the Navan SCIM tenant URL and secret token
4. Map attributes: `userPrincipalName` -> `userName`, `department`, `companyName`
5. Enable provisioning and set scope to "Sync only assigned users"

### Step 5: Department and Cost Center Structure

```typescript
// Organize users by department for policy assignment analysis
const byDepartment: Record<string, any[]> = {};
users.forEach((u: any) => {
  const dept = u.department ?? 'Unassigned';
  if (!byDepartment[dept]) byDepartment[dept] = [];
  byDepartment[dept].push(u);
});

console.log('\nDepartment Summary:');
Object.entries(byDepartment)
  .sort((a, b) => b[1].length - a[1].length)
  .forEach(([dept, members]) => {
    const costCenters = [...new Set(members.map((m: any) => m.cost_center))];
    console.log(`  ${dept}: ${members.length} users, cost centers: ${costCenters.join(', ')}`);
  });
```

### Step 6: Approval Chain Configuration

```typescript
// Define multi-level approval routing
// Configure in Navan Admin > Policies > Approval Chains
interface ApprovalChain {
  department: string;
  levels: {
    threshold: number;
    approverRole: string;
    approverEmail: string;
  }[];
}

const approvalChains: ApprovalChain[] = [
  {
    department: 'Engineering',
    levels: [
      { threshold: 500, approverRole: 'manager', approverEmail: 'eng-mgr@company.com' },
      { threshold: 2000, approverRole: 'director', approverEmail: 'eng-dir@company.com' },
      { threshold: Infinity, approverRole: 'vp', approverEmail: 'vp-eng@company.com' },
    ],
  },
  {
    department: 'Sales',
    levels: [
      { threshold: 1000, approverRole: 'manager', approverEmail: 'sales-mgr@company.com' },
      { threshold: 5000, approverRole: 'director', approverEmail: 'sales-dir@company.com' },
      { threshold: Infinity, approverRole: 'cro', approverEmail: 'cro@company.com' },
    ],
  },
];

// Determine required approver for a given expense
function routeForApproval(dept: string, amount: number): string {
  const chain = approvalChains.find(c => c.department === dept);
  if (!chain) return 'finance@company.com'; // fallback
  const level = chain.levels.find(l => amount <= l.threshold);
  return level?.approverEmail ?? 'cfo@company.com';
}
```

## Output

Successful execution produces:
- Complete user roster with roles, departments, cost centers, and policy assignments
- Access audit report identifying users with incomplete configuration
- SCIM provisioning configuration for Okta or Entra ID
- Department hierarchy with cost center mappings
- Approval chain definitions with threshold-based routing

## Error Handling

| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| Unauthorized | 401 | Expired or invalid bearer token | Re-authenticate via POST /ta-auth/oauth/token |
| Forbidden | 403 | Non-admin credentials used | Verify admin-level API credentials |
| Rate Limited | 429 | Too many requests | Implement exponential backoff (start at 1s) |
| SCIM Auth Failed | 401 | Invalid SCIM bearer token | Regenerate token in Navan Admin > Identity Provider |
| SCIM Mapping Error | 400 | Missing required attribute | Verify userName and email mappings in IdP |
| Server Error | 500 | Navan platform issue | Retry with backoff; check Navan status page |

## Examples

**Python — User audit with CSV export:**

```python
import requests
import csv
import os

base_url = os.environ.get('NAVAN_BASE_URL', 'https://api.navan.com')
auth = requests.post(f'{base_url}/ta-auth/oauth/token', data={
    'grant_type': 'client_credentials',
    'client_id': os.environ['NAVAN_CLIENT_ID'],
    'client_secret': os.environ['NAVAN_CLIENT_SECRET'],
})
headers = {'Authorization': f'Bearer {auth.json()["access_token"]}'}

# Retrieve bookings and extract user data
resp = requests.get(f'{base_url}/v1/bookings', params={'page': 0, 'size': 50}, headers=headers).json()
bookings = resp['data']
# Deduplicate users from booking records
users = list({b.get('traveler_email'): b for b in bookings}.values())

with open('navan-user-audit.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'email', 'role', 'department', 'cost_center', 'manager', 'policy'
    ])
    writer.writeheader()
    for u in users:
        writer.writerow({
            'email': u.get('email'),
            'role': u.get('role'),
            'department': u.get('department', ''),
            'cost_center': u.get('cost_center', ''),
            'manager': u.get('manager_email', ''),
            'policy': u.get('travel_policy_name', ''),
        })
print(f'Exported {len(users)} users to navan-user-audit.csv')
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — Official documentation and support
- [Navan Integrations](https://navan.com/integrations) — Okta, Entra ID, BambooHR, Workday, ADP connectors
- [Booking Data Integration](https://app.navan.com/app/helpcenter/articles/travel/admin/other-integrations/booking-data-integration) — Data export and user management

## Next Steps

After configuring entities, proceed to `navan-core-workflow-a` for travel booking workflows or `navan-enterprise-rbac` for role-based access control.
