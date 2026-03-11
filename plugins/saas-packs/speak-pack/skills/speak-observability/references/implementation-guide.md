# Speak Observability - Implementation Guide

Detailed implementation reference for the speak-observability skill.

## Key Metrics for Language Learning

### Business Metrics
| Metric | Type | Description |
|--------|------|-------------|
| `speak_lessons_started_total` | Counter | Lessons initiated |
| `speak_lessons_completed_total` | Counter | Lessons completed |
| `speak_lessons_abandoned_total` | Counter | Lessons abandoned mid-session |
| `speak_pronunciation_score` | Histogram | Pronunciation scores distribution |
| `speak_active_sessions` | Gauge | Currently active lesson sessions |
| `speak_daily_active_learners` | Gauge | Unique learners today |

### Technical Metrics
| Metric | Type | Description |
|--------|------|-------------|
| `speak_api_requests_total` | Counter | Total API requests |
| `speak_api_duration_seconds` | Histogram | Request latency |
| `speak_api_errors_total` | Counter | Error count by type |
| `speak_speech_recognition_duration_seconds` | Histogram | Audio processing time |
| `speak_rate_limit_remaining` | Gauge | Rate limit headroom |


## Prometheus Metrics Implementation

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

// Business metrics
const lessonsStarted = new Counter({
  name: 'speak_lessons_started_total',
  help: 'Total lessons started',
  labelNames: ['language', 'topic', 'difficulty'],
  registers: [registry],
});

const lessonsCompleted = new Counter({
  name: 'speak_lessons_completed_total',
  help: 'Total lessons completed',
  labelNames: ['language', 'topic', 'difficulty'],
  registers: [registry],
});

const pronunciationScore = new Histogram({
  name: 'speak_pronunciation_score',
  help: 'Pronunciation scores distribution',
  labelNames: ['language'],
  buckets: [40, 50, 60, 70, 80, 85, 90, 95, 100],
  registers: [registry],
});

const activeSessions = new Gauge({
  name: 'speak_active_sessions',
  help: 'Currently active lesson sessions',
  labelNames: ['language'],
  registers: [registry],
});

// Technical metrics
const apiRequests = new Counter({
  name: 'speak_api_requests_total',
  help: 'Total Speak API requests',
  labelNames: ['method', 'endpoint', 'status'],
  registers: [registry],
});

const apiDuration = new Histogram({
  name: 'speak_api_duration_seconds',
  help: 'Speak API request duration',
  labelNames: ['method', 'endpoint'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

const speechRecognitionDuration = new Histogram({
  name: 'speak_speech_recognition_duration_seconds',
  help: 'Speech recognition processing time',
  labelNames: ['language'],
  buckets: [0.5, 1, 2, 3, 5, 10],
  registers: [registry],
});
```


## Instrumented Speak Client

```typescript
async function instrumentedSpeakRequest<T>(
  method: string,
  endpoint: string,
  operation: () => Promise<T>
): Promise<T> {
  const timer = apiDuration.startTimer({ method, endpoint });

  try {
    const result = await operation();
    apiRequests.inc({ method, endpoint, status: 'success' });
    return result;
  } catch (error: any) {
    apiRequests.inc({ method, endpoint, status: 'error' });
    throw error;
  } finally {
    timer();
  }
}

// Lesson tracking
async function trackLessonStart(session: LessonSession): Promise<void> {
  lessonsStarted.inc({
    language: session.language,
    topic: session.topic,
    difficulty: session.difficulty,
  });
  activeSessions.inc({ language: session.language });
}

async function trackLessonEnd(
  session: LessonSession,
  summary: SessionSummary
): Promise<void> {
  const labels = {
    language: session.language,
    topic: session.topic,
    difficulty: session.difficulty,
  };

  if (summary.completed) {
    lessonsCompleted.inc(labels);
  } else {
    lessonsAbandoned.inc({
      ...labels,
      abandonReason: summary.abandonReason || 'unknown',
    });
  }

  activeSessions.dec({ language: session.language });

  // Record pronunciation score
  if (summary.averagePronunciationScore) {
    pronunciationScore.observe(
      { language: session.language },
      summary.averagePronunciationScore
    );
  }
}
```


## Distributed Tracing

### OpenTelemetry Setup
```typescript
import { trace, SpanStatusCode, context, propagation } from '@opentelemetry/api';

const tracer = trace.getTracer('speak-service');

async function tracedSpeakCall<T>(
  operationName: string,
  attributes: Record<string, string>,
  operation: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(`speak.${operationName}`, async (span) => {
    span.setAttributes(attributes);

    try {
      const result = await operation();
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error: any) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
      span.recordException(error);
      throw error;
    } finally {
      span.end();
    }
  });
}

// Trace a complete lesson session
async function tracedLessonSession(
  userId: string,
  config: LessonConfig
): Promise<SessionSummary> {
  return tracedSpeakCall(
    'lesson.session',
    {
      'user.id': userId,
      'lesson.language': config.language,
      'lesson.topic': config.topic,
    },
    async () => {
      const session = await speakService.startSession(config);

      // Create child spans for each exchange
      while (!session.isComplete) {
        await tracedSpeakCall(
          'lesson.exchange',
          { 'session.id': session.id },
          async () => {
            const prompt = await session.getPrompt();
            const response = await getUserResponse();
            return session.submitResponse(response);
          }
        );
      }

      return session.getSummary();
    }
  );
}
```


## Structured Logging

```typescript
import pino from 'pino';

const logger = pino({
  name: 'speak-service',
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
});

interface SpeakLogContext {
  service: 'speak';
  operation: string;
  sessionId?: string;
  userId?: string;
  language?: string;
  duration_ms?: number;
  pronunciationScore?: number;
  error?: any;
}

function logSpeakOperation(
  level: 'info' | 'warn' | 'error',
  operation: string,
  context: Partial<SpeakLogContext>
): void {
  const logContext: SpeakLogContext = {
    service: 'speak',
    operation,
    ...context,
  };

  logger[level](logContext, `Speak ${operation}`);
}

// Usage
logSpeakOperation('info', 'lesson.completed', {
  sessionId: session.id,
  userId: session.userId,
  language: session.language,
  duration_ms: summary.duration,
  pronunciationScore: summary.averagePronunciationScore,
});
```


## Alert Configuration

### Prometheus AlertManager Rules
```yaml
# speak_alerts.yaml
groups:
  - name: speak_alerts
    rules:
      # High error rate
      - alert: SpeakHighErrorRate
        expr: |
          rate(speak_api_errors_total[5m]) /
          rate(speak_api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
          service: speak
        annotations:
          summary: "Speak API error rate > 5%"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Speech recognition slow
      - alert: SpeakSpeechRecognitionSlow
        expr: |
          histogram_quantile(0.95,
            rate(speak_speech_recognition_duration_seconds_bucket[5m])
          ) > 5
        for: 5m
        labels:
          severity: warning
          service: speak
        annotations:
          summary: "Speech recognition P95 latency > 5s"

      # Low lesson completion rate
      - alert: SpeakLowCompletionRate
        expr: |
          rate(speak_lessons_completed_total[1h]) /
          rate(speak_lessons_started_total[1h]) < 0.5
        for: 30m
        labels:
          severity: warning
          service: speak
        annotations:
          summary: "Lesson completion rate < 50%"

      # Speak API down
      - alert: SpeakAPIDown
        expr: up{job="speak"} == 0
        for: 1m
        labels:
          severity: critical
          service: speak
        annotations:
          summary: "Speak API is unreachable"

      # Pronunciation scores dropping
      - alert: SpeakPronunciationScoresDrop
        expr: |
          avg(speak_pronunciation_score) < 60
        for: 1h
        labels:
          severity: info
          service: speak
        annotations:
          summary: "Average pronunciation scores below 60%"
```


## Grafana Dashboard

```json
{
  "title": "Speak Language Learning",
  "panels": [
    {
      "title": "Active Lesson Sessions",
      "type": "stat",
      "targets": [{
        "expr": "sum(speak_active_sessions)"
      }]
    },
    {
      "title": "Lessons Started vs Completed",
      "type": "graph",
      "targets": [
        { "expr": "rate(speak_lessons_started_total[5m])", "legendFormat": "Started" },
        { "expr": "rate(speak_lessons_completed_total[5m])", "legendFormat": "Completed" }
      ]
    },
    {
      "title": "Pronunciation Score Distribution",
      "type": "heatmap",
      "targets": [{
        "expr": "sum by (le) (rate(speak_pronunciation_score_bucket[5m]))"
      }]
    },
    {
      "title": "API Latency P50/P95/P99",
      "type": "graph",
      "targets": [
        { "expr": "histogram_quantile(0.5, rate(speak_api_duration_seconds_bucket[5m]))", "legendFormat": "P50" },
        { "expr": "histogram_quantile(0.95, rate(speak_api_duration_seconds_bucket[5m]))", "legendFormat": "P95" },
        { "expr": "histogram_quantile(0.99, rate(speak_api_duration_seconds_bucket[5m]))", "legendFormat": "P99" }
      ]
    },
    {
      "title": "Speech Recognition Duration",
      "type": "graph",
      "targets": [{
        "expr": "histogram_quantile(0.95, rate(speak_speech_recognition_duration_seconds_bucket[5m]))"
      }]
    },
    {
      "title": "Error Rate by Type",
      "type": "graph",
      "targets": [{
        "expr": "sum by (error_type) (rate(speak_api_errors_total[5m]))"
      }]
    }
  ]
}
```

