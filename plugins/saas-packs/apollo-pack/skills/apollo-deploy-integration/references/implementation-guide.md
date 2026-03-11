# Apollo Deploy Integration - Implementation Guide

> Full implementation details and code examples for the `apollo-deploy-integration` skill.

# Apollo Deploy Integration

## Overview
Deploy Apollo.io integrations to production environments with proper configuration, health checks, and rollback procedures.

## Deployment Platforms

### Vercel Deployment
```json
// vercel.json
{
  "env": {
    "APOLLO_API_KEY": "@apollo-api-key"
  },
  "build": {
    "env": {
      "APOLLO_API_KEY": "@apollo-api-key"
    }
  }
}
```

```bash
# Add secret to Vercel
vercel secrets add apollo-api-key "your-api-key"

# Deploy
vercel --prod
```

### Google Cloud Run
```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/apollo-service', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/apollo-service']

  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'apollo-service'
      - '--image=gcr.io/$PROJECT_ID/apollo-service'
      - '--platform=managed'
      - '--region=us-central1'
      - '--set-secrets=APOLLO_API_KEY=apollo-api-key:latest'
      - '--allow-unauthenticated'
```

```bash
# Create secret in Google Cloud
gcloud secrets create apollo-api-key --data-file=-
echo -n "your-api-key" | gcloud secrets versions add apollo-api-key --data-file=-

# Grant access to Cloud Run
gcloud secrets add-iam-policy-binding apollo-api-key \
  --member="serviceAccount:YOUR-SA@PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### AWS Lambda
```yaml
# serverless.yml
service: apollo-integration

provider:
  name: aws
  runtime: nodejs20.x
  region: us-east-1
  environment:
    APOLLO_API_KEY: ${ssm:/apollo/api-key~true}

functions:
  search:
    handler: src/handlers/search.handler
    events:
      - http:
          path: /api/apollo/search
          method: post
    timeout: 30

  enrich:
    handler: src/handlers/enrich.handler
    events:
      - http:
          path: /api/apollo/enrich
          method: get
    timeout: 30
```

```bash
# Store secret in SSM
aws ssm put-parameter \
  --name "/apollo/api-key" \
  --type "SecureString" \
  --value "your-api-key"

# Deploy
serverless deploy --stage production
```

### Kubernetes
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apollo-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: apollo-service
  template:
    metadata:
      labels:
        app: apollo-service
    spec:
      containers:
        - name: apollo-service
          image: your-registry/apollo-service:latest
          ports:
            - containerPort: 3000
          env:
            - name: APOLLO_API_KEY
              valueFrom:
                secretKeyRef:
                  name: apollo-secrets
                  key: api-key
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/apollo
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
---
apiVersion: v1
kind: Secret
metadata:
  name: apollo-secrets
type: Opaque
stringData:
  api-key: your-api-key  # Use sealed-secrets in production
```

## Health Check Endpoints

```typescript
// src/routes/health.ts
import { Router } from 'express';
import { apollo } from '../lib/apollo/client';

const router = Router();

// Basic health check
router.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Apollo-specific health check
router.get('/health/apollo', async (req, res) => {
  try {
    const start = Date.now();
    await apollo.healthCheck();
    const latency = Date.now() - start;

    res.json({
      status: 'ok',
      apollo: {
        connected: true,
        latencyMs: latency,
      },
    });
  } catch (error: any) {
    res.status(503).json({
      status: 'degraded',
      apollo: {
        connected: false,
        error: error.message,
      },
    });
  }
});

// Readiness check (for Kubernetes)
router.get('/ready', async (req, res) => {
  try {
    await apollo.healthCheck();
    res.json({ ready: true });
  } catch {
    res.status(503).json({ ready: false });
  }
});

export default router;
```

## Blue-Green Deployment

```yaml
# .github/workflows/blue-green.yml
name: Blue-Green Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Green
        run: |
          kubectl apply -f k8s/deployment-green.yaml
          kubectl rollout status deployment/apollo-service-green

      - name: Run smoke tests on Green
        run: |
          GREEN_URL=$(kubectl get svc apollo-service-green -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
          curl -sf "http://$GREEN_URL/health/apollo" || exit 1

      - name: Switch traffic to Green
        if: success()
        run: |
          kubectl patch service apollo-service -p '{"spec":{"selector":{"version":"green"}}}'

      - name: Rollback on failure
        if: failure()
        run: |
          kubectl patch service apollo-service -p '{"spec":{"selector":{"version":"blue"}}}'
```

## Deployment Checklist

```typescript
// scripts/pre-deploy-check.ts
import { apollo } from '../src/lib/apollo/client';

interface Check {
  name: string;
  check: () => Promise<boolean>;
  required: boolean;
}

const checks: Check[] = [
  {
    name: 'API Key Valid',
    check: async () => {
      try {
        await apollo.healthCheck();
        return true;
      } catch {
        return false;
      }
    },
    required: true,
  },
  {
    name: 'Rate Limit Available',
    check: async () => {
      // Check we have rate limit headroom
      const response = await apollo.searchPeople({ per_page: 1 });
      return true; // If we got here, we have capacity
    },
    required: false,
  },
  {
    name: 'Search Working',
    check: async () => {
      const result = await apollo.searchPeople({
        q_organization_domains: ['apollo.io'],
        per_page: 1,
      });
      return result.people.length > 0;
    },
    required: true,
  },
];

async function runChecks() {
  console.log('Running pre-deployment checks...\n');

  let allPassed = true;

  for (const { name, check, required } of checks) {
    try {
      const passed = await check();
      const status = passed ? 'PASS' : required ? 'FAIL' : 'WARN';
      console.log(`[${status}] ${name}`);

      if (!passed && required) {
        allPassed = false;
      }
    } catch (error: any) {
      console.log(`[FAIL] ${name}: ${error.message}`);
      if (required) {
        allPassed = false;
      }
    }
  }

  if (!allPassed) {
    console.error('\nPre-deployment checks failed. Aborting.');
    process.exit(1);
  }

  console.log('\nAll checks passed. Ready to deploy.');
}

runChecks();
```

## Environment Configuration

```typescript
// src/config/environments.ts
interface EnvironmentConfig {
  apollo: {
    apiKey: string;
    rateLimit: number;
    timeout: number;
  };
  features: {
    enrichment: boolean;
    sequences: boolean;
  };
}

const configs: Record<string, EnvironmentConfig> = {
  development: {
    apollo: {
      apiKey: process.env.APOLLO_API_KEY_DEV!,
      rateLimit: 10,
      timeout: 30000,
    },
    features: {
      enrichment: true,
      sequences: false,
    },
  },
  staging: {
    apollo: {
      apiKey: process.env.APOLLO_API_KEY_STAGING!,
      rateLimit: 50,
      timeout: 30000,
    },
    features: {
      enrichment: true,
      sequences: true,
    },
  },
  production: {
    apollo: {
      apiKey: process.env.APOLLO_API_KEY!,
      rateLimit: 90,
      timeout: 30000,
    },
    features: {
      enrichment: true,
      sequences: true,
    },
  },
};

export function getConfig(): EnvironmentConfig {
  const env = process.env.NODE_ENV || 'development';
  return configs[env] || configs.development;
}
```

## Output
- Platform-specific deployment configs (Vercel, GCP, AWS, K8s)
- Health check endpoints
- Blue-green deployment workflow
- Pre-deployment validation
- Environment configuration

## Error Handling
| Issue | Resolution |
|-------|------------|
| Secret not found | Verify secret configuration |
| Health check fails | Check Apollo connectivity |
| Deployment timeout | Increase timeout, check resources |
| Traffic not switching | Verify service selector |

## Resources
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager)
- [AWS Systems Manager](https://docs.aws.amazon.com/systems-manager/)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

## Next Steps
Proceed to `apollo-webhooks-events` for webhook implementation.
