# Evernote Multi-Environment Setup - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Environment Configuration Files

```bash
project/
├── config/
│   ├── default.js        # Shared defaults
│   ├── development.js    # Dev overrides
│   ├── staging.js        # Staging overrides
│   └── production.js     # Production overrides
├── .env.development
├── .env.staging
├── .env.production
└── .env.example
```

```javascript
// config/default.js
module.exports = {
  evernote: {
    requestTimeout: 30000,
    connectionTimeout: 10000,
    maxRetries: 3
  },
  cache: {
    ttl: 300,
    prefix: 'evernote:'
  },
  logging: {
    redactTokens: true
  }
};
```

```javascript
// config/development.js
module.exports = {
  evernote: {
    sandbox: true,
    serviceHost: 'sandbox.evernote.com',
    // More lenient for debugging
    requestTimeout: 60000,
    maxRetries: 1
  },
  cache: {
    ttl: 60, // Short TTL for development
    prefix: 'evernote:dev:'
  },
  logging: {
    level: 'debug'
  }
};
```

```javascript
// config/staging.js
module.exports = {
  evernote: {
    sandbox: true, // Still using sandbox for staging
    serviceHost: 'sandbox.evernote.com',
    requestTimeout: 30000,
    maxRetries: 2
  },
  cache: {
    ttl: 180,
    prefix: 'evernote:staging:'
  },
  logging: {
    level: 'info'
  }
};
```

```javascript
// config/production.js
module.exports = {
  evernote: {
    sandbox: false, // Production mode
    serviceHost: 'www.evernote.com',
    requestTimeout: 30000,
    maxRetries: 3
  },
  cache: {
    ttl: 300,
    prefix: 'evernote:prod:'
  },
  logging: {
    level: 'warn'
  }
};
```

### Step 2: Environment Variables

```bash
NODE_ENV=development

EVERNOTE_CONSUMER_KEY=
EVERNOTE_CONSUMER_SECRET=
EVERNOTE_SANDBOX=true

APP_URL=http://localhost:3000
SESSION_SECRET=change-this-secret

DATABASE_URL=

REDIS_URL=
```

```bash
NODE_ENV=development
EVERNOTE_CONSUMER_KEY=your-sandbox-key
EVERNOTE_CONSUMER_SECRET=your-sandbox-secret
EVERNOTE_SANDBOX=true
APP_URL=http://localhost:3000
SESSION_SECRET=dev-secret-not-secure
DATABASE_URL=postgresql://localhost:5432/evernote_dev
REDIS_URL=redis://localhost:6379/0
```

```bash
NODE_ENV=staging
EVERNOTE_CONSUMER_KEY=your-sandbox-key
EVERNOTE_CONSUMER_SECRET=your-sandbox-secret
EVERNOTE_SANDBOX=true
APP_URL=https://staging.yourapp.com
```

```bash
NODE_ENV=production
EVERNOTE_SANDBOX=false
APP_URL=https://yourapp.com
```

### Step 3: Configuration Loader

```javascript
// config/index.js
const path = require('path');
const deepMerge = require('lodash.merge');

class ConfigLoader {
  constructor() {
    this.env = process.env.NODE_ENV || 'development';
    this.config = this.loadConfig();
  }

  loadConfig() {
    // Load default config
    const defaultConfig = require('./default');

    // Load environment-specific config
    let envConfig = {};
    try {
      envConfig = require(`./${this.env}`);
    } catch (error) {
      console.warn(`No config file for environment: ${this.env}`);
    }

    // Merge configs
    const merged = deepMerge({}, defaultConfig, envConfig);

    // Override with environment variables
    return this.applyEnvOverrides(merged);
  }

  applyEnvOverrides(config) {
    // Evernote overrides
    if (process.env.EVERNOTE_CONSUMER_KEY) {
      config.evernote.consumerKey = process.env.EVERNOTE_CONSUMER_KEY;
    }
    if (process.env.EVERNOTE_CONSUMER_SECRET) {
      config.evernote.consumerSecret = process.env.EVERNOTE_CONSUMER_SECRET;
    }
    if (process.env.EVERNOTE_SANDBOX !== undefined) {
      config.evernote.sandbox = process.env.EVERNOTE_SANDBOX === 'true';
    }

    // App overrides
    if (process.env.APP_URL) {
      config.app = config.app || {};
      config.app.url = process.env.APP_URL;
    }

    // Database overrides
    if (process.env.DATABASE_URL) {
      config.database = config.database || {};
      config.database.url = process.env.DATABASE_URL;
    }

    // Redis overrides
    if (process.env.REDIS_URL) {
      config.redis = config.redis || {};
      config.redis.url = process.env.REDIS_URL;
    }

    return config;
  }

  get(key) {
    const keys = key.split('.');
    let value = this.config;

    for (const k of keys) {
      if (value === undefined) return undefined;
      value = value[k];
    }

    return value;
  }

  getAll() {
    return this.config;
  }

  isProduction() {
    return this.env === 'production';
  }

  isDevelopment() {
    return this.env === 'development';
  }

  isStaging() {
    return this.env === 'staging';
  }
}

module.exports = new ConfigLoader();
```

### Step 4: Environment-Aware Client Factory

```javascript
// services/evernote-factory.js
const Evernote = require('evernote');
const config = require('../config');

class EvernoteClientFactory {
  static createOAuthClient() {
    return new Evernote.Client({
      consumerKey: config.get('evernote.consumerKey'),
      consumerSecret: config.get('evernote.consumerSecret'),
      sandbox: config.get('evernote.sandbox'),
      china: false
    });
  }

  static createAuthenticatedClient(accessToken) {
    return new Evernote.Client({
      token: accessToken,
      sandbox: config.get('evernote.sandbox')
    });
  }

  static getEnvironmentInfo() {
    return {
      environment: process.env.NODE_ENV,
      sandbox: config.get('evernote.sandbox'),
      serviceHost: config.get('evernote.sandbox')
        ? 'sandbox.evernote.com'
        : 'www.evernote.com'
    };
  }

  static validateEnvironment() {
    const errors = [];

    if (!config.get('evernote.consumerKey')) {
      errors.push('Missing EVERNOTE_CONSUMER_KEY');
    }

    if (!config.get('evernote.consumerSecret')) {
      errors.push('Missing EVERNOTE_CONSUMER_SECRET');
    }

    if (config.isProduction() && config.get('evernote.sandbox')) {
      errors.push('Production environment cannot use sandbox mode');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
}

module.exports = EvernoteClientFactory;
```

### Step 5: Docker Compose for Local Development

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
    env_file:
      - .env.development
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: evernote_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Step 6: Environment-Specific Middleware

```javascript
// middleware/environment.js
const config = require('../config');

function environmentMiddleware(req, res, next) {
  // Add environment info to request
  req.environment = {
    name: process.env.NODE_ENV,
    sandbox: config.get('evernote.sandbox'),
    isProduction: config.isProduction()
  };

  // Development-only features
  if (config.isDevelopment()) {
    // Add debug headers
    res.setHeader('X-Environment', 'development');
    res.setHeader('X-Evernote-Mode', 'sandbox');
  }

  // Production safety checks
  if (config.isProduction()) {
    // Ensure HTTPS
    if (req.protocol !== 'https') {
      return res.redirect(301, `https://${req.hostname}${req.url}`);
    }
  }

  next();
}

function requireProduction(req, res, next) {
  if (!config.isProduction()) {
    return res.status(403).json({
      error: 'This endpoint is only available in production'
    });
  }
  next();
}

function blockInProduction(req, res, next) {
  if (config.isProduction()) {
    return res.status(403).json({
      error: 'This endpoint is not available in production'
    });
  }
  next();
}

module.exports = {
  environmentMiddleware,
  requireProduction,
  blockInProduction
};
```

### Step 7: CI/CD Environment Configuration

```yaml
name: Deploy

on:
  push:
    branches: [main, develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - branch: develop
            environment: staging
            evernote_sandbox: 'true'
          - branch: main
            environment: production
            evernote_sandbox: 'false'

    steps:
      - uses: actions/checkout@v4

      - name: Set environment
        if: github.ref == format('refs/heads/{0}', matrix.branch)
        run: echo "DEPLOY_ENV=${{ matrix.environment }}" >> $GITHUB_ENV

      - name: Deploy to ${{ matrix.environment }}
        if: env.DEPLOY_ENV != ''
        uses: ./.github/actions/deploy
        with:
          environment: ${{ matrix.environment }}
        env:
          EVERNOTE_CONSUMER_KEY: ${{ secrets[format('EVERNOTE_CONSUMER_KEY_{0}', matrix.environment)] }}
          EVERNOTE_CONSUMER_SECRET: ${{ secrets[format('EVERNOTE_CONSUMER_SECRET_{0}', matrix.environment)] }}
          EVERNOTE_SANDBOX: ${{ matrix.evernote_sandbox }}
```

### Step 8: Environment Health Check

```javascript
// routes/health.js
const config = require('../config');
const EvernoteClientFactory = require('../services/evernote-factory');

router.get('/health/environment', async (req, res) => {
  const envInfo = EvernoteClientFactory.getEnvironmentInfo();
  const validation = EvernoteClientFactory.validateEnvironment();

  res.json({
    status: validation.valid ? 'ok' : 'error',
    environment: {
      ...envInfo,
      nodeEnv: process.env.NODE_ENV,
      version: process.env.APP_VERSION || 'unknown'
    },
    validation,
    checks: {
      database: await checkDatabase(),
      redis: await checkRedis(),
      evernote: await checkEvernoteConnectivity()
    }
  });
});

async function checkEvernoteConnectivity() {
  try {
    // Simple connectivity check - doesn't require auth
    const https = require('https');
    const host = config.get('evernote.sandbox')
      ? 'sandbox.evernote.com'
      : 'www.evernote.com';

    return new Promise((resolve) => {
      const req = https.get(`https://${host}`, { timeout: 5000 }, (res) => {
        resolve({ status: 'ok', host });
      });

      req.on('error', () => {
        resolve({ status: 'error', host, message: 'Connection failed' });
      });

      req.on('timeout', () => {
        req.destroy();
        resolve({ status: 'error', host, message: 'Timeout' });
      });
    });
  } catch (error) {
    return { status: 'error', message: error.message };
  }
}
```


## Environment Strategy

| Environment | Evernote Mode | Purpose | Users |
|-------------|---------------|---------|-------|
| Development | Sandbox | Local development | Developers |
| Staging | Sandbox | Integration testing | QA team |
| Production | Production | Live users | Customers |


## Environment Checklist

```markdown


## Per-Environment Checklist

### Development
- [ ] Sandbox credentials configured
- [ ] Local database running
- [ ] Redis cache running
- [ ] Debug logging enabled

### Staging
- [ ] Sandbox credentials (separate from dev)
- [ ] Staging database provisioned
- [ ] Staging Redis provisioned
- [ ] Monitoring configured

### Production
- [ ] Production API key approved
- [ ] Secrets in secure storage
- [ ] Production database provisioned
- [ ] Production Redis provisioned
- [ ] Monitoring and alerting
- [ ] Backup procedures
```
