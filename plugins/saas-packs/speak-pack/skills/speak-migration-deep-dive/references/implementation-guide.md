# Speak Migration Deep Dive - Implementation Guide

Detailed implementation reference for the speak-migration-deep-dive skill.

## Migration Types

| Type | Complexity | Duration | Risk |
|------|-----------|----------|------|
| Fresh install | Low | Days | Low |
| From competitor (Duolingo API, etc.) | Medium | Weeks | Medium |
| SDK major version upgrade | Medium | Weeks | Medium |
| Full language platform migration | High | Months | High |


## Pre-Migration Assessment

### Step 1: Current State Analysis
```bash
# Document current language learning implementation
find . -name "*.ts" -o -name "*.py" | xargs grep -l "language\|lesson\|speech" > learning-files.txt

# Count integration points
wc -l learning-files.txt

# Identify dependencies
npm list | grep -i "language\|speech\|duolingo\|babbel"
pip freeze | grep -i "language\|speech"

# Analyze data structures
grep -r "interface.*Lesson\|type.*Lesson" src/ --include="*.ts"
```

### Step 2: Data Inventory
```typescript
interface MigrationInventory {
  // User data
  userCount: number;
  activeUsersLast30Days: number;

  // Learning data
  lessonRecordsCount: number;
  languagesUsed: string[];
  averageLessonsPerUser: number;

  // Audio data
  audioRecordingsCount: number;
  totalAudioDurationHours: number;
  audioStorageGB: number;

  // Progress data
  pronunciationScoresCount: number;
  vocabularyEntriesCount: number;
  streakRecordsCount: number;

  // Integration points
  apiEndpoints: string[];
  webhooksConfigured: string[];
  customFeatures: string[];
}

async function assessMigration(): Promise<MigrationInventory> {
  const [users, lessons, audio, progress] = await Promise.all([
    assessUserData(),
    assessLessonData(),
    assessAudioData(),
    assessProgressData(),
  ]);

  return {
    ...users,
    ...lessons,
    ...audio,
    ...progress,
    apiEndpoints: await findApiEndpoints(),
    webhooksConfigured: await findWebhooks(),
    customFeatures: await documentCustomFeatures(),
  };
}
```

### Step 3: Language Support Mapping
```typescript
// Map your current languages to Speak's supported languages
const LANGUAGE_MAPPING: Record<string, string> = {
  // Current system -> Speak code
  'spanish': 'es',
  'korean': 'ko',
  'japanese': 'ja',
  'mandarin': 'zh-CN',
  'french': 'fr',
  'german': 'de',
  'portuguese': 'pt-BR',
  'indonesian': 'id',
};

function validateLanguageSupport(
  currentLanguages: string[]
): LanguageValidation {
  const supported: string[] = [];
  const unsupported: string[] = [];

  for (const lang of currentLanguages) {
    if (LANGUAGE_MAPPING[lang]) {
      supported.push(lang);
    } else {
      unsupported.push(lang);
    }
  }

  return {
    supported,
    unsupported,
    migrationReady: unsupported.length === 0,
    recommendation: unsupported.length > 0
      ? `${unsupported.join(', ')} not supported by Speak. Consider alternatives.`
      : 'All languages supported',
  };
}
```


## Migration Strategy: Strangler Fig Pattern

```
Phase 1: Parallel Run
┌─────────────────┐     ┌─────────────┐
│   Old Language  │     │   Speak     │
│   Platform      │ ──▶ │   (Shadow)  │
│   (100%)        │     │   (0%)      │
└─────────────────┘     └─────────────┘

Phase 2: Feature-by-Feature Migration
┌─────────────────┐     ┌─────────────┐
│   Old Platform  │     │   Speak     │
│   (Core only)   │ ──▶ │   (New)     │
│                 │     │   Features  │
└─────────────────┘     └─────────────┘

Phase 3: Gradual User Migration
┌─────────────────┐     ┌─────────────┐
│   Old Platform  │     │   Speak     │
│   (50% users)   │ ──▶ │   (50%)     │
└─────────────────┘     └─────────────┘

Phase 4: Complete
┌─────────────────┐     ┌─────────────┐
│   Old Platform  │     │   Speak     │
│   (Deprecated)  │ ──▶ │   (100%)    │
└─────────────────┘     └─────────────┘
```


## Implementation Plan

### Phase 1: Setup (Week 1-2)
```bash
# Install Speak SDK
npm install @speak/language-sdk

# Configure credentials
cp .env.example .env.speak
# Edit with Speak credentials

# Verify connectivity
npx tsx -e "
const { SpeakClient } = require('@speak/language-sdk');
const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY,
  appId: process.env.SPEAK_APP_ID,
});
client.health.check().then(console.log);
"
```

### Phase 2: Adapter Layer (Week 3-4)
```typescript
// src/adapters/language-service.ts
interface LanguageServiceAdapter {
  // Session management
  startLesson(config: LessonConfig): Promise<LessonSession>;
  endLesson(sessionId: string): Promise<LessonSummary>;

  // Speech processing
  recognizeSpeech(audio: ArrayBuffer): Promise<RecognitionResult>;
  scorePronunciation(audio: ArrayBuffer, text: string): Promise<PronunciationScore>;

  // Progress tracking
  getProgress(userId: string): Promise<UserProgress>;
  updateProgress(userId: string, progress: Partial<UserProgress>): Promise<void>;
}

// Old system adapter
class LegacyLanguageAdapter implements LanguageServiceAdapter {
  async startLesson(config: LessonConfig): Promise<LessonSession> {
    return legacyClient.lessons.create(config);
  }
  // ... implement other methods
}

// New Speak adapter
class SpeakLanguageAdapter implements LanguageServiceAdapter {
  private client: SpeakClient;

  constructor(client: SpeakClient) {
    this.client = client;
  }

  async startLesson(config: LessonConfig): Promise<LessonSession> {
    const speakConfig = this.transformConfig(config);
    const session = await this.client.tutor.startSession(speakConfig);
    return this.transformSession(session);
  }

  private transformConfig(config: LessonConfig): SpeakLessonConfig {
    return {
      language: LANGUAGE_MAPPING[config.language],
      topic: config.topic,
      difficulty: config.level,
      duration: config.durationMinutes,
    };
  }

  private transformSession(session: SpeakSession): LessonSession {
    return {
      id: session.id,
      status: session.status,
      language: session.language,
      // Map other fields
    };
  }
}
```

### Phase 3: Data Migration (Week 5-8)
```typescript
interface MigrationBatch {
  users: UserMigration[];
  startedAt: Date;
  completedAt?: Date;
  errors: MigrationError[];
}

async function migrateUserData(): Promise<MigrationReport> {
  const batchSize = 100;
  let processed = 0;
  let errors: MigrationError[] = [];

  const totalUsers = await db.users.count();
  console.log(`Migrating ${totalUsers} users...`);

  for await (const batch of iterateUserBatches(batchSize)) {
    const results = await Promise.allSettled(
      batch.map(user => migrateUser(user))
    );

    for (let i = 0; i < results.length; i++) {
      if (results[i].status === 'rejected') {
        errors.push({
          userId: batch[i].id,
          error: results[i].reason,
          timestamp: new Date(),
        });
      }
    }

    processed += batch.length;
    console.log(`Progress: ${processed}/${totalUsers} (${(processed/totalUsers*100).toFixed(1)}%)`);

    // Rate limit protection
    await sleep(100);
  }

  return { processed, errors, successRate: (processed - errors.length) / processed };
}

async function migrateUser(user: LegacyUser): Promise<void> {
  // 1. Create user in Speak
  const speakUser = await speakClient.users.create({
    externalId: user.id,
    email: user.email,
    preferences: {
      nativeLanguage: LANGUAGE_MAPPING[user.nativeLanguage],
      targetLanguages: user.learningLanguages.map(l => LANGUAGE_MAPPING[l]),
    },
  });

  // 2. Migrate progress data
  const legacyProgress = await legacyDb.progress.findByUser(user.id);
  await speakClient.users.updateProgress(speakUser.id, {
    vocabularyCount: legacyProgress.vocabularyLearned,
    lessonsCompleted: legacyProgress.totalLessons,
    streak: legacyProgress.currentStreak,
  });

  // 3. Store mapping
  await db.userMigrations.insert({
    legacyId: user.id,
    speakId: speakUser.id,
    migratedAt: new Date(),
  });
}
```

### Phase 4: Traffic Shift (Week 9-12)
```typescript
// Feature flag controlled adapter selection
function getLanguageAdapter(userId: string): LanguageServiceAdapter {
  const speakPercentage = getFeatureFlag('speak_migration_percentage');
  const userInSpeakCohort = isUserInMigrationCohort(userId, speakPercentage);

  if (userInSpeakCohort) {
    return new SpeakLanguageAdapter(speakClient);
  }

  return new LegacyLanguageAdapter();
}

// Gradual rollout controller
async function adjustMigrationPercentage(): Promise<void> {
  const metrics = await getMigrationMetrics();

  // Auto-rollback if error rate too high
  if (metrics.speakErrorRate > 0.05) {
    console.error('High error rate detected, reducing Speak traffic');
    await setFeatureFlag('speak_migration_percentage', Math.max(0, metrics.currentPercentage - 10));
    return;
  }

  // Increase if stable
  if (metrics.speakErrorRate < 0.01 && metrics.latencyOk) {
    const newPercentage = Math.min(100, metrics.currentPercentage + 10);
    console.log(`Increasing Speak traffic to ${newPercentage}%`);
    await setFeatureFlag('speak_migration_percentage', newPercentage);
  }
}
```


## Audio Migration

```typescript
// Migrate audio recordings (if needed)
async function migrateAudioRecordings(userId: string): Promise<void> {
  const legacyAudioFiles = await legacyStorage.listUserAudio(userId);

  for (const file of legacyAudioFiles) {
    // Download from legacy storage
    const audioData = await legacyStorage.download(file.id);

    // Re-encode if necessary (Speak requires specific format)
    const optimizedAudio = await optimizeAudioForSpeak(audioData);

    // Upload to new storage (Speak-compatible)
    await newStorage.upload({
      userId: getMigratedUserId(userId),
      audioData: optimizedAudio,
      metadata: {
        legacyId: file.id,
        language: file.language,
        duration: file.duration,
        migratedAt: new Date(),
      },
    });
  }
}
```


## Rollback Plan

```bash
#!/bin/bash
# rollback-speak-migration.sh

echo "=== Speak Migration Rollback ==="

# 1. Route all traffic back to legacy
kubectl set env deployment/language-service SPEAK_MIGRATION_PERCENTAGE=0

# 2. Disable Speak adapter
kubectl set env deployment/language-service SPEAK_ENABLED=false

# 3. Restart to apply
kubectl rollout restart deployment/language-service
kubectl rollout status deployment/language-service

# 4. Verify legacy is working
curl -f https://api.yourapp.com/health | jq '.services.language'

# 5. Notify team
echo "Rollback complete. Legacy language service active."
```


## Post-Migration Validation

```typescript
async function validateMigration(): Promise<ValidationReport> {
  const checks = [
    { name: 'User count match', fn: checkUserCounts },
    { name: 'Progress data intact', fn: checkProgressData },
    { name: 'Audio accessible', fn: checkAudioAccess },
    { name: 'All languages working', fn: checkLanguageSupport },
    { name: 'Speech recognition', fn: checkSpeechRecognition },
    { name: 'Lesson completion flow', fn: checkLessonFlow },
    { name: 'Webhook delivery', fn: checkWebhooks },
    { name: 'Performance baseline', fn: checkPerformance },
  ];

  const results = await Promise.all(
    checks.map(async c => ({
      name: c.name,
      result: await c.fn(),
    }))
  );

  return {
    checks: results,
    passed: results.every(r => r.result.success),
    timestamp: new Date(),
  };
}

// User communication after migration
async function notifyMigratedUsers(userIds: string[]): Promise<void> {
  for (const userId of userIds) {
    await notifications.send(userId, {
      type: 'migration_complete',
      title: 'Your learning experience just got better!',
      body: 'We\'ve upgraded your language learning with improved AI tutoring and speech recognition.',
      action: {
        label: 'Try a lesson',
        url: '/lessons/new',
      },
    });
  }
}
```


## Post-Migration
After completing migration, refer back to the standard skills for ongoing operations.
