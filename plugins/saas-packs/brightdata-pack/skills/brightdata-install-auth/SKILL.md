---
name: brightdata-install-auth
description: |
  Install and configure Bright Data SDK/CLI authentication.
  Use when setting up a new Bright Data integration, configuring API keys,
  or initializing Bright Data in your project.
  Trigger with phrases like "install brightdata", "setup brightdata",
  "brightdata auth", "configure brightdata API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Install & Auth

## Overview

Configure Bright Data proxy credentials, API tokens, and SSL certificates for web scraping. Bright Data uses HTTP proxy protocols and REST APIs — you authenticate via zone credentials from the control panel, not a dedicated npm SDK.

## Prerequisites

- Node.js 18+ or Python 3.10+
- Bright Data account at https://brightdata.com
- A configured zone (Web Unlocker, Scraping Browser, SERP API, or Residential)
- Zone credentials from the Bright Data control panel

## Instructions

### Step 1: Gather Credentials from Control Panel

Log into https://brightdata.com/cp and navigate to your zone's overview tab:

| Credential | Location | Example |
|-----------|----------|---------|
| Customer ID | Settings > Account | `c_abc123` |
| Zone Name | Zone overview tab | `web_unlocker1` |
| Zone Password | Zone overview tab | `z_pass_xyz` |
| API Token | Settings > API tokens | `abc123def456` |

### Step 2: Configure Environment Variables

```bash
# .env (NEVER commit to git)
BRIGHTDATA_CUSTOMER_ID=c_abc123
BRIGHTDATA_ZONE=web_unlocker1
BRIGHTDATA_ZONE_PASSWORD=z_pass_xyz
BRIGHTDATA_API_TOKEN=abc123def456

# .gitignore — add these
echo '.env' >> .gitignore
echo '.env.local' >> .gitignore
```

### Step 3: Download Bright Data SSL Certificate

Required for HTTPS proxy connections through the super proxy:

```bash
curl -sO https://brightdata.com/ssl/brd-ca.crt

# Node.js — set environment variable
export NODE_EXTRA_CA_CERTS=./brd-ca.crt
```

### Step 4: Install HTTP Libraries

```bash
# Node.js
npm install axios dotenv

# Python
pip install requests python-dotenv
```

### Step 5: Verify Connection

```typescript
// verify-brightdata.ts
import axios from 'axios';
import https from 'https';
import 'dotenv/config';

const { BRIGHTDATA_CUSTOMER_ID, BRIGHTDATA_ZONE, BRIGHTDATA_ZONE_PASSWORD } = process.env;

const proxy = {
  host: 'brd.superproxy.io',
  port: 33335,
  auth: {
    username: `brd-customer-${BRIGHTDATA_CUSTOMER_ID}-zone-${BRIGHTDATA_ZONE}`,
    password: BRIGHTDATA_ZONE_PASSWORD!,
  },
};

async function verify() {
  const res = await axios.get('https://lumtest.com/myip.json', {
    proxy,
    httpsAgent: new https.Agent({ rejectUnauthorized: false }),
  });
  console.log('Proxy IP:', res.data.ip);
  console.log('Country:', res.data.country);
  console.log('Connection verified.');
}

verify().catch(console.error);
```

```python
# verify_brightdata.py
import os, requests
from dotenv import load_dotenv

load_dotenv()
proxy_url = (
    f"http://brd-customer-{os.environ['BRIGHTDATA_CUSTOMER_ID']}"
    f"-zone-{os.environ['BRIGHTDATA_ZONE']}"
    f":{os.environ['BRIGHTDATA_ZONE_PASSWORD']}"
    f"@brd.superproxy.io:33335"
)
resp = requests.get(
    'https://lumtest.com/myip.json',
    proxies={'https': proxy_url},
    verify='./brd-ca.crt',
)
print(f"Proxy IP: {resp.json()['ip']}, Country: {resp.json()['country']}")
```

## Output

- `.env` file with zone credentials (git-ignored)
- `brd-ca.crt` SSL certificate for HTTPS proxying
- Successful proxy connection showing rotated IP and country

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `407 Proxy Authentication Required` | Wrong username format | Use `brd-customer-{ID}-zone-{ZONE}` |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Missing CA cert | Download `brd-ca.crt` |
| `ECONNREFUSED` on port 33335 | Firewall blocking | Allow outbound TCP to `brd.superproxy.io:33335` |
| `403 Forbidden` | Zone not active | Activate zone in control panel |

## Resources

- [Bright Data Control Panel](https://brightdata.com/cp)
- [Proxy Setup Docs](https://docs.brightdata.com/general/account/proxy-infrastructure)
- [SSL Certificate](https://docs.brightdata.com/general/account/ssl-certificate)

## Next Steps

After successful auth, proceed to `brightdata-hello-world` for your first scraping request.
