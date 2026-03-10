---
title: "Progressive Enhancement Patterns"
description: "Safe AI feature rollout strategies. Feature flags (0% → 100%), A/B testing, canary deployments, graceful degradation, and automated rollback on failures."
category: "Operations"
wordCount: 5500
readTime: 28
featured: false
order: 10
tags: ["feature-flags", "a-b-testing", "canary", "rollout", "degradation"]
prerequisites: []
relatedPlaybooks: ["02-cost-caps", "05-incident-debugging"]
---

<p><strong>Production Playbook for Product Engineers and SREs</strong></p>

<p>Rolling out AI features requires progressive enhancement strategies to minimize risk, gather feedback, and ensure graceful degradation. This playbook provides feature flag implementation, A/B testing frameworks, canary deployment patterns, and fallback strategies for Claude Code AI features.</p>

<h2>Progressive Enhancement Strategy</h2>

<h3>Rollout Phases</h3>

<pre><code class="language-mermaid">graph LR
    A[Development] --> B[Internal Alpha]
    B --> C[Canary 1%]
    C --> D[Gradual 5%]
    D --> E[Gradual 25%]
    E --> F[Gradual 50%]
    F --> G[Full 100%]

<p>G -.Rollback.-> F</p>
<p>F -.Rollback.-> E</p>
<p>E -.Rollback.-> D</p>
<p>D -.Rollback.-> C</code></pre></p>

<p><strong>Phase Durations</strong> (for SEV-2 or lower changes):</p>
<ul>
<li><strong>Internal Alpha</strong>: 1-2 days (employees only)</li>
<li><strong>Canary 1%</strong>: 1 day (monitor closely)</li>
<li><strong>Gradual 5%</strong>: 2 days</li>
<li><strong>Gradual 25%</strong>: 3 days</li>
<li><strong>Gradual 50%</strong>: 3 days</li>
<li><strong>Full 100%</strong>: Indefinite (or rollback)</li>
</ul>

<p><strong>Metrics to Monitor</strong>:</p>
<ul>
<li>Error rate (must be < 1%)</li>
<li>Latency p95 (< 3 seconds)</li>
<li>User satisfaction (survey or implicit signals)</li>
<li>Cost impact (< 10% increase)</li>
<li>Rollback rate (< 5% of users)</li>
</ul>

<hr>

<h2>Feature Flags</h2>

<h3>Feature Flag Implementation</h3>

<pre><code class="language-typescript">enum FeatureFlag {
  AI_CODE_REVIEW = 'ai_code_review',
  OLLAMA_MIGRATION = 'ollama_migration',
  ADVANCED_ANALYTICS = 'advanced_analytics',
  EXPERIMENTAL_AGENT = 'experimental_agent'
}

<p>interface FeatureFlagConfig {</p>
<p>enabled: boolean;</p>
<p>rolloutPercentage: number;  // 0-100</p>
<p>allowlist?: string[];       // User IDs</p>
<p>blocklist?: string[];       // User IDs</p>
<p>startDate?: number;</p>
<p>endDate?: number;</p>
<p>}</p>

<p>class FeatureFlagManager {</p>
<p>private flags: Map<FeatureFlag, FeatureFlagConfig> = new Map();</p>

<p>constructor() {</p>
<p>// Load from database or config file</p>
<p>this.loadFlags();</p>
<p>}</p>

<p>async isEnabled(flag: FeatureFlag, userId: string): Promise<boolean> {</p>
<p>const config = this.flags.get(flag);</p>
<p>if (!config) return false;</p>

<p>// Explicit blocklist</p>
<p>if (config.blocklist?.includes(userId)) {</p>
<p>return false;</p>
<p>}</p>

<p>// Explicit allowlist</p>
<p>if (config.allowlist?.includes(userId)) {</p>
<p>return true;</p>
<p>}</p>

<p>// Time-based gating</p>
<p>const now = Date.now();</p>
<p>if (config.startDate && now < config.startDate) return false;</p>
<p>if (config.endDate && now > config.endDate) return false;</p>

<p>// Percentage rollout (deterministic based on user ID)</p>
<p>if (!config.enabled) return false;</p>

<p>const hash = this.hashUserId(userId);</p>
<p>const userPercentile = (hash % 100) + 1;  // 1-100</p>

<p>return userPercentile <= config.rolloutPercentage;</p>
<p>}</p>

<p>async setFlag(flag: FeatureFlag, config: FeatureFlagConfig): Promise<void> {</p>
<p>this.flags.set(flag, config);</p>
<p>await this.saveFlags();</p>
<p>}</p>

<p>async incrementRollout(flag: FeatureFlag, step: number = 5): Promise<void> {</p>
<p>const config = this.flags.get(flag);</p>
<p>if (!config) throw new Error(<code>Flag not found: ${flag}</code>);</p>

<p>config.rolloutPercentage = Math.min(100, config.rolloutPercentage + step);</p>
<p>await this.setFlag(flag, config);</p>

<p>console.log(<code>🚀 Increased ${flag} rollout to ${config.rolloutPercentage}%</code>);</p>
<p>}</p>

<p>private hashUserId(userId: string): number {</p>
<p>let hash = 0;</p>
<p>for (let i = 0; i < userId.length; i++) {</p>
<p>hash = ((hash << 5) - hash) + userId.charCodeAt(i);</p>
<p>hash = hash & hash;  // Convert to 32-bit integer</p>
<p>}</p>
<p>return Math.abs(hash);</p>
<p>}</p>

<p>private async loadFlags(): Promise<void> {</p>
<p>// Load from database or config file</p>
<p>const configs = await db.featureFlags.find();</p>
<p>for (const config of configs) {</p>
<p>this.flags.set(config.flag, config.config);</p>
<p>}</p>
<p>}</p>

<p>private async saveFlags(): Promise<void> {</p>
<p>for (const [flag, config] of this.flags) {</p>
<p>await db.featureFlags.upsert({ flag, config });</p>
<p>}</p>
<p>}</p>
<p>}</code></pre></p>

<h3>Usage Example</h3>

<pre><code class="language-typescript">const flags = new FeatureFlagManager();

<p>// Enable AI code review for 10% of users</p>
<p>await flags.setFlag(FeatureFlag.AI_CODE_REVIEW, {</p>
<p>enabled: true,</p>
<p>rolloutPercentage: 10</p>
<p>});</p>

<p>// Check flag before using feature</p>
<p>async function reviewCode(userId: string, code: string): Promise<string> {</p>
<p>const useAI = await flags.isEnabled(FeatureFlag.AI_CODE_REVIEW, userId);</p>

<p>if (useAI) {</p>
<p>// New AI-powered review</p>
<p>return await aiCodeReview(code);</p>
<p>} else {</p>
<p>// Traditional linter-based review</p>
<p>return await linterReview(code);</p>
<p>}</p>
<p>}</p>

<p>// Gradual rollout (automated)</p>
<p>setInterval(async () => {</p>
<p>await flags.incrementRollout(FeatureFlag.AI_CODE_REVIEW, 5);  // +5% every hour</p>
<p>}, 3600000);</code></pre></p>

<hr>

<h2>A/B Testing</h2>

<h3>A/B Test Framework</h3>

<pre><code class="language-typescript">enum Variant {
  CONTROL = 'control',
  TREATMENT = 'treatment'
}

<p>interface ABTest {</p>
<p>name: string;</p>
<p>startDate: number;</p>
<p>endDate: number;</p>
<p>controlPercentage: number;  // e.g., 50</p>
<p>treatmentPercentage: number; // e.g., 50</p>
<p>metrics: string[];  // ['conversion_rate', 'latency', 'satisfaction']</p>
<p>}</p>

<p>class ABTestManager {</p>
<p>private tests: Map<string, ABTest> = new Map();</p>

<p>async assignVariant(testName: string, userId: string): Promise<Variant> {</p>
<p>const test = this.tests.get(testName);</p>
<p>if (!test) throw new Error(<code>Test not found: ${testName}</code>);</p>

<p>// Check if test is active</p>
<p>const now = Date.now();</p>
<p>if (now < test.startDate || now > test.endDate) {</p>
<p>return Variant.CONTROL;</p>
<p>}</p>

<p>// Deterministic assignment based on user ID</p>
<p>const hash = this.hashUserId(userId);</p>
<p>const percentile = (hash % 100) + 1;</p>

<p>if (percentile <= test.controlPercentage) {</p>
<p>return Variant.CONTROL;</p>
<p>} else if (percentile <= test.controlPercentage + test.treatmentPercentage) {</p>
<p>return Variant.TREATMENT;</p>
<p>} else {</p>
<p>return Variant.CONTROL;</p>
<p>}</p>
<p>}</p>

<p>async recordMetric(testName: string, userId: string, metric: string, value: number): Promise<void> {</p>
<p>const variant = await this.assignVariant(testName, userId);</p>

<p>await db.abTestMetrics.insert({</p>
<p>test: testName,</p>
<p>variant,</p>
<p>userId,</p>
<p>metric,</p>
<p>value,</p>
<p>timestamp: Date.now()</p>
<p>});</p>
<p>}</p>

<p>async analyzeResults(testName: string): Promise<{</p>
<p>control: Record<string, number>;</p>
<p>treatment: Record<string, number>;</p>
<p>significant: boolean;</p>
<p>}> {</p>
<p>const metrics = await db.abTestMetrics.find({ test: testName });</p>

<p>const controlMetrics = metrics.filter(m => m.variant === Variant.CONTROL);</p>
<p>const treatmentMetrics = metrics.filter(m => m.variant === Variant.TREATMENT);</p>

<p>const controlAvg = this.calculateAverages(controlMetrics);</p>
<p>const treatmentAvg = this.calculateAverages(treatmentMetrics);</p>

<p>// Simplified statistical significance (use proper t-test in production)</p>
<p>const significant = this.checkSignificance(controlMetrics, treatmentMetrics);</p>

<p>return {</p>
<p>control: controlAvg,</p>
<p>treatment: treatmentAvg,</p>
<p>significant</p>
<p>};</p>
<p>}</p>

<p>private calculateAverages(metrics: any[]): Record<string, number> {</p>
<p>const grouped = this.groupBy(metrics, 'metric');</p>
<p>const averages: Record<string, number> = {};</p>

<p>for (const [metric, values] of Object.entries(grouped)) {</p>
<p>const sum = values.reduce((acc: number, v: any) => acc + v.value, 0);</p>
<p>averages[metric] = sum / values.length;</p>
<p>}</p>

<p>return averages;</p>
<p>}</p>

<p>private groupBy(items: any[], key: string): Record<string, any[]> {</p>
<p>return items.reduce((acc, item) => {</p>
<p>const groupKey = item[key];</p>
<p>if (!acc[groupKey]) acc[groupKey] = [];</p>
<p>acc[groupKey].push(item);</p>
<p>return acc;</p>
<p>}, {});</p>
<p>}</p>

<p>private checkSignificance(control: any[], treatment: any[]): boolean {</p>
<p>// Simplified: Check if sample sizes are sufficient</p>
<p>return control.length >= 100 && treatment.length >= 100;</p>
<p>}</p>

<p>private hashUserId(userId: string): number {</p>
<p>let hash = 0;</p>
<p>for (let i = 0; i < userId.length; i++) {</p>
<p>hash = ((hash << 5) - hash) + userId.charCodeAt(i);</p>
<p>hash = hash & hash;</p>
<p>}</p>
<p>return Math.abs(hash);</p>
<p>}</p>
<p>}</code></pre></p>

<h3>A/B Test Example</h3>

<pre><code class="language-typescript">const abTest = new ABTestManager();

<p>// Create A/B test: Claude Sonnet vs Ollama Llama</p>
<p>await abTest.createTest({</p>
<p>name: 'ollama-vs-claude',</p>
<p>startDate: Date.now(),</p>
<p>endDate: Date.now() + 7 * 86400000,  // 7 days</p>
<p>controlPercentage: 50,    // Claude (control)</p>
<p>treatmentPercentage: 50,  // Ollama (treatment)</p>
<p>metrics: ['latency', 'quality', 'cost']</p>
<p>});</p>

<p>// Assign variant and execute</p>
<p>async function generateCode(userId: string, prompt: string): Promise<string> {</p>
<p>const variant = await abTest.assignVariant('ollama-vs-claude', userId);</p>

<p>const start = Date.now();</p>
<p>let result: string;</p>
<p>let cost: number;</p>

<p>if (variant === Variant.CONTROL) {</p>
<p>// Control: Claude 3.5 Sonnet</p>
<p>result = await callClaude(prompt);</p>
<p>cost = 0.015;  // $0.015 per request (example)</p>
<p>} else {</p>
<p>// Treatment: Ollama Llama 3.3 70B</p>
<p>result = await callOllama(prompt, 'llama3.3:70b');</p>
<p>cost = 0;  // Free</p>
<p>}</p>

<p>const latency = Date.now() - start;</p>

<p>// Record metrics</p>
<p>await abTest.recordMetric('ollama-vs-claude', userId, 'latency', latency);</p>
<p>await abTest.recordMetric('ollama-vs-claude', userId, 'cost', cost);</p>

<p>return result;</p>
<p>}</p>

<p>// Analyze after 7 days</p>
<p>const results = await abTest.analyzeResults('ollama-vs-claude');</p>
<p>console.log('Control (Claude):', results.control);</p>
<p>// { latency: 4500, cost: 0.015, quality: 9.2 }</p>

<p>console.log('Treatment (Ollama):', results.treatment);</p>
<p>// { latency: 3800, cost: 0, quality: 8.5 }</p>

<p>console.log('Statistically significant?', results.significant);</p>
<p>// true (if sample size sufficient)</code></pre></p>

<hr>

<h2>Canary Deployments</h2>

<h3>Canary Deployment Strategy</h3>

<pre><code class="language-typescript">interface CanaryConfig {
  percentage: number;
  duration: number;  // milliseconds
  autoPromote: boolean;
  thresholds: {
    errorRate: number;    // e.g., 0.01 (1%)
    latencyP95: number;   // e.g., 3000 (3 seconds)
  };
}

<p>class CanaryDeployment {</p>
<p>async deploy(newVersion: string, config: CanaryConfig): Promise<boolean> {</p>
<p>console.log(<code>🐤 Starting canary deployment: ${newVersion} (${config.percentage}%)</code>);</p>

<p>// Route traffic</p>
<p>await this.routeTraffic(newVersion, config.percentage);</p>

<p>// Monitor for duration</p>
<p>await sleep(config.duration);</p>

<p>// Check metrics</p>
<p>const metrics = await this.collectMetrics(newVersion, config.duration);</p>

<p>const healthy = this.evaluateHealth(metrics, config.thresholds);</p>

<p>if (healthy) {</p>
<p>console.log(<code>✅ Canary healthy. Promoting ${newVersion}</code>);</p>
<p>if (config.autoPromote) {</p>
<p>await this.promote(newVersion);</p>
<p>}</p>
<p>return true;</p>
<p>} else {</p>
<p>console.error(<code>❌ Canary failed. Rolling back ${newVersion}</code>);</p>
<p>await this.rollback(newVersion);</p>
<p>return false;</p>
<p>}</p>
<p>}</p>

<p>private async routeTraffic(version: string, percentage: number): Promise<void> {</p>
<p>// Update load balancer routing rules</p>
<p>await updateLoadBalancer({</p>
<p>versions: [</p>
<p>{ version: 'stable', weight: 100 - percentage },</p>
<p>{ version, weight: percentage }</p>
<p>]</p>
<p>});</p>
<p>}</p>

<p>private async collectMetrics(version: string, duration: number): Promise<any> {</p>
<p>// Query Prometheus for metrics</p>
<p>const errorRate = await prometheus.query(</p>
<p><code>rate(http_requests_errors{version="${version}"}[${duration / 1000}s])</code></p>
<p>);</p>

<p>const latencyP95 = await prometheus.query(</p>
<p><code>histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{version="${version}"}[${duration / 1000}s]))</code></p>
<p>);</p>

<p>return { errorRate, latencyP95 };</p>
<p>}</p>

<p>private evaluateHealth(metrics: any, thresholds: any): boolean {</p>
<p>if (metrics.errorRate > thresholds.errorRate) {</p>
<p>console.warn(<code>Error rate too high: ${metrics.errorRate} > ${thresholds.errorRate}</code>);</p>
<p>return false;</p>
<p>}</p>

<p>if (metrics.latencyP95 > thresholds.latencyP95) {</p>
<p>console.warn(<code>Latency too high: ${metrics.latencyP95}ms > ${thresholds.latencyP95}ms</code>);</p>
<p>return false;</p>
<p>}</p>

<p>return true;</p>
<p>}</p>

<p>private async promote(version: string): Promise<void> {</p>
<p>// Gradually increase traffic to 100%</p>
<p>await this.routeTraffic(version, 100);</p>
<p>console.log(<code>🚀 Promoted ${version} to 100%</code>);</p>
<p>}</p>

<p>private async rollback(version: string): Promise<void> {</p>
<p>// Route all traffic back to stable</p>
<p>await this.routeTraffic('stable', 100);</p>
<p>console.log(<code>⏪ Rolled back ${version}</code>);</p>
<p>}</p>
<p>}</p>

<p>// Usage</p>
<p>const canary = new CanaryDeployment();</p>
<p>await canary.deploy('v2.5.0', {</p>
<p>percentage: 5,           // 5% of traffic</p>
<p>duration: 600000,        // 10 minutes</p>
<p>autoPromote: false,      // Manual promotion</p>
<p>thresholds: {</p>
<p>errorRate: 0.01,       // Max 1% errors</p>
<p>latencyP95: 3000       // Max 3s p95 latency</p>
<p>}</p>
<p>});</code></pre></p>

<hr>

<h2>Graceful Degradation</h2>

<h3>Fallback Strategies</h3>

<pre><code class="language-typescript">enum FallbackStrategy {
  SIMPLER_MODEL = 'simpler_model',
  CACHED_RESPONSE = 'cached_response',
  TRADITIONAL_METHOD = 'traditional_method',
  REDUCED_FUNCTIONALITY = 'reduced_functionality'
}

<p>class GracefulDegradation {</p>
<p>async executeWithFallback<T>(</p>
<p>primary: () => Promise<T>,</p>
<p>fallback: () => Promise<T>,</p>
<p>strategy: FallbackStrategy</p>
<p>): Promise<{ result: T; usedFallback: boolean }> {</p>
<p>try {</p>
<p>const result = await primary();</p>
<p>return { result, usedFallback: false };</p>
<p>} catch (error) {</p>
<p>console.warn(<code>Primary method failed: ${error.message}</code>);</p>
<p>console.log(<code>Using fallback strategy: ${strategy}</code>);</p>

<p>const result = await fallback();</p>
<p>return { result, usedFallback: true };</p>
<p>}</p>
<p>}</p>
<p>}</p>

<p>// Strategy 1: Simpler Model</p>
<p>async function codeReviewWithFallback(code: string): Promise<string> {</p>
<p>const degradation = new GracefulDegradation();</p>

<p>return (await degradation.executeWithFallback(</p>
<p>// Primary: Claude 3.5 Sonnet (high quality)</p>
<p>async () => {</p>
<p>return await callClaude(code, 'claude-3-5-sonnet-20241022');</p>
<p>},</p>
<p>// Fallback: Claude 3.5 Haiku (faster, cheaper)</p>
<p>async () => {</p>
<p>return await callClaude(code, 'claude-3-5-haiku-20241022');</p>
<p>},</p>
<p>FallbackStrategy.SIMPLER_MODEL</p>
<p>)).result;</p>
<p>}</p>

<p>// Strategy 2: Cached Response</p>
<p>async function summarizeWithCache(text: string): Promise<string> {</p>
<p>const cache = new Map<string, string>();</p>
<p>const degradation = new GracefulDegradation();</p>

<p>return (await degradation.executeWithFallback(</p>
<p>// Primary: Fresh AI summary</p>
<p>async () => {</p>
<p>const summary = await callClaude(text, 'claude-3-5-haiku-20241022');</p>
<p>cache.set(text, summary);</p>
<p>return summary;</p>
<p>},</p>
<p>// Fallback: Cached summary</p>
<p>async () => {</p>
<p>const cached = cache.get(text);</p>
<p>if (!cached) throw new Error('No cache available');</p>
<p>return cached + '\n\n(Cached response)';</p>
<p>},</p>
<p>FallbackStrategy.CACHED_RESPONSE</p>
<p>)).result;</p>
<p>}</p>

<p>// Strategy 3: Traditional Method</p>
<p>async function formatCodeWithFallback(code: string): Promise<string> {</p>
<p>const degradation = new GracefulDegradation();</p>

<p>return (await degradation.executeWithFallback(</p>
<p>// Primary: AI-powered formatting with context awareness</p>
<p>async () => {</p>
<p>return await callClaude(<code>Format this code:\n${code}</code>, 'claude-3-5-haiku-20241022');</p>
<p>},</p>
<p>// Fallback: Traditional Prettier</p>
<p>async () => {</p>
<p>return prettier.format(code, { parser: 'typescript' });</p>
<p>},</p>
<p>FallbackStrategy.TRADITIONAL_METHOD</p>
<p>)).result;</p>
<p>}</code></pre></p>

<hr>

<h2>Rollback Strategies</h2>

<h3>Automated Rollback</h3>

<pre><code class="language-typescript">class AutomatedRollback {
  private readonly errorRateThreshold = 0.05;  // 5%
  private readonly checkInterval = 60000;      // 1 minute

<p>async monitorAndRollback(version: string): Promise<void> {</p>
<p>const startTime = Date.now();</p>

<p>const monitor = setInterval(async () => {</p>
<p>const metrics = await this.collectMetrics(version, this.checkInterval);</p>

<p>// Check error rate</p>
<p>if (metrics.errorRate > this.errorRateThreshold) {</p>
<p>console.error(<code>🚨 Error rate ${metrics.errorRate} > threshold ${this.errorRateThreshold}</code>);</p>
<p>console.error(<code>⏪ Auto-rolling back ${version}</code>);</p>

<p>clearInterval(monitor);</p>
<p>await this.rollback(version);</p>
<p>await this.alertTeam(<code>Auto-rollback triggered for ${version}: error rate ${metrics.errorRate}</code>);</p>
<p>}</p>

<p>// Stop monitoring after 1 hour if healthy</p>
<p>if (Date.now() - startTime > 3600000) {</p>
<p>console.log(<code>✅ ${version} stable after 1 hour. Stopping auto-rollback monitor.</code>);</p>
<p>clearInterval(monitor);</p>
<p>}</p>
<p>}, this.checkInterval);</p>
<p>}</p>

<p>private async collectMetrics(version: string, window: number): Promise<any> {</p>
<p>const errorRate = await prometheus.query(</p>
<p><code>rate(http_requests_errors{version="${version}"}[${window / 1000}s])</code></p>
<p>);</p>

<p>return { errorRate };</p>
<p>}</p>

<p>private async rollback(version: string): Promise<void> {</p>
<p>// Route traffic back to stable</p>
<p>await updateLoadBalancer({</p>
<p>versions: [{ version: 'stable', weight: 100 }]</p>
<p>});</p>
<p>}</p>

<p>private async alertTeam(message: string): Promise<void> {</p>
<p>// Send to PagerDuty, Slack, etc.</p>
<p>console.log(<code>ALERT: ${message}</code>);</p>
<p>}</p>
<p>}</code></pre></p>

<hr>

<h2>Monitoring & Metrics</h2>

<h3>Rollout Metrics Dashboard</h3>

<pre><code class="language-typescript">interface RolloutMetrics {
  version: string;
  percentage: number;
  errorRate: number;
  latencyP50: number;
  latencyP95: number;
  latencyP99: number;
  requestCount: number;
  userSatisfaction: number;  // 0-5 star rating
}

<p>class RolloutMonitor {</p>
<p>async getMetrics(version: string): Promise<RolloutMetrics> {</p>
<p>const errorRate = await prometheus.query(</p>
<p><code>rate(http_requests_errors{version="${version}"}[5m])</code></p>
<p>);</p>

<p>const latencyP50 = await prometheus.query(</p>
<p><code>histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{version="${version}"}[5m]))</code></p>
<p>);</p>

<p>const latencyP95 = await prometheus.query(</p>
<p><code>histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{version="${version}"}[5m]))</code></p>
<p>);</p>

<p>const latencyP99 = await prometheus.query(</p>
<p><code>histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{version="${version}"}[5m]))</code></p>
<p>);</p>

<p>const requestCount = await prometheus.query(</p>
<p><code>sum(rate(http_requests_total{version="${version}"}[5m]))</code></p>
<p>);</p>

<p>const userSatisfaction = await this.calculateSatisfaction(version);</p>

<p>return {</p>
<p>version,</p>
<p>percentage: await this.getCurrentRolloutPercentage(version),</p>
<p>errorRate,</p>
<p>latencyP50,</p>
<p>latencyP95,</p>
<p>latencyP99,</p>
<p>requestCount,</p>
<p>userSatisfaction</p>
<p>};</p>
<p>}</p>

<p>private async calculateSatisfaction(version: string): Promise<number> {</p>
<p>// Calculate from user feedback</p>
<p>const ratings = await db.userRatings.find({ version });</p>
<p>const avg = ratings.reduce((sum, r) => sum + r.rating, 0) / ratings.length;</p>
<p>return avg || 0;</p>
<p>}</p>

<p>private async getCurrentRolloutPercentage(version: string): Promise<number> {</p>
<p>// Get from load balancer config</p>
<p>return 50;  // Example</p>
<p>}</p>
<p>}</code></pre></p>

<hr>

<h2>Best Practices</h2>

<h3>DO ✅</h3>

<ul>
<li><strong>Use feature flags</strong></li>
</ul>
   <pre><code class="language-typescript">const enabled = await flags.isEnabled(FeatureFlag.AI_CODE_REVIEW, userId);
   if (enabled) { /* new feature */ } else { /* old feature */ }</code></pre>

<ul>
<li><strong>Test with real users</strong></li>
</ul>
   <pre><code class="language-typescript">const variant = await abTest.assignVariant('experiment', userId);
   // Run both variants, measure results</code></pre>

<ul>
<li><strong>Monitor metrics</strong></li>
</ul>
   <pre><code class="language-typescript">const metrics = await monitor.getMetrics('v2.0');
   if (metrics.errorRate > 0.01) await rollback();</code></pre>

<ul>
<li><strong>Gradual rollouts</strong></li>
</ul>
   <pre><code class="language-typescript">// Day 1: 1%, Day 2: 5%, Day 3: 25%, Day 4: 100%
   await incrementRollout(5);</code></pre>

<h3>DON'T ❌</h3>

<ul>
<li><strong>Don't skip canary phase</strong></li>
</ul>
   <pre><code class="language-typescript">// ❌ Deploy directly to 100%
   await deploy('v2.0', { percentage: 100 });

<p>// ✅ Start with canary</p>
<p>await deploy('v2.0', { percentage: 1 });</code></pre></p>

<ul>
<li><strong>Don't ignore metrics</strong></li>
</ul>
   <pre><code class="language-typescript">// ❌ No monitoring
   await deploy('v2.0');

<p>// ✅ Monitor and auto-rollback</p>
<p>await monitorAndRollback('v2.0');</code></pre></p>

<ul>
<li><strong>Don't forget fallbacks</strong></li>
</ul>
   <pre><code class="language-typescript">// ❌ No fallback
   const result = await newAIFeature();

<p>// ✅ Always have fallback</p>
<p>const result = await executeWithFallback(newAIFeature, traditionalMethod);</code></pre></p>

<hr>

<h2>Tools & Resources</h2>

<h3>Feature Flag Platforms</h3>

<ul>
<li><strong>LaunchDarkly</strong>: Enterprise feature flags</li>
<li><strong>Split.io</strong>: Feature flags + experimentation</li>
<li><strong>Unleash</strong>: Open-source feature toggles</li>
</ul>

<h3>A/B Testing Tools</h3>

<ul>
<li><strong>Optimizely</strong>: A/B testing platform</li>
<li><strong>VWO</strong>: Visual testing</li>
<li><strong>Google Optimize</strong>: Free A/B testing</li>
</ul>

<h3>Deployment Tools</h3>

<ul>
<li><strong>Spinnaker</strong>: Multi-cloud continuous delivery</li>
<li><strong>Flagger</strong>: Progressive delivery for Kubernetes</li>
<li><strong>Argo Rollouts</strong>: Canary deployments on K8s</li>
</ul>

<hr>

<h2>Summary</h2>

<p><strong>Key Takeaways</strong>:</p>

<ul>
<li><strong>Feature flags enable safe rollouts</strong> - Gradual percentage-based rollouts</li>
<li><strong>A/B testing validates changes</strong> - Compare control vs treatment</li>
<li><strong>Canary deployments minimize risk</strong> - 1% → 5% → 25% → 100%</li>
<li><strong>Graceful degradation prevents outages</strong> - Fallback to simpler models</li>
<li><strong>Automated rollbacks protect users</strong> - Monitor error rates, auto-rollback</li>
<li><strong>Metrics guide decisions</strong> - Error rate, latency, satisfaction</li>
<li><strong>Progressive enhancement is continuous</strong> - Always improving safely</li>
</ul>

<p><strong>Rollout Checklist</strong>:</p>
<ul>
<li>[ ] Implement feature flags for new AI features</li>
<li>[ ] Define rollout phases (1% → 5% → 25% → 50% → 100%)</li>
<li>[ ] Set up A/B testing framework</li>
<li>[ ] Configure canary deployment thresholds</li>
<li>[ ] Implement graceful degradation fallbacks</li>
<li>[ ] Enable automated rollback monitoring</li>
<li>[ ] Create rollout metrics dashboard</li>
<li>[ ] Document rollback procedures</li>
<li>[ ] Train team on progressive enhancement</li>
<li>[ ] Schedule quarterly rollout reviews</li>
</ul>

<hr>

<p><strong>Last Updated</strong>: 2025-12-24</p>
<p><strong>Author</strong>: Jeremy Longshore</p>
<p><strong>Related Playbooks</strong>: <a href="./02-cost-caps.md">Cost Caps & Budget Management</a>, <a href="./05-incident-debugging.md">Incident Debugging Playbook</a></p>
