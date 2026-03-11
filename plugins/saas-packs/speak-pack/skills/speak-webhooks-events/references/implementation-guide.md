# Speak Webhooks Events - Implementation Guide

Detailed implementation reference for the speak-webhooks-events skill.

## Speak Event Types

| Event | Description | Payload |
|-------|-------------|---------|
| `lesson.started` | User started a lesson | sessionId, userId, topic |
| `lesson.completed` | User completed a lesson | sessionId, summary, score |
| `lesson.abandoned` | User abandoned mid-lesson | sessionId, progress, reason |
| `pronunciation.milestone` | Score threshold reached | userId, language, score |
| `streak.achieved` | Learning streak milestone | userId, streakDays |
| `level.up` | User advanced a level | userId, language, newLevel |
| `subscription.changed` | Plan changed | userId, plan, action |


## Webhook Endpoint Setup

### Express.js Implementation
```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();

// IMPORTANT: Raw body needed for signature verification
app.post('/webhooks/speak',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const signature = req.headers['x-speak-signature'] as string;
    const timestamp = req.headers['x-speak-timestamp'] as string;
    const eventId = req.headers['x-speak-event-id'] as string;

    // Verify signature
    if (!verifySpeakSignature(req.body, signature, timestamp)) {
      console.error('Invalid webhook signature', { eventId });
      return res.status(401).json({ error: 'Invalid signature' });
    }

    // Check for duplicate (idempotency)
    if (await isEventProcessed(eventId)) {
      return res.status(200).json({ received: true, duplicate: true });
    }

    const event = JSON.parse(req.body.toString());

    try {
      await handleSpeakEvent(event);
      await markEventProcessed(eventId);
      res.status(200).json({ received: true });
    } catch (error) {
      console.error('Webhook processing failed', { eventId, error });
      // Return 500 to trigger Speak retry
      res.status(500).json({ error: 'Processing failed' });
    }
  }
);
```


## Signature Verification

```typescript
function verifySpeakSignature(
  payload: Buffer,
  signature: string,
  timestamp: string
): boolean {
  const secret = process.env.SPEAK_WEBHOOK_SECRET!;

  // Reject old timestamps (replay attack protection)
  const timestampAge = Date.now() - parseInt(timestamp) * 1000;
  if (timestampAge > 300000) { // 5 minutes
    console.error('Webhook timestamp too old', { age: timestampAge });
    return false;
  }

  // Reject future timestamps
  if (timestampAge < -60000) { // 1 minute tolerance
    console.error('Webhook timestamp in future');
    return false;
  }

  // Compute expected signature
  const signedPayload = `${timestamp}.${payload.toString()}`;
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(signedPayload)
    .digest('hex');

  // Timing-safe comparison
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature.replace('sha256=', '')),
      Buffer.from(expectedSignature)
    );
  } catch {
    return false;
  }
}
```


## Event Handler Pattern

```typescript
type SpeakEventType =
  | 'lesson.started'
  | 'lesson.completed'
  | 'lesson.abandoned'
  | 'pronunciation.milestone'
  | 'streak.achieved'
  | 'level.up'
  | 'subscription.changed';

interface SpeakEvent {
  id: string;
  type: SpeakEventType;
  data: Record<string, any>;
  userId: string;
  createdAt: string;
}

// Type-safe event handlers
interface LessonCompletedData {
  sessionId: string;
  topic: string;
  language: string;
  duration: number;
  averagePronunciationScore: number;
  vocabularyLearned: number;
  grammarPatternsUsed: string[];
}

interface StreakAchievedData {
  streakDays: number;
  totalLessons: number;
  milestone: number;
}

const eventHandlers: Record<SpeakEventType, (data: any, userId: string) => Promise<void>> = {
  'lesson.started': async (data, userId) => {
    console.log(`User ${userId} started lesson: ${data.topic}`);
    await analytics.track('lesson_started', { userId, ...data });
  },

  'lesson.completed': async (data: LessonCompletedData, userId) => {
    console.log(`User ${userId} completed lesson: ${data.topic}`);

    // Update user progress
    await db.users.update(userId, {
      totalLessons: { $inc: 1 },
      vocabularyCount: { $inc: data.vocabularyLearned },
      lastLessonAt: new Date(),
    });

    // Award XP
    const xp = calculateXP(data);
    await gamification.awardXP(userId, xp);

    // Send completion notification
    await notifications.send(userId, {
      type: 'lesson_complete',
      title: 'Lesson Complete!',
      body: `Great job! You scored ${data.averagePronunciationScore}%`,
    });

    await analytics.track('lesson_completed', { userId, ...data });
  },

  'lesson.abandoned': async (data, userId) => {
    console.log(`User ${userId} abandoned lesson at ${data.progress}%`);

    // Track for engagement analysis
    await analytics.track('lesson_abandoned', { userId, ...data });

    // Maybe send re-engagement notification later
    await scheduler.schedule('re_engagement', {
      userId,
      delayHours: 24,
    });
  },

  'pronunciation.milestone': async (data, userId) => {
    console.log(`User ${userId} reached pronunciation milestone: ${data.score}`);

    await gamification.awardBadge(userId, `pronunciation_${data.score}`);
    await notifications.send(userId, {
      type: 'achievement',
      title: 'Pronunciation Milestone!',
      body: `You've reached ${data.score}% pronunciation accuracy!`,
    });
  },

  'streak.achieved': async (data: StreakAchievedData, userId) => {
    console.log(`User ${userId} achieved ${data.streakDays} day streak`);

    await gamification.awardBadge(userId, `streak_${data.milestone}`);

    // Special rewards for milestone streaks
    if ([7, 30, 100, 365].includes(data.milestone)) {
      await rewards.grantStreakReward(userId, data.milestone);
    }
  },

  'level.up': async (data, userId) => {
    console.log(`User ${userId} leveled up to ${data.newLevel} in ${data.language}`);

    await db.users.update(userId, {
      [`levels.${data.language}`]: data.newLevel,
    });

    await gamification.awardBadge(userId, `level_${data.language}_${data.newLevel}`);
  },

  'subscription.changed': async (data, userId) => {
    console.log(`User ${userId} subscription: ${data.action}`);

    await db.users.update(userId, {
      subscriptionPlan: data.plan,
      subscriptionStatus: data.action === 'cancelled' ? 'cancelled' : 'active',
    });

    await analytics.track('subscription_changed', { userId, ...data });
  },
};

async function handleSpeakEvent(event: SpeakEvent): Promise<void> {
  const handler = eventHandlers[event.type];

  if (!handler) {
    console.log(`Unhandled event type: ${event.type}`);
    return;
  }

  try {
    await handler(event.data, event.userId);
    console.log(`Processed ${event.type}: ${event.id}`);
  } catch (error) {
    console.error(`Failed to process ${event.type}: ${event.id}`, error);
    throw error; // Rethrow to trigger retry
  }
}
```


## Idempotency Handling

```typescript
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

async function isEventProcessed(eventId: string): Promise<boolean> {
  const key = `speak:event:${eventId}`;
  const exists = await redis.exists(key);
  return exists === 1;
}

async function markEventProcessed(eventId: string): Promise<void> {
  const key = `speak:event:${eventId}`;
  // Keep for 7 days to handle delayed retries
  await redis.set(key, '1', 'EX', 86400 * 7);
}
```


## Webhook Testing

```bash
# Use Speak CLI to send test events
speak webhooks trigger lesson.completed \
  --url http://localhost:3000/webhooks/speak \
  --data '{"sessionId":"sess_123","topic":"greetings","score":85}'

# Test with signature
TIMESTAMP=$(date +%s)
PAYLOAD='{"type":"lesson.completed","data":{"score":85}}'
SIGNATURE=$(echo -n "${TIMESTAMP}.${PAYLOAD}" | openssl dgst -sha256 -hmac "$SPEAK_WEBHOOK_SECRET" | cut -d' ' -f2)

curl -X POST http://localhost:3000/webhooks/speak \
  -H "Content-Type: application/json" \
  -H "X-Speak-Signature: sha256=${SIGNATURE}" \
  -H "X-Speak-Timestamp: ${TIMESTAMP}" \
  -H "X-Speak-Event-Id: test_$(uuidgen)" \
  -d "${PAYLOAD}"
```


## Local Development with ngrok

```bash
# Expose local server
ngrok http 3000

# Register webhook URL in Speak dashboard
# URL: https://your-ngrok-url.ngrok.io/webhooks/speak

# Test events will now hit your local server
```

