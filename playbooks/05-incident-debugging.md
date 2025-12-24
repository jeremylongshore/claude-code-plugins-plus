# Incident Debugging Playbook: Production Troubleshooting Guide

**Production Playbook for DevOps and Plugin Maintainers**

Debugging production incidents in multi-agent Claude Code workflows requires systematic approaches to log analysis, root cause identification, and rapid remediation. This playbook provides battle-tested debugging techniques, incident response workflows, postmortem templates, and real-world examples of common failure modes.

## Table of Contents

1. [Incident Classification](#incident-classification)
2. [Initial Response Protocol](#initial-response-protocol)
3. [Common Failure Modes](#common-failure-modes)
4. [Debugging Techniques](#debugging-techniques)
5. [Log Analysis](#log-analysis)
6. [Root Cause Analysis](#root-cause-analysis)
7. [Recovery Procedures](#recovery-procedures)
8. [Postmortem Templates](#postmortem-templates)
9. [Best Practices](#best-practices)
10. [Tools & Resources](#tools--resources)
11. [Summary](#summary)

---

## Incident Classification

### Severity Levels

| Severity | Impact | Response Time | Example |
|----------|--------|---------------|---------|
| **SEV-1** | Production down | Immediate | All agents failing, API completely offline |
| **SEV-2** | Major degradation | 15 minutes | 50%+ error rate, critical features broken |
| **SEV-3** | Minor degradation | 1 hour | Intermittent failures, single plugin broken |
| **SEV-4** | Cosmetic issues | 24 hours | UI bugs, non-critical warnings |

### Common Incident Types

```typescript
enum IncidentType {
  API_FAILURE = 'api_failure',           // Claude API unreachable
  RATE_LIMIT = 'rate_limit',             // 429 errors from API
  TIMEOUT = 'timeout',                    // Agent/tool timeouts
  MEMORY_LEAK = 'memory_leak',           // Process memory exhaustion
  PLUGIN_CRASH = 'plugin_crash',         // Plugin process died
  DATA_CORRUPTION = 'data_corruption',   // Invalid data in DB/cache
  PERFORMANCE = 'performance',           // Slow response times
  AUTHENTICATION = 'authentication'      // Auth failures
}

interface Incident {
  id: string;
  severity: 'SEV-1' | 'SEV-2' | 'SEV-3' | 'SEV-4';
  type: IncidentType;
  startTime: number;
  affectedUsers: number;
  errorRate: number;
  description: string;
}
```

---

## Initial Response Protocol

### First 5 Minutes (SEV-1/SEV-2)

**Step 1: Assess Impact**
```bash
# Check current error rate
tail -n 1000 /var/log/claude-code.log | grep -c ERROR

# Check affected users
grep "ERROR" /var/log/claude-code.log | awk '{print $5}' | sort -u | wc -l

# Check service health
curl http://localhost:3333/api/status
```

**Step 2: Check Obvious Issues**
```typescript
// Quick health check script
async function quickHealthCheck(): Promise<{ healthy: boolean; issues: string[] }> {
  const issues: string[] = [];

  // 1. Check Claude API connectivity
  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'x-api-key': process.env.ANTHROPIC_API_KEY },
      body: JSON.stringify({ model: 'claude-3-5-haiku-20241022', messages: [{ role: 'user', content: 'test' }], max_tokens: 10 })
    });
    if (!response.ok) issues.push('Claude API unreachable');
  } catch (error) {
    issues.push('Network connectivity issue');
  }

  // 2. Check disk space
  const { stdout } = await execAsync("df -h / | tail -1 | awk '{print $5}' | sed 's/%//'");
  if (parseInt(stdout) > 90) issues.push('Disk space critical');

  // 3. Check memory
  const memUsage = process.memoryUsage();
  if (memUsage.heapUsed / memUsage.heapTotal > 0.9) issues.push('Memory exhaustion');

  return { healthy: issues.length === 0, issues };
}
```

**Step 3: Stabilize (if possible)**
```bash
# Restart failed services
systemctl restart claude-code-daemon
pm2 restart all

# Clear cache if corrupted
redis-cli FLUSHALL

# Rate limit protection
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
```

### Communication Template

```markdown
# Incident Alert: [TITLE]

**Severity**: SEV-2
**Status**: Investigating
**Started**: 2025-12-24 14:35 UTC
**Affected**: ~1,200 users (15% of total)

## Current Impact
- Agent execution failing with 429 errors
- Error rate: 68% (normal: <1%)
- No data loss

## Actions Taken
1. ✅ Identified rate limit exhaustion (14:40)
2. ✅ Implemented emergency rate limiting (14:42)
3. 🔄 Monitoring recovery (14:45)

## Next Update
In 15 minutes or when resolved.
```

---

## Common Failure Modes

### 1. Rate Limit Exhaustion

**Symptoms**:
```
Error 429: Rate limit exceeded
anthropic-ratelimit-requests-remaining: 0
anthropic-ratelimit-requests-reset: 2025-12-24T15:00:00Z
```

**Diagnosis**:
```typescript
async function diagnoseRateLimits(): Promise<void> {
  // Check recent API calls
  const recentCalls = await queryLogs('SELECT COUNT(*) FROM api_calls WHERE timestamp > NOW() - INTERVAL 1 MINUTE');
  console.log(`API calls in last minute: ${recentCalls}`);

  // Check rate limit headers from last successful call
  const lastHeaders = await getLastAPIHeaders();
  console.log('Remaining requests:', lastHeaders['anthropic-ratelimit-requests-remaining']);
  console.log('Reset time:', lastHeaders['anthropic-ratelimit-requests-reset']);
}
```

**Fix**:
```typescript
// Implement token bucket rate limiter
class EmergencyRateLimiter {
  private tokens = 50; // Match API tier
  private lastRefill = Date.now();

  async throttle(): Promise<void> {
    this.refill();
    while (this.tokens < 1) {
      await sleep(100);
      this.refill();
    }
    this.tokens--;
  }

  private refill() {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    const tokensToAdd = elapsed * (50 / 60); // 50 per minute
    this.tokens = Math.min(50, this.tokens + tokensToAdd);
    this.lastRefill = now;
  }
}
```

### 2. Agent Timeout

**Symptoms**:
```
Error: Agent execution timed out after 300000ms
Task: code-review
Conversation: abc-123-def
```

**Diagnosis**:
```bash
# Check for hung processes
ps aux | grep claude | grep -v grep

# Check system load
uptime
# Output: load average: 12.5, 8.3, 5.2 (CPU overload!)

# Check for blocking I/O
iotop -o -d 5
```

**Fix**:
```typescript
// Implement aggressive timeouts
class TimeoutManager {
  async executeWithTimeout<T>(
    fn: () => Promise<T>,
    timeoutMs: number
  ): Promise<T> {
    return Promise.race([
      fn(),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error(`Timeout after ${timeoutMs}ms`)), timeoutMs)
      )
    ]);
  }
}

// Usage
const timeout = new TimeoutManager();
const result = await timeout.executeWithTimeout(
  () => agent.execute(task),
  30000 // 30 second hard limit
);
```

### 3. Memory Leak

**Symptoms**:
```bash
# Memory usage climbing over time
free -m
#              total   used   free
# Mem:         16384  15892    492  # Critical!

# Process memory
ps aux --sort=-%mem | head -5
# claude-daemon: 8.2GB (!)
```

**Diagnosis**:
```typescript
// Track memory usage over time
setInterval(() => {
  const usage = process.memoryUsage();
  console.log(JSON.stringify({
    timestamp: Date.now(),
    heapUsed: usage.heapUsed / 1024 / 1024, // MB
    heapTotal: usage.heapTotal / 1024 / 1024,
    external: usage.external / 1024 / 1024,
    rss: usage.rss / 1024 / 1024
  }));

  // Trigger GC if usage > 80%
  if (usage.heapUsed / usage.heapTotal > 0.8) {
    global.gc(); // Requires --expose-gc flag
  }
}, 60000); // Every minute
```

**Common Causes**:
```typescript
// ❌ Leak: Global cache never cleared
const cache = new Map<string, any>();
function addToCache(key: string, value: any) {
  cache.set(key, value); // Grows forever!
}

// ✅ Fix: LRU cache with size limit
import LRU from 'lru-cache';
const cache = new LRU<string, any>({ max: 1000 });
```

### 4. Plugin Crash Loop

**Symptoms**:
```bash
# PM2 showing rapid restarts
pm2 status
# plugin-server | errored | 47 restarts in 2 minutes

# Logs show crash
tail -f /var/log/pm2/plugin-server-error.log
# Error: ECONNREFUSED 127.0.0.1:5432
# (PostgreSQL connection failed)
```

**Diagnosis**:
```bash
# Check dependencies
docker ps | grep postgres
# (empty - PostgreSQL container not running!)

# Check network
netstat -tulpn | grep 5432
# (no listener on port 5432)
```

**Fix**:
```bash
# Restart dependency
docker-compose up -d postgres

# Verify connectivity
psql -h localhost -U user -d database -c "SELECT 1"

# Restart plugin
pm2 restart plugin-server
```

---

## Debugging Techniques

### 1. Binary Search Debugging

**Problem**: Unknown change broke production

```bash
# Use git bisect to find breaking commit
git bisect start
git bisect bad HEAD              # Current version is broken
git bisect good v1.2.0           # Last known good version

# Git will check out commits for testing
# Test each commit:
npm install && npm run build && npm test

# Mark results
git bisect good   # if tests pass
git bisect bad    # if tests fail

# Git will find the exact breaking commit
```

### 2. Correlation Analysis

**Find patterns in failures**:
```typescript
interface FailureEvent {
  timestamp: number;
  errorType: string;
  userId?: string;
  pluginName?: string;
  duration: number;
}

function analyzeFailureCorrelations(failures: FailureEvent[]): void {
  // Group by time windows
  const byHour = groupBy(failures, f => Math.floor(f.timestamp / 3600000));

  // Find spike times
  const spikes = Object.entries(byHour)
    .filter(([_, events]) => events.length > 100)
    .map(([hour, events]) => ({
      hour: new Date(parseInt(hour) * 3600000),
      count: events.length,
      topError: mode(events.map(e => e.errorType))
    }));

  console.log('Failure spikes:', spikes);

  // Find common attributes
  const byPlugin = groupBy(failures, f => f.pluginName);
  const suspiciousPlugin = Object.entries(byPlugin)
    .sort((a, b) => b[1].length - a[1].length)[0];

  console.log(`Most failures from plugin: ${suspiciousPlugin[0]} (${suspiciousPlugin[1].length} errors)`);
}
```

### 3. Distributed Tracing

**Track request across services**:
```typescript
import { trace, context, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('claude-code');

async function executeAgent(agentName: string, task: any): Promise<any> {
  const span = tracer.startSpan('agent.execute', {
    attributes: {
      'agent.name': agentName,
      'task.id': task.id
    }
  });

  try {
    // Execute agent logic
    const result = await agent.run(task);

    span.setStatus({ code: SpanStatusCode.OK });
    span.setAttribute('result.success', true);

    return result;
  } catch (error) {
    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: error.message
    });
    span.recordException(error);
    throw error;
  } finally {
    span.end();
  }
}
```

---

## Log Analysis

### Parsing Claude Code Logs

**Log Format**:
```
[2025-12-24T14:35:22.123Z] [ERROR] [agent:code-review] Rate limit exceeded
  conversationId: abc-123-def
  userId: user-456
  errorCode: 429
  retryAfter: 12
  stack: Error: Rate limit exceeded
    at callClaude (/app/src/api.ts:45:11)
```

**Analysis Script**:
```typescript
import { readFileSync } from 'fs';

interface LogEntry {
  timestamp: Date;
  level: 'ERROR' | 'WARN' | 'INFO';
  component: string;
  message: string;
  metadata: Record<string, any>;
}

function parseLog(line: string): LogEntry | null {
  const match = line.match(/\[(.*?)\] \[(.*?)\] \[(.*?)\] (.*)/);
  if (!match) return null;

  const [, timestamp, level, component, rest] = match;
  const lines = rest.split('\n');
  const message = lines[0];

  // Parse metadata
  const metadata: Record<string, any> = {};
  for (const line of lines.slice(1)) {
    const metaMatch = line.match(/^\s*(\w+): (.+)$/);
    if (metaMatch) {
      const [, key, value] = metaMatch;
      metadata[key] = value;
    }
  }

  return {
    timestamp: new Date(timestamp),
    level: level as any,
    component,
    message,
    metadata
  };
}

function analyzeLogs(logPath: string): void {
  const content = readFileSync(logPath, 'utf-8');
  const logs = content.split('\n')
    .map(parseLog)
    .filter(Boolean) as LogEntry[];

  // Error rate by component
  const errorsByComponent = groupBy(
    logs.filter(l => l.level === 'ERROR'),
    l => l.component
  );

  console.log('Errors by component:');
  Object.entries(errorsByComponent)
    .sort((a, b) => b[1].length - a[1].length)
    .forEach(([component, errors]) => {
      console.log(`  ${component}: ${errors.length}`);
    });

  // Recent errors (last 5 minutes)
  const recentErrors = logs.filter(l =>
    l.level === 'ERROR' &&
    Date.now() - l.timestamp.getTime() < 300000
  );

  console.log(`\nRecent errors: ${recentErrors.length}`);
  recentErrors.slice(0, 10).forEach(err => {
    console.log(`  ${err.timestamp.toISOString()} - ${err.message}`);
  });
}
```

### Using Analytics Daemon

```typescript
// Query analytics daemon for incident patterns
const ws = new WebSocket('ws://localhost:3456');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // Track rate limit warnings
  if (data.type === 'rate_limit.warning') {
    console.warn(`⚠️ Rate limit approaching: ${data.current}/${data.limit}`);
  }

  // Track errors
  if (data.type === 'llm.call' && data.error) {
    console.error(`❌ LLM call failed: ${data.error}`);
  }
};

// Query historical data
const response = await fetch('http://localhost:3333/api/sessions');
const sessions = await response.json();
const failedSessions = sessions.filter(s => s.errorCount > 0);

console.log(`Failed sessions: ${failedSessions.length}/${sessions.length}`);
```

---

## Root Cause Analysis

### The 5 Whys Method

**Example: Agent Timeout Incident**

1. **Why did the agent timeout?**
   → Because it took > 300 seconds to respond

2. **Why did it take so long?**
   → Because the Claude API call was slow (280s)

3. **Why was the API call slow?**
   → Because we sent a 50,000 token prompt

4. **Why did we send such a large prompt?**
   → Because the code-reviewer agent included entire codebase in context

5. **Why did it include the entire codebase?**
   → **Root Cause**: File globbing pattern `**/*` matched all files including node_modules (500MB)

**Fix**: Update file globbing to exclude node_modules
```typescript
// Before: includes everything
const files = glob.sync('**/*');

// After: exclude dependencies
const files = glob.sync('**/*', {
  ignore: ['node_modules/**', '.git/**', 'dist/**']
});
```

### Fishbone Diagram (Ishikawa)

```typescript
interface RootCauseAnalysis {
  problem: string;
  categories: {
    people?: string[];
    process?: string[];
    technology?: string[];
    environment?: string[];
  };
  rootCause: string;
  fix: string;
}

const analysis: RootCauseAnalysis = {
  problem: 'Agent timeout causing 68% error rate',
  categories: {
    people: [
      'Developer added file globbing without testing',
      'No code review caught the issue'
    ],
    process: [
      'No integration tests for large codebases',
      'No performance testing in CI/CD'
    ],
    technology: [
      'Glob pattern included node_modules (500MB)',
      'No size limit on prompts',
      'No timeout on file reading'
    ],
    environment: [
      'Production codebase larger than test repos',
      'No staging environment for testing'
    ]
  },
  rootCause: 'Missing file size validation and glob pattern filtering',
  fix: 'Add file exclusion patterns and max prompt size validation'
};
```

---

## Recovery Procedures

### Emergency Rollback

```bash
# Immediate rollback to last known good version
git log --oneline | head -5
# c534df4 (HEAD) feat: Add new feature (BROKEN)
# 3946b1f docs: Update README
# fc73caa (tag: v1.2.0) fix: Bug fix (LAST GOOD)

# Rollback
git reset --hard fc73caa
npm install
npm run build
pm2 restart all

# Deploy
./deploy.sh production

# Verify
curl http://api.example.com/health
```

### Circuit Breaker Reset

```typescript
// Manually reset circuit breaker after fixing issue
class CircuitBreakerManager {
  private breakers = new Map<string, CircuitBreaker>();

  reset(serviceName: string): void {
    const breaker = this.breakers.get(serviceName);
    if (breaker) {
      breaker.state = 'closed';
      breaker.failures = 0;
      console.log(`✓ Reset circuit breaker for ${serviceName}`);
    }
  }

  resetAll(): void {
    for (const [service, breaker] of this.breakers) {
      this.reset(service);
    }
    console.log('✓ Reset all circuit breakers');
  }
}
```

### Data Recovery

```bash
# Recover from backup
BACKUP_DATE="2025-12-24-14:00"

# Stop services
pm2 stop all

# Restore database
pg_restore -d database_prod backups/backup_${BACKUP_DATE}.sql

# Restore files
rsync -av backups/files_${BACKUP_DATE}/ /var/lib/claude-code/

# Restart
pm2 restart all

# Verify data integrity
psql -d database_prod -c "SELECT COUNT(*) FROM conversations"
```

---

## Postmortem Templates

### Incident Postmortem

```markdown
# Postmortem: Agent Timeout Incident (2025-12-24)

**Date**: 2025-12-24
**Duration**: 14:35 - 15:15 UTC (40 minutes)
**Severity**: SEV-2
**Impact**: 1,200 users (15%), 68% error rate

## Summary
Code-reviewer agent began timing out due to excessive file inclusion in prompts, causing 68% error rate for 40 minutes.

## Timeline (UTC)
- **14:35** - First timeout alerts
- **14:40** - Error rate reaches 68%
- **14:42** - On-call engineer paged
- **14:45** - Root cause identified (file globbing)
- **14:50** - Fix deployed to staging
- **14:55** - Fix deployed to production
- **15:00** - Error rate drops to 5%
- **15:15** - Incident resolved, error rate < 1%

## Root Cause
File globbing pattern `**/*` included `node_modules/` directory (500MB), creating prompts exceeding Claude API's context limits and causing timeouts.

## Contributing Factors
1. No file size validation before prompt construction
2. No integration tests with large codebases
3. No staging environment for testing

## What Went Well
- Fast root cause identification (10 minutes)
- Effective rollback procedure
- Clear communication to affected users

## What Went Poorly
- No monitoring alerts before user reports
- No prompt size limits prevented the issue
- Fix took 20 minutes to deploy

## Action Items
- [ ] **P0**: Add file size validation (Owner: @dev, Due: 2025-12-25)
- [ ] **P0**: Implement max prompt size limit (Owner: @dev, Due: 2025-12-25)
- [ ] **P1**: Add monitoring for agent timeouts (Owner: @ops, Due: 2025-12-27)
- [ ] **P1**: Create staging environment (Owner: @ops, Due: 2025-12-30)
- [ ] **P2**: Add integration tests with large repos (Owner: @qa, Due: 2026-01-05)

## Lessons Learned
- File operations need size limits
- Production testing with realistic data is critical
- Monitoring must detect issues before users report them
```

---

## Best Practices

### DO ✅

1. **Log structured data**
   ```typescript
   // ✅ Structured logging
   logger.error('Agent execution failed', {
     agentName: 'code-reviewer',
     conversationId: 'abc-123',
     errorCode: 429,
     duration: 1234
   });

   // ❌ Unstructured
   console.log('Error in code-reviewer agent');
   ```

2. **Set up alerts before incidents**
   ```typescript
   // Alert on error rate > 5%
   if (errorRate > 0.05) {
     pagerDuty.trigger({
       severity: 'critical',
       title: 'High error rate detected',
       details: `Error rate: ${(errorRate * 100).toFixed(1)}%`
     });
   }
   ```

3. **Keep runbooks updated**
   ```markdown
   # Agent Timeout Runbook

   1. Check logs: `tail -f /var/log/claude-code.log | grep TIMEOUT`
   2. Identify pattern: Which agents are timing out?
   3. Check system resources: `top`, `free -m`, `df -h`
   4. If rate limits: Implement emergency throttling
   5. If resource exhaustion: Restart services
   ```

4. **Test recovery procedures**
   ```bash
   # Monthly disaster recovery drill
   ./test-recovery.sh
   # 1. Trigger circuit breaker
   # 2. Verify monitoring alerts
   # 3. Execute rollback
   # 4. Verify service restoration
   ```

### DON'T ❌

1. **Don't skip postmortems**
   ```typescript
   // ❌ Mark as resolved without learning
   incident.status = 'resolved';

   // ✅ Document and learn
   incident.status = 'resolved';
   await createPostmortem(incident);
   await scheduleReview(incident);
   ```

2. **Don't blame individuals**
   ```markdown
   # ❌ Blame-focused
   Root cause: Developer X wrote bad code

   # ✅ System-focused
   Root cause: Missing code review process for file operations
   ```

3. **Don't ignore warning signs**
   ```typescript
   // ❌ Suppress warnings
   if (memoryUsage > 0.8) {
     // TODO: Fix later
   }

   // ✅ Alert and track
   if (memoryUsage > 0.8) {
     logger.warn('High memory usage', { usage: memoryUsage });
     metrics.gauge('memory.usage', memoryUsage);
   }
   ```

---

## Tools & Resources

### Monitoring Tools

**Analytics Daemon** (from this marketplace):
```bash
cd packages/analytics-daemon
pnpm start
# Real-time monitoring on http://localhost:3333
```

**System Monitoring**:
```bash
# CPU, memory, disk
htop

# Network
iftop

# Disk I/O
iotop
```

### Log Aggregation

**Centralized logging**:
```bash
# Ship logs to central server
tail -f /var/log/claude-code.log | \
  nc logserver.example.com 514
```

### External Tools

- [Datadog](https://www.datadoghq.com/) - APM and monitoring
- [Sentry](https://sentry.io/) - Error tracking
- [PagerDuty](https://www.pagerduty.com/) - Incident management
- [Grafana](https://grafana.com/) - Dashboards
- [ELK Stack](https://www.elastic.co/elk-stack) - Log analysis

---

## Summary

**Key Takeaways**:

1. **Classify incidents immediately** - SEV-1/2 require immediate response
2. **Follow response protocol** - Assess, stabilize, communicate
3. **Use systematic debugging** - Binary search, correlation analysis, tracing
4. **Analyze logs effectively** - Structured logging enables fast analysis
5. **Find root causes** - 5 Whys and Fishbone diagrams prevent recurrence
6. **Document everything** - Postmortems are learning opportunities
7. **Test recovery procedures** - Practice makes perfect

**Incident Response Checklist**:
- [ ] Classify severity (SEV-1 through SEV-4)
- [ ] Assess impact (error rate, affected users)
- [ ] Check obvious issues (API, disk, memory)
- [ ] Stabilize systems (restart, rate limit, rollback)
- [ ] Communicate status to stakeholders
- [ ] Identify root cause (5 Whys, logs, metrics)
- [ ] Deploy fix and verify recovery
- [ ] Write postmortem within 24 hours
- [ ] Create action items with owners and dates
- [ ] Schedule review meeting with team

---

**Last Updated**: 2025-12-24
**Author**: Jeremy Longshore
**Related Playbooks**: [Multi-Agent Rate Limits](./01-multi-agent-rate-limits.md), [MCP Server Reliability](./03-mcp-reliability.md)
