# Lindy Core Workflow A - Implementation Guide

# Lindy Core Workflow A: Agent Creation

## Overview
Complete workflow for creating, configuring, and deploying Lindy AI agents.

## Prerequisites
- Completed `lindy-install-auth` setup
- Understanding of agent use case
- Clear instructions/persona defined

## Instructions

### Step 1: Define Agent Specification
```typescript
interface AgentSpec {
  name: string;
  description: string;
  instructions: string;
  tools: string[];
  model?: string;
  temperature?: number;
}

const agentSpec: AgentSpec = {
  name: 'Customer Support Agent',
  description: 'Handles customer inquiries and support tickets',
  instructions: `
    You are a helpful customer support agent.
    - Be polite and professional
    - Ask clarifying questions when needed
    - Escalate complex issues to human support
    - Always confirm resolution with the customer
  `,
  tools: ['email', 'calendar', 'knowledge-base'],
  model: 'gpt-4',
  temperature: 0.7,
};
```

### Step 2: Create the Agent
```typescript
import { Lindy } from '@lindy-ai/sdk';

const lindy = new Lindy({ apiKey: process.env.LINDY_API_KEY });

async function createAgent(spec: AgentSpec) {
  const agent = await lindy.agents.create({
    name: spec.name,
    description: spec.description,
    instructions: spec.instructions,
    tools: spec.tools,
    config: {
      model: spec.model || 'gpt-4',
      temperature: spec.temperature || 0.7,
    },
  });

  console.log(`Created agent: ${agent.id}`);
  return agent;
}
```

### Step 3: Configure Agent Tools
```typescript
async function configureTools(agentId: string, tools: string[]) {
  for (const tool of tools) {
    await lindy.agents.addTool(agentId, {
      name: tool,
      enabled: true,
    });
  }
  console.log(`Configured ${tools.length} tools`);
}
```

### Step 4: Test the Agent
```typescript
async function testAgent(agentId: string) {
  const testCases = [
    'Hello, I need help with my order',
    'Can you check my subscription status?',
    'I want to cancel my account',
  ];

  for (const input of testCases) {
    const result = await lindy.agents.run(agentId, { input });
    console.log(`Input: ${input}`);
    console.log(`Output: ${result.output}\n`);
  }
}
```

## Output
- Fully configured AI agent
- Connected tools and integrations
- Tested agent responses
- Ready for deployment

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Tool not found | Invalid tool name | Check available tools list |
| Instructions too long | Exceeds limit | Summarize or split instructions |
| Model unavailable | Unsupported model | Use default gpt-4 |

## Examples

### Complete Agent Creation Flow
```typescript
async function main() {
  // Create agent
  const agent = await createAgent(agentSpec);

  // Configure tools
  await configureTools(agent.id, agentSpec.tools);

  // Test agent
  await testAgent(agent.id);

  console.log(`Agent ${agent.id} is ready!`);
}

main().catch(console.error);
```

## Resources
- [Lindy Agent Creation](https://docs.lindy.ai/agents/create)
- [Available Tools](https://docs.lindy.ai/tools)
- [Model Options](https://docs.lindy.ai/models)

## Next Steps
Proceed to `lindy-core-workflow-b` for task automation workflows.
