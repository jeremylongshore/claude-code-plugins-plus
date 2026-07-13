# MaintainX Upgrade & Migration - Implementation Guide

> Full implementation details and code examples for the `maintainx-upgrade-migration` skill.

# MaintainX Upgrade & Migration

## Overview

Guide for handling MaintainX API version upgrades, deprecations, and breaking changes in your integrations.

## Prerequisites

- Existing MaintainX integration
- Understanding of current API usage
- Test environment available

## Migration Planning

### Step 1: Assess Current Usage

```typescript
// scripts/analyze-api-usage.ts

interface ApiUsageReport {
  endpoints: Map<string, number>;
  methods: Map<string, number>;
  fields: Map<string, Set<string>>;
  deprecations: string[];
}

async function analyzeApiUsage(logFile: string): Promise<ApiUsageReport> {
  const fs = require('fs');
  const logs = JSON.parse(fs.readFileSync(logFile, 'utf8'));

  const report: ApiUsageReport = {
    endpoints: new Map(),
    methods: new Map(),
    fields: new Map(),
    deprecations: [],
  };

  logs.forEach((log: any) => {
    // Count endpoint usage
    const endpoint = log.url?.replace(/\/[a-z0-9_-]+$/i, '/:id');
    if (endpoint) {
      report.endpoints.set(endpoint, (report.endpoints.get(endpoint) || 0) + 1);
    }

    // Count HTTP methods
    if (log.method) {
      report.methods.set(log.method, (report.methods.get(log.method) || 0) + 1);
    }

    // Track fields used in requests
    if (log.requestBody) {
      const fields = Object.keys(log.requestBody);
      const endpointFields = report.fields.get(endpoint) || new Set();
      fields.forEach(f => endpointFields.add(f));
      report.fields.set(endpoint, endpointFields);
    }

    // Check for deprecation warnings
    if (log.responseHeaders?.['x-deprecation-warning']) {
      report.deprecations.push(log.responseHeaders['x-deprecation-warning']);
    }
  });

  return report;
}

// Print report
async function printUsageReport() {
  const report = await analyzeApiUsage('./logs/api-requests.json');

  console.log('=== MaintainX API Usage Analysis ===\n');

  console.log('Endpoints Used:');
  report.endpoints.forEach((count, endpoint) => {
    console.log(`  ${endpoint}: ${count} calls`);
  });

  console.log('\nHTTP Methods:');
  report.methods.forEach((count, method) => {
    console.log(`  ${method}: ${count} calls`);
  });

  console.log('\nFields by Endpoint:');
  report.fields.forEach((fields, endpoint) => {
    console.log(`  ${endpoint}: ${[...fields].join(', ')}`);
  });

  if (report.deprecations.length > 0) {
    console.log('\nDeprecation Warnings:');
    [...new Set(report.deprecations)].forEach(d => {
      console.log(`  - ${d}`);
    });
  }
}
```

### Step 2: Version Compatibility Layer

```typescript
// src/api/version-adapter.ts

// API version types
type ApiVersion = 'v1' | 'v2';

interface VersionAdapter {
  transformRequest(data: any): any;
  transformResponse(data: any): any;
  getBaseUrl(): string;
}

// V1 Adapter (current)
class V1Adapter implements VersionAdapter {
  getBaseUrl(): string {
    return 'https://api.getmaintainx.com/v1';
  }

  transformRequest(data: any): any {
    return data;  // No transformation needed for current version
  }

  transformResponse(data: any): any {
    return data;
  }
}

// V2 Adapter (future/hypothetical)
class V2Adapter implements VersionAdapter {
  getBaseUrl(): string {
    return 'https://api.getmaintainx.com/v2';
  }

  transformRequest(data: any): any {
    // Transform V1 request format to V2
    const transformed = { ...data };

    // Example: V2 might rename 'assignees' to 'assigned_users'
    if (transformed.assignees) {
      transformed.assigned_users = transformed.assignees;
      delete transformed.assignees;
    }

    // Example: V2 might use different priority values
    if (transformed.priority) {
      const priorityMap: Record<string, string> = {
        'NONE': 'P4',
        'LOW': 'P3',
        'MEDIUM': 'P2',
        'HIGH': 'P1',
      };
      transformed.priority = priorityMap[transformed.priority] || transformed.priority;
    }

    return transformed;
  }

  transformResponse(data: any): any {
    // Transform V2 response format to V1 for backward compatibility
    const transformed = { ...data };

    // Reverse the transformations
    if (transformed.assigned_users) {
      transformed.assignees = transformed.assigned_users;
      delete transformed.assigned_users;
    }

    if (transformed.priority) {
      const priorityMap: Record<string, string> = {
        'P4': 'NONE',
        'P3': 'LOW',
        'P2': 'MEDIUM',
        'P1': 'HIGH',
      };
      transformed.priority = priorityMap[transformed.priority] || transformed.priority;
    }

    return transformed;
  }
}

// Factory
function createAdapter(version: ApiVersion): VersionAdapter {
  switch (version) {
    case 'v2':
      return new V2Adapter();
    case 'v1':
    default:
      return new V1Adapter();
  }
}

// Version-aware client
class VersionedMaintainXClient {
  private adapter: VersionAdapter;
  private client: AxiosInstance;

  constructor(version: ApiVersion = 'v1') {
    this.adapter = createAdapter(version);
    this.client = axios.create({
      baseURL: this.adapter.getBaseUrl(),
      headers: {
        'Authorization': `Bearer ${process.env.MAINTAINX_API_KEY}`,
        'Content-Type': 'application/json',
      },
    });
  }

  async createWorkOrder(data: any) {
    const transformedRequest = this.adapter.transformRequest(data);
    const response = await this.client.post('/workorders', transformedRequest);
    return this.adapter.transformResponse(response.data);
  }
}
```

### Step 3: Feature Flag for Gradual Migration

```typescript
// src/config/feature-flags.ts

interface FeatureFlags {
  useV2Api: boolean;
  useNewWorkOrderFormat: boolean;
  enableBetaFeatures: boolean;
}

function getFeatureFlags(): FeatureFlags {
  return {
    useV2Api: process.env.USE_V2_API === 'true',
    useNewWorkOrderFormat: process.env.USE_NEW_WO_FORMAT === 'true',
    enableBetaFeatures: process.env.ENABLE_BETA === 'true',
  };
}

// Feature-flagged API client
class MigratableMaintainXClient {
  private v1Client: MaintainXClient;
  private v2Client?: MaintainXClient;
  private flags: FeatureFlags;

  constructor() {
    this.flags = getFeatureFlags();
    this.v1Client = new MaintainXClient();

    if (this.flags.useV2Api) {
      // Initialize V2 client when ready
      // this.v2Client = new MaintainXClientV2();
    }
  }

  async createWorkOrder(data: any) {
    if (this.flags.useV2Api && this.v2Client) {
      return this.v2Client.createWorkOrder(data);
    }
    return this.v1Client.createWorkOrder(data);
  }
}
```

### Step 4: Migration Testing

```typescript
// tests/migration.test.ts

describe('API Migration Tests', () => {
  describe('Request Transformation', () => {
    it('should transform V1 work order to V2 format', () => {
      const v1Data = {
        title: 'Test Work Order',
        priority: 'HIGH',
        assignees: ['user1', 'user2'],
      };

      const adapter = new V2Adapter();
      const v2Data = adapter.transformRequest(v1Data);

      expect(v2Data.title).toBe('Test Work Order');
      expect(v2Data.priority).toBe('P1');
      expect(v2Data.assigned_users).toEqual(['user1', 'user2']);
      expect(v2Data.assignees).toBeUndefined();
    });
  });

  describe('Response Transformation', () => {
    it('should transform V2 response to V1 format', () => {
      const v2Response = {
        id: 'wo_123',
        title: 'Test',
        priority: 'P1',
        assigned_users: ['user1'],
      };

      const adapter = new V2Adapter();
      const v1Response = adapter.transformResponse(v2Response);

      expect(v1Response.priority).toBe('HIGH');
      expect(v1Response.assignees).toEqual(['user1']);
      expect(v1Response.assigned_users).toBeUndefined();
    });
  });

  describe('Parallel API Calls', () => {
    it('should return same results from both API versions', async () => {
      const v1Client = new VersionedMaintainXClient('v1');
      // const v2Client = new VersionedMaintainXClient('v2');

      const v1WorkOrders = await v1Client.getWorkOrders({ limit: 10 });
      // const v2WorkOrders = await v2Client.getWorkOrders({ limit: 10 });

      // Compare results (accounting for transformations)
      // expect(v1WorkOrders.length).toBe(v2WorkOrders.length);
    });
  });
});
```

### Step 5: Rollback Plan

```typescript
// scripts/rollback.ts

interface RollbackStep {
  name: string;
  execute: () => Promise<void>;
}

const rollbackSteps: RollbackStep[] = [
  {
    name: 'Disable V2 API flag',
    execute: async () => {
      // Update feature flag
      console.log('Setting USE_V2_API=false');
      // In practice, update your feature flag service
    },
  },
  {
    name: 'Restart services',
    execute: async () => {
      console.log('Restarting services to pick up flag change');
      // kubectl rollout restart deployment/your-app
    },
  },
  {
    name: 'Verify V1 API usage',
    execute: async () => {
      console.log('Verifying API calls are using V1');
      // Check logs for API version
    },
  },
  {
    name: 'Monitor for errors',
    execute: async () => {
      console.log('Monitoring error rates...');
      // Check monitoring dashboards
    },
  },
];

async function executeRollback() {
  console.log('=== Executing API Rollback ===\n');

  for (const step of rollbackSteps) {
    console.log(`Executing: ${step.name}`);
    try {
      await step.execute();
      console.log(`  [DONE]\n`);
    } catch (error: any) {
      console.error(`  [FAILED] ${error.message}`);
      console.error('Rollback halted. Manual intervention required.');
      process.exit(1);
    }
  }

  console.log('=== Rollback Complete ===');
}
```

## Migration Checklist

- [ ] Analyzed current API usage
- [ ] Identified deprecated features
- [ ] Created version adapter layer
- [ ] Set up feature flags
- [ ] Written migration tests
- [ ] Documented rollback procedure
- [ ] Tested in staging environment
- [ ] Communicated timeline to stakeholders
- [ ] Scheduled maintenance window
- [ ] Prepared monitoring dashboards

## Output

- API usage analysis report
- Version compatibility layer
- Feature flag configuration
- Migration tests passing
- Rollback procedure documented

## Resources

- [MaintainX API Documentation](https://maintainx.dev/)
- [MaintainX Changelog](https://maintainx.dev/changelog)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)

## Next Steps

For CI/CD integration, see `maintainx-ci-integration`.
