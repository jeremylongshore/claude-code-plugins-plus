---
name: alchemy-prod-checklist
description: |
  Execute production readiness checklist for Alchemy-powered dApps.
  Use when deploying Web3 applications, preparing for mainnet launch,
  or validating blockchain integration before go-live.
  Trigger: "alchemy production", "alchemy go-live", "alchemy mainnet checklist",
  "dApp production readiness".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, production]
compatible-with: claude-code
---

# Alchemy Production Checklist

## Pre-Launch Checklist

### API & Infrastructure
- [ ] API key restricted to production domains in Alchemy Dashboard
- [ ] Separate Alchemy apps for dev/staging/prod environments
- [ ] Rate limit headroom verified (< 70% of CU/sec budget)
- [ ] Retry logic with exponential backoff implemented
- [ ] Error monitoring configured (Sentry, Datadog, etc.)
- [ ] Webhook endpoints HTTPS-only with signature verification

### Security
- [ ] API key NOT in frontend code — proxied through backend
- [ ] Private keys in secret manager (not env files)
- [ ] All user-supplied addresses validated and checksummed
- [ ] No `console.log` of sensitive data in production builds
- [ ] npm audit clean — no critical vulnerabilities

### Smart Contracts (if applicable)
- [ ] Contracts audited by reputable firm
- [ ] Deployed and verified on Etherscan/Polygonscan
- [ ] Admin keys secured in multi-sig wallet
- [ ] Emergency pause function tested

### Performance
- [ ] Response caching for frequently-queried data (balances, metadata)
- [ ] Connection pooling for provider instances
- [ ] Batch requests where possible (NFT metadata, balances)
- [ ] WebSocket reconnection logic for real-time subscriptions

### Validation Script

```typescript
// src/prod/readiness.ts
import { Alchemy, Network } from 'alchemy-sdk';

async function checkReadiness(): Promise<void> {
  const checks: Array<{ name: string; pass: boolean; detail: string }> = [];

  // 1. API connectivity
  const alchemy = new Alchemy({ apiKey: process.env.ALCHEMY_API_KEY, network: Network.ETH_MAINNET });
  try {
    const block = await alchemy.core.getBlockNumber();
    checks.push({ name: 'API Connectivity', pass: true, detail: `Block ${block}` });
  } catch (err: any) {
    checks.push({ name: 'API Connectivity', pass: false, detail: err.message });
  }

  // 2. Enhanced API
  try {
    await alchemy.core.getTokenBalances('0x0000000000000000000000000000000000000000');
    checks.push({ name: 'Enhanced API', pass: true, detail: 'getTokenBalances works' });
  } catch { checks.push({ name: 'Enhanced API', pass: false, detail: 'Enhanced API unavailable' }); }

  // 3. NFT API
  try {
    await alchemy.nft.getContractMetadata('0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D');
    checks.push({ name: 'NFT API', pass: true, detail: 'getContractMetadata works' });
  } catch { checks.push({ name: 'NFT API', pass: false, detail: 'NFT API unavailable' }); }

  // 4. API key not in build output
  const fs = await import('fs');
  const buildDir = './dist';
  if (fs.existsSync(buildDir)) {
    const content = fs.readdirSync(buildDir, { recursive: true })
      .filter((f: any) => f.toString().endsWith('.js'))
      .map((f: any) => fs.readFileSync(`${buildDir}/${f}`, 'utf8'))
      .join('');
    const apiKeyExposed = content.includes(process.env.ALCHEMY_API_KEY || '');
    checks.push({ name: 'API Key Safety', pass: !apiKeyExposed, detail: apiKeyExposed ? 'CRITICAL: API key found in build!' : 'API key not in build' });
  }

  // Print results
  console.log('\n=== Alchemy Production Readiness ===\n');
  for (const c of checks) {
    console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
  }
  const failures = checks.filter(c => !c.pass);
  console.log(`\n${failures.length === 0 ? 'READY FOR PRODUCTION' : `${failures.length} BLOCKING ISSUES`}`);
}

checkReadiness().catch(console.error);
```

## Output

- All checklist items validated
- Readiness script with pass/fail reporting
- API key exposure scan in build output
- Multi-network connectivity verified

## Resources

- [Alchemy Docs](https://www.alchemy.com/docs)
- [Alchemy Dashboard](https://dashboard.alchemy.com)

## Next Steps

For version upgrades, see `alchemy-upgrade-migration`.
