---
name: alchemy-ci-integration
description: |
  Configure CI/CD pipeline for Alchemy-powered Web3 applications.
  Use when setting up automated testing with Hardhat forks,
  smart contract verification, or testnet deployment pipelines.
  Trigger: "alchemy CI", "alchemy GitHub Actions", "web3 CI/CD pipeline".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, ci-cd]
compatible-with: claude-code
---

# Alchemy CI Integration

## Overview

CI/CD pipeline for Alchemy-powered dApps with Hardhat mainnet fork testing, Sepolia deployment, and contract verification.

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/web3-ci.yml
name: Web3 CI

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - name: Run Hardhat tests with Alchemy fork
        env:
          ALCHEMY_API_KEY: ${{ secrets.ALCHEMY_API_KEY }}
        run: npx hardhat test
      - name: Check API key not in build
        run: |
          npm run build
          if grep -r "${{ secrets.ALCHEMY_API_KEY }}" dist/ 2>/dev/null; then
            echo "FAIL: API key found in build output!"
            exit 1
          fi

  deploy-testnet:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - name: Deploy to Sepolia
        env:
          ALCHEMY_API_KEY: ${{ secrets.ALCHEMY_API_KEY }}
          DEPLOYER_PRIVATE_KEY: ${{ secrets.DEPLOYER_PRIVATE_KEY }}
        run: npx hardhat run scripts/deploy.ts --network sepolia
```

### Step 2: Fork Test Configuration

```typescript
// hardhat.config.ts — CI-optimized
const config = {
  solidity: '0.8.24',
  networks: {
    hardhat: {
      forking: {
        url: `https://eth-mainnet.g.alchemy.com/v2/${process.env.ALCHEMY_API_KEY}`,
        blockNumber: 19000000,  // Pinned for reproducible CI
        enabled: !!process.env.ALCHEMY_API_KEY,
      },
    },
  },
  mocha: {
    timeout: 60000,  // Fork tests are slower
  },
};
```

## Output

- GitHub Actions with fork-based tests and testnet deployment
- API key exposure scanning in build output
- Pinned block number for reproducible CI results

## Resources

- [Alchemy Docs](https://www.alchemy.com/docs)
- [Hardhat Testing](https://hardhat.org/hardhat-runner/docs/guides/test-contracts)

## Next Steps

For deployment procedures, see `alchemy-deploy-integration`.
