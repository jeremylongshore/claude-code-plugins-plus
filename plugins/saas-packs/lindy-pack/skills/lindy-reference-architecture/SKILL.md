---
name: lindy-reference-architecture
description: |
  Reference architectures for Lindy AI integrations.
  Use when designing systems, planning architecture,
  or implementing production patterns.
  Trigger with phrases like "lindy architecture", "lindy design",
  "lindy system design", "lindy patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy Reference Architecture

## Overview
Production-ready reference architectures for Lindy AI integrations covering basic integration, event-driven, multi-agent orchestration, and high-availability patterns.

## Prerequisites
- Understanding of system design principles
- Familiarity with cloud services
- Production requirements defined

## Instructions

### Step 1: Choose Architecture Pattern
Select based on requirements: Basic (simple request/response), Event-driven (async with queues), Multi-agent (orchestrated pipelines), or HA (failover and caching).

### Step 2: Implement Basic Integration
Set up Express backend with Lindy SDK for simple synchronous agent interactions.

### Step 3: Add Event-Driven Processing (if needed)
Use BullMQ workers to process agent tasks asynchronously from a queue, emitting results on completion.

### Step 4: Set Up Multi-Agent Orchestration (if needed)
Build an orchestrator that plans work, delegates to specialized agents (research, analysis, writing), and synthesizes results.

### Step 5: Configure High Availability (if needed)
Create an HA client with primary/fallback Lindy instances and Redis caching for automatic failover.

For detailed implementation code and architecture diagrams, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Architecture pattern selection guide
- Basic integration implementation
- Event-driven worker setup
- Multi-agent orchestration
- HA client with failover

## Error Handling
| Pattern | Failure Mode | Recovery |
|---------|--------------|----------|
| Basic | API error | Retry with backoff |
| Event-driven | Worker crash | Queue retry |
| Multi-agent | Step failure | Skip or fallback |
| HA | Primary down | Automatic failover |

## Resources
- [Lindy Architecture Guide](https://docs.lindy.ai/architecture)
- [Best Practices](https://docs.lindy.ai/best-practices)
- [Case Studies](https://lindy.ai/case-studies)

## Next Steps
Proceed to Flagship tier skills for enterprise features.

## Examples

**Basic usage**: Apply lindy reference architecture to a standard project setup with default configuration options.

**Advanced scenario**: Customize lindy reference architecture for production environments with multiple constraints and team-specific requirements.