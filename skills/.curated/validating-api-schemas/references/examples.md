# API Schema Validation Examples

## Spectral OpenAPI Linting

```yaml
# .spectral.yaml
extends: spectral:oas
rules:
  operation-operationId:
    severity: error
    description: Every operation must have an operationId
  oas3-valid-schema-example:
    severity: error
  path-casing:
    severity: warn
    given: "$.paths[*]~"
    then:
      function: casing
      functionOptions: { type: kebab }
  require-description:
    severity: warn
    given: "$.paths[*][*]"
    then:
      field: description
      function: truthy
  require-error-responses:
    severity: warn
    given: "$.paths[*][get,post,put,patch,delete].responses"
    then:
      field: "400"
      function: truthy
```

## Running Schema Validation

```bash
# Lint OpenAPI spec
npx @stoplight/spectral-cli lint openapi.yaml --fail-severity error
# Expected: No errors found

# Validate spec structure
npx swagger-cli validate openapi.yaml
# openapi.yaml is valid

# Breaking change detection
npx oasdiff breaking openapi-v1.yaml openapi-v2.yaml
# 1 breaking change found:
#   GET /users - removed required property 'name' from response

# JSON Schema validation
npx ajv validate -s schema.json -d data.json
```

## Schema Completeness Audit Script

```javascript
// scripts/audit-schema.js
const yaml = require('js-yaml');
const fs = require('fs');

const spec = yaml.load(fs.readFileSync('openapi.yaml'));
const report = [];

for (const [path, methods] of Object.entries(spec.paths)) {
  for (const [method, op] of Object.entries(methods)) {
    if (typeof op !== 'object') continue;
    const checks = {
      path: `${method.toUpperCase()} ${path}`,
      hasDescription: !!op.description,
      hasOperationId: !!op.operationId,
      has200Schema: !!op.responses?.['200']?.content,
      has400Schema: !!op.responses?.['400'],
      has401Schema: !!op.responses?.['401'],
      hasExamples: !!(op.responses?.['200']?.content?.['application/json']?.example),
    };
    const score = Object.values(checks).filter(Boolean).length - 1; // -1 for path
    report.push({ ...checks, score, maxScore: 6 });
  }
}

console.table(report);
const total = report.reduce((s, r) => s + r.score, 0);
const max = report.reduce((s, r) => s + r.maxScore, 0);
console.log(`Coverage: ${Math.round(total / max * 100)}%`);
```

## Audit Output

```
| Path              | description | operationId | 200 | 400 | 401 | examples | score |
|-------------------|------------|-------------|-----|-----|-----|----------|-------|
| GET /users        | yes        | yes         | yes | yes | yes | yes      | 6/6   |
| POST /users       | yes        | yes         | yes | yes | yes | no       | 5/6   |
| GET /users/:id    | yes        | yes         | yes | no  | yes | yes      | 5/6   |
| DELETE /users/:id | no         | yes         | yes | no  | yes | no       | 3/6   |
Coverage: 79%
```

## Breaking Change Detection

```javascript
// scripts/check-breaking-changes.js
const { diff } = require('openapi-diff');

async function checkBreakingChanges(oldSpec, newSpec) {
  const result = await diff(oldSpec, newSpec);

  const breaking = result.breakingDifferences || [];
  const nonBreaking = result.nonBreakingDifferences || [];

  if (breaking.length > 0) {
    console.error('BREAKING CHANGES DETECTED:');
    for (const change of breaking) {
      console.error(`  - ${change.type}: ${change.sourceSpecEntityDetails[0]?.location}`);
      console.error(`    ${change.details}`);
    }
    process.exit(1);
  }

  console.log(`Non-breaking changes: ${nonBreaking.length}`);
  console.log('No breaking changes detected');
}

checkBreakingChanges('./specs/openapi-v1.yaml', './specs/openapi-v2.yaml');
```

## CI Schema Validation Script

```bash
#!/bin/bash
set -e

echo "=== Schema Validation ==="

# Structural validation
npx swagger-cli validate openapi.yaml
echo "Structure: PASS"

# Linting
npx @stoplight/spectral-cli lint openapi.yaml --fail-severity error
echo "Linting: PASS"

# Breaking changes (compare against main branch)
if git show main:openapi.yaml > /tmp/openapi-main.yaml 2>/dev/null; then
  npx oasdiff breaking /tmp/openapi-main.yaml openapi.yaml
  echo "Breaking changes: PASS"
fi

# Completeness audit
node scripts/audit-schema.js
echo "=== All checks passed ==="
```

## Naming Convention Check

```javascript
function checkNamingConventions(spec) {
  const issues = [];

  for (const path of Object.keys(spec.paths)) {
    if (path !== path.toLowerCase().replace(/[A-Z]/g, '-$&').toLowerCase()) {
      issues.push({ path, issue: 'Path should be kebab-case' });
    }
  }

  for (const [name, schema] of Object.entries(spec.components?.schemas || {})) {
    for (const prop of Object.keys(schema.properties || {})) {
      if (prop !== prop.replace(/[A-Z]/g, (m, i) => i ? m : m.toLowerCase())) {
        // Not camelCase - skip complex check, just flag snake_case
        if (prop.includes('_')) {
          issues.push({ schema: name, property: prop, issue: 'Property should be camelCase' });
        }
      }
    }
  }

  return issues;
}
```

## GraphQL Schema Validation

```bash
# Lint GraphQL SDL
npx graphql-schema-linter schema.graphql \
  --rules fields-have-descriptions,types-have-descriptions,deprecations-have-a-reason

# Validate query against schema
npx graphql-inspector validate query.graphql schema.graphql

# Detect breaking changes
npx graphql-inspector diff old-schema.graphql new-schema.graphql
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
