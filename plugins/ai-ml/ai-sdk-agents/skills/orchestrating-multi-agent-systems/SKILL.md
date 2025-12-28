---
name: orchestrating-multi-agent-systems
description: |
  Orchestrate multi-agent systems with handoffs, routing, and workflows across AI providers.
  Use when building complex AI systems requiring agent collaboration, task delegation, or workflow coordination.
  Trigger with phrases like "create multi-agent system", "orchestrate agents", or "coordinate agent workflows".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(npm:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Ai Sdk Agents

This skill provides automated assistance for ai sdk agents tasks.

## Prerequisites

Before using this skill, ensure you have:
- Node.js 18+ installed for TypeScript agent development
- AI SDK v5 package installed (`npm install ai`)
- API keys for AI providers (OpenAI, Anthropic, Google, etc.)
- Understanding of agent-based architecture patterns
- TypeScript knowledge for agent implementation
- Project directory structure for multi-agent systems

## Instructions

### Step 1: Initialize Project Structure
Set up the foundation for your multi-agent system:
1. Create project directory with necessary subdirectories
2. Initialize npm project with TypeScript configuration
3. Install AI SDK v5 and provider-specific packages
4. Set up configuration files for agent orchestration

### Step 2: Define Agent Roles
Identify and specify specialized agents needed:
- Determine agent responsibilities and capabilities
- Define agent system prompts with clear instructions
- Specify tools each agent can access
- Establish agent communication protocols

### Step 3: Implement Agents
Create individual agent files with proper configuration:
1. Write agent initialization code with AI SDK
2. Configure system prompts for agent behavior
3. Define tool functions for agent capabilities
4. Implement handoff rules for inter-agent delegation

### Step 4: Configure Orchestration
Set up coordination between agents:
- Define workflow sequences for task processing
- Implement routing logic for task distribution
- Configure handoff mechanisms between agents
- Set up state management for multi-step workflows

### Step 5: Test and Refine
Validate the multi-agent system functionality:
- Test individual agent responses and behaviors
- Verify handoff execution between agents
- Validate routing logic with different input scenarios
- Monitor coordination and identify bottlenecks

## Output

The skill generates a complete multi-agent system including:

### Project Structure
```
{baseDir}/
├── agents/
│   ├── coordinator.ts       # Main orchestration agent
│   ├── specialist-1.ts      # Domain-specific agent
│   ├── specialist-2.ts      # Domain-specific agent
│   └── [additional agents]
├── orchestration/
│   ├── workflow.ts          # Workflow definitions
│   ├── routing.ts           # Routing logic
│   └── handoffs.ts          # Handoff configurations
├── tools/
│   └── [agent tools]        # Shared tool implementations
├── config/
│   └── agents.config.ts     # Agent configurations
└── package.json             # Dependencies
```

### Agent Implementation Files
- TypeScript files with AI SDK v5 integration
- System prompts tailored to each agent role
- Tool definitions and implementations
- Handoff rules and coordination logic

### Orchestration Configuration
- Workflow definitions for task sequences
- Routing rules for intelligent task distribution
- State management for multi-step processes
- Error handling and fallback mechanisms

### Documentation
- Agent role descriptions and capabilities
- Workflow diagrams showing agent interactions
- API documentation for agent endpoints
- Usage examples for common scenarios

## Error Handling

Common issues and solutions:

**Agent Initialization Failures**
- Error: AI SDK provider configuration invalid
- Solution: Verify API keys in environment variables, check provider-specific setup requirements

**Handoff Execution Errors**
- Error: Agent handoff fails or creates circular dependencies
- Solution: Review handoff rules for clarity, implement handoff depth limits, add fallback agents

**Routing Logic Failures**
- Error: Tasks routed to incorrect agent or no agent
- Solution: Refine routing criteria, add default routing rules, implement topic classification improvement

**Tool Access Violations**
- Error: Agent attempts to use unauthorized tools
- Solution: Review tool permissions per agent, implement proper access control, validate tool configurations

**Workflow Deadlocks**
- Error: Multi-agent workflow stalls without completion
- Solution: Implement timeout mechanisms, add workflow monitoring, design escape conditions for stuck states

## Resources

### AI SDK Documentation
- AI SDK v5 official documentation for agent creation
- Provider-specific integration guides (OpenAI, Anthropic, Google)
- Tool definition and implementation examples
- Handoff and routing pattern references

### Multi-Agent Architecture Patterns
- Coordinator-worker pattern for task distribution
- Pipeline pattern for sequential processing
- Hub-and-spoke pattern for centralized coordination
- Peer-to-peer pattern for collaborative agents

### Agent Design Best Practices
- Single responsibility principle for agent specialization
- Clear handoff criteria and routing rules
- Comprehensive error handling and fallbacks
- State management for complex workflows
- Testing strategies for multi-agent systems

### Example Use Cases
- Code generation pipelines with specialized agents
- Customer support routing systems
- Research and analysis workflows
- Content creation and review pipelines
- Data processing and validation systems

## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.