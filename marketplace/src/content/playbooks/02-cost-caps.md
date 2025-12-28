---
title: "Cost Caps & Budget Management"
description: "Hard budget controls for AI spending. Real-time spend tracking, automatic shutoffs, team quotas, and financial safeguards to prevent runaway costs."
category: "Cost"
wordCount: 3200
readTime: 16
featured: false
order: 2
tags: ["cost", "budget", "spending", "quotas", "optimization"]
prerequisites: []
relatedPlaybooks: ["01-multi-agent-rate-limits", "09-cost-attribution"]
---

<p>API costs can spiral quickly when running multi-agent workflows at scale. This playbook provides proven strategies for implementing cost controls, monitoring spend in real-time, and optimizing Claude API usage without sacrificing quality.</p>

<h2>Understanding API Costs</h2>

<h3>Anthropic Claude Pricing (January 2025)</h3>

<table>
<thead>
<tr>
<th>Model</th>
<th>Input (per 1M tokens)</th>
<th>Output (per 1M tokens)</th>
<th>Context Window</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Claude 3.5 Sonnet</strong></td>
<td>$3.00</td>
<td>$15.00</td>
<td>200K</td>
</tr>
<tr>
<td><strong>Claude 3.5 Haiku</strong></td>
<td>$0.80</td>
<td>$4.00</td>
<td>200K</td>
</tr>
<tr>
<td><strong>Claude 3 Opus</strong></td>
<td>$15.00</td>
<td>$75.00</td>
<td>200K</td>
</tr>
</tbody>
</table>

<p><strong>Reality Check</strong>: A single code review session can cost:</p>
<ul>
<li>Small file (500 tokens): $0.0075 (Sonnet)</li>
<li>Large file (5,000 tokens): $0.075 (Sonnet)</li>
<li>Full repository (50,000 tokens): $0.75 (Sonnet)</li>
</ul>

<h3>Hidden Cost Drivers</h3>

<pre><code class="language-typescript">// ❌ This conversation costs $4.50
const response = await claude.messages.create({
  model: 'claude-3-5-sonnet-20241022',
  max_tokens: 4096,
  messages: [{
    role: 'user',
    content: `Review this entire codebase: ${fs.readFileSync('monorepo.txt')}` // 250K tokens
  }]
});

// Breakdown:
// - Input: 250K tokens × $3/1M = $0.75
// - Output: 4K tokens × $15/1M = $0.06
// - Total per call: $0.81
//
// Multi-agent workflow (5 agents):
// - 5 agents × $0.81 = $4.05
// - Daily runs: 10
// - Monthly cost: $4.05 × 10 × 30 = $1,215</code></pre>

<hr>

<h2>Cost Tracking</h2>

<h3>1. Real-Time Token Counting</h3>

<pre><code class="language-typescript">import Anthropic from '@anthropic-ai/sdk';

interface CostMetrics {
inputTokens: number;
outputTokens: number;
inputCost: number;
outputCost: number;
totalCost: number;
model: string;
}

class CostTracker {
private costs: CostMetrics[] = [];

// Pricing table (per 1M tokens)
private pricing = {
'claude-3-5-sonnet-20241022': { input: 3.00, output: 15.00 },
'claude-3-5-haiku-20241022': { input: 0.80, output: 4.00 },
'claude-3-opus-20240229': { input: 15.00, output: 75.00 },
};

track(usage: Anthropic.Usage, model: string): CostMetrics {
const prices = this.pricing[model];

const metrics: CostMetrics = {
inputTokens: usage.input_tokens,
outputTokens: usage.output_tokens,
inputCost: (usage.input_tokens / 1_000_000) * prices.input,
outputCost: (usage.output_tokens / 1_000_000) * prices.output,
totalCost: 0,
model
};

metrics.totalCost = metrics.inputCost + metrics.outputCost;
this.costs.push(metrics);

return metrics;
}

getTotalCost(): number {
return this.costs.reduce((sum, c) => sum + c.totalCost, 0);
}

getCostByModel(model: string): number {
return this.costs
.filter(c => c.model === model)
.reduce((sum, c) => sum + c.totalCost, 0);
}

getAverageCostPerRequest(): number {
return this.getTotalCost() / this.costs.length;
}
}

// Usage
const tracker = new CostTracker();

const response = await claude.messages.create({
model: 'claude-3-5-sonnet-20241022',
messages: [...]
});

const cost = tracker.track(response.usage, response.model);
console.log(`Request cost: $${cost.totalCost.toFixed(4)}`);
console.log(`Total spent: $${tracker.getTotalCost().toFixed(2)}`);</code></pre>

<h3>2. Analytics Daemon Integration</h3>

<p>The <code>@claude-code-plugins/analytics-daemon</code> emits cost events:</p>

<pre><code class="language-typescript">// WebSocket event from analytics daemon
interface CostUpdateEvent {
  type: 'cost.update';
  timestamp: number;
  conversationId: string;
  model: 'claude-3-5-sonnet-20241022';
  inputCost: 0.0045;
  outputCost: 0.012;
  totalCost: 0.0165;
  currency: 'USD';
}

// Monitor costs in real-time
const ws = new WebSocket('ws://localhost:3456');
ws.onmessage = (event) => {
const data = JSON.parse(event.data);
if (data.type === 'cost.update') {
updateBudget(data.totalCost);
}
};</code></pre>

<h3>3. Daily Budget Dashboard</h3>

<p>Query costs via HTTP API:</p>

<pre><code class="language-bash"># Get session costs
curl http://localhost:3333/api/sessions | jq '.sessions[] | {id, plugins, totalCost}'

# Get status including total spend
curl http://localhost:3333/api/status | jq '.watcher'</code></pre>

<hr>

<h2>Budget Enforcement</h2>

<h3>Strategy 1: Hard Caps with Circuit Breakers</h3>

<pre><code class="language-typescript">class BudgetEnforcer {
  private spent = 0;
  private dailyBudget: number;
  private lastReset: Date;

constructor(dailyBudgetUSD: number) {
this.dailyBudget = dailyBudgetUSD;
this.lastReset = new Date();
}

async executeWithBudget<T>(
fn: () => Promise<{ result: T; cost: number }>
): Promise<T> {
// Reset budget if new day
if (this.isNewDay()) {
this.spent = 0;
this.lastReset = new Date();
}

// Check budget before execution
if (this.spent >= this.dailyBudget) {
throw new Error(
`Daily budget exceeded: $${this.spent.toFixed(2)} / $${this.dailyBudget}`
);
}

const { result, cost } = await fn();

this.spent += cost;

// Warn at 80%
if (this.spent >= this.dailyBudget * 0.8) {
console.warn(
`⚠️ 80% of daily budget used: $${this.spent.toFixed(2)} / $${this.dailyBudget}`
);
}

return result;
}

private isNewDay(): boolean {
const now = new Date();
return now.toDateString() !== this.lastReset.toDateString();
}

getRemainingBudget(): number {
return Math.max(0, this.dailyBudget - this.spent);
}

getSpendPercentage(): number {
return (this.spent / this.dailyBudget) * 100;
}
}

// Usage
const budget = new BudgetEnforcer(50.00); // $50/day

try {
await budget.executeWithBudget(async () => {
const response = await claude.messages.create(...);
const cost = calculateCost(response.usage);
return { result: response, cost };
});
} catch (error) {
// Budget exceeded - halt operations
console.error('Budget exhausted for today');
}</code></pre>

<h3>Strategy 2: Tiered Budgets by Priority</h3>

<pre><code class="language-typescript">enum Priority {
  CRITICAL = 'critical',  // $100/day
  HIGH = 'high',          // $50/day
  MEDIUM = 'medium',      // $20/day
  LOW = 'low'             // $5/day
}

class TieredBudget {
private budgets = new Map<Priority, BudgetEnforcer>([
[Priority.CRITICAL, new BudgetEnforcer(100)],
[Priority.HIGH, new BudgetEnforcer(50)],
[Priority.MEDIUM, new BudgetEnforcer(20)],
[Priority.LOW, new BudgetEnforcer(5)],
]);

async execute<T>(
priority: Priority,
fn: () => Promise<{ result: T; cost: number }>
): Promise<T> {
const budget = this.budgets.get(priority)!;
return await budget.executeWithBudget(fn);
}

getStatus() {
return Array.from(this.budgets.entries()).map(([priority, budget]) => ({
priority,
spent: budget.getSpendPercentage().toFixed(1) + '%',
remaining: '$' + budget.getRemainingBudget().toFixed(2)
}));
}
}

// Usage
const tiered = new TieredBudget();

// Critical: Production incident debugging
await tiered.execute(Priority.CRITICAL, async () => {
const result = await debugIncident();
return { result, cost: 0.50 };
});

// Low: Non-urgent code reviews
await tiered.execute(Priority.LOW, async () => {
const result = await reviewCode();
return { result, cost: 0.05 };
});</code></pre>

<h3>Strategy 3: Per-User Quotas</h3>

<pre><code class="language-typescript">class UserQuotaManager {
  private userBudgets = new Map<string, number>();
  private userSpent = new Map<string, number>();

constructor(private defaultQuota: number = 10) {}

setQuota(userId: string, quotaUSD: number) {
this.userBudgets.set(userId, quotaUSD);
}

async executeForUser<T>(
userId: string,
fn: () => Promise<{ result: T; cost: number }>
): Promise<T> {
const quota = this.userBudgets.get(userId) || this.defaultQuota;
const spent = this.userSpent.get(userId) || 0;

if (spent >= quota) {
throw new Error(
`User ${userId} quota exceeded: $${spent.toFixed(2)} / $${quota}`
);
}

const { result, cost } = await fn();
this.userSpent.set(userId, spent + cost);

return result;
}

getUserStatus(userId: string) {
const quota = this.userBudgets.get(userId) || this.defaultQuota;
const spent = this.userSpent.get(userId) || 0;

return {
userId,
quota: `$${quota}`,
spent: `$${spent.toFixed(2)}`,
remaining: `$${(quota - spent).toFixed(2)}`,
percentage: `${((spent / quota) * 100).toFixed(1)}%`
};
}
}</code></pre>

<hr>

<h2>Optimization Strategies</h2>

<h3>1. Model Selection by Task</h3>

<pre><code class="language-typescript">// Cost comparison for 10K token input + 1K token output

const models = {
sonnet: {
input: (10_000 / 1_000_000) * 3.00,   // $0.03
output: (1_000 / 1_000_000) * 15.00,  // $0.015
total: 0.045                           // $0.045
},
haiku: {
input: (10_000 / 1_000_000) * 0.80,   // $0.008
output: (1_000 / 1_000_000) * 4.00,   // $0.004
total: 0.012                           // $0.012 (73% cheaper!)
},
opus: {
input: (10_000 / 1_000_000) * 15.00,  // $0.15
output: (1_000 / 1_000_000) * 75.00,  // $0.075
total: 0.225                           // $0.225 (5x more expensive)
}
};

// Smart model selection
function selectModel(task: AgentTask): string {
if (task.requiresReasoning) {
return 'claude-3-5-sonnet-20241022'; // Best reasoning
} else if (task.isSimple) {
return 'claude-3-5-haiku-20241022';  // 73% cost savings
} else {
return 'claude-3-5-sonnet-20241022'; // Default
}
}

// Real savings example:
// 1000 simple tasks/day × $0.045 (Sonnet) = $45/day
// 1000 simple tasks/day × $0.012 (Haiku) = $12/day
// Savings: $33/day = $990/month</code></pre>

<h3>2. Context Window Optimization</h3>

<pre><code class="language-typescript">// ❌ Expensive: Send entire codebase every time
async function reviewFile(file: string, codebase: string) {
  return await claude.messages.create({
    model: 'claude-3-5-sonnet-20241022',
    messages: [{
      role: 'user',
      content: `Codebase context:\n${codebase}\n\nReview:\n${file}` // 100K + 5K tokens
    }]
  });
}
// Cost per call: 100K tokens × $3/1M = $0.30

// ✅ Optimized: Send only relevant context
async function reviewFileOptimized(file: string, relatedFiles: string[]) {
const context = relatedFiles.join('\n'); // 10K tokens
return await claude.messages.create({
model: 'claude-3-5-sonnet-20241022',
messages: [{
role: 'user',
content: `Related files:\n${context}\n\nReview:\n${file}` // 10K + 5K tokens
}]
});
}
// Cost per call: 15K tokens × $3/1M = $0.045 (85% cheaper!)</code></pre>

<h3>3. Caching Strategy</h3>

<pre><code class="language-typescript">class ResponseCache {
  private cache = new Map<string, { response: any; cost: number; timestamp: number }>();
  private ttl = 3600000; // 1 hour

async execute<T>(
cacheKey: string,
fn: () => Promise<{ result: T; cost: number }>
): Promise<{ result: T; cost: number; cached: boolean }> {
const cached = this.cache.get(cacheKey);

if (cached && Date.now() - cached.timestamp < this.ttl) {
console.log(`Cache hit: $${cached.cost.toFixed(4)} saved`);
return { result: cached.response, cost: 0, cached: true };
}

const { result, cost } = await fn();

this.cache.set(cacheKey, {
response: result,
cost,
timestamp: Date.now()
});

return { result, cost, cached: false };
}

getCacheStats() {
const entries = Array.from(this.cache.values());
return {
entries: entries.length,
totalSavings: entries.reduce((sum, e) => sum + e.cost, 0),
hitRate: 0 // Track separately
};
}
}

// Usage
const cache = new ResponseCache();

const { result, cost, cached } = await cache.execute(
`code-review-${fileHash}`,
async () => {
const response = await claude.messages.create(...);
return { result: response, cost: calculateCost(response.usage) };
}
);

// Real impact:
// 100 requests/day, 30% cache hit rate
// Without cache: 100 × $0.045 = $4.50/day
// With cache: 70 × $0.045 = $3.15/day
// Savings: $1.35/day = $40.50/month</code></pre>

<h3>4. Batch Processing</h3>

<pre><code class="language-typescript">// ❌ Process files individually
async function reviewFiles(files: string[]) {
  for (const file of files) {
    await claude.messages.create({
      messages: [{ role: 'user', content: `Review: ${file}` }]
    });
  }
}
// Cost: 10 files × $0.045 = $0.45

// ✅ Batch process
async function reviewFilesBatch(files: string[]) {
const batches = chunk(files, 10); // 10 files per batch

for (const batch of batches) {
await claude.messages.create({
messages: [{
role: 'user',
content: `Review these files:\n${batch.map((f, i) => `${i+1}. ${f}`).join('\n')}`
}]
});
}
}
// Cost: 1 batch × $0.05 = $0.05 (90% cheaper!)</code></pre>

<hr>

<h2>Production Examples</h2>

<h3>Example 1: Plugin Marketplace Review</h3>

<pre><code class="language-typescript">// Scenario: Review 258 plugins for security issues
// Average plugin size: 5K tokens
// Total tokens: 258 × 5K = 1.29M tokens

const budget = new BudgetEnforcer(10.00); // $10 budget
const cache = new ResponseCache();
const tracker = new CostTracker();

async function reviewPlugins() {
const plugins = await getPlugins(); // 258 plugins
const results = [];

for (const plugin of plugins) {
try {
await budget.executeWithBudget(async () => {
const { result, cost, cached } = await cache.execute(
`security-review-${plugin.id}`,
async () => {
const response = await claude.messages.create({
model: 'claude-3-5-haiku-20241022', // Use cheaper model
max_tokens: 500,
messages: [{
role: 'user',
content: `Security review:\n${plugin.code}`
}]
});

const metrics = tracker.track(response.usage, response.model);
return { result: response, cost: metrics.totalCost };
}
);

results.push({ plugin: plugin.name, review: result, cached });
return { result, cost };
});
} catch (error) {
console.error(`Budget exceeded at plugin ${plugin.name}`);
break;
}
}

return results;
}

// Real metrics:
// - Cost without optimization: 258 × $0.045 = $11.61 (exceeds budget)
// - Cost with Haiku: 258 × $0.012 = $3.10 (73% savings)
// - Cost with 50% cache: 129 × $0.012 = $1.55 (87% savings)
// - Plugins reviewed: 258 (all)
// - Budget remaining: $8.45</code></pre>

<h3>Example 2: Cost Attribution by Team</h3>

<pre><code class="language-typescript">interface Team {
  name: string;
  members: string[];
  monthlyBudget: number;
}

class TeamBudgetManager {
private teams = new Map<string, Team>();
private teamSpend = new Map<string, number>();

addTeam(team: Team) {
this.teams.set(team.name, team);
this.teamSpend.set(team.name, 0);
}

async executeForTeam<T>(
teamName: string,
userId: string,
fn: () => Promise<{ result: T; cost: number }>
): Promise<T> {
const team = this.teams.get(teamName);
if (!team) throw new Error(`Unknown team: ${teamName}`);
if (!team.members.includes(userId)) {
throw new Error(`User ${userId} not in team ${teamName}`);
}

const spent = this.teamSpend.get(teamName) || 0;
if (spent >= team.monthlyBudget) {
throw new Error(`Team ${teamName} budget exceeded`);
}

const { result, cost } = await fn();
this.teamSpend.set(teamName, spent + cost);

return result;
}

getTeamReport(teamName: string) {
const team = this.teams.get(teamName)!;
const spent = this.teamSpend.get(teamName) || 0;

return {
team: teamName,
members: team.members.length,
budget: `$${team.monthlyBudget}`,
spent: `$${spent.toFixed(2)}`,
remaining: `$${(team.monthlyBudget - spent).toFixed(2)}`,
percentageUsed: `${((spent / team.monthlyBudget) * 100).toFixed(1)}%`,
daysRemaining: 30 - new Date().getDate(),
projectedOverage: spent / new Date().getDate() * 30 > team.monthlyBudget
};
}
}

// Usage
const manager = new TeamBudgetManager();

manager.addTeam({
name: 'Engineering',
members: ['alice@example.com', 'bob@example.com'],
monthlyBudget: 500
});

manager.addTeam({
name: 'QA',
members: ['charlie@example.com'],
monthlyBudget: 100
});

// Engineering team member makes request
await manager.executeForTeam('Engineering', 'alice@example.com', async () => {
const result = await runTests();
return { result, cost: 2.50 };
});

console.log(manager.getTeamReport('Engineering'));
// {
//   team: 'Engineering',
//   members: 2,
//   budget: '$500',
//   spent: '$2.50',
//   remaining: '$497.50',
//   percentageUsed: '0.5%',
//   daysRemaining: 7,
//   projectedOverage: false
// }</code></pre>

<hr>

<h2>ROI Analysis</h2>

<h3>Cost vs. Value Metrics</h3>

<pre><code class="language-typescript">interface WorkflowMetrics {
  name: string;
  costPerRun: number;
  timesSaved: number;    // minutes
  errorsPrevented: number;
  manualCost: number;    // $ per hour equivalent
}

function calculateROI(metrics: WorkflowMetrics): number {
const timeSavingsValue = (metrics.timesSaved / 60) * metrics.manualCost;
const errorCostSavings = metrics.errorsPrevented * 100; // $100 per error

const totalValue = timeSavingsValue + errorCostSavings;
const totalCost = metrics.costPerRun;

return ((totalValue - totalCost) / totalCost) * 100;
}

// Example: Automated Code Review
const codeReviewMetrics: WorkflowMetrics = {
name: 'Automated Code Review',
costPerRun: 0.50,           // Claude API cost
timesSaved: 30,              // 30 minutes saved
errorsPrevented: 3,          // 3 bugs caught
manualCost: 100              // $100/hour developer time
};

const roi = calculateROI(codeReviewMetrics);
// timeSavingsValue: (30/60) × $100 = $50
// errorCostSavings: 3 × $100 = $300
// totalValue: $350
// totalCost: $0.50
// ROI: (($350 - $0.50) / $0.50) × 100 = 69,900%

console.log(`ROI: ${roi.toFixed(0)}%`); // 69,900% ROI</code></pre>

<h3>Break-Even Analysis</h3>

<table>
<thead>
<tr>
<th>Workflow</th>
<th>API Cost/Run</th>
<th>Manual Cost/Run</th>
<th>Runs to Break Even</th>
</tr>
</thead>
<tbody>
<tr>
<td>Code Review</td>
<td>$0.50</td>
<td>$50</td>
<td>1</td>
</tr>
<tr>
<td>Test Generation</td>
<td>$2.00</td>
<td>$200</td>
<td>1</td>
</tr>
<tr>
<td>Documentation</td>
<td>$1.00</td>
<td>$80</td>
<td>1</td>
</tr>
<tr>
<td>Bug Triage</td>
<td>$0.25</td>
<td>$25</td>
<td>1</td>
</tr>
</tbody>
</table>

<p><strong>Key Insight</strong>: Even "expensive" AI workflows pay for themselves in the first run.</p>

<hr>

<h2>Best Practices</h2>

<h3>DO ✅</h3>

<ul>
<li><strong>Track every API call</strong></li>
</ul>
   <pre><code class="language-typescript">const tracker = new CostTracker();
   // Log costs to analytics daemon</code></pre>

<ul>
<li><strong>Set hard budget limits</strong></li>
</ul>
   <pre><code class="language-typescript">const budget = new BudgetEnforcer(50); // Never exceed $50/day</code></pre>

<ul>
<li><strong>Use model selection</strong></li>
</ul>
   <pre><code class="language-typescript">const model = task.isComplex ? 'sonnet' : 'haiku'; // 73% savings</code></pre>

<ul>
<li><strong>Cache responses</strong></li>
</ul>
   <pre><code class="language-typescript">const cache = new ResponseCache();
   // 30% cache hit rate = 30% cost savings</code></pre>

<ul>
<li><strong>Monitor in real-time</strong></li>
</ul>
   <pre><code class="language-bash">ccp-analytics  # Watch costs live</code></pre>

<h3>DON'T ❌</h3>

<ul>
<li><strong>Don't use Opus for everything</strong></li>
</ul>
   <pre><code class="language-typescript">// ❌ 5x more expensive than Sonnet
   model: 'claude-3-opus-20240229'</code></pre>

<ul>
<li><strong>Don't send full codebase every time</strong></li>
</ul>
   <pre><code class="language-typescript">// ❌ Wastes 90% of tokens
   content: fs.readFileSync('entire-repo.txt')</code></pre>

<ul>
<li><strong>Don't ignore token usage</strong></li>
</ul>
   <pre><code class="language-typescript">// ❌ No cost tracking
   await claude.messages.create({...});</code></pre>

<ul>
<li><strong>Don't run without budgets</strong></li>
</ul>
   <pre><code class="language-typescript">// ❌ Unlimited spending = surprise bills
   while (true) { await expensiveCall(); }</code></pre>

<hr>

<h2>Tools & Resources</h2>

<h3>Analytics Daemon</h3>
<p>Monitor costs in real-time:</p>
<pre><code class="language-bash">cd packages/analytics-daemon
pnpm start
# Cost events: ws://localhost:3456
# Cost API: http://localhost:3333/api/status</code></pre>

<h3>Anthropic Dashboard</h3>
<p>Official cost tracking: <a href="https://console.anthropic.com/">console.anthropic.com</a></p>

<h3>Plugins with Built-in Cost Optimization</h3>
<ul>
<li><code>performance-engineer</code> - Automatic model selection</li>
<li><code>cost-optimizer</code> - Budget tracking</li>
<li><code>cache-manager</code> - Response caching</li>
</ul>

<hr>

<h2>Summary</h2>

<p><strong>Key Takeaways</strong>:</p>

<ul>
<li><strong>Sonnet</strong>: $3/1M input, $15/1M output - Production standard</li>
<li><strong>Haiku</strong>: 73% cheaper - Use for simple tasks</li>
<li><strong>Context optimization</strong>: 85% cost savings</li>
<li><strong>Caching</strong>: 30% cost savings</li>
<li><strong>Budget enforcement</strong>: Prevents runaway costs</li>
</ul>

<p><strong>Cost Control Checklist</strong>:</p>
<ul>
<li>[ ] Implement CostTracker</li>
<li>[ ] Set daily budget limits</li>
<li>[ ] Use Haiku for simple tasks</li>
<li>[ ] Optimize context windows</li>
<li>[ ] Enable response caching</li>
<li>[ ] Monitor with analytics daemon</li>
<li>[ ] Calculate ROI for workflows</li>
<li>[ ] Set up team quotas</li>
</ul>

<hr>

<p><strong>Last Updated</strong>: 2025-12-24</p>
<p><strong>Author</strong>: Jeremy Longshore</p>
<p><strong>Related Playbooks</strong>: <a href="./01-multi-agent-rate-limits.md">Multi-Agent Rate Limits</a>, <a href="./09-cost-attribution.md">Cost Attribution System</a></p>
