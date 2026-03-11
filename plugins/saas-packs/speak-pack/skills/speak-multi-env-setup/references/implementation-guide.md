# Speak Multi Env Setup - Implementation Guide

Detailed implementation reference for the speak-multi-env-setup skill.

## Environment Strategy

| Environment | Purpose | API Keys | Data | Languages |
|-------------|---------|----------|------|-----------|
| Development | Local dev | Sandbox keys | Mock/test | All enabled |
| Staging | Pre-prod validation | Staging keys | Test data | All enabled |
| Production | Live users | Production keys | Real data | Enabled per plan |


## Configuration Structure

```
config/
├── speak/
│   ├── base.json           # Shared config
│   ├── development.json    # Dev overrides
│   ├── staging.json        # Staging overrides
│   └── production.json     # Prod overrides
```

### base.json
```json
{
  "timeout": 30000,
  "retries": 3,
  "cache": {
    "enabled": true,
    "ttlSeconds": 300
  },
  "audio": {
    "maxDuration": 60,
    "format": "wav",
    "sampleRate": 16000
  },
  "supportedLanguages": ["en", "es", "fr", "de", "ko", "ja", "zh-CN", "pt-BR"]
}
```

### development.json
```json
{
  "baseUrl": "https://api-sandbox.speak.com",
  "debug": true,
  "cache": {
    "enabled": false
  },
  "mockMode": true,
  "features": {
    "experimentalTutor": true,
    "betaSpeechEngine": true,
    "allLanguages": true
  }
}
```

### staging.json
```json
{
  "baseUrl": "https://api-staging.speak.com",
  "debug": false,
  "features": {
    "experimentalTutor": true,
    "betaSpeechEngine": false,
    "allLanguages": true
  },
  "rateLimits": {
    "lessonsPerHour": 100,
    "audioMinutesPerHour": 60
  }
}
```

### production.json
```json
{
  "baseUrl": "https://api.speak.com",
  "debug": false,
  "retries": 5,
  "features": {
    "experimentalTutor": false,
    "betaSpeechEngine": false,
    "allLanguages": false
  },
  "rateLimits": {
    "lessonsPerHour": 1000,
    "audioMinutesPerHour": 500
  }
}
```


## Environment Detection

```typescript
// src/speak/config.ts
import baseConfig from '../../config/speak/base.json';

type Environment = 'development' | 'staging' | 'production';

function detectEnvironment(): Environment {
  // Check multiple sources for environment
  const env = process.env.SPEAK_ENV ||
              process.env.NODE_ENV ||
              'development';

  const validEnvs: Environment[] = ['development', 'staging', 'production'];
  return validEnvs.includes(env as Environment)
    ? (env as Environment)
    : 'development';
}

export function getSpeakConfig(): SpeakConfig {
  const env = detectEnvironment();
  const envConfig = require(`../../config/speak/${env}.json`);

  return {
    ...baseConfig,
    ...envConfig,
    apiKey: process.env.SPEAK_API_KEY!,
    appId: process.env.SPEAK_APP_ID!,
    webhookSecret: process.env.SPEAK_WEBHOOK_SECRET,
    environment: env,
  };
}
```


## Secret Management by Environment

### Local Development
```bash
# .env.local (git-ignored)
SPEAK_ENV=development
SPEAK_API_KEY=sk_sandbox_***
SPEAK_APP_ID=app_dev_***
SPEAK_MOCK_MODE=true
```

### CI/CD (GitHub Actions)
```yaml
jobs:
  deploy:
    environment: ${{ matrix.environment }}
    env:
      SPEAK_ENV: ${{ matrix.environment }}
      SPEAK_API_KEY: ${{ secrets[format('SPEAK_API_KEY_{0}', matrix.environment)] }}
      SPEAK_APP_ID: ${{ secrets[format('SPEAK_APP_ID_{0}', matrix.environment)] }}
    strategy:
      matrix:
        environment: [staging, production]
```

### Production (Vault/Secrets Manager)
```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id speak/production/credentials

# GCP Secret Manager
gcloud secrets versions access latest \
  --secret=speak-production-api-key

# HashiCorp Vault
vault kv get -field=api_key secret/speak/production
```


## Environment Isolation

### Prevent Production Operations in Non-Prod
```typescript
function guardProductionOperation(operation: string): void {
  const config = getSpeakConfig();

  if (config.environment !== 'production') {
    console.warn(`[speak] ${operation} blocked in ${config.environment}`);
    throw new Error(`${operation} only allowed in production`);
  }
}

// Usage
async function deleteUserData(userId: string): Promise<void> {
  guardProductionOperation('deleteUserData');
  await speakClient.users.delete(userId);
}
```

### Environment-Specific Lesson Restrictions
```typescript
function getAvailableLanguages(): string[] {
  const config = getSpeakConfig();

  if (config.features?.allLanguages) {
    return config.supportedLanguages;
  }

  // Production: Only enabled languages for user's plan
  return getUserPlanLanguages();
}

function canAccessFeature(feature: string): boolean {
  const config = getSpeakConfig();
  return config.features?.[feature] ?? false;
}
```


## Feature Flags by Environment

```typescript
interface FeatureFlags {
  experimentalTutor: boolean;
  betaSpeechEngine: boolean;
  newPronunciationModel: boolean;
  gamificationV2: boolean;
  offlineMode: boolean;
}

const featureFlags: Record<Environment, FeatureFlags> = {
  development: {
    experimentalTutor: true,
    betaSpeechEngine: true,
    newPronunciationModel: true,
    gamificationV2: true,
    offlineMode: true,
  },
  staging: {
    experimentalTutor: true,
    betaSpeechEngine: true,
    newPronunciationModel: true,
    gamificationV2: false,
    offlineMode: false,
  },
  production: {
    experimentalTutor: false,
    betaSpeechEngine: false,
    newPronunciationModel: false,
    gamificationV2: false,
    offlineMode: false,
  },
};

export function isFeatureEnabled(feature: keyof FeatureFlags): boolean {
  const env = detectEnvironment();
  return featureFlags[env][feature];
}
```


## Environment-Specific Audio Storage

```typescript
interface AudioStorageConfig {
  type: 'local' | 's3' | 'gcs';
  bucket?: string;
  encryption: boolean;
  retention: number; // days
}

const audioStorage: Record<Environment, AudioStorageConfig> = {
  development: {
    type: 'local',
    encryption: false,
    retention: 1,
  },
  staging: {
    type: 's3',
    bucket: 'speak-staging-audio',
    encryption: true,
    retention: 7,
  },
  production: {
    type: 's3',
    bucket: 'speak-production-audio',
    encryption: true,
    retention: 30,
  },
};
```


## Environment Health Checks

```typescript
async function verifyEnvironmentConfig(): Promise<EnvironmentCheck> {
  const config = getSpeakConfig();
  const checks = {
    apiKeyValid: false,
    canConnect: false,
    correctEnvironment: false,
    featuresAccessible: false,
  };

  try {
    // Verify API key
    const health = await speakClient.health.check();
    checks.apiKeyValid = true;
    checks.canConnect = health.healthy;

    // Verify we're hitting the right environment
    const expectedBase = config.baseUrl;
    checks.correctEnvironment = health.endpoint.includes(
      config.environment === 'production' ? 'api.speak.com' : `api-${config.environment}`
    );

    // Verify feature access
    if (config.features?.experimentalTutor) {
      checks.featuresAccessible = await canAccessExperimentalTutor();
    } else {
      checks.featuresAccessible = true;
    }
  } catch (error) {
    console.error('Environment verification failed:', error);
  }

  return {
    environment: config.environment,
    checks,
    allPassed: Object.values(checks).every(Boolean),
  };
}
```


## Detailed Examples

### Quick Environment Check
```typescript
const config = getSpeakConfig();
console.log(`Environment: ${config.environment}`);
console.log(`API Base: ${config.baseUrl}`);
console.log(`Mock Mode: ${config.mockMode ? 'ON' : 'OFF'}`);
console.log(`Features:`, config.features);
```

### Environment Switching Script
```bash
#!/bin/bash
# switch-speak-env.sh

case "$1" in
  dev)
    export SPEAK_ENV=development
    export SPEAK_API_KEY=$(vault kv get -field=api_key secret/speak/development)
    ;;
  staging)
    export SPEAK_ENV=staging
    export SPEAK_API_KEY=$(vault kv get -field=api_key secret/speak/staging)
    ;;
  prod)
    export SPEAK_ENV=production
    export SPEAK_API_KEY=$(vault kv get -field=api_key secret/speak/production)
    ;;
esac

echo "Switched to $SPEAK_ENV environment"
```

