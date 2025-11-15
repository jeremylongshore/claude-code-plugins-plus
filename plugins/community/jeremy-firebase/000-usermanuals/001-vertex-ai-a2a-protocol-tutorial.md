# Vertex AI Agent Engine: A2A Protocol Tutorial

**Source:** `agents/agent_engine/tutorial_a2a_on_agent_engine.ipynb`
**Repository:** GoogleCloudPlatform/generative-ai
**URL:** https://github.com/GoogleCloudPlatform/generative-ai/blob/main/agents/agent_engine/tutorial_a2a_on_agent_engine.ipynb

---

## Overview

This Jupyter notebook demonstrates building, deploying, and interacting with Agent-to-Agent (A2A) protocol agents on Google Cloud's Vertex AI Agent Engine, a fully-managed serverless platform.

## Key Concepts

### A2A Protocol
An open standard enabling AI agents to communicate and collaborate by standardizing capability discovery through Agent Cards and standardized interactions, eliminating custom integrations.

### Agent Engine
A fully-managed, serverless platform handling infrastructure, scaling, security, and monitoring for A2A agents.

## Setup Requirements

The tutorial requires installing:
- `a2a-sdk>=0.3.4` - Open-source SDK for building A2A-compliant agents
- `google-cloud-aiplatform[agent_engines, adk]>=1.112.0` - Vertex AI SDK with Agent Engine templates

Authentication via Google Colab is provided, along with Google Cloud project configuration and bucket setup.

## Implementation Components

### Agent Creation
Uses the Agent Development Kit (ADK) to build an `LlmAgent` with Gemini 2.5 Flash model and Google Search integration.

### Agent Card Definition
Defines agent metadata including:
- Name
- Description
- Skills with examples
- Input/output modes for capability discovery

### Agent Executor
Implements the `AgentExecutor` class bridging A2A protocol with internal agent logic, managing task lifecycle:
- `submitted` → `working` → `completed`

## Query Methods

The notebook demonstrates three approaches to interact with deployed agents:

1. **Vertex AI SDK** - Python SDK for direct management
2. **A2A Client** - Standard open-source protocol client
3. **HTTP Requests** - Direct REST API calls using standard endpoints

## Local Testing & Deployment

### Local Testing
Before cloud deployment, the tutorial validates agents locally using mock requests.

### Deployment
Deployment occurs via single `client.agent_engines.create()` call, which handles:
- Serialization
- Dependency inspection
- Packaging
- Endpoint provisioning

## Sample Implementation

The Q&A agent demonstrates practical usage by:
- Answering questions using web search
- Extracting responses into artifacts
- Managing task states throughout execution

## Key Takeaways

1. **A2A Protocol** standardizes agent communication
2. **Agent Engine** provides fully-managed serverless infrastructure
3. **Three interaction methods** support different use cases (SDK, A2A Client, HTTP)
4. **Local testing** validates before cloud deployment
5. **Single-command deployment** simplifies production release

## Related Plugins

This tutorial is relevant to:
- **jeremy-vertex-engine** - Agent Engine inspection and orchestration
- **jeremy-adk-orchestrator** - ADK supervisory orchestration with A2A protocol support
- **jeremy-vertex-validator** - Production readiness validation for Agent Engine deployments
- **jeremy-gcp-starter-examples** - GCP starter kit examples aggregator

---

**Status:** Pending full notebook retrieval
**Next Steps:** Download complete notebook with code cells for detailed implementation examples
