---
name: juicebox-reference-architecture
description: |
  Implement Juicebox reference architecture.
  Use when designing system architecture, planning integrations,
  or implementing enterprise-grade Juicebox solutions.
  Trigger with phrases like "juicebox architecture", "juicebox design",
  "juicebox system design", "juicebox enterprise".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Reference Architecture

## Overview
Enterprise-grade reference architecture for Juicebox-powered recruiting and people search applications.

## Instructions
1. Architecture Patterns
2. Implementation
3. Deployment Topology

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Architecture diagrams
- Core service implementations
- Database schema
- Kubernetes manifests

## Resources
- [Architecture Guide](https://juicebox.ai/docs/architecture)
- [Enterprise Patterns](https://juicebox.ai/docs/enterprise)

## Next Steps
After architecture setup, see `juicebox-multi-env-setup` for environment configuration.

## Prerequisites

- Access to the design environment or API
- Required CLI tools installed and authenticated
- Familiarity with design concepts and terminology

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with design |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply juicebox reference architecture to a standard project setup with default configuration options.

**Advanced scenario**: Customize juicebox reference architecture for production environments with multiple constraints and team-specific requirements.