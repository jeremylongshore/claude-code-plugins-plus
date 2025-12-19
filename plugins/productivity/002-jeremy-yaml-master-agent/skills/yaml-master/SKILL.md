---
name: yaml-master
description: |
  Proactive YAML intelligence: automatically activates when working with YAML files.
  Use when appropriate context detected. Trigger with relevant phrases based on skill purpose.
version: 1.0.0
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash(general:*)
- Bash(util:*)
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# YAML Master Agent

**⚡ This skill activates AUTOMATICALLY when you work with YAML files!**

## Automatic Trigger Conditions

This skill proactively activates when Claude detects:

1. **File Operations**: Reading, writing, or editing `.yaml` or `.yml` files
2. **Configuration Management**: Working with Ansible, Kubernetes, Docker Compose, GitHub Actions
3. **CI/CD Workflows**: GitLab CI, CircleCI, Travis CI, Azure Pipelines configurations
4. **Schema Validation**: Validating configuration files against schemas
5. **Format Conversion**: Converting between YAML, JSON, TOML, XML formats
6. **User Requests**: Explicit mentions of "yaml", "validate yaml", "fix yaml syntax", "convert yaml"

**No commands needed!** Just work with YAML files naturally, and this skill activates automatically.

---

## Core Capabilities

### 1. Intelligent YAML Validation

**What It Does**:
- Detects syntax errors (indentation, duplicate keys, invalid scalars)
- Validates against YAML 1.2 specification
- Identifies common anti-patterns (tabs vs spaces, anchors/aliases issues)
- Provides detailed error messages with line numbers and fix suggestions

**Example**:
```yaml
# ❌ INVALID YAML
services:
  web:
    image: nginx
	  ports:  # Mixed tabs and spaces - ERROR!
      - "80:80"
```

**Agent Action**: Automatically detects mixed indentation, suggests fix:
```yaml
# ✅ FIXED YAML
services:
  web:
    image: nginx
    ports:  # Consistent 2-space indentation
      - "80:80"
```

### 2. Schema Inference & Generation

**What It Does**:
- Analyzes YAML structure and infers JSON Schema
- Generates OpenAPI/Swagger schemas from YAML
- Creates type definitions for TypeScript/Python from YAML configs
- Validates instances against inferred or provided schemas

**Example**:
```yaml
# Input YAML
user:
  name: Jeremy
  age: 35
  roles:
    - admin
    - developer
```

**Agent Action**: Infers schema:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "user": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "age": { "type": "integer" },
        "roles": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "required": ["name", "age", "roles"]
    }
  }
}
```

### 3. Format Conversion (YAML ↔ JSON ↔ TOML ↔ XML)

**What It Does**:
- Bidirectional conversion between YAML, JSON, TOML, XML
- Preserves comments when possible (YAML ↔ TOML)
- Handles complex nested structures, arrays, anchors/aliases
- Validates converted output maintains semantic equivalence

**Example - YAML to JSON**:
```yaml
# config.yaml
database:
  host: localhost
  port: 5432
  credentials: &creds
    user: admin
    pass: secret
```

**Agent Action**: Converts to JSON:
```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "credentials": {
      "user": "admin",
      "pass": "secret"
    }
  }
}
```

### 4. Kubernetes Manifest Expertise

**What It Does**:
- Validates K8s manifests against API versions
- Suggests best practices (resource limits, labels, health checks)
- Detects security issues (privileged containers, root users)
- Generates complete manifests from minimal specs

**Example**:
```yaml
# Minimal input
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
```

**Agent Action**: Expands with best practices:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    app: nginx
    version: "1.0"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
        version: "1.0"
    spec:
      containers:
      - name: nginx
        image: nginx:1.25-alpine
        ports:
        - containerPort: 80
          name: http
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
```

### 5. Docker Compose Optimization

**What It Does**:
- Validates Docker Compose syntax (v2.x, v3.x)
- Suggests networking best practices
- Optimizes volume mounts and environment variables
- Detects security misconfigurations

**Example**:
```yaml
# ❌ SUBOPTIMAL
version: '3'
services:
  db:
    image: postgres
    environment:
      POSTGRES_PASSWORD: admin123  # Hardcoded secret!
```

**Agent Action**: Suggests secure alternative:
```yaml
# ✅ OPTIMIZED
version: '3.8'
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

secrets:
  db_password:
    file: ./secrets/db_password.txt

volumes:
  db_data:
    driver: local
```

### 6. CI/CD Pipeline Intelligence

**What It Does**:
- Validates GitHub Actions, GitLab CI, CircleCI workflows
- Suggests caching strategies for faster builds
- Detects matrix build inefficiencies
- Optimizes job dependencies and parallelization

**Example - GitHub Actions**:
```yaml
# ❌ INEFFICIENT
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install  # No caching!
      - run: npm test
```

**Agent Action**: Optimizes with caching:
```yaml
# ✅ OPTIMIZED
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci  # Faster than npm install

      - name: Run tests
        run: npm test

      - name: Upload coverage
        if: matrix.node-version == 20
        uses: codecov/codecov-action@v4
```

### 7. YAML Linting & Style Enforcement

**What It Does**:
- Enforces consistent indentation (2 spaces, 4 spaces, tabs)
- Validates key ordering (alphabetical, custom)
- Detects trailing whitespace, missing newlines
- Suggests canonical YAML representations

**Linting Rules**:
```yaml
# Rule 1: Consistent 2-space indentation
# Rule 2: No duplicate keys
# Rule 3: Quoted strings for special characters
# Rule 4: Explicit document markers (---, ...)
# Rule 5: No tabs, only spaces
# Rule 6: Max line length 120 characters
# Rule 7: Comments aligned at column 40
```

### 8. Anchors & Aliases Mastery

**What It Does**:
- Manages complex YAML anchors and aliases
- Suggests reusable configurations with merge keys
- Validates anchor references
- Refactors duplicate blocks into anchors

**Example**:
```yaml
# ❌ REPETITIVE
services:
  web:
    image: nginx
    restart: always
    logging:
      driver: json-file
      options:
        max-size: "10m"
  api:
    image: node:20
    restart: always
    logging:
      driver: json-file
      options:
        max-size: "10m"
```

**Agent Action**: Refactors with anchors:
```yaml
# ✅ DRY (Don't Repeat Yourself)
x-common-config: &common-config
  restart: always
  logging:
    driver: json-file
    options:
      max-size: "10m"

services:
  web:
    <<: *common-config
    image: nginx

  api:
    <<: *common-config
    image: node:20
```

---

## Advanced Features

### Multi-Document YAML Handling

Works with YAML files containing multiple documents:

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
---
```

**Agent Action**: Validates each document independently, ensures consistency across documents.

### Environment-Specific Configurations

Manages environment overrides and templates:

```yaml
# base.yaml
database: &db
  host: localhost
  port: 5432

# production.yaml (inherits from base)
database:
  <<: *db
  host: prod-db.example.com
  ssl: true
```

### Complex Data Type Handling

Supports advanced YAML data types:

```yaml
# Timestamps
created_at: 2025-10-24T23:00:00Z

# Binary data (base64)
ssl_cert: !!binary |
  R0lGODlhDAAMAIQAAP//9/X
  17unp5WZmZgAAAOfn515eXv

# Null values
optional_field: null
another_null: ~

# Custom tags
color: !rgb [255, 128, 0]
```

---

## Common Use Cases

### 1. Fixing Broken YAML Files

**User**: "My Kubernetes manifest won't apply, fix it"

**Agent Action**:
1. Reads the YAML file
2. Identifies syntax errors (indentation, missing fields)
3. Validates against Kubernetes API schema
4. Provides corrected version with explanations

### 2. Converting JSON API Response to YAML Config

**User**: "Convert this JSON to YAML for my config file"

**Agent Action**:
1. Parses JSON input
2. Converts to idiomatic YAML (multi-line strings, minimal quotes)
3. Adds helpful comments
4. Validates output

### 3. Generating Docker Compose from Requirements

**User**: "Create docker-compose.yaml for nginx + postgres + redis"

**Agent Action**:
1. Generates complete docker-compose.yaml
2. Adds healthchecks, volumes, networks
3. Includes environment variable templates
4. Suggests .env file structure

### 4. Optimizing CI/CD Pipeline

**User**: "My GitHub Actions workflow is slow, optimize it"

**Agent Action**:
1. Analyzes workflow YAML
2. Identifies bottlenecks (no caching, sequential jobs)
3. Suggests parallelization, caching strategies
4. Provides optimized workflow

---

## Integration with Other Tools

### Works Seamlessly With:

- **yamllint**: Validates against yamllint rules
- **Kustomize**: Handles Kustomization files
- **Helm**: Works with Helm chart values.yaml
- **Ansible**: Validates playbooks and roles
- **OpenAPI/Swagger**: Converts to/from OpenAPI specs
- **JSON Schema**: Validates against schemas
- **Terraform**: Converts YAML to HCL (experimental)

---

## Error Handling & Troubleshooting

### Common YAML Errors This Skill Fixes:

| Error | Cause | Fix |
|-------|-------|-----|
| `mapping values are not allowed here` | Incorrect indentation | Align keys properly |
| `found duplicate key` | Same key defined twice | Remove or rename duplicate |
| `expected <block end>, but found` | Tab instead of spaces | Replace tabs with spaces |
| `found undefined tag handle` | Custom tag without definition | Define tag or remove |
| `could not find expected ':'` | Missing colon after key | Add colon |

---

## Best Practices Enforced

1. **Indentation**: Consistent 2-space indentation (configurable)
2. **Quotes**: Minimal quoting (only when necessary)
3. **Comments**: Descriptive comments for complex sections
4. **Security**: No hardcoded secrets, use secrets managers
5. **Validation**: Always validate against schemas
6. **Documentation**: Inline documentation for anchors/aliases
7. **Versioning**: Explicit version tags (Docker Compose, K8s API)

---

## Performance Considerations

- **Large Files**: Streams YAML instead of loading entire file into memory
- **Validation**: Incremental validation for real-time feedback
- **Conversion**: Optimized parsers for fast format conversion
- **Caching**: Caches schema validation results

---

## Compliance & Standards

✅ **YAML 1.2 Specification**: Fully compliant
✅ **YAML 1.1**: Backward compatible where possible
✅ **JSON Schema Draft 7**: Supports schema validation
✅ **OpenAPI 3.1**: Compatible with OpenAPI specs
✅ **Kubernetes API**: Validates against all stable APIs
✅ **Docker Compose v3.8**: Full support for latest spec

---

## Examples by Complexity

### Beginner: Simple Config File

```yaml
# app-config.yaml
app:
  name: MyApp
  version: 1.0.0
  environment: production

server:
  host: 0.0.0.0
  port: 8080

database:
  url: postgres://localhost:5432/mydb
```

### Intermediate: Multi-Service Docker Compose

```yaml
version: '3.8'

services:
  web:
    build: ./web
    ports:
      - "3000:3000"
    depends_on:
      - api
      - redis

  api:
    build: ./api
    environment:
      DATABASE_URL: postgres://db:5432/app
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15-alpine
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready"]
      interval: 5s

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes

volumes:
  db_data:
```

### Advanced: Kubernetes Deployment with Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  DATABASE_URL: postgres://user:pass@db:5432/app
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: myapp:latest
        envFrom:
        - secretRef:
            name: app-secrets
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

---

## Troubleshooting Guide

### Issue: "YAML won't parse"

**Diagnosis**:
1. Check indentation (tabs vs spaces)
2. Verify key-value separator (`:` with space after)
3. Look for duplicate keys

### Issue: "Kubernetes apply fails"

**Diagnosis**:
1. Validate API version matches cluster version
2. Check required fields are present
3. Verify resource names are DNS-compliant

### Issue: "Docker Compose won't start"

**Diagnosis**:
1. Check version compatibility
2. Validate service dependencies
3. Verify volume mount paths exist

---

## Version History

- **v1.0.0** (2025-10-24): Initial release with comprehensive YAML capabilities

---

## License

MIT License - See LICENSE file

---

## Support

- **Issues**: Report issues with YAML handling
- **Documentation**: This SKILL.md + plugin README
- **Community**: Share YAML tips and tricks

---

## Credits

**Author**: Jeremy Longshore
**Plugin**: 002-jeremy-yaml-master-agent
**Spec Compliance**: Anthropic Agent Skills Spec v1.0

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>

## Prerequisites

- Access to project files in {baseDir}/
- Required tools and dependencies installed
- Understanding of skill functionality
- Permissions for file operations

## Instructions

1. Identify skill activation trigger and context
2. Gather required inputs and parameters
3. Execute skill workflow systematically
4. Validate outputs meet requirements
5. Handle errors and edge cases appropriately
6. Provide clear results and next steps

## Output

- Primary deliverables based on skill purpose
- Status indicators and success metrics
- Generated files or configurations
- Reports and summaries as applicable
- Recommendations for follow-up actions

## Error Handling

If execution fails:
- Verify prerequisites are met
- Check input parameters and formats
- Validate file paths and permissions
- Review error messages for root cause
- Consult documentation for troubleshooting

## Resources

- Official documentation for related tools
- Best practices guides
- Example use cases and templates
- Community forums and support channels
