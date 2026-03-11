---
name: vercel-architecture-variants
description: |
  Execute choose and implement Vercel validated architecture blueprints for different scales.
  Use when designing new Vercel integrations, choosing between monolith/service/microservice
  architectures, or planning migration paths for Vercel applications.
  Trigger with phrases like "vercel architecture", "vercel blueprint",
  "how to structure vercel", "vercel project layout", "vercel microservice".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vercel Architecture Variants

## Prerequisites
- Understanding of team size and DAU requirements
- Knowledge of deployment infrastructure
- Clear SLA requirements
- Growth projections available

## Instructions

### Step 1: Assess Requirements
Use the decision matrix to identify appropriate variant.

### Step 2: Choose Architecture
Select Monolith, Service Layer, or Microservice based on needs.

### Step 3: Implement Structure
Set up project layout following the chosen blueprint.

### Step 4: Plan Migration Path
Document upgrade path for future scaling.

## Output
- Architecture variant selected
- Project structure implemented
- Migration path documented
- Appropriate patterns applied

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Monolith First](https://martinfowler.com/bliki/MonolithFirst.html)
- [Microservices Guide](https://martinfowler.com/microservices/)
- [Vercel Architecture Guide](https://vercel.com/docs/architecture)
