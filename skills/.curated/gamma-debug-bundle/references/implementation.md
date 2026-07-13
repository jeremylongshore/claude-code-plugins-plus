# Gamma Debug Bundle - Implementation Details

## Debug Client with Request Tracing

```typescript
// debug/gamma-debug.ts
interface DebugLog {
  timestamp: string; method: string; path: string;
  requestBody?: object; responseBody?: object;
  duration: number; status: number; error?: string;
}

const logs: DebugLog[] = [];

export function createDebugClient() {
  const gamma = new GammaClient({
    apiKey: process.env.GAMMA_API_KEY,
    interceptors: {
      request: (config) => {
        config._startTime = Date.now();
        config._id = crypto.randomUUID();
        console.log(`[${config._id}] -> ${config.method} ${config.path}`);
        return config;
      },
      response: (response, config) => {
        const duration = Date.now() - config._startTime;
        console.log(`[${config._id}] <- ${response.status} (${duration}ms)`);
        logs.push({ timestamp: new Date().toISOString(), method: config.method,
          path: config.path, requestBody: config.body, responseBody: response.data,
          duration, status: response.status });
        return response;
      },
      error: (error, config) => {
        const duration = Date.now() - config._startTime;
        logs.push({ timestamp: new Date().toISOString(), method: config.method,
          path: config.path, duration, status: error.status || 0, error: error.message });
        throw error;
      },
    },
  });
  return { gamma, getLogs: () => [...logs], clearLogs: () => logs.length = 0 };
}
```

## Diagnostic Script

```typescript
// debug/diagnose.ts
async function diagnose() {
  const { gamma, getLogs } = createDebugClient();
  console.log('=== Gamma Diagnostic Report ===\n');

  // Test 1: Authentication
  console.log('1. Testing Authentication...');
  try { await gamma.ping(); console.log('   OK\n'); }
  catch (err) { console.log(`   FAIL - ${err.message}\n`); return; }

  // Test 2: API Access
  console.log('2. Testing API Access...');
  try {
    const presentations = await gamma.presentations.list({ limit: 1 });
    console.log(`   OK - ${presentations.length} found\n`);
  } catch (err) { console.log(`   FAIL - ${err.message}\n`); }

  // Test 3: Generation
  console.log('3. Testing Generation...');
  try {
    await gamma.presentations.create({ title: 'Debug Test', prompt: 'Single test slide', slideCount: 1, dryRun: true });
    console.log('   OK\n');
  } catch (err) { console.log(`   FAIL - ${err.message}\n`); }

  // Test 4: Rate Limits
  const status = await gamma.rateLimit.status();
  console.log(`4. Rate Limits: ${status.remaining}/${status.limit}\n`);

  // Summary
  console.log('=== Request Log ===');
  for (const log of getLogs()) {
    console.log(`${log.method} ${log.path} - ${log.status} (${log.duration}ms)`);
  }
}
```

## Environment Checker

```typescript
function checkEnvironment() {
  const checks = [
    { name: 'GAMMA_API_KEY', value: process.env.GAMMA_API_KEY },
    { name: 'NODE_ENV', value: process.env.NODE_ENV },
    { name: 'Node Version', value: process.version },
  ];
  console.log('=== Environment Check ===\n');
  for (const check of checks) {
    const status = check.value ? 'SET' : 'MISSING';
    console.log(`${check.name}: ${status} (${check.value?.substring(0, 8) || 'NOT SET'}...)`);
  }
}
```

## Export Debug Bundle

```typescript
async function exportDebugBundle() {
  const bundle = {
    timestamp: new Date().toISOString(),
    environment: { nodeVersion: process.version, platform: process.platform, env: process.env.NODE_ENV },
    logs: getLogs(),
    config: { apiKeySet: !!process.env.GAMMA_API_KEY, timeout: 30000 },
  };
  await fs.writeFile('gamma-debug-bundle.json', JSON.stringify(bundle, null, 2));
  console.log('Debug bundle exported to gamma-debug-bundle.json');
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
