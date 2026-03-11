# Guidewire Multi-Environment Setup — Implementation Guide

## Environment Topology

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Environment Landscape                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐              │
│  │    DEV    │───▶│    QA     │───▶│    UAT    │───▶│   PROD    │              │
│  │ Feature   │    │ Integration│   │ Acceptance│    │ Production│              │
│  │ Development│   │ Testing   │    │ Testing   │    │           │              │
│  └───────────┘    └───────────┘    └───────────┘    └───────────┘              │
│       │                │                │                │                      │
│       ▼                ▼                ▼                ▼                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    Shared Infrastructure                                 │   │
│  │  • Identity Provider (Guidewire Hub)                                    │   │
│  │  • Document Storage                                                      │   │
│  │  • Monitoring/Logging                                                    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Environment-Specific Properties

### Development

```properties
# config/environments/dev/env.properties
environment=development
environment.code=DEV
gw.tenant.id=your-tenant-dev
gw.hub.url=https://hub-dev.guidewire.com
gw.api.base.url=https://your-tenant-dev.cloud.guidewire.com

policycenter.url=${gw.api.base.url}/pc/rest
claimcenter.url=${gw.api.base.url}/cc/rest
billingcenter.url=${gw.api.base.url}/bc/rest

database.readonly.enabled=false
logging.level.root=DEBUG
logging.level.gw.api=DEBUG
logging.level.gw.custom=DEBUG

feature.debug.enabled=true
feature.sample.data.enabled=true
feature.mock.integrations=true

integration.rating.url=http://localhost:8081/mock/rating
integration.mvr.url=http://localhost:8081/mock/mvr
integration.credit.url=http://localhost:8081/mock/credit
```

### Production

```properties
# config/environments/prod/env.properties
environment=production
environment.code=PROD
gw.tenant.id=your-tenant-prod
gw.hub.url=https://hub.guidewire.com
gw.api.base.url=https://your-tenant.cloud.guidewire.com

policycenter.url=${gw.api.base.url}/pc/rest
claimcenter.url=${gw.api.base.url}/cc/rest
billingcenter.url=${gw.api.base.url}/bc/rest

database.readonly.enabled=false
logging.level.root=WARN
logging.level.gw.api=INFO
logging.level.gw.custom=INFO

feature.debug.enabled=false
feature.sample.data.enabled=false
feature.mock.integrations=false

integration.rating.url=https://rating.production.com/api
integration.mvr.url=https://mvr.production.com/api
integration.credit.url=https://credit.production.com/api
```

## Gradle Environment Configuration

```groovy
// build.gradle
plugins {
    id 'com.guidewire.gradle' version '10.12.0'
}

ext {
    environment = project.findProperty('env') ?: 'dev'
    envConfigDir = file("config/environments/${environment}")
}

def loadEnvProperties() {
    def props = new Properties()
    file('config/environments/base').eachFile { f ->
        if (f.name.endsWith('.properties')) {
            props.load(f.newReader())
        }
    }
    envConfigDir.eachFile { f ->
        if (f.name.endsWith('.properties')) {
            props.load(f.newReader())
        }
    }
    return props
}

ext.envProps = loadEnvProperties()

guidewire {
    server {
        environment = project.ext.environment
        properties = project.ext.envProps
    }
}

['dev', 'qa', 'uat', 'prod'].each { env ->
    tasks.register("deploy${env.capitalize()}") {
        description = "Deploy to ${env} environment"
        group = 'deployment'
        doLast {
            println "Deploying to ${env}..."
        }
    }
}

tasks.register('validateEnvConfig') {
    description = 'Validate environment configuration'
    doLast {
        def requiredProps = ['gw.tenant.id', 'gw.hub.url', 'gw.api.base.url']
        requiredProps.each { prop ->
            if (!project.ext.envProps.containsKey(prop)) {
                throw new GradleException("Missing required property: ${prop}")
            }
        }
        println "Environment configuration valid for: ${project.ext.environment}"
    }
}
```

## TypeScript Environment Manager

```typescript
interface EnvironmentConfig {
  name: string;
  code: string;
  tenantId: string;
  hubUrl: string;
  apiBaseUrl: string;
  features: Record<string, boolean>;
  integrations: Record<string, string>;
}

class EnvironmentManager {
  private configs: Map<string, EnvironmentConfig> = new Map();

  constructor() {
    this.loadConfigurations();
  }

  private loadConfigurations(): void {
    this.configs.set('dev', {
      name: 'Development',
      code: 'DEV',
      tenantId: process.env.GW_TENANT_DEV!,
      hubUrl: 'https://hub-dev.guidewire.com',
      apiBaseUrl: `https://${process.env.GW_TENANT_DEV}.cloud.guidewire.com`,
      features: { debug: true, sampleData: true, mockIntegrations: true },
      integrations: {
        rating: 'http://localhost:8081/mock/rating',
        mvr: 'http://localhost:8081/mock/mvr'
      }
    });

    this.configs.set('prod', {
      name: 'Production',
      code: 'PROD',
      tenantId: process.env.GW_TENANT_PROD!,
      hubUrl: 'https://hub.guidewire.com',
      apiBaseUrl: `https://${process.env.GW_TENANT_PROD}.cloud.guidewire.com`,
      features: { debug: false, sampleData: false, mockIntegrations: false },
      integrations: {
        rating: 'https://rating.production.com/api',
        mvr: 'https://mvr.production.com/api'
      }
    });
  }

  getConfig(env: string): EnvironmentConfig {
    const config = this.configs.get(env);
    if (!config) throw new Error(`Unknown environment: ${env}`);
    return config;
  }

  getCurrentEnvironment(): string {
    return process.env.GW_ENVIRONMENT || 'dev';
  }

  isFeatureEnabled(feature: string): boolean {
    const config = this.getConfig(this.getCurrentEnvironment());
    return config.features[feature] ?? false;
  }
}
```

## Environment-Aware API Client

```typescript
class EnvironmentAwareClient {
  private envManager: EnvironmentManager;
  private tokenManager: TokenManager;

  constructor() {
    this.envManager = new EnvironmentManager();
    const config = this.envManager.getConfig(this.envManager.getCurrentEnvironment());

    this.tokenManager = new TokenManager({
      clientId: this.getClientId(),
      clientSecret: this.getClientSecret(),
      hubUrl: config.hubUrl
    });
  }

  private getClientId(): string {
    const env = this.envManager.getCurrentEnvironment();
    return process.env[`GW_CLIENT_ID_${env.toUpperCase()}`]!;
  }

  private getClientSecret(): string {
    const env = this.envManager.getCurrentEnvironment();
    return process.env[`GW_CLIENT_SECRET_${env.toUpperCase()}`]!;
  }

  async request<T>(path: string, options?: RequestOptions): Promise<T> {
    const config = this.envManager.getConfig(this.envManager.getCurrentEnvironment());
    const token = await this.tokenManager.getToken();

    const response = await fetch(`${config.apiBaseUrl}${path}`, {
      ...options,
      headers: {
        ...options?.headers,
        'Authorization': `Bearer ${token}`,
        'X-GW-Environment': config.code
      }
    });

    return response.json();
  }
}
```

## Secrets Management

```typescript
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

interface EnvironmentSecrets {
  clientId: string;
  clientSecret: string;
  webhookSecret: string;
  encryptionKey: string;
}

class SecretsManager {
  private client: SecretManagerServiceClient;
  private projectId: string;

  constructor(projectId: string) {
    this.client = new SecretManagerServiceClient();
    this.projectId = projectId;
  }

  async getSecrets(environment: string): Promise<EnvironmentSecrets> {
    const prefix = `gw-${environment}`;
    const [clientId, clientSecret, webhookSecret, encryptionKey] = await Promise.all([
      this.getSecret(`${prefix}-client-id`),
      this.getSecret(`${prefix}-client-secret`),
      this.getSecret(`${prefix}-webhook-secret`),
      this.getSecret(`${prefix}-encryption-key`)
    ]);
    return { clientId, clientSecret, webhookSecret, encryptionKey };
  }

  private async getSecret(secretName: string): Promise<string> {
    const name = `projects/${this.projectId}/secrets/${secretName}/versions/latest`;
    const [response] = await this.client.accessSecretVersion({ name });
    return response.payload?.data?.toString() || '';
  }

  async rotateSecret(environment: string, secretName: string, newValue: string): Promise<void> {
    const fullName = `gw-${environment}-${secretName}`;
    const parent = `projects/${this.projectId}/secrets/${fullName}`;
    await this.client.addSecretVersion({
      parent,
      payload: { data: Buffer.from(newValue) }
    });
    console.log(`Rotated secret: ${fullName}`);
  }
}
```

## Environment Promotion Workflow

```typescript
interface PromotionRequest {
  sourceEnv: string;
  targetEnv: string;
  packageVersion: string;
  approver: string;
  changeTicket: string;
}

class EnvironmentPromotion {
  private allowedPromotionPaths = [
    ['dev', 'qa'], ['qa', 'uat'], ['uat', 'prod']
  ];

  async promote(request: PromotionRequest): Promise<PromotionResult> {
    this.validatePromotionPath(request.sourceEnv, request.targetEnv);
    await this.runPrePromotionChecks(request);

    const package = await this.getPackageFromEnvironment(request.sourceEnv, request.packageVersion);
    const deploymentId = await this.deployToEnvironment(request.targetEnv, package);
    await this.waitForDeployment(deploymentId);
    await this.runPostPromotionValidation(request.targetEnv);

    return await this.recordPromotion(request, deploymentId);
  }

  private validatePromotionPath(source: string, target: string): void {
    const isValid = this.allowedPromotionPaths.some(
      ([from, to]) => from === source && to === target
    );
    if (!isValid) throw new Error(`Invalid promotion path: ${source} -> ${target}`);
  }

  private async runPrePromotionChecks(request: PromotionRequest): Promise<void> {
    if (request.targetEnv === 'prod') {
      const ticketApproved = await this.checkChangeTicketApproved(request.changeTicket);
      if (!ticketApproved) throw new Error('Change ticket not approved for production promotion');
    }

    const sourceHealth = await this.checkEnvironmentHealth(request.sourceEnv);
    if (!sourceHealth.healthy) throw new Error(`Source environment unhealthy: ${sourceHealth.issues.join(', ')}`);

    const targetAvailable = await this.checkEnvironmentAvailable(request.targetEnv);
    if (!targetAvailable) throw new Error('Target environment not available for deployment');
  }

  private async runPostPromotionValidation(environment: string): Promise<void> {
    const smokeResults = await this.runSmokeTests(environment);
    if (!smokeResults.passed) throw new Error(`Smoke tests failed: ${smokeResults.failures.join(', ')}`);

    const integrationResults = await this.verifyIntegrations(environment);
    if (!integrationResults.allHealthy) {
      console.warn('Some integrations unhealthy:', integrationResults.unhealthy);
    }
  }
}
```

## Environment Health Dashboard

```typescript
interface EnvironmentHealth {
  environment: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: ComponentHealth[];
  lastUpdated: Date;
}

interface ComponentHealth {
  name: string;
  status: 'up' | 'down' | 'degraded';
  latency?: number;
  errorRate?: number;
}

class EnvironmentHealthMonitor {
  private environments = ['dev', 'qa', 'uat', 'prod'];

  async checkAllEnvironments(): Promise<Map<string, EnvironmentHealth>> {
    const results = new Map<string, EnvironmentHealth>();
    await Promise.all(
      this.environments.map(async (env) => {
        const health = await this.checkEnvironment(env);
        results.set(env, health);
      })
    );
    return results;
  }

  async checkEnvironment(env: string): Promise<EnvironmentHealth> {
    const envManager = new EnvironmentManager();
    const config = envManager.getConfig(env);

    const components = await Promise.all([
      this.checkPolicyCenter(config),
      this.checkClaimCenter(config),
      this.checkBillingCenter(config),
      this.checkIntegrations(config)
    ]);

    const unhealthyCount = components.filter(c => c.status === 'down').length;
    const degradedCount = components.filter(c => c.status === 'degraded').length;

    let status: EnvironmentHealth['status'] = 'healthy';
    if (unhealthyCount > 0) status = 'unhealthy';
    else if (degradedCount > 0) status = 'degraded';

    return { environment: env, status, components, lastUpdated: new Date() };
  }

  private async checkPolicyCenter(config: EnvironmentConfig): Promise<ComponentHealth> {
    const startTime = Date.now();
    try {
      const response = await fetch(`${config.apiBaseUrl}/pc/rest/common/v1/system-info`);
      return {
        name: 'PolicyCenter',
        status: response.ok ? 'up' : 'degraded',
        latency: Date.now() - startTime
      };
    } catch {
      return { name: 'PolicyCenter', status: 'down' };
    }
  }
}
```
