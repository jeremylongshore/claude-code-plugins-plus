---
name: alchemy-security-basics
description: |
  Apply Web3 security best practices for Alchemy-powered applications.
  Use when securing API keys, validating blockchain inputs, preventing
  private key exposure, or hardening dApp infrastructure.
  Trigger: "alchemy security", "web3 security", "protect private key",
  "alchemy API key security", "dApp security".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, security]
compatible-with: claude-code
---

# Alchemy Security Basics

## Overview

Web3 security practices for Alchemy-powered applications: API key protection, private key management, input validation, and smart contract interaction safety.

## Security Checklist

| Category | Requirement | Priority |
|----------|------------|----------|
| API keys | Never expose in client-side code | Critical |
| Private keys | Use environment vars or secret manager | Critical |
| Addresses | Validate and checksum all inputs | High |
| RPC calls | Never pass user input directly to RPC | High |
| Webhooks | Verify HMAC signatures | High |
| Dependencies | Audit npm packages for supply chain | Medium |

## Instructions

### Step 1: API Key Protection

```typescript
// WRONG — API key in frontend code
// const alchemy = new Alchemy({ apiKey: 'demo123' }); // NEVER DO THIS

// RIGHT — API key in backend proxy
// src/api/proxy.ts
import express from 'express';
import { Alchemy, Network } from 'alchemy-sdk';

const app = express();
const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY, // Server-side only
  network: Network.ETH_MAINNET,
});

// Proxy endpoint — frontend calls this instead of Alchemy directly
app.get('/api/balance/:address', async (req, res) => {
  const { address } = req.params;
  if (!/^0x[a-fA-F0-9]{40}$/.test(address)) {
    return res.status(400).json({ error: 'Invalid address format' });
  }
  const balance = await alchemy.core.getBalance(address);
  res.json({ balance: balance.toString() });
});

// Alchemy Dashboard: restrict API key to specific domains/IPs
// Dashboard > App > Settings > Allowed Domains
```

### Step 2: Input Validation for Blockchain Queries

```typescript
// src/security/validators.ts
import { ethers } from 'ethers';

function validateAddress(input: string): string {
  if (!ethers.isAddress(input)) throw new Error(`Invalid address: ${input}`);
  return ethers.getAddress(input); // Returns checksummed address
}

function validateBlockNumber(input: string | number): string {
  if (input === 'latest' || input === 'pending' || input === 'earliest') return input;
  const num = typeof input === 'string' ? parseInt(input) : input;
  if (isNaN(num) || num < 0) throw new Error(`Invalid block number: ${input}`);
  return `0x${num.toString(16)}`;
}

function validateTokenId(input: string): string {
  if (!/^\d+$/.test(input) && !input.startsWith('0x')) {
    throw new Error(`Invalid token ID: ${input}`);
  }
  return input;
}

export { validateAddress, validateBlockNumber, validateTokenId };
```

### Step 3: Private Key Safety

```typescript
// src/security/wallet-safety.ts
// NEVER:
// - Hardcode private keys in source code
// - Log private keys or mnemonic phrases
// - Store private keys in .env files committed to git
// - Accept private keys from user input in a web app

// Safe wallet setup for server-side operations
import { ethers } from 'ethers';
import { Alchemy, Network } from 'alchemy-sdk';

async function createSafeWallet() {
  const alchemy = new Alchemy({
    apiKey: process.env.ALCHEMY_API_KEY,
    network: Network.ETH_SEPOLIA,
  });

  const provider = await alchemy.config.getProvider();

  // Load private key from secret manager (GCP example)
  const { SecretManagerServiceClient } = await import('@google-cloud/secret-manager');
  const client = new SecretManagerServiceClient();
  const [version] = await client.accessSecretVersion({
    name: `projects/${process.env.GCP_PROJECT}/secrets/deployer-private-key/versions/latest`,
  });
  const privateKey = version.payload?.data?.toString() || '';

  const wallet = new ethers.Wallet(privateKey, provider);
  return wallet;
}
```

### Step 4: Webhook Signature Verification

```typescript
// src/security/webhook-verify.ts
import crypto from 'crypto';

function verifyAlchemyWebhookSignature(
  body: string,
  signature: string,
  signingKey: string,
): boolean {
  const hmac = crypto.createHmac('sha256', signingKey);
  hmac.update(body, 'utf8');
  const expectedSig = hmac.digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSig),
  );
}
```

## Output

- API key proxy pattern (never expose to client)
- Input validation for addresses, blocks, and token IDs
- Private key loaded from secret manager
- Webhook HMAC signature verification

## Resources

- [Alchemy Security Best Practices](https://www.alchemy.com/docs)
- [Ethers.js Security](https://docs.ethers.org/v6/)
- [Web3 Security Checklist](https://www.alchemy.com/docs/reference/security)

## Next Steps

For production deployment, see `alchemy-prod-checklist`.
