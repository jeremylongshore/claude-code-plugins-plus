# TwinMind Multi-Environment Setup - Detailed Implementation

## Environment Configuration

```typescript
export type Environment = 'development' | 'staging' | 'production';

export interface EnvironmentConfig {
  name: Environment;
  twinmind: {
    apiKey: string;
    baseUrl: string;
    webhookSecret: string;
    model: 'ear-2' | 'ear-3';
    features: { diarization: boolean; autoSummary: boolean; actionItems: boolean; debug: boolean };
  };
  limits: { rateLimit: number; concurrentJobs: number; dailyQuota?: number };
  integrations: { slack?: { webhook: string; channel: string }; calendar?: { enabled: boolean }; email?: { enabled: boolean } };
}

const configs: Record<Environment, EnvironmentConfig> = {
  development: {
    name: 'development',
    twinmind: {
      apiKey: process.env.TWINMIND_API_KEY_DEV!,
      baseUrl: 'https://api.twinmind.com/v1',
      webhookSecret: process.env.TWINMIND_WEBHOOK_SECRET_DEV!,
      model: 'ear-2',
      features: { diarization: false, autoSummary: true, actionItems: true, debug: true },
    },
    limits: { rateLimit: 30, concurrentJobs: 1, dailyQuota: 10 },
    integrations: { slack: { webhook: process.env.SLACK_WEBHOOK_DEV!, channel: '#dev-alerts' }, calendar: { enabled: false }, email: { enabled: false } },
  },
  staging: {
    name: 'staging',
    twinmind: {
      apiKey: process.env.TWINMIND_API_KEY_STAGING!,
      baseUrl: 'https://api.twinmind.com/v1',
      webhookSecret: process.env.TWINMIND_WEBHOOK_SECRET_STAGING!,
      model: 'ear-3',
      features: { diarization: true, autoSummary: true, actionItems: true, debug: true },
    },
    limits: { rateLimit: 60, concurrentJobs: 2, dailyQuota: 50 },
    integrations: { slack: { webhook: process.env.SLACK_WEBHOOK_STAGING!, channel: '#staging-alerts' }, calendar: { enabled: true }, email: { enabled: false } },
  },
  production: {
    name: 'production',
    twinmind: {
      apiKey: process.env.TWINMIND_API_KEY_PROD!,
      baseUrl: 'https://api.twinmind.com/v1',
      webhookSecret: process.env.TWINMIND_WEBHOOK_SECRET_PROD!,
      model: 'ear-3',
      features: { diarization: true, autoSummary: true, actionItems: true, debug: false },
    },
    limits: { rateLimit: 300, concurrentJobs: 10 },
    integrations: { slack: { webhook: process.env.SLACK_WEBHOOK_PROD!, channel: '#production-alerts' }, calendar: { enabled: true }, email: { enabled: true } },
  },
};

export function getEnvironmentConfig(): EnvironmentConfig {
  const env = (process.env.NODE_ENV || 'development') as Environment;
  return configs[env];
}
```

## Environment Variable Files

```bash
# .env.development
NODE_ENV=development
TWINMIND_API_KEY_DEV=tm_sk_dev_xxx
TWINMIND_WEBHOOK_SECRET_DEV=whsec_dev_xxx

# .env.staging
NODE_ENV=staging
TWINMIND_API_KEY_STAGING=tm_sk_staging_xxx

# .env.production
NODE_ENV=production
TWINMIND_API_KEY_PROD=tm_sk_prod_xxx

# .env.example (committed)
NODE_ENV=development
TWINMIND_API_KEY_DEV=
TWINMIND_WEBHOOK_SECRET_DEV=
```

## Client Factory

```typescript
const clients = new Map<Environment, TwinMindClient>();

export function getTwinMindClient(env?: Environment): TwinMindClient {
  const config = getEnvironmentConfig();
  const targetEnv = env || config.name;

  if (!clients.has(targetEnv)) {
    const envConfig = configs[targetEnv];
    clients.set(targetEnv, new TwinMindClient({
      apiKey: envConfig.twinmind.apiKey,
      baseUrl: envConfig.twinmind.baseUrl,
      debug: envConfig.twinmind.features.debug,
    }));
  }
  return clients.get(targetEnv)!;
}
```

## Environment Validation

```typescript
async function validateEnvironment(env: Environment): Promise<{ valid: boolean; issues: string[] }> {
  const issues: string[] = [];
  const envUpper = env === 'development' ? 'DEV' : env === 'staging' ? 'STAGING' : 'PROD';

  const apiKeyVar = `TWINMIND_API_KEY_${envUpper}`;
  if (!process.env[apiKeyVar]) issues.push(`Missing: ${apiKeyVar}`);
  else if (!process.env[apiKeyVar]!.startsWith('tm_sk_')) issues.push('Invalid API key format');

  if (process.env[apiKeyVar]) {
    try {
      const response = await fetch('https://api.twinmind.com/v1/health', { headers: { 'Authorization': `Bearer ${process.env[apiKeyVar]}` } });
      if (!response.ok) issues.push(`Health check failed: ${response.status}`);
    } catch (e: any) { issues.push(`Connectivity failed: ${e.message}`); }
  }

  return { valid: issues.length === 0, issues };
}

async function validateAll() {
  for (const env of ['development', 'staging', 'production'] as Environment[]) {
    const result = await validateEnvironment(env);
    console.log(`${env.toUpperCase()}: ${result.valid ? 'VALID' : 'INVALID'}`);
    result.issues.forEach(i => console.log(`  - ${i}`));
  }
}
```

## Config Promotion

```typescript
async function promoteConfig(fromEnv: 'development' | 'staging', toEnv: 'staging' | 'production'): Promise<{ changes: string[] }> {
  const sourceConfig = JSON.parse(fs.readFileSync(`config/twinmind.${fromEnv}.json`, 'utf-8'));
  const targetConfig = JSON.parse(fs.readFileSync(`config/twinmind.${toEnv}.json`, 'utf-8'));
  const changes: string[] = [];

  for (const key of ['features', 'webhookEvents', 'integrationSettings']) {
    if (JSON.stringify(sourceConfig[key]) !== JSON.stringify(targetConfig[key])) {
      changes.push(`${key}: ${JSON.stringify(sourceConfig[key])}`);
      targetConfig[key] = sourceConfig[key];
    }
  }

  if (changes.length > 0) fs.writeFileSync(`config/twinmind.${toEnv}.json`, JSON.stringify(targetConfig, null, 2));
  return { changes };
}
```

## Feature Flags

```typescript
export interface FeatureFlags {
  enableDiarization: boolean;
  enableAutoSummary: boolean;
  enableRealTimeTranscription: boolean;
  enableEmailFollowUps: boolean;
  maxAudioDurationMinutes: number;
  enableBetaFeatures: boolean;
}

const environmentFlags: Record<Environment, Partial<FeatureFlags>> = {
  development: { enableBetaFeatures: true, maxAudioDurationMinutes: 10 },
  staging: { enableDiarization: true, enableBetaFeatures: true, maxAudioDurationMinutes: 30 },
  production: { enableDiarization: true, enableRealTimeTranscription: true, enableEmailFollowUps: true, maxAudioDurationMinutes: 120 },
};

export function getFeatureFlags(): FeatureFlags {
  const config = getEnvironmentConfig();
  return { enableDiarization: false, enableAutoSummary: true, enableRealTimeTranscription: false, enableEmailFollowUps: false, maxAudioDurationMinutes: 60, enableBetaFeatures: false, ...environmentFlags[config.name] };
}

export function isFeatureEnabled(feature: keyof FeatureFlags): boolean {
  return Boolean(getFeatureFlags()[feature]);
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
