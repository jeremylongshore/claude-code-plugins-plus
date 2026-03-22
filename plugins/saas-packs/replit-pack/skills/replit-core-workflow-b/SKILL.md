---
name: replit-core-workflow-b
description: |
  Manage Replit Teams, member permissions, deployment promotion, and bulk Repl admin.
  Use when managing team access, configuring deployment environments,
  auditing Repls, or administering organization settings.
  Trigger with phrases like "replit team management", "replit admin",
  "replit permissions", "replit bulk operations", "manage replit members".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, workflow, admin, teams]

---
# Replit Core Workflow B — Teams & Admin

## Overview
Secondary workflow for Replit: team member management, role assignment, deployment promotion (dev to production), custom domain setup, and organizational audit. Complements the app-building workflow in `replit-core-workflow-a`.

## Prerequisites
- Replit Teams or Enterprise plan
- Organization Owner or Admin role
- Team API token stored in `REPLIT_TOKEN`

## Instructions

### Step 1: Team Member Management
```typescript
// src/admin/team-manager.ts
interface TeamMember {
  username: string;
  email: string;
  role: 'owner' | 'admin' | 'member';
  lastActive: string;
}

async function listMembers(teamId: string): Promise<TeamMember[]> {
  const res = await fetch(`https://replit.com/api/v1/teams/${teamId}/members`, {
    headers: { Authorization: `Bearer ${process.env.REPLIT_TOKEN}` },
  });
  return res.json();
}

async function inviteMember(teamId: string, email: string, role: string) {
  return fetch(`https://replit.com/api/v1/teams/${teamId}/members`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.REPLIT_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, role }),
  });
}

async function removeMember(teamId: string, username: string) {
  return fetch(`https://replit.com/api/v1/teams/${teamId}/members/${username}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${process.env.REPLIT_TOKEN}` },
  });
}
```

### Step 2: Seat Audit
```typescript
// Identify inactive members for seat optimization
async function auditSeats(teamId: string) {
  const members = await listMembers(teamId);
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);

  const audit = {
    total: members.length,
    active: members.filter(m => new Date(m.lastActive) > thirtyDaysAgo),
    inactive: members.filter(m => new Date(m.lastActive) <= thirtyDaysAgo),
    costPerSeat: 25, // USD/month for Teams
  };

  console.log(`Active: ${audit.active.length}, Inactive: ${audit.inactive.length}`);
  console.log(`Potential savings: $${audit.inactive.length * audit.costPerSeat}/month`);

  return audit;
}
```

### Step 3: Deployment Promotion
```typescript
// Promote from development to production deployment
async function promoteDeployment(replId: string) {
  // Step 1: Verify dev deployment is healthy
  const devHealth = await fetch(`https://${replId}.replit.dev/health`);
  if (!devHealth.ok) {
    throw new Error('Development deployment not healthy. Fix before promoting.');
  }

  // Step 2: Trigger production deployment
  const res = await fetch(`https://replit.com/api/v1/repls/${replId}/deploy`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.REPLIT_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      type: 'autoscale', // or 'reserved-vm'
    }),
  });

  const deployment = await res.json();
  console.log(`Production URL: ${deployment.url}`);

  // Step 3: Verify production health
  await new Promise(r => setTimeout(r, 10000)); // Wait for deploy
  const prodHealth = await fetch(`${deployment.url}/health`);
  if (!prodHealth.ok) {
    console.error('Production health check failed. Consider rollback.');
  }

  return deployment;
}
```

### Step 4: Custom Domain Configuration
```markdown
1. Go to Deployment Settings > Custom Domain
2. Enter your domain: app.example.com
3. Add DNS records at your registrar:
   - CNAME: app -> your-repl-slug.replit.app
4. Wait for SSL certificate auto-provisioning (1-5 minutes)
5. Verify: curl -I https://app.example.com

For domains purchased through Replit:
- MX records supported for custom email services
- DNS managed in Replit dashboard
```

### Step 5: Bulk Repl Audit
```typescript
// Audit all team Repls for compliance
async function auditRepls(teamId: string) {
  const res = await fetch(`https://replit.com/api/v1/teams/${teamId}/repls`, {
    headers: { Authorization: `Bearer ${process.env.REPLIT_TOKEN}` },
  });
  const repls = await res.json();

  const report = {
    total: repls.length,
    withDeployments: repls.filter((r: any) => r.deployment).length,
    publicRepls: repls.filter((r: any) => r.isPublic).length,
    staleRepls: repls.filter((r: any) => {
      const lastEdit = new Date(r.lastEdited);
      return Date.now() - lastEdit.getTime() > 90 * 24 * 60 * 60 * 1000;
    }),
  };

  console.log('Repl Audit Report:');
  console.log(`  Total: ${report.total}`);
  console.log(`  Deployed: ${report.withDeployments}`);
  console.log(`  Public: ${report.publicRepls} (review for secrets exposure)`);
  console.log(`  Stale (>90 days): ${report.staleRepls.length}`);

  return report;
}
```

### Step 6: Activity Monitoring
```bash
# Review recent team activity
curl "https://replit.com/api/v1/teams/TEAM_ID/audit-log?limit=50" \
  -H "Authorization: Bearer $REPLIT_TOKEN" | \
  jq '.events[] | {user, action, resource, timestamp}'

# Export member activity CSV
curl "https://replit.com/api/v1/teams/TEAM_ID/members" \
  -H "Authorization: Bearer $REPLIT_TOKEN" | \
  jq -r '.[] | [.username, .email, .role, .lastActive] | @csv' > team-activity.csv
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 403 on member invite | Not an admin | Requires Owner or Admin role |
| Seat limit exceeded | Plan capacity reached | Remove inactive or upgrade plan |
| Deploy promotion fails | Dev not healthy | Fix dev deployment first |
| DNS not resolving | Wrong CNAME record | Verify DNS points to `.replit.app` |

## Resources
- [Replit Teams](https://docs.replit.com/teams/identity-and-access-management/groups-and-permissions)
- [Replit Deployments](https://docs.replit.com/cloud-services/deployments/reserved-vm-deployments)
- [Custom Domains](https://docs.replit.com/hosting/custom-domains)

## Next Steps
For common errors, see `replit-common-errors`.
