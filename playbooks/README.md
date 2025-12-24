# Production Playbooks

Comprehensive technical guides for building production-grade Claude Code plugin systems. Each playbook provides deep implementation details, production-ready code examples, and real-world patterns learned from operating large-scale AI agent deployments.

## 📚 Complete Playbook Collection

### AI Architecture & Tool Use

**[11. Advanced Tool Use](./11-advanced-tool-use.md)** (~6,500 words) ⭐ NEW
Dynamic tool discovery, programmatic orchestration, and parameter guidance. Tool Search Tool (85% token reduction), Programmatic Tool Calling (37% efficiency gains), and Tool Use Examples (90% parameter accuracy). Enterprise-scale agent architecture.

### Cost Management & Optimization

**[01. Multi-Agent Rate Limits](./01-multi-agent-rate-limits.md)** (~2,800 words)
Prevent API throttling in concurrent multi-agent systems. Token bucket algorithms, sliding windows, priority queues, and backpressure handling for Claude API rate limits.

**[02. Cost Caps & Budget Management](./02-cost-caps.md)** (~3,200 words)
Hard budget controls for AI spending. Real-time spend tracking, automatic shutoffs, team quotas, and financial safeguards to prevent runaway costs.

**[09. Cost Attribution System](./09-cost-attribution.md)** (~5,500 words)
Multi-dimensional cost tracking (team/project/user/workflow). Automatic tagging, chargeback models, budget enforcement, and usage analytics for AI operations.

### Infrastructure & Deployment

**[03. MCP Server Reliability](./03-mcp-reliability.md)** (~3,500 words)
Self-healing MCP servers with circuit breakers, exponential backoff, health checks, and automatic recovery. Production-grade Model Context Protocol implementations.

**[04. Ollama Migration Guide](./04-ollama-migration.md)** (~4,500 words)
Switch from OpenAI/Anthropic to self-hosted LLMs. Complete migration path: local setup, prompt translation, performance benchmarks, and cost analysis.

**[06. Self-Hosted Stack Setup](./06-self-hosted-stack.md)** (~5,500 words)
Full infrastructure deployment with Docker/Kubernetes. Ollama, PostgreSQL, Redis, Prometheus, Grafana, Nginx - complete production stack with monitoring and backups.

### Operations & Reliability

**[05. Incident Debugging Playbook](./05-incident-debugging.md)** (~5,000 words)
SEV-1/2/3/4 incident response protocols. Log analysis, root cause investigation (5 Whys, Fishbone), postmortem templates, and on-call procedures.

**[10. Progressive Enhancement Patterns](./10-progressive-enhancement.md)** (~5,500 words)
Safe AI feature rollout strategies. Feature flags (0% → 100%), A/B testing, canary deployments, graceful degradation, and automated rollback on failures.

### Compliance & Governance

**[07. Compliance & Audit Guide](./07-compliance-audit.md)** (~6,000 words)
SOC 2, GDPR, HIPAA, PCI DSS implementation. Audit logging with immutable signatures, RBAC, data privacy (PII redaction), and regulatory compliance.

**[08. Team Presets & Workflows](./08-team-presets.md)** (~5,000 words)
Team standardization and collaboration. Plugin bundles, workflow templates, automated onboarding, and multi-layer configuration hierarchy (org/team/project/individual).

## 📊 Statistics

- **Total Content**: ~53,500 words across 11 playbooks
- **Average Length**: 4,900 words per playbook (range: 2,800 - 6,500 words)
- **Code Examples**: 120+ production-ready TypeScript implementations
- **Topics Covered**: 60+ production patterns
- **Coverage Areas**: AI Architecture, Cost, Infrastructure, Operations, Compliance

## 🎯 Use Cases

### For Plugin Developers
- Learn production patterns for MCP servers
- Implement cost controls and monitoring
- Build self-hosted AI infrastructure
- Create team-ready plugin bundles

### For Engineering Teams
- Standardize Claude Code workflows
- Control AI spending with budget systems
- Deploy compliant self-hosted stacks
- Respond to production incidents

### For Technical Leaders
- Understand total cost of ownership
- Plan migration to self-hosted LLMs
- Meet compliance requirements (SOC 2, GDPR, HIPAA)
- Roll out features safely with progressive enhancement

## 🛠 Technologies

All playbooks use production-grade tools and frameworks:

- **Languages**: TypeScript (primary), Python, Bash
- **Infrastructure**: Docker, Kubernetes, Prometheus, Grafana
- **Databases**: PostgreSQL, Redis, ClickHouse
- **AI/ML**: Ollama, llama.cpp, vLLM
- **Protocols**: MCP (Model Context Protocol)
- **Compliance**: GDPR, HIPAA, SOC 2, PCI DSS

## 📖 Reading Guide

### New to Claude Code Plugins?
Start with:
1. **Team Presets** (08) - Understand collaboration patterns
2. **MCP Reliability** (03) - Core plugin architecture
3. **Progressive Enhancement** (10) - Safe rollout strategies

### Building Large-Scale Agent Systems?
Essential path:
1. **Advanced Tool Use** (11) - Dynamic discovery, programmatic orchestration ⭐ NEW
2. **Multi-Agent Rate Limits** (01) - Prevent API throttling
3. **Cost Attribution** (09) - Track usage across features

### Building Production Systems?
Focus on:
1. **Self-Hosted Stack** (06) - Infrastructure foundation
2. **Cost Attribution** (09) - Financial visibility
3. **Incident Debugging** (05) - Operations readiness

### Enterprise Compliance?
Essential reads:
1. **Compliance & Audit** (07) - Regulatory requirements
2. **Cost Caps** (02) - Budget governance
3. **Team Presets** (08) - Access controls

### Migrating from Cloud to Self-Hosted?
Migration path:
1. **Ollama Migration** (04) - Local LLM setup
2. **Self-Hosted Stack** (06) - Full infrastructure
3. **Cost Attribution** (09) - Compare cloud vs self-hosted costs

## 🔗 Related Resources

- **[Learning Lab](../../workspace/lab/)** - Hands-on tutorials for agent workflow patterns
- **[Plugin Marketplace](https://claudecodeplugins.io/)** - 258 plugins across 18 categories
- **[MCP Plugins](../../plugins/mcp/)** - Production MCP server implementations
- **[Templates](../../templates/)** - Starter templates for new plugins

## 📝 Playbook Format

Each playbook follows a consistent structure:

1. **Introduction** - Problem statement and overview
2. **Core Concepts** - Fundamental principles
3. **Architecture** - System design patterns
4. **Implementation** - Production-ready code with TypeScript
5. **Configuration** - Setup and deployment guides
6. **Monitoring** - Observability and metrics
7. **Best Practices** - DO/DON'T guidelines
8. **Troubleshooting** - Common issues and solutions
9. **Tools & Resources** - Recommended tools and further reading
10. **Summary** - Key takeaways and checklist

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/jeremylongshore/claude-code-plugins.git
cd claude-code-plugins/docs/playbooks/

# Read a playbook
cat 01-multi-agent-rate-limits.md

# Or browse online
# https://github.com/jeremylongshore/claude-code-plugins/tree/main/docs/playbooks
```

## 🤝 Contributing

Found an issue or want to improve a playbook? Contributions welcome!

1. Open an issue describing the problem or improvement
2. Submit a pull request with detailed changes
3. Include code examples and real-world evidence

## 📄 License

All playbooks are released under the MIT License. Use them freely in your commercial and open-source projects.

---

**Last Updated**: December 24, 2025
**Version**: 1.0.0
**Author**: Jeremy Longshore (jeremy@intentsolutions.io)
**Repository**: https://github.com/jeremylongshore/claude-code-plugins
