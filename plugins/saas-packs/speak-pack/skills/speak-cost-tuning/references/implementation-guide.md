# Speak Cost Tuning - Implementation Guide

Detailed implementation reference for the speak-cost-tuning skill.

## Pricing Model

### Subscription Tiers
| Tier | Monthly Cost | Lessons/mo | Audio Min/mo | Users |
|------|-------------|------------|--------------|-------|
| Free | $0 | 50 | 30 | 1 |
| Personal | $29 | 500 | 300 | 1 |
| Team | $199 | 5,000 | 2,000 | 10 |
| Business | $499 | 20,000 | 10,000 | 50 |
| Enterprise | Custom | Unlimited | Unlimited | Unlimited |

### Usage-Based Pricing (Overages)
| Resource | Unit | Overage Cost |
|----------|------|--------------|
| Lesson Sessions | per session | $0.05 |
| Audio Recognition | per minute | $0.02 |
| Pronunciation Scoring | per evaluation | $0.01 |
| AI Tutor Interactions | per exchange | $0.02 |


## Cost Estimation

```typescript
interface UsageEstimate {
  lessonsPerMonth: number;
  audioMinutesPerMonth: number;
  tier: string;
  baseCost: number;
  overageCost: number;
  totalCost: number;
  recommendation?: string;
}

function estimateSpeakCost(
  lessonsPerMonth: number,
  audioMinutesPerMonth: number,
  currentTier: 'free' | 'personal' | 'team' | 'business' = 'personal'
): UsageEstimate {
  const tiers = {
    free: { cost: 0, lessons: 50, audio: 30 },
    personal: { cost: 29, lessons: 500, audio: 300 },
    team: { cost: 199, lessons: 5000, audio: 2000 },
    business: { cost: 499, lessons: 20000, audio: 10000 },
  };

  const tier = tiers[currentTier];
  const baseCost = tier.cost;

  // Calculate overages
  const lessonOverage = Math.max(0, lessonsPerMonth - tier.lessons);
  const audioOverage = Math.max(0, audioMinutesPerMonth - tier.audio);

  const overageCost =
    lessonOverage * 0.05 +
    audioOverage * 0.02;

  const totalCost = baseCost + overageCost;

  // Recommend upgrade if overage is high
  let recommendation: string | undefined;
  if (overageCost > baseCost * 0.5) {
    const nextTier = getNextTier(currentTier);
    if (nextTier) {
      const nextTierCost = estimateSpeakCost(
        lessonsPerMonth,
        audioMinutesPerMonth,
        nextTier
      );
      if (nextTierCost.totalCost < totalCost) {
        recommendation = `Consider upgrading to ${nextTier} tier to save $${(totalCost - nextTierCost.totalCost).toFixed(2)}/month`;
      }
    }
  }

  return {
    lessonsPerMonth,
    audioMinutesPerMonth,
    tier: currentTier,
    baseCost,
    overageCost,
    totalCost,
    recommendation,
  };
}
```


## Usage Monitoring

```typescript
class SpeakUsageMonitor {
  private lessonCount = 0;
  private audioMinutes = 0;
  private pronunciationScores = 0;
  private monthStart: Date;
  private alertThreshold: number;

  constructor(monthlyBudget: number) {
    this.alertThreshold = monthlyBudget * 0.8; // 80% warning
    this.monthStart = new Date();
    this.monthStart.setDate(1);
  }

  trackLesson(duration: number, audioMinutes: number, scores: number): void {
    this.lessonCount++;
    this.audioMinutes += audioMinutes;
    this.pronunciationScores += scores;

    const currentCost = this.estimatedCost();
    if (currentCost > this.alertThreshold) {
      this.sendAlert(`Approaching Speak budget: $${currentCost.toFixed(2)}`);
    }
  }

  estimatedCost(): number {
    // Base tier cost prorated + overages
    const lessonCost = Math.max(0, this.lessonCount - 500) * 0.05;
    const audioCost = Math.max(0, this.audioMinutes - 300) * 0.02;
    const scoreCost = Math.max(0, this.pronunciationScores - 1000) * 0.01;

    return 29 + lessonCost + audioCost + scoreCost; // Assuming personal tier
  }

  getUsageReport(): UsageReport {
    return {
      lessons: this.lessonCount,
      audioMinutes: this.audioMinutes,
      pronunciationScores: this.pronunciationScores,
      estimatedCost: this.estimatedCost(),
      period: {
        start: this.monthStart,
        end: new Date(),
      },
    };
  }

  private sendAlert(message: string): void {
    // Send to Slack, email, PagerDuty, etc.
    console.warn('[SPEAK BUDGET ALERT]', message);
  }
}
```


## Cost Reduction Strategies

### Strategy 1: Efficient Lesson Design
```typescript
// Reduce unnecessary API calls by batching
async function efficientLesson(
  session: LessonSession,
  exchanges: number
): Promise<void> {
  // Pre-fetch all prompts at once
  const prompts = await session.getPromptsBatch(exchanges);

  // Process in sequence but with prepared data
  for (const prompt of prompts) {
    displayPrompt(prompt);
    const response = await getUserResponse();
    // Submit when ready
  }
}
```

### Strategy 2: Client-Side Audio Pre-processing
```typescript
// Reduce audio minutes billed by trimming silence
async function optimizedAudioSubmit(
  session: LessonSession,
  rawAudio: ArrayBuffer
): Promise<Feedback> {
  // Trim silence locally (free)
  const trimmed = await trimSilence(rawAudio);

  // Only upload meaningful audio (billed)
  const durationReduction = 1 - (trimmed.byteLength / rawAudio.byteLength);
  console.log(`Saved ${(durationReduction * 100).toFixed(0)}% audio cost`);

  return session.submitAudio(trimmed);
}
```

### Strategy 3: Caching Vocabulary Lookups
```typescript
// Cache vocabulary to reduce API calls
const vocabularyCache = new Map<string, VocabularyEntry>();

async function cachedVocabularyLookup(
  word: string,
  language: string
): Promise<VocabularyEntry> {
  const key = `${language}:${word.toLowerCase()}`;

  if (vocabularyCache.has(key)) {
    return vocabularyCache.get(key)!; // Free
  }

  const entry = await speakClient.vocabulary.lookup(word, language); // Costs
  vocabularyCache.set(key, entry);
  return entry;
}
```

### Strategy 4: Pronunciation Scoring Optimization
```typescript
// Only score pronunciation on final attempts
async function smartPronunciationScoring(
  session: LessonSession,
  phrase: string,
  audioAttempts: ArrayBuffer[]
): Promise<PronunciationResult> {
  // Quick local validation for early attempts (free)
  for (let i = 0; i < audioAttempts.length - 1; i++) {
    const basic = await localAudioValidation(audioAttempts[i]);
    if (!basic.acceptable) {
      return { needsRetry: true, feedback: basic.feedback };
    }
  }

  // Only call paid API for final attempt
  return session.scorePronunciation(audioAttempts[audioAttempts.length - 1], phrase);
}
```

### Strategy 5: Off-Peak Usage
```typescript
// Schedule non-urgent operations for off-peak
async function scheduleProgressSync(userId: string): Promise<void> {
  const now = new Date();
  const hour = now.getUTCHours();

  // Off-peak: 2am-6am UTC
  if (hour >= 2 && hour < 6) {
    // Immediate sync
    await speakClient.users.syncProgress(userId);
  } else {
    // Queue for off-peak
    await queue.add('progress-sync', { userId }, {
      delay: getDelayUntilOffPeak(),
    });
  }
}
```


## Budget Alerts Configuration

```typescript
// Set up billing alerts
interface BudgetAlert {
  threshold: number; // Percentage of budget
  channels: ('email' | 'slack' | 'pagerduty')[];
  action?: 'notify' | 'throttle' | 'pause';
}

const budgetAlerts: BudgetAlert[] = [
  { threshold: 50, channels: ['email'], action: 'notify' },
  { threshold: 75, channels: ['email', 'slack'], action: 'notify' },
  { threshold: 90, channels: ['email', 'slack', 'pagerduty'], action: 'throttle' },
  { threshold: 100, channels: ['email', 'slack', 'pagerduty'], action: 'pause' },
];

async function checkBudget(usage: UsageReport): Promise<void> {
  const budget = 500; // Monthly budget
  const percentUsed = (usage.estimatedCost / budget) * 100;

  for (const alert of budgetAlerts) {
    if (percentUsed >= alert.threshold) {
      await sendBudgetAlert(alert, usage, percentUsed);

      if (alert.action === 'throttle') {
        await enableRateLimiting();
      } else if (alert.action === 'pause') {
        await pauseNonEssentialFeatures();
      }
    }
  }
}
```


## Cost Dashboard Query

```sql
-- Track Speak usage costs by user and feature
SELECT
  DATE_TRUNC('day', created_at) as date,
  user_id,
  feature,
  COUNT(*) as operations,
  SUM(audio_seconds) / 60.0 as audio_minutes,
  SUM(
    CASE
      WHEN feature = 'lesson' THEN 0.05
      WHEN feature = 'audio' THEN audio_seconds / 60.0 * 0.02
      WHEN feature = 'pronunciation' THEN 0.01
      ELSE 0
    END
  ) as estimated_cost
FROM speak_usage_logs
WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY 1, 2, 3
ORDER BY estimated_cost DESC;
```

