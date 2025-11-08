# YAML Master Agent

**Intelligent YAML validation, generation, and transformation with schema inference and format conversion.**

[![Version](https://img.shields.io/badge/version-1.0.0-brightgreen)](.claude-plugin/plugin.json)
[![Category](https://img.shields.io/badge/category-productivity-blue)](.claude-plugin/plugin.json)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-enabled-orange?logo=sparkles)](.claude-plugin/plugin.json)
[![Anthropic Spec](https://img.shields.io/badge/Anthropic%20Spec-v1.0%20Compliant-success?logo=checkmarx)](https://github.com/anthropics/skills/blob/main/agent_skills_spec.md)

---

## Problem This Solves

**Before**: Working with YAML files is error-prone. Syntax errors from indentation, duplicate keys, and format inconsistencies cause pipeline failures. Manual validation and conversion between formats is tedious.

**After**: The YAML Master Agent automatically detects YAML work and provides intelligent validation, schema inference, linting, and seamless format conversion. Never struggle with YAML syntax again.

---

## Quick Start

### Installation

```bash
/plugin install 002-jeremy-yaml-master-agent@claude-code-plugins-plus
```

### Basic Usage

The skill activates automatically when working with YAML files. No commands needed!

**Example 1: Validate YAML**
```
User: Check this kubernetes manifest for errors
*Opens deployment.yaml*

Agent: 🔍 YAML Master Agent activated
Found 3 issues:
1. Line 12: Mixed indentation (tabs and spaces)
2. Line 24: Duplicate key "metadata"
3. Line 31: Missing required field "selector"

Here's the corrected version...
```

**Example 2: Convert JSON to YAML**
```
User: Convert this JSON config to YAML

Agent: 📋 Converting JSON to idiomatic YAML...
✅ Conversion complete! Added comments and optimized structure.
```

**Example 3: Generate Docker Compose**
```
User: Create docker-compose.yaml for nginx, postgres, redis

Agent: 🐳 Generating optimized Docker Compose configuration...
✅ Complete with healthchecks, volumes, and networks!
```

---

## Features

### ⚡ Automatic Activation (Proactive Skill)

The YAML Master Agent activates automatically when Claude detects:
- Reading/writing `.yaml` or `.yml` files
- Working with Kubernetes, Docker Compose, CI/CD configs
- Mentions of "yaml", "validate", "convert", "lint"

**No user action required!**

### 🔍 Intelligent Validation

- Detects syntax errors with line numbers
- Validates against YAML 1.2 specification
- Identifies anti-patterns (tabs vs spaces, duplicate keys)
- Provides detailed fix suggestions

**Example**:
```yaml
# ❌ INVALID
services:
  web:
	image: nginx  # Tab indentation ERROR!
```
**Agent fixes**:
```yaml
# ✅ VALID
services:
  web:
    image: nginx  # Consistent spaces
```

### 🎯 Schema Inference & Generation

- Infers JSON Schema from YAML structure
- Generates TypeScript/Python types from configs
- Validates instances against schemas
- Creates OpenAPI specs from YAML

**Example**:
```yaml
# Input
user:
  name: Jeremy
  age: 35
```

**Agent generates schema**:
```json
{
  "type": "object",
  "properties": {
    "user": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "age": { "type": "integer" }
      }
    }
  }
}
```

### 🔄 Format Conversion

Seamless conversion between:
- **YAML** ↔ **JSON**
- **YAML** ↔ **TOML**
- **YAML** ↔ **XML**

Preserves comments and maintains semantic equivalence.

### ☸️ Kubernetes Manifest Expertise

- Validates manifests against K8s API versions
- Suggests best practices (resource limits, health checks)
- Detects security issues (privileged containers, root users)
- Generates complete manifests from minimal specs

**Example - Minimal to Production-Ready**:
```yaml
# You provide
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
```

**Agent expands with best practices**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    spec:
      containers:
      - name: nginx
        image: nginx:1.25-alpine
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
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
# ... full production-ready manifest
```

### 🐳 Docker Compose Optimization

- Validates Docker Compose syntax (v2.x, v3.x)
- Suggests networking and security best practices
- Optimizes volume mounts and environment variables
- Detects misconfigurations (hardcoded secrets, missing healthchecks)

### ⚙️ CI/CD Pipeline Intelligence

Optimizes workflows for:
- **GitHub Actions**
- **GitLab CI**
- **CircleCI**
- **Azure Pipelines**
- **Travis CI**

Suggests caching, parallelization, and matrix builds for faster pipelines.

### 📏 Linting & Style Enforcement

- Enforces consistent indentation (2/4 spaces)
- Validates key ordering
- Detects trailing whitespace
- Suggests canonical YAML representations

**Linting Rules**:
1. Consistent 2-space indentation
2. No duplicate keys
3. Quoted strings for special characters
4. No tabs, only spaces
5. Max line length 120 characters

### 🔗 Anchors & Aliases Mastery

- Manages complex anchors and aliases
- Refactors duplicate blocks into reusable configs
- Validates anchor references
- Suggests merge keys for DRY configurations

**Example - Refactoring with Anchors**:
```yaml
# ❌ REPETITIVE
services:
  web:
    restart: always
    logging:
      driver: json-file
  api:
    restart: always
    logging:
      driver: json-file
```

**Agent refactors**:
```yaml
# ✅ DRY
x-common: &common
  restart: always
  logging:
    driver: json-file

services:
  web:
    <<: *common
  api:
    <<: *common
```

---

## Common Use Cases

### 1. Fix Broken YAML Files

**Scenario**: Kubernetes manifest won't apply

**Agent Action**:
1. Reads YAML file
2. Identifies syntax errors
3. Validates against K8s API schema
4. Provides corrected version with explanations

### 2. Convert JSON API Response to YAML Config

**Scenario**: Need to convert JSON to YAML for configuration

**Agent Action**:
1. Parses JSON input
2. Converts to idiomatic YAML (multi-line strings, minimal quotes)
3. Adds helpful comments
4. Validates output

### 3. Generate Docker Compose from Requirements

**Scenario**: "Create docker-compose.yaml for nginx + postgres + redis"

**Agent Action**:
1. Generates complete docker-compose.yaml
2. Adds healthchecks, volumes, networks
3. Includes environment variable templates
4. Suggests .env file structure

### 4. Optimize CI/CD Pipeline

**Scenario**: GitHub Actions workflow is slow

**Agent Action**:
1. Analyzes workflow YAML
2. Identifies bottlenecks (no caching, sequential jobs)
3. Suggests parallelization and caching strategies
4. Provides optimized workflow

---

## Integration with Other Tools

Works seamlessly with:
- **yamllint** - Validates against yamllint rules
- **Kustomize** - Handles Kustomization files
- **Helm** - Works with chart values.yaml
- **Ansible** - Validates playbooks and roles
- **OpenAPI/Swagger** - Converts to/from OpenAPI specs
- **JSON Schema** - Validates against schemas

---

## Error Handling

### Common YAML Errors Fixed

| Error | Cause | Agent Fix |
|-------|-------|-----------|
| `mapping values are not allowed here` | Incorrect indentation | Aligns keys properly |
| `found duplicate key` | Same key twice | Removes or renames duplicate |
| `expected <block end>, but found` | Tab instead of spaces | Replaces tabs with spaces |
| `found undefined tag handle` | Custom tag without definition | Defines tag or removes |
| `could not find expected ':'` | Missing colon | Adds colon after key |

---

## Best Practices Enforced

1. **Indentation**: Consistent 2-space indentation
2. **Quotes**: Minimal quoting (only when necessary)
3. **Comments**: Descriptive comments for complex sections
4. **Security**: No hardcoded secrets, use secrets managers
5. **Validation**: Always validate against schemas
6. **Documentation**: Inline docs for anchors/aliases
7. **Versioning**: Explicit version tags (Docker Compose, K8s API)

---

## Advanced Features

### Multi-Document YAML

Handles YAML files with multiple documents:

```yaml
---
apiVersion: v1
kind: Service
---
apiVersion: apps/v1
kind: Deployment
---
```

Validates each document independently and ensures consistency.

### Environment-Specific Configurations

Manages environment overrides and templates:

```yaml
# base.yaml
database: &db
  host: localhost

# production.yaml
database:
  <<: *db
  host: prod-db.example.com
  ssl: true
```

### Complex Data Types

Supports advanced YAML types:
- Timestamps
- Binary data (base64)
- Null values
- Custom tags

---

## Compliance & Standards

✅ **YAML 1.2 Specification**: Fully compliant
✅ **YAML 1.1**: Backward compatible
✅ **JSON Schema Draft 7**: Supports validation
✅ **OpenAPI 3.1**: Compatible with specs
✅ **Kubernetes API**: Validates all stable APIs
✅ **Docker Compose v3.8**: Full support

---

## Troubleshooting

### Issue: "YAML won't parse"

**Diagnosis**:
1. Check indentation (tabs vs spaces)
2. Verify key-value separator (`:` with space)
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

## Performance

- **Large Files**: Streams YAML instead of loading into memory
- **Validation**: Incremental validation for real-time feedback
- **Conversion**: Optimized parsers for fast format conversion
- **Caching**: Caches schema validation results

---

## Examples by Complexity

### Beginner: Simple Config

```yaml
app:
  name: MyApp
  version: 1.0.0

server:
  host: 0.0.0.0
  port: 8080
```

### Intermediate: Docker Compose

```yaml
version: '3.8'
services:
  web:
    build: ./web
    ports:
      - "3000:3000"
    depends_on:
      - api
  api:
    build: ./api
    environment:
      DATABASE_URL: postgres://db:5432/app
```

### Advanced: Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: web
        image: myapp:latest
        resources:
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
```

---

## Changelog

### v1.0.0 (2025-10-24)

**Initial Release**:
- ✅ Intelligent YAML validation
- ✅ Schema inference and generation
- ✅ Format conversion (JSON/TOML/XML)
- ✅ Kubernetes manifest expertise
- ✅ Docker Compose optimization
- ✅ CI/CD pipeline intelligence
- ✅ Linting and style enforcement
- ✅ Anchors/aliases mastery
- ✅ Anthropic Spec v1.0 compliant

---

## Contributing

This plugin is part of the [Claude Code Plugins Plus](https://github.com/jeremylongshore/claude-code-plugins-plus) collection.

**Ideas for enhancements**:
- YAML diff visualization
- Helm chart validation
- Ansible vault integration
- Real-time collaborative YAML editing
- YAML to Terraform HCL conversion

---

## License

MIT License - See LICENSE file

---

## Support

- **Issues**: [GitHub Issues](https://github.com/jeremylongshore/claude-code-plugins-plus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jeremylongshore/claude-code-plugins-plus/discussions)
- **Documentation**: This README + [SKILL.md](skills/yaml-master/SKILL.md)

---

## Credits

**Author**: Jeremy Longshore
**Plugin**: 002-jeremy-yaml-master-agent
**Spec Compliance**: Anthropic Agent Skills Spec v1.0

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
