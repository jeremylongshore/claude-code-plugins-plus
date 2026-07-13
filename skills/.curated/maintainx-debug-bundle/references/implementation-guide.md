# MaintainX Debug Bundle - Implementation Guide

> Full implementation details and code examples for the `maintainx-debug-bundle` skill.

# MaintainX Debug Bundle

## Overview

Complete debugging toolkit for diagnosing and resolving MaintainX integration issues with detailed logging, diagnostic scripts, and troubleshooting procedures.

## Prerequisites

- MaintainX API access configured
- Node.js environment
- curl for direct API testing

## Instructions

### Step 1: Environment Diagnostic

```typescript
// scripts/diagnose-env.ts
import axios from 'axios';

interface DiagnosticResult {
  category: string;
  check: string;
  status: 'PASS' | 'FAIL' | 'WARN';
  message: string;
}

async function runDiagnostics(): Promise<DiagnosticResult[]> {
  const results: DiagnosticResult[] = [];

  // Check 1: API Key presence
  const apiKey = process.env.MAINTAINX_API_KEY;
  results.push({
    category: 'Environment',
    check: 'API Key Configured',
    status: apiKey ? 'PASS' : 'FAIL',
    message: apiKey ? 'API key is set' : 'MAINTAINX_API_KEY not found',
  });

  // Check 2: API Key format
  if (apiKey) {
    const isValidFormat = apiKey.length > 20 && !apiKey.includes(' ');
    results.push({
      category: 'Environment',
      check: 'API Key Format',
      status: isValidFormat ? 'PASS' : 'WARN',
      message: isValidFormat
        ? 'API key format appears valid'
        : 'API key format may be incorrect',
    });
  }

  // Check 3: Network connectivity
  try {
    await axios.get('https://api.getmaintainx.com', { timeout: 5000 });
    results.push({
      category: 'Network',
      check: 'API Reachable',
      status: 'PASS',
      message: 'Can reach MaintainX API endpoint',
    });
  } catch (error: any) {
    results.push({
      category: 'Network',
      check: 'API Reachable',
      status: 'FAIL',
      message: `Cannot reach API: ${error.message}`,
    });
  }

  // Check 4: Authentication
  if (apiKey) {
    try {
      const response = await axios.get(
        'https://api.getmaintainx.com/v1/users?limit=1',
        {
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json',
          },
          timeout: 10000,
        }
      );
      results.push({
        category: 'Authentication',
        check: 'API Key Valid',
        status: 'PASS',
        message: 'Successfully authenticated with API',
      });
    } catch (error: any) {
      const status = error.response?.status;
      results.push({
        category: 'Authentication',
        check: 'API Key Valid',
        status: 'FAIL',
        message: `Authentication failed: HTTP ${status || error.message}`,
      });
    }
  }

  // Check 5: Node.js version
  const nodeVersion = process.version;
  const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
  results.push({
    category: 'Environment',
    check: 'Node.js Version',
    status: majorVersion >= 18 ? 'PASS' : 'WARN',
    message: `Node.js ${nodeVersion} (18+ recommended)`,
  });

  return results;
}

// Print results
async function main() {
  console.log('=== MaintainX Integration Diagnostics ===\n');

  const results = await runDiagnostics();

  // Group by category
  const categories = [...new Set(results.map(r => r.category))];

  categories.forEach(category => {
    console.log(`\n${category}:`);
    results
      .filter(r => r.category === category)
      .forEach(r => {
        const icon = r.status === 'PASS' ? '[OK]' : r.status === 'FAIL' ? '[!!]' : '[?]';
        console.log(`  ${icon} ${r.check}: ${r.message}`);
      });
  });

  // Summary
  const passed = results.filter(r => r.status === 'PASS').length;
  const failed = results.filter(r => r.status === 'FAIL').length;
  const warned = results.filter(r => r.status === 'WARN').length;

  console.log(`\n=== Summary ===`);
  console.log(`Passed: ${passed}, Failed: ${failed}, Warnings: ${warned}`);

  if (failed > 0) {
    console.log('\nAction Required: Fix failed checks before proceeding.');
    process.exit(1);
  }
}

main().catch(console.error);
```

### Step 2: Request/Response Logger

```typescript
// src/debug/logger.ts
import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import fs from 'fs';
import path from 'path';

interface LogEntry {
  timestamp: string;
  requestId: string;
  method: string;
  url: string;
  requestHeaders: Record<string, string>;
  requestBody?: any;
  responseStatus?: number;
  responseHeaders?: Record<string, string>;
  responseBody?: any;
  duration?: number;
  error?: string;
}

class DebugLogger {
  private logs: LogEntry[] = [];
  private logFile: string;

  constructor(logDir = './logs') {
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    this.logFile = path.join(logDir, `maintainx-debug-${Date.now()}.json`);
  }

  createInterceptors(client: AxiosInstance) {
    // Request interceptor
    client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const requestId = `req_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
        (config as any).metadata = {
          requestId,
          startTime: Date.now(),
        };

        const entry: LogEntry = {
          timestamp: new Date().toISOString(),
          requestId,
          method: config.method?.toUpperCase() || 'UNKNOWN',
          url: `${config.baseURL}${config.url}`,
          requestHeaders: this.sanitizeHeaders(config.headers as Record<string, string>),
          requestBody: config.data,
        };

        this.logs.push(entry);
        this.writeLog();

        console.log(`[${requestId}] ${entry.method} ${entry.url}`);
        return config;
      },
      error => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    client.interceptors.response.use(
      (response: AxiosResponse) => {
        const metadata = (response.config as any).metadata;
        const entry = this.logs.find(l => l.requestId === metadata?.requestId);

        if (entry) {
          entry.responseStatus = response.status;
          entry.responseHeaders = response.headers as Record<string, string>;
          entry.responseBody = response.data;
          entry.duration = Date.now() - metadata.startTime;
          this.writeLog();

          console.log(`[${entry.requestId}] ${response.status} (${entry.duration}ms)`);
        }

        return response;
      },
      error => {
        const metadata = (error.config as any)?.metadata;
        const entry = this.logs.find(l => l.requestId === metadata?.requestId);

        if (entry) {
          entry.responseStatus = error.response?.status;
          entry.responseBody = error.response?.data;
          entry.error = error.message;
          entry.duration = metadata ? Date.now() - metadata.startTime : undefined;
          this.writeLog();

          console.error(`[${entry.requestId}] ERROR: ${error.response?.status || error.message}`);
        }

        return Promise.reject(error);
      }
    );
  }

  private sanitizeHeaders(headers: Record<string, string>): Record<string, string> {
    const sanitized = { ...headers };
    if (sanitized.Authorization) {
      sanitized.Authorization = 'Bearer [REDACTED]';
    }
    return sanitized;
  }

  private writeLog() {
    fs.writeFileSync(this.logFile, JSON.stringify(this.logs, null, 2));
  }

  getLogs(): LogEntry[] {
    return this.logs;
  }

  getLogFile(): string {
    return this.logFile;
  }

  printSummary() {
    console.log('\n=== Debug Log Summary ===');
    console.log(`Total requests: ${this.logs.length}`);
    console.log(`Log file: ${this.logFile}`);

    const errors = this.logs.filter(l => l.error || (l.responseStatus && l.responseStatus >= 400));
    if (errors.length > 0) {
      console.log(`\nErrors (${errors.length}):`);
      errors.forEach(e => {
        console.log(`  - [${e.requestId}] ${e.method} ${e.url}: ${e.responseStatus || e.error}`);
      });
    }
  }
}

export { DebugLogger };
```

### Step 3: API Health Check Script

```bash
#!/bin/bash
# scripts/health-check.sh

set -e

echo "=== MaintainX API Health Check ==="
echo ""

# Check environment
if [ -z "$MAINTAINX_API_KEY" ]; then
  echo "[FAIL] MAINTAINX_API_KEY not set"
  exit 1
fi
echo "[OK] API key configured"

# Test endpoints
ENDPOINTS=(
  "/v1/users?limit=1"
  "/v1/workorders?limit=1"
  "/v1/assets?limit=1"
  "/v1/locations?limit=1"
)

BASE_URL="https://api.getmaintainx.com"

for endpoint in "${ENDPOINTS[@]}"; do
  echo -n "Testing $endpoint... "

  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $MAINTAINX_API_KEY" \
    -H "Content-Type: application/json" \
    "$BASE_URL$endpoint")

  if [ "$HTTP_CODE" == "200" ]; then
    echo "[OK] HTTP $HTTP_CODE"
  elif [ "$HTTP_CODE" == "429" ]; then
    echo "[WARN] Rate limited (HTTP 429)"
  else
    echo "[FAIL] HTTP $HTTP_CODE"
  fi
done

echo ""
echo "=== Health Check Complete ==="
```

### Step 4: Data Validation Tool

```typescript
// scripts/validate-data.ts
import { MaintainXClient } from '../src/api/maintainx-client';

interface ValidationIssue {
  resource: string;
  resourceId: string;
  issue: string;
  severity: 'error' | 'warning' | 'info';
}

async function validateData(client: MaintainXClient): Promise<ValidationIssue[]> {
  const issues: ValidationIssue[] = [];

  console.log('Validating MaintainX data...\n');

  // Validate Work Orders
  console.log('Checking work orders...');
  const workOrders = await client.getWorkOrders({ limit: 100 });

  workOrders.workOrders.forEach(wo => {
    // Check for missing title
    if (!wo.title || wo.title.trim() === '') {
      issues.push({
        resource: 'WorkOrder',
        resourceId: wo.id,
        issue: 'Missing title',
        severity: 'error',
      });
    }

    // Check for overdue open work orders
    if (wo.status === 'OPEN' && wo.dueDate) {
      const dueDate = new Date(wo.dueDate);
      if (dueDate < new Date()) {
        issues.push({
          resource: 'WorkOrder',
          resourceId: wo.id,
          issue: `Overdue since ${dueDate.toLocaleDateString()}`,
          severity: 'warning',
        });
      }
    }

    // Check for high priority without assignee
    if (wo.priority === 'HIGH' && (!wo.assignees || wo.assignees.length === 0)) {
      issues.push({
        resource: 'WorkOrder',
        resourceId: wo.id,
        issue: 'High priority work order without assignee',
        severity: 'warning',
      });
    }
  });

  // Validate Assets
  console.log('Checking assets...');
  const assets = await client.getAssets({ limit: 100 });

  assets.assets.forEach(asset => {
    // Check for assets without location
    if (!asset.locationId) {
      issues.push({
        resource: 'Asset',
        resourceId: asset.id,
        issue: 'Asset not assigned to a location',
        severity: 'info',
      });
    }

    // Check for non-operational assets
    if (asset.status === 'NON_OPERATIONAL') {
      issues.push({
        resource: 'Asset',
        resourceId: asset.id,
        issue: 'Asset marked as non-operational',
        severity: 'warning',
      });
    }
  });

  return issues;
}

// Run validation
async function main() {
  const client = new MaintainXClient();
  const issues = await validateData(client);

  console.log('\n=== Validation Results ===\n');

  if (issues.length === 0) {
    console.log('No issues found!');
    return;
  }

  // Group by severity
  const errors = issues.filter(i => i.severity === 'error');
  const warnings = issues.filter(i => i.severity === 'warning');
  const infos = issues.filter(i => i.severity === 'info');

  if (errors.length > 0) {
    console.log(`ERRORS (${errors.length}):`);
    errors.forEach(i => console.log(`  [${i.resource}:${i.resourceId}] ${i.issue}`));
  }

  if (warnings.length > 0) {
    console.log(`\nWARNINGS (${warnings.length}):`);
    warnings.forEach(i => console.log(`  [${i.resource}:${i.resourceId}] ${i.issue}`));
  }

  if (infos.length > 0) {
    console.log(`\nINFO (${infos.length}):`);
    infos.forEach(i => console.log(`  [${i.resource}:${i.resourceId}] ${i.issue}`));
  }

  console.log(`\nTotal: ${errors.length} errors, ${warnings.length} warnings, ${infos.length} info`);
}

main().catch(console.error);
```

### Step 5: Network Debug with Verbose Logging

```bash
#!/bin/bash
# scripts/verbose-request.sh

# Make a verbose request to MaintainX API
curl -v \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.getmaintainx.com/v1/workorders?limit=1" 2>&1 | tee maintainx-debug.log

echo ""
echo "Full output saved to maintainx-debug.log"
```

### Step 6: Support Bundle Generator

```typescript
// scripts/generate-support-bundle.ts
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

interface SupportBundle {
  generated: string;
  environment: Record<string, string>;
  nodeVersion: string;
  npmVersion: string;
  installedPackages: string[];
  diagnostics: any;
  recentLogs: any[];
}

async function generateSupportBundle(): Promise<void> {
  console.log('Generating MaintainX Support Bundle...\n');

  const bundle: SupportBundle = {
    generated: new Date().toISOString(),
    environment: {
      NODE_ENV: process.env.NODE_ENV || 'development',
      MAINTAINX_API_KEY: process.env.MAINTAINX_API_KEY ? '[SET]' : '[NOT SET]',
    },
    nodeVersion: process.version,
    npmVersion: execSync('npm --version').toString().trim(),
    installedPackages: [],
    diagnostics: {},
    recentLogs: [],
  };

  // Get relevant packages
  try {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    bundle.installedPackages = Object.keys(packageJson.dependencies || {});
  } catch (e) {
    bundle.installedPackages = ['Unable to read package.json'];
  }

  // Include recent logs if available
  const logsDir = './logs';
  if (fs.existsSync(logsDir)) {
    const logFiles = fs.readdirSync(logsDir)
      .filter(f => f.endsWith('.json'))
      .sort()
      .slice(-5);

    logFiles.forEach(file => {
      try {
        const content = JSON.parse(fs.readFileSync(path.join(logsDir, file), 'utf8'));
        bundle.recentLogs.push({ file, content: content.slice(-20) });
      } catch (e) {
        // Skip unreadable files
      }
    });
  }

  // Write bundle
  const bundlePath = `maintainx-support-bundle-${Date.now()}.json`;
  fs.writeFileSync(bundlePath, JSON.stringify(bundle, null, 2));

  console.log(`Support bundle generated: ${bundlePath}`);
  console.log('\nIncluded:');
  console.log('  - Environment information');
  console.log('  - Node.js and npm versions');
  console.log('  - Installed packages');
  console.log('  - Recent API logs');
  console.log('\nShare this file (without API keys) when requesting support.');
}

generateSupportBundle().catch(console.error);
```

## Output

- Environment diagnostic report
- Request/response logs with timing
- API health check results
- Data validation issues
- Support bundle for troubleshooting

## Debug Commands Quick Reference

```bash
# Run environment diagnostics
npx ts-node scripts/diagnose-env.ts

# API health check
./scripts/health-check.sh

# Validate data
npx ts-node scripts/validate-data.ts

# Generate support bundle
npx ts-node scripts/generate-support-bundle.ts

# Verbose API request
./scripts/verbose-request.sh
```

## Resources

- [MaintainX Help Center](https://help.getmaintainx.com/)
- [MaintainX API Status](https://status.getmaintainx.com)
- [MaintainX Community](https://community.getmaintainx.com/)

## Next Steps

For rate limit handling, see `maintainx-rate-limits`.
