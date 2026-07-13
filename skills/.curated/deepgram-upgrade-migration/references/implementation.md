# Deepgram Upgrade Migration - Implementation Details

## SDK v2 to v3 Migration

```typescript
// v2 (old)
import Deepgram from '@deepgram/sdk';
const deepgram = new Deepgram(apiKey);
const response = await deepgram.transcription.preRecorded({ url: audioUrl }, { punctuate: true });

// v3 (new)
import { createClient } from '@deepgram/sdk';
const deepgram = createClient(apiKey);
const { result, error } = await deepgram.listen.prerecorded.transcribeUrl({ url: audioUrl }, { punctuate: true });
```

## Breaking Changes Checklist

```typescript
const v3MigrationChecks = [
  { name: 'Import statement', fix: 'Change: import Deepgram from "@deepgram/sdk" to import { createClient } from "@deepgram/sdk"' },
  { name: 'Client initialization', fix: 'Change: new Deepgram(key) to createClient(key)' },
  { name: 'Transcription method', fix: 'Change: deepgram.transcription.preRecorded() to deepgram.listen.prerecorded.transcribeUrl()' },
  { name: 'Response handling', fix: 'Change: const response = await ... to const { result, error } = await ...' },
  { name: 'Error handling', fix: 'Handle error in destructured response instead of try/catch only' },
];

export function runMigrationChecks() {
  console.log('=== SDK v3 Migration Checklist ===\n');
  for (const check of v3MigrationChecks) {
    console.log(`[ ] ${check.name}`);
    console.log(`    Fix: ${check.fix}\n`);
  }
}
```

## Model Migration: Nova to Nova-2

```typescript
const modelComparison = {
  'nova': { accuracy: 'Good', speed: 'Fast', languages: 36, deprecated: false },
  'nova-2': { accuracy: 'Best', speed: 'Fast', languages: 47, deprecated: false },
};

// Migration is simple - just change the model parameter
const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
  { url: audioUrl },
  { model: 'nova-2', smart_format: true, punctuate: true, diarize: true }
);
```

## A/B Testing Models

```typescript
export async function compareModels(audioUrl: string, models: string[] = ['nova', 'nova-2']) {
  const client = createClient(process.env.DEEPGRAM_API_KEY!);
  const results = [];

  for (const model of models) {
    const startTime = Date.now();
    const { result, error } = await client.listen.prerecorded.transcribeUrl({ url: audioUrl }, { model, smart_format: true });
    if (error) { console.error(`Error with model ${model}:`, error); continue; }

    const alternative = result.results.channels[0].alternatives[0];
    results.push({ model, transcript: alternative.transcript, confidence: alternative.confidence, processingTime: Date.now() - startTime });
  }

  // Find best model
  const best = results.reduce((a, b) => a.confidence > b.confidence ? a : b);
  console.log(`Best Model: ${best.model} (${(best.confidence * 100).toFixed(2)}% confidence)`);
  return results;
}
```

## Rollback Manager

```typescript
interface DeploymentVersion {
  sdkVersion: string;
  model: string;
  config: Record<string, unknown>;
  deployedAt: Date;
}

class RollbackManager {
  private versions: DeploymentVersion[] = [];

  recordDeployment(version: Omit<DeploymentVersion, 'deployedAt'>) {
    this.versions.unshift({ ...version, deployedAt: new Date() });
    this.versions = this.versions.slice(0, 5);
  }

  getLastStableVersion(): DeploymentVersion | null { return this.versions[1] || null; }

  getRollbackInstructions(target: DeploymentVersion): string[] {
    return [
      `1. Update package.json: "@deepgram/sdk": "${target.sdkVersion}"`,
      `2. Run: npm install`,
      `3. Update config: model = "${target.model}"`,
      `4. Verify: npm test`,
      `5. Deploy: npm run deploy`,
      `6. Monitor: Check dashboards for 30 minutes`,
    ];
  }
}
```

## Emergency Rollback Script

```bash
#!/bin/bash
set -e
echo "=== Emergency Rollback ==="
CURRENT_VERSION=$(npm list @deepgram/sdk --json | jq -r '.dependencies["@deepgram/sdk"].version')
echo "Current version: $CURRENT_VERSION"
git show HEAD~1:package-lock.json > /tmp/prev-lock.json
PREV_VERSION=$(cat /tmp/prev-lock.json | jq -r '.packages["node_modules/@deepgram/sdk"].version')
echo "Rolling back to: $PREV_VERSION"
npm install @deepgram/sdk@$PREV_VERSION --save-exact
npm test
echo "Rollback complete. Deploy when ready."
```

## Migration Validation

```typescript
async function validateMigration() {
  const results = [];
  const client = createClient(process.env.DEEPGRAM_API_KEY!);

  // Test 1: API connectivity
  try {
    const { error } = await client.manage.getProjects();
    results.push({ test: 'API Connectivity', passed: !error, details: error?.message });
  } catch (err) {
    results.push({ test: 'API Connectivity', passed: false, details: err instanceof Error ? err.message : 'Unknown' });
  }

  // Test 2: Pre-recorded transcription
  try {
    const { result, error } = await client.listen.prerecorded.transcribeUrl(
      { url: 'https://static.deepgram.com/examples/nasa-podcast.wav' },
      { model: 'nova-2', smart_format: true }
    );
    results.push({ test: 'Pre-recorded Transcription', passed: !error && !!result?.results?.channels?.[0]?.alternatives?.[0]?.transcript });
  } catch (err) {
    results.push({ test: 'Pre-recorded Transcription', passed: false, details: err instanceof Error ? err.message : 'Unknown' });
  }

  // Test 3: Live transcription connection
  try {
    const connection = client.listen.live({ model: 'nova-2' });
    await new Promise<void>((resolve, reject) => {
      connection.on('open', () => { connection.finish(); resolve(); });
      connection.on('error', reject);
      setTimeout(() => reject(new Error('Timeout')), 10000);
    });
    results.push({ test: 'Live Transcription', passed: true });
  } catch (err) {
    results.push({ test: 'Live Transcription', passed: false, details: err instanceof Error ? err.message : 'Unknown' });
  }

  const allPassed = results.every(r => r.passed);
  process.exit(allPassed ? 0 : 1);
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
