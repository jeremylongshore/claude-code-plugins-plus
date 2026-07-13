# PRD: Genkit Production Expert

**Version:** 2.1.0
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

Firebase Genkit applications require integrating multiple concerns — flow definition, schema validation, model configuration, tool calling, RAG retrieval, and deployment — across three languages (Node.js, Python, Go). Developers struggle to connect these pieces correctly: schemas don't match flow signatures, retrievers return empty results due to embedding mismatches, safety filters block legitimate content, and cold starts cause deployment timeouts. Without expert guidance, teams ship Genkit flows that lack type safety, monitoring, and cost controls.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| Backend Developer | Building a new AI feature with Genkit for a production app | Complete flow implementation with typed schemas, error handling, and deployment config |
| AI Engineer | Implementing RAG with vector search and document retrieval | Retriever setup with embeddings, Firestore vector integration, and context caching |
| Full-Stack Developer | Adding tool-calling agents to an existing Node.js/Python app | Tool definitions with validated schemas and multi-turn conversation support |
| DevOps Engineer | Deploying Genkit flows to Firebase Functions or Cloud Run | Deployment configuration with auto-scaling, monitoring, and cost optimization |

## Success Criteria

1. Generate a complete Genkit flow with typed input/output schemas that passes validation without modification
2. RAG flows return relevant documents with source citations on first implementation attempt
3. Deployed flows have OpenTelemetry tracing and token usage monitoring configured out of the box
4. Cold start time under 5 seconds for Firebase Functions deployments with appropriate memory allocation
5. SAFETY_BLOCK errors handled gracefully with fallback response instead of crash
6. Cost optimization applied: Flash model used by default, Pro only when explicitly needed

## Functional Requirements

1. Analyze requirements to determine target language, flow complexity (simple/multi-step/RAG), model selection, and deployment target
2. Initialize project structure with proper config files (`tsconfig.json`, `genkit.config.ts`, or language equivalent)
3. Define input/output schemas using Zod (TypeScript), Pydantic (Python), or Go structs for runtime type safety
4. Implement Genkit flows using `ai.defineFlow()` with model configuration, temperature, and token limits
5. Define tools using `ai.defineTool()` with scoped schemas for external capabilities
6. For RAG: implement retrievers with `ai.defineRetriever()`, embedding generation, and vector database integration
7. Configure error handling for safety blocks, quota exceeded, and provider timeouts
8. Enable OpenTelemetry tracing with custom span attributes for cost and latency tracking
9. Deploy to Firebase Functions or Cloud Run with auto-scaling configuration

## Non-Functional Requirements

- All API keys stored in Secret Manager; never hardcoded in source or environment variables
- Schema validation must occur at runtime, not just compile time
- Flows must handle `SAFETY_BLOCK` responses gracefully without crashing
- Token usage must be tracked per-flow for cost attribution
- Retry logic with exponential backoff for all model API calls
- All flows must be testable locally via the Genkit Developer UI before deployment
- Generated code must follow the conventions of the target language (TypeScript/Python/Go)

## Dependencies

- Node.js 18+ (TypeScript), Python 3.10+ (Python), or Go 1.21+ (Go) runtime
- Genkit CLI and core packages (`genkit`, `@genkit-ai/googleai` for TypeScript)
- Google Cloud project with Vertex AI API enabled for Gemini model access
- Firebase CLI for Firebase Functions deployments
- Zod, Pydantic, or Go structs for schema validation

## Out of Scope

- Infrastructure provisioning with Terraform (handled by genkit-infra-expert)
- Fine-tuning or training custom models
- Non-Google model providers (OpenAI, Anthropic) — Genkit supports them but this skill focuses on Google AI
- Frontend UI development for chat interfaces
- Custom embedding model training (uses pre-built text-embedding-gecko)
- Multi-tenant architecture with per-user flow isolation
