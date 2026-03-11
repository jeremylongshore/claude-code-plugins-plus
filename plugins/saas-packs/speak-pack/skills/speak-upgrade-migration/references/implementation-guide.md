# Speak Upgrade Migration - Implementation Guide

Detailed implementation reference for the speak-upgrade-migration skill.

## Instructions

### Step 1: Check Current Version
```bash
# Check installed version
npm list @speak/language-sdk

# Check latest available version
npm view @speak/language-sdk version

# Check for updates
npm outdated @speak/language-sdk
```

### Step 2: Review Changelog
```bash
# Open changelog
open https://github.com/speak/language-sdk/releases

# Or check locally if available
cat node_modules/@speak/language-sdk/CHANGELOG.md
```

### Step 3: Create Upgrade Branch
```bash
git checkout -b upgrade/speak-sdk-vX.Y.Z

# Install new version
npm install @speak/language-sdk@latest

# Run tests
npm test
```

### Step 4: Handle Common Breaking Changes

#### SDK Version History
| SDK Version | API Version | Node.js | Key Changes |
|-------------|-------------|---------|-------------|
| 3.x | 2025-01 | 20+ | Real-time API, new speech engine |
| 2.x | 2024-01 | 18+ | Async/await patterns, TypeScript |
| 1.x | 2023-01 | 16+ | Initial release |

#### Import Changes (v1 to v2)
```typescript
// Before (v1.x)
import { Client, Lesson } from 'speak-sdk';
const client = new Client({ key: 'xxx' });

// After (v2.x)
import { SpeakClient, LessonSession } from '@speak/language-sdk';
const client = new SpeakClient({
  apiKey: 'xxx',
  appId: 'app_xxx',
});
```

#### Session API Changes (v2 to v3)
```typescript
// Before (v2.x) - Promise-based
const session = await tutor.startLesson({ topic: 'greetings' });
const feedback = await session.submitResponse({ text: 'Hola' });

// After (v3.x) - Real-time streams
const session = tutor.createLessonStream({ topic: 'greetings' });
session.on('prompt', (prompt) => console.log(prompt));
session.on('feedback', (feedback) => console.log(feedback));
await session.send({ text: 'Hola', audio: audioBuffer });
```

#### Speech Recognition Changes
```typescript
// Before (v2.x)
const result = await client.speech.recognize(audioBuffer);

// After (v3.x) - Streaming recognition
const recognizer = client.speech.createRecognizer({
  language: 'es',
  continuous: true,
});
recognizer.on('result', (result) => {
  console.log('Partial:', result.partial);
  console.log('Final:', result.final);
});
recognizer.start(audioStream);
```

### Step 5: Migration Script

```typescript
// scripts/migrate-speak-v3.ts
import { readdir, readFile, writeFile } from 'fs/promises';
import { join } from 'path';

const MIGRATIONS = [
  {
    pattern: /from 'speak-sdk'/g,
    replacement: "from '@speak/language-sdk'",
    description: 'Update import path',
  },
  {
    pattern: /new Client\(/g,
    replacement: 'new SpeakClient(',
    description: 'Rename Client to SpeakClient',
  },
  {
    pattern: /{ key:/g,
    replacement: '{ apiKey:',
    description: 'Rename key to apiKey',
  },
  {
    pattern: /\.startLesson\(/g,
    replacement: '.createLessonStream(',
    description: 'Update to streaming API',
  },
];

async function migrateFile(filePath: string): Promise<void> {
  let content = await readFile(filePath, 'utf-8');
  let modified = false;

  for (const migration of MIGRATIONS) {
    if (migration.pattern.test(content)) {
      console.log(`  Applying: ${migration.description}`);
      content = content.replace(migration.pattern, migration.replacement);
      modified = true;
    }
  }

  if (modified) {
    await writeFile(filePath, content);
    console.log(`  ✓ Updated: ${filePath}`);
  }
}

async function migrateProject(dir: string): Promise<void> {
  const files = await readdir(dir, { withFileTypes: true, recursive: true });

  for (const file of files) {
    if (file.isFile() && /\.(ts|tsx|js|jsx)$/.test(file.name)) {
      const filePath = join(file.parentPath, file.name);
      await migrateFile(filePath);
    }
  }
}

migrateProject('./src');
```

### Step 6: Update Type Definitions

```typescript
// types/speak-v3.d.ts

// Old types that changed
interface LegacySession {
  submitResponse(response: { text: string }): Promise<Feedback>;
}

// New streaming types
interface LessonStream {
  on(event: 'prompt', callback: (prompt: TutorPrompt) => void): void;
  on(event: 'feedback', callback: (feedback: Feedback) => void): void;
  on(event: 'error', callback: (error: SpeakError) => void): void;
  send(input: LessonInput): Promise<void>;
  close(): Promise<SessionSummary>;
}

// Adapter for gradual migration
class SessionAdapter {
  private stream: LessonStream;
  private feedbackPromise: Promise<Feedback> | null = null;

  constructor(stream: LessonStream) {
    this.stream = stream;
  }

  // Provide v2-style API on top of v3 streams
  async submitResponse(response: { text: string }): Promise<Feedback> {
    return new Promise((resolve, reject) => {
      this.stream.on('feedback', resolve);
      this.stream.on('error', reject);
      this.stream.send(response);
    });
  }
}
```


## Deprecation Handling

```typescript
// Monitor for deprecation warnings
if (process.env.NODE_ENV === 'development') {
  process.on('warning', (warning) => {
    if (warning.name === 'DeprecationWarning' && warning.message.includes('speak')) {
      console.warn('[Speak SDK]', warning.message);

      // Log to tracking for proactive updates
      trackDeprecation({
        message: warning.message,
        stack: warning.stack,
        version: process.env.SPEAK_SDK_VERSION,
      });
    }
  });
}

// Graceful handling of deprecated features
async function getLesson(config: LessonConfig) {
  const client = getSpeakClient();

  // Check if using deprecated API
  if ('startLesson' in client.tutor) {
    console.warn('Using deprecated startLesson API. Update to createLessonStream.');
    // @ts-ignore - Deprecated but still works
    return await client.tutor.startLesson(config);
  }

  // New API
  return client.tutor.createLessonStream(config);
}
```


## Rollback Procedure

```bash
# If upgrade fails, rollback to previous version
npm install @speak/language-sdk@2.x.x --save-exact

# Verify rollback
npm list @speak/language-sdk
npm test
```


## Testing Upgrade in Staging

```bash
# Create feature flag for gradual rollout
export SPEAK_SDK_VERSION=3.x

# Deploy to staging
npm run deploy:staging

# Run comprehensive tests
npm run test:integration
npm run test:e2e

# Monitor for 24 hours
# Check:
# - Speech recognition accuracy
# - Lesson completion rates
# - Error rates
# - Latency metrics
```

