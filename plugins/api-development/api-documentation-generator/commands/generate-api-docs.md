---
name: generate-api-docs
description: >
  Generate comprehensive OpenAPI/Swagger documentation from existing APIs
shortcut: apid
---
# Generate API Documentation

Automatically generate comprehensive OpenAPI 3.0 specifications with interactive documentation, automated testing, and multi-language client SDKs from your existing API codebase or by analyzing live endpoints.

## When to Use This Command

Use `/generate-api-docs` when you need to:
- Document existing APIs without manual specification writing
- Generate interactive API documentation for developers
- Create Postman/Insomnia collections from your API
- Enable "try it out" functionality for API endpoints
- Generate client SDKs in multiple languages
- Maintain API documentation synchronized with code
- Create API reference documentation for external consumers
- Validate API contracts and schemas
- Enable API mocking for frontend development

DON'T use this when:
- Your API is still in early design phase (use `/api-contract-generator` instead)
- You only need internal code comments (use JSDoc/docstrings)
- Building GraphQL APIs (use `/build-graphql-server` with introspection)
- APIs have no stable contract (too early in development)

## Design Decisions

This command implements **OpenAPI 3.0.3 specification** as the primary approach because:
- Industry standard adopted by major organizations
- Extensive tooling ecosystem (Swagger UI, Redoc, SDKs)
- Supports complex schemas including oneOf, allOf, discriminators
- Native support for webhooks and callbacks
- JSON Schema validation built-in
- Multiple security schemes support

**Alternative considered: API Blueprint**
- Markdown-based format
- Simpler for human writing
- Less tooling support
- Recommended for documentation-first design

**Alternative considered: RAML**
- YAML-based with reusable components
- Good for large enterprise APIs
- Smaller ecosystem
- Recommended when modularity is critical

**Alternative considered: AsyncAPI**
- Specialized for event-driven APIs
- WebSocket and message queue support
- Use alongside OpenAPI for complete coverage

## Prerequisites

Before running this command:
1. Functioning API with consistent patterns
2. Request/response examples available
3. Authentication mechanism implemented
4. Error response format standardized
5. API versioning strategy defined

## Implementation Process

### Step 1: API Analysis and Discovery
Scan codebase and running API to discover all endpoints, methods, and data structures.

### Step 2: Schema Extraction
Extract request/response schemas from code annotations, TypeScript types, or runtime analysis.

### Step 3: OpenAPI Generation
Generate complete OpenAPI 3.0 specification with all paths, schemas, and security definitions.

### Step 4: Documentation Enhancement
Add descriptions, examples, and grouping tags for better organization and understanding.

### Step 5: Interactive Documentation Setup
Deploy Swagger UI and Redoc for interactive API exploration and testing.

## Output Format

The command generates:
- `openapi.yaml` - Main OpenAPI 3.0 specification
- `openapi.json` - JSON format for tooling
- `docs/` - Static HTML documentation
  - `index.html` - Swagger UI interface
  - `redoc.html` - Redoc documentation
- `collections/` - External tool formats
  - `postman_collection.json` - Postman import
  - `insomnia_workspace.json` - Insomnia import
  - `bruno_collection.bru` - Bruno collection
- `examples/` - Request/response examples
- `schemas/` - Extracted JSON schemas
- `README.md` - Getting started guide

## Code Examples

### Example 1: Express.js API with Automatic Documentation Generation

```javascript
// api-documentation-generator.js
const swaggerJsdoc = require('swagger-jsdoc');
const swaggerUi = require('swagger-ui-express');
const { z } = require('zod');
const zodToJsonSchema = require('zod-to-json-schema');
const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const yaml = require('js-yaml');

class APIDocumentationGenerator {
  constructor(app, config = {}) {
    this.app = app;
    this.config = {
      title: config.title || 'API Documentation',
      version: config.version || '1.0.0',
      description: config.description || 'API Documentation',
      servers: config.servers || [{ url: 'http://localhost:3000' }],
      contact: config.contact || {},
      license: config.license || { name: 'MIT' },
      security: config.security || [],
      ...config
    };

    this.paths = {};
    this.schemas = {};
    this.examples = {};
    this.tags = [];
  }

  // Analyze Express routes and generate OpenAPI paths
  analyzeRoutes() {
    const routes = [];

    // Extract all routes from Express app
    this.app._router.stack.forEach((middleware) => {
      if (middleware.route) {
        // Regular routes
        routes.push({
          path: middleware.route.path,
          methods: Object.keys(middleware.route.methods)
        });
      } else if (middleware.name === 'router') {
        // Router middleware
        middleware.handle.stack.forEach((handler) => {
          if (handler.route) {
            const basePath = middleware.regexp.source
              .replace('\\/?', '')
              .replace('(?=\\/|$)', '')
              .replace(/\\/g, '/')
              .replace('^', '');

            routes.push({
              path: basePath + handler.route.path,
              methods: Object.keys(handler.route.methods)
            });
          }
        });
      }
    });

    // Convert Express routes to OpenAPI paths
    routes.forEach(route => {
      const openApiPath = this.expressToOpenAPIPath(route.path);

      if (!this.paths[openApiPath]) {
        this.paths[openApiPath] = {};
      }

      route.methods.forEach(method => {
        this.paths[openApiPath][method] = this.generateOperation(
          method,
          route.path,
          openApiPath
        );
      });
    });

    return this.paths;
  }

  // Convert Express path to OpenAPI format
  expressToOpenAPIPath(expressPath) {
    // Convert :param to {param}
    return expressPath.replace(/:([^/]+)/g, '{$1}');
  }

  // Generate operation object for a route
  generateOperation(method, expressPath, openApiPath) {
    const operation = {
      tags: this.inferTags(expressPath),
      summary: this.generateSummary(method, expressPath),
      description: this.generateDescription(method, expressPath),
      operationId: this.generateOperationId(method, expressPath),
      parameters: this.extractParameters(openApiPath),
      responses: this.generateResponses(method, expressPath)
    };

    // Add request body for POST, PUT, PATCH
    if (['post', 'put', 'patch'].includes(method)) {
      operation.requestBody = this.generateRequestBody(method, expressPath);
    }

    // Add security if applicable
    if (this.requiresAuth(expressPath)) {
      operation.security = [{ bearerAuth: [] }];
    }

    return operation;
  }

  // Infer tags from path
  inferTags(path) {
    const segments = path.split('/').filter(s => s && !s.startsWith(':'));
    if (segments.length > 0) {
      const tag = segments[0].charAt(0).toUpperCase() + segments[0].slice(1);

      // Add tag to tags list if not exists
      if (!this.tags.find(t => t.name === tag)) {
        this.tags.push({
          name: tag,
          description: `Operations related to ${tag.toLowerCase()}`
        });
      }

      return [tag];
    }
    return ['General'];
  }

  // Generate operation summary
  generateSummary(method, path) {
    const resource = path.split('/').filter(s => s && !s.startsWith(':')).pop() || 'resource';
    const summaries = {
      get: path.includes(':') ? `Get ${resource} by ID` : `List all ${resource}`,
      post: `Create a new ${resource}`,
      put: `Update ${resource}`,
      patch: `Partially update ${resource}`,
      delete: `Delete ${resource}`,
      head: `Check ${resource} existence`,
      options: `Get ${resource} options`
    };
    return summaries[method] || `${method.toUpperCase()} ${resource}`;
  }

  // Generate detailed description
  generateDescription(method, path) {
    const resource = path.split('/').filter(s => s && !s.startsWith(':')).pop() || 'resource';
    return `Performs a ${method.toUpperCase()} operation on ${resource}. ` +
           `This endpoint ${this.requiresAuth(path) ? 'requires authentication' : 'is publicly accessible'}.`;
  }

  // Generate operation ID
  generateOperationId(method, path) {
    const segments = path.split('/').filter(s => s && !s.startsWith(':'));
    const resource = segments.join('_');
    return `${method}_${resource}`.replace(/[^a-zA-Z0-9_]/g, '_');
  }

  // Extract parameters from path
  extractParameters(path) {
    const parameters = [];

    // Extract path parameters
    const pathParams = path.match(/{([^}]+)}/g);
    if (pathParams) {
      pathParams.forEach(param => {
        const name = param.slice(1, -1);
        parameters.push({
          name,
          in: 'path',
          required: true,
          description: `ID of the ${name}`,
          schema: {
            type: 'string',
            format: name.toLowerCase().includes('id') ? 'uuid' : undefined
          }
        });
      });
    }

    // Add common query parameters for list operations
    if (!path.includes('{')) {
      parameters.push(
        {
          name: 'page',
          in: 'query',
          description: 'Page number for pagination',
          schema: { type: 'integer', default: 1, minimum: 1 }
        },
        {
          name: 'limit',
          in: 'query',
          description: 'Number of items per page',
          schema: { type: 'integer', default: 20, minimum: 1, maximum: 100 }
        },
        {
          name: 'sort',
          in: 'query',
          description: 'Sort field and direction (e.g., "name:asc")',
          schema: { type: 'string' }
        },
        {
          name: 'filter',
          in: 'query',
          description: 'Filter criteria',
          schema: { type: 'string' }
        }
      );
    }

    return parameters;
  }

  // Generate request body schema
  generateRequestBody(method, path) {
    const resource = path.split('/').filter(s => s && !s.startsWith(':')).pop() || 'resource';
    const schemaName = resource.charAt(0).toUpperCase() + resource.slice(1);

    // Generate or retrieve schema
    if (!this.schemas[schemaName]) {
      this.schemas[schemaName] = this.generateResourceSchema(schemaName);
    }

    return {
      required: method === 'post',
      content: {
        'application/json': {
          schema: {
            $ref: `#/components/schemas/${schemaName}`
          },
          examples: this.generateExamples(schemaName)
        }
      }
    };
  }

  // Generate resource schema
  generateResourceSchema(name) {
    // This would ideally extract from your actual models
    // Here's a generic example
    return {
      type: 'object',
      required: ['name'],
      properties: {
        id: {
          type: 'string',
          format: 'uuid',
          readOnly: true,
          description: 'Unique identifier'
        },
        name: {
          type: 'string',
          minLength: 1,
          maxLength: 255,
          description: `Name of the ${name.toLowerCase()}`
        },
        description: {
          type: 'string',
          maxLength: 1000,
          description: 'Detailed description'
        },
        status: {
          type: 'string',
          enum: ['active', 'inactive', 'pending'],
          default: 'active',
          description: 'Current status'
        },
        metadata: {
          type: 'object',
          additionalProperties: true,
          description: 'Additional metadata'
        },
        createdAt: {
          type: 'string',
          format: 'date-time',
          readOnly: true,
          description: 'Creation timestamp'
        },
        updatedAt: {
          type: 'string',
          format: 'date-time',
          readOnly: true,
          description: 'Last update timestamp'
        }
      }
    };
  }

  // Generate response schemas
  generateResponses(method, path) {
    const responses = {
      '200': {
        description: 'Successful operation',
        content: {
          'application/json': {
            schema: this.generateResponseSchema(method, path)
          }
        }
      },
      '400': {
        description: 'Bad request',
        content: {
          'application/json': {
            schema: { $ref: '#/components/schemas/Error' }
          }
        }
      },
      '401': {
        description: 'Unauthorized',
        content: {
          'application/json': {
            schema: { $ref: '#/components/schemas/Error' }
          }
        }
      },
      '404': {
        description: 'Resource not found',
        content: {
          'application/json': {
            schema: { $ref: '#/components/schemas/Error' }
          }
        }
      },
      '500': {
        description: 'Internal server error',
        content: {
          'application/json': {
            schema: { $ref: '#/components/schemas/Error' }
          }
        }
      }
    };

    // Customize based on method
    if (method === 'post') {
      responses['201'] = responses['200'];
      responses['201'].description = 'Resource created successfully';
      delete responses['200'];
    } else if (method === 'delete') {
      responses['204'] = {
        description: 'Resource deleted successfully'
      };
      delete responses['200'];
    }

    return responses;
  }

  // Generate response schema based on operation
  generateResponseSchema(method, path) {
    const resource = path.split('/').filter(s => s && !s.startsWith(':')).pop() || 'resource';
    const schemaName = resource.charAt(0).toUpperCase() + resource.slice(1);

    if (!path.includes(':') && method === 'get') {
      // List operation
      return {
        type: 'object',
        properties: {
          data: {
            type: 'array',
            items: { $ref: `#/components/schemas/${schemaName}` }
          },
          pagination: { $ref: '#/components/schemas/Pagination' },
          meta: { $ref: '#/components/schemas/Meta' }
        }
      };
    } else {
      // Single resource
      return { $ref: `#/components/schemas/${schemaName}` };
    }
  }

  // Generate examples for schemas
  generateExamples(schemaName) {
    return {
      default: {
        summary: 'Standard example',
        value: {
          name: `Example ${schemaName}`,
          description: 'This is an example description',
          status: 'active',
          metadata: {
            category: 'example',
            priority: 'high'
          }
        }
      },
      minimal: {
        summary: 'Minimal required fields',
        value: {
          name: `Minimal ${schemaName}`
        }
      },
      complete: {
        summary: 'All fields populated',
        value: {
          id: '550e8400-e29b-41d4-a716-446655440000',
          name: `Complete ${schemaName}`,
          description: 'This example includes all possible fields',
          status: 'active',
          metadata: {
            category: 'complete',
            priority: 'high',
            tags: ['example', 'complete'],
            customField: 'custom value'
          },
          createdAt: '2024-01-15T10:30:00Z',
          updatedAt: '2024-01-15T14:45:00Z'
        }
      }
    };
  }

  // Check if path requires authentication
  requiresAuth(path) {
    // Implement your auth logic
    const publicPaths = ['/health', '/docs', '/api-docs', '/login', '/register'];
    return !publicPaths.some(p => path.includes(p));
  }

  // Add common schemas
  addCommonSchemas() {
    this.schemas.Error = {
      type: 'object',
      required: ['code', 'message'],
      properties: {
        code: {
          type: 'string',
          description: 'Error code'
        },
        message: {
          type: 'string',
          description: 'Error message'
        },
        details: {
          type: 'object',
          additionalProperties: true,
          description: 'Additional error details'
        },
        timestamp: {
          type: 'string',
          format: 'date-time',
          description: 'Error timestamp'
        }
      }
    };

    this.schemas.Pagination = {
      type: 'object',
      properties: {
        page: { type: 'integer', minimum: 1 },
        limit: { type: 'integer', minimum: 1, maximum: 100 },
        total: { type: 'integer', minimum: 0 },
        pages: { type: 'integer', minimum: 0 }
      }
    };

    this.schemas.Meta = {
      type: 'object',
      properties: {
        version: { type: 'string' },
        timestamp: { type: 'string', format: 'date-time' },
        requestId: { type: 'string', format: 'uuid' }
      }
    };
  }

  // Generate complete OpenAPI specification
  generateOpenAPISpec() {
    // Analyze routes
    this.analyzeRoutes();

    // Add common schemas
    this.addCommonSchemas();

    const spec = {
      openapi: '3.0.3',
      info: {
        title: this.config.title,
        version: this.config.version,
        description: this.config.description,
        contact: this.config.contact,
        license: this.config.license
      },
      servers: this.config.servers,
      tags: this.tags,
      paths: this.paths,
      components: {
        schemas: this.schemas,
        securitySchemes: {
          bearerAuth: {
            type: 'http',
            scheme: 'bearer',
            bearerFormat: 'JWT'
          },
          apiKey: {
            type: 'apiKey',
            name: 'X-API-Key',
            in: 'header'
          },
          oauth2: {
            type: 'oauth2',
            flows: {
              authorizationCode: {
                authorizationUrl: 'https://auth.example.com/oauth/authorize',
                tokenUrl: 'https://auth.example.com/oauth/token',
                refreshUrl: 'https://auth.example.com/oauth/refresh',
                scopes: {
                  read: 'Read access',
                  write: 'Write access',
                  admin: 'Admin access'
                }
              }
            }
          }
        }
      },
      security: this.config.security
    };

    return spec;
  }

  // Export to various formats
  async exportDocumentation(outputDir = './api-docs') {
    const spec = this.generateOpenAPISpec();

    // Create output directory
    await fs.mkdir(outputDir, { recursive: true });
    await fs.mkdir(path.join(outputDir, 'collections'), { recursive: true });

    // Save OpenAPI spec in YAML and JSON
    await fs.writeFile(
      path.join(outputDir, 'openapi.yaml'),
      yaml.dump(spec, { indent: 2 })
    );

    await fs.writeFile(
      path.join(outputDir, 'openapi.json'),
      JSON.stringify(spec, null, 2)
    );

    // Generate Postman collection
    const postmanCollection = this.convertToPostmanCollection(spec);
    await fs.writeFile(
      path.join(outputDir, 'collections', 'postman_collection.json'),
      JSON.stringify(postmanCollection, null, 2)
    );

    // Generate HTML documentation
    await this.generateHTMLDocs(spec, outputDir);

    // Generate README
    await this.generateREADME(spec, outputDir);

    console.log(`API documentation generated in ${outputDir}`);
    return spec;
  }

  // Convert OpenAPI to Postman Collection
  convertToPostmanCollection(openApiSpec) {
    const collection = {
      info: {
        name: openApiSpec.info.title,
        description: openApiSpec.info.description,
        version: openApiSpec.info.version,
        schema: 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
      },
      item: [],
      auth: {
        type: 'bearer',
        bearer: [{
          key: 'token',
          value: '{{access_token}}',
          type: 'string'
        }]
      },
      variable: [
        {
          key: 'baseUrl',
          value: openApiSpec.servers[0].url,
          type: 'string'
        },
        {
          key: 'access_token',
          value: '',
          type: 'string'
        }
      ]
    };

    // Group by tags
    const folders = {};

    Object.entries(openApiSpec.paths).forEach(([path, methods]) => {
      Object.entries(methods).forEach(([method, operation]) => {
        const tag = operation.tags?.[0] || 'General';

        if (!folders[tag]) {
          folders[tag] = {
            name: tag,
            item: []
          };
        }

        const request = {
          name: operation.summary,
          request: {
            method: method.toUpperCase(),
            header: [],
            url: {
              raw: `{{baseUrl}}${path}`,
              host: ['{{baseUrl}}'],
              path: path.split('/').filter(p => p)
            },
            description: operation.description
          }
        };

        // Add path parameters
        if (operation.parameters) {
          const pathParams = operation.parameters.filter(p => p.in === 'path');
          const queryParams = operation.parameters.filter(p => p.in === 'query');

          if (pathParams.length > 0) {
            request.request.url.variable = pathParams.map(p => ({
              key: p.name,
              value: '',
              description: p.description
            }));
          }

          if (queryParams.length > 0) {
            request.request.url.query = queryParams.map(p => ({
              key: p.name,
              value: '',
              description: p.description,
              disabled: !p.required
            }));
          }
        }

        // Add request body
        if (operation.requestBody) {
          const content = operation.requestBody.content['application/json'];
          if (content) {
            request.request.header.push({
              key: 'Content-Type',
              value: 'application/json'
            });

            request.request.body = {
              mode: 'raw',
              raw: JSON.stringify(
                content.examples?.default?.value || {},
                null,
                2
              )
            };
          }
        }

        // Add auth if required
        if (operation.security) {
          request.request.auth = {
            type: 'bearer',
            bearer: [{
              key: 'token',
              value: '{{access_token}}'
            }]
          };
        }

        folders[tag].item.push(request);
      });
    });

    collection.item = Object.values(folders);
    return collection;
  }

  // Generate HTML documentation
  async generateHTMLDocs(spec, outputDir) {
    // Swagger UI HTML
    const swaggerHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>${spec.info.title} - Swagger UI</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css">
    <style>
      body { margin: 0; padding: 0; }
      .swagger-ui .topbar { display: none; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
      window.onload = () => {
        window.ui = SwaggerUIBundle({
          url: './openapi.json',
          dom_id: '#swagger-ui',
          presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIStandalonePreset
          ],
          layout: "BaseLayout",
          deepLinking: true,
          showExtensions: true,
          showCommonExtensions: true,
          tryItOutEnabled: true
        });
      };
    </script>
</body>
</html>`;

    // Redoc HTML
    const redocHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>${spec.info.title} - ReDoc</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body { margin: 0; padding: 0; }
    </style>
</head>
<body>
    <redoc spec-url='./openapi.json'></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
</body>
</html>`;

    await fs.writeFile(path.join(outputDir, 'index.html'), swaggerHtml);
    await fs.writeFile(path.join(outputDir, 'redoc.html'), redocHtml);
  }

  // Generate README documentation
  async generateREADME(spec, outputDir) {
    const readme = `# ${spec.info.title}

${spec.info.description}

**Version:** ${spec.info.version}

## Base URL

\`\`\`
${spec.servers.map(s => s.url).join('\n')}
\`\`\`

## Authentication

This API uses the following authentication methods:
${spec.components.securitySchemes ? Object.entries(spec.components.securitySchemes).map(([name, scheme]) =>
  `- **${name}**: ${scheme.type} ${scheme.scheme || ''}`
).join('\n') : '- No authentication required'}

## Available Endpoints

${Object.entries(spec.paths).map(([path, methods]) =>
  Object.entries(methods).map(([method, op]) =>
    `- \`${method.toUpperCase()} ${path}\` - ${op.summary}`
  ).join('\n')
).join('\n')}

## Quick Start

### Installation

\`\`\`bash
# Using npm
npm install axios

# Using curl
curl -X GET "${spec.servers[0].url}/endpoint"
\`\`\`

### Example Request

\`\`\`javascript
const axios = require('axios');

const config = {
  method: 'get',
  url: '${spec.servers[0].url}${Object.keys(spec.paths)[0]}',
  headers: {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
  }
};

axios(config)
  .then(response => {
    console.log(JSON.stringify(response.data));
  })
  .catch(error => {
    console.error(error);
  });
\`\`\`

## Documentation

- [Swagger UI](./index.html) - Interactive API documentation
- [ReDoc](./redoc.html) - Alternative documentation format
- [OpenAPI Spec](./openapi.json) - Raw OpenAPI specification
- [Postman Collection](./collections/postman_collection.json) - Import to Postman

## SDKs

Generate client SDKs using:

\`\`\`bash
# JavaScript/TypeScript
npx @openapitools/openapi-generator-cli generate -i openapi.yaml -g typescript-axios -o ./sdk/typescript

# Python
openapi-generator-cli generate -i openapi.yaml -g python -o ./sdk/python

# Go
openapi-generator-cli generate -i openapi.yaml -g go -o ./sdk/go
\`\`\`

## Support

${spec.info.contact?.email ? `For support, contact ${spec.info.contact.email}` : 'For support, please refer to the documentation.'}

## License

${spec.info.license?.name || 'See LICENSE file'}
`;

    await fs.writeFile(path.join(outputDir, 'README.md'), readme);
  }

  // Setup interactive documentation routes
  setupDocumentationRoutes(basePath = '/api-docs') {
    // Serve OpenAPI spec
    this.app.get(`${basePath}/openapi.json`, (req, res) => {
      res.json(this.generateOpenAPISpec());
    });

    // Serve Swagger UI
    this.app.use(
      `${basePath}`,
      swaggerUi.serve,
      swaggerUi.setup(this.generateOpenAPISpec(), {
        customCss: '.swagger-ui .topbar { display: none }',
        customSiteTitle: this.config.title
      })
    );

    console.log(`API documentation available at ${basePath}`);
  }
}

// Usage example
const app = express();

const docGenerator = new APIDocumentationGenerator(app, {
  title: 'E-commerce API',
  version: '2.0.0',
  description: 'Complete e-commerce platform API with user management, products, and orders',
  servers: [
    { url: 'https://api.example.com/v2', description: 'Production' },
    { url: 'https://staging-api.example.com/v2', description: 'Staging' },
    { url: 'http://localhost:3000', description: 'Development' }
  ],
  contact: {
    name: 'API Support',
    email: 'api@example.com',
    url: 'https://support.example.com'
  }
});

// Generate and export documentation
docGenerator.exportDocumentation('./api-documentation');

// Setup interactive docs
docGenerator.setupDocumentationRoutes('/docs');

module.exports = APIDocumentationGenerator;
```

### Example 2: Python FastAPI with Automatic OpenAPI Enhancement

```python
# api_doc_enhancer.py
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import yaml
from pathlib import Path
import httpx
from datetime import datetime

class OpenAPIEnhancer:
    """Enhance FastAPI's auto-generated OpenAPI with additional features"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.examples = {}
        self.additional_schemas = {}
        self.external_docs = {}

    def enhance_openapi(self):
        """Enhance the OpenAPI spec with additional information"""
        if self.app.openapi_schema:
            return self.app.openapi_schema

        openapi_schema = get_openapi(
            title=self.app.title,
            version=self.app.version,
            description=self.app.description,
            routes=self.app.routes,
        )

        # Add custom enhancements
        self._add_api_versioning(openapi_schema)
        self._add_rate_limiting_info(openapi_schema)
        self._add_webhook_definitions(openapi_schema)
        self._add_code_samples(openapi_schema)
        self._add_security_schemes(openapi_schema)
        self._add_server_variables(openapi_schema)
        self._enhance_schemas(openapi_schema)
        self._add_tags_metadata(openapi_schema)

        self.app.openapi_schema = openapi_schema
        return self.app.openapi_schema

    def _add_api_versioning(self, spec: Dict[str, Any]):
        """Add API versioning information"""
        spec["info"]["x-api-versioning"] = {
            "strategy": "uri",
            "current": "v2",
            "supported": ["v1", "v2"],
            "deprecated": ["v0"],
            "sunset": {
                "v0": "2024-01-01",
                "v1": "2025-01-01"
            }
        }

    def _add_rate_limiting_info(self, spec: Dict[str, Any]):
        """Add rate limiting documentation"""
        spec["info"]["x-rate-limiting"] = {
            "default": {
                "requests": 1000,
                "window": "1h"
            },
            "authenticated": {
                "requests": 5000,
                "window": "1h"
            },
            "endpoints": {
                "/api/search": {
                    "requests": 100,
                    "window": "1m"
                }
            },
            "headers": {
                "limit": "X-RateLimit-Limit",
                "remaining": "X-RateLimit-Remaining",
                "reset": "X-RateLimit-Reset"
            }
        }

    def _add_webhook_definitions(self, spec: Dict[str, Any]):
        """Add webhook definitions to OpenAPI spec"""
        spec["webhooks"] = {
            "orderCreated": {
                "post": {
                    "requestBody": {
                        "description": "Order creation notification",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/OrderWebhook"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Webhook processed successfully"
                        }
                    }
                }
            },
            "paymentProcessed": {
                "post": {
                    "requestBody": {
                        "description": "Payment processing notification",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/PaymentWebhook"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Webhook acknowledged"
                        }
                    }
                }
            }
        }

        # Add webhook schemas
        if "components" not in spec:
            spec["components"] = {}
        if "schemas" not in spec["components"]:
            spec["components"]["schemas"] = {}

        spec["components"]["schemas"]["OrderWebhook"] = {
            "type": "object",
            "required": ["event", "data", "timestamp"],
            "properties": {
                "event": {
                    "type": "string",
                    "enum": ["order.created", "order.updated", "order.cancelled"]
                },
                "data": {
                    "type": "object",
                    "properties": {
                        "orderId": {"type": "string", "format": "uuid"},
                        "customerId": {"type": "string", "format": "uuid"},
                        "amount": {"type": "number", "format": "float"},
                        "status": {"type": "string"}
                    }
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time"
                }
            }
        }

    def _add_code_samples(self, spec: Dict[str, Any]):
        """Add code samples to each endpoint"""
        for path, methods in spec.get("paths", {}).items():
            for method, operation in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    operation["x-code-samples"] = self._generate_code_samples(
                        method, path, operation
                    )

    def _generate_code_samples(self, method: str, path: str, operation: Dict) -> List[Dict]:
        """Generate code samples for multiple languages"""
        samples = []

        # cURL example
        curl_sample = f"curl -X {method.upper()} '{self.app.servers[0]['url'] if hasattr(self.app, 'servers') else 'https://api.example.com'}{path}'"
        if method in ["post", "put", "patch"]:
            curl_sample += """ \\
  -H 'Content-Type: application/json' \\
  -H 'Authorization: Bearer YOUR_TOKEN' \\
  -d '{
    "name": "example",
    "value": 123
  }'"""
        else:
            curl_sample += " \\\n  -H 'Authorization: Bearer YOUR_TOKEN'"

        samples.append({
            "lang": "Shell",
            "source": curl_sample,
            "label": "cURL"
        })

        # Python example
        python_sample = f"""import requests

url = "https://api.example.com{path}"
headers = {{
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}}"""

        if method in ["post", "put", "patch"]:
            python_sample += """
data = {
    "name": "example",
    "value": 123
}
response = requests.""" + method + """(url, json=data, headers=headers)"""
        else:
            python_sample += f"""
response = requests.{method}(url, headers=headers)"""

        python_sample += """
print(response.json())"""

        samples.append({
            "lang": "Python",
            "source": python_sample,
            "label": "Python (requests)"
        })

        # JavaScript example
        js_sample = f"""const axios = require('axios');

const config = {{
  method: '{method}',
  url: 'https://api.example.com{path}',
  headers: {{
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  }}"""

        if method in ["post", "put", "patch"]:
            js_sample += """,
  data: {
    name: 'example',
    value: 123
  }"""

        js_sample += """
};

axios(config)
  .then(response => {
    console.log(JSON.stringify(response.data));
  })
  .catch(error => {
    console.error(error);
  });"""

        samples.append({
            "lang": "JavaScript",
            "source": js_sample,
            "label": "Node.js (axios)"
        })

        # Go example
        go_sample = f"""package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io/ioutil"
    "net/http"
)

func main() {{
    url := "https://api.example.com{path}"

"""

        if method in ["post", "put", "patch"]:
            go_sample += """    payload := map[string]interface{}{
        "name": "example",
        "value": 123,
    }

    jsonData, _ := json.Marshal(payload)
    req, _ := http.NewRequest(""" + f'"{method.upper()}", url, bytes.NewBuffer(jsonData))'
        else:
            go_sample += f"""    req, _ := http.NewRequest("{method.upper()}", url, nil)"""

        go_sample += """
    req.Header.Set("Authorization", "Bearer YOUR_TOKEN")
    req.Header.Set("Content-Type", "application/json")

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()

    body, _ := ioutil.ReadAll(resp.Body)
    fmt.Println(string(body))
}"""

        samples.append({
            "lang": "Go",
            "source": go_sample,
            "label": "Go (net/http)"
        })

        return samples

    def _add_security_schemes(self, spec: Dict[str, Any]):
        """Add comprehensive security schemes"""
        if "components" not in spec:
            spec["components"] = {}

        spec["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token authentication"
            },
            "apiKey": {
                "type": "apiKey",
                "name": "X-API-Key",
                "in": "header",
                "description": "API key authentication"
            },
            "oauth2": {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": "https://auth.example.com/oauth/authorize",
                        "tokenUrl": "https://auth.example.com/oauth/token",
                        "refreshUrl": "https://auth.example.com/oauth/refresh",
                        "scopes": {
                            "read": "Read access to protected resources",
                            "write": "Write access to protected resources",
                            "admin": "Admin access to all resources"
                        }
                    },
                    "clientCredentials": {
                        "tokenUrl": "https://auth.example.com/oauth/token",
                        "scopes": {
                            "api": "API access"
                        }
                    }
                }
            },
            "cookieAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "session_id",
                "description": "Session cookie authentication"
            }
        }

    def _add_server_variables(self, spec: Dict[str, Any]):
        """Add server variables for environment switching"""
        spec["servers"] = [
            {
                "url": "https://{environment}.api.example.com/{version}",
                "description": "API Server",
                "variables": {
                    "environment": {
                        "enum": ["production", "staging", "development"],
                        "default": "production",
                        "description": "Server environment"
                    },
                    "version": {
                        "enum": ["v1", "v2", "v3"],
                        "default": "v2",
                        "description": "API version"
                    }
                }
            },
            {
                "url": "http://localhost:{port}",
                "description": "Local development server",
                "variables": {
                    "port": {
                        "enum": ["3000", "8000", "8080"],
                        "default": "8000",
                        "description": "Server port"
                    }
                }
            }
        ]

    def _enhance_schemas(self, spec: Dict[str, Any]):
        """Enhance schemas with examples and additional properties"""
        for schema_name, schema in spec.get("components", {}).get("schemas", {}).items():
            if "properties" in schema:
                # Add examples to properties
                for prop_name, prop in schema["properties"].items():
                    if "example" not in prop:
                        prop["example"] = self._generate_example_for_type(prop)

                # Add schema-level example
                if "example" not in schema:
                    schema["example"] = {
                        prop_name: prop.get("example")
                        for prop_name, prop in schema["properties"].items()
                    }

    def _generate_example_for_type(self, prop: Dict) -> Any:
        """Generate example based on property type"""
        prop_type = prop.get("type", "string")
        prop_format = prop.get("format", "")

        examples = {
            ("string", "email"): "user@example.com",
            ("string", "date"): "2024-01-15",
            ("string", "date-time"): "2024-01-15T10:30:00Z",
            ("string", "uuid"): "550e8400-e29b-41d4-a716-446655440000",
            ("string", "uri"): "https://example.com/resource",
            ("string", "hostname"): "api.example.com",
            ("string", "ipv4"): "192.168.1.1",
            ("string", "ipv6"): "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            ("integer", ""): 42,
            ("number", ""): 123.45,
            ("boolean", ""): True,
            ("array", ""): ["item1", "item2"],
            ("object", ""): {"key": "value"}
        }

        return examples.get((prop_type, prop_format), "example")

    def _add_tags_metadata(self, spec: Dict[str, Any]):
        """Add detailed tag descriptions"""
        spec["tags"] = [
            {
                "name": "Authentication",
                "description": "Authentication and authorization endpoints",
                "externalDocs": {
                    "description": "Authentication guide",
                    "url": "https://docs.example.com/auth"
                }
            },
            {
                "name": "Users",
                "description": "User management operations",
                "externalDocs": {
                    "description": "User API documentation",
                    "url": "https://docs.example.com/users"
                }
            },
            {
                "name": "Products",
                "description": "Product catalog management",
                "externalDocs": {
                    "description": "Product API documentation",
                    "url": "https://docs.example.com/products"
                }
            },
            {
                "name": "Orders",
                "description": "Order processing and management",
                "externalDocs": {
                    "description": "Order API documentation",
                    "url": "https://docs.example.com/orders"
                }
            }
        ]

    def export_documentation(self, output_dir: str = "./api-docs"):
        """Export documentation in various formats"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Get enhanced OpenAPI spec
        spec = self.enhance_openapi()

        # Export as JSON
        with open(output_path / "openapi.json", "w") as f:
            json.dump(spec, f, indent=2)

        # Export as YAML
        with open(output_path / "openapi.yaml", "w") as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

        # Generate AsyncAPI spec if websockets are used
        asyncapi_spec = self._generate_asyncapi_spec()
        if asyncapi_spec:
            with open(output_path / "asyncapi.yaml", "w") as f:
                yaml.dump(asyncapi_spec, f, default_flow_style=False)

        # Generate Postman collection
        postman_collection = self._convert_to_postman(spec)
        with open(output_path / "postman_collection.json", "w") as f:
            json.dump(postman_collection, f, indent=2)

        # Generate README
        self._generate_readme(spec, output_path)

        print(f"Documentation exported to {output_path}")

    def _generate_asyncapi_spec(self) -> Optional[Dict]:
        """Generate AsyncAPI spec for WebSocket/event-driven APIs"""
        # Check if app has WebSocket routes
        has_websocket = any(
            hasattr(route, "endpoint") and "websocket" in str(route.endpoint)
            for route in self.app.routes
        )

        if not has_websocket:
            return None

        return {
            "asyncapi": "2.6.0",
            "info": {
                "title": f"{self.app.title} WebSocket API",
                "version": self.app.version,
                "description": f"WebSocket API for {self.app.title}"
            },
            "servers": {
                "production": {
                    "url": "wss://api.example.com",
                    "protocol": "ws",
                    "description": "Production WebSocket server"
                }
            },
            "channels": {
                "/ws": {
                    "subscribe": {
                        "message": {
                            "$ref": "#/components/messages/notification"
                        }
                    },
                    "publish": {
                        "message": {
                            "$ref": "#/components/messages/command"
                        }
                    }
                }
            },
            "components": {
                "messages": {
                    "notification": {
                        "payload": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "data": {"type": "object"}
                            }
                        }
                    },
                    "command": {
                        "payload": {
                            "type": "object",
                            "properties": {
                                "action": {"type": "string"},
                                "params": {"type": "object"}
                            }
                        }
                    }
                }
            }
        }

    def _convert_to_postman(self, spec: Dict) -> Dict:
        """Convert OpenAPI to Postman Collection"""
        # Implementation similar to JavaScript version
        # Simplified for brevity
        return {
            "info": {
                "name": spec["info"]["title"],
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }

    def _generate_readme(self, spec: Dict, output_path: Path):
        """Generate comprehensive README"""
        readme_content = f"""# {spec['info']['title']}

{spec['info'].get('description', '')}

## Version

{spec['info']['version']}

## Documentation

- [OpenAPI Specification](./openapi.json)
- [Postman Collection](./postman_collection.json)
- [AsyncAPI Specification](./asyncapi.yaml) (if applicable)

## Quick Start

```python
import requests

# Example API call
response = requests.get(
    "https://api.example.com/endpoint",
    headers={{"Authorization": "Bearer YOUR_TOKEN"}}
)
print(response.json())
```

## Authentication

See the OpenAPI specification for detailed authentication information.

## Support

{spec['info'].get('contact', {}).get('email', 'support@example.com')}
"""

        with open(output_path / "README.md", "w") as f:
            f.write(readme_content)


# FastAPI app example with enhanced documentation
app = FastAPI(
    title="E-commerce API",
    version="2.0.0",
    description="Comprehensive e-commerce platform API"
)

enhancer = OpenAPIEnhancer(app)

# Override the default OpenAPI endpoint
@app.get("/openapi.json")
async def get_open_api_endpoint():
    return enhancer.enhance_openapi()

# Export documentation
if __name__ == "__main__":
    enhancer.export_documentation()
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "No routes found" | Empty Express/FastAPI app | Ensure routes are defined before generation |
| "Invalid OpenAPI spec" | Malformed specification | Validate with online validators |
| "Schema extraction failed" | TypeScript/Pydantic issues | Check type definitions are correct |
| "Swagger UI not loading" | CORS or path issues | Check CORS settings and base path configuration |
| "Examples not generated" | Missing schema definitions | Ensure all models have proper schemas |

## Configuration Options

**Basic Usage:**
```bash
/generate-api-docs \
  --framework=express \
  --output=./api-docs \
  --format=openapi3 \
  --include-examples
```

**Available Options:**

`--framework <type>` - Web framework to analyze
- `express` - Express.js applications
- `fastapi` - FastAPI Python applications
- `spring` - Spring Boot applications
- `rails` - Ruby on Rails APIs
- `django` - Django REST framework

`--format <spec>` - Output specification format
- `openapi3` - OpenAPI 3.0.3 (default)
- `openapi2` - OpenAPI 2.0 (Swagger)
- `asyncapi` - AsyncAPI for event-driven
- `graphql` - GraphQL schema

`--output <path>` - Output directory for documentation
- Default: `./api-docs`

`--include-examples` - Generate request/response examples
- Analyzes codebase for real examples
- Creates synthetic examples from schemas

`--interactive-ui <type>` - Interactive documentation UI
- `swagger` - Swagger UI (default)
- `redoc` - ReDoc documentation
- `both` - Both UIs
- `none` - Static docs only

`--auth-docs` - Include authentication documentation
- Extracts auth middleware
- Documents OAuth flows
- Includes example tokens

`--sdk-generation` - Generate client SDKs
- `--languages` - Comma-separated list (js,python,go,java)
- `--sdk-output` - SDK output directory

`--postman` - Generate Postman collection
- Includes environment variables
- Pre-request scripts
- Test assertions

`--validate` - Validate generated specification
- Checks for completeness
- Validates examples
- Tests schema consistency

## Best Practices

DO:
- Keep API documentation in sync with code using CI/CD
- Include realistic examples from actual API usage
- Document all error responses and status codes
- Use consistent naming conventions across endpoints
- Include rate limiting and pagination information
- Document deprecated endpoints with sunset dates
- Provide "Try it out" functionality in docs
- Version your API documentation alongside code

DON'T:
- Expose sensitive information in examples
- Use production data in documentation
- Skip documenting edge cases and errors
- Forget to document authentication requirements
- Leave schemas without descriptions
- Mix API versions in single documentation

## Performance Considerations

- Large APIs (500+ endpoints) may take time to analyze
- Schema extraction from TypeScript can be memory-intensive
- Consider splitting documentation by module for very large APIs
- Cache generated documentation to avoid regeneration
- Use CDN for serving interactive documentation

## Security Considerations

- Never include real API keys or tokens in examples
- Sanitize any production data used in documentation
- Use separate documentation URLs for internal vs external APIs
- Implement authentication on documentation endpoints if needed
- Review generated schemas for accidentally exposed fields

## Troubleshooting

**Issue: Routes not detected**
```javascript
// Ensure routes are registered before doc generation
app.use('/api', apiRouter);
// Then generate docs
const docs = new APIDocumentationGenerator(app);
```

**Issue: TypeScript types not extracted**
```bash
# Install required packages
npm install --save-dev typescript ts-json-schema-generator
# Ensure tsconfig.json includes all source files
```

**Issue: Swagger UI CORS errors**
```javascript
// Enable CORS for documentation
app.use('/api-docs', cors({
  origin: '*',
  credentials: true
}));
```

## Related Commands

- `/api-contract-generator` - Design-first API specification
- `/api-mock-server` - Create mock server from OpenAPI spec
- `/api-sdk-generator` - Generate client libraries
- `/api-versioning-manager` - Manage API versions
- `/api-testing-framework` - Generate tests from spec

## Version History

- v1.0.0 (2024-10): Initial implementation with OpenAPI 3.0 support
- Planned v1.1.0: GraphQL introspection and AsyncAPI support