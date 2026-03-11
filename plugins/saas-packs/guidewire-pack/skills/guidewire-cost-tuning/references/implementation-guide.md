# Guidewire Cost Tuning - Implementation Guide

## Cost Components

| Component | Billing Model | Optimization Focus |
|-----------|---------------|-------------------|
| Licensing | Per user/policy | User management, policy counts |
| API Calls | Per call/volume | Request optimization, caching |
| Storage | Per GB | Data retention, archiving |
| Compute | Per instance-hour | Right-sizing, auto-scaling |
| Data Transfer | Per GB | Efficient payloads, compression |

## Instructions

### Step 1: Analyze Current Usage

```typescript
// Cost analysis utilities
interface UsageMetrics {
  period: string;
  apiCalls: number;
  activeUsers: number;
  storageGB: number;
  computeHours: number;
  dataTransferGB: number;
}

interface CostBreakdown {
  licensing: number;
  apiCalls: number;
  storage: number;
  compute: number;
  dataTransfer: number;
  total: number;
}

class CostAnalyzer {
  async getUsageReport(startDate: Date, endDate: Date): Promise<UsageMetrics> {
    const token = await this.getToken();

    const response = await fetch(
      `${this.gccUrl}/api/v1/usage?start=${startDate.toISOString()}&end=${endDate.toISOString()}`,
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );

    return response.json();
  }

  async getCostBreakdown(startDate: Date, endDate: Date): Promise<CostBreakdown> {
    const usage = await this.getUsageReport(startDate, endDate);

    return {
      licensing: this.calculateLicensingCost(usage),
      apiCalls: this.calculateApiCost(usage),
      storage: this.calculateStorageCost(usage),
      compute: this.calculateComputeCost(usage),
      dataTransfer: this.calculateTransferCost(usage),
      total: 0 // Sum calculated below
    };
  }

  identifyOptimizations(usage: UsageMetrics): Optimization[] {
    const optimizations: Optimization[] = [];

    // Check for inactive users
    if (usage.activeUsers < usage.totalLicensedUsers * 0.7) {
      optimizations.push({
        type: 'licensing',
        description: 'Reduce unused user licenses',
        potentialSavings: (usage.totalLicensedUsers - usage.activeUsers) * this.perUserCost,
        priority: 'high'
      });
    }

    // Check for high API volume
    if (usage.apiCalls > usage.expectedApiCalls * 1.5) {
      optimizations.push({
        type: 'api',
        description: 'Implement API response caching',
        potentialSavings: usage.apiCalls * 0.3 * this.perApiCallCost,
        priority: 'medium'
      });
    }

    // Check for storage growth
    if (usage.storageGrowthRate > 0.1) { // 10% monthly growth
      optimizations.push({
        type: 'storage',
        description: 'Implement data archiving policy',
        potentialSavings: usage.storageGB * 0.2 * this.perGBCost,
        priority: 'medium'
      });
    }

    return optimizations;
  }
}
```

### Step 2: License Optimization

```typescript
// User license management
interface UserActivity {
  userId: string;
  lastLogin: Date;
  loginCount30Days: number;
  role: string;
  department: string;
}

class LicenseOptimizer {
  async analyzeUserActivity(): Promise<UserActivityReport> {
    const users = await this.getUserActivity();

    const inactive30Days = users.filter(u =>
      daysSince(u.lastLogin) > 30 && u.loginCount30Days === 0
    );

    const inactive90Days = users.filter(u =>
      daysSince(u.lastLogin) > 90
    );

    const lowActivity = users.filter(u =>
      u.loginCount30Days < 5 && u.loginCount30Days > 0
    );

    return {
      totalUsers: users.length,
      inactive30Days: inactive30Days.length,
      inactive90Days: inactive90Days.length,
      lowActivity: lowActivity.length,
      recommendations: this.generateRecommendations(inactive30Days, inactive90Days, lowActivity)
    };
  }

  generateRecommendations(
    inactive30: UserActivity[],
    inactive90: UserActivity[],
    lowActivity: UserActivity[]
  ): Recommendation[] {
    const recommendations: Recommendation[] = [];

    // Deactivate 90-day inactive users
    if (inactive90.length > 0) {
      recommendations.push({
        action: 'DEACTIVATE_USERS',
        users: inactive90.map(u => u.userId),
        reason: 'No activity for 90+ days',
        estimatedSavings: inactive90.length * this.userLicenseCost
      });
    }

    // Review 30-day inactive users
    if (inactive30.length > 0) {
      recommendations.push({
        action: 'REVIEW_USERS',
        users: inactive30.map(u => u.userId),
        reason: 'No activity for 30+ days',
        estimatedSavings: inactive30.length * 0.5 * this.userLicenseCost
      });
    }

    // Consider read-only licenses for low activity
    if (lowActivity.length > 0) {
      recommendations.push({
        action: 'DOWNGRADE_LICENSE',
        users: lowActivity.map(u => u.userId),
        reason: 'Low activity - consider read-only license',
        estimatedSavings: lowActivity.length * 0.6 * this.userLicenseCost
      });
    }

    return recommendations;
  }
}
```

### Step 3: API Cost Optimization

```typescript
// API usage optimization
class ApiCostOptimizer {
  private callCounts: Map<string, number> = new Map();

  // Track API call patterns
  trackCall(endpoint: string, responseSize: number): void {
    const key = endpoint.replace(/\/[a-f0-9-]{36}/g, '/{id}'); // Normalize IDs
    this.callCounts.set(key, (this.callCounts.get(key) || 0) + 1);
  }

  // Identify optimization opportunities
  analyzePatterns(): ApiOptimization[] {
    const optimizations: ApiOptimization[] = [];

    // Find frequently called endpoints
    const topEndpoints = Array.from(this.callCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    topEndpoints.forEach(([endpoint, count]) => {
      // Suggest caching for read-heavy endpoints
      if (endpoint.includes('GET') && count > 1000) {
        optimizations.push({
          type: 'CACHE',
          endpoint,
          callCount: count,
          suggestion: 'Implement response caching',
          potentialReduction: 0.7
        });
      }

      // Suggest batching for related calls
      if (endpoint.includes('/accounts/') && count > 500) {
        optimizations.push({
          type: 'BATCH',
          endpoint,
          callCount: count,
          suggestion: 'Use includes parameter to reduce calls',
          potentialReduction: 0.5
        });
      }
    });

    return optimizations;
  }
}

// Implement efficient API patterns
class EfficientApiClient {
  private cache: LRUCache<string, any>;
  private batchQueue: Map<string, Promise<any>>;

  // Cache responses for repeated requests
  async getCached<T>(
    cacheKey: string,
    fetcher: () => Promise<T>,
    ttlMs: number = 60000
  ): Promise<T> {
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    const result = await fetcher();
    this.cache.set(cacheKey, result, { ttl: ttlMs });
    return result;
  }

  // Batch multiple requests into one
  async batchGetAccounts(accountIds: string[]): Promise<Account[]> {
    // Instead of N calls, use filter parameter
    const filter = accountIds.map(id => `id:eq:${id}`).join(',or,');
    return this.client.get(`/account/v1/accounts?filter=${filter}`);
  }

  // Use includes to reduce round trips
  async getAccountComplete(accountId: string): Promise<AccountComplete> {
    // Single call instead of 4
    return this.client.get(
      `/account/v1/accounts/${accountId}?include=policies,contacts,locations,activities`
    );
  }

  // Compress large payloads
  async postLargePayload(endpoint: string, data: any): Promise<any> {
    const compressed = await gzip(JSON.stringify(data));
    return this.client.post(endpoint, compressed, {
      headers: {
        'Content-Encoding': 'gzip',
        'Content-Type': 'application/json'
      }
    });
  }
}
```

### Step 4: Storage Cost Optimization

```gosu
// Data archiving and retention
package gw.cost.storage

uses gw.api.database.Query
uses gw.api.util.Logger
uses gw.transaction.Transaction

class StorageOptimizer {
  private static final var LOG = Logger.forCategory("StorageOptimizer")

  // Archive old claims
  static function archiveOldClaims(olderThanDays : int) {
    var cutoffDate = Date.Today.addDays(-olderThanDays)

    var claimsToArchive = Query.make(Claim)
      .compare(Claim#CloseDate, LessThan, cutoffDate)
      .compare(Claim#State, Equals, ClaimState.TC_CLOSED)
      .select()
      .toList()

    LOG.info("Found ${claimsToArchive.Count} claims to archive")

    claimsToArchive.batch(100).each(\batch -> {
      Transaction.runWithNewBundle(\bundle -> {
        batch.each(\claim -> {
          var c = bundle.add(claim)
          c.archiveToExternalStorage()  // Custom archive implementation
        })
      })
    })
  }

  // Purge old audit logs
  static function purgeAuditLogs(olderThanDays : int) {
    var cutoffDate = Date.Today.addDays(-olderThanDays)

    var deleted = Query.make(AuditLog)
      .compare(AuditLog#CreateTime, LessThan, cutoffDate)
      .delete()

    LOG.info("Purged ${deleted} audit log entries")
  }

  // Compress document attachments
  static function compressAttachments(claim : Claim) {
    claim.Documents.each(\doc -> {
      if (doc.Size > 1024 * 1024 && !doc.IsCompressed) {  // > 1MB
        Transaction.runWithNewBundle(\bundle -> {
          var d = bundle.add(doc)
          d.compress()
        })
      }
    })
  }

  // Generate storage report
  static function getStorageReport() : StorageReport {
    var report = new StorageReport()

    report.TotalDocumentsMB = calculateTotalDocumentSize()
    report.TotalAuditLogsMB = calculateAuditLogSize()
    report.TotalHistoryMB = calculateHistorySize()

    report.ArchivableClaims = Query.make(Claim)
      .compare(Claim#CloseDate, LessThan, Date.Today.addYears(-2))
      .select()
      .Count

    report.PurgeableAuditLogs = Query.make(AuditLog)
      .compare(AuditLog#CreateTime, LessThan, Date.Today.addDays(-90))
      .select()
      .Count

    return report
  }
}
```

### Step 5: Compute Resource Right-Sizing

```typescript
// Resource utilization analysis
interface ResourceMetrics {
  cpuUtilization: number[];  // Hourly samples
  memoryUtilization: number[];
  requestsPerSecond: number[];
  timestamp: Date[];
}

class ResourceOptimizer {
  async analyzeUtilization(days: number = 30): Promise<ResourceAnalysis> {
    const metrics = await this.getMetrics(days);

    const cpuP95 = percentile(metrics.cpuUtilization, 95);
    const memoryP95 = percentile(metrics.memoryUtilization, 95);
    const rpsP95 = percentile(metrics.requestsPerSecond, 95);

    const recommendations: ResourceRecommendation[] = [];

    // CPU under-utilized
    if (cpuP95 < 40) {
      recommendations.push({
        resource: 'CPU',
        currentUtilization: cpuP95,
        recommendation: 'Reduce CPU allocation',
        potentialSavings: this.calculateCpuSavings(cpuP95)
      });
    }

    // Memory over-provisioned
    if (memoryP95 < 50) {
      recommendations.push({
        resource: 'Memory',
        currentUtilization: memoryP95,
        recommendation: 'Reduce memory allocation',
        potentialSavings: this.calculateMemorySavings(memoryP95)
      });
    }

    // Auto-scaling opportunities
    const utilizationVariance = calculateVariance(metrics.cpuUtilization);
    if (utilizationVariance > 0.3) {
      recommendations.push({
        resource: 'Compute',
        recommendation: 'Enable auto-scaling',
        reason: 'High utilization variance detected',
        potentialSavings: this.calculateAutoScalingSavings(metrics)
      });
    }

    return {
      cpuP95,
      memoryP95,
      rpsP95,
      recommendations
    };
  }

  async implementAutoScaling(): Promise<void> {
    const config = {
      minInstances: 2,
      maxInstances: 10,
      targetCpuUtilization: 70,
      scaleUpCooldown: 300,
      scaleDownCooldown: 600
    };

    await this.configureAutoScaling(config);
  }
}
```

### Step 6: Cost Monitoring Dashboard

```typescript
// Cost monitoring and alerting
interface CostAlert {
  threshold: number;
  period: 'daily' | 'weekly' | 'monthly';
  metric: string;
  recipients: string[];
}

class CostMonitor {
  private alerts: CostAlert[] = [];

  addAlert(alert: CostAlert): void {
    this.alerts.push(alert);
  }

  async checkAlerts(): Promise<AlertNotification[]> {
    const notifications: AlertNotification[] = [];

    for (const alert of this.alerts) {
      const currentValue = await this.getCurrentValue(alert.metric, alert.period);

      if (currentValue > alert.threshold) {
        notifications.push({
          alert,
          currentValue,
          exceededBy: ((currentValue - alert.threshold) / alert.threshold) * 100,
          timestamp: new Date()
        });
      }
    }

    return notifications;
  }

  async generateReport(): Promise<CostReport> {
    const currentMonth = await this.getMonthToDateCosts();
    const previousMonth = await this.getPreviousMonthCosts();

    return {
      currentMonth,
      previousMonth,
      change: ((currentMonth.total - previousMonth.total) / previousMonth.total) * 100,
      breakdown: {
        licensing: currentMonth.licensing,
        api: currentMonth.apiCalls,
        storage: currentMonth.storage,
        compute: currentMonth.compute
      },
      recommendations: await this.generateRecommendations()
    };
  }
}

// Example cost alert setup
const costMonitor = new CostMonitor();

costMonitor.addAlert({
  threshold: 10000,
  period: 'daily',
  metric: 'api_calls',
  recipients: ['devops@company.com']
});

costMonitor.addAlert({
  threshold: 5000,
  period: 'monthly',
  metric: 'total_cost',
  recipients: ['finance@company.com', 'cto@company.com']
});
```

## Cost Optimization Checklist

| Category | Action | Potential Savings |
|----------|--------|-------------------|
| Licensing | Deactivate inactive users | 10-30% |
| Licensing | Review license tiers | 5-15% |
| API | Implement caching | 20-50% |
| API | Use batch operations | 10-30% |
| Storage | Archive old data | 15-40% |
| Storage | Compress attachments | 10-20% |
| Compute | Right-size instances | 20-40% |
| Compute | Enable auto-scaling | 15-30% |
