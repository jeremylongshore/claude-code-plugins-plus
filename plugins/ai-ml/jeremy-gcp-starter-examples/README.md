# Jeremy GCP Starter Examples

Comprehensive Google Cloud starter kit examples aggregator. Expert in ADK samples, Genkit templates, Agent Starter Pack, Vertex AI examples, and production-ready code from official Google Cloud repositories.

## Overview

This plugin provides instant access to production-ready code examples from 6 official Google Cloud repositories, helping developers quickly implement AI agents, workflows, and applications on Google Cloud Platform.

## Installation

```bash
/plugin install jeremy-gcp-starter-examples@claude-code-plugins-plus
```

## Features

✅ **ADK Sample Code**: Agent creation, Code Execution Sandbox, Memory Bank
✅ **Agent Starter Pack**: Production templates with monitoring and security
✅ **Genkit Flows**: RAG, multi-step workflows, tool calling patterns
✅ **Vertex AI Samples**: Model training, batch prediction, deployment
✅ **Gemini Examples**: Multimodal analysis, function calling, structured output
✅ **AgentSmithy Patterns**: Multi-agent orchestration and coordination

## Components

### Agent
- **gcp-starter-kit-expert**: Aggregates code examples from official Google Cloud repos

### Skills (Auto-Activating)
- **gcp-examples-expert**: Triggers on "show adk example", "genkit starter template", "vertex ai code sample"
  - **Tool Permissions**: Read, Write, Edit, Grep, Glob, Bash
  - **Version**: 1.0.0 (2025 schema compliant)

## Quick Start

### Natural Language Activation

Simply mention what you need:

```
"Show me ADK sample code for creating an agent"
"I need a Genkit starter template for RAG"
"How do I implement Gemini function calling?"
"Show me Agent Starter Pack production template"
"Vertex AI code example for model training"
"Multi-agent orchestration pattern with AgentSmithy"
```

The skill auto-activates and provides production-ready code examples.

## Code Example Categories

### 1. ADK (Agent Development Kit) Samples

**Source**: google/adk-samples

- Basic agent creation with Code Execution Sandbox (14-day state persistence)
- Memory Bank configuration for persistent conversation memory
- A2A protocol implementation for inter-agent communication
- Multi-tool agent configuration
- VPC Service Controls integration
- IAM least privilege patterns

**Example Request**:
```
"Show me how to create an ADK agent with Code Execution and Memory Bank"
```

### 2. Agent Starter Pack Templates

**Source**: GoogleCloudPlatform/agent-starter-pack

- Production agent with comprehensive monitoring
- Auto-scaling configuration (min/max instances)
- Security best practices (Model Armor, VPC-SC, IAM)
- Cloud Monitoring dashboards
- Alerting policies for errors and latency
- Error tracking and distributed tracing

**Example Request**:
```
"Give me the Agent Starter Pack production template"
```

### 3. Firebase Genkit Flows

**Source**: firebase/genkit

- RAG flows with vector search and embeddings
- Multi-step workflows with tool calling
- Prompt templates and evaluation frameworks
- Deployment patterns (Cloud Run, Cloud Functions)
- Node.js, Python, and Go examples

**Example Request**:
```
"I need a Genkit RAG flow template with vector search"
```

### 4. Vertex AI Training & Deployment

**Source**: GoogleCloudPlatform/vertex-ai-samples

- Custom model fine-tuning with Gemini
- Batch prediction jobs for bulk inference
- Hyperparameter tuning with Vertex AI
- Model evaluation and monitoring
- Endpoint deployment with auto-scaling
- A/B testing and traffic splitting

**Example Request**:
```
"Show me how to fine-tune Gemini on custom data"
```

### 5. Gemini API Integration

**Source**: GoogleCloudPlatform/generative-ai

- Multimodal analysis (text, images, video)
- Function calling with live API integration
- Structured output generation with schemas
- Grounding with Google Search
- Safety filters and content moderation
- Token counting and cost optimization

**Example Request**:
```
"How do I analyze video content with Gemini multimodal?"
```

### 6. Multi-Agent Orchestration

**Source**: GoogleCloudPlatform/agentsmithy

- Multi-agent system coordination
- Supervisory agent patterns
- Agent-to-agent communication (A2A protocol)
- Workflow strategies (sequential, parallel, conditional)
- Task delegation and error handling
- Retry logic with exponential backoff

**Example Request**:
```
"I want to build a multi-agent system with AgentSmithy"
```

## Use Cases

### Quick Prototyping
Get production-ready code to start building immediately without searching through documentation.

### Learning Best Practices
See how Google Cloud engineers implement security, monitoring, and scalability in official examples.

### Production Templates
Use battle-tested patterns from Agent Starter Pack for production deployments.

### Framework Comparison
Compare ADK, Genkit, and Vertex AI implementations to choose the right framework.

### Infrastructure as Code
Get Terraform templates for deploying agents and infrastructure.

## Integration with Other Plugins

### jeremy-genkit-pro
- Provides Genkit code examples
- Complements Genkit flow architect agent
- Shares production best practices

### jeremy-adk-orchestrator
- Provides ADK sample code
- Shows A2A protocol implementation
- Demonstrates multi-agent patterns

### jeremy-vertex-validator
- Provides code that passes production validation
- Follows security and performance best practices
- Includes monitoring from the start

### jeremy-*-terraform plugins
- Provides infrastructure code examples
- Shows Terraform module patterns
- Demonstrates resource configuration

## Example Workflows

### Workflow 1: Build ADK Agent

```
User: "Show me ADK code for an agent with Code Execution"

Plugin provides:
1. Agent creation code from google/adk-samples
2. Code Execution Sandbox configuration (14-day TTL)
3. Security best practices (IAM, VPC-SC)
4. Monitoring setup
5. Deployment commands
```

### Workflow 2: Implement Genkit RAG

```
User: "I need a Genkit RAG flow template"

Plugin provides:
1. RAG flow code from firebase/genkit
2. Vector search integration
3. Embedding generation
4. Context retrieval logic
5. Deployment to Cloud Run
```

### Workflow 3: Production Agent Deployment

```
User: "How do I deploy a production agent?"

Plugin provides:
1. Agent Starter Pack template
2. Auto-scaling configuration
3. Monitoring dashboard code
4. Alerting policy setup
5. Terraform deployment code
```

## Best Practices Included

### Security
- IAM least privilege service accounts
- VPC Service Controls for enterprise isolation
- Model Armor for prompt injection protection
- Encrypted data at rest and in transit
- No hardcoded credentials (Secret Manager)

### Performance
- Auto-scaling (min/max instances)
- Appropriate machine types and accelerators
- Caching strategies
- Batch processing
- Token optimization

### Observability
- Cloud Monitoring dashboards
- Alerting policies
- Structured logging
- Distributed tracing
- Error tracking

### Reliability
- Multi-region deployment
- Circuit breaker patterns
- Retry logic with exponential backoff
- Health check endpoints
- Graceful degradation

### Cost Optimization
- Gemini 2.5 Flash for simple tasks
- Gemini 2.5 Pro for complex reasoning
- Batch predictions for bulk processing
- Preemptible instances
- Token counting

## Official Repositories Referenced

This plugin aggregates code from these official Google Cloud repositories:

1. **google/adk-samples** - ADK agent examples and patterns
2. **GoogleCloudPlatform/agent-starter-pack** - Production agent templates
3. **firebase/genkit** - Genkit flows and integrations
4. **GoogleCloudPlatform/vertex-ai-samples** - Vertex AI notebooks and code
5. **GoogleCloudPlatform/generative-ai** - Gemini API examples
6. **GoogleCloudPlatform/agentsmithy** - Multi-agent orchestration

## Requirements

- Google Cloud Project with Vertex AI enabled
- Appropriate IAM permissions for agent creation
- gcloud CLI configured (for deployment)
- Node.js 20+ (for Genkit examples)
- Python 3.10+ (for ADK/Vertex AI examples)

## License

MIT

## Support

- Issues: https://github.com/jeremylongshore/claude-code-plugins/issues
- Discussions: https://github.com/jeremylongshore/claude-code-plugins/discussions

## Version

1.0.0 (2025) - Initial release with 6 official Google Cloud repository integrations
