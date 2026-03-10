---
title: "Cost Attribution System"
description: "Multi-dimensional cost tracking (team/project/user/workflow). Automatic tagging, chargeback models, budget enforcement, and usage analytics for AI operations."
category: "Cost"
wordCount: 5500
readTime: 28
featured: false
order: 9
tags: ["cost", "attribution", "chargeback", "budget", "analytics"]
prerequisites: []
relatedPlaybooks: ["02-cost-caps", "08-team-presets"]
---

<p><strong>Production Playbook for Finance Teams and Engineering Managers</strong></p>

<p>Tracking AI infrastructure costs by team, project, user, and workflow enables accurate chargeback, budget management, and cost optimization. This playbook provides cost tagging strategies, budget enforcement, chargeback models, usage analytics, and optimization recommendations for Claude Code deployments.</p>

<h2>Cost Attribution Strategy</h2>

<h3>Cost Dimensions</h3>

<pre><code class="language-typescript">interface CostAttribution {
  // Primary dimensions
  team: string;              // engineering-backend
  project: string;           // api-server
  user: string;              // user-123
  workflow: string;          // code-review

<p>// Secondary dimensions</p>
<p>environment: 'dev' | 'staging' | 'production';</p>
<p>region: string;            // us-east-1</p>
<p>costCenter: string;        // eng-001</p>

<p>// Cost details</p>
<p>provider: 'anthropic' | 'ollama' | 'self-hosted';</p>
<p>model: string;             // claude-3-5-sonnet-20241022</p>
<p>inputTokens: number;</p>
<p>outputTokens: number;</p>
<p>cost: number;              // USD</p>
<p>timestamp: number;</p>
<p>}</code></pre></p>

<h3>Attribution Hierarchy</h3>

<pre><code class="language-mermaid">graph TB
    A[Organization] --> B[Cost Center]
    B --> C[Team]
    C --> D[Project]
    D --> E[User]
    E --> F[Workflow]
    F --> G[API Call]</code></pre>

<p><strong>Roll-up Example</strong>:</p>
<ul>
<li><strong>API Call</strong>: $0.015 (Claude API call)</li>
<li><strong>Workflow</strong> (code-review): $0.045 (3 API calls)</li>
<li><strong>User</strong> (alice): $2.50/day (multiple workflows)</li>
<li><strong>Project</strong> (api-server): $75/day (multiple users)</li>
<li><strong>Team</strong> (backend): $300/day (4 projects)</li>
<li><strong>Cost Center</strong> (eng-001): $1,200/day (4 teams)</li>
</ul>

<hr>

<h2>Cost Tagging</h2>

<h3>Automatic Cost Tagging</h3>

<pre><code class="language-typescript">class CostTagger {
  async tagAPICall(
    request: any,
    context: {
      userId: string;
      teamId: string;
      projectId: string;
      workflow: string;
    }
  ): Promise<CostAttribution> {
    // Calculate cost
    const inputCost = (request.inputTokens / 1_000_000) * 3.00;  // $3/1M
    const outputCost = (request.outputTokens / 1_000_000) * 15.00; // $15/1M
    const totalCost = inputCost + outputCost;

<p>// Create attribution record</p>
<p>const attribution: CostAttribution = {</p>
<p>team: context.teamId,</p>
<p>project: context.projectId,</p>
<p>user: context.userId,</p>
<p>workflow: context.workflow,</p>
<p>environment: process.env.NODE_ENV as any,</p>
<p>region: process.env.AWS_REGION || 'us-east-1',</p>
<p>costCenter: await this.getCostCenter(context.teamId),</p>
<p>provider: 'anthropic',</p>
<p>model: request.model,</p>
<p>inputTokens: request.inputTokens,</p>
<p>outputTokens: request.outputTokens,</p>
<p>cost: totalCost,</p>
<p>timestamp: Date.now()</p>
<p>};</p>

<p>// Store for analysis</p>
<p>await this.storeCostData(attribution);</p>

<p>return attribution;</p>
<p>}</p>

<p>private async getCostCenter(teamId: string): Promise<string> {</p>
<p>const teamMapping: Record<string, string> = {</p>
<p>'engineering-backend': 'eng-001',</p>
<p>'engineering-frontend': 'eng-002',</p>
<p>'product': 'prod-001',</p>
<p>'marketing': 'mkt-001'</p>
<p>};</p>

<p>return teamMapping[teamId] || 'unallocated';</p>
<p>}</p>

<p>private async storeCostData(attribution: CostAttribution): Promise<void> {</p>
<p>// Option 1: PostgreSQL</p>
<p>await db.costs.insert(attribution);</p>

<p>// Option 2: Time-series database (InfluxDB)</p>
<p>await influx.writePoint({</p>
<p>measurement: 'api_costs',</p>
<p>tags: {</p>
<p>team: attribution.team,</p>
<p>project: attribution.project,</p>
<p>environment: attribution.environment</p>
<p>},</p>
<p>fields: {</p>
<p>cost: attribution.cost,</p>
<p>inputTokens: attribution.inputTokens,</p>
<p>outputTokens: attribution.outputTokens</p>
<p>},</p>
<p>timestamp: attribution.timestamp</p>
<p>});</p>

<p>// Option 3: Export to CSV for billing</p>
<p>await this.appendToCSV(attribution);</p>
<p>}</p>

<p>private async appendToCSV(attribution: CostAttribution): Promise<void> {</p>
<p>const line = [</p>
<p>new Date(attribution.timestamp).toISOString(),</p>
<p>attribution.team,</p>
<p>attribution.project,</p>
<p>attribution.user,</p>
<p>attribution.workflow,</p>
<p>attribution.provider,</p>
<p>attribution.model,</p>
<p>attribution.inputTokens,</p>
<p>attribution.outputTokens,</p>
<p>attribution.cost.toFixed(4)</p>
<p>].join(',') + '\n';</p>

<p>await appendFile('/var/log/costs/costs.csv', line);</p>
<p>}</p>
<p>}</code></pre></p>

<h3>Usage Example</h3>

<pre><code class="language-typescript">// Intercept all API calls and tag costs
const tagger = new CostTagger();

<p>async function callClaudeWithTagging(prompt: string, context: any): Promise<string> {</p>
<p>const startTime = Date.now();</p>

<p>const response = await anthropic.messages.create({</p>
<p>model: 'claude-3-5-sonnet-20241022',</p>
<p>max_tokens: 1024,</p>
<p>messages: [{ role: 'user', content: prompt }]</p>
<p>});</p>

<p>// Tag costs</p>
<p>await tagger.tagAPICall({</p>
<p>model: 'claude-3-5-sonnet-20241022',</p>
<p>inputTokens: response.usage.input_tokens,</p>
<p>outputTokens: response.usage.output_tokens</p>
<p>}, {</p>
<p>userId: context.userId,</p>
<p>teamId: context.teamId,</p>
<p>projectId: context.projectId,</p>
<p>workflow: context.workflow</p>
<p>});</p>

<p>return response.content[0].text;</p>
<p>}</code></pre></p>

<hr>

<h2>Budget Management</h2>

<h3>Budget Enforcement</h3>

<pre><code class="language-typescript">interface Budget {
  id: string;
  entity: { type: 'team' | 'project' | 'user'; id: string };
  period: 'daily' | 'weekly' | 'monthly';
  limit: number;  // USD
  alertThresholds: number[];  // [0.5, 0.8, 0.9]
  enforced: boolean;
}

<p>class BudgetManager {</p>
<p>private budgets: Map<string, Budget> = new Map();</p>

<p>async setBudget(budget: Budget): Promise<void> {</p>
<p>this.budgets.set(budget.id, budget);</p>
<p>await db.budgets.upsert(budget);</p>
<p>}</p>

<p>async checkBudget(</p>
<p>entityType: 'team' | 'project' | 'user',</p>
<p>entityId: string</p>
<p>): Promise<{ allowed: boolean; spent: number; limit: number; remaining: number }> {</p>
<p>// Find budget</p>
<p>const budget = await this.findBudget(entityType, entityId);</p>
<p>if (!budget) {</p>
<p>return { allowed: true, spent: 0, limit: Infinity, remaining: Infinity };</p>
<p>}</p>

<p>// Calculate current period spend</p>
<p>const periodStart = this.getPeriodStart(budget.period);</p>
<p>const spent = await this.calculateSpend(entityType, entityId, periodStart);</p>

<p>// Check against limit</p>
<p>const allowed = !budget.enforced || spent < budget.limit;</p>
<p>const remaining = budget.limit - spent;</p>

<p>// Check alert thresholds</p>
<p>const utilizationRate = spent / budget.limit;</p>
<p>for (const threshold of budget.alertThresholds) {</p>
<p>if (utilizationRate >= threshold && utilizationRate < threshold + 0.01) {</p>
<p>await this.sendBudgetAlert(budget, spent, utilizationRate);</p>
<p>}</p>
<p>}</p>

<p>return { allowed, spent, limit: budget.limit, remaining };</p>
<p>}</p>

<p>private getPeriodStart(period: 'daily' | 'weekly' | 'monthly'): number {</p>
<p>const now = new Date();</p>

<p>switch (period) {</p>
<p>case 'daily':</p>
<p>return new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();</p>
<p>case 'weekly':</p>
<p>const weekStart = new Date(now);</p>
<p>weekStart.setDate(now.getDate() - now.getDay());</p>
<p>return weekStart.getTime();</p>
<p>case 'monthly':</p>
<p>return new Date(now.getFullYear(), now.getMonth(), 1).getTime();</p>
<p>}</p>
<p>}</p>

<p>private async calculateSpend(</p>
<p>entityType: string,</p>
<p>entityId: string,</p>
<p>since: number</p>
<p>): Promise<number> {</p>
<p>const costs = await db.costs.find({</p>
<p>[entityType]: entityId,</p>
<p>timestamp: { $gte: since }</p>
<p>});</p>

<p>return costs.reduce((sum, c) => sum + c.cost, 0);</p>
<p>}</p>

<p>private async findBudget(entityType: string, entityId: string): Promise<Budget | null> {</p>
<p>return await db.budgets.findOne({</p>
<p>'entity.type': entityType,</p>
<p>'entity.id': entityId</p>
<p>});</p>
<p>}</p>

<p>private async sendBudgetAlert(budget: Budget, spent: number, rate: number): Promise<void> {</p>
<p>const message = <code></p>
<p>Budget Alert: ${budget.entity.type} ${budget.entity.id}</p>

<p>Current spend: $${spent.toFixed(2)}</p>
<p>Budget limit: $${budget.limit.toFixed(2)}</p>
<p>Utilization: ${(rate * 100).toFixed(1)}%</p>

<p>Period: ${budget.period}</p>
    </code>.trim();

<p>// Send to Slack, email, PagerDuty, etc.</p>
<p>console.warn(message);</p>
<p>}</p>
<p>}</code></pre></p>

<h3>Usage with Budget Enforcement</h3>

<pre><code class="language-typescript">const budgetManager = new BudgetManager();

<p>// Set team budget: $500/month</p>
<p>await budgetManager.setBudget({</p>
<p>id: 'budget-backend-monthly',</p>
<p>entity: { type: 'team', id: 'engineering-backend' },</p>
<p>period: 'monthly',</p>
<p>limit: 500,</p>
<p>alertThresholds: [0.5, 0.8, 0.9],  // Alert at 50%, 80%, 90%</p>
<p>enforced: true</p>
<p>});</p>

<p>// Check budget before API call</p>
<p>async function callWithBudgetCheck(prompt: string, teamId: string): Promise<string> {</p>
<p>const budget = await budgetManager.checkBudget('team', teamId);</p>

<p>if (!budget.allowed) {</p>
<p>throw new Error(`Budget exceeded for team ${teamId}. Spent: $${budget.spent.toFixed(2)}, Limit: $${budget.limit.toFixed(2)}`);</p>
<p>}</p>

<p>return await callClaude(prompt);</p>
<p>}</code></pre></p>

<hr>

<h2>Chargeback Models</h2>

<h3>Model 1: Direct Chargeback (Pay-per-use)</h3>

<pre><code class="language-typescript">interface ChargebackModel {
  type: 'direct' | 'allocated' | 'tiered';
  rates: {
    inputTokens: number;   // $/1M tokens
    outputTokens: number;  // $/1M tokens
  };
  markup?: number;  // e.g., 1.2 for 20% markup
}

<p>class DirectChargeback {</p>
<p>async calculateMonthlyChargeback(teamId: string, month: string): Promise<number> {</p>
<p>// Get all costs for team in month</p>
<p>const costs = await db.costs.find({</p>
<p>team: teamId,</p>
<p>timestamp: {</p>
<p>$gte: new Date(`${month}-01`).getTime(),</p>
<p>$lt: new Date(`${month}-01`).getTime() + 30 * 86400000</p>
<p>}</p>
<p>});</p>

<p>// Sum costs</p>
<p>const total = costs.reduce((sum, c) => sum + c.cost, 0);</p>

<p>// Apply markup (if infrastructure overhead)</p>
<p>const markup = 1.2;  // 20% overhead</p>
<p>return total * markup;</p>
<p>}</p>
<p>}</code></pre></p>

<h3>Model 2: Allocated Chargeback (Fixed budgets)</h3>

<pre><code class="language-typescript">class AllocatedChargeback {
  async allocateBudget(totalBudget: number, teams: string[]): Promise<Record<string, number>> {
    // Get usage share for each team
    const usageShares = await this.calculateUsageShares(teams);

<p>// Allocate budget proportionally</p>
<p>const allocations: Record<string, number> = {};</p>
<p>for (const team of teams) {</p>
<p>allocations[team] = totalBudget * usageShares[team];</p>
<p>}</p>

<p>return allocations;</p>
<p>}</p>

<p>private async calculateUsageShares(teams: string[]): Promise<Record<string, number>> {</p>
<p>const usage: Record<string, number> = {};</p>
<p>let total = 0;</p>

<p>for (const team of teams) {</p>
<p>const costs = await db.costs.find({ team });</p>
<p>const teamCost = costs.reduce((sum, c) => sum + c.cost, 0);</p>
<p>usage[team] = teamCost;</p>
<p>total += teamCost;</p>
<p>}</p>

<p>// Convert to shares (0-1)</p>
<p>const shares: Record<string, number> = {};</p>
<p>for (const team of teams) {</p>
<p>shares[team] = usage[team] / total;</p>
<p>}</p>

<p>return shares;</p>
<p>}</p>
<p>}</code></pre></p>

<h3>Model 3: Tiered Pricing (Volume discounts)</h3>

<pre><code class="language-typescript">interface PricingTier {
  minTokens: number;
  maxTokens: number;
  pricePerMillion: number;
}

<p>class TieredChargeback {</p>
<p>private tiers: PricingTier[] = [</p>
<p>{ minTokens: 0, maxTokens: 1_000_000, pricePerMillion: 15 },        // 0-1M: $15/M</p>
<p>{ minTokens: 1_000_000, maxTokens: 10_000_000, pricePerMillion: 12 }, // 1M-10M: $12/M</p>
<p>{ minTokens: 10_000_000, maxTokens: Infinity, pricePerMillion: 10 }   // 10M+: $10/M</p>
<p>];</p>

<p>calculateCost(tokens: number): number {</p>
<p>let cost = 0;</p>
<p>let remaining = tokens;</p>

<p>for (const tier of this.tiers) {</p>
<p>const tierSize = tier.maxTokens - tier.minTokens;</p>
<p>const tokensInTier = Math.min(remaining, tierSize);</p>

<p>if (tokensInTier > 0) {</p>
<p>cost += (tokensInTier / 1_000_000) * tier.pricePerMillion;</p>
<p>remaining -= tokensInTier;</p>
<p>}</p>

<p>if (remaining === 0) break;</p>
<p>}</p>

<p>return cost;</p>
<p>}</p>
<p>}</p>

<p>// Example</p>
<p>const tiered = new TieredChargeback();</p>
<p>console.log(tiered.calculateCost(15_000_000));</p>
<p>// 0-1M: $15</p>
<p>// 1M-10M: $108 (9M × $12)</p>
<p>// 10M-15M: $50 (5M × $10)</p>
<p>// Total: $173</code></pre></p>

<hr>

<h2>Usage Analytics</h2>

<h3>Cost Analytics Dashboard</h3>

<pre><code class="language-typescript">interface UsageMetrics {
  totalCost: number;
  totalTokens: number;
  avgCostPerRequest: number;
  topProjects: Array<{ project: string; cost: number }>;
  topUsers: Array<{ user: string; cost: number }>;
  costTrend: Array<{ date: string; cost: number }>;
}

<p>class UsageAnalytics {</p>
<p>async generateMonthlyReport(month: string): Promise<UsageMetrics> {</p>
<p>const costs = await db.costs.find({</p>
<p>timestamp: {</p>
<p>$gte: new Date(`${month}-01`).getTime(),</p>
<p>$lt: new Date(`${month}-01`).getTime() + 30 * 86400000</p>
<p>}</p>
<p>});</p>

<p>// Total cost</p>
<p>const totalCost = costs.reduce((sum, c) => sum + c.cost, 0);</p>
<p>const totalTokens = costs.reduce((sum, c) => sum + c.inputTokens + c.outputTokens, 0);</p>

<p>// Average cost per request</p>
<p>const avgCostPerRequest = totalCost / costs.length;</p>

<p>// Top projects by cost</p>
<p>const projectCosts = this.groupBy(costs, 'project');</p>
<p>const topProjects = Object.entries(projectCosts)</p>
<p>.map(([project, costs]) => ({</p>
<p>project,</p>
<p>cost: costs.reduce((sum: number, c: any) => sum + c.cost, 0)</p>
<p>}))</p>
<p>.sort((a, b) => b.cost - a.cost)</p>
<p>.slice(0, 10);</p>

<p>// Top users by cost</p>
<p>const userCosts = this.groupBy(costs, 'user');</p>
<p>const topUsers = Object.entries(userCosts)</p>
<p>.map(([user, costs]) => ({</p>
<p>user,</p>
<p>cost: costs.reduce((sum: number, c: any) => sum + c.cost, 0)</p>
<p>}))</p>
<p>.sort((a, b) => b.cost - a.cost)</p>
<p>.slice(0, 10);</p>

<p>// Daily cost trend</p>
<p>const dailyCosts = this.groupByDate(costs);</p>
<p>const costTrend = Object.entries(dailyCosts)</p>
<p>.map(([date, costs]) => ({</p>
<p>date,</p>
<p>cost: costs.reduce((sum: number, c: any) => sum + c.cost, 0)</p>
<p>}))</p>
<p>.sort((a, b) => a.date.localeCompare(b.date));</p>

<p>return {</p>
<p>totalCost,</p>
<p>totalTokens,</p>
<p>avgCostPerRequest,</p>
<p>topProjects,</p>
<p>topUsers,</p>
<p>costTrend</p>
<p>};</p>
<p>}</p>

<p>private groupBy(items: any[], key: string): Record<string, any[]> {</p>
<p>return items.reduce((acc, item) => {</p>
<p>const groupKey = item[key];</p>
<p>if (!acc[groupKey]) acc[groupKey] = [];</p>
<p>acc[groupKey].push(item);</p>
<p>return acc;</p>
<p>}, {});</p>
<p>}</p>

<p>private groupByDate(costs: any[]): Record<string, any[]> {</p>
<p>return costs.reduce((acc, cost) => {</p>
<p>const date = new Date(cost.timestamp).toISOString().split('T')[0];</p>
<p>if (!acc[date]) acc[date] = [];</p>
<p>acc[date].push(cost);</p>
<p>return acc;</p>
<p>}, {});</p>
<p>}</p>
<p>}</code></pre></p>

<hr>

<h2>Cost Optimization</h2>

<h3>Optimization Recommendations</h3>

<pre><code class="language-typescript">interface OptimizationRecommendation {
  category: 'model-selection' | 'caching' | 'batching' | 'workflow';
  description: string;
  potentialSavings: number;  // USD/month
  effort: 'low' | 'medium' | 'high';
  implementation: string;
}

<p>class CostOptimizer {</p>
<p>async analyzeAndRecommend(teamId: string): Promise<OptimizationRecommendation[]> {</p>
<p>const recommendations: OptimizationRecommendation[] = [];</p>

<p>// Analyze model usage</p>
<p>const modelRecommendation = await this.analyzeModelUsage(teamId);</p>
<p>if (modelRecommendation) recommendations.push(modelRecommendation);</p>

<p>// Analyze caching opportunities</p>
<p>const cacheRecommendation = await this.analyzeCachingOpportunities(teamId);</p>
<p>if (cacheRecommendation) recommendations.push(cacheRecommendation);</p>

<p>// Analyze batching opportunities</p>
<p>const batchRecommendation = await this.analyzeBatchingOpportunities(teamId);</p>
<p>if (batchRecommendation) recommendations.push(batchRecommendation);</p>

<p>return recommendations.sort((a, b) => b.potentialSavings - a.potentialSavings);</p>
<p>}</p>

<p>private async analyzeModelUsage(teamId: string): Promise<OptimizationRecommendation | null> {</p>
<p>// Check if using expensive model for simple tasks</p>
<p>const costs = await db.costs.find({ team: teamId });</p>

<p>const sonnetUsage = costs.filter(c => c.model.includes('sonnet'));</p>
<p>const simplePrompts = sonnetUsage.filter(c =></p>
<p>c.inputTokens < 1000 && c.outputTokens < 500</p>
<p>);</p>

<p>if (simplePrompts.length > sonnetUsage.length * 0.5) {</p>
<p>const currentCost = simplePrompts.reduce((sum, c) => sum + c.cost, 0);</p>
<p>const haikuCost = currentCost * (0.8 / 3.0);  // Haiku is cheaper</p>
<p>const monthlySavings = (currentCost - haikuCost) * 30;</p>

<p>return {</p>
<p>category: 'model-selection',</p>
<p>description: `${simplePrompts.length} simple prompts use Claude 3.5 Sonnet. Switch to Claude 3.5 Haiku for 73% cost reduction.`,</p>
<p>potentialSavings: monthlySavings,</p>
<p>effort: 'low',</p>
<p>implementation: 'Update model parameter in simple workflows to claude-3-5-haiku-20241022'</p>
<p>};</p>
<p>}</p>

<p>return null;</p>
<p>}</p>

<p>private async analyzeCachingOpportunities(teamId: string): Promise<OptimizationRecommendation | null> {</p>
<p>const costs = await db.costs.find({ team: teamId });</p>

<p>// Find duplicate prompts</p>
<p>const promptCounts = new Map<string, number>();</p>
<p>for (const cost of costs) {</p>
<p>const hash = this.hashPrompt(cost);</p>
<p>promptCounts.set(hash, (promptCounts.get(hash) || 0) + 1);</p>
<p>}</p>

<p>const duplicates = Array.from(promptCounts.entries()).filter(([_, count]) => count > 1);</p>
<p>const duplicateCost = duplicates.reduce((sum, [hash, count]) => {</p>
<p>const prompt = costs.find(c => this.hashPrompt(c) === hash);</p>
<p>return sum + (prompt?.cost || 0) * (count - 1);</p>
<p>}, 0);</p>

<p>if (duplicateCost > 10) {</p>
<p>return {</p>
<p>category: 'caching',</p>
<p>description: `${duplicates.length} prompts are duplicated. Implement caching to avoid redundant API calls.`,</p>
<p>potentialSavings: duplicateCost * 30,</p>
<p>effort: 'medium',</p>
<p>implementation: 'Add Redis cache for LLM responses with 1-hour TTL'</p>
<p>};</p>
<p>}</p>

<p>return null;</p>
<p>}</p>

<p>private async analyzeBatchingOpportunities(teamId: string): Promise<OptimizationRecommendation | null> {</p>
<p>// Find sequential requests that could be batched</p>
<p>const costs = await db.costs.find({ team: teamId }).sort({ timestamp: 1 });</p>

<p>let batchableCount = 0;</p>
<p>for (let i = 0; i < costs.length - 1; i++) {</p>
<p>const timeDiff = costs[i + 1].timestamp - costs[i].timestamp;</p>
<p>if (timeDiff < 1000) {  // Within 1 second</p>
<p>batchableCount++;</p>
<p>}</p>
<p>}</p>

<p>if (batchableCount > costs.length * 0.3) {</p>
<p>const savings = (batchableCount / costs.length) * costs.reduce((sum, c) => sum + c.cost, 0);</p>

<p>return {</p>
<p>category: 'batching',</p>
<p>description: `${batchableCount} requests could be batched. Combine multiple prompts into single API call.`,</p>
<p>potentialSavings: savings * 30 * 0.3,  // 30% reduction from batching</p>
<p>effort: 'high',</p>
<p>implementation: 'Implement request batching with 100ms window'</p>
<p>};</p>
<p>}</p>

<p>return null;</p>
<p>}</p>

<p>private hashPrompt(cost: any): string {</p>
<p>return `${cost.workflow}-${cost.inputTokens}-${cost.outputTokens}`;</p>
<p>}</p>
<p>}</code></pre></p>

<hr>

<h2>Reporting & Dashboards</h2>

<h3>Monthly Cost Report</h3>

<pre><code class="language-typescript">class CostReporter {
  async generateMonthlyReport(month: string): Promise<string> {
    const analytics = new UsageAnalytics();
    const metrics = await analytics.generateMonthlyReport(month);

<p>const report = <code></p>
<p># Cost Report - ${month}</p>

<p><h2>Summary</h2></p>
<ul>
<li><strong>Total Cost</strong>: $${metrics.totalCost.toFixed(2)}</li>
<li><strong>Total Tokens</strong>: ${metrics.totalTokens.toLocaleString()}</li>
<li><strong>Avg Cost/Request</strong>: $${metrics.avgCostPerRequest.toFixed(4)}</li>
</ul>

<p><h2>Top Projects by Cost</h2></p>
<p>${metrics.topProjects.map((p, i) => `${i + 1}. ${p.project}: $${p.cost.toFixed(2)}`).join('\n')}</p>

<p><h2>Top Users by Cost</h2></p>
<p>${metrics.topUsers.map((u, i) => `${i + 1}. ${u.user}: $${u.cost.toFixed(2)}`).join('\n')}</p>

<p><h2>Daily Cost Trend</h2></p>
<p>${metrics.costTrend.map(d => `${d.date}: $${d.cost.toFixed(2)}`).join('\n')}</p>

<p><h2>Optimization Recommendations</h2></p>
<p>${await this.getOptimizationRecommendations()}</p>

<hr>
<p>Generated: ${new Date().toISOString()}</p>
    </code>.trim();

<p>return report;</p>
<p>}</p>

<p>private async getOptimizationRecommendations(): Promise<string> {</p>
<p>const optimizer = new CostOptimizer();</p>
<p>const recommendations = await optimizer.analyzeAndRecommend('engineering-backend');</p>

<p>return recommendations</p>
<p>.map(r => `- <strong>${r.category}</strong>: ${r.description} (Savings: $${r.potentialSavings.toFixed(2)}/month, Effort: ${r.effort})`)</p>
<p>.join('\n');</p>
<p>}</p>
<p>}</code></pre></p>

<hr>

<h2>Best Practices</h2>

<h3>DO ✅</h3>

<ul>
<li><strong>Tag all costs</strong></li>
</ul>
   <pre><code class="language-typescript">await tagger.tagAPICall(request, { teamId, projectId, userId, workflow });</code></pre>

<ul>
<li><strong>Enforce budgets</strong></li>
</ul>
   <pre><code class="language-typescript">const budget = await budgetManager.checkBudget('team', teamId);
   if (!budget.allowed) throw new Error('Budget exceeded');</code></pre>

<ul>
<li><strong>Monitor trends</strong></li>
</ul>
   <pre><code class="language-typescript">const report = await analytics.generateMonthlyReport('2025-12');</code></pre>

<h3>DON'T ❌</h3>

<ul>
<li><strong>Don't skip cost tracking</strong></li>
</ul>
   <pre><code class="language-typescript">// ❌ No cost tracking
   await callClaude(prompt);

<p>// ✅ Track costs</p>
<p>await callClaudeWithTagging(prompt, context);</code></pre></p>

<ul>
<li><strong>Don't ignore optimization</strong></li>
</ul>
   <pre><code class="language-typescript">const recommendations = await optimizer.analyzeAndRecommend(teamId);
   // Implement high-value, low-effort optimizations</code></pre>

<hr>

<h2>Tools & Resources</h2>

<h3>Analytics Tools</h3>

<ul>
<li><strong>PostgreSQL</strong>: Cost data storage</li>
<li><strong>InfluxDB</strong>: Time-series metrics</li>
<li><strong>Grafana</strong>: Dashboards</li>
<li><strong>Metabase</strong>: BI reporting</li>
</ul>

<h3>Cost Management</h3>

<ul>
<li><strong>AWS Cost Explorer</strong>: Cloud infrastructure costs</li>
<li><strong>CloudHealth</strong>: Multi-cloud cost management</li>
<li><strong>Kubecost</strong>: Kubernetes cost allocation</li>
</ul>

<hr>

<h2>Summary</h2>

<p><strong>Key Takeaways</strong>:</p>

<ul>
<li><strong>Tag all costs</strong> - Team, project, user, workflow dimensions</li>
<li><strong>Enforce budgets</strong> - Hard limits with alerts at 50%/80%/90%</li>
<li><strong>Implement chargeback</strong> - Direct, allocated, or tiered models</li>
<li><strong>Analyze usage</strong> - Monthly reports with top consumers</li>
<li><strong>Optimize continuously</strong> - Model selection, caching, batching</li>
<li><strong>Report transparently</strong> - Share costs with stakeholders</li>
<li><strong>Monitor trends</strong> - Daily cost tracking</li>
</ul>

<p><strong>Cost Attribution Checklist</strong>:</p>
<ul>
<li>[ ] Implement cost tagging on all API calls</li>
<li>[ ] Set up PostgreSQL/InfluxDB for cost data</li>
<li>[ ] Define budgets for teams and projects</li>
<li>[ ] Configure budget alerts (50%, 80%, 90%)</li>
<li>[ ] Implement chargeback model</li>
<li>[ ] Generate monthly cost reports</li>
<li>[ ] Create Grafana dashboard for cost visualization</li>
<li>[ ] Run cost optimizer monthly</li>
<li>[ ] Implement top 3 optimization recommendations</li>
<li>[ ] Share cost reports with finance team</li>
</ul>

<hr>

<p><strong>Last Updated</strong>: 2025-12-24</p>
<p><strong>Author</strong>: Jeremy Longshore</p>
<p><strong>Related Playbooks</strong>: <a href="./02-cost-caps.md">Cost Caps & Budget Management</a>, <a href="./08-team-presets.md">Team Presets & Workflows</a></p>
