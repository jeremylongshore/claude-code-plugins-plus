# Systematic Isolation

## Systematic Isolation

### Layer-by-Layer Testing

```typescript
// Test each layer independently
async function diagnoseVercelIssue(): Promise<DiagnosisReport> {
  const results: DiagnosisResult[] = [];

  // Layer 1: Network connectivity
  results.push(await testNetworkConnectivity());

  // Layer 2: DNS resolution
  results.push(await testDNSResolution('api.vercel.com'));

  // Layer 3: TLS handshake
  results.push(await testTLSHandshake('api.vercel.com'));

  // Layer 4: Authentication
  results.push(await testAuthentication());

  // Layer 5: API response
  results.push(await testAPIResponse());

  // Layer 6: Response parsing
  results.push(await testResponseParsing());

  return { results, firstFailure: results.find(r => !r.success) };
}
```

### Minimal Reproduction

```typescript
// Strip down to absolute minimum
async function minimalRepro(): Promise<void> {
  // 1. Fresh client, no customization
  const client = new VercelClient({
    apiKey: process.env.VERCEL_API_KEY!,
  });

  // 2. Simplest possible call
  try {
    const result = await client.ping();
    console.log('Ping successful:', result);
  } catch (error) {
    console.error('Ping failed:', {
      message: error.message,
      code: error.code,
      stack: error.stack,
    });
  }
}
```
