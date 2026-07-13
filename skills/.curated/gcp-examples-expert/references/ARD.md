# ARD: GCP Examples Expert

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The GCP Examples Expert maps developer requirements to the correct Google Cloud AI repository and generates production-ready code adapted from official patterns. It operates as a code generation skill that bridges six official GCP AI repositories.

```
Developer Request ("Build a RAG system on GCP")
       ↓
[GCP Examples Expert]
  ├── Maps to: Framework selection (Genkit, ADK, Vertex AI, etc.)
  ├── Sources: 6 official GCP repositories
  ├── Adapts: language, security, monitoring, deployment
  └── Generates: runnable code + deployment config + IaC
       ↓
Production-Ready Code Package
  ├── Application code (adapted from source repo)
  ├── Deployment config (Cloud Run / Functions / Agent Engine)
  ├── Terraform module (infrastructure)
  └── Documentation (source citations, cost estimates)
```

## Data Flow

1. **Input**: User request describing the AI use case, preferred language, and deployment target. May include constraints like model preference, cost budget, or compliance requirements.
2. **Processing**: Classify the request into one of six framework categories. Select the matching code pattern from the categorized reference. Adapt to the target language. Layer on security (IAM, VPC-SC, Secret Manager), monitoring (OpenTelemetry, dashboards), and deployment configuration. Generate Terraform when infrastructure provisioning is needed.
3. **Output**: Complete code package with application files, deployment config (YAML/JSON), Terraform module, environment variable template, monitoring setup, cost estimate, and source repository citations.

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Six-category framework taxonomy | ADK, Starter Pack, Genkit, Vertex AI, Gen AI, AgentSmithy | Covers the complete GCP AI landscape; each category maps to a distinct official repo |
| Security-by-default | Every example includes IAM, Secret Manager, and VPC-SC | Production examples must not teach insecure patterns; developers copy-paste examples |
| Source attribution | Cite the specific repo and pattern for every adaptation | Enables developers to find updates and deeper documentation; maintains trust |
| Model selection guidance | Gemini 2.5 Flash for throughput, Pro for reasoning | Prevents cost surprises; Flash handles 80% of use cases at 10x lower cost |
| Multi-target deployment | Generate configs for Cloud Run, Firebase Functions, and Agent Engine | Different deployment targets suit different flow types; developers choose |
| Language adaptation | Transform patterns to TypeScript, Python, or Go | Each repo has language-specific conventions; adapt rather than translate literally |
| IaC inclusion | Terraform templates alongside application code | Production deployments need reproducible infrastructure, not just application code |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| Read | Inspect existing project files, requirements, and configuration to adapt examples to the user's codebase |
| Write | Create new application files, deployment configs, Terraform modules, and environment templates |
| Edit | Patch existing code to integrate GCP patterns, update dependencies, or add monitoring |
| Grep | Search for existing framework usage, import patterns, and configuration in the target project |
| Glob | Discover project structure to determine where generated code should be placed |
| Bash(cmd:*) | Run dependency installation, gcloud commands, firebase CLI, and validation scripts |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Framework mismatch | User request doesn't clearly map to a single category | Ask clarifying questions; present the two closest matches with trade-offs |
| API not enabled | `gcloud services list` missing required APIs | Provide the exact `gcloud services enable` command for each missing API |
| Region unavailability | Requested model not available in specified region | Suggest `us-central1` or `europe-west4` where Gemini models are available |
| Dependency conflict | Incompatible SDK versions in existing project | Pin versions explicitly; provide a clean `requirements.txt` or `package.json` |
| Quota exceeded | Rate limit on Vertex AI prediction endpoints | Include exponential backoff in generated code; provide quota increase request link |

## Extension Points

- Additional framework categories: add new GCP AI repos (e.g., MLOps pipelines) as they become official
- Language expansion: extend beyond TypeScript/Python/Go when Genkit or ADK adds language support
- Custom security profiles: allow enterprise users to specify compliance frameworks (SOC2, HIPAA) for stricter defaults
- Cost calculator integration: generate detailed cost projections based on expected query volume and model selection
- Template versioning: pin examples to specific SDK versions with automated upgrade paths
- Interactive selection: when multiple frameworks match, present a comparison table for the user to choose
- Batch generation: create examples for multiple frameworks from a single requirements document
