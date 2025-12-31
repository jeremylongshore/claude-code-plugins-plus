---
name: windsurf-cascade-agents
description: |
  Create custom Cascade agent configurations for specialized tasks. Activate when users mention
  "custom cascade agent", "specialized ai agent", "domain-specific cascade", "agent configuration",
  or "custom ai behavior". Handles custom agent creation and configuration.
allowed-tools: Read,Write,Edit,Bash,Grep,Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Cascade Agents

Create custom Cascade agent configurations for domain-specific tasks.

## Directory Structure

```
project-root/
    .windsurf/
        agents/
            registry.json                # Agent registry
                # Available agents
                # Activation triggers
                # Priority ordering

            definitions/
                security-reviewer.agent.json     # Security review agent
                    # Security-focused prompts
                    # Vulnerability patterns
                    # Compliance checks

                api-designer.agent.json          # API design agent
                    # REST/GraphQL patterns
                    # Schema validation
                    # Documentation generation

                performance-optimizer.agent.json # Performance agent
                    # Profiling integration
                    # Optimization patterns
                    # Benchmark comparison

                documentation-writer.agent.json  # Docs agent
                    # Documentation style
                    # API documentation
                    # User guide generation

            contexts/
                shared-context.md            # Common context for all agents
                    # Project overview
                    # Team conventions
                    # Technology stack

                security-context.md          # Security agent context
                    # Security requirements
                    # Threat model
                    # Compliance standards

                api-context.md               # API agent context
                    # API conventions
                    # Schema standards
                    # Versioning policies

            prompts/
                system-prompts/
                    security-system.md       # Security agent system prompt
                    api-system.md            # API agent system prompt
                    performance-system.md    # Performance agent system prompt

                user-templates/
                    review-request.md        # Review request template
                    design-request.md        # Design request template
                    optimize-request.md      # Optimization request template
```

## Agent Features

### Domain Specialization
- Security-focused analysis
- API design patterns
- Performance optimization
- Documentation generation

### Context Management
- Persistent domain knowledge
- Project-specific patterns
- Team conventions integration
- Cross-agent context sharing

## Configuration Steps

1. **Define Agent Purpose**
   - Identify specialized needs
   - Document domain knowledge
   - Set behavior guidelines

2. **Create Agent Configuration**
   - Write system prompts
   - Configure context sources
   - Define activation triggers

3. **Test and Refine**
   - Test with sample tasks
   - Gather feedback
   - Iterate on prompts

## Success Criteria

- 90%+ accuracy on domain-specific prompts
- Appropriate agent activation
- Specialized workflows enabled
