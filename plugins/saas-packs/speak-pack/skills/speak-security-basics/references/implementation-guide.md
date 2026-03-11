# Speak Security Basics - Implementation Guide

Detailed implementation reference for the speak-security-basics skill.

## Instructions

### Step 1: Configure Environment Variables
```bash
# .env (NEVER commit to git)
SPEAK_API_KEY=sk_live_***
SPEAK_APP_ID=app_***
SPEAK_WEBHOOK_SECRET=whsec_***

# .gitignore
.env
.env.local
.env.*.local
*.wav  # User audio recordings
*.mp3
recordings/
```

### Step 2: Implement Secret Rotation
```bash
# 1. Generate new key in Speak developer dashboard
# https://developer.speak.com/dashboard/api-keys

# 2. Update environment variable
export SPEAK_API_KEY="new_key_here"

# 3. Verify new key works
curl -X POST https://api.speak.com/v1/health \
  -H "Authorization: Bearer ${SPEAK_API_KEY}" \
  -H "X-App-ID: ${SPEAK_APP_ID}"

# 4. Revoke old key in dashboard
```

### Step 3: Apply Least Privilege Access
| Environment | Recommended Scopes |
|-------------|-------------------|
| Development | `lessons:read`, `speech:analyze` |
| Staging | `lessons:read`, `lessons:write`, `speech:analyze` |
| Production | Only required scopes for features |

```typescript
// Use scoped API keys per feature
const lessonClient = new SpeakClient({
  apiKey: process.env.SPEAK_LESSON_API_KEY!, // lessons:* only
  appId: process.env.SPEAK_APP_ID!,
});

const speechClient = new SpeakClient({
  apiKey: process.env.SPEAK_SPEECH_API_KEY!, // speech:* only
  appId: process.env.SPEAK_APP_ID!,
});
```

### Step 4: User Audio Privacy

```typescript
// Audio data handling policies
interface AudioPrivacyConfig {
  retention: 'session_only' | '30_days' | 'permanent';
  shareWithSpeak: boolean; // For model improvement
  allowPlayback: boolean; // Let users hear their recordings
  encryption: 'at_rest' | 'in_transit' | 'both';
}

class SecureAudioHandler {
  private config: AudioPrivacyConfig;

  constructor(config: AudioPrivacyConfig) {
    this.config = config;
  }

  async storeAudio(userId: string, audioData: ArrayBuffer): Promise<string> {
    // Encrypt before storage
    const encrypted = await this.encrypt(audioData);

    // Generate non-guessable ID
    const audioId = crypto.randomUUID();

    // Store with expiration
    const expiry = this.config.retention === 'session_only'
      ? Date.now() + 60 * 60 * 1000 // 1 hour
      : this.config.retention === '30_days'
        ? Date.now() + 30 * 24 * 60 * 60 * 1000
        : null;

    await storage.put(audioId, encrypted, { expiry });

    // Audit log
    await auditLog({
      action: 'audio_stored',
      userId,
      audioId,
      retention: this.config.retention,
    });

    return audioId;
  }

  async deleteUserAudio(userId: string): Promise<void> {
    const audioIds = await storage.listByUser(userId);

    for (const id of audioIds) {
      await storage.delete(id);
    }

    await auditLog({
      action: 'audio_deleted',
      userId,
      count: audioIds.length,
    });
  }

  private async encrypt(data: ArrayBuffer): Promise<ArrayBuffer> {
    // Use AES-256-GCM encryption
    const key = await crypto.subtle.importKey(
      'raw',
      Buffer.from(process.env.AUDIO_ENCRYPTION_KEY!, 'base64'),
      'AES-GCM',
      false,
      ['encrypt']
    );

    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encrypted = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      data
    );

    // Prepend IV to encrypted data
    const result = new Uint8Array(iv.length + encrypted.byteLength);
    result.set(iv);
    result.set(new Uint8Array(encrypted), iv.length);

    return result.buffer;
  }
}
```

### Step 5: Webhook Signature Verification

```typescript
import crypto from 'crypto';

function verifySpeakWebhook(
  payload: string,
  signature: string,
  timestamp: string
): boolean {
  const secret = process.env.SPEAK_WEBHOOK_SECRET!;

  // Reject old timestamps (replay attack protection)
  const timestampAge = Date.now() - parseInt(timestamp) * 1000;
  if (timestampAge > 300000) { // 5 minutes
    console.error('Webhook timestamp too old');
    return false;
  }

  // Compute expected signature
  const signedPayload = `${timestamp}.${payload}`;
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(signedPayload)
    .digest('hex');

  // Timing-safe comparison
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(`sha256=${expectedSignature}`)
  );
}

// Express middleware
function speakWebhookMiddleware(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers['x-speak-signature'] as string;
  const timestamp = req.headers['x-speak-timestamp'] as string;

  if (!verifySpeakWebhook(req.body.toString(), signature, timestamp)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  next();
}
```

### Step 6: User Data Protection

```typescript
// GDPR/CCPA compliance for language learning data
interface UserLearningData {
  lessonHistory: LessonRecord[];
  pronunciationScores: PronunciationRecord[];
  vocabularyProgress: VocabularyProgress[];
  audioRecordings: AudioReference[];
}

class UserDataManager {
  async exportUserData(userId: string): Promise<UserLearningData> {
    // Gather all user data for GDPR export
    const [lessons, scores, vocab, audio] = await Promise.all([
      db.lessons.findByUser(userId),
      db.pronunciation.findByUser(userId),
      db.vocabulary.findByUser(userId),
      storage.listAudioByUser(userId),
    ]);

    await auditLog({
      action: 'user_data_export',
      userId,
      timestamp: new Date(),
    });

    return {
      lessonHistory: lessons,
      pronunciationScores: scores,
      vocabularyProgress: vocab,
      audioRecordings: audio,
    };
  }

  async deleteUserData(userId: string): Promise<DeletionResult> {
    // Complete data deletion for GDPR
    const results = await Promise.allSettled([
      db.lessons.deleteByUser(userId),
      db.pronunciation.deleteByUser(userId),
      db.vocabulary.deleteByUser(userId),
      this.deleteUserAudio(userId),
      speakClient.users.delete(userId), // Delete from Speak's servers
    ]);

    await auditLog({
      action: 'user_data_deleted',
      userId,
      timestamp: new Date(),
      results: results.map(r => r.status),
    });

    return {
      success: results.every(r => r.status === 'fulfilled'),
      timestamp: new Date(),
    };
  }
}
```


## Security Checklist

### API Security
- [ ] API keys in environment variables
- [ ] `.env` files in `.gitignore`
- [ ] Different keys for dev/staging/prod
- [ ] Minimal scopes per environment
- [ ] Webhook signatures validated
- [ ] Key rotation schedule documented

### Audio Security
- [ ] Audio encrypted at rest
- [ ] Audio encrypted in transit (HTTPS)
- [ ] Clear retention policy
- [ ] User consent obtained
- [ ] Deletion mechanism implemented

### User Data
- [ ] GDPR export implemented
- [ ] CCPA compliance verified
- [ ] Audit logging enabled
- [ ] Data minimization practiced
- [ ] Privacy policy updated


## Detailed Examples

### Service Account Pattern
```typescript
const clients = {
  lessons: new SpeakClient({
    apiKey: process.env.SPEAK_LESSON_KEY,
    appId: process.env.SPEAK_APP_ID,
  }),
  speech: new SpeakClient({
    apiKey: process.env.SPEAK_SPEECH_KEY,
    appId: process.env.SPEAK_APP_ID,
  }),
};
```

### Audit Logging
```typescript
interface AuditEntry {
  timestamp: Date;
  action: string;
  userId: string;
  resource: string;
  result: 'success' | 'failure';
  metadata?: Record<string, any>;
}

async function auditLog(entry: Omit<AuditEntry, 'timestamp'>): Promise<void> {
  const log: AuditEntry = { ...entry, timestamp: new Date() };

  // Store in audit database
  await auditDb.insert(log);

  // Also log for compliance
  console.log('[AUDIT]', JSON.stringify(log));
}
```

