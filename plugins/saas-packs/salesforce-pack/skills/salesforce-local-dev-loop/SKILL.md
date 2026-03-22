---
name: salesforce-local-dev-loop
description: |
  Configure Salesforce local development with scratch orgs, SFDX, and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Salesforce.
  Trigger with phrases like "salesforce dev setup", "salesforce local development",
  "salesforce scratch org", "sfdx project", "develop with salesforce".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(sf:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow using Salesforce CLI (sf), scratch orgs, and jsforce with hot reload.

## Prerequisites
- Completed `salesforce-install-auth` setup
- Salesforce CLI installed (`npm install -g @salesforce/cli`)
- Dev Hub enabled in your production org (Setup > Dev Hub)
- Node.js 18+ with npm/pnpm

## Instructions

### Step 1: Create SFDX Project Structure
```bash
# Initialize a new SFDX project
sf project generate --name my-sf-project --template standard

# Project structure created:
# my-sf-project/
# ├── config/
# │   └── project-scratch-def.json   # Scratch org definition
# ├── force-app/
# │   └── main/default/              # Metadata source (Apex, LWC, etc.)
# ├── scripts/
# │   └── apex/                      # Anonymous Apex scripts
# ├── sfdx-project.json              # Project config
# └── .sf/                           # Local CLI state
```

### Step 2: Create a Scratch Org
```bash
# Authenticate to your Dev Hub first
sf org login web --set-default-dev-hub --alias DevHub

# Create a scratch org (expires in 7 days by default)
sf org create scratch \
  --definition-file config/project-scratch-def.json \
  --alias my-scratch \
  --duration-days 7 \
  --set-default

# Open scratch org in browser
sf org open --target-org my-scratch
```

### Step 3: Configure scratch-def for development
```json
{
  "orgName": "My Dev Org",
  "edition": "Developer",
  "features": ["EnableSetPasswordInApi", "MultiCurrency"],
  "settings": {
    "lightningExperienceSettings": {
      "enableS1DesktopEnabled": true
    },
    "securitySettings": {
      "passwordPolicies": {
        "enableSetPasswordInApi": true
      }
    }
  }
}
```

### Step 4: Node.js Integration Dev Loop
```
my-integration/
├── src/
│   ├── salesforce/
│   │   ├── connection.ts     # jsforce connection wrapper
│   │   ├── accounts.ts       # Account operations
│   │   ├── contacts.ts       # Contact operations
│   │   └── queries.ts        # SOQL query builders
│   └── index.ts
├── tests/
│   ├── unit/
│   │   └── queries.test.ts   # Mock-based tests
│   └── integration/
│       └── accounts.test.ts  # Live org tests
├── .env.local                # Local secrets (git-ignored)
├── .env.example              # Template for team
└── package.json
```

### Step 5: Configure Hot Reload
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "SF_ENV=scratch vitest run tests/integration/",
    "push": "sf project deploy start --target-org my-scratch",
    "pull": "sf project retrieve start --target-org my-scratch"
  }
}
```

### Step 6: Configure Testing with Mocked Connections
```typescript
import { describe, it, expect, vi } from 'vitest';

// Mock jsforce for unit tests — no live org needed
vi.mock('jsforce', () => ({
  default: {
    Connection: vi.fn().mockImplementation(() => ({
      login: vi.fn().mockResolvedValue({ id: '005xx', organizationId: '00Dxx' }),
      query: vi.fn().mockResolvedValue({
        totalSize: 1,
        done: true,
        records: [{ Id: '001xx', Name: 'Test Account', Industry: 'Tech' }],
      }),
      sobject: vi.fn().mockReturnValue({
        create: vi.fn().mockResolvedValue({ id: '001xx', success: true }),
        update: vi.fn().mockResolvedValue({ id: '001xx', success: true }),
        destroy: vi.fn().mockResolvedValue({ id: '001xx', success: true }),
      }),
    })),
  },
}));

describe('Account Service', () => {
  it('should query accounts with SOQL', async () => {
    const conn = new (await import('jsforce')).default.Connection({});
    const result = await conn.query("SELECT Id, Name FROM Account LIMIT 5");
    expect(result.totalSize).toBe(1);
    expect(result.records[0].Name).toBe('Test Account');
  });
});
```

## Output
- SFDX project with scratch org configured
- Hot reload development server running
- Unit tests with mocked jsforce connections
- Integration tests against scratch org
- Fast iteration cycle: edit, auto-reload, test

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `ERROR: No default dev hub` | Dev Hub not set | Run `sf org login web --set-default-dev-hub` |
| `INVALID_OPERATION: scratch org limit` | Hit scratch org limit (6 active) | Delete old orgs: `sf org delete scratch --target-org old-alias` |
| `SourceConflictError` | Local/remote metadata conflicts | Run `sf project retrieve start` to sync |
| `MODULE_NOT_FOUND: jsforce` | Not installed | Run `npm install jsforce` |
| `sf: command not found` | CLI not installed | Run `npm install -g @salesforce/cli` |

## Resources
- [Salesforce CLI Command Reference](https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/)
- [Scratch Org Definition File](https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_def_file.htm)
- [jsforce Documentation](https://jsforce.github.io/document/)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps
See `salesforce-sdk-patterns` for production-ready code patterns.
