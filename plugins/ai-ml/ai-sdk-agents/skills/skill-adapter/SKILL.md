---
name: Orchestrating Multi-Agent Systems
description: |
  This skill enables Claude to orchestrate multi-agent systems using the AI SDK v5. It allows Claude to set up agent handoffs, intelligent routing, and coordinated workflows across different AI providers like OpenAI, Anthropic, and Google. Use this skill when the user asks to create multi-agent systems, needs help with agent coordination, task routing, or wants to build complex workflows involving specialized agents. It is triggered by phrases like "multi-agent system", "agent orchestration", "agent handoff", "intelligent routing", or "coordinate agents".
---

## Overview

This skill empowers Claude to create and manage sophisticated multi-agent systems. It leverages the AI SDK v5 to facilitate agent collaboration, task delegation, and intelligent routing, enabling the creation of complex AI-powered workflows.

## How It Works

1. **Project Initialization**: The skill sets up a basic multi-agent project structure, including agent files and orchestration configurations.
2. **Agent Creation**: It facilitates the creation of specialized agents with custom system prompts, tool definitions, and handoff rules.
3. **Orchestration Configuration**: It configures the agent orchestration workflow, defining how agents interact and pass tasks to each other.

## When to Use This Skill

This skill activates when you need to:
- Create a new multi-agent system from scratch.
- Orchestrate existing agents to perform a complex task.
- Define handoff rules between agents.
- Route tasks intelligently to the most appropriate agent.
- Coordinate a workflow involving multiple LLMs.

## Examples

### Example 1: Building a Code Generation Pipeline

User request: "Set up a multi-agent system for code generation with an architect, coder, tester, reviewer, and documenter."

The skill will:
1. Initialize a multi-agent project with the specified agents.
2. Create individual agent files (architect.ts, coder.ts, etc.) with relevant system prompts and tool access.
3. Configure an orchestration workflow to pass tasks between the agents in the order: Architect -> Coder -> Tester -> Reviewer -> Documenter.

### Example 2: Intelligent Routing for Customer Support

User request: "Create a multi-agent system for customer support that routes inquiries to the appropriate agent based on the topic."

The skill will:
1. Initialize a multi-agent project with a coordinator agent and specialized support agents (e.g., billing, technical support, sales).
2. Configure the coordinator agent with routing rules based on topic classification.
3. Implement handoff mechanisms for agents to transfer inquiries if needed.

## Best Practices

- **Agent Specialization**: Design agents with specific expertise and limited scope for better performance.
- **Clear Handoff Rules**: Define clear and unambiguous handoff rules to avoid confusion and circular dependencies.
- **Comprehensive Testing**: Thoroughly test the multi-agent system to ensure proper coordination and task completion.

## Integration

This skill integrates seamlessly with other Claude Code plugins, allowing you to combine multi-agent orchestration with other functionalities like code generation, data analysis, and external API integrations. It leverages the AI SDK v5 for robust and flexible agent management.