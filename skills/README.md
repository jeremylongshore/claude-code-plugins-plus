# Standalone Agent Skills

**500 production-ready Agent Skills** organized into 20 categories.

## Categories

| Category | Skills | Description |
|----------|--------|-------------|
| [01-devops-basics](./01-devops-basics/) | 25 | CI/CD, containers, infrastructure basics |
| [02-devops-advanced](./02-devops-advanced/) | 25 | GitOps, service mesh, observability |
| [03-security-fundamentals](./03-security-fundamentals/) | 25 | Auth, encryption, vulnerability scanning |
| [04-security-advanced](./04-security-advanced/) | 25 | Zero-trust, threat modeling, DevSecOps |
| [05-frontend-dev](./05-frontend-dev/) | 25 | React, Vue, performance, accessibility |
| [06-backend-dev](./06-backend-dev/) | 25 | API design, databases, microservices |
| [07-ml-training](./07-ml-training/) | 25 | Data preprocessing, model training |
| [08-ml-deployment](./08-ml-deployment/) | 25 | MLOps, model serving, inference |
| [09-test-automation](./09-test-automation/) | 25 | Unit, integration, e2e testing |
| [10-performance-testing](./10-performance-testing/) | 25 | Load testing, benchmarking, profiling |
| [11-data-pipelines](./11-data-pipelines/) | 25 | ETL, streaming, orchestration |
| [12-data-analytics](./12-data-analytics/) | 25 | SQL, BI, visualization |
| [13-aws-skills](./13-aws-skills/) | 25 | Lambda, S3, EC2, managed services |
| [14-gcp-skills](./14-gcp-skills/) | 25 | BigQuery, Vertex AI, Cloud Run |
| [15-api-development](./15-api-development/) | 25 | REST, GraphQL, OpenAPI |
| [16-api-integration](./16-api-integration/) | 25 | Webhooks, OAuth, SDK development |
| [17-technical-docs](./17-technical-docs/) | 25 | API docs, READMEs, Docusaurus |
| [18-visual-content](./18-visual-content/) | 25 | Diagrams, screenshots, video |
| [19-business-automation](./19-business-automation/) | 25 | Workflow automation, reporting |
| [20-enterprise-workflows](./20-enterprise-workflows/) | 25 | Governance, compliance, collaboration |

## How Skills Work

Agent Skills auto-activate when Claude Code detects relevant context. Simply describe what you need - no commands required.

```
You: "Set up a CI/CD pipeline for my Node.js app"
Claude: *Activates relevant DevOps skills automatically*
```

## Installation

Skills are included with the Claude Code Plugins marketplace:

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
```

## 2025 Schema Compliance

All 500 skills follow the 2025 Agent Skills schema:

```yaml
---
name: skill-name
description: |
  What this skill does and trigger phrases.
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
```

## Related

- [239 Embedded Skills](../plugins/) - Skills bundled within plugins
- [Learning Lab](../workspace/lab/) - Build your own agent workflows
- [Tutorials](../tutorials/) - Interactive Jupyter notebooks

## License

MIT License - All skills are open source.
