# Plugin Repository Report

Generated: 2025-10-11
Repository: `jeremylongshore/claude-code-plugins`
Location: `/home/jeremy/projects/claude-code-plugins`

---

## 1. Repository Structure

### Compact Tree (Depth 4)
```
claude-code-plugins/
├── .claude-plugin/
│   └── marketplace.json (10118 bytes)
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/
│   │   ├── deploy-marketplace.yml
│   │   ├── release.yml
│   │   └── validate-plugins.yml
│   ├── FUNDING.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── RELEASE_CHECKLIST.md
├── plugins/
│   ├── ai-agency/          # 6 AI agency plugins
│   ├── community/          # (empty - for community contributions)
│   ├── devops/             # Production DevOps plugins
│   ├── examples/           # 3 example plugins
│   ├── mcp/                # 5 MCP server plugins
│   ├── packages/           # 4 plugin packs
│   └── productivity/       # Productivity plugins
├── marketplace/            # Astro-based marketplace website
├── docs/                   # Documentation
├── scripts/                # Repository maintenance scripts
├── templates/              # 4 plugin templates
└── claudes-docs/          # Generated documentation
```

### Plugin Packages Structure
```
packages/
├── ai-ml-engineering-pack/    # 12 AI/ML plugins
├── devops-automation-pack/    # 25 DevOps plugins
├── fullstack-starter-pack/    # 15 fullstack plugins
└── security-pro-pack/          # 10 security plugins
```

### MCP Plugins
```
mcp/
├── conversational-api-debugger/
├── design-to-code/
├── domain-memory-agent/
├── project-health-auditor/
└── workflow-orchestrator/
```

---

## 2. Plugin Metadata

### Main Marketplace Configuration
| Field | Value |
|-------|-------|
| Name | claude-code-plugins |
| Owner | Jeremy Longshore |
| Version | 1.1.0 |
| Homepage | https://jeremylongshore.github.io/claude-code-plugins/ |
| Plugins Count | 20 registered in marketplace.json |

### Sample Plugin Pack Metadata (DevOps Automation)
| Field | Value |
|-------|-------|
| Name | devops-automation-pack |
| Version | 1.0.0 |
| Description | 25 professional DevOps plugins for CI/CD, deployment, Docker, Kubernetes... |
| Author | Jeremy Longshore <jeremy@intentsolutions.ai> |
| License | MIT |
| Keywords | devops, ci-cd, docker, kubernetes, terraform, deployment |

---

## 3. MCP Integrations

### Discovered MCP Servers (5 total)

| Plugin | MCP Config | Server Name | Type |
|--------|------------|-------------|------|
| project-health-auditor | .mcp.json | code-metrics | node |
| conversational-api-debugger | .mcp.json | (present) | node |
| domain-memory-agent | .mcp.json | (present) | node |
| design-to-code | .mcp.json | (present) | node |
| workflow-orchestrator | .mcp.json | (present) | node |

### MCP Server Configuration Example
```json
{
  "mcpServers": {
    "code-metrics": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/dist/servers/code-metrics.js"],
      "env": {}
    }
  }
}
```

**Note**: MCP tools are defined in compiled JavaScript files in `dist/servers/` directories.

---

## 4. Slash Commands

### Example Commands Found

| Plugin | Command | Description |
|--------|---------|-------------|
| project-health-auditor | /analyze | Trigger full repository health analysis |
| git-commit-smart | (in commands/) | AI-powered commit messages |
| n8n-workflow-designer | (in commands/) | Design n8n workflows |
| make-scenario-builder | (in commands/) | Build Make.com scenarios |
| zapier-zap-builder | (in commands/) | Create Zapier Zaps |

### Command Structure Example (project-health-auditor/analyze.md)
- **Name**: Repository Health Analysis
- **MCP Calls**: `list_repo_files`, `file_metrics`, `git_churn`, `map_tests`
- **Workflow**:
  1. File Discovery
  2. Complexity Analysis
  3. Git Churn Analysis
  4. Test Coverage Mapping
- **Output**: Health report with actionable recommendations

---

## 5. Sub-agents

### Discovered Agents (Sample)

| Pack | Agent | Purpose |
|------|-------|---------|
| ai-ml-engineering | prompt-optimizer | Optimize prompts for efficiency |
| ai-ml-engineering | llm-integration-expert | Multi-provider LLM integration |
| ai-ml-engineering | rag-architect | Design RAG systems |
| security-pro | compliance-checker | Check HIPAA, GDPR, PCI DSS compliance |
| security-pro | crypto-expert | Cryptography auditing |
| devops-automation | ci-cd-expert | CI/CD pipeline optimization |
| fullstack-starter | frontend-architect | React/Vue component design |

### Agent Count by Pack
- **AI/ML Engineering**: 8 agents
- **Security Pro**: 5 agents
- **DevOps Automation**: 5 agents
- **Fullstack Starter**: 6 agents

---

## 6. Hooks

### Discovered Hook Implementations

| Plugin | Trigger | Action | File Modified |
|--------|---------|--------|---------------|
| formatter | PostToolUse (Write\|Edit) | format.sh | Formats written/edited files |

### Hook Structure Example
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"
      }]
    }]
  }
}
```

---

## 7. GitHub Automation

### Workflow Files

#### validate-plugins.yml
- **Triggers**: Pull requests (plugins/**, .claude-plugin/**), Push to main
- **Main Steps**:
  - Checkout code
  - Validate JSON files with jq
  - Check plugin structure (plugin.json, README.md)
  - Verify scripts are executable
- **Env/Secrets**: None required

#### release.yml
- **Triggers**: Manual dispatch, tags
- **Main Steps**:
  - Build release artifacts
  - Create GitHub release
  - Publish to marketplace
- **Env/Secrets**: GITHUB_TOKEN

#### deploy-marketplace.yml
- **Triggers**: Push to main (marketplace changes)
- **Main Steps**:
  - Build Astro site
  - Deploy to GitHub Pages
- **Env/Secrets**: GITHUB_TOKEN

---

## 8. Quick Lint

### JSON Syntax Check
-  marketplace.json: Valid
-  plugin.json files: Valid (sampled)
-  hooks.json files: Valid
-  .mcp.json files: Valid

### Command File Validation
- ️ Command files should have H1 matching slash command name
-  Commands reference existing MCP tools (where applicable)

### Script Permissions
-  Shell scripts in examples/formatter/scripts/ are present
- ️ Need to verify all .sh files have execute permissions

---

## 9. Usage Snippet

### Installation

```bash
# Add the marketplace to Claude Code
/plugin marketplace add jeremylongshore/claude-code-plugins

# Install a plugin pack
/plugin install devops-automation-pack@claude-code-plugins-plus

# Install individual plugins
/plugin install project-health-auditor@claude-code-plugins-plus
/plugin install git-commit-smart@claude-code-plugins-plus
```

### Example Invocations

```bash
# Analyze repository health
/analyze /path/to/repo

# Generate smart commit message
/gc

# Design n8n workflow
/n8n-workflow

# Trigger security audit
/security-audit
```

### Local Testing

```bash
# Create test marketplace
mkdir -p ~/test-marketplace/.claude-plugin
cat > ~/test-marketplace/.claude-plugin/marketplace.json << 'EOF'
{
  "name": "test",
  "owner": {"name": "Test"},
  "plugins": [{
    "name": "my-plugin",
    "source": "/absolute/path/to/plugin"
  }]
}
EOF

# Add and install
/plugin marketplace add ~/test-marketplace
/plugin install my-plugin@test
```

---

## 10. Gaps & TODOs

### Concrete Fixes Needed

1. **Missing plugin.json files**
   - [ ] Add `.claude-plugin/plugin.json` to individual example plugins
   - [ ] Add `.claude-plugin/plugin.json` to AI agency plugins

2. **MCP Server Configuration**
   - [ ] Document MCP tools in README for each MCP plugin
   - [ ] Add tool descriptions to plugin documentation

3. **Command Documentation**
   - [ ] Ensure all command files have proper frontmatter
   - [ ] Verify command names match file names

4. **Script Permissions**
   - [ ] Run `chmod +x` on all .sh files in scripts/ directories
   - [ ] Add permission check to validation script

5. **Agent Documentation**
   - [ ] Add frontmatter to all agent .md files
   - [ ] Document expected inputs/outputs

6. **Hook Implementations**
   - [ ] Add hooks examples to more plugins
   - [ ] Document hook side effects clearly

7. **Package Structure**
   - [ ] Standardize sub-plugin structure in packages
   - [ ] Add individual plugin.json to each sub-plugin

8. **Testing**
   - [ ] Add test scripts for MCP servers
   - [ ] Create integration tests for commands

---

## Summary

**Repository Stats:**
- Total Plugins: 20 in marketplace
- Plugin Packs: 4 (62 total components)
- MCP Servers: 5 (with compiled TypeScript)
- Example Plugins: 3
- Templates: 4
- GitHub Workflows: 3

**Key Features:**
- Comprehensive marketplace with installation system
- Professional plugin packs for different domains
- MCP server integration for external tools
- Automated validation and release workflows
- Active development with clear structure

**Repository Health:**  Well-organized, actively maintained, ready for community contributions

---

*Report generated using Claude Code analysis tools*