---
name: navan-enterprise-rbac
description: 'Configure Navan admin roles, travel policies, approval workflows, and
  department-level access controls.

  Use when setting up enterprise RBAC, policy enforcement, or approval chains in Navan.

  Trigger with "navan rbac", "navan roles", "navan travel policy", "navan approval
  workflow".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Enterprise RBAC

## Overview
Navan's enterprise tier provides granular role-based access control, configurable travel policies, and multi-tier approval workflows. The platform enforces in-policy vs out-of-policy bookings at the point of purchase — travelers see policy-compliant options highlighted and must justify out-of-policy selections through approval chains. This skill covers the admin role hierarchy, policy rule configuration, department-scoped access, and API-driven policy management.

## Prerequisites
- Navan enterprise account with Global Admin or Travel Admin access
- OAuth 2.0 credentials with admin-scoped permissions (see `navan-install-auth`)
- Organizational hierarchy defined (departments, cost centers, reporting lines)
- Dedicated Customer Success Manager contact (included with enterprise tier)

## Instructions

### Step 1: Understand the Navan Role Hierarchy
```
Global Admin
├── Travel Admin         — Manage travel policies, view all bookings
├── Expense Admin        — Manage expense policies, approve/reject reports
├── Finance Admin        — View spend analytics, export financial reports
├── Department Manager   — Approve bookings/expenses for direct reports
├── Arranger            — Book travel on behalf of other employees
└── Traveler            — Book own travel within policy, submit expenses
```

| Role | Book Travel | Approve | View All Bookings | Edit Policies | Manage Users |
|------|-------------|---------|-------------------|---------------|--------------|
| Global Admin | Yes | Yes | Yes | Yes | Yes |
| Travel Admin | Yes | Yes | Yes | Yes | No |
| Expense Admin | No | Yes | Expenses Only | Expense Only | No |
| Finance Admin | No | No | Yes (read-only) | No | No |
| Dept Manager | Yes | Own Dept | Own Dept | No | No |
| Arranger | Others | No | Arranged Only | No | No |
| Traveler | Self | No | Own Only | No | No |

### Step 2: Configure Travel Policy Rules via API
```typescript
const accessToken = process.env.NAVAN_ACCESS_TOKEN!;

// Retrieve current travel policy
const policyRes = await fetch('https://api.navan.com/v1/travel-policies', {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});
const policies = await policyRes.json();

// Create a department-specific policy
const newPolicy = await fetch('https://api.navan.com/v1/travel-policies', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Engineering Department Policy',
    department_ids: ['dept-eng-001'],
    rules: {
      flight: {
        max_price: 800,
        cabin_class: 'economy',
        advance_booking_days: 14,
        allow_premium_economy: true,
        allow_business_class: false
      },
      hotel: {
        max_nightly_rate: 250,
        max_star_rating: 4,
        preferred_chains: ['marriott', 'hilton', 'hyatt']
      },
      car_rental: {
        max_daily_rate: 75,
        max_class: 'intermediate',
        preferred_vendors: ['enterprise', 'national']
      },
      out_of_policy: {
        action: 'require_approval',        // 'block' | 'require_approval' | 'warn'
        require_justification: true,
        auto_escalate_above: 1500          // Auto-escalate to finance above this amount
      }
    }
  })
});
```

### Step 3: Set Up Approval Workflows
```typescript
// Configure multi-tier approval chain
const approvalWorkflow = await fetch('https://api.navan.com/v1/approval-workflows', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Standard Travel Approval',
    applies_to: ['booking', 'expense'],
    tiers: [
      {
        order: 1,
        approver_type: 'direct_manager',
        conditions: { min_amount: 0 },
        auto_approve_below: 200,
        timeout_hours: 48,
        timeout_action: 'escalate'
      },
      {
        order: 2,
        approver_type: 'department_head',
        conditions: { min_amount: 1000 },
        timeout_hours: 72,
        timeout_action: 'escalate'
      },
      {
        order: 3,
        approver_type: 'finance_admin',
        conditions: { min_amount: 5000 },
        timeout_hours: 24,
        timeout_action: 'notify_global_admin'
      }
    ],
    out_of_policy_override: {
      always_require_tier: 2,
      justification_required: true
    }
  })
});
```

### Step 4: Assign Users to Departments and Roles
```typescript
// Bulk role assignment for department onboarding
async function assignDepartmentRoles(
  departmentId: string,
  userEmails: string[],
  role: string
): Promise<void> {
  for (const email of userEmails) {
    const res = await fetch('https://api.navan.com/v1/users/role-assignment', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email,
        role,
        department_id: departmentId,
        effective_date: new Date().toISOString()
      })
    });

    if (!res.ok) {
      console.error(`Failed to assign ${role} to ${email}: HTTP ${res.status}`);
    } else {
      console.log(`Assigned ${role} to ${email} in dept ${departmentId}`);
    }
  }
}

// Example: onboard engineering managers
await assignDepartmentRoles('dept-eng-001', [
  'manager1@company.com',
  'manager2@company.com'
], 'department_manager');
```

### Step 5: Audit Role Assignments
```bash
# List all users with admin roles
curl -s -H "Authorization: Bearer $NAVAN_ACCESS_TOKEN" \
  'https://api.navan.com/v1/users?role=admin&limit=100' | python3 -m json.tool

# Get policy violations report
curl -s -H "Authorization: Bearer $NAVAN_ACCESS_TOKEN" \
  'https://api.navan.com/v1/reports/policy-violations?start_date=2026-01-01' \
  | python3 -m json.tool
```

## Output
A fully configured RBAC system with department-scoped travel policies, multi-tier approval workflows, and role assignments for the organizational hierarchy. Travelers see policy-compliant options at booking time, out-of-policy requests route through the approval chain, and admins have audit visibility into policy violations.

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| Insufficient admin permissions | 403 | Requesting user needs Global Admin or Travel Admin role |
| Department not found | 404 | Verify department_id exists; create via admin dashboard first |
| Conflicting policy rules | 409 | Two policies targeting the same department; deactivate the old one first |
| Invalid approval chain | 400 | Ensure tier order is sequential and approver_type values are valid |
| User not found | 404 | Verify email matches an active Navan user; check SCIM sync status |

## Examples

**Check a user's effective policy:**
```bash
curl -s -H "Authorization: Bearer $NAVAN_ACCESS_TOKEN" \
  'https://api.navan.com/v1/users/user@company.com/effective-policy' \
  | python3 -m json.tool
```

**Export policy compliance summary:**
```bash
curl -s -H "Authorization: Bearer $NAVAN_ACCESS_TOKEN" \
  'https://api.navan.com/v1/reports/policy-compliance?period=monthly' \
  | python3 -m json.tool
```

## Resources
- [Navan Help Center](https://app.navan.com/app/helpcenter) — Admin role configuration and policy setup guides
- [Navan Security](https://navan.com/security) — SOC 2, ISO 27001, PCI DSS compliance documentation
- [Navan Integrations](https://navan.com/integrations) — SCIM and directory sync for automated role management

## Next Steps
After configuring RBAC, see `navan-security-basics` for SSO/SAML enforcement and credential hardening, or `navan-observability` for monitoring policy compliance and booking patterns.
