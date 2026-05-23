# Directory Structure

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
