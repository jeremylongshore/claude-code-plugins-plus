# ZCF Integration Guide

> Integrate Claude Code Plugins with ZCF (Zero Config Framework) for optimized tool routing and token management.

## Overview

[ZCF (Zero Config Framework)](https://github.com/UfoMiao/zcf) is a CLI tool that simplifies Claude Code setup with pre-configured MCP servers. This guide covers:

1. **Installing our MCP servers via ZCF**
2. **Tool routing for token efficiency**
3. **BMAD workflow integration**
4. **CCR (Claude Code Router) compatibility**

---

## Quick Start with ZCF

### Install ZCF

```bash
npx zcf@latest i
```

### Select Our MCP Servers

During ZCF installation, you'll see our servers as options:

| Server | Description | Category |
|--------|-------------|----------|
| **Project Health Auditor** | Analyze code health, complexity, test coverage gaps | code-quality |
| **Design to Code** | Convert Figma designs to React/Vue/Svelte components | design |
| **Conversational API Debugger** | Debug REST APIs with OpenAPI specs and HTTP logs | api |

---

## Tool Routing for Token Efficiency

### The Problem

When you have many MCP servers, Claude loads ALL tool schemas into context. With 7+ MCPs, this can burn 60,000+ tokens (30%+ of context) before any conversation.

### Solution: Selective Loading

Use Claude Code's built-in commands to manage MCP servers:

```bash
# See active MCP servers and their status
/mcp

# Disable servers you don't need right now
/mcp disable project-health-auditor
/mcp disable design-to-code

# Re-enable when needed
/mcp enable project-health-auditor
```

### Recommended Workflows

**For Code Review Sessions:**
```bash
/mcp enable project-health-auditor
/mcp disable design-to-code
/mcp disable conversational-api-debugger
```

**For API Development:**
```bash
/mcp enable conversational-api-debugger
/mcp disable project-health-auditor
/mcp disable design-to-code
```

**For UI Development:**
```bash
/mcp enable design-to-code
/mcp disable project-health-auditor
/mcp disable conversational-api-debugger
```

### Context Management

```bash
# Check current context usage
/context

# Compact conversation to free space
/compact

# Clear and start fresh
/clear
```

---

## MCP Server Categories

Our 7 MCP servers organized by use case:

### Code Quality
- **project-health-auditor** - Analyze code health, complexity, test coverage gaps

### API Development
- **conversational-api-debugger** - Debug REST APIs with OpenAPI specs

### Design & UI
- **design-to-code** - Convert designs to React/Vue/Svelte components

### Knowledge Management
- **domain-memory-agent** - Persist domain knowledge across sessions

### Workflow Automation
- **workflow-orchestrator** - Multi-step automated workflows

### AI/ML Development
- **ai-experiment-logger** - Track AI experiments, hyperparameters, results

### Memory Systems
- **lumera-agent-memory** - Privacy-first agent memory with MCP

---

## BMAD Workflow Integration

Our plugins are compatible with [BMAD (Breakthrough Method for Agile AI-Driven Development)](https://github.com/bmad-method) workflows.

### Available Workflows

Located in `workflows/bmad/`:

| Workflow | Agents | Duration |
|----------|--------|----------|
| **feature-planning** | Analyst, PM, Architect | 30-60 min |
| **architecture-review** | Architect, Security, Reviewer | 20-40 min |
| **full-development-cycle** | All 6 agents | 2-4 hours |

### Using BMAD Workflows

```bash
# Feature planning workflow
# Uses Analyst → PM → Architect agent roles
cat workflows/bmad/feature-planning.md

# Architecture review
# Uses Architect → Security → Reviewer roles
cat workflows/bmad/architecture-review.md

# Full development cycle
# All 6 BMAD agents: Analyst, PM, Architect, Developer, QA, DevOps
cat workflows/bmad/full-development-cycle.md
```

### MCP Integration with BMAD Phases

| Phase | Recommended MCP |
|-------|-----------------|
| Analysis | domain-memory-agent |
| Planning | workflow-orchestrator |
| Solutioning | project-health-auditor |
| Implementation | design-to-code |
| Testing | conversational-api-debugger |
| Deployment | workflow-orchestrator |

---

## CCR (Claude Code Router) Compatibility

Our MCP servers work with [CCR (Claude Code Router)](https://github.com/cognitrix/ccr) for routing requests to alternative LLM providers.

### Supported Configurations

```json
{
  "zcf_metadata": {
    "bmad_compatible": true,
    "ccr_compatible": true
  }
}
```

### Using with Alternative Providers

CCR can route to:
- **OpenRouter** - Multiple model providers
- **DeepSeek** - Cost-effective reasoning
- **Ollama** - Local model inference

Our MCP tools work with any provider that supports function calling.

---

## Configuration Files

### ZCF Discovery

Our marketplace includes ZCF configuration at the root:

**config.zcf.json:**
```json
{
  "zcf_integration": {
    "type": "marketplace",
    "marketplace_slug": "claude-code-plugins-plus"
  },
  "mcp_servers": {
    "presets_file": ".claude-plugin/mcp-presets.json"
  }
}
```

### MCP Presets

**`.claude-plugin/mcp-presets.json`:**
```json
{
  "presets": {
    "project-health-auditor": {
      "command": "npx",
      "args": ["-y", "@claude-code-plugins-plus/project-health-auditor"],
      "category": "code-quality"
    }
  }
}
```

---

## Best Practices

### 1. Start Minimal
Enable only the MCPs you need for your current task. Add more as needed.

### 2. Use Categories
Group your work by MCP category (code-quality, api, design) to minimize context.

### 3. Compact Regularly
Run `/compact` periodically to free context for tool schemas.

### 4. Disable Unused Servers
If you haven't used an MCP in 30+ minutes, disable it:
```bash
/mcp disable [server-name]
```

### 5. Combine with BMAD
Use BMAD workflows to guide which MCPs to enable for each development phase.

---

## Troubleshooting

### High Token Usage

```bash
# Check context usage
/context

# See which MCPs are loaded
/mcp

# Disable unused servers
/mcp disable [server-name]
```

### MCP Server Not Responding

```bash
# Check server status
/mcp

# Restart specific server
/mcp restart [server-name]

# View server logs
/mcp logs [server-name]
```

### ZCF Installation Issues

```bash
# Clear ZCF cache
rm -rf ~/.zcf

# Reinstall
npx zcf@latest i
```

---

## Resources

- [ZCF Repository](https://github.com/UfoMiao/zcf)
- [BMAD Method](https://github.com/bmad-method)
- [CCR (Claude Code Router)](https://github.com/cognitrix/ccr)
- [Claude Code Plugins Marketplace](https://claudecodeplugins.io/)
- [MCP Registry](https://registry.modelcontextprotocol.io)

---

*Part of Claude Code Plugins Marketplace - https://claudecodeplugins.io/*
