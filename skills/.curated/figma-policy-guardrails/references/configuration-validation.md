# Step 4: Configuration Validation

Deep-dive reference for the `figma-policy-guardrails` skill — extracted from the 'Step 4: Configuration Validation' step of the workflow.

```typescript
// Validate Figma config at startup, fail fast if misconfigured
function validateFigmaConfig() {
  const errors: string[] = [];

  // Token format
  const pat = process.env.FIGMA_PAT;
  if (!pat) {
    errors.push('FIGMA_PAT is not set');
  } else if (!pat.startsWith('figd_')) {
    errors.push('FIGMA_PAT does not have expected figd_ prefix');
  }

  // File key format
  const fileKey = process.env.FIGMA_FILE_KEY;
  if (!fileKey) {
    errors.push('FIGMA_FILE_KEY is not set');
  } else if (fileKey.length < 10) {
    errors.push('FIGMA_FILE_KEY seems too short');
  }

  // Webhook passcode (if webhooks are configured)
  if (process.env.FIGMA_WEBHOOK_ENABLED === 'true') {
    if (!process.env.FIGMA_WEBHOOK_PASSCODE) {
      errors.push('FIGMA_WEBHOOK_PASSCODE required when webhooks are enabled');
    } else if (process.env.FIGMA_WEBHOOK_PASSCODE.length < 16) {
      errors.push('FIGMA_WEBHOOK_PASSCODE should be at least 16 characters');
    }
  }

  if (errors.length > 0) {
    console.error('[figma-policy] Configuration errors:');
    errors.forEach(e => console.error(`  - ${e}`));
    throw new Error(`Figma configuration invalid: ${errors.length} errors`);
  }

  console.log('[figma-policy] Configuration validated');
}

// Call at startup
validateFigmaConfig();
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
