---
name: gcp-examples-expert
description: |
  Generate production-ready Google Cloud code examples from official repositories including ADK samples, Genkit templates, Vertex AI notebooks, and Gemini patterns. Use when asked to "show ADK example" or "provide GCP starter kit". Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Gcp Examples Expert

This skill provides automated assistance for gcp examples expert tasks.

## What This Skill Does

Expert aggregator of production-ready code examples from official Google Cloud repositories. Provides battle-tested starter kits, templates, and best practices for building AI agents, workflows, and applications on Google Cloud Platform.

## When This Skill Activates

### Trigger Phrases
- "Show me ADK sample code"
- "Genkit starter template"
- "Vertex AI code example"
- "Agent Starter Pack template"
- "Gemini function calling example"
- "Multi-agent orchestration pattern"
- "Google Cloud starter kit"
- "Production agent template"
- "How to implement RAG with Genkit"
- "A2A protocol code example"

### Use Cases
- Quick access to official Google Cloud code examples
- Production-ready agent templates
- Genkit flow patterns (RAG, multi-step workflows, tool calling)
- Vertex AI training and deployment code
- Gemini API integration examples
- Multi-agent system orchestration
- Infrastructure as Code (Terraform) templates

## Code Example Categories

### 1. ADK (Agent Development Kit) Samples

**Source**: google/adk-samples

**Examples Provided**:
- Basic agent creation with Code Execution Sandbox
- Memory Bank configuration for stateful agents
- A2A protocol implementation for inter-agent communication
- Multi-tool agent configuration
- VPC Service Controls integration
- IAM least privilege patterns

**Sample Pattern**:
```python
from google.cloud.aiplatform import agent_builder

def create_adk_agent(project_id: str, location: str):
    agent_config = {
        "display_name": "production-agent",
        "model": "gemini-2.5-flash",
        "code_execution_config": {
            "enabled": True,
            "state_ttl_days": 14
        },
        "memory_bank_config": {
            "enabled": True
        }
    }
    # Implementation from google/adk-samples
```

### 2. Agent Starter Pack

**Source**: GoogleCloudPlatform/agent-starter-pack

**Examples Provided**:
- Production agent with monitoring and observability
- Auto-scaling configuration
- Security best practices (Model Armor, VPC-SC)
- Cloud Monitoring dashboards
- Alerting policies
- Error tracking setup

**Sample Pattern**:
```python
def production_agent_with_observability(project_id: str):
    agent = aiplatform.Agent.create(
        config={
            "auto_scaling": {
                "min_instances": 2,
                "max_instances": 10
            },
            "vpc_service_controls": {"enabled": True},
            "model_armor": {"enabled": True}
        }
    )
    # Full implementation from agent-starter-pack
```

### 3. Firebase Genkit

**Source**: firebase/genkit

**Examples Provided**:
- RAG flows with vector search
- Multi-step workflows
- Tool calling integration
- Prompt templates
- Evaluation frameworks
- Deployment patterns (Cloud Run, Functions)

**Sample Pattern**:
```typescript
import { genkit, z } from 'genkit';
import { googleAI, gemini15ProLatest } from '@genkit-ai/googleai';

const ragFlow = ai.defineFlow({
  name: 'ragSearchFlow',
  inputSchema: z.object({ query: z.string() }),
  outputSchema: z.object({ answer: z.string() })
}, async (input) => {
  // Implementation from firebase/genkit examples
});
```

### 4. Vertex AI Samples

**Source**: GoogleCloudPlatform/vertex-ai-samples

**Examples Provided**:
- Custom model training with Gemini
- Batch prediction jobs
- Hyperparameter tuning
- Model evaluation
- Endpoint deployment with auto-scaling
- A/B testing patterns

**Sample Pattern**:
```python
def fine_tune_gemini_model(project_id: str, training_data_uri: str):
    job = aiplatform.CustomTrainingJob(
        training_config={
            "base_model": "gemini-2.5-flash",
            "learning_rate": 0.001,
            "adapter_size": 8  # LoRA
        }
    )
    # Full implementation from vertex-ai-samples
```

### 5. Generative AI Examples

**Source**: GoogleCloudPlatform/generative-ai

**Examples Provided**:
- Gemini multimodal analysis (text, images, video)
- Function calling with live APIs
- Structured output generation
- Grounding with Google Search
- Safety filters and content moderation
- Token counting and cost optimization

**Sample Pattern**:
```python
from vertexai.generative_models import GenerativeModel, Part

def analyze_multimodal_content(video_uri: str, question: str):
    model = GenerativeModel("gemini-2.5-pro")
    video_part = Part.from_uri(video_uri, mime_type="video/mp4")
    response = model.generate_content([video_part, question])
    # Implementation from generative-ai examples
```

### 6. AgentSmithy

**Source**: GoogleCloudPlatform/agentsmithy

**Examples Provided**:
- Multi-agent orchestration
- Supervisory agent patterns
- Agent-to-agent communication
- Workflow coordination (sequential, parallel, conditional)
- Task delegation strategies
- Error handling and retry logic

**Sample Pattern**:
```python
from agentsmithy import Agent, Orchestrator, Task

def create_multi_agent_system(project_id: str):
    orchestrator = Orchestrator(
        agents=[research_agent, analysis_agent, writer_agent],
        strategy="sequential"
    )
    # Full implementation from agentsmithy
```

## Workflow

### Phase 1: Identify Use Case
```
1. Listen for trigger phrases in user request
2. Determine which repository has relevant examples
3. Identify specific code pattern needed
4. Select appropriate framework (ADK, Genkit, Vertex AI)
```

### Phase 2: Provide Code Example
```
1. Fetch relevant code snippet from knowledge base
2. Adapt to user's specific requirements
3. Include imports and dependencies
4. Add configuration details
5. Cite source repository
```

### Phase 3: Explain Best Practices
```
1. Highlight security considerations (IAM, VPC-SC, Model Armor)
2. Show monitoring and observability setup
3. Demonstrate error handling patterns
4. Include infrastructure deployment code
5. Provide cost optimization tips
```

### Phase 4: Deployment Guidance
```
1. Provide Terraform/IaC templates
2. Show Cloud Build CI/CD configuration
3. Include testing strategies
4. Document environment variables
5. Link to official documentation
```

## Tool Permissions

This skill uses the following tools:
- **Read**: Access code examples and documentation
- **Write**: Create starter template files
- **Edit**: Modify templates for user's project
- **Grep**: Search for specific patterns in examples
- **Glob**: Find related code files
- **Bash**: Run setup commands and validation

## Example Interactions

### Example 1: ADK Agent Creation
**User**: "Show me how to create an ADK agent with Code Execution"

**Skill Activates**:
- Provides code example from google/adk-samples
- Includes Code Execution Sandbox configuration
- Shows 14-day state persistence setup
- Demonstrates security best practices
- Links to official ADK documentation

### Example 2: Genkit RAG Flow
**User**: "I need a Genkit starter template for RAG"

**Skill Activates**:
- Provides RAG flow code from firebase/genkit
- Shows vector search integration
- Demonstrates embedding generation
- Includes context retrieval logic
- Provides deployment configuration

### Example 3: Production Agent Template
**User**: "What's the best way to deploy a production agent?"

**Skill Activates**:
- Provides Agent Starter Pack template
- Shows auto-scaling configuration
- Includes monitoring dashboard setup
- Demonstrates alerting policies
- Provides Terraform deployment code

### Example 4: Gemini Multimodal
**User**: "How do I analyze video with Gemini?"

**Skill Activates**:
- Provides multimodal code from generative-ai repo
- Shows video part creation
- Demonstrates prompt engineering
- Includes error handling
- Provides cost optimization tips

### Example 5: Multi-Agent System
**User**: "I want to build a multi-agent system"

**Skill Activates**:
- Provides AgentSmithy orchestration code
- Shows supervisory agent pattern
- Demonstrates A2A protocol usage
- Includes workflow coordination
- Provides testing strategies

## Best Practices Applied

### Security
✅ IAM least privilege service accounts
✅ VPC Service Controls for enterprise isolation
✅ Model Armor for prompt injection protection
✅ Encrypted data at rest and in transit
✅ No hardcoded credentials (use Secret Manager)

### Performance
✅ Auto-scaling configuration (min/max instances)
✅ Appropriate machine types and accelerators
✅ Caching strategies for repeated queries
✅ Batch processing for high throughput
✅ Token optimization for cost efficiency

### Observability
✅ Cloud Monitoring dashboards
✅ Alerting policies for errors and latency
✅ Structured logging with severity levels
✅ Distributed tracing with Cloud Trace
✅ Error tracking with Cloud Error Reporting

### Reliability
✅ Multi-region deployment for high availability
✅ Circuit breaker patterns for fault tolerance
✅ Retry logic with exponential backoff
✅ Health check endpoints
✅ Graceful degradation strategies

### Cost Optimization
✅ Use Gemini 2.5 Flash for simple tasks (cheaper)
✅ Gemini 2.5 Pro for complex reasoning (higher quality)
✅ Batch predictions for bulk processing
✅ Preemptible instances for non-critical workloads
✅ Token counting to estimate costs

## Integration with Other Plugins

### Works with jeremy-genkit-pro
- Provides Genkit code examples
- Complements Genkit flow architect agent
- Shares Genkit production best practices

### Works with jeremy-adk-orchestrator
- Provides ADK sample code
- Shows A2A protocol implementation
- Demonstrates multi-agent patterns

### Works with jeremy-vertex-validator
- Provides production-ready code that passes validation
- Follows security and performance best practices
- Includes monitoring from the start

### Works with jeremy-*-terraform plugins
- Provides infrastructure code examples
- Shows Terraform module patterns
- Demonstrates resource configuration

## Version History

- **1.0.0** (2025): Initial release with 6 official Google Cloud repository integrations

## References

- **google/adk-samples**: https://github.com/google/adk-samples
- **GoogleCloudPlatform/agent-starter-pack**: https://github.com/GoogleCloudPlatform/agent-starter-pack
- **firebase/genkit**: https://github.com/firebase/genkit
- **GoogleCloudPlatform/vertex-ai-samples**: https://github.com/GoogleCloudPlatform/vertex-ai-samples
- **GoogleCloudPlatform/generative-ai**: https://github.com/GoogleCloudPlatform/generative-ai
- **GoogleCloudPlatform/agentsmithy**: https://github.com/GoogleCloudPlatform/agentsmithy

## Overview

This skill provides automated assistance for the described functionality.

## Prerequisites

- Appropriate file access permissions
- Required dependencies installed

## Instructions

1. Invoke this skill when the trigger conditions are met
2. Provide necessary context and parameters
3. Review the generated output
4. Apply modifications as needed

## Output

The skill produces structured output relevant to the task.

## Error Handling

- Invalid input: Prompts for correction
- Missing dependencies: Lists required components
- Permission errors: Suggests remediation steps

## Examples

Example usage patterns will be demonstrated in context.

## Resources

- Project documentation
- Related skills and commands
