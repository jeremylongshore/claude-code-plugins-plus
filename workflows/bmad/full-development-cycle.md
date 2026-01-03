# Full Development Cycle Workflow

> BMAD-compatible workflow for complete Claude Code plugin development

## Overview

End-to-end plugin development from idea to deployment. Uses all BMAD agents: Analyst, PM, Architect, Developer, QA, and DevOps.

## Prerequisites

- Plugin idea or feature request
- Development environment ready
- Familiarity with Claude Code plugin system

## Phase 1: Analysis (Analyst Agent)

### Duration: 15-30 min

```
As the Analyst agent:

1. Understand the problem space
2. Research existing solutions
3. Identify constraints and risks
4. Document findings
```

**Deliverables:**
- [ ] Problem statement
- [ ] User research summary
- [ ] Competitive analysis
- [ ] Feasibility assessment

---

## Phase 2: Planning (PM Agent)

### Duration: 30-45 min

```
As the PM agent:

1. Define product requirements
2. Create user stories
3. Prioritize features
4. Set success metrics
```

**Deliverables:**
- [ ] PRD (Product Requirements Document)
- [ ] User stories with acceptance criteria
- [ ] MoSCoW prioritization
- [ ] Success metrics defined

### User Story Template

```markdown
## Story: [Title]

**As a** [user type]
**I want** [goal]
**So that** [benefit]

### Acceptance Criteria
- [ ] Given [context], when [action], then [result]

### Technical Notes
[Any implementation hints]

### Dependencies
[Blockers or prerequisites]
```

---

## Phase 3: Solutioning (Architect Agent)

### Duration: 30-60 min

```
As the Architect agent:

1. Design plugin structure
2. Define component interfaces
3. Plan integration points
4. Document technical decisions
```

**Deliverables:**
- [ ] Architecture diagram
- [ ] Component specifications
- [ ] API/interface definitions
- [ ] Technology decisions

### Plugin Architecture Template

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Manifest
├── commands/
│   ├── main-command.md      # Primary command
│   └── helper-command.md    # Supporting commands
├── skills/
│   └── auto-skill/
│       └── SKILL.md         # Auto-activated skill
├── agents/
│   └── specialist.md        # Specialized agent
├── hooks/
│   └── hooks.json           # Event hooks
├── README.md                # Documentation
└── LICENSE                  # License file
```

---

## Phase 4: Implementation (Developer Agent)

### Duration: 60-120 min

```
As the Developer agent:

1. Set up plugin structure
2. Implement commands
3. Create skills with proper schema
4. Add hooks if needed
5. Write documentation
```

### Implementation Checklist

**Structure**
- [ ] Create plugin directory
- [ ] Initialize plugin.json
- [ ] Set up component directories

**Commands**
- [ ] Create command files
- [ ] Add YAML frontmatter
- [ ] Write clear instructions
- [ ] Include examples

**Skills (2025 Schema)**
```yaml
---
name: skill-name
description: |
  Description with trigger phrases
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Name <email>
---
```

**Hooks** (optional)
```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "tool": "Bash",
      "script": "${CLAUDE_PLUGIN_ROOT}/hooks/validate.sh"
    }
  ]
}
```

**Documentation**
- [ ] README with overview
- [ ] Usage examples
- [ ] Installation instructions
- [ ] Configuration options

---

## Phase 5: Testing (QA Agent)

### Duration: 30-45 min

```
As the QA agent:

1. Validate plugin structure
2. Test all commands
3. Verify skill triggers
4. Check edge cases
```

### Testing Checklist

**Validation**
```bash
# Validate plugin structure
node scripts/validate-plugin.js ./my-plugin/

# Validate skills schema
python3 scripts/validate-skills-schema.py

# Check frontmatter
python3 scripts/validate-frontmatter.py
```

**Functional Testing**
- [ ] Each command works as documented
- [ ] Skills trigger on expected phrases
- [ ] Hooks execute correctly
- [ ] Error handling works

**Integration Testing**
- [ ] Works with Claude Code
- [ ] Compatible with other plugins
- [ ] MCP servers integrate properly

**Edge Cases**
- [ ] Empty inputs handled
- [ ] Invalid inputs rejected
- [ ] Large inputs managed
- [ ] Concurrent usage safe

---

## Phase 6: Deployment (DevOps Agent)

### Duration: 15-30 min

```
As the DevOps agent:

1. Add to marketplace catalog
2. Run sync script
3. Verify deployment
4. Document release
```

### Deployment Checklist

**Pre-Deployment**
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Version number set
- [ ] Changelog updated

**Marketplace Integration**
```bash
# Add to extended catalog
# Edit .claude-plugin/marketplace.extended.json

# Sync to CLI catalog
pnpm run sync-marketplace

# Validate
./scripts/validate-all-plugins.sh ./my-plugin/
```

**Git Operations**
```bash
git add .
git commit -m "feat: add my-plugin"
git push
```

**Post-Deployment**
- [ ] Verify on marketplace website
- [ ] Test installation: `/plugin install my-plugin@claude-code-plugins-plus`
- [ ] Monitor for issues

---

## Workflow Summary

| Phase | Agent | Duration | Key Output |
|-------|-------|----------|------------|
| 1. Analysis | Analyst | 15-30 min | Feasibility report |
| 2. Planning | PM | 30-45 min | PRD + User stories |
| 3. Solutioning | Architect | 30-60 min | Tech spec |
| 4. Implementation | Developer | 60-120 min | Working plugin |
| 5. Testing | QA | 30-45 min | Test report |
| 6. Deployment | DevOps | 15-30 min | Live plugin |

**Total: 3-5 hours**

---

## Integration with MCP Servers

| Phase | Recommended MCP |
|-------|-----------------|
| Analysis | domain-memory-agent |
| Planning | workflow-orchestrator |
| Solutioning | project-health-auditor |
| Implementation | design-to-code |
| Testing | conversational-api-debugger |
| Deployment | workflow-orchestrator |

---

## Quick Commands

```bash
# Initialize new plugin
*workflow-init

# Run full validation
./scripts/validate-all-plugins.sh ./my-plugin/

# Local testing
/plugin marketplace add /path/to/claude-code-plugins
/plugin install my-plugin@claude-code-plugins-plus

# Commit and deploy
git add -A && git commit -m "feat: add my-plugin" && git push
```

---

*Part of Claude Code Plugins Marketplace - https://claudecodeplugins.io/*
