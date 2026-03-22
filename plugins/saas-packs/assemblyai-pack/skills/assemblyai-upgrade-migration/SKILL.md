---
name: assemblyai-upgrade-migration
description: |
  Analyze, plan, and execute AssemblyAI SDK upgrades with breaking change detection.
  Use when upgrading the assemblyai npm package, migrating from the old SDK,
  or switching between speech models (Best, Nano, Universal).
  Trigger with phrases like "upgrade assemblyai", "assemblyai migration",
  "assemblyai breaking changes", "update assemblyai SDK".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription]
compatible-with: claude-code
---

# AssemblyAI Upgrade & Migration

## Overview
Guide for upgrading the `assemblyai` npm package and migrating between SDK versions, including the major v3 to v4 migration and speech model transitions.

## Prerequisites
- Current `assemblyai` package installed
- Git for version control
- Test suite available

## Instructions

### Step 1: Check Current Version

```bash
# Check installed version
npm list assemblyai

# Check latest available version
npm view assemblyai version

# See what changed
npm view assemblyai --json | jq '.versions[-5:]'
```

### Step 2: Review Changelog

```bash
# View release notes
open https://github.com/AssemblyAI/assemblyai-node-sdk/releases

# Or check from CLI
gh release list --repo AssemblyAI/assemblyai-node-sdk --limit 10
```

### Step 3: Create Upgrade Branch

```bash
git checkout -b upgrade/assemblyai-sdk-v$(npm view assemblyai version)
npm install assemblyai@latest
npm test
```

### Step 4: Major Migration — Old SDK to Current (v4.x)

If migrating from `@assemblyai/sdk` (old package) to `assemblyai` (current):

```typescript
// BEFORE (old package — @assemblyai/sdk)
import { AssemblyAI as OldClient } from '@assemblyai/sdk';
const client = new OldClient({ apiKey: '...' });

// AFTER (current package — assemblyai)
import { AssemblyAI } from 'assemblyai';
const client = new AssemblyAI({ apiKey: '...' });
```

```bash
# Remove old package, install new
npm uninstall @assemblyai/sdk
npm install assemblyai
```

**Key changes in the migration:**

| Old (`@assemblyai/sdk`) | New (`assemblyai`) |
|--------------------------|---------------------|
| `import { AssemblyAI } from '@assemblyai/sdk'` | `import { AssemblyAI } from 'assemblyai'` |
| `client.transcripts.create()` | `client.transcripts.transcribe()` (blocks until done) |
| Manual polling with `client.transcripts.get()` | `transcribe()` auto-polls, `submit()` for manual control |
| `RealtimeTranscriber` class | `client.streaming.createService()` |
| `client.realtime.createTemporaryToken()` | `client.streaming.createTemporaryToken()` |

### Step 5: Transcription Method Changes

```typescript
// v3 pattern: create + poll loop
const job = await client.transcripts.create({ audio_url: url });
let transcript;
while (true) {
  transcript = await client.transcripts.get(job.id);
  if (transcript.status === 'completed' || transcript.status === 'error') break;
  await new Promise(r => setTimeout(r, 3000));
}

// v4 pattern: transcribe() handles everything
const transcript = await client.transcripts.transcribe({
  audio: url,  // Note: 'audio' not 'audio_url'
});

// v4 pattern: submit() for webhook-based (no polling)
const submitted = await client.transcripts.submit({
  audio: url,
  webhook_url: 'https://your-app.com/webhook',
});
```

### Step 6: Streaming Migration

```typescript
// v3 pattern: RealtimeTranscriber class
import { RealtimeTranscriber } from 'assemblyai';
const rt = new RealtimeTranscriber({ apiKey: '...' });
rt.on('transcript', (msg) => { /* ... */ });
await rt.connect();

// v4 pattern: client.streaming.createService()
const transcriber = client.streaming.createService({
  speech_model: 'nova-3',
  sample_rate: 16000,
});
transcriber.on('transcript', (msg) => { /* ... */ });
await transcriber.connect();
```

### Step 7: Speech Model Migration

```typescript
// Switch from legacy models to Universal-3
const transcript = await client.transcripts.transcribe({
  audio: audioUrl,
  speech_model: 'best',    // Uses Universal-3 (highest accuracy)
  // Other options: 'nano' (fastest, lowest cost)
  // Note: 'best' supports word_boost (up to 1000 terms)
});

// For streaming: nova-3 or nova-3-pro
const transcriber = client.streaming.createService({
  speech_model: 'nova-3-pro',  // Most accurate streaming model
  sample_rate: 16000,
});
```

### Step 8: Verify After Upgrade

```typescript
import { AssemblyAI } from 'assemblyai';

async function verifyUpgrade() {
  const client = new AssemblyAI({ apiKey: process.env.ASSEMBLYAI_API_KEY! });

  // Test async transcription
  const transcript = await client.transcripts.transcribe({
    audio: 'https://storage.googleapis.com/aai-web-samples/5_common_sports_702.wav',
  });
  console.assert(transcript.status === 'completed', 'Transcription should complete');
  console.assert(transcript.text && transcript.text.length > 0, 'Should have text');

  // Test LeMUR
  const { response } = await client.lemur.task({
    transcript_ids: [transcript.id],
    prompt: 'What is this about? Reply in one sentence.',
  });
  console.assert(response.length > 0, 'LeMUR should respond');

  // Test transcript listing
  const page = await client.transcripts.list({ limit: 1 });
  console.assert(page.transcripts.length > 0, 'Should list transcripts');

  console.log('All checks passed.');
}

verifyUpgrade().catch(console.error);
```

## Output
- Updated `assemblyai` package to latest version
- Migrated import paths and method calls
- Updated streaming setup to current patterns
- Verified all API endpoints work post-upgrade

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `Cannot find module 'assemblyai'` | Old package name | `npm uninstall @assemblyai/sdk && npm install assemblyai` |
| `transcripts.create is not a function` | API changed in v4 | Use `transcripts.transcribe()` or `transcripts.submit()` |
| `audio_url` not recognized | Parameter renamed | Use `audio` instead of `audio_url` |
| Streaming not connecting | API changed | Use `client.streaming.createService()` |
| TypeScript errors | Type definitions changed | Update imports to match new types |

## Resources
- [AssemblyAI Node SDK Releases](https://github.com/AssemblyAI/assemblyai-node-sdk/releases)
- [AssemblyAI SDK Migration Guide](https://github.com/AssemblyAI/assemblyai-node-sdk/blob/main/MIGRATION.md)
- [AssemblyAI npm Package](https://www.npmjs.com/package/assemblyai)

## Next Steps
For CI integration during upgrades, see `assemblyai-ci-integration`.
