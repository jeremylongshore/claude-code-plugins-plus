---
name: deepgram-upgrade-migration
description: |
  Plan and execute Deepgram SDK upgrades and model migrations.
  Use when upgrading SDK versions (v3->v4->v5), migrating models
  (Nova-2 to Nova-3), or planning API version transitions.
  Trigger: "upgrade deepgram", "deepgram migration", "update deepgram SDK",
  "deepgram version upgrade", "nova-3 migration".
allowed-tools: Read, Write, Edit, Grep, Bash(npm:*), Bash(pip:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, api, migration, upgrade]

---
# Deepgram Upgrade Migration

## Current State
!`npm list @deepgram/sdk 2>/dev/null | grep deepgram || echo 'SDK not installed'`

## Overview
Guide for Deepgram SDK version upgrades (v3 -> v4 -> v5) and model migrations (Nova-2 -> Nova-3). Includes breaking change maps, side-by-side API comparison, A/B testing scripts, automated validation, and rollback procedures.

## SDK Version History

| Version | Client Init | STT API | Live API | TTS API | Status |
|---------|------------|---------|----------|---------|--------|
| v3.x | `createClient(key)` | `listen.prerecorded.transcribeUrl()` | `listen.live()` | `speak.request()` | Stable |
| v4.x | `createClient(key)` | `listen.prerecorded.transcribeUrl()` | `listen.live()` | `speak.request()` | Stable |
| v5.x | `new DeepgramClient({apiKey})` | `listen.v1.media.transcribeUrl()` | `listen.v1.connect()` | `speak.v1.audio.generate()` | Beta |

## Instructions

### Step 1: Identify Current Version and Breaking Changes

```bash
# Check installed version
npm list @deepgram/sdk

# Check latest available
npm view @deepgram/sdk versions --json | tail -5
```

### Step 2: v3/v4 to v5 Migration Map

```typescript
// ============= CLIENT CREATION =============
// v3/v4:
import { createClient } from '@deepgram/sdk';
const dg = createClient(process.env.DEEPGRAM_API_KEY!);

// v5:
import { DeepgramClient } from '@deepgram/sdk';
const dg = new DeepgramClient({ apiKey: process.env.DEEPGRAM_API_KEY });

// ============= PRE-RECORDED STT =============
// v3/v4:
const { result, error } = await dg.listen.prerecorded.transcribeUrl(
  { url: audioUrl },
  { model: 'nova-3', smart_format: true }
);

// v5:
const response = await dg.listen.v1.media.transcribeUrl(
  { url: audioUrl },
  { model: 'nova-3', smart_format: true }
);
// v5 throws on error instead of returning { error }

// ============= FILE TRANSCRIPTION =============
// v3/v4:
const { result, error } = await dg.listen.prerecorded.transcribeFile(
  buffer,
  { model: 'nova-3', mimetype: 'audio/wav' }
);

// v5:
const response = await dg.listen.v1.media.transcribeFile(
  createReadStream('audio.wav'),
  { model: 'nova-3' }
);

// ============= LIVE STREAMING =============
// v3/v4:
const connection = dg.listen.live({ model: 'nova-3', encoding: 'linear16' });
connection.on(LiveTranscriptionEvents.Transcript, (data) => { ... });

// v5:
const connection = await dg.listen.v1.connect({ model: 'nova-3', encoding: 'linear16' });
// Note: v5 connect() is async

// ============= TEXT-TO-SPEECH =============
// v3/v4:
const response = await dg.speak.request(
  { text: 'Hello world' },
  { model: 'aura-2-thalia-en' }
);
const stream = await response.getStream();

// v5:
const response = await dg.speak.v1.audio.generate(
  { text: 'Hello world' },
  { model: 'aura-2-thalia-en' }
);

// ============= ERROR HANDLING =============
// v3/v4: Destructured { result, error }
const { result, error } = await dg.listen.prerecorded.transcribeUrl(src, opts);
if (error) handleError(error);

// v5: try/catch (throws on error)
try {
  const result = await dg.listen.v1.media.transcribeUrl(src, opts);
} catch (err) {
  handleError(err);
}
```

### Step 3: Model Migration (Nova-2 -> Nova-3)

```typescript
// Nova-3 is a drop-in replacement — same API, better accuracy
// Just change the model parameter:

// Before:
{ model: 'nova-2' }

// After:
{ model: 'nova-3' }

// Nova-3 improvements over Nova-2:
// - Higher accuracy across all languages
// - Better handling of accents and dialects
// - Improved punctuation and formatting
// - Same pricing tier
// - Same API parameters
```

### Step 4: A/B Test Models

```typescript
async function compareModels(audioUrl: string) {
  const client = createClient(process.env.DEEPGRAM_API_KEY!);

  const [nova2, nova3] = await Promise.all([
    client.listen.prerecorded.transcribeUrl(
      { url: audioUrl },
      { model: 'nova-2', smart_format: true }
    ),
    client.listen.prerecorded.transcribeUrl(
      { url: audioUrl },
      { model: 'nova-3', smart_format: true }
    ),
  ]);

  const t2 = nova2.result.results.channels[0].alternatives[0];
  const t3 = nova3.result.results.channels[0].alternatives[0];

  console.log('=== Nova-2 ===');
  console.log(`Confidence: ${t2.confidence}`);
  console.log(`Words: ${t2.words?.length}`);
  console.log(`Transcript: ${t2.transcript.substring(0, 200)}...`);

  console.log('\n=== Nova-3 ===');
  console.log(`Confidence: ${t3.confidence}`);
  console.log(`Words: ${t3.words?.length}`);
  console.log(`Transcript: ${t3.transcript.substring(0, 200)}...`);

  // Simple word-level similarity
  const words2 = new Set(t2.transcript.toLowerCase().split(/\s+/));
  const words3 = new Set(t3.transcript.toLowerCase().split(/\s+/));
  const intersection = new Set([...words2].filter(w => words3.has(w)));
  const union = new Set([...words2, ...words3]);
  const similarity = intersection.size / union.size;

  console.log(`\nSimilarity: ${(similarity * 100).toFixed(1)}%`);
  console.log(`Nova-3 confidence delta: ${((t3.confidence - t2.confidence) * 100).toFixed(2)}%`);
}
```

### Step 5: Automated Validation Suite

```typescript
import { describe, it, expect } from 'vitest';
import { createClient } from '@deepgram/sdk';

const SAMPLE_URL = 'https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav';

describe('Deepgram Migration Validation', () => {
  const client = createClient(process.env.DEEPGRAM_API_KEY!);

  it('API key is valid', async () => {
    const { error } = await client.manage.getProjects();
    expect(error).toBeNull();
  });

  it('Pre-recorded transcription works', async () => {
    const { result, error } = await client.listen.prerecorded.transcribeUrl(
      { url: SAMPLE_URL }, { model: 'nova-3', smart_format: true }
    );
    expect(error).toBeNull();
    expect(result.results.channels[0].alternatives[0].transcript).toBeTruthy();
    expect(result.results.channels[0].alternatives[0].confidence).toBeGreaterThan(0.8);
  }, 30000);

  it('Diarization returns speaker labels', async () => {
    const { result } = await client.listen.prerecorded.transcribeUrl(
      { url: SAMPLE_URL }, { model: 'nova-3', diarize: true, utterances: true }
    );
    const words = result.results.channels[0].alternatives[0].words;
    expect(words?.[0]).toHaveProperty('speaker');
  }, 30000);

  it('TTS generates audio', async () => {
    const response = await client.speak.request(
      { text: 'Migration test successful.' },
      { model: 'aura-2-thalia-en' }
    );
    const stream = await response.getStream();
    expect(stream).toBeTruthy();
  }, 15000);
});
```

### Step 6: Rollback Procedure

```bash
# If issues are found after upgrade:

# 1. Revert SDK version
npm install @deepgram/sdk@3.x.x  # Pin to previous working version

# 2. Revert model in config
# Change nova-3 back to nova-2 in environment/config

# 3. Run validation
npx vitest run tests/deepgram-validation.test.ts

# 4. Verify in production
curl -s -X POST 'https://api.deepgram.com/v1/listen?model=nova-2' \
  -H "Authorization: Token $DEEPGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav"}'
```

## Output
- SDK version migration map (v3/v4 -> v5)
- Model migration path (Nova-2 -> Nova-3)
- A/B testing script with similarity scoring
- Automated validation test suite
- Rollback procedure

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `createClient is not a function` | v5 installed | Use `new DeepgramClient()` |
| `listen.prerecorded is undefined` | v5 namespace change | Use `listen.v1.media` |
| Quality regression after model change | Edge case in Nova-3 | A/B test, report to Deepgram, rollback |
| `speak.request is undefined` | v5 namespace change | Use `speak.v1.audio.generate` |

## Resources
- [JS SDK Releases](https://github.com/deepgram/deepgram-js-sdk/releases)
- [Model Options](https://developers.deepgram.com/docs/model)
- [Models & Languages](https://developers.deepgram.com/docs/models-languages-overview)
