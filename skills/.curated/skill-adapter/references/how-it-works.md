# How It Works

## How It Works

### 1. Task Analysis

When user presents a task:

- Identify the core capability needed (e.g., "analyze code quality", "generate documentation", "automate deployment")
- Determine the domain (security, devops, testing, etc.)
- Extract key requirements and constraints

### 2. Plugin Discovery

Search existing plugins for relevant capabilities:

```bash
# Find plugins in relevant category
ls plugins/community/ plugins/packages/ plugins/examples/

# Search for keywords in plugin descriptions
grep -r "keyword" --include="plugin.json" plugins/

# Find similar commands/agents
grep -r "capability-name" --include="*.md" plugins/
```

### 3. Capability Extraction

For each relevant plugin found, analyze:

**Commands (commands/*.md):**

- Read the markdown content
- Extract the approach/methodology
- Identify input/output patterns
- Note any scripts or tools used

**Agents (agents/*.md):**

- Understand the agent's role
- Extract problem-solving approach
- Note decision-making patterns
- Identify expertise areas

**Skills (skills/*/SKILL.md):**

- Read the skill instructions
- Extract core capability
- Note trigger conditions
- Understand tool usage patterns

**Scripts (scripts/*.sh, *.py):**

- Analyze script logic
- Extract reusable patterns
- Identify best practices
- Note error handling approaches

### 4. Pattern Synthesis

Combine learned patterns:

- Merge multiple approaches if beneficial
- Adapt to current context and constraints
- Simplify or enhance based on user needs
- Ensure compatibility with current environment

### 5. Skill Application

Apply the adapted skill:

- Use the learned approach
- Follow the extracted patterns
- Apply best practices discovered
- Adapt syntax/tools to current context
