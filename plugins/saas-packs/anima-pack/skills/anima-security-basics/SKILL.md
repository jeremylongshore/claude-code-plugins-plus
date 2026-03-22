---
name: anima-security-basics
description: |
  Secure Anima and Figma tokens for design-to-code pipelines.
  Use when protecting API credentials, restricting Figma access scope,
  or hardening CI/CD design automation pipelines.
  Trigger: "anima security", "anima token safety", "figma token security".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, security]
compatible-with: claude-code
---

# Anima Security Basics

## Security Checklist

- [ ] Anima token stored in secret manager (not .env in prod)
- [ ] Figma PAT has minimum required scope (file:read only)
- [ ] SDK runs server-side only (never ship tokens to browser)
- [ ] `.env` files gitignored and chmod 600
- [ ] CI secrets stored in GitHub Secrets, not workflow files
- [ ] Generated code reviewed before committing (no embedded tokens)

## Instructions

### Step 1: Figma Token Scope Restriction

```bash
# When creating a Figma Personal Access Token:
# - Give it the MINIMUM scope needed: File Content (read-only)
# - Do NOT grant write access unless you need Figma plugin features
# - Set an expiration date (90 days recommended)
# - Create separate tokens for dev vs CI environments
```

### Step 2: Server-Side Only Enforcement

```typescript
// src/anima/safety.ts
// Anima SDK is designed for server-side use only

function validateEnvironment(): void {
  if (typeof window !== 'undefined') {
    throw new Error('Anima SDK must run server-side only — never import in browser code');
  }
  if (!process.env.ANIMA_TOKEN) throw new Error('ANIMA_TOKEN not set');
  if (!process.env.FIGMA_TOKEN) throw new Error('FIGMA_TOKEN not set');
}

// Call this at startup
validateEnvironment();
```

### Step 3: Secret Manager Integration

```typescript
// src/anima/secrets.ts
async function loadAnimaSecrets(): Promise<{ animaToken: string; figmaToken: string }> {
  const { SecretManagerServiceClient } = await import('@google-cloud/secret-manager');
  const client = new SecretManagerServiceClient();

  const [animaVersion] = await client.accessSecretVersion({
    name: `projects/${process.env.GCP_PROJECT}/secrets/anima-token/versions/latest`,
  });
  const [figmaVersion] = await client.accessSecretVersion({
    name: `projects/${process.env.GCP_PROJECT}/secrets/figma-token/versions/latest`,
  });

  return {
    animaToken: animaVersion.payload?.data?.toString() || '',
    figmaToken: figmaVersion.payload?.data?.toString() || '',
  };
}
```

## Output

- Figma token with minimal scope (read-only)
- Server-side enforcement preventing browser usage
- Secrets loaded from cloud secret manager

## Resources

- [Figma Access Tokens](https://www.figma.com/developers/api#access-tokens)
- [GCP Secret Manager](https://cloud.google.com/secret-manager)

## Next Steps

For production deployment, see `anima-prod-checklist`.
