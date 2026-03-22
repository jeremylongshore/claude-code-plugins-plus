---
name: snowflake-install-auth
description: |
  Install and configure Snowflake driver authentication for Node.js and Python.
  Use when setting up snowflake-sdk, snowflake-connector-python, key pair auth,
  OAuth, or SSO browser authentication.
  Trigger with phrases like "install snowflake", "setup snowflake",
  "snowflake auth", "snowflake connection", "snowflake key pair".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(openssl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Install & Auth

## Overview

Set up Snowflake drivers and configure authentication for Node.js (`snowflake-sdk`) and Python (`snowflake-connector-python`).

## Prerequisites

- Node.js 18+ or Python 3.9+
- Snowflake account (format: `<orgname>-<account_name>` or legacy `<account_locator>.<region>`)
- User with appropriate role granted

## Instructions

### Step 1: Install the Driver

```bash
# Node.js — official driver from snowflakedb
npm install snowflake-sdk

# Python — official connector
pip install snowflake-connector-python

# Python with pandas support
pip install "snowflake-connector-python[pandas]"
```

### Step 2: Choose an Authentication Method

| Method | Use Case | Env Vars Needed |
|--------|----------|-----------------|
| Password | Quick dev setup | `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD` |
| Key Pair | CI/CD, service accounts | `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PRIVATE_KEY_PATH` |
| External Browser SSO | Interactive dev | `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER` |
| OAuth | Enterprise SSO integration | `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_OAUTH_TOKEN` |

### Step 3a: Password Authentication

```typescript
// src/snowflake/client.ts
import snowflake from 'snowflake-sdk';

const connection = snowflake.createConnection({
  account: process.env.SNOWFLAKE_ACCOUNT!,   // e.g. 'myorg-myaccount'
  username: process.env.SNOWFLAKE_USER!,
  password: process.env.SNOWFLAKE_PASSWORD!,
  warehouse: process.env.SNOWFLAKE_WAREHOUSE || 'COMPUTE_WH',
  database: process.env.SNOWFLAKE_DATABASE,
  schema: process.env.SNOWFLAKE_SCHEMA || 'PUBLIC',
  role: process.env.SNOWFLAKE_ROLE || 'PUBLIC',
});

connection.connect((err, conn) => {
  if (err) {
    console.error('Unable to connect:', err.message);
    return;
  }
  console.log('Connected as id:', conn.getId());
});
```

```python
# src/snowflake_client.py
import snowflake.connector
import os

conn = snowflake.connector.connect(
    account=os.environ['SNOWFLAKE_ACCOUNT'],
    user=os.environ['SNOWFLAKE_USER'],
    password=os.environ['SNOWFLAKE_PASSWORD'],
    warehouse=os.environ.get('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
    database=os.environ.get('SNOWFLAKE_DATABASE'),
    schema=os.environ.get('SNOWFLAKE_SCHEMA', 'PUBLIC'),
    role=os.environ.get('SNOWFLAKE_ROLE', 'PUBLIC'),
)
print(f"Connected: {conn.get_query_id()}")
```

### Step 3b: Key Pair Authentication (Recommended for Automation)

```bash
# Generate 2048-bit RSA key pair
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# Assign public key to Snowflake user
# Run in Snowflake worksheet:
# ALTER USER my_service_user SET RSA_PUBLIC_KEY='MIIBIj...';
```

```typescript
import snowflake from 'snowflake-sdk';
import fs from 'fs';
import path from 'path';

const privateKey = fs.readFileSync(
  path.resolve(process.env.SNOWFLAKE_PRIVATE_KEY_PATH!),
  'utf-8'
);

const connection = snowflake.createConnection({
  account: process.env.SNOWFLAKE_ACCOUNT!,
  username: process.env.SNOWFLAKE_USER!,
  authenticator: 'SNOWFLAKE_JWT',
  privateKey: privateKey,
  warehouse: 'COMPUTE_WH',
  database: 'MY_DB',
  schema: 'PUBLIC',
});
```

```python
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

with open(os.environ['SNOWFLAKE_PRIVATE_KEY_PATH'], 'rb') as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(), password=None, backend=default_backend()
    )

conn = snowflake.connector.connect(
    account=os.environ['SNOWFLAKE_ACCOUNT'],
    user=os.environ['SNOWFLAKE_USER'],
    private_key=private_key,
    warehouse='COMPUTE_WH',
    database='MY_DB',
    schema='PUBLIC',
)
```

### Step 3c: External Browser SSO

```typescript
const connection = snowflake.createConnection({
  account: process.env.SNOWFLAKE_ACCOUNT!,
  username: process.env.SNOWFLAKE_USER!,
  authenticator: 'EXTERNALBROWSER',
  warehouse: 'COMPUTE_WH',
});
// Opens browser for IdP login, returns token to driver
```

### Step 4: Configure Environment

```bash
# .env (NEVER commit — add to .gitignore)
SNOWFLAKE_ACCOUNT=myorg-myaccount
SNOWFLAKE_USER=my_user
SNOWFLAKE_PASSWORD=my_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=MY_DB
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=SYSADMIN
SNOWFLAKE_PRIVATE_KEY_PATH=./rsa_key.p8

# .gitignore additions
.env
.env.local
rsa_key.p8
rsa_key.pub
```

### Step 5: Verify Connection

```typescript
connection.connect((err, conn) => {
  if (err) { console.error(err.message); return; }
  conn.execute({
    sqlText: 'SELECT CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_ROLE()',
    complete: (err, stmt, rows) => {
      if (err) { console.error(err.message); return; }
      console.log('Context:', rows?.[0]);
    },
  });
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `390100: Incorrect username or password` | Bad credentials | Verify user/password in Snowflake console |
| `390144: JWT token is invalid` | Wrong private key or expired | Regenerate key pair, re-assign public key |
| `390429: IP ... is not allowed to access Snowflake` | Network policy blocking | Add IP to network policy allowlist |
| `ECONNREFUSED` / `ENOTFOUND` | Wrong account identifier | Use format `orgname-accountname` (not URL) |
| `Could not connect to Snowflake backend` | Firewall or proxy | Allow outbound HTTPS to `*.snowflakecomputing.com` |

## Resources

- [Node.js Driver Docs](https://docs.snowflake.com/en/developer-guide/node-js/nodejs-driver)
- [Python Connector Docs](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector)
- [Key Pair Auth](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- [Authentication Overview](https://docs.snowflake.com/en/user-guide/security-authentication-overview)

## Next Steps

After successful auth, proceed to `snowflake-hello-world` for your first query.
