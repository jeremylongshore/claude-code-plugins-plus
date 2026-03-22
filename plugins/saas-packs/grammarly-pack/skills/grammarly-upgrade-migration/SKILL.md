---
name: grammarly-upgrade-migration
description: |
description: |
  
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Upgrade & Migration

## Overview

Grammarly APIs are versioned (v1 for AI/plagiarism, v2 for scores). Monitor the developer portal for changes.

## Instructions

### Check Current Usage

```bash
grep -r 'api.grammarly.com' src/ --include='*.ts'
```

### Version-Specific Endpoints

| API | Version | Endpoint |
|-----|---------|----------|
| Writing Score | v2 | /ecosystem/api/v2/scores |
| AI Detection | v1 | /ecosystem/api/v1/ai-detection |
| Plagiarism | v1 | /ecosystem/api/v1/plagiarism |
| OAuth | v1 | /ecosystem/api/v1/oauth/token |

### Migration Pattern

```typescript
const API_VERSIONS = { scores: 'v2', aiDetection: 'v1', plagiarism: 'v1' };
const endpoint = \`https://api.grammarly.com/ecosystem/api/\${API_VERSIONS.scores}/scores\`;
```

## Resources

- [Grammarly Developer Portal](https://developer.grammarly.com/)

## Next Steps

For CI, see `grammarly-ci-integration`.
