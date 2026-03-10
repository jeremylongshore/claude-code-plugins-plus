---
title: "Incident Debugging Playbook"
description: "SEV-1/2/3/4 incident response protocols. Log analysis, root cause investigation (5 Whys, Fishbone), postmortem templates, and on-call procedures."
category: "Operations"
wordCount: 5000
readTime: 25
featured: false
order: 5
tags: ["incident-response", "debugging", "postmortem", "log-analysis", "root-cause"]
prerequisites: []
relatedPlaybooks: ["01-multi-agent-rate-limits", "03-mcp-reliability"]
---

<p><strong>Production Playbook for DevOps and Plugin Maintainers</strong></p>

<p>Debugging production incidents in multi-agent Claude Code workflows requires systematic approaches to log analysis, root cause identification, and rapid remediation. This playbook provides battle-tested debugging techniques, incident response workflows, postmortem templates, and real-world examples of common failure modes.</p>

<h2>Incident Classification</h2>

<h3>Severity Levels</h3>

<table>
<thead>
<tr>
<th>Severity</th>
<th>Impact</th>
<th>Response Time</th>
<th>Example</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>SEV-1</strong></td>
<td>Production down</td>
<td>Immediate</td>
<td>All agents failing, API completely offline</td>
</tr>
<tr>
<td><strong>SEV-2</strong></td>
<td>Major degradation</td>
<td>15 minutes</td>
<td>50%+ error rate, critical features broken</td>
</tr>
<tr>
<td><strong>SEV-3</strong></td>
<td>Minor degradation</td>
<td>1 hour</td>
<td>Intermittent failures, single plugin broken</td>
</tr>
<tr>
<td><strong>SEV-4</strong></td>
<td>Cosmetic issues</td>
<td>24 hours</td>
<td>UI bugs, non-critical warnings</td>
</tr>
</tbody>
</table>

<h3>Common Incident Types</h3>

<pre><code class="language-typescript">enum IncidentType {
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
}</code></pre>

<hr>

<h2>Initial Response Protocol</h2>

<h3>First 5 Minutes (SEV-1/SEV-2)</h3>

<p><strong>Step 1: Assess Impact</strong></p>
<pre><code class="language-bash"># Check current error rate
tail -n 1000 /var/log/claude-code.log | grep -c ERROR

# Check affected users
grep "ERROR" /var/log/claude-code.log | awk '{print $5}' | sort -u | wc -l

# Check service health
curl http://localhost:3333/api/status</code></pre>

<p><strong>Step 2: Check Obvious Issues</strong></p>
<pre><code class="language-typescript">// Quick health check script
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
}</code></pre>

<p><strong>Step 3: Stabilize (if possible)</strong></p>
<pre><code class="language-bash"># Restart failed services
systemctl restart claude-code-daemon
pm2 restart all

# Clear cache if corrupted
redis-cli FLUSHALL

# Rate limit protection
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT</code></pre>

<h3>Communication Template</h3>

<pre><code class="language-markdown"># Incident Alert: [TITLE]

<strong>Severity</strong>: SEV-2
<strong>Status</strong>: Investigating
<strong>Started</strong>: 2025-12-24 14:35 UTC
<strong>Affected</strong>: ~1,200 users (15% of total)

<h2>Current Impact</h2>
<ul>
<li>Agent execution failing with 429 errors</li>
<li>Error rate: 68% (normal: <1%)</li>
<li>No data loss</li>
</ul>

<h2>Actions Taken</h2>
<ul>
<li>✅ Identified rate limit exhaustion (14:40)</li>
<li>✅ Implemented emergency rate limiting (14:42)</li>
<li>🔄 Monitoring recovery (14:45)</li>
</ul>

<h2>Next Update</h2>
In 15 minutes or when resolved.</code></pre>

<hr>

<h2>Common Failure Modes</h2>

<h3>1. Rate Limit Exhaustion</h3>

<p><strong>Symptoms</strong>:</p>
<p>\`\`<code></p>
<p>Error 429: Rate limit exceeded</p>
<p>anthropic-ratelimit-requests-remaining: 0</p>
<p>anthropic-ratelimit-requests-reset: 2025-12-24T15:00:00Z</p>
<code>\`</code>

<p><strong>Diagnosis</strong>:</p>
<pre><code class="language-typescript">async function diagnoseRateLimits(): Promise<void> {
  // Check recent API calls
  const recentCalls = await queryLogs('SELECT COUNT(*) FROM api_calls WHERE timestamp > NOW() - INTERVAL 1 MINUTE');
  console.log(`API calls in last minute: ${recentCalls}`);

// Check rate limit headers from last successful call
const lastHeaders = await getLastAPIHeaders();
console.log('Remaining requests:', lastHeaders['anthropic-ratelimit-requests-remaining']);
console.log('Reset time:', lastHeaders['anthropic-ratelimit-requests-reset']);
}</code></pre>

<p><strong>Fix</strong>:</p>
<pre><code class="language-typescript">// Implement token bucket rate limiter
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
}</code></pre>

<h3>2. Agent Timeout</h3>

<p><strong>Symptoms</strong>:</p>
<code>\`</code>
<p>Error: Agent execution timed out after 300000ms</p>
<p>Task: code-review</p>
<p>Conversation: abc-123-def</p>
<code>\`</code>

<p><strong>Diagnosis</strong>:</p>
<pre><code class="language-bash"># Check for hung processes
ps aux | grep claude | grep -v grep

# Check system load
uptime
# Output: load average: 12.5, 8.3, 5.2 (CPU overload!)

# Check for blocking I/O
iotop -o -d 5</code></pre>

<p><strong>Fix</strong>:</p>
<pre><code class="language-typescript">// Implement aggressive timeouts
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
);</code></pre>

<h3>3. Memory Leak</h3>

<p><strong>Symptoms</strong>:</p>
<pre><code class="language-bash"># Memory usage climbing over time
free -m
#              total   used   free
# Mem:         16384  15892    492  # Critical!

# Process memory
ps aux --sort=-%mem | head -5
# claude-daemon: 8.2GB (!)</code></pre>

<p><strong>Diagnosis</strong>:</p>
<pre><code class="language-typescript">// Track memory usage over time
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
}, 60000); // Every minute</code></pre>

<p><strong>Common Causes</strong>:</p>
<pre><code class="language-typescript">// ❌ Leak: Global cache never cleared
const cache = new Map<string, any>();
function addToCache(key: string, value: any) {
  cache.set(key, value); // Grows forever!
}

// ✅ Fix: LRU cache with size limit
import LRU from 'lru-cache';
const cache = new LRU<string, any>({ max: 1000 });</code></pre>

<h3>4. Plugin Crash Loop</h3>

<p><strong>Symptoms</strong>:</p>
<pre><code class="language-bash"># PM2 showing rapid restarts
pm2 status
# plugin-server | errored | 47 restarts in 2 minutes

# Logs show crash
tail -f /var/log/pm2/plugin-server-error.log
# Error: ECONNREFUSED 127.0.0.1:5432
# (PostgreSQL connection failed)</code></pre>

<p><strong>Diagnosis</strong>:</p>
<pre><code class="language-bash"># Check dependencies
docker ps | grep postgres
# (empty - PostgreSQL container not running!)

# Check network
netstat -tulpn | grep 5432
# (no listener on port 5432)</code></pre>

<p><strong>Fix</strong>:</p>
<pre><code class="language-bash"># Restart dependency
docker-compose up -d postgres

# Verify connectivity
psql -h localhost -U user -d database -c "SELECT 1"

# Restart plugin
pm2 restart plugin-server</code></pre>

<hr>

<h2>Debugging Techniques</h2>

<h3>1. Binary Search Debugging</h3>

<p><strong>Problem</strong>: Unknown change broke production</p>

<pre><code class="language-bash"># Use git bisect to find breaking commit
git bisect start
git bisect bad HEAD              # Current version is broken
git bisect good v1.2.0           # Last known good version

# Git will check out commits for testing
# Test each commit:
npm install && npm run build && npm test

# Mark results
git bisect good   # if tests pass
git bisect bad    # if tests fail

# Git will find the exact breaking commit</code></pre>

<h3>2. Correlation Analysis</h3>

<p><strong>Find patterns in failures</strong>:</p>
<pre><code class="language-typescript">interface FailureEvent {
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
}</code></pre>

<h3>3. Distributed Tracing</h3>

<p><strong>Track request across services</strong>:</p>
<pre><code class="language-typescript">import { trace, context, SpanStatusCode } from '@opentelemetry/api';

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
}</code></pre>

<hr>

<h2>Log Analysis</h2>

<h3>Parsing Claude Code Logs</h3>

<p><strong>Log Format</strong>:</p>
<code>\`</code>
<p>[2025-12-24T14:35:22.123Z] [ERROR] [agent:code-review] Rate limit exceeded</p>
<p>conversationId: abc-123-def</p>
<p>userId: user-456</p>
<p>errorCode: 429</p>
<p>retryAfter: 12</p>
<p>stack: Error: Rate limit exceeded</p>
<p>at callClaude (/app/src/api.ts:45:11)</p>
<code>\`</code>

<p><strong>Analysis Script</strong>:</p>
<pre><code class="language-typescript">import { readFileSync } from 'fs';

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
}</code></pre>

<h3>Using Analytics Daemon</h3>

<pre><code class="language-typescript">// Query analytics daemon for incident patterns
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

console.log(`Failed sessions: ${failedSessions.length}/${sessions.length}`);</code></pre>

<hr>

<h2>Root Cause Analysis</h2>

<h3>The 5 Whys Method</h3>

<p><strong>Example: Agent Timeout Incident</strong></p>

<ul>
<li><strong>Why did the agent timeout?</strong></li>
</ul>
<p>→ Because it took > 300 seconds to respond</p>

<ul>
<li><strong>Why did it take so long?</strong></li>
</ul>
<p>→ Because the Claude API call was slow (280s)</p>

<ul>
<li><strong>Why was the API call slow?</strong></li>
</ul>
<p>→ Because we sent a 50,000 token prompt</p>

<ul>
<li><strong>Why did we send such a large prompt?</strong></li>
</ul>
<p>→ Because the code-reviewer agent included entire codebase in context</p>

<ul>
<li><strong>Why did it include the entire codebase?</strong></li>
</ul>
<p>→ <strong>Root Cause</strong>: File globbing pattern </code>**/*<code> matched all files including node_modules (500MB)</p>

<p><strong>Fix</strong>: Update file globbing to exclude node_modules</p>
<pre><code class="language-typescript">// Before: includes everything
const files = glob.sync('**/*');

// After: exclude dependencies
const files = glob.sync('**/*', {
ignore: ['node_modules/<strong>', '.git/</strong>', 'dist/**']
});</code></pre>

<h3>Fishbone Diagram (Ishikawa)</h3>

<pre><code class="language-typescript">interface RootCauseAnalysis {
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
};</code></pre>

<hr>

<h2>Recovery Procedures</h2>

<h3>Emergency Rollback</h3>

<pre><code class="language-bash"># Immediate rollback to last known good version
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
curl http://api.example.com/health</code></pre>

<h3>Circuit Breaker Reset</h3>

<pre><code class="language-typescript">// Manually reset circuit breaker after fixing issue
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
}</code></pre>

<h3>Data Recovery</h3>

<pre><code class="language-bash"># Recover from backup
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
psql -d database_prod -c "SELECT COUNT(*) FROM conversations"</code></pre>

<hr>

<h2>Postmortem Templates</h2>

<h3>Incident Postmortem</h3>

<pre><code class="language-markdown"># Postmortem: Agent Timeout Incident (2025-12-24)

<strong>Date</strong>: 2025-12-24
<strong>Duration</strong>: 14:35 - 15:15 UTC (40 minutes)
<strong>Severity</strong>: SEV-2
<strong>Impact</strong>: 1,200 users (15%), 68% error rate

<h2>Summary</h2>
Code-reviewer agent began timing out due to excessive file inclusion in prompts, causing 68% error rate for 40 minutes.

<h2>Timeline (UTC)</h2>
<ul>
<li><strong>14:35</strong> - First timeout alerts</li>
<li><strong>14:40</strong> - Error rate reaches 68%</li>
<li><strong>14:42</strong> - On-call engineer paged</li>
<li><strong>14:45</strong> - Root cause identified (file globbing)</li>
<li><strong>14:50</strong> - Fix deployed to staging</li>
<li><strong>14:55</strong> - Fix deployed to production</li>
<li><strong>15:00</strong> - Error rate drops to 5%</li>
<li><strong>15:15</strong> - Incident resolved, error rate < 1%</li>
</ul>

<h2>Root Cause</h2>
File globbing pattern </code>**/*<code> included </code>node_modules/</code> directory (500MB), creating prompts exceeding Claude API's context limits and causing timeouts.

<h2>Contributing Factors</h2>
<ul>
<li>No file size validation before prompt construction</li>
<li>No integration tests with large codebases</li>
<li>No staging environment for testing</li>
</ul>

<h2>What Went Well</h2>
<ul>
<li>Fast root cause identification (10 minutes)</li>
<li>Effective rollback procedure</li>
<li>Clear communication to affected users</li>
</ul>

<h2>What Went Poorly</h2>
<ul>
<li>No monitoring alerts before user reports</li>
<li>No prompt size limits prevented the issue</li>
<li>Fix took 20 minutes to deploy</li>
</ul>

<h2>Action Items</h2>
<ul>
<li>[ ] <strong>P0</strong>: Add file size validation (Owner: @dev, Due: 2025-12-25)</li>
<li>[ ] <strong>P0</strong>: Implement max prompt size limit (Owner: @dev, Due: 2025-12-25)</li>
<li>[ ] <strong>P1</strong>: Add monitoring for agent timeouts (Owner: @ops, Due: 2025-12-27)</li>
<li>[ ] <strong>P1</strong>: Create staging environment (Owner: @ops, Due: 2025-12-30)</li>
<li>[ ] <strong>P2</strong>: Add integration tests with large repos (Owner: @qa, Due: 2026-01-05)</li>
</ul>

<h2>Lessons Learned</h2>
<ul>
<li>File operations need size limits</li>
<li>Production testing with realistic data is critical</li>
<li>Monitoring must detect issues before users report them</code></pre></li>
</ul>

<hr>

<h2>Best Practices</h2>

<h3>DO ✅</h3>

<ul>
<li><strong>Log structured data</strong></li>
</ul>
   <pre><code class="language-typescript">// ✅ Structured logging
   logger.error('Agent execution failed', {
     agentName: 'code-reviewer',
     conversationId: 'abc-123',
     errorCode: 429,
     duration: 1234
   });

// ❌ Unstructured
console.log('Error in code-reviewer agent');</code></pre>

<ul>
<li><strong>Set up alerts before incidents</strong></li>
</ul>
   <pre><code class="language-typescript">// Alert on error rate > 5%
   if (errorRate > 0.05) {
     pagerDuty.trigger({
       severity: 'critical',
       title: 'High error rate detected',
       details: `Error rate: ${(errorRate * 100).toFixed(1)}%`
     });
   }</code></pre>

<ul>
<li><strong>Keep runbooks updated</strong></li>
</ul>
   <pre><code class="language-markdown"># Agent Timeout Runbook

1. Check logs: <code>tail -f /var/log/claude-code.log | grep TIMEOUT</code>
2. Identify pattern: Which agents are timing out?
3. Check system resources: <code>top, free -m</code>, </code>df -h\`
4. If rate limits: Implement emergency throttling
5. If resource exhaustion: Restart services</code></pre>

<ul>
<li><strong>Test recovery procedures</strong></li>
</ul>
   <pre><code class="language-bash"># Monthly disaster recovery drill
   ./test-recovery.sh
   # 1. Trigger circuit breaker
   # 2. Verify monitoring alerts
   # 3. Execute rollback
   # 4. Verify service restoration</code></pre>

<h3>DON'T ❌</h3>

<ul>
<li><strong>Don't skip postmortems</strong></li>
</ul>
   <pre><code class="language-typescript">// ❌ Mark as resolved without learning
   incident.status = 'resolved';

// ✅ Document and learn
incident.status = 'resolved';
await createPostmortem(incident);
await scheduleReview(incident);</code></pre>

<ul>
<li><strong>Don't blame individuals</strong></li>
</ul>
   <pre><code class="language-markdown"># ❌ Blame-focused
   Root cause: Developer X wrote bad code

# ✅ System-focused
Root cause: Missing code review process for file operations</code></pre>

<ul>
<li><strong>Don't ignore warning signs</strong></li>
</ul>
   <pre><code class="language-typescript">// ❌ Suppress warnings
   if (memoryUsage > 0.8) {
     // TODO: Fix later
   }

// ✅ Alert and track
if (memoryUsage > 0.8) {
logger.warn('High memory usage', { usage: memoryUsage });
metrics.gauge('memory.usage', memoryUsage);
}</code></pre>

<hr>

<h2>Tools & Resources</h2>

<h3>Monitoring Tools</h3>

<p><strong>Analytics Daemon</strong> (from this marketplace):</p>
<pre><code class="language-bash">cd packages/analytics-daemon
pnpm start
# Real-time monitoring on http://localhost:3333</code></pre>

<p><strong>System Monitoring</strong>:</p>
<pre><code class="language-bash"># CPU, memory, disk
htop

# Network
iftop

# Disk I/O
iotop</code></pre>

<h3>Log Aggregation</h3>

<p><strong>Centralized logging</strong>:</p>
<pre><code class="language-bash"># Ship logs to central server
tail -f /var/log/claude-code.log | \
  nc logserver.example.com 514</code></pre>

<h3>External Tools</h3>

<ul>
<li><a href="https://www.datadoghq.com/">Datadog</a> - APM and monitoring</li>
<li><a href="https://sentry.io/">Sentry</a> - Error tracking</li>
<li><a href="https://www.pagerduty.com/">PagerDuty</a> - Incident management</li>
<li><a href="https://grafana.com/">Grafana</a> - Dashboards</li>
<li><a href="https://www.elastic.co/elk-stack">ELK Stack</a> - Log analysis</li>
</ul>

<hr>

<h2>Summary</h2>

<p><strong>Key Takeaways</strong>:</p>

<ul>
<li><strong>Classify incidents immediately</strong> - SEV-1/2 require immediate response</li>
<li><strong>Follow response protocol</strong> - Assess, stabilize, communicate</li>
<li><strong>Use systematic debugging</strong> - Binary search, correlation analysis, tracing</li>
<li><strong>Analyze logs effectively</strong> - Structured logging enables fast analysis</li>
<li><strong>Find root causes</strong> - 5 Whys and Fishbone diagrams prevent recurrence</li>
<li><strong>Document everything</strong> - Postmortems are learning opportunities</li>
<li><strong>Test recovery procedures</strong> - Practice makes perfect</li>
</ul>

<p><strong>Incident Response Checklist</strong>:</p>
<ul>
<li>[ ] Classify severity (SEV-1 through SEV-4)</li>
<li>[ ] Assess impact (error rate, affected users)</li>
<li>[ ] Check obvious issues (API, disk, memory)</li>
<li>[ ] Stabilize systems (restart, rate limit, rollback)</li>
<li>[ ] Communicate status to stakeholders</li>
<li>[ ] Identify root cause (5 Whys, logs, metrics)</li>
<li>[ ] Deploy fix and verify recovery</li>
<li>[ ] Write postmortem within 24 hours</li>
<li>[ ] Create action items with owners and dates</li>
<li>[ ] Schedule review meeting with team</li>
</ul>

<hr>

<p><strong>Last Updated</strong>: 2025-12-24</p>
<p><strong>Author</strong>: Jeremy Longshore</p>
<p><strong>Related Playbooks</strong>: <a href="./01-multi-agent-rate-limits.md">Multi-Agent Rate Limits</a>, <a href="./03-mcp-reliability.md">MCP Server Reliability</a></p>
