# Guidewire Deploy Integration - Implementation Guide

## Deployment Architecture

```
+------------------+      +------------------+      +------------------+
|                  |      |                  |      |                  |
|   Development    |----->|    Sandbox       |----->|   Production     |
|   Environment    |      |    Environment   |      |   Environment    |
|                  |      |                  |      |                  |
+------------------+      +------------------+      +------------------+
        |                         |                         |
        v                         v                         v
   Build Package            Deploy & Test             Deploy & Verify
   Run Unit Tests           Integration Tests         Production Tests
   Code Review              UAT Approval              Go-Live Approval
```

## Instructions

### Step 1: Prepare Configuration Package

```groovy
// build.gradle - Configuration package creation
tasks.register('createConfigPackage', Zip) {
    description = 'Creates configuration package for Guidewire Cloud deployment'
    group = 'deployment'

    archiveFileName = "config-${project.version}-${new Date().format('yyyyMMddHHmmss')}.zip"
    destinationDirectory = file("$buildDir/packages")

    from('modules/configuration') {
        include 'gsrc/**'
        include 'config/**'
        exclude '**/*.swp'
        exclude '**/test/**'
    }

    from('modules/integration') {
        include 'gsrc/**'
        exclude '**/*Test.gs'
    }

    // Include metadata
    from('.') {
        include 'version.properties'
        include 'deployment-manifest.json'
    }
}

tasks.register('validatePackage') {
    description = 'Validates configuration package before deployment'
    dependsOn 'createConfigPackage'

    doLast {
        def packageFile = file("$buildDir/packages").listFiles().find { it.name.endsWith('.zip') }

        // Validate package size
        def sizeMB = packageFile.length() / (1024 * 1024)
        if (sizeMB > 100) {
            throw new GradleException("Package too large: ${sizeMB}MB (max 100MB)")
        }

        // Validate required files
        def zipFile = new java.util.zip.ZipFile(packageFile)
        def requiredFiles = ['deployment-manifest.json', 'version.properties']
        requiredFiles.each { required ->
            if (!zipFile.entries().any { it.name == required }) {
                throw new GradleException("Missing required file: ${required}")
            }
        }
        zipFile.close()

        println "Package validation passed: ${packageFile.name} (${sizeMB}MB)"
    }
}
```

### Step 2: Deployment Manifest

```json
{
  "manifestVersion": "2.0",
  "packageInfo": {
    "name": "policycenter-custom-config",
    "version": "1.5.0",
    "description": "Custom PolicyCenter configuration with integration extensions",
    "buildNumber": "${BUILD_NUMBER}",
    "buildTimestamp": "${BUILD_TIMESTAMP}"
  },
  "targetApplications": [
    {
      "application": "PolicyCenter",
      "minimumVersion": "202503",
      "maximumVersion": "202507"
    }
  ],
  "components": [
    {
      "type": "gosu",
      "path": "gsrc/gw/custom/**",
      "description": "Custom Gosu business logic"
    },
    {
      "type": "pcf",
      "path": "config/pcf/**",
      "description": "Custom UI screens"
    },
    {
      "type": "product",
      "path": "config/products/**",
      "description": "Product model customizations"
    },
    {
      "type": "integration",
      "path": "config/integration/**",
      "description": "Integration configurations"
    }
  ],
  "preDeploymentChecks": [
    {
      "name": "database-compatibility",
      "type": "schema-validation"
    },
    {
      "name": "api-compatibility",
      "type": "api-version-check"
    }
  ],
  "postDeploymentActions": [
    {
      "name": "clear-cache",
      "type": "cache-invalidation"
    },
    {
      "name": "reload-products",
      "type": "product-reload"
    }
  ]
}
```

### Step 3: Deployment API Client

```typescript
// Guidewire Cloud Deployment Client
interface DeploymentStatus {
  id: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'ROLLED_BACK';
  startTime: string;
  endTime?: string;
  progress: number;
  message?: string;
  logs?: string[];
}

interface DeploymentRequest {
  environment: string;
  packagePath: string;
  rollbackOnFailure: boolean;
  validationMode?: 'STRICT' | 'LENIENT';
}

class GuidewireDeploymentClient {
  private baseUrl: string;
  private tokenManager: TokenManager;

  constructor(baseUrl: string, tokenManager: TokenManager) {
    this.baseUrl = baseUrl;
    this.tokenManager = tokenManager;
  }

  async deploy(request: DeploymentRequest): Promise<string> {
    const token = await this.tokenManager.getToken();

    // Upload package
    const packageBuffer = await fs.readFile(request.packagePath);
    const uploadResponse = await fetch(`${this.baseUrl}/deployment/v1/packages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/zip',
        'X-Environment': request.environment,
        'X-Rollback-On-Failure': String(request.rollbackOnFailure),
        'X-Validation-Mode': request.validationMode || 'STRICT'
      },
      body: packageBuffer
    });

    if (!uploadResponse.ok) {
      const error = await uploadResponse.json();
      throw new Error(`Deployment failed: ${error.message}`);
    }

    const result = await uploadResponse.json();
    return result.deploymentId;
  }

  async getStatus(deploymentId: string): Promise<DeploymentStatus> {
    const token = await this.tokenManager.getToken();

    const response = await fetch(
      `${this.baseUrl}/deployment/v1/deployments/${deploymentId}`,
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );

    return response.json();
  }

  async waitForCompletion(
    deploymentId: string,
    timeoutMs: number = 1800000,
    pollIntervalMs: number = 10000
  ): Promise<DeploymentStatus> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeoutMs) {
      const status = await this.getStatus(deploymentId);

      console.log(`Deployment ${deploymentId}: ${status.status} (${status.progress}%)`);

      if (status.status === 'COMPLETED') {
        return status;
      }

      if (status.status === 'FAILED' || status.status === 'ROLLED_BACK') {
        throw new Error(`Deployment failed: ${status.message}`);
      }

      await sleep(pollIntervalMs);
    }

    throw new Error(`Deployment timed out after ${timeoutMs}ms`);
  }

  async rollback(deploymentId: string): Promise<void> {
    const token = await this.tokenManager.getToken();

    const response = await fetch(
      `${this.baseUrl}/deployment/v1/deployments/${deploymentId}/rollback`,
      {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );

    if (!response.ok) {
      throw new Error('Rollback failed');
    }
  }
}
```

### Step 4: Blue-Green Deployment

```typescript
// Blue-Green deployment strategy
interface EnvironmentSlot {
  name: 'blue' | 'green';
  status: 'active' | 'standby';
  version: string;
  healthUrl: string;
}

class BlueGreenDeployment {
  private deploymentClient: GuidewireDeploymentClient;
  private loadBalancer: LoadBalancerClient;

  async deploy(packagePath: string): Promise<void> {
    // Step 1: Identify current active and standby slots
    const slots = await this.getSlotStatus();
    const activeSlot = slots.find(s => s.status === 'active')!;
    const standbySlot = slots.find(s => s.status === 'standby')!;

    console.log(`Current active: ${activeSlot.name} (${activeSlot.version})`);
    console.log(`Deploying to: ${standbySlot.name}`);

    // Step 2: Deploy to standby slot
    const deploymentId = await this.deploymentClient.deploy({
      environment: standbySlot.name,
      packagePath,
      rollbackOnFailure: true
    });

    await this.deploymentClient.waitForCompletion(deploymentId);

    // Step 3: Run health checks on standby
    const healthy = await this.runHealthChecks(standbySlot.healthUrl);
    if (!healthy) {
      throw new Error('Health checks failed on standby slot');
    }

    // Step 4: Run smoke tests
    const smokeTestsPassed = await this.runSmokeTests(standbySlot.name);
    if (!smokeTestsPassed) {
      throw new Error('Smoke tests failed');
    }

    // Step 5: Switch traffic
    console.log('Switching traffic to new deployment...');
    await this.loadBalancer.switchTraffic(standbySlot.name);

    // Step 6: Verify switch
    const newActive = await this.verifyActiveSlot();
    if (newActive !== standbySlot.name) {
      throw new Error('Traffic switch verification failed');
    }

    console.log(`Deployment complete. Active slot: ${standbySlot.name}`);
  }

  async rollback(): Promise<void> {
    const slots = await this.getSlotStatus();
    const standbySlot = slots.find(s => s.status === 'standby')!;

    console.log(`Rolling back to ${standbySlot.name}...`);
    await this.loadBalancer.switchTraffic(standbySlot.name);
    console.log('Rollback complete');
  }

  private async runHealthChecks(healthUrl: string): Promise<boolean> {
    for (let i = 0; i < 5; i++) {
      try {
        const response = await fetch(healthUrl);
        const health = await response.json();
        if (health.status === 'healthy') {
          return true;
        }
      } catch (error) {
        console.log(`Health check attempt ${i + 1} failed`);
      }
      await sleep(10000);
    }
    return false;
  }
}
```

### Step 5: Environment Promotion

```typescript
// Promote deployments between environments
interface PromotionRequest {
  sourceEnvironment: string;
  targetEnvironment: string;
  packageId: string;
  approver: string;
  changeTicket: string;
}

class EnvironmentPromotion {
  async promote(request: PromotionRequest): Promise<string> {
    // Validate promotion path
    const validPaths = [
      ['dev', 'sandbox'],
      ['sandbox', 'staging'],
      ['staging', 'production']
    ];

    const isValidPath = validPaths.some(
      ([from, to]) => from === request.sourceEnvironment && to === request.targetEnvironment
    );

    if (!isValidPath) {
      throw new Error(`Invalid promotion path: ${request.sourceEnvironment} -> ${request.targetEnvironment}`);
    }

    // Verify package exists in source
    const sourcePackage = await this.getPackage(request.sourceEnvironment, request.packageId);
    if (!sourcePackage) {
      throw new Error('Package not found in source environment');
    }

    // Check prerequisites for target environment
    await this.checkPromotionPrerequisites(request);

    // Create promotion record
    const promotionId = await this.createPromotionRecord(request);

    // Execute deployment to target
    const deploymentId = await this.deploymentClient.deploy({
      environment: request.targetEnvironment,
      packagePath: sourcePackage.packagePath,
      rollbackOnFailure: true
    });

    // Wait for completion
    await this.deploymentClient.waitForCompletion(deploymentId);

    // Update promotion record
    await this.updatePromotionRecord(promotionId, 'COMPLETED');

    return promotionId;
  }

  private async checkPromotionPrerequisites(request: PromotionRequest): Promise<void> {
    // Check approval
    if (request.targetEnvironment === 'production') {
      const approval = await this.getApproval(request.changeTicket);
      if (!approval.approved) {
        throw new Error('Production deployment requires approval');
      }
    }

    // Check no active deployments
    const activeDeployments = await this.getActiveDeployments(request.targetEnvironment);
    if (activeDeployments.length > 0) {
      throw new Error('Another deployment is in progress');
    }

    // Check maintenance window (for production)
    if (request.targetEnvironment === 'production') {
      const inWindow = await this.isInMaintenanceWindow();
      if (!inWindow) {
        throw new Error('Production deployments only allowed during maintenance windows');
      }
    }
  }
}
```

### Step 6: Deployment Verification

```gosu
// Post-deployment verification tests
package gw.deployment.verify

uses gw.api.util.Logger
uses gw.api.database.Query

class DeploymentVerification {
  private static final var LOG = Logger.forCategory("DeploymentVerification")

  static function runVerification() : VerificationResult {
    var result = new VerificationResult()

    // Check database connectivity
    result.addCheck("Database", verifyDatabaseConnection())

    // Check product model loaded
    result.addCheck("ProductModel", verifyProductModel())

    // Check integrations configured
    result.addCheck("Integrations", verifyIntegrations())

    // Check custom Gosu classes loaded
    result.addCheck("CustomCode", verifyCustomCode())

    return result
  }

  private static function verifyDatabaseConnection() : boolean {
    try {
      var count = Query.make(Account).select().Count
      LOG.info("Database check passed: ${count} accounts found")
      return true
    } catch (e : Exception) {
      LOG.error("Database check failed", e)
      return false
    }
  }

  private static function verifyProductModel() : boolean {
    try {
      var products = gw.api.productmodel.ProductLookup.getAll()
      LOG.info("Product model check passed: ${products.Count} products loaded")
      return products.Count > 0
    } catch (e : Exception) {
      LOG.error("Product model check failed", e)
      return false
    }
  }

  private static function verifyIntegrations() : boolean {
    try {
      // Verify integration endpoints are configured
      var endpoints = IntegrationConfig.getAllEndpoints()
      LOG.info("Integration check passed: ${endpoints.Count} endpoints configured")
      return true
    } catch (e : Exception) {
      LOG.error("Integration check failed", e)
      return false
    }
  }

  private static function verifyCustomCode() : boolean {
    try {
      // Try to instantiate custom classes
      var instance = new gw.custom.MyCustomClass()
      LOG.info("Custom code check passed")
      return true
    } catch (e : Exception) {
      LOG.error("Custom code check failed", e)
      return false
    }
  }
}
```
