---
name: oraclecloud-install-auth
description: |
  Install and configure Oracle Cloud SDK/API authentication.
  Use when setting up a new Oracle Cloud integration.
  Trigger: "install oraclecloud", "setup oraclecloud", "oraclecloud auth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Install & Auth

## Overview
Set up Oracle Cloud Infrastructure (OCI) SDK for compute, storage, networking, and database management.

## Prerequisites
- Oracle Cloud account and API access
- API key/credentials from Oracle Cloud dashboard
- Node.js 18+ or Python 3.8+

## Instructions

### Step 1: Install SDK
```bash
pip install oci
# or: npm install oci-sdk
# Configure: oci setup config
```

### Step 2: Configure Authentication
```bash
export OCI_CONFIG_FILE="your-api-key-here"
echo 'OCI_CONFIG_FILE=your-api-key' >> .env
```

### Step 3: Verify Connection (TypeScript)
```typescript
import * as oci from 'oci-sdk';

const provider = new oci.ConfigFileAuthenticationDetailsProvider();
const computeClient = new oci.core.ComputeClient({ authenticationDetailsProvider: provider });

const instances = await computeClient.listInstances({
  compartmentId: process.env.OCI_COMPARTMENT_ID!
});
console.log(`Found ${instances.items.length} compute instances`);
```

### Step 4: Verify Connection (Python)
```python
import oci

config = oci.config.from_file()  # Reads ~/.oci/config
compute = oci.core.ComputeClient(config)

instances = compute.list_instances(compartment_id=config['tenancy'])
print(f'Found {len(instances.data)} compute instances')
```

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| Invalid API key | 401 | Verify credentials in dashboard |
| Permission denied | 403 | Check API scopes/permissions |
| Rate limited | 429 | Implement backoff |

## Resources
- [Oracle Cloud Documentation](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
After auth, proceed to `oraclecloud-hello-world`.
