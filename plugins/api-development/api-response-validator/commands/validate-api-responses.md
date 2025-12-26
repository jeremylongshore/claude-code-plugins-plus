---
name: validate-api-responses
description: Validate API responses against schemas
shortcut: val
---
# Validate API Responses

Implement comprehensive API response validation using JSON Schema, OpenAPI specifications, and custom business rules to ensure data integrity and contract compliance.

## When to Use This Command

Use `/validate-api-responses` when you need to:
- Ensure API responses conform to documented schemas
- Catch contract violations before they reach clients
- Validate response data types, formats, and constraints
- Implement runtime schema validation in production
- Create automated contract testing pipelines
- Monitor API compatibility across versions

DON'T use this when:
- Building prototypes without defined schemas (premature optimization)
- Working with highly dynamic responses (consider runtime type checking instead)
- Validating simple scalar responses (overkill for basic types)

## Design Decisions

This command implements **JSON Schema + Ajv** as the primary approach because:
- Industry-standard schema format with wide ecosystem support
- Blazing fast validation with compiled schemas (10x faster than alternatives)
- Comprehensive format validators for dates, emails, UUIDs, etc.
- Custom keyword support for business-specific validation
- Clear, actionable error messages for debugging

**Alternative considered: OpenAPI/Swagger validation**
- Better for full API contract validation
- Includes request validation, not just responses
- More complex setup and configuration
- Recommended when using OpenAPI for documentation

**Alternative considered: Joi/Yup validation**
- More intuitive API for JavaScript developers
- Better TypeScript integration
- Limited to JavaScript ecosystem
- Recommended for Node.js-only projects

## Prerequisites

Before running this command:
1. Define response schemas (JSON Schema or OpenAPI)
2. Identify validation points (middleware, tests, runtime)
3. Determine error handling strategy
4. Plan performance impact for large payloads
5. Consider validation modes (strict vs. permissive)

## Implementation Process

### Step 1: Define Response Schemas
Create JSON Schema definitions for all API responses with proper constraints.

### Step 2: Configure Validation Middleware
Set up validation middleware to intercept and validate responses automatically.

### Step 3: Implement Custom Validators
Add business-specific validation rules beyond structural validation.

### Step 4: Set Up Error Handling
Configure how validation errors are reported to clients and logged.

### Step 5: Create Test Suites
Build comprehensive test suites for schema validation and edge cases.

## Output Format

The command generates:
- `schemas/` - JSON Schema definitions for all endpoints
- `validators/` - Compiled validator functions
- `middleware/response-validator.js` - Express/Koa middleware
- `tests/schema-validation.test.js` - Validation test suites
- `docs/api-schemas.md` - Human-readable schema documentation
- `monitoring/validation-metrics.js` - Validation failure tracking

## Code Examples

### Example 1: JSON Schema Validation with Ajv

```javascript
// schemas/user-response.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "UserResponse",
  "type": "object",
  "required": ["id", "email", "createdAt"],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "email": {
      "type": "string",
      "format": "email",
      "maxLength": 255
    },
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    },
    "age": {
      "type": "integer",
      "minimum": 0,
      "maximum": 150
    },
    "roles": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["admin", "user", "moderator"]
      },
      "minItems": 1,
      "uniqueItems": true
    },
    "preferences": {
      "type": "object",
      "properties": {
        "theme": {
          "type": "string",
          "enum": ["light", "dark", "auto"]
        },
        "notifications": {
          "type": "boolean"
        }
      }
    },
    "createdAt": {
      "type": "string",
      "format": "date-time"
    },
    "updatedAt": {
      "type": "string",
      "format": "date-time"
    }
  },
  "additionalProperties": false
}

// validators/response-validator.js
const Ajv = require('ajv');
const addFormats = require('ajv-formats');
const fs = require('fs');
const path = require('path');

class ResponseValidator {
  constructor() {
    this.ajv = new Ajv({
      allErrors: true,
      removeAdditional: 'failing',
      useDefaults: true,
      coerceTypes: false,
      strict: true
    });

    // Add format validators
    addFormats(this.ajv);

    // Add custom keywords
    this.addCustomKeywords();

    // Load and compile schemas
    this.schemas = this.loadSchemas();
    this.validators = {};
  }

  addCustomKeywords() {
    // Custom business rule validator
    this.ajv.addKeyword({
      keyword: 'businessRule',
      schemaType: 'string',
      compile: function(schemaValue) {
        return function validate(data, dataCxt) {
          switch(schemaValue) {
            case 'validSubscription':
              return data.subscriptionEnd > new Date().toISOString();
            case 'activeUser':
              return !data.deleted && data.verified;
            default:
              return true;
          }
        };
      }
    });
  }

  loadSchemas() {
    const schemaDir = path.join(__dirname, '../schemas');
    const schemas = {};

    fs.readdirSync(schemaDir).forEach(file => {
      if (file.endsWith('.json')) {
        const schema = JSON.parse(
          fs.readFileSync(path.join(schemaDir, file), 'utf8')
        );
        schemas[schema.$id] = schema;
        this.ajv.addSchema(schema);
      }
    });

    return schemas;
  }

  getValidator(schemaId) {
    if (!this.validators[schemaId]) {
      const schema = this.schemas[schemaId];
      if (!schema) {
        throw new Error(`Schema not found: ${schemaId}`);
      }
      this.validators[schemaId] = this.ajv.compile(schema);
    }
    return this.validators[schemaId];
  }

  validate(schemaId, data) {
    const validator = this.getValidator(schemaId);
    const valid = validator(data);

    if (!valid) {
      return {
        valid: false,
        errors: this.formatErrors(validator.errors),
        rawErrors: validator.errors
      };
    }

    return { valid: true };
  }

  formatErrors(errors) {
    return errors.map(err => ({
      field: err.instancePath || 'root',
      message: err.message,
      params: err.params,
      keyword: err.keyword,
      schemaPath: err.schemaPath
    }));
  }
}

// middleware/response-validator.js
const ResponseValidator = require('../validators/response-validator');

function createResponseValidationMiddleware(options = {}) {
  const validator = new ResponseValidator();
  const {
    enabled = true,
    strict = false,
    logErrors = true,
    includeErrorDetails = process.env.NODE_ENV !== 'production'
  } = options;

  return function responseValidationMiddleware(req, res, next) {
    if (!enabled) return next();

    // Store original json method
    const originalJson = res.json;

    res.json = function(data) {
      // Determine schema based on route
      const schemaId = determineSchema(req.route, res.statusCode);

      if (schemaId) {
        const result = validator.validate(schemaId, data);

        if (!result.valid) {
          if (logErrors) {
            console.error('Response validation failed:', {
              endpoint: req.originalUrl,
              method: req.method,
              schemaId,
              errors: result.errors
            });
          }

          if (strict) {
            // In strict mode, return validation error
            return originalJson.call(this, {
              error: 'Response validation failed',
              details: includeErrorDetails ? result.errors : undefined
            });
          }

          // In non-strict mode, log but send response
          // Could also send to monitoring service
        }
      }

      return originalJson.call(this, data);
    };

    next();
  };
}

function determineSchema(route, statusCode) {
  // Map routes to schemas
  const schemaMap = {
    'GET /users/:id': 'UserResponse',
    'GET /users': 'UserListResponse',
    'POST /users': 'UserResponse',
    'GET /products': 'ProductListResponse',
    'GET /orders/:id': 'OrderResponse'
  };

  const routeKey = `${route.method} ${route.path}`;
  return schemaMap[routeKey];
}

module.exports = createResponseValidationMiddleware;
```

### Example 2: OpenAPI Response Validation

```javascript
// validators/openapi-validator.js
const OpenAPIValidator = require('express-openapi-validator');
const SwaggerParser = require('@apidevtools/swagger-parser');
const fs = require('fs');
const yaml = require('js-yaml');

class OpenAPIResponseValidator {
  constructor(specPath) {
    this.specPath = specPath;
    this.spec = null;
    this.middleware = null;
  }

  async initialize() {
    // Parse and validate OpenAPI spec
    this.spec = await SwaggerParser.validate(this.specPath);

    // Create validation middleware
    this.middleware = OpenAPIValidator.middleware({
      apiSpec: this.specPath,
      validateRequests: false,  // Only validate responses
      validateResponses: {
        removeAdditional: 'failing',
        coerceTypes: false,
        onError: (error, body, req) => {
          console.error('OpenAPI validation error:', {
            endpoint: req.path,
            method: req.method,
            error: error.message,
            errors: error.errors
          });
        }
      },
      validateSecurity: false
    });

    return this;
  }

  getMiddleware() {
    return this.middleware;
  }

  // Manual validation method
  async validateResponse(path, method, status, response) {
    const operation = this.getOperation(path, method);
    if (!operation) {
      throw new Error(`Operation not found: ${method} ${path}`);
    }

    const responseSpec = operation.responses[status];
    if (!responseSpec) {
      throw new Error(`Response not defined for status: ${status}`);
    }

    const schema = responseSpec.content?.['application/json']?.schema;
    if (!schema) {
      return { valid: true };  // No schema defined
    }

    // Validate against schema
    return this.validateAgainstSchema(response, schema);
  }

  getOperation(path, method) {
    const pathItem = this.spec.paths[path];
    return pathItem?.[method.toLowerCase()];
  }

  validateAgainstSchema(data, schema) {
    // Implementation would use Ajv or similar
    // This is simplified for brevity
    const Ajv = require('ajv');
    const ajv = new Ajv();
    const valid = ajv.validate(schema, data);

    return {
      valid,
      errors: ajv.errors
    };
  }
}

// Usage
const validator = await new OpenAPIResponseValidator('./openapi.yaml').initialize();
app.use(validator.getMiddleware());
```

### Example 3: Custom Business Rule Validation

```javascript
// validators/business-rules.js
class BusinessRuleValidator {
  constructor() {
    this.rules = new Map();
    this.registerDefaultRules();
  }

  registerDefaultRules() {
    // User-related rules
    this.addRule('user.ageRestriction', (user) => {
      if (user.role === 'admin' && user.age < 21) {
        return 'Admins must be at least 21 years old';
      }
      return null;
    });

    this.addRule('user.emailDomain', (user) => {
      if (user.role === 'employee' && !user.email.endsWith('@company.com')) {
        return 'Employees must use company email';
      }
      return null;
    });

    // Order-related rules
    this.addRule('order.minimumAmount', (order) => {
      const total = order.items.reduce((sum, item) =>
        sum + (item.price * item.quantity), 0
      );
      if (total < 10) {
        return 'Order must be at least $10';
      }
      return null;
    });

    this.addRule('order.inventoryCheck', async (order) => {
      for (const item of order.items) {
        const available = await checkInventory(item.productId);
        if (available < item.quantity) {
          return `Insufficient inventory for product ${item.productId}`;
        }
      }
      return null;
    });
  }

  addRule(name, validator) {
    this.rules.set(name, validator);
  }

  async validate(context, data) {
    const errors = [];
    const applicableRules = Array.from(this.rules.entries())
      .filter(([name]) => name.startsWith(context));

    for (const [name, validator] of applicableRules) {
      try {
        const error = await validator(data);
        if (error) {
          errors.push({
            rule: name,
            message: error
          });
        }
      } catch (e) {
        errors.push({
          rule: name,
          message: `Rule execution failed: ${e.message}`
        });
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
}

// Integration with response validation
async function validateWithBusinessRules(req, res, next) {
  const originalJson = res.json;
  const validator = new BusinessRuleValidator();

  res.json = async function(data) {
    const context = determineContext(req.route);

    if (context) {
      const result = await validator.validate(context, data);

      if (!result.valid) {
        console.error('Business rule validation failed:', result.errors);

        // Could return error or just log
        if (process.env.STRICT_VALIDATION === 'true') {
          return originalJson.call(this, {
            error: 'Business rule validation failed',
            violations: result.errors
          });
        }
      }
    }

    return originalJson.call(this, data);
  };

  next();
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Schema not found" | Missing schema file | Ensure schema exists in schemas/ directory |
| "Invalid schema" | Malformed JSON Schema | Validate schema with JSON Schema validator |
| "Circular reference" | Schema references itself | Refactor schema to avoid circular dependencies |
| "Performance degradation" | Large payload validation | Use streaming validation or async processing |
| "Memory leak" | Schema compilation on every request | Cache compiled validators |

## Configuration Options

**Validation Modes**
- `strict`: Reject invalid responses (production)
- `permissive`: Log but allow invalid responses (development)
- `monitor`: Send metrics without blocking (staging)

**Performance Tuning**
- `cacheSize`: Number of compiled schemas to cache (default: 100)
- `maxDepth`: Maximum recursion depth for nested objects (default: 10)
- `timeout`: Maximum validation time in ms (default: 1000)

## Best Practices

DO:
- Version your schemas alongside API versions
- Use shared schema definitions for common types
- Validate at multiple layers (client, server, database)
- Include examples in schema definitions
- Monitor validation failures in production
- Use semantic versioning for schema changes

DON'T:
- Validate responses in production synchronously (use async)
- Include sensitive data in validation error messages
- Use overly strict validation that breaks compatibility
- Ignore validation errors in production
- Mix validation logic with business logic

## Performance Considerations

- Compile schemas once at startup, not per request
- Use references for shared schema components
- Consider async validation for large payloads
- Implement sampling for high-traffic endpoints
- Cache validation results for identical responses

## Related Commands

- `/api-contract-generator` - Generate schemas from code
- `/api-documentation-generator` - Document schemas
- `/api-testing-framework` - Test against schemas
- `/api-versioning-manager` - Handle schema evolution

## Version History

- v1.0.0 (2024-10): Initial implementation with JSON Schema validation
- Planned v1.1.0: GraphQL schema validation support