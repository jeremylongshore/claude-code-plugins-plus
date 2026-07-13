# Deepgram Cost Tuning - Implementation Details

## Cost-Optimized Transcription Service

```typescript
import { createClient } from '@deepgram/sdk';

interface CostConfig {
  maxMonthlySpend: number;
  warningThreshold: number;
  model: string;
  enabledFeatures: { diarization: boolean; smartFormat: boolean };
}

export class CostOptimizedTranscription {
  private client;
  private config: CostConfig;
  private metrics = { currentMonthMinutes: 0, currentMonthCost: 0, projectedMonthlyCost: 0 };
  private modelCosts: Record<string, number> = { 'nova-2': 0.0043, 'nova': 0.0043, 'base': 0.0048, 'enhanced': 0.0145 };

  constructor(apiKey: string, config: Partial<CostConfig> = {}) {
    this.client = createClient(apiKey);
    this.config = {
      maxMonthlySpend: config.maxMonthlySpend ?? 100,
      warningThreshold: config.warningThreshold ?? 80,
      model: config.model ?? 'nova-2',
      enabledFeatures: config.enabledFeatures ?? { diarization: false, smartFormat: true },
    };
  }

  private calculateCost(durationMinutes: number): number {
    let cost = durationMinutes * this.modelCosts[this.config.model];
    if (this.config.enabledFeatures.diarization) cost += durationMinutes * 0.0044;
    return cost;
  }

  private checkBudget(estimatedMinutes: number): void {
    const estimatedCost = this.calculateCost(estimatedMinutes);
    const projectedTotal = this.metrics.currentMonthCost + estimatedCost;
    if (projectedTotal > this.config.maxMonthlySpend) {
      throw new Error(`Budget exceeded. Current: $${this.metrics.currentMonthCost.toFixed(2)}, Limit: $${this.config.maxMonthlySpend}`);
    }
    const percentage = (projectedTotal / this.config.maxMonthlySpend) * 100;
    if (percentage >= this.config.warningThreshold) console.warn(`Budget warning: ${percentage.toFixed(1)}% used`);
  }

  async transcribe(audioUrl: string, estimatedDurationMinutes: number) {
    this.checkBudget(estimatedDurationMinutes);
    const { result, error } = await this.client.listen.prerecorded.transcribeUrl(
      { url: audioUrl },
      { model: this.config.model, smart_format: this.config.enabledFeatures.smartFormat, diarize: this.config.enabledFeatures.diarization }
    );
    if (error) throw error;
    const actualDuration = result.metadata.duration / 60;
    const cost = this.calculateCost(actualDuration);
    this.metrics.currentMonthMinutes += actualDuration;
    this.metrics.currentMonthCost += cost;
    return { transcript: result.results.channels[0].alternatives[0].transcript, metadata: { duration: actualDuration, cost, model: this.config.model } };
  }

  getMetrics() { return { ...this.metrics, budgetRemaining: this.config.maxMonthlySpend - this.metrics.currentMonthCost }; }
}
```

## Audio Duration Reducer

```typescript
import ffmpeg from 'fluent-ffmpeg';

export async function reduceDuration(inputPath: string, outputPath: string, options: { silenceThreshold?: string; silenceMinDuration?: number; speed?: number } = {}) {
  const { silenceThreshold = '-30dB', silenceMinDuration = 0.5, speed = 1.0 } = options;

  return new Promise((resolve, reject) => {
    let originalDuration = 0;
    ffmpeg(inputPath)
      .on('codecData', (data) => { originalDuration = parseDuration(data.duration); })
      .audioFilters([
        `silenceremove=start_periods=1:start_silence=${silenceMinDuration}:start_threshold=${silenceThreshold}`,
        `silenceremove=stop_periods=-1:stop_silence=${silenceMinDuration}:stop_threshold=${silenceThreshold}`,
        ...(speed !== 1.0 ? [`atempo=${speed}`] : []),
      ])
      .output(outputPath)
      .on('end', () => {
        ffmpeg.ffprobe(outputPath, (err, metadata) => {
          if (err) return reject(err);
          const reducedDuration = metadata.format.duration || 0;
          resolve({ originalDuration, reducedDuration, savings: ((originalDuration - reducedDuration) / originalDuration) * 100 });
        });
      })
      .on('error', reject)
      .run();
  });
}
```

## Usage Dashboard

```typescript
export class UsageDashboard {
  private client;
  private projectId: string;

  constructor(apiKey: string, projectId: string) {
    this.client = createClient(apiKey);
    this.projectId = projectId;
  }

  async getUsageSummary(daysBack = 30) {
    const end = new Date();
    const start = new Date(end.getTime() - daysBack * 24 * 60 * 60 * 1000);

    const { result, error } = await this.client.manage.getProjectUsageRequest(this.projectId, {
      start: start.toISOString(), end: end.toISOString(),
    });
    if (error) throw error;

    const byModel: Record<string, { minutes: number; cost: number }> = {};
    let totalMinutes = 0, totalCost = 0;

    for (const request of result.requests || []) {
      const minutes = (request.duration || 0) / 60;
      const model = request.model || 'unknown';
      const cost = minutes * ({ 'nova-2': 0.0043, 'nova': 0.0043, 'base': 0.0048, 'enhanced': 0.0145 }[model] || 0.0043);
      totalMinutes += minutes;
      totalCost += cost;
      if (!byModel[model]) byModel[model] = { minutes: 0, cost: 0 };
      byModel[model].minutes += minutes;
      byModel[model].cost += cost;
    }

    return { period: { start, end }, totalMinutes, totalCost, byModel,
      projections: { monthlyMinutes: (totalMinutes / daysBack) * 30, monthlyCost: (totalCost / daysBack) * 30 } };
  }
}
```

## Cost Alerts

```typescript
export class CostAlerts {
  private dashboard: UsageDashboard;
  private config: { dailyLimit: number; weeklyLimit: number; monthlyLimit: number; alertChannels: string[] };
  private alertsSent: Set<string> = new Set();

  constructor(dashboard: UsageDashboard, config: Partial<typeof this.config> = {}) {
    this.dashboard = dashboard;
    this.config = { dailyLimit: config.dailyLimit ?? 10, weeklyLimit: config.weeklyLimit ?? 50, monthlyLimit: config.monthlyLimit ?? 200, alertChannels: config.alertChannels ?? ['email'] };
  }

  async checkAndAlert(): Promise<void> {
    const daily = await this.dashboard.getUsageSummary(1);
    const weekly = await this.dashboard.getUsageSummary(7);
    const monthly = await this.dashboard.getUsageSummary(30);

    const alerts: string[] = [];
    if (daily.totalCost > this.config.dailyLimit) alerts.push(`Daily spend ($${daily.totalCost.toFixed(2)}) exceeds limit`);
    if (weekly.totalCost > this.config.weeklyLimit) alerts.push(`Weekly spend ($${weekly.totalCost.toFixed(2)}) exceeds limit`);
    if (monthly.totalCost > this.config.monthlyLimit) alerts.push(`Monthly spend ($${monthly.totalCost.toFixed(2)}) exceeds limit`);

    for (const alert of alerts) {
      const alertKey = `${new Date().toDateString()}-${alert}`;
      if (!this.alertsSent.has(alertKey)) { await this.sendAlert(alert); this.alertsSent.add(alertKey); }
    }
  }

  private async sendAlert(message: string): Promise<void> { console.log(`COST ALERT: ${message}`); }
}
```

## Model Selection for Cost

```typescript
export function recommendModel(params: {
  audioDurationMinutes: number; monthlyBudget: number; currentMonthSpend: number; qualityRequirement: 'high' | 'medium' | 'any';
}) {
  const budgetRemaining = params.monthlyBudget - params.currentMonthSpend;
  const models = [
    { name: 'nova-2', rate: 0.0043, quality: 'high' as const },
    { name: 'nova', rate: 0.0043, quality: 'high' as const },
    { name: 'base', rate: 0.0048, quality: 'low' as const },
  ];

  const eligible = models.filter(m => {
    if (params.qualityRequirement === 'high') return m.quality === 'high';
    return true;
  });

  for (const model of eligible.sort((a, b) => a.rate - b.rate)) {
    const cost = params.audioDurationMinutes * model.rate;
    if (cost <= budgetRemaining) return { model: model.name, estimatedCost: cost, qualityLevel: model.quality, reason: `Best value within budget ($${budgetRemaining.toFixed(2)} remaining)` };
  }

  const cheapest = eligible[0];
  return { model: cheapest.name, estimatedCost: params.audioDurationMinutes * cheapest.rate, qualityLevel: cheapest.quality, reason: 'Warning: May exceed budget' };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
