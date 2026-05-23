# Google Cloud Agent SDK — Skill References

## Overview

This directory contains reference materials for the Google Cloud Agent SDK Master skill,
covering ADK (Agent Development Kit) patterns, Agent Starter Pack templates, deployment
targets, and production best practices.

## Reference Files

### SKILL.full.md

The comprehensive guide containing:

- ADK framework overview and supported agent types (LLM, Workflow, Custom, Multi-agent)
- Agent Starter Pack templates (adk_base, agentic_rag, langgraph_base_react, crewai_coding_crew, adk_live)
- Deployment targets: Vertex AI Agent Engine, Cloud Run, GKE, Local/Docker
- Code examples: agent creation, RAG implementation, multi-agent orchestration
- CI/CD automation with GitHub Actions and Cloud Build
- Security patterns: service accounts, Secret Manager, VPC Service Controls
- Cost optimization strategies and pricing reference
- Evaluation and monitoring with Cloud Trace

## Quick Reference: ADK Agent Types

| Agent Type    | Use Case                              | Example                          |
|---------------|---------------------------------------|----------------------------------|
| LLM Agent     | Dynamic routing with intelligence     | ReAct agent with tool selection  |
| Sequential    | Linear multi-step workflows           | ETL pipeline, form processing    |
| Loop          | Iterative refinement                  | Code review → fix → re-review    |
| Parallel      | Concurrent independent tasks          | Multi-source research            |
| Custom        | Domain-specific logic                 | Trading bot, compliance checker  |
| Multi-agent   | Hierarchical coordination             | PM agent delegating to workers   |

## Quick Reference: Deployment Targets

| Target             | Best For                    | Scaling        | Cost Model         |
|--------------------|-----------------------------|----------------|--------------------|
| Agent Engine       | Production-scale agents     | Auto-scaling   | Pay-per-request    |
| Cloud Run          | Web-facing agents           | Auto-scaling   | Pay-per-use        |
| GKE                | Complex multi-agent systems | Configurable   | Cluster costs      |
| Local/Docker       | Development and testing     | N/A            | Free               |

## Quick Reference: Agent Starter Pack Templates

```bash
# Create a ReAct agent (recommended starting point)
uvx agent-starter-pack create my-agent --template adk_base

# Create a RAG agent with document retrieval
uvx agent-starter-pack create my-rag --template agentic_rag

# Create a LangGraph-based agent
uvx agent-starter-pack create my-graph --template langgraph_base_react

# Create a multi-agent coding team
uvx agent-starter-pack create my-team --template crewai_coding_crew

# Create a multimodal RAG agent (audio/video/text)
uvx agent-starter-pack create my-multi --template adk_live
```

## Quick Reference: Essential Commands

```bash
# Install ADK
pip install google-cloud-aiplatform[adk,agent_engines]>=1.111

# Local development
adk serve --port 8080
curl http://localhost:8080/query -d '{"question": "test"}'

# Deploy to Cloud Run
adk deploy --target cloud_run --region us-central1

# Deploy to Agent Engine
asp deploy --env production --target agent_engine

# Gradual rollout
asp deploy --env dev      # Test in dev
asp deploy --env staging  # Validate in staging
asp deploy --env production  # Production push

# Evaluation
adk evaluate --test-dataset gs://bucket/eval_data.jsonl --metrics accuracy,relevance
```

## Architecture Decision Guide

**Choose a single ADK agent when:**

- One domain, one set of tools
- Latency requirements under 2 seconds
- Simple request/response pattern

**Choose multi-agent orchestration when:**

- Multiple specialized domains (research, analysis, writing)
- Complex workflows with branching logic
- Different models needed for different subtasks (Pro for reasoning, Flash for speed)

**Choose Agent Starter Pack templates when:**

- Starting a new project from scratch
- Need CI/CD and deployment automation out of the box
- Want a proven project structure with tests included

## Security Checklist

1. Create a dedicated service account with minimal permissions
2. Store API keys in Secret Manager (never in code or env files)
3. Enable VPC Service Controls for data-sensitive workloads
4. Use IAM conditions to restrict access by time, IP, or resource
5. Enable Cloud Audit Logging for all agent API calls
6. Set up billing alerts and quota limits per project

## Related Resources

- ADK Documentation: https://google.github.io/adk-docs/
- Agent Starter Pack: https://github.com/GoogleCloudPlatform/agent-starter-pack
- Agent Engine: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- Agent Builder: https://cloud.google.com/products/agent-builder
