# Speak Data Handling - Implementation Guide

Detailed implementation reference for the speak-data-handling skill.

## Data Classification

| Category | Examples | Handling |
|----------|----------|----------|
| PII | Email, name, phone | Encrypt, minimize |
| Sensitive | API keys, tokens | Never log, rotate |
| Learning Data | Scores, progress | Anonymize for analytics |
| Audio Recordings | Voice samples | Encrypt, consent required |
| User Preferences | Languages, goals | Standard handling |


## Audio Data Privacy

### Audio Consent Management
```typescript
interface AudioConsent {
  userId: string;
  consentGiven: boolean;
  consentDate: Date;
  purposes: ('pronunciation_scoring' | 'model_improvement' | 'playback')[];
  retentionDays: number;
  canWithdraw: boolean;
}

class AudioConsentManager {
  async getConsent(userId: string): Promise<AudioConsent | null> {
    return db.audioConsents.findOne({ userId });
  }

  async grantConsent(
    userId: string,
    purposes: AudioConsent['purposes'],
    retentionDays: number = 30
  ): Promise<void> {
    await db.audioConsents.upsert({
      userId,
      consentGiven: true,
      consentDate: new Date(),
      purposes,
      retentionDays,
      canWithdraw: true,
    });

    await auditLog({
      action: 'audio_consent_granted',
      userId,
      purposes,
      retentionDays,
    });
  }

  async withdrawConsent(userId: string): Promise<void> {
    // Mark consent withdrawn
    await db.audioConsents.update(userId, {
      consentGiven: false,
      withdrawnDate: new Date(),
    });

    // Delete existing audio
    await this.deleteUserAudio(userId);

    await auditLog({
      action: 'audio_consent_withdrawn',
      userId,
    });
  }

  async canRecordAudio(userId: string): Promise<boolean> {
    const consent = await this.getConsent(userId);
    return consent?.consentGiven === true &&
           consent.purposes.includes('pronunciation_scoring');
  }
}
```

### Secure Audio Storage
```typescript
class SecureAudioStorage {
  private encryptionKey: Buffer;
  private storage: StorageBackend;

  constructor(encryptionKeyBase64: string, storage: StorageBackend) {
    this.encryptionKey = Buffer.from(encryptionKeyBase64, 'base64');
    this.storage = storage;
  }

  async storeAudio(
    userId: string,
    sessionId: string,
    audioData: ArrayBuffer,
    metadata: AudioMetadata
  ): Promise<string> {
    // Encrypt audio
    const encrypted = await this.encrypt(audioData);

    // Generate non-guessable ID
    const audioId = crypto.randomUUID();

    // Calculate expiry based on consent
    const consent = await audioConsentManager.getConsent(userId);
    const expiryDate = new Date();
    expiryDate.setDate(expiryDate.getDate() + (consent?.retentionDays || 7));

    // Store with metadata
    await this.storage.put(`audio/${audioId}`, encrypted, {
      metadata: {
        userId: hashUserId(userId), // Store hashed for lookup
        sessionId,
        language: metadata.language,
        duration: metadata.duration,
        createdAt: new Date().toISOString(),
        expiresAt: expiryDate.toISOString(),
      },
    });

    // Store mapping (encrypted)
    await db.audioMappings.insert({
      audioId,
      userId: encrypt(userId),
      expiresAt: expiryDate,
    });

    await auditLog({
      action: 'audio_stored',
      userId,
      audioId,
      sessionId,
      expiresAt: expiryDate,
    });

    return audioId;
  }

  async deleteUserAudio(userId: string): Promise<number> {
    const mappings = await db.audioMappings.find({
      userId: encrypt(userId),
    });

    for (const mapping of mappings) {
      await this.storage.delete(`audio/${mapping.audioId}`);
      await db.audioMappings.delete(mapping.audioId);
    }

    await auditLog({
      action: 'user_audio_deleted',
      userId,
      count: mappings.length,
    });

    return mappings.length;
  }

  private async encrypt(data: ArrayBuffer): Promise<ArrayBuffer> {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const key = await crypto.subtle.importKey(
      'raw',
      this.encryptionKey,
      'AES-GCM',
      false,
      ['encrypt']
    );

    const encrypted = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      data
    );

    // Prepend IV
    const result = new Uint8Array(iv.length + encrypted.byteLength);
    result.set(iv);
    result.set(new Uint8Array(encrypted), iv.length);
    return result.buffer;
  }
}
```


## Learning Data Handling

### PII Detection in Learning Data
```typescript
const PII_PATTERNS = [
  { type: 'email', regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { type: 'phone', regex: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g },
  { type: 'name_pattern', regex: /my name is ([A-Z][a-z]+ ?)+/gi },
  { type: 'address', regex: /\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|blvd)/gi },
];

function detectPIIInLessonContent(text: string): PIIFinding[] {
  const findings: PIIFinding[] = [];

  for (const pattern of PII_PATTERNS) {
    const matches = text.matchAll(pattern.regex);
    for (const match of matches) {
      findings.push({
        type: pattern.type,
        match: match[0],
        position: match.index,
      });
    }
  }

  return findings;
}

// Scan lesson responses before storage
async function sanitizeLessonResponse(
  response: LessonResponse
): Promise<LessonResponse> {
  const findings = detectPIIInLessonContent(response.text);

  if (findings.length > 0) {
    console.warn('PII detected in lesson response', {
      types: findings.map(f => f.type),
    });

    // Redact PII before storage
    let sanitizedText = response.text;
    for (const finding of findings) {
      sanitizedText = sanitizedText.replace(finding.match, '[REDACTED]');
    }

    return { ...response, text: sanitizedText };
  }

  return response;
}
```

### Data Retention Policy
```typescript
interface RetentionPolicy {
  dataType: string;
  retentionDays: number;
  reason: string;
}

const RETENTION_POLICIES: RetentionPolicy[] = [
  { dataType: 'audio_recordings', retentionDays: 30, reason: 'User consent period' },
  { dataType: 'lesson_transcripts', retentionDays: 90, reason: 'Learning history' },
  { dataType: 'pronunciation_scores', retentionDays: 365, reason: 'Progress tracking' },
  { dataType: 'session_logs', retentionDays: 30, reason: 'Debugging' },
  { dataType: 'error_logs', retentionDays: 90, reason: 'Root cause analysis' },
  { dataType: 'audit_logs', retentionDays: 2555, reason: 'Compliance (7 years)' },
  { dataType: 'user_preferences', retentionDays: -1, reason: 'Until account deletion' },
];

async function cleanupExpiredData(): Promise<CleanupReport> {
  const report: CleanupReport = { deletedCounts: {} };

  for (const policy of RETENTION_POLICIES) {
    if (policy.retentionDays < 0) continue; // -1 = keep forever

    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - policy.retentionDays);

    const count = await db[policy.dataType].deleteMany({
      createdAt: { $lt: cutoff },
    });

    report.deletedCounts[policy.dataType] = count;
  }

  await auditLog({
    action: 'data_cleanup',
    report,
  });

  return report;
}

// Schedule daily cleanup
cron.schedule('0 3 * * *', cleanupExpiredData);
```


## GDPR/CCPA Compliance

### Data Subject Access Request (DSAR)
```typescript
interface UserDataExport {
  exportedAt: string;
  userId: string;
  profile: UserProfile;
  learningData: {
    languages: string[];
    totalLessons: number;
    totalPracticeTime: number;
    pronunciationHistory: PronunciationRecord[];
    vocabularyProgress: VocabularyProgress[];
    streakHistory: StreakRecord[];
  };
  audioRecordings: {
    count: number;
    totalDuration: number;
    files?: ArrayBuffer[]; // If user requests actual audio
  };
  consents: ConsentRecord[];
  auditTrail: AuditEntry[];
}

async function exportUserData(
  userId: string,
  includeAudio: boolean = false
): Promise<UserDataExport> {
  const [
    profile,
    lessons,
    pronunciation,
    vocabulary,
    streaks,
    audioMeta,
    consents,
    audit,
  ] = await Promise.all([
    db.users.findOne({ id: userId }),
    db.lessons.find({ userId }),
    db.pronunciationScores.find({ userId }),
    db.vocabulary.find({ userId }),
    db.streaks.find({ userId }),
    db.audioMappings.find({ userId: encrypt(userId) }),
    db.consents.find({ userId }),
    db.auditLogs.find({ userId }),
  ]);

  let audioFiles: ArrayBuffer[] | undefined;
  if (includeAudio && audioMeta.length > 0) {
    audioFiles = await Promise.all(
      audioMeta.map(meta => audioStorage.retrieve(meta.audioId))
    );
  }

  const exportData: UserDataExport = {
    exportedAt: new Date().toISOString(),
    userId,
    profile: sanitizeProfile(profile),
    learningData: {
      languages: extractLanguages(lessons),
      totalLessons: lessons.length,
      totalPracticeTime: calculatePracticeTime(lessons),
      pronunciationHistory: pronunciation,
      vocabularyProgress: vocabulary,
      streakHistory: streaks,
    },
    audioRecordings: {
      count: audioMeta.length,
      totalDuration: audioMeta.reduce((sum, m) => sum + m.duration, 0),
      files: audioFiles,
    },
    consents,
    auditTrail: audit,
  };

  await auditLog({
    action: 'data_export',
    userId,
    includeAudio,
    timestamp: new Date(),
  });

  return exportData;
}
```

### Right to Deletion
```typescript
interface DeletionResult {
  success: boolean;
  deletedItems: Record<string, number>;
  retainedForCompliance: string[];
  deletedAt: Date;
}

async function deleteUserData(userId: string): Promise<DeletionResult> {
  const deletedItems: Record<string, number> = {};
  const retainedForCompliance: string[] = [];

  // Delete from Speak's servers first
  try {
    await speakClient.users.delete(userId);
    deletedItems['speak_remote'] = 1;
  } catch (error) {
    console.error('Failed to delete from Speak:', error);
  }

  // Delete local data
  deletedItems['lessons'] = await db.lessons.deleteMany({ userId });
  deletedItems['pronunciation'] = await db.pronunciationScores.deleteMany({ userId });
  deletedItems['vocabulary'] = await db.vocabulary.deleteMany({ userId });
  deletedItems['streaks'] = await db.streaks.deleteMany({ userId });
  deletedItems['preferences'] = await db.preferences.deleteMany({ userId });

  // Delete audio recordings
  deletedItems['audio'] = await audioStorage.deleteUserAudio(userId);

  // Anonymize data we must retain (not delete)
  await db.auditLogs.updateMany(
    { userId },
    { $set: { userId: 'DELETED_USER', pii: null } }
  );
  retainedForCompliance.push('audit_logs (anonymized)');

  // Final audit entry
  await auditLog({
    action: 'GDPR_DELETION',
    userId: 'DELETED_USER',
    originalUserId: hashUserId(userId),
    deletedItems,
    retainedForCompliance,
    timestamp: new Date(),
  });

  // Delete user profile last
  deletedItems['profile'] = await db.users.deleteOne({ id: userId });

  return {
    success: true,
    deletedItems,
    retainedForCompliance,
    deletedAt: new Date(),
  };
}
```

