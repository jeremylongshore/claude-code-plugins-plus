---
name: skill-adapter
description: Analyzes existing plugins to extract their capabilities, then adapts and applies those skills to the current task. Acts as a universal skill chameleon that learns from other plugins.
allowed-tools: Read, Grep, Glob, Bash
---

# Skill Adapter - Universal Plugin Capability Extractor

## Purpose
Analyzes plugins in the claude-code-plugins marketplace to understand their capabilities, extracts the core patterns and approaches, then adapts those skills to solve the current user's task. Acts as a "skill chameleon" that can adopt any plugin's capabilities.

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

## Example Workflows

### Example 1: Learning Code Analysis from Security Plugins

**User task:** "Analyze this codebase for issues"

**Process:**
1. Search for security and code-analysis plugins
2. Find: `owasp-top-10-scanner`, `code-quality-enforcer`, `security-audit-agent`
3. Extract patterns:
   - OWASP scanner checks for: SQL injection, XSS, CSRF, auth issues
   - Quality enforcer looks at: complexity, duplication, standards
   - Audit agent examines: dependencies, secrets, permissions
4. Synthesize approach:
   - Run multi-layer analysis
   - Check security patterns first
   - Then code quality metrics
   - Then dependency issues
5. Apply to user's codebase with adapted checks

### Example 2: Adopting Documentation Skills

**User task:** "Generate API documentation"

**Process:**
1. Find documentation plugins
2. Discover: `api-documenter`, `openapi-generator`, `readme-builder`
3. Extract approaches:
   - API documenter: parses code, generates OpenAPI spec
   - OpenAPI generator: creates interactive docs
   - README builder: structures documentation hierarchically
4. Synthesize:
   - Parse code for endpoints
   - Generate OpenAPI/Swagger spec
   - Create interactive documentation
   - Build comprehensive README
5. Apply combined approach to user's API

### Example 3: Learning Automation from DevOps Plugins

**User task:** "Automate deployment process"

**Process:**
1. Search DevOps category
2. Find: `deployment-automation`, `ci-cd-pipeline`, `docker-compose-generator`
3. Extract patterns:
   - Deployment automation: build → test → deploy → verify
   - CI/CD pipeline: trigger conditions, parallel jobs, rollback
   - Docker compose: service orchestration, environment management
4. Synthesize deployment workflow
5. Apply to user's specific tech stack

## Reasoning Process

### When to Use Skill Adapter

Trigger when:
- User needs capability that might exist in marketplace
- Task could benefit from existing plugin patterns
- User asks: "Is there a plugin for this?"
- Similar problems have been solved before
- Multiple approaches could be combined

### Plugin Selection Criteria

Choose plugins based on:
1. **Relevance**: Matches task domain/requirements
2. **Quality**: Well-documented, clear approach
3. **Simplicity**: Not overly complex for the task
4. **Recency**: Updated plugins preferred
5. **Popularity**: Featured or well-maintained plugins

### Adaptation Strategy

When adapting skills:
- **Keep**: Core logic and proven patterns
- **Adapt**: Syntax, tool names, specific commands
- **Enhance**: Add error handling, user feedback
- **Simplify**: Remove unnecessary complexity
- **Contextualize**: Adjust to user's environment

## Limitations and Boundaries

### What Skill Adapter CAN Do:
✅ Read and analyze plugin source code
✅ Extract patterns and approaches
✅ Adapt methodologies to new contexts
✅ Combine multiple plugin capabilities
✅ Apply learned skills with reasoning

### What Skill Adapter CANNOT Do:
❌ Execute compiled code (MCP servers)
❌ Access external APIs without credentials
❌ Modify original plugins
❌ Guarantee exact plugin behavior replication
❌ Use plugins that require specific environment setup

## Success Criteria

Skill adaptation is successful when:
1. User's task is completed effectively
2. Approach borrowed makes logical sense
3. Adapted skill is properly contextualized
4. User understands where the approach came from
5. Result quality matches or exceeds original plugin

## Transparency

Always inform user:
- Which plugins were analyzed
- What patterns were extracted
- How the skill was adapted
- Why this approach was chosen
- Any limitations of the adaptation

## Example Usage

```
User: "I need to validate JSON schemas in my project"

Skill Adapter Process:
1. Searches plugins for JSON validation
2. Finds: schema-validator, json-lint-enforcer
3. Extracts: ajv library usage, error formatting patterns
4. Adapts: Uses available tools (jq, node, python)
5. Applies: Validates user's schemas with detailed errors
6. Reports: "I adapted the schema-validator approach using jq
   for validation and added custom error formatting"
```

## Meta-Learning

Skill Adapter improves by:
- Tracking which plugins solve which tasks best
- Learning which patterns are most reusable
- Noting which adaptations work well
- Building a mental model of the marketplace
- Understanding plugin ecosystem relationships

---

**In essence:** Skill Adapter is a meta-skill that makes the entire plugin marketplace available as a learning resource, extracting and applying capabilities on-demand to solve user tasks efficiently.
