# Guidewire Observability - Implementation Guide

## Observability Stack

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Observability Platform                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        Visualization Layer                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │ Dashboards  │  │   Alerts    │  │   Reports   │  │   SLOs      │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│  ┌─────────────────────────────────────┴───────────────────────────────────┐   │
│  │                        Processing Layer                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │ Log Parser  │  │  Metrics    │  │   Trace     │  │   Event     │    │   │
│  │  │             │  │ Aggregator  │  │ Collector   │  │ Processor   │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│  ┌─────────────────────────────────────┴───────────────────────────────────┐   │
│  │                         Collection Layer                                 │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │   Logs      │  │  Metrics    │  │   Traces    │  │   Events    │    │   │
│  │  │ (Fluentd)   │  │(Prometheus) │  │  (Jaeger)   │  │  (Kafka)    │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        ▲
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
            ┌───────┴───────┐   ┌───────┴───────┐   ┌───────┴───────┐
            │  PolicyCenter │   │  ClaimCenter  │   │ BillingCenter │
            │               │   │               │   │               │
            │ • App Logs    │   │ • App Logs    │   │ • App Logs    │
            │ • Metrics     │   │ • Metrics     │   │ • Metrics     │
            │ • Traces      │   │ • Traces      │   │ • Traces      │
            └───────────────┘   └───────────────┘   └───────────────┘
```

## Instructions

### Step 1: Structured Logging

```gosu
// Structured logging implementation
package gw.observability.logging

uses gw.api.util.Logger
uses java.util.Map
uses gw.api.json.JsonObject

class StructuredLogger {
  private var _category : String
  private var _logger : Logger

  construct(category : String) {
    _category = category
    _logger = Logger.forCategory(category)
  }

  function info(message : String, context : Map<String, Object> = null) {
    _logger.info(formatMessage("INFO", message, context))
  }

  function warn(message : String, context : Map<String, Object> = null) {
    _logger.warn(formatMessage("WARN", message, context))
  }

  function error(message : String, error : Exception = null, context : Map<String, Object> = null) {
    var ctx = context ?: new HashMap<String, Object>()
    if (error != null) {
      ctx.put("error_type", error.Class.Name)
      ctx.put("error_message", error.Message)
      ctx.put("stack_trace", getStackTrace(error))
    }
    _logger.error(formatMessage("ERROR", message, ctx))
  }

  private function formatMessage(level : String, message : String, context : Map<String, Object>) : String {
    var log = new HashMap<String, Object>()

    // Standard fields
    log.put("timestamp", Date.Now.format("yyyy-MM-dd'T'HH:mm:ss.SSSZ"))
    log.put("level", level)
    log.put("category", _category)
    log.put("message", message)

    // Request context
    var requestContext = getRequestContext()
    if (requestContext != null) {
      log.putAll(requestContext)
    }

    // Custom context
    if (context != null) {
      log.putAll(context)
    }

    return JsonObject.toJson(log)
  }

  private function getRequestContext() : Map<String, Object> {
    var context = new HashMap<String, Object>()

    try {
      var session = gw.api.web.SessionUtil.getCurrentSession()
      if (session != null) {
        context.put("user_id", session.User?.PublicID)
        context.put("session_id", session.ID)
      }

      var request = gw.api.web.RequestUtil.getCurrentRequest()
      if (request != null) {
        context.put("request_id", request.getAttribute("X-Request-ID"))
        context.put("trace_id", request.getAttribute("X-Trace-ID"))
      }
    } catch (e : Exception) {
      // Ignore - not in request context
    }

    return context
  }

  private function getStackTrace(e : Exception) : String {
    var sw = new java.io.StringWriter()
    e.printStackTrace(new java.io.PrintWriter(sw))
    return sw.toString().substring(0, Math.min(sw.length(), 5000))
  }
}

// Usage
class PolicyService {
  private static var LOG = new StructuredLogger("PolicyService")

  function issuePolicy(policy : Policy) : Policy {
    LOG.info("Issuing policy", {
      "policy_number" -> policy.PolicyNumber,
      "account_id" -> policy.Account.PublicID,
      "premium" -> policy.TotalPremiumRPT.Amount
    })

    try {
      // Policy issuance logic
      return policy
    } catch (e : Exception) {
      LOG.error("Policy issuance failed", e, {
        "policy_number" -> policy.PolicyNumber
      })
      throw e
    }
  }
}
```

### Step 2: Metrics Collection

```gosu
// Custom metrics collection
package gw.observability.metrics

uses java.util.concurrent.ConcurrentHashMap
uses java.util.concurrent.atomic.AtomicLong
uses java.util.concurrent.atomic.LongAdder

class MetricsCollector {
  private static var _counters = new ConcurrentHashMap<String, LongAdder>()
  private static var _gauges = new ConcurrentHashMap<String, AtomicLong>()
  private static var _histograms = new ConcurrentHashMap<String, Histogram>()

  // Counter - monotonically increasing value
  static function incrementCounter(name : String, tags : Map<String, String> = null) {
    var key = buildKey(name, tags)
    _counters.computeIfAbsent(key, \k -> new LongAdder()).increment()
  }

  static function incrementCounter(name : String, value : long, tags : Map<String, String> = null) {
    var key = buildKey(name, tags)
    _counters.computeIfAbsent(key, \k -> new LongAdder()).add(value)
  }

  // Gauge - point-in-time value
  static function setGauge(name : String, value : long, tags : Map<String, String> = null) {
    var key = buildKey(name, tags)
    _gauges.computeIfAbsent(key, \k -> new AtomicLong()).set(value)
  }

  // Histogram - distribution of values
  static function recordHistogram(name : String, value : double, tags : Map<String, String> = null) {
    var key = buildKey(name, tags)
    _histograms.computeIfAbsent(key, \k -> new Histogram()).record(value)
  }

  // Timer helper
  static function time<T>(name : String, operation() : T, tags : Map<String, String> = null) : T {
    var startTime = System.nanoTime()
    var success = true

    try {
      return operation()
    } catch (e : Exception) {
      success = false
      throw e
    } finally {
      var duration = (System.nanoTime() - startTime) / 1_000_000.0  // ms
      var metricTags = tags ?: new HashMap<String, String>()
      metricTags.put("success", success.toString())
      recordHistogram(name + "_duration_ms", duration, metricTags)
      incrementCounter(name + "_total", metricTags)
    }
  }

  // Export metrics in Prometheus format
  static function exportPrometheus() : String {
    var sb = new StringBuilder()

    // Counters
    _counters.eachKeyAndValue(\key, counter -> {
      sb.append("# TYPE ${key} counter\n")
      sb.append("${key} ${counter.sum()}\n")
    })

    // Gauges
    _gauges.eachKeyAndValue(\key, gauge -> {
      sb.append("# TYPE ${key} gauge\n")
      sb.append("${key} ${gauge.get()}\n")
    })

    // Histograms
    _histograms.eachKeyAndValue(\key, histogram -> {
      sb.append("# TYPE ${key} histogram\n")
      sb.append("${key}_count ${histogram.Count}\n")
      sb.append("${key}_sum ${histogram.Sum}\n")
      histogram.Buckets.eachKeyAndValue(\bucket, count -> {
        sb.append("${key}_bucket{le=\"${bucket}\"} ${count}\n")
      })
    })

    return sb.toString()
  }

  private static function buildKey(name : String, tags : Map<String, String>) : String {
    if (tags == null || tags.Empty) {
      return name
    }
    var tagStr = tags.Keys.toList().sort().map(\k -> "${k}=\"${tags.get(k)}\"").join(",")
    return "${name}{${tagStr}}"
  }
}

// Usage
class ClaimService {
  function processClaim(claimId : String) : Claim {
    return MetricsCollector.time("claim_processing", \-> {
      // Process claim
      var claim = loadClaim(claimId)
      MetricsCollector.incrementCounter("claims_processed", {
        "claim_type" -> claim.LossType.Code,
        "status" -> claim.State.Code
      })
      return claim
    }, {"claim_id" -> claimId})
  }
}
```

### Step 3: Distributed Tracing

```typescript
// Distributed tracing implementation
import { trace, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('guidewire-integration');

// Trace API calls
async function tracedApiCall<T>(
  operationName: string,
  apiCall: () => Promise<T>,
  attributes?: Record<string, string>
): Promise<T> {
  return tracer.startActiveSpan(operationName, {
    kind: SpanKind.CLIENT,
    attributes: {
      'service.name': 'guidewire-api',
      ...attributes
    }
  }, async (span) => {
    try {
      const result = await apiCall();
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error instanceof Error ? error.message : 'Unknown error'
      });
      span.recordException(error as Error);
      throw error;
    } finally {
      span.end();
    }
  });
}

// Example: Traced policy creation
async function createPolicy(submissionData: SubmissionData): Promise<Policy> {
  return tracer.startActiveSpan('create_policy', async (rootSpan) => {
    try {
      // Step 1: Create account
      const account = await tracedApiCall(
        'create_account',
        () => guidewireClient.createAccount(submissionData.account),
        { 'account.name': submissionData.account.name }
      );

      // Step 2: Create submission
      const submission = await tracedApiCall(
        'create_submission',
        () => guidewireClient.createSubmission(account.id, submissionData),
        { 'account.id': account.id }
      );

      // Step 3: Quote
      const quote = await tracedApiCall(
        'quote_submission',
        () => guidewireClient.quoteSubmission(submission.id),
        { 'submission.id': submission.id }
      );

      // Step 4: Bind
      const policy = await tracedApiCall(
        'bind_submission',
        () => guidewireClient.bindSubmission(submission.id),
        { 'submission.id': submission.id }
      );

      rootSpan.setStatus({ code: SpanStatusCode.OK });
      rootSpan.setAttribute('policy.number', policy.policyNumber);

      return policy;
    } catch (error) {
      rootSpan.setStatus({ code: SpanStatusCode.ERROR });
      rootSpan.recordException(error as Error);
      throw error;
    } finally {
      rootSpan.end();
    }
  });
}

// Propagate trace context in headers
function getTraceHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  const currentContext = context.active();

  trace.getSpan(currentContext)?.spanContext();

  // W3C Trace Context format
  const spanContext = trace.getSpan(currentContext)?.spanContext();
  if (spanContext) {
    headers['traceparent'] = `00-${spanContext.traceId}-${spanContext.spanId}-01`;
  }

  return headers;
}
```

### Step 4: Alerting Configuration

```yaml
# Alert rules configuration
alerts:
  # API Error Rate
  - name: high_api_error_rate
    description: API error rate exceeds threshold
    query: |
      rate(http_requests_total{status=~"5.."}[5m])
      / rate(http_requests_total[5m]) > 0.05
    for: 5m
    severity: critical
    channels:
      - pagerduty
      - slack-oncall
    annotations:
      summary: "High API error rate: {{ $value | humanizePercentage }}"
      runbook: https://wiki.company.com/runbooks/api-errors

  # API Latency
  - name: high_api_latency
    description: P95 API latency exceeds 2 seconds
    query: |
      histogram_quantile(0.95,
        rate(http_request_duration_seconds_bucket[5m])
      ) > 2
    for: 10m
    severity: warning
    channels:
      - slack-engineering
    annotations:
      summary: "P95 latency: {{ $value | humanizeDuration }}"

  # Policy Processing Failures
  - name: policy_processing_failures
    description: Policy processing failure rate high
    query: |
      rate(policy_processing_total{success="false"}[15m])
      / rate(policy_processing_total[15m]) > 0.01
    for: 15m
    severity: critical
    channels:
      - pagerduty
      - email-policy-team
    annotations:
      summary: "Policy processing failures: {{ $value | humanizePercentage }}"

  # Claim Processing Queue Depth
  - name: claim_queue_depth
    description: Claim processing queue is backing up
    query: |
      claim_processing_queue_depth > 1000
    for: 30m
    severity: warning
    channels:
      - slack-claims-team
    annotations:
      summary: "Claim queue depth: {{ $value }}"

  # Database Connection Pool
  - name: db_connection_pool_exhausted
    description: Database connection pool near exhaustion
    query: |
      db_connection_pool_available
      / db_connection_pool_max < 0.1
    for: 5m
    severity: critical
    channels:
      - pagerduty
    annotations:
      summary: "DB pool {{ $value | humanizePercentage }} available"
```

### Step 5: Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Guidewire InsuranceSuite Overview",
    "refresh": "30s",
    "panels": [
      {
        "title": "API Request Rate",
        "type": "graph",
        "query": "rate(http_requests_total[5m])",
        "gridPos": { "x": 0, "y": 0, "w": 8, "h": 6 }
      },
      {
        "title": "API Error Rate",
        "type": "graph",
        "query": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
        "gridPos": { "x": 8, "y": 0, "w": 8, "h": 6 },
        "thresholds": [
          { "value": 0.01, "color": "yellow" },
          { "value": 0.05, "color": "red" }
        ]
      },
      {
        "title": "P95 Latency",
        "type": "graph",
        "query": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
        "gridPos": { "x": 16, "y": 0, "w": 8, "h": 6 }
      },
      {
        "title": "Policies Issued Today",
        "type": "stat",
        "query": "increase(policies_issued_total[24h])",
        "gridPos": { "x": 0, "y": 6, "w": 6, "h": 4 }
      },
      {
        "title": "Claims Filed Today",
        "type": "stat",
        "query": "increase(claims_filed_total[24h])",
        "gridPos": { "x": 6, "y": 6, "w": 6, "h": 4 }
      },
      {
        "title": "Active Users",
        "type": "stat",
        "query": "sum(active_user_sessions)",
        "gridPos": { "x": 12, "y": 6, "w": 6, "h": 4 }
      },
      {
        "title": "Application Health",
        "type": "table",
        "query": "up{job=~\"guidewire.*\"}",
        "gridPos": { "x": 0, "y": 10, "w": 24, "h": 6 }
      }
    ]
  }
}
```

### Step 6: Log Analysis Queries

```sql
-- Guidewire Cloud Console log queries

-- Find all errors in the last hour
SELECT * FROM logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
  AND level = 'ERROR'
ORDER BY timestamp DESC
LIMIT 100;

-- Policy issuance failures
SELECT
  timestamp,
  message,
  context.policy_number,
  context.error_type,
  context.error_message
FROM logs
WHERE category = 'PolicyService'
  AND level = 'ERROR'
  AND message LIKE '%issuance failed%'
  AND timestamp > NOW() - INTERVAL '24 hours';

-- Slow API calls (> 5 seconds)
SELECT
  timestamp,
  context.request_id,
  context.endpoint,
  context.duration_ms,
  context.user_id
FROM logs
WHERE context.duration_ms > 5000
  AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY context.duration_ms DESC;

-- Authentication failures
SELECT
  timestamp,
  context.client_id,
  context.ip_address,
  context.error_code,
  COUNT(*) as failure_count
FROM logs
WHERE category = 'Authentication'
  AND level = 'WARN'
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY context.client_id, context.ip_address, context.error_code
ORDER BY failure_count DESC;
```

## Key Metrics to Monitor

| Category | Metric | Target | Alert Threshold |
|----------|--------|--------|-----------------|
| Availability | Uptime | 99.9% | < 99.5% |
| Latency | P95 Response Time | < 1s | > 3s |
| Errors | Error Rate | < 0.1% | > 1% |
| Throughput | Requests/sec | Baseline | +/- 50% |
| Business | Policies Issued | Baseline | -20% |
| Business | Claims Filed | Baseline | +50% |
