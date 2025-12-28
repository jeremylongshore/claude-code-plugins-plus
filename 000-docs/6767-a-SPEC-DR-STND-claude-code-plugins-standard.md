# Global Master Standard – Claude Code Plugins & Marketplace Specification

**Document ID**: 6767-a-SPEC-MASTER-claude-code-plugins-standard
**Version**: 1.0.0
**Status**: CANONICAL - Cross-Repo Standard
**Created**: 2025-12-06
**Updated**: 2025-12-07

**Sources**:
- [Official Anthropic Plugins Reference](https://code.claude.com/docs/en/plugins-reference)
- [Official Marketplace Documentation](https://code.claude.com/docs/en/plugin-marketplaces)
- [Official Hooks Reference](https://code.claude.com/docs/en/hooks)
- [Official Settings Reference](https://code.claude.com/docs/en/settings)
- [Claude Code Plugins Blog](https://www.claude.com/blog/claude-code-plugins)
- [Anthropic Official Plugins Repository](https://github.com/anthropics/claude-plugins-official)
- [Claude Code GitHub Repository](https://github.com/anthropics/claude-code)

---

## 1. Executive Summary

### What is a Claude Code Plugin?

A **Claude Code plugin** is a packaged collection of extensions that enhance Claude Code's capabilities. Plugins bundle together any combination of:

- **Slash Commands**: User-triggered shortcuts for common operations (e.g., `/deploy`, `/review`)
- **Agents (Subagents)**: Specialized AI assistants for specific task domains
- **Skills**: Auto-invoked knowledge modules Claude uses autonomously
- **Hooks**: Event handlers that intercept and modify Claude Code's behavior
- **MCP Servers**: External tool integrations via Model Context Protocol

### Why Use Plugins (vs. Skills or Ad-hoc Prompts)?

| Approach | Use Case | Distribution | Persistence |
|----------|----------|--------------|-------------|
| **Plugins** | Complete workflows, team tooling, external integrations | Marketplace, Git, local | Installed globally or per-project |
| **Skills** | Domain knowledge, autonomous behavior | Within plugins or standalone | Project-scoped |
| **Ad-hoc Prompts** | One-off instructions | None | Session-only |

Plugins provide:
- **Composability**: Bundle multiple components into cohesive toolkits
- **Distribution**: Share via marketplaces or Git repositories
- **Versioning**: Track changes with semantic versioning
- **Team Standardization**: Ensure consistent tooling across developers

### Relationship: Plugins, Skills, and Tools

```
┌─────────────────────────────────────────────────────────────┐
│                      CLAUDE CODE                            │
├─────────────────────────────────────────────────────────────┤
│  Built-in Tools: Read, Write, Bash, Glob, Grep, Edit, etc. │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    PLUGINS                          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │  │Commands │ │ Agents  │ │ Skills  │ │  Hooks  │   │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │            MCP Servers                      │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Plugin Lifecycle Overview

1. **Discovery**: Browse marketplaces via `/plugin` menu or add custom marketplaces
2. **Installation**: `/plugin install plugin-name@marketplace-name`
3. **Enable/Disable**: Configure in settings or via `/plugin enable/disable`
4. **Update**: `/plugin marketplace update marketplace-name`
5. **Removal**: `/plugin uninstall plugin-name@marketplace-name`

---

## 2. Core Concepts & Architecture

### Conceptual Model

A plugin consists of:

```
Plugin = Code + Configuration + Metadata + Assets
         │        │              │          │
         │        │              │          └── Icons, templates, scripts
         │        │              └── Name, version, author, license
         │        └── plugin.json, hooks.json, .mcp.json
         └── Commands, agents, skills (markdown files)
```

### Plugin Boundary

**Inside the plugin** (packaged and distributed):
- Plugin manifest (`plugin.json`)
- Command definitions (`.md` files)
- Agent/skill definitions (`.md` files with frontmatter)
- Hook configurations (`.json` files)
- MCP server configurations
- Helper scripts and utilities
- Documentation (README, CHANGELOG)

**External to the plugin** (not packaged):
- User settings and preferences
- API keys and secrets (via environment variables)
- External services (APIs, databases)
- System tools (git, npm, docker)

### Component Registration

Plugins register components through their manifest and directory structure:

| Component | Registration Method | Invocation |
|-----------|---------------------|------------|
| **Commands** | `commands/` directory or `commands` field | User types `/command-name` |
| **Agents** | `agents/` directory or `agents` field | Claude delegates via Task tool |
| **Skills** | `skills/` directory with `SKILL.md` | Claude auto-invokes based on context |
| **Hooks** | `hooks/hooks.json` or `hooks` field | Automatic on matching events |
| **MCP Servers** | `.mcp.json` or `mcpServers` field | Registered as tools |

---

## 3. Folder & Packaging Layout

### Standard Plugin Directory Structure

```
plugin-name/
├── .claude-plugin/           # REQUIRED: Metadata directory
│   └── plugin.json          # REQUIRED: Plugin manifest
├── commands/                 # OPTIONAL: Slash commands
│   ├── deploy.md
│   ├── review.md
│   └── test.md
├── agents/                   # OPTIONAL: Subagent definitions
│   ├── code-reviewer.md
│   ├── security-scanner.md
│   └── performance-tester.md
├── skills/                   # OPTIONAL: Agent Skills
│   ├── code-review/
│   │   └── SKILL.md
│   └── deployment-expert/
│       ├── SKILL.md
│       └── scripts/
│           └── validate.py
├── hooks/                    # OPTIONAL: Event handlers
│   └── hooks.json
├── .mcp.json                # OPTIONAL: MCP server config
├── scripts/                 # OPTIONAL: Helper scripts
│   ├── format.sh
│   ├── lint.py
│   └── deploy.js
├── LICENSE                  # RECOMMENDED: License file
├── README.md                # RECOMMENDED: Documentation
└── CHANGELOG.md             # RECOMMENDED: Version history
```

### Critical Layout Rules

1. **`.claude-plugin/` contains ONLY `plugin.json`** - No other files
2. **All component directories at plugin root** - NOT inside `.claude-plugin/`
3. **Only create directories you use** - Don't add empty placeholder directories
4. **Skills require `SKILL.md`** - Each skill in its own subdirectory

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Plugin folder | `kebab-case` | `deployment-tools/` |
| Plugin name (in manifest) | `kebab-case` | `"name": "deployment-tools"` |
| Command files | `kebab-case.md` | `run-tests.md` |
| Agent files | `kebab-case.md` | `security-reviewer.md` |
| Skill directories | `kebab-case/` | `code-analysis/` |
| Scripts | `kebab-case.*` | `validate-config.sh` |

### Packaging for Distribution

**Local Development**: Use directory structure as-is

**Git/GitHub Distribution**: Push to repository with standard structure
```bash
# Repository structure
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── ...
└── README.md
```

**Marketplace Distribution**: Reference in `marketplace.json`
```json
{
  "plugins": [
    {
      "name": "my-plugin",
      "source": {
        "source": "github",
        "repo": "owner/my-plugin"
      }
    }
  ]
}
```

---

## 4. Plugin Manifest Specification

The plugin manifest lives at `.claude-plugin/plugin.json`.

### Complete Schema

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Brief explanation of plugin purpose",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://github.com/author"
  },
  "homepage": "https://docs.example.com/plugin",
  "repository": "https://github.com/author/plugin",
  "license": "MIT",
  "keywords": ["deployment", "ci-cd", "automation"],
  "commands": "./custom/commands/",
  "agents": ["./agents/", "./specialized-agents/"],
  "hooks": "./config/hooks.json",
  "mcpServers": {
    "server-name": {
      "command": "${CLAUDE_PLUGIN_ROOT}/bin/server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```

### Field Reference

#### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `name` | string | Unique identifier. Kebab-case, no spaces, max 64 chars | `"deployment-tools"` |

#### Metadata Fields (Recommended)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `version` | string | Semantic version (MAJOR.MINOR.PATCH) | `"2.1.0"` |
| `description` | string | Brief explanation of purpose | `"Deployment automation tools"` |
| `author` | object | Author information | `{"name": "Dev Team"}` |
| `author.name` | string | Author/team name | `"DevTools Team"` |
| `author.email` | string | Contact email | `"team@example.com"` |
| `author.url` | string | Author website/profile | `"https://github.com/author"` |
| `homepage` | string | Documentation URL | `"https://docs.example.com"` |
| `repository` | string | Source code URL | `"https://github.com/org/plugin"` |
| `license` | string | SPDX license identifier | `"MIT"`, `"Apache-2.0"` |
| `keywords` | array | Discovery/categorization tags | `["testing", "automation"]` |

#### Component Path Fields (Optional)

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `commands` | string \| array | Additional command paths | `commands/` |
| `agents` | string \| array | Additional agent paths | `agents/` |
| `hooks` | string \| object | Hook config path or inline | `hooks/hooks.json` |
| `mcpServers` | string \| object | MCP config path or inline | `.mcp.json` |

**Important**: Custom paths **supplement** default directories—they don't replace them.

### Environment Variables

Use `${CLAUDE_PLUGIN_ROOT}` for portable paths:

```json
{
  "mcpServers": {
    "database": {
      "command": "${CLAUDE_PLUGIN_ROOT}/bin/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": {
        "DATA_DIR": "${CLAUDE_PLUGIN_ROOT}/data"
      }
    }
  }
}
```

### Minimal Valid Manifest

```json
{
  "name": "my-plugin"
}
```

### Complete Production Manifest

```json
{
  "name": "enterprise-deployment",
  "version": "2.3.1",
  "description": "Enterprise deployment automation with staging, canary, and production workflows",
  "author": {
    "name": "Platform Team",
    "email": "platform@company.com",
    "url": "https://github.com/company/platform-team"
  },
  "homepage": "https://docs.company.com/plugins/enterprise-deployment",
  "repository": "https://github.com/company/enterprise-deployment-plugin",
  "license": "Apache-2.0",
  "keywords": ["deployment", "kubernetes", "ci-cd", "enterprise"],
  "commands": [
    "./commands/core/",
    "./commands/advanced/"
  ],
  "agents": [
    "./agents/deployment-strategist.md",
    "./agents/rollback-specialist.md"
  ],
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/log-command.sh"
          }
        ]
      }
    ]
  },
  "mcpServers": {
    "k8s-manager": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/k8s-manager",
      "args": ["--kubeconfig", "${HOME}/.kube/config"]
    }
  }
}
```

---

## 5. Commands, Agents, Skills, and Hooks

### Slash Commands

**Location**: `commands/` directory
**Format**: Markdown files with optional frontmatter

```markdown
---
description: Deploy to production environment
allowed-tools: "Bash(kubectl:*),Bash(docker:*),Read,Glob"
---

# Production Deployment

Deploy the current branch to production after validation checks.

## Steps

1. Run test suite
2. Build Docker image
3. Push to registry
4. Apply Kubernetes manifests
5. Verify deployment health

## Usage

Invoke with `/deploy-prod` and provide the target environment.
```

**Invocation**: User types `/command-name` (derived from filename)

### Agents (Subagents)

**Location**: `agents/` directory
**Format**: Markdown files with YAML frontmatter

```markdown
---
name: security-reviewer
description: Reviews code changes for security vulnerabilities and compliance issues
tools: Read, Glob, Grep, Bash(grep:*), Bash(find:*)
model: sonnet
---

# Security Code Review Agent

You are a security-focused code reviewer specializing in:
- OWASP Top 10 vulnerabilities
- Secure coding practices
- Dependency vulnerability analysis
- Secret/credential detection

## Review Process

1. Scan changed files for security patterns
2. Check for hardcoded secrets
3. Analyze input validation
4. Review authentication/authorization logic
5. Generate security report with severity ratings

## Output Format

Provide findings as:
- CRITICAL: Immediate action required
- HIGH: Address before merge
- MEDIUM: Fix in next sprint
- LOW: Improvement suggestion
```

**Frontmatter Fields**:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Agent identifier |
| `description` | Yes | When Claude should delegate to this agent |
| `tools` | No | Comma-separated tool list (inherits all if omitted) |
| `model` | No | `sonnet`, `opus`, `haiku`, or `inherit` |
| `permissionMode` | No | Permission mode for agent execution |
| `skills` | No | Skills to auto-load |

### Skills

**Location**: `skills/skill-name/SKILL.md`
**Format**: Markdown with YAML frontmatter

```markdown
---
name: kubernetes-expert
description: >
  Expert on Kubernetes deployments, configurations, and troubleshooting.
  Use when user works with K8s manifests, pods, services, or cluster issues.
  Trigger with 'kubernetes', 'k8s', 'deploy to cluster', 'pod issues'.
allowed-tools: "Read,Glob,Grep,Bash(kubectl:*)"
version: "1.0.0"
---

# Kubernetes Expert Skill

Transform Claude into a Kubernetes specialist for cluster management.

## Capabilities

- Manifest generation and validation
- Deployment strategy recommendations
- Troubleshooting pod/service issues
- Resource optimization

## Instructions

### When Reviewing Manifests
1. Check resource limits
2. Validate label selectors
3. Verify security contexts
4. Suggest best practices

### When Troubleshooting
1. Check pod status and events
2. Review container logs
3. Analyze resource constraints
4. Identify networking issues
```

**See**: `6767-b-SPEC-DR-STND-claude-skills-standard.md` for complete skill specification.

### Hooks

**Location**: `hooks/hooks.json` or inline in `plugin.json`
**Format**: JSON configuration

```json
{
  "description": "Automatic formatting and validation hooks",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
            "timeout": 30
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate-command.sh"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/init-environment.sh"
          }
        ]
      }
    ]
  }
}
```

**Hook Events**:

| Event | Matcher Required | Use Case |
|-------|------------------|----------|
| `PreToolUse` | Yes | Validate/modify tool inputs, control permissions |
| `PostToolUse` | Yes | Process results, trigger actions |
| `PermissionRequest` | Yes | Auto-approve/deny permissions |
| `UserPromptSubmit` | No | Add context to prompts |
| `Stop` | No | Prevent premature stops |
| `SubagentStop` | No | Control subagent completion |
| `SessionStart` | Yes | Initialize environment |
| `SessionEnd` | No | Cleanup operations |
| `PreCompact` | Yes | Before context compaction |
| `Notification` | Optional | Handle notifications |

**Hook Types**:

| Type | Description | Example |
|------|-------------|---------|
| `command` | Execute bash command | `{"type": "command", "command": "./script.sh"}` |
| `prompt` | LLM-based evaluation | `{"type": "prompt", "prompt": "Evaluate: $ARGUMENTS"}` |

**Hook Output (JSON)**:

```json
{
  "continue": true,
  "stopReason": "Optional reason to stop",
  "suppressOutput": false,
  "systemMessage": "Message shown to user",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "Reason for decision",
    "updatedInput": { "modified_field": "new_value" }
  }
}
```

---

## 6. Marketplace & Registry Specification

### Built-in Marketplace

Claude Code includes access to the official Anthropic marketplace at `anthropics/claude-plugins-official`.

**Browsing**: `/plugin` menu → Discover
**Installing**: `/plugin install plugin-name@marketplace-name`

### Marketplace Configuration File

Marketplaces are configured via `.claude-plugin/marketplace.json`:

```json
{
  "name": "company-tools",
  "owner": {
    "name": "DevTools Team",
    "email": "devtools@company.com"
  },
  "metadata": {
    "description": "Company-wide development tools and automation",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "code-formatter",
      "source": "./plugins/formatter",
      "description": "Automatic code formatting",
      "version": "2.1.0",
      "author": { "name": "DevTools Team" },
      "license": "MIT",
      "keywords": ["formatting", "code-quality"],
      "category": "productivity"
    },
    {
      "name": "deployment-tools",
      "source": {
        "source": "github",
        "repo": "company/deploy-plugin"
      },
      "description": "Deployment automation",
      "version": "1.5.0"
    }
  ]
}
```

### Marketplace Schema

#### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Marketplace identifier (kebab-case) |
| `owner` | object | Marketplace maintainer info |
| `plugins` | array | List of available plugins |

#### Optional Metadata

| Field | Type | Description |
|-------|------|-------------|
| `metadata.description` | string | Marketplace description |
| `metadata.version` | string | Marketplace version |
| `metadata.pluginRoot` | string | Base path for relative sources |

### Plugin Entry Schema

Plugin entries inherit from `plugin.json` schema (all fields optional except `name`) plus:

| Field | Type | Description |
|-------|------|-------------|
| `source` | string \| object | **Required**. Where to fetch the plugin |
| `category` | string | Plugin category for organization |
| `tags` | array | Additional discovery tags |
| `strict` | boolean | Require `plugin.json` in source (default: `true`) |

### Source Types

#### 1. Relative Path (Same Repository)

```json
{
  "name": "local-plugin",
  "source": "./plugins/local-plugin"
}
```

#### 2. GitHub Repository

```json
{
  "name": "github-plugin",
  "source": {
    "source": "github",
    "repo": "owner/plugin-repo"
  }
}
```

#### 3. Git URL

```json
{
  "name": "git-plugin",
  "source": {
    "source": "git",
    "url": "https://gitlab.com/team/plugin.git"
  }
}
```

#### 4. Local Directory (Development)

```json
{
  "name": "dev-plugin",
  "source": {
    "source": "directory",
    "path": "/path/to/local/plugin"
  }
}
```

### Configuring Custom Marketplaces

Add to `.claude/settings.json` (project) or `~/.claude/settings.json` (user):

```json
{
  "extraKnownMarketplaces": {
    "company-tools": {
      "source": {
        "source": "github",
        "repo": "company/claude-plugins"
      }
    },
    "team-plugins": {
      "source": {
        "source": "git",
        "url": "https://git.company.com/team/plugins.git"
      }
    },
    "local-dev": {
      "source": {
        "source": "directory",
        "path": "/home/dev/claude-plugins"
      }
    }
  },
  "enabledPlugins": {
    "formatter@company-tools": true,
    "deployer@company-tools": true,
    "test-runner@team-plugins": true
  }
}
```

### Marketplace Priority and Conflicts

1. **Priority**: Later-added marketplaces override earlier ones for same plugin name
2. **Conflicts**: Plugin ID includes marketplace: `plugin-name@marketplace-name`
3. **Resolution**: Explicitly specify marketplace when installing

### Publishing to a Marketplace

1. **Create plugin** following standard structure
2. **Add entry** to `marketplace.json`:
   ```json
   {
     "name": "your-plugin",
     "source": "./plugins/your-plugin",
     "description": "What it does",
     "version": "1.0.0",
     "keywords": ["relevant", "tags"]
   }
   ```
3. **Commit and push** to marketplace repository
4. **Users update**: `/plugin marketplace update marketplace-name`

### Strict vs Non-Strict Mode

| Setting | Behavior |
|---------|----------|
| `strict: true` (default) | Plugin must have `plugin.json`; marketplace fields supplement |
| `strict: false` | Marketplace entry serves as complete manifest if no `plugin.json` |

---

## 7. Plugin Lifecycle: Development, Testing, and Release

### Development Workflow

#### 1. Create Plugin Structure

```bash
mkdir -p my-plugin/.claude-plugin
mkdir -p my-plugin/commands
mkdir -p my-plugin/agents

cat > my-plugin/.claude-plugin/plugin.json << 'EOF'
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "Development version of my plugin"
}
EOF
```

#### 2. Develop Components

Create commands, agents, skills, or hooks as needed.

#### 3. Test Locally

```bash
# Add local marketplace for testing
# In ~/.claude/settings.json:
{
  "extraKnownMarketplaces": {
    "local-dev": {
      "source": {
        "source": "directory",
        "path": "/path/to/my-plugin"
      }
    }
  }
}

# Start Claude Code with debug mode
claude --debug

# Test plugin loading
/plugin install my-plugin@local-dev
```

#### 4. Validate Plugin

```bash
/plugin validate my-plugin@local-dev
```

#### 5. Debug Issues

```bash
# Enable debug output
claude --debug

# Check for:
# - Manifest parsing errors
# - Component registration
# - Hook execution
# - MCP server initialization
```

### Release Workflow

#### 1. Update Version

```bash
# Bump version in plugin.json
# Follow semver: MAJOR.MINOR.PATCH
```

#### 2. Update Changelog

```markdown
## [1.2.0] - 2025-12-06

### Added
- New `/deploy-canary` command
- Support for blue-green deployments

### Changed
- Improved rollback speed

### Fixed
- Fixed timeout in long deployments
```

#### 3. Tag Release

```bash
git add .
git commit -m "release: v1.2.0"
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags
```

#### 4. Update Marketplace Entry

```json
{
  "name": "my-plugin",
  "version": "1.2.0",
  "source": {
    "source": "github",
    "repo": "myorg/my-plugin"
  }
}
```

### Backward Compatibility Guidelines

1. **Non-breaking changes**: New commands, optional parameters, bug fixes
2. **Breaking changes**: Removed commands, changed behavior, renamed components
3. **Deprecation process**:
   - Mark deprecated in description: `"[DEPRECATED] Old command..."`
   - Keep working for one minor version
   - Remove in next major version

### Migration Strategies

When breaking changes are necessary:

1. **Document migration path** in CHANGELOG and README
2. **Provide migration script** if possible
3. **Support parallel versions** temporarily
4. **Announce deprecation** in release notes

---

## 8. Security & Safety Guidelines

### Minimal Permissions Principle

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
          }
        ]
      }
    ]
  }
}
```

**Only request tools you need**:
- Read-only operations: `"Read,Glob,Grep"`
- File modifications: `"Read,Write,Edit,Glob,Grep"`
- Shell commands: `"Bash(git:*),Bash(npm run:*)"`

### Dangerous Operations

**Avoid**:
- Unrestricted `Bash` access
- Hardcoded credentials
- Unvalidated user input to shell
- Network calls without timeout
- File operations outside project

**Instead**:
- Scope bash: `Bash(git:*)`, `Bash(npm run test:*)`
- Use environment variables for secrets
- Sanitize all inputs
- Set timeouts on hooks
- Use `${CLAUDE_PLUGIN_ROOT}` for paths

### Secrets and Tokens

```json
{
  "mcpServers": {
    "api-server": {
      "command": "${CLAUDE_PLUGIN_ROOT}/bin/server",
      "env": {
        "API_KEY": "${API_KEY}",
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

**Never**:
- Hardcode API keys in plugin files
- Store secrets in plugin.json
- Log sensitive data

**Always**:
- Use environment variables
- Document required env vars in README
- Provide setup instructions

### Security Audit Checklist

Before publishing, verify:

- [ ] No hardcoded secrets or API keys
- [ ] All bash commands are scoped appropriately
- [ ] Scripts validate and sanitize inputs
- [ ] Network calls have timeouts
- [ ] File paths use `${CLAUDE_PLUGIN_ROOT}`
- [ ] No path traversal vulnerabilities (`..` not in user inputs)
- [ ] Sensitive files excluded (`.env`, credentials)
- [ ] Dependencies are from trusted sources
- [ ] MCP servers don't expose sensitive data

### Marketplace Security Warning

From official docs:
> ⚠️ **Trust Warning**: Users must trust plugins before installing. Anthropic does not control MCP servers, files, or included software, and cannot verify intended functionality or future changes.

---

## 9. Versioning, Compatibility, and Support

### Semantic Versioning

```
MAJOR.MINOR.PATCH
  │     │     └── Bug fixes, documentation
  │     └──────── New features, backward-compatible
  └────────────── Breaking changes
```

**Examples**:
- `1.0.0` → `1.0.1`: Bug fix
- `1.0.1` → `1.1.0`: New command added
- `1.1.0` → `2.0.0`: Command removed or renamed

### Compatibility Constraints

Document in README:

```markdown
## Compatibility

- **Claude Code**: v2.0.0+
- **Platform**: macOS, Linux, Windows (WSL)
- **Node.js**: 18+ (for MCP servers)
- **Python**: 3.10+ (for scripts)
```

### Long-Term Maintenance

1. **Monitor Claude Code releases** for breaking changes
2. **Test plugins** against new Claude Code versions
3. **Update dependencies** regularly
4. **Respond to issues** promptly
5. **Document EOL timeline** for major versions

### Deprecation Policy

```markdown
## Deprecation Notice

### v1.x (Current)
- Status: Active
- Support: Full support

### v0.x (Legacy)
- Status: Deprecated
- Support: Security fixes only until 2025-06-01
- Migration: See MIGRATION.md
```

---

## 10. Production-Readiness Checklist

### Pre-Publish Validation

#### Manifest
- [ ] `name` is kebab-case, unique, descriptive
- [ ] `version` follows semver
- [ ] `description` clearly explains purpose
- [ ] `author` information is complete
- [ ] `license` specified (SPDX identifier)
- [ ] `keywords` aid discovery
- [ ] `repository` points to source

#### Components
- [ ] All commands documented
- [ ] Agents have clear descriptions
- [ ] Skills follow standard schema
- [ ] Hooks have appropriate matchers
- [ ] MCP servers use `${CLAUDE_PLUGIN_ROOT}`

#### Security
- [ ] No hardcoded secrets
- [ ] Bash commands appropriately scoped
- [ ] Inputs validated/sanitized
- [ ] Timeouts configured
- [ ] Paths are relative with `${CLAUDE_PLUGIN_ROOT}`

#### Testing
- [ ] Plugin loads without errors (`claude --debug`)
- [ ] Commands execute correctly
- [ ] Agents respond appropriately
- [ ] Hooks fire on expected events
- [ ] MCP servers initialize

#### Documentation
- [ ] README explains installation
- [ ] README documents usage
- [ ] README lists requirements
- [ ] CHANGELOG tracks versions
- [ ] Environment variables documented

#### Marketplace
- [ ] Marketplace entry complete
- [ ] Source URL accessible
- [ ] Version matches plugin.json
- [ ] Keywords appropriate

---

## Appendix A: Canonical Plugin Skeleton

### Directory Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── commands/
│   └── example.md           # Example command
├── agents/
│   └── example-agent.md     # Example agent
├── skills/
│   └── example-skill/
│       └── SKILL.md         # Example skill
├── hooks/
│   └── hooks.json           # Hook configuration
├── scripts/
│   └── validate.sh          # Helper script
├── LICENSE
├── README.md
└── CHANGELOG.md
```

### plugin.json

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "TODO: Describe your plugin",
  "author": {
    "name": "TODO: Your Name",
    "email": "TODO: your@email.com"
  },
  "repository": "TODO: https://github.com/you/my-plugin",
  "license": "MIT",
  "keywords": ["TODO", "add", "keywords"]
}
```

### commands/example.md

```markdown
---
description: Example command that demonstrates plugin structure
allowed-tools: "Read,Glob,Grep"
---

# Example Command

This command demonstrates the basic structure of a plugin command.

## Usage

Invoke with `/example` and describe what you want to accomplish.

## Steps

1. Analyze the request
2. Execute appropriate actions
3. Report results
```

### agents/example-agent.md

```markdown
---
name: example-agent
description: Example agent for demonstrating plugin structure
tools: Read, Glob, Grep
model: sonnet
---

# Example Agent

You are an example agent demonstrating the plugin agent structure.

## Capabilities

- Analyze code structure
- Provide recommendations
- Generate reports

## Instructions

When invoked, analyze the user's request and provide helpful assistance.
```

### skills/example-skill/SKILL.md

```markdown
---
name: example-skill
description: >
  Example skill demonstrating plugin skill structure.
  Use when demonstrating skills capabilities.
allowed-tools: "Read,Glob,Grep"
version: "1.0.0"
---

# Example Skill

This skill demonstrates the structure of a plugin skill.

## Overview

Provides example functionality for demonstration purposes.

## Instructions

### Step 1: Analyze Context
Review the current context and user request.

### Step 2: Apply Knowledge
Use skill knowledge to assist.

## Output

Provide clear, actionable guidance.
```

### hooks/hooks.json

```json
{
  "description": "Example hooks configuration",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### scripts/validate.sh

```bash
#!/bin/bash
# Example validation script
# Receives JSON input via stdin

set -e

# Read input
INPUT=$(cat)

# Parse tool info (using jq if available)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || echo "unknown")

# Perform validation
echo "Validated: $TOOL_NAME" >&2

# Return success
exit 0
```

### README.md

```markdown
# My Plugin

TODO: Describe your plugin.

## Installation

```bash
/plugin install my-plugin@marketplace-name
```

## Usage

- `/example` - Run the example command

## Requirements

- Claude Code v2.0.0+
- TODO: List other requirements

## Configuration

Set these environment variables:
- `TODO_API_KEY` - API key for TODO service

## License

MIT
```

---

## Appendix B: Canonical Marketplace Configuration

### marketplace.json Template

```json
{
  "name": "company-marketplace",
  "owner": {
    "name": "Company DevTools Team",
    "email": "devtools@company.com"
  },
  "metadata": {
    "description": "Company-wide Claude Code plugins",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "code-quality",
      "source": "./plugins/code-quality",
      "description": "Code quality tools including linting and formatting",
      "version": "2.0.0",
      "author": {
        "name": "Quality Team",
        "email": "quality@company.com"
      },
      "license": "MIT",
      "keywords": ["linting", "formatting", "code-quality"],
      "category": "quality"
    },
    {
      "name": "deployment-suite",
      "source": {
        "source": "github",
        "repo": "company/deployment-plugin"
      },
      "description": "Full deployment pipeline automation",
      "version": "3.1.0",
      "keywords": ["deployment", "ci-cd", "kubernetes"],
      "category": "devops"
    },
    {
      "name": "experimental-tools",
      "source": {
        "source": "git",
        "url": "https://git.company.com/experimental/tools.git"
      },
      "description": "Experimental tools in development",
      "version": "0.5.0",
      "strict": false,
      "keywords": ["experimental"],
      "category": "experimental"
    }
  ]
}
```

### settings.json Marketplace Configuration

```json
{
  "extraKnownMarketplaces": {
    "company-tools": {
      "source": {
        "source": "github",
        "repo": "company/claude-plugins"
      }
    },
    "team-internal": {
      "source": {
        "source": "git",
        "url": "https://git.company.com/team/plugins.git"
      }
    },
    "local-development": {
      "source": {
        "source": "directory",
        "path": "/home/dev/plugin-workspace"
      }
    }
  },
  "enabledPlugins": {
    "code-quality@company-tools": true,
    "deployment-suite@company-tools": true,
    "debug-tools@team-internal": true,
    "my-plugin@local-development": true
  }
}
```

---

## Appendix C: Author Checklists

### New Plugin Creation Checklist

- [ ] Create `.claude-plugin/plugin.json` with required fields
- [ ] Add `name`, `version`, `description`
- [ ] Create component directories (commands/, agents/, skills/, hooks/)
- [ ] Write initial command or agent
- [ ] Create README.md with installation/usage instructions
- [ ] Add LICENSE file
- [ ] Test locally with `claude --debug`
- [ ] Verify plugin loads and components register

### Pre-Publish Checklist

- [ ] Version bumped appropriately (semver)
- [ ] CHANGELOG.md updated
- [ ] All components documented
- [ ] README.md complete and accurate
- [ ] No hardcoded secrets
- [ ] Security audit checklist passed
- [ ] Tested with latest Claude Code
- [ ] Marketplace entry updated (if applicable)
- [ ] Git tagged with version

### Post-Publish Maintenance Checklist

- [ ] Monitor for user issues
- [ ] Test against new Claude Code releases
- [ ] Update dependencies as needed
- [ ] Respond to security vulnerabilities
- [ ] Plan next version features
- [ ] Update documentation as needed
- [ ] Archive old versions appropriately

---

## Open Questions / Potentially Out-of-Date Areas

### Areas Requiring Verification

1. **Plugin Permissions Inheritance**: How exactly do `allowed-tools` in skills/agents interact with plugin-level permissions? Verify in your environment.

2. **MCP Server Auto-Start**: Documentation states MCP servers "automatically start when the plugin is enabled" - verify startup timing and error handling.

3. **Marketplace Update Mechanism**: The exact process for how users receive plugin updates when a marketplace is updated needs verification.

4. **Source Type `"url"`**: Some examples show `"source": "url"` while others use `"source": "git"`. Verify current accepted values.

5. **Enterprise Managed Settings**: The exact schema and precedence for enterprise managed policy files may vary by deployment.

### Experimental/Unstable Areas

1. **Prompt-based Hooks**: `type: "prompt"` for hooks is documented but behavior may evolve.

2. **Hook Input Modification**: `updatedInput` in PreToolUse hooks (v2.0.10+) is a newer feature.

3. **Nested Sandbox Settings**: `enableWeakerNestedSandbox` for Docker containers is platform-specific.

### How to Future-Proof

1. **Re-run research periodically**: Claude Code is in public beta; features evolve rapidly.

2. **Test against official docs**: Always verify against https://code.claude.com/docs/en/

3. **Monitor GitHub releases**: Watch https://github.com/anthropics/claude-code for updates

4. **Check official blog**: https://www.claude.com/blog for feature announcements

5. **Validate in environment**: Test specific behaviors rather than assuming documentation accuracy.

---

**Last Updated**: 2025-12-07
**Status**: CANONICAL - Cross-Repo Standard
**Next Review**: Re-validate when Claude Code releases major version updates
