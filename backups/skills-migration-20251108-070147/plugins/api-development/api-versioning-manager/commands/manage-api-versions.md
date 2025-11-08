---
description: Manage API versions with proper migration strategies
shortcut: apiver
---

# Manage API Versions

Implement comprehensive API versioning strategies with backward compatibility, smooth migration paths, deprecation workflows, and automated compatibility testing to ensure seamless API evolution.

## When to Use This Command

Use `/manage-api-versions` when you need to:
- Introduce breaking changes without disrupting existing clients
- Support multiple API versions simultaneously
- Provide smooth migration paths for API consumers
- Implement deprecation strategies with clear timelines
- Maintain backward compatibility while innovating
- Comply with enterprise SLA requirements

DON'T use this when:
- Building internal-only APIs with controlled clients (coordinate directly)
- API is in early beta with no production users (iterate freely)
- Changes are purely additive and backward compatible (versioning unnecessary)

## Design Decisions

This command implements **URL Path Versioning + Accept Header** as the primary approach because:
- Most intuitive for developers (visible in URL)
- Easy to route and cache at infrastructure level
- Clear version separation in code organization
- Accept headers provide fine-grained control
- Works well with API gateways and CDNs
- Industry standard for REST APIs

**Alternative considered: Header-Only Versioning**
- Cleaner URLs
- More RESTful approach
- Harder to test and debug
- Recommended for purist REST APIs

**Alternative considered: Query Parameter Versioning**
- Easy to implement
- Optional versioning support
- Can pollute URL structure
- Recommended for simple versioning needs

## Prerequisites

Before running this command:
1. Define versioning strategy and policy
2. Identify breaking vs. non-breaking changes
3. Plan deprecation timeline (typically 6-12 months)
4. Set up monitoring for version usage
5. Prepare migration documentation

## Implementation Process

### Step 1: Choose Versioning Strategy
Select and implement the appropriate versioning mechanism for your API architecture.

### Step 2: Create Version Infrastructure
Set up routing, middleware, and transformers for multi-version support.

### Step 3: Implement Compatibility Layer
Build backward compatibility adapters and response transformers.

### Step 4: Add Deprecation Workflow
Implement deprecation notices, sunset headers, and migration tools.

### Step 5: Set Up Version Testing
Create comprehensive test suites covering all supported versions.

## Output Format

The command generates:
- `api/v1/` - Version 1 implementation
- `api/v2/` - Version 2 implementation
- `middleware/version-router.js` - Version routing logic
- `transformers/` - Version-specific data transformers
- `tests/compatibility/` - Cross-version compatibility tests
- `docs/migration-guide.md` - Version migration documentation

## Code Examples

### Example 1: Comprehensive URL Path Versioning System

```javascript
// middleware/version-router.js
const express = require('express');
const semver = require('semver');

class APIVersionManager {
  constructor(options = {}) {
    this.versions = new Map();
    this.defaultVersion = options.defaultVersion || 'v1';
    this.deprecationPolicy = options.deprecationPolicy || {
      warningPeriod: 90,  // days before sunset
      sunsetPeriod: 180   // days until removal
    };
    this.versionInfo = new Map();
  }

  registerVersion(version, router, metadata = {}) {
    this.versions.set(version, router);
    this.versionInfo.set(version, {
      releaseDate: metadata.releaseDate || new Date(),
      deprecatedDate: metadata.deprecatedDate,
      sunsetDate: metadata.sunsetDate,
      changes: metadata.changes || [],
      status: metadata.status || 'active' // active, deprecated, sunset
    });
  }

  createVersionMiddleware() {
    return (req, res, next) => {
      // Extract version from URL path
      const pathMatch = req.path.match(/^\/v(\d+(?:\.\d+)?)/);
      const version = pathMatch ? `v${pathMatch[1]}` : null;

      // Check Accept header for version preference
      const acceptHeader = req.headers.accept || '';
      const headerMatch = acceptHeader.match(/application\/vnd\.api\.v(\d+)/);
      const headerVersion = headerMatch ? `v${headerMatch[1]}` : null;

      // Determine final version (path takes precedence)
      const requestedVersion = version || headerVersion || this.defaultVersion;

      // Validate version exists
      if (!this.versions.has(requestedVersion)) {
        return res.status(400).json({
          error: 'Invalid API version',
          message: `Version ${requestedVersion} is not supported`,
          supportedVersions: Array.from(this.versions.keys()),
          latestVersion: this.getLatestVersion()
        });
      }

      // Check if version is deprecated or sunset
      const versionMeta = this.versionInfo.get(requestedVersion);

      if (versionMeta.status === 'sunset') {
        return res.status(410).json({
          error: 'API version sunset',
          message: `Version ${requestedVersion} is no longer available`,
          sunsetDate: versionMeta.sunsetDate,
          alternatives: this.getActiveVersions(),
          migrationGuide: `/docs/migration/${requestedVersion}`
        });
      }

      // Add version headers
      res.set({
        'API-Version': requestedVersion,
        'X-API-Version': requestedVersion
      });

      // Add deprecation headers if applicable
      if (versionMeta.status === 'deprecated') {
        const sunsetDate = versionMeta.sunsetDate || this.calculateSunsetDate(versionMeta.deprecatedDate);

        res.set({
          'Deprecation': 'true',
          'Sunset': sunsetDate.toUTCString(),
          'Link': `</docs/migration/${requestedVersion}>; rel="deprecation"`,
          'Warning': `299 - "Version ${requestedVersion} is deprecated and will be removed on ${sunsetDate.toDateString()}"`
        });

        // Add deprecation notice to response
        res.on('finish', () => {
          console.log(`Deprecated API version ${requestedVersion} called by ${req.ip}`);
        });
      }

      // Store version info in request
      req.apiVersion = requestedVersion;
      req.apiVersionInfo = versionMeta;

      // Route to version-specific handler
      const versionRouter = this.versions.get(requestedVersion);
      versionRouter(req, res, next);
    };
  }

  getLatestVersion() {
    const versions = Array.from(this.versions.keys());
    return versions.sort((a, b) => semver.rcompare(a.slice(1), b.slice(1)))[0];
  }

  getActiveVersions() {
    return Array.from(this.versionInfo.entries())
      .filter(([_, info]) => info.status === 'active')
      .map(([version, _]) => version);
  }

  calculateSunsetDate(deprecatedDate) {
    const sunset = new Date(deprecatedDate);
    sunset.setDate(sunset.getDate() + this.deprecationPolicy.sunsetPeriod);
    return sunset;
  }

  generateVersionReport() {
    const report = {
      current: this.getLatestVersion(),
      supported: [],
      deprecated: [],
      sunset: []
    };

    for (const [version, info] of this.versionInfo) {
      const versionData = {
        version,
        releaseDate: info.releaseDate,
        status: info.status
      };

      switch (info.status) {
        case 'active':
          report.supported.push(versionData);
          break;
        case 'deprecated':
          report.deprecated.push({
            ...versionData,
            sunsetDate: info.sunsetDate
          });
          break;
        case 'sunset':
          report.sunset.push({
            ...versionData,
            sunsetDate: info.sunsetDate
          });
          break;
      }
    }

    return report;
  }
}

// api/v1/routes.js - Version 1 Implementation
const v1Router = express.Router();

v1Router.get('/users', async (req, res) => {
  const users = await getUsersV1();

  // V1 response format
  res.json({
    data: users.map(user => ({
      id: user.id,
      name: user.name,
      email: user.email
      // V1 doesn't include profile field
    }))
  });
});

v1Router.get('/users/:id', async (req, res) => {
  const user = await getUserByIdV1(req.params.id);

  res.json({
    data: {
      id: user.id,
      name: user.name,
      email: user.email
    }
  });
});

// api/v2/routes.js - Version 2 Implementation
const v2Router = express.Router();

v2Router.get('/users', async (req, res) => {
  const users = await getUsersV2();

  // V2 response format with additional fields
  res.json({
    data: users.map(user => ({
      id: user.id,
      displayName: user.name, // Field renamed
      email: user.email,
      profile: {              // New nested object
        avatar: user.avatar,
        bio: user.bio,
        createdAt: user.createdAt
      }
    })),
    meta: {                   // New metadata section
      total: users.length,
      version: 'v2'
    }
  });
});

// transformers/v1-to-v2.js - Backward Compatibility Transformer
class V1ToV2Transformer {
  transformUserResponse(v2Response) {
    // Transform V2 response to V1 format
    if (Array.isArray(v2Response.data)) {
      return {
        data: v2Response.data.map(user => ({
          id: user.id,
          name: user.displayName,  // Map back to old field name
          email: user.email
          // Omit profile field for V1
        }))
      };
    }

    return {
      data: {
        id: v2Response.data.id,
        name: v2Response.data.displayName,
        email: v2Response.data.email
      }
    };
  }

  transformUserRequest(v1Request) {
    // Transform V1 request to V2 format
    return {
      ...v1Request,
      displayName: v1Request.name,
      profile: {
        // Set defaults for new required fields
        avatar: null,
        bio: '',
        createdAt: new Date().toISOString()
      }
    };
  }
}

// Usage
const versionManager = new APIVersionManager({
  defaultVersion: 'v2',
  deprecationPolicy: {
    warningPeriod: 90,
    sunsetPeriod: 180
  }
});

// Register versions
versionManager.registerVersion('v1', v1Router, {
  releaseDate: new Date('2023-01-01'),
  deprecatedDate: new Date('2024-06-01'),
  status: 'deprecated',
  changes: ['Initial API release']
});

versionManager.registerVersion('v2', v2Router, {
  releaseDate: new Date('2024-01-01'),
  status: 'active',
  changes: [
    'Renamed user.name to user.displayName',
    'Added user.profile nested object',
    'Added metadata to list responses'
  ]
});

// Apply versioning middleware
app.use('/api', versionManager.createVersionMiddleware());

// Version discovery endpoint
app.get('/api/versions', (req, res) => {
  res.json(versionManager.generateVersionReport());
});
```

### Example 2: Advanced Content Negotiation Versioning

```javascript
// middleware/content-negotiation.js
const accepts = require('accepts');

class ContentNegotiationVersioning {
  constructor() {
    this.handlers = new Map();
    this.transformers = new Map();
  }

  register(version, mediaType, handler, transformer = null) {
    const key = `${version}:${mediaType}`;
    this.handlers.set(key, handler);

    if (transformer) {
      this.transformers.set(key, transformer);
    }
  }

  negotiate() {
    return async (req, res, next) => {
      const accept = accepts(req);

      // Define supported media types with versions
      const supportedTypes = [
        'application/vnd.api.v3+json',
        'application/vnd.api.v2+json',
        'application/vnd.api.v1+json',
        'application/json' // Default fallback
      ];

      const acceptedType = accept.type(supportedTypes);

      if (!acceptedType) {
        return res.status(406).json({
          error: 'Not Acceptable',
          message: 'None of the requested media types are supported',
          supported: supportedTypes
        });
      }

      // Extract version from media type
      let version = 'v2'; // Default version
      let format = 'json';

      const versionMatch = acceptedType.match(/v(\d+)/);
      if (versionMatch) {
        version = `v${versionMatch[1]}`;
      }

      const formatMatch = acceptedType.match(/\+(\w+)$/);
      if (formatMatch) {
        format = formatMatch[1];
      }

      // Set request properties
      req.apiVersion = version;
      req.responseFormat = format;

      // Override res.json to apply version transformations
      const originalJson = res.json.bind(res);

      res.json = function(data) {
        // Apply version-specific transformations
        const transformerKey = `${version}:${format}`;
        const transformer = this.transformers.get(transformerKey);

        if (transformer) {
          data = transformer(data, req);
        }

        // Set content type header
        res.type(acceptedType);

        // Add version headers
        res.set({
          'Content-Type': acceptedType,
          'API-Version': version,
          'Vary': 'Accept' // Important for caching
        });

        return originalJson(data);
      }.bind(this);

      next();
    };
  }
}

// services/version-compatibility.js
class VersionCompatibilityService {
  constructor() {
    this.breakingChanges = new Map();
    this.migrationStrategies = new Map();
  }

  registerBreakingChange(fromVersion, toVersion, change) {
    const key = `${fromVersion}->${toVersion}`;

    if (!this.breakingChanges.has(key)) {
      this.breakingChanges.set(key, []);
    }

    this.breakingChanges.get(key).push(change);
  }

  registerMigrationStrategy(fromVersion, toVersion, strategy) {
    const key = `${fromVersion}->${toVersion}`;
    this.migrationStrategies.set(key, strategy);
  }

  analyzeCompatibility(fromVersion, toVersion, data) {
    const key = `${fromVersion}->${toVersion}`;
    const changes = this.breakingChanges.get(key) || [];

    const issues = [];

    for (const change of changes) {
      if (change.detector(data)) {
        issues.push({
          type: change.type,
          field: change.field,
          description: change.description,
          severity: change.severity,
          migration: change.migration
        });
      }
    }

    return {
      compatible: issues.length === 0,
      issues,
      canAutoMigrate: issues.every(i => i.migration !== null)
    };
  }

  migrate(fromVersion, toVersion, data) {
    const key = `${fromVersion}->${toVersion}`;
    const strategy = this.migrationStrategies.get(key);

    if (!strategy) {
      throw new Error(`No migration strategy from ${fromVersion} to ${toVersion}`);
    }

    return strategy(data);
  }
}

// Example breaking changes registration
const compatibilityService = new VersionCompatibilityService();

compatibilityService.registerBreakingChange('v1', 'v2', {
  type: 'field_renamed',
  field: 'name',
  description: 'Field "name" renamed to "displayName"',
  severity: 'major',
  detector: (data) => data.hasOwnProperty('name'),
  migration: (data) => {
    data.displayName = data.name;
    delete data.name;
    return data;
  }
});

compatibilityService.registerBreakingChange('v1', 'v2', {
  type: 'field_added_required',
  field: 'profile',
  description: 'Required field "profile" added',
  severity: 'major',
  detector: (data) => !data.hasOwnProperty('profile'),
  migration: (data) => {
    data.profile = {
      avatar: null,
      bio: '',
      createdAt: new Date().toISOString()
    };
    return data;
  }
});

// Migration strategy for v1 to v2
compatibilityService.registerMigrationStrategy('v1', 'v2', (data) => {
  // Full migration logic
  const migrated = { ...data };

  // Rename fields
  if (migrated.name) {
    migrated.displayName = migrated.name;
    delete migrated.name;
  }

  // Add new required fields
  if (!migrated.profile) {
    migrated.profile = {
      avatar: null,
      bio: '',
      createdAt: new Date().toISOString()
    };
  }

  // Transform nested structures
  if (migrated.addresses && Array.isArray(migrated.addresses)) {
    migrated.locations = migrated.addresses.map(addr => ({
      type: addr.type || 'home',
      address: addr,
      isPrimary: addr.primary || false
    }));
    delete migrated.addresses;
  }

  return migrated;
});
```

### Example 3: Automated Version Testing and Documentation

```javascript
// tests/version-compatibility.test.js
const request = require('supertest');
const app = require('../app');

class VersionCompatibilityTester {
  constructor(app) {
    this.app = app;
    this.versions = ['v1', 'v2', 'v3'];
    this.endpoints = [];
    this.results = [];
  }

  addEndpoint(method, path, testCases) {
    this.endpoints.push({ method, path, testCases });
  }

  async runCompatibilityTests() {
    console.log('Running API version compatibility tests...\n');

    for (const endpoint of this.endpoints) {
      for (const version of this.versions) {
        for (const testCase of endpoint.testCases) {
          const result = await this.testEndpoint(
            version,
            endpoint.method,
            endpoint.path,
            testCase
          );

          this.results.push(result);

          // Log result
          const status = result.passed ? '✓' : '✗';
          console.log(
            `${status} ${version} ${endpoint.method} ${endpoint.path} - ${testCase.name}`
          );
        }
      }
    }

    return this.generateReport();
  }

  async testEndpoint(version, method, path, testCase) {
    const url = `/api/${version}${path}`;

    try {
      const response = await request(this.app)
        [method.toLowerCase()](url)
        .send(testCase.payload || {})
        .set('Accept', `application/vnd.api.${version}+json`)
        .expect(testCase.expectedStatus || 200);

      // Validate response structure
      const validation = this.validateResponse(
        version,
        response.body,
        testCase.expectedSchema
      );

      return {
        version,
        endpoint: `${method} ${path}`,
        testCase: testCase.name,
        passed: validation.valid,
        errors: validation.errors,
        response: response.body
      };
    } catch (error) {
      return {
        version,
        endpoint: `${method} ${path}`,
        testCase: testCase.name,
        passed: false,
        errors: [error.message],
        response: null
      };
    }
  }

  validateResponse(version, response, expectedSchema) {
    // Version-specific validation logic
    const errors = [];

    // Check required fields
    for (const field of expectedSchema.required || []) {
      if (!response.hasOwnProperty(field)) {
        errors.push(`Missing required field: ${field}`);
      }
    }

    // Check field types
    for (const [field, type] of Object.entries(expectedSchema.properties || {})) {
      if (response[field] !== undefined && typeof response[field] !== type) {
        errors.push(`Invalid type for ${field}: expected ${type}`);
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        total: this.results.length,
        passed: this.results.filter(r => r.passed).length,
        failed: this.results.filter(r => !r.passed).length
      },
      versionMatrix: this.generateVersionMatrix(),
      failures: this.results.filter(r => !r.passed),
      recommendations: this.generateRecommendations()
    };

    // Save report
    require('fs').writeFileSync(
      'version-compatibility-report.json',
      JSON.stringify(report, null, 2)
    );

    return report;
  }

  generateVersionMatrix() {
    const matrix = {};

    for (const version of this.versions) {
      matrix[version] = {
        endpoints: {},
        compatibility: 0
      };

      for (const endpoint of this.endpoints) {
        const key = `${endpoint.method} ${endpoint.path}`;
        const results = this.results.filter(
          r => r.version === version && r.endpoint === key
        );

        matrix[version].endpoints[key] = {
          total: results.length,
          passed: results.filter(r => r.passed).length
        };
      }

      // Calculate compatibility percentage
      const versionResults = this.results.filter(r => r.version === version);
      matrix[version].compatibility = (
        (versionResults.filter(r => r.passed).length / versionResults.length) * 100
      ).toFixed(2);
    }

    return matrix;
  }

  generateRecommendations() {
    const recommendations = [];

    // Check for consistent failures across versions
    const failurePatterns = {};

    for (const failure of this.results.filter(r => !r.passed)) {
      const key = failure.endpoint;

      if (!failurePatterns[key]) {
        failurePatterns[key] = new Set();
      }

      failurePatterns[key].add(failure.version);
    }

    for (const [endpoint, versions] of Object.entries(failurePatterns)) {
      if (versions.size > 1) {
        recommendations.push({
          type: 'cross_version_failure',
          endpoint,
          affectedVersions: Array.from(versions),
          recommendation: 'Review endpoint implementation for version-agnostic issues'
        });
      }
    }

    return recommendations;
  }
}

// Usage
const tester = new VersionCompatibilityTester(app);

// Add test cases
tester.addEndpoint('GET', '/users', [
  {
    name: 'List users',
    expectedStatus: 200,
    expectedSchema: {
      required: ['data'],
      properties: {
        data: 'object'
      }
    }
  }
]);

tester.addEndpoint('POST', '/users', [
  {
    name: 'Create user with v1 format',
    payload: {
      name: 'John Doe',
      email: 'john@example.com'
    },
    expectedStatus: 201
  },
  {
    name: 'Create user with v2 format',
    payload: {
      displayName: 'John Doe',
      email: 'john@example.com',
      profile: {
        bio: 'Developer'
      }
    },
    expectedStatus: 201
  }
]);

// Run tests
tester.runCompatibilityTests()
  .then(report => {
    console.log('\nCompatibility Report Generated');
    console.log(`Total Tests: ${report.summary.total}`);
    console.log(`Passed: ${report.summary.passed}`);
    console.log(`Failed: ${report.summary.failed}`);
  });
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid API version" | Unsupported version requested | Return list of supported versions |
| "Version sunset" | Version no longer available | Provide migration guide and alternatives |
| "Incompatible request" | Breaking changes detected | Apply automatic migration if possible |
| "Deprecation warning ignored" | Client using deprecated version | Send stronger warnings, contact client |
| "Version routing conflict" | Overlapping route definitions | Review route precedence rules |

## Configuration Options

**Versioning Strategies**
- `url-path`: Version in URL path (/v1/)
- `header`: Version in Accept header
- `query`: Version in query parameter
- `subdomain`: Version in subdomain (v1.api.example.com)

**Deprecation Policies**
- `aggressive`: 3-month deprecation cycle
- `standard`: 6-month deprecation cycle
- `conservative`: 12-month deprecation cycle
- `enterprise`: Custom per-client agreements

## Best Practices

DO:
- Support at least 2 major versions simultaneously
- Provide clear deprecation timelines
- Version your database schemas
- Maintain comprehensive migration documentation
- Use semantic versioning
- Monitor version usage analytics

DON'T:
- Remove versions without notice
- Make breaking changes in minor versions
- Ignore backward compatibility
- Version too granularly
- Mix versioning strategies

## Performance Considerations

- Cache responses per version
- Lazy-load version-specific code
- Use CDN with version-aware caching
- Monitor performance per version
- Optimize hot migration paths

## Monitoring and Analytics

```javascript
// Track version usage
const versionMetrics = {
  requests: new Map(),
  deprecated: new Map(),
  errors: new Map()
};

app.use((req, res, next) => {
  const version = req.apiVersion || 'unknown';
  versionMetrics.requests.set(
    version,
    (versionMetrics.requests.get(version) || 0) + 1
  );
  next();
});
```

## Related Commands

- `/api-documentation-generator` - Generate version-specific docs
- `/api-sdk-generator` - Create versioned SDKs
- `/api-testing-framework` - Test version compatibility
- `/api-migration-tool` - Automate version migrations

## Version History

- v1.0.0 (2024-10): Initial implementation with URL path versioning
- Planned v1.1.0: Add GraphQL schema versioning support