# Claude Code Plugins - Architecture Diagrams

**Generated:** 2025-10-16

---

## 1. Repository Structure Overview

```
claude-code-plugins/
│
├── CORE CATALOG
│   ├── .claude-plugin/
│   │   ├── marketplace.extended.json    [SOURCE - manual edits]
│   │   └── marketplace.json             [GENERATED - auto-synced via script]
│   │
│   └── scripts/
│       ├── sync-marketplace.cjs         [Generates ↑ from extended]
│       ├── validate-all.sh              [Quality checks]
│       ├── check-frontmatter.py         [Markdown validation]
│       └── test-installation.sh         [Installation testing]
│
├── PLUGINS (226 total)
│   ├── mcp/                             [5 executable plugins]
│   │   ├── project-health-auditor/
│   │   ├── conversational-api-debugger/
│   │   ├── domain-memory-agent/
│   │   ├── design-to-code/
│   │   └── workflow-orchestrator/
│   │
│   ├── packages/                        [4 plugin packs]
│   │   ├── devops-automation-pack/      [25 components]
│   │   ├── security-pro-pack/           [10 components]
│   │   ├── fullstack-starter-pack/      [15 components]
│   │   └── ai-ml-engineering-pack/      [12 components]
│   │
│   ├── examples/                        [3 learning plugins]
│   │   ├── hello-world/
│   │   ├── formatter/
│   │   └── security-agent/
│   │
│   └── [12 Category Directories]        [Total 200+ plugins]
│       ├── devops/           → 25+
│       ├── ai-ml/            → 25+
│       ├── security/         → 25+
│       ├── api-development/  → 25+
│       ├── database/         → 25+
│       ├── testing/          → 25+
│       ├── crypto/           → 25+
│       ├── performance/      → 25+
│       ├── productivity/     → Var
│       ├── finance/          → New
│       ├── ai-agency/        → 6
│       └── community/        → Var
│
├── WEBSITE
│   └── marketplace/          [Astro 5 + Tailwind 4]
│       ├── src/
│       │   ├── components/   [React components]
│       │   ├── pages/        [Astro pages]
│       │   ├── content/      [Markdown]
│       │   ├── layouts/      [Page layouts]
│       │   └── styles/       [Tailwind CSS]
│       ├── dist/             [Built output → GitHub Pages]
│       └── package.json
│
├── TEMPLATES
│   ├── minimal-plugin/       [Bare minimum]
│   ├── command-plugin/       [With slash commands]
│   ├── agent-plugin/         [With subagent]
│   └── full-plugin/          [All features]
│
├── DOCUMENTATION
│   ├── docs/
│   │   ├── USER_SECURITY_GUIDE.md
│   │   ├── creating-plugins.md
│   │   ├── getting-started.md
│   │   └── learning-paths/
│   │       ├── 01-quick-start/
│   │       ├── 02-plugin-creator/
│   │       ├── 03-advanced-developer/
│   │       └── use-cases/
│   ├── README.md
│   ├── CONTRIBUTING.md
│   ├── SECURITY.md
│   └── CHANGELOG.md
│
└── CI/CD
    └── .github/
        ├── workflows/
        │   ├── validate-plugins.yml        [JSON, structure, perms]
        │   ├── release.yml                 [Versioning]
        │   ├── deploy-marketplace.yml      [GitHub Pages]
        │   ├── codeql.yml                  [Security scan]
        │   └── security-audit.yml          [Dependency check]
        └── ISSUE_TEMPLATE/
```

---

## 2. Plugin Distribution Flow

```
┌─────────────────────────────────────────────────────────┐
│  Developer Workflow                                      │
└─────────────────────────────────────────────────────────┘

1. LOCAL DEVELOPMENT
   ┌──────────────────────────┐
   │ Create/Edit Plugin Files │
   │ ├── .claude-plugin/plugin.json
   │ ├── README.md
   │ ├── LICENSE
   │ └── [components]
   └──────────────────────────┘
              ↓
   ┌──────────────────────────┐
   │ Run Local Validation     │
   │ $ ./scripts/validate-all.sh
   └──────────────────────────┘
              ↓
   ┌──────────────────────────┐
   │ Test Installation        │
   │ $ ./scripts/test-installation.sh
   └──────────────────────────┘
              ↓
   ┌──────────────────────────┐
   │ Test with Plugin CLI     │
   │ $ /plugin install test-plugin@test
   └──────────────────────────┘
              ↓
   
2. PUSH TO REPOSITORY
   ┌──────────────────────────┐
   │ Edit marketplace.extended.json
   │ (add plugin entry)
   └──────────────────────────┘
              ↓
   ┌──────────────────────────┐
   │ $ pnpm run sync-marketplace
   │ (generates marketplace.json)
   └──────────────────────────┘
              ↓
   ┌──────────────────────────┐
   │ Commit & Push
   │ $ git push origin feature/plugin
   └──────────────────────────┘
              ↓
   
3. CI VALIDATION
   ┌──────────────────────────────────────────┐
   │ GitHub Actions: validate-plugins.yml     │
   │ ├── Sync check (marketplace.json)        │
   │ ├── JSON validation                      │
   │ ├── Plugin structure check               │
   │ ├── Script permissions check             │
   │ ├── Markdown frontmatter validation      │
   │ └── Status: PASS/FAIL                    │
   └──────────────────────────────────────────┘
              ↓
   ┌──────────────────────────┐
   │ Review & Merge PR        │
   │ → Merge to main branch   │
   └──────────────────────────┘
              ↓
   
4. DISTRIBUTION
   ┌────────────────────────────────────┐
   │ GitHub Actions: deploy-marketplace │
   │ ├── Build website (Astro)          │
   │ ├── Deploy to GitHub Pages         │
   │ └── Live at claudecodeplugins.io   │
   └────────────────────────────────────┘
              ↓
   ┌────────────────────────────────────┐
   │ Available to Users                 │
   │ $ /plugin marketplace add           │
   │   jeremylongshore/claude-code-plugins
   │ $ /plugin install new-plugin@...   │
   └────────────────────────────────────┘
```

---

## 3. Plugin Catalog Sync Process

```
┌────────────────────────────────────────────────────────────┐
│ Catalog Synchronization Pipeline                           │
└────────────────────────────────────────────────────────────┘

Developer makes change to plugin:
        ↓
┌─────────────────────────────────────────────────────────┐
│ .claude-plugin/marketplace.extended.json                │
│ {                                                        │
│   "plugins": [                                           │
│     {                                                    │
│       "name": "my-new-plugin",                           │
│       "source": "./plugins/category/my-new-plugin",    │
│       "description": "...",                             │
│       "version": "1.0.0",                               │
│       "category": "devops",                             │
│       ...                                               │
│     }                                                    │
│   ]                                                      │
│ }                                                        │
└─────────────────────────────────────────────────────────┘
        ↓ (pnpm run sync-marketplace)
┌──────────────────────────────────────┐
│ scripts/sync-marketplace.cjs          │
│ • Read extended catalog              │
│ • Apply transformations              │
│ • Generate CLI-compatible format     │
└──────────────────────────────────────┘
        ↓ (AUTO-GENERATED)
┌─────────────────────────────────────────────────────────┐
│ .claude-plugin/marketplace.json                         │
│ (Used by Claude CLI for /plugin install commands)      │
└─────────────────────────────────────────────────────────┘
        ↓ (CI verification)
┌──────────────────────────────────────┐
│ validate-plugins.yml                  │
│ • Verify no manual edits to .json    │
│ • Check against .extended.json       │
│ • Fail if out of sync                │
└──────────────────────────────────────┘
        ↓ (GitHub Pages deployment)
┌──────────────────────────────────────┐
│ claudecodeplugins.io (website)       │
│ • Reads marketplace.json             │
│ • Displays plugin cards              │
│ • Provides search/filter             │
└──────────────────────────────────────┘
```

---

## 4. Plugin Architecture Types

```
TYPE 1: AI INSTRUCTION PLUGINS (221 plugins)
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  plugin.json                                            │
│  ├── name: "my-plugin"                                  │
│  ├── version: "1.0.0"                                   │
│  └── description: "..."                                 │
│                                                          │
│  README.md (documentation)                              │
│                                                          │
│  commands/                (optional)                     │
│  ├── command1.md          → Becomes /command1            │
│  └── command2.md          → Becomes /command2            │
│                                                          │
│  agents/                  (optional)                     │
│  └── expert-agent.md      → Specialized AI subagent     │
│                                                          │
│  hooks/hooks.json         (optional)                     │
│  └── Event-driven automation                            │
│                                                          │
│  scripts/                 (optional)                     │
│  └── automation.sh        → Shell automation            │
│                                                          │
│  EXECUTION: Claude interprets markdown instructions     │
│  NO CODE EXECUTION                                      │
│                                                          │
└─────────────────────────────────────────────────────────┘

TYPE 2: MCP EXECUTABLE PLUGINS (5 plugins)
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  plugin.json                                            │
│  ├── name: "project-health-auditor"                     │
│  ├── version: "1.0.0"                                   │
│  └── mcpTools: 4                                        │
│                                                          │
│  src/                                                   │
│  └── TypeScript source code                            │
│      ├── index.ts                                       │
│      ├── tools/                                         │
│      │   ├── listRepoFiles.ts  → Tool 1                 │
│      │   ├── fileMetrics.ts    → Tool 2                 │
│      │   ├── gitChurn.ts       → Tool 3                 │
│      │   └── mapTests.ts       → Tool 4                 │
│      └── ...                                            │
│                                                          │
│  dist/                                                  │
│  └── Compiled JavaScript (13-26KB)                     │
│                                                          │
│  package.json                                          │
│  ├── @modelcontextprotocol/sdk                         │
│  ├── zod (validation)                                  │
│  └── other dependencies                                │
│                                                          │
│  EXECUTION: Runs as separate Node.js process           │
│  Claude calls tools via MCP protocol                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Monorepo Structure (pnpm workspace)

```
claude-code-plugins/
│
├── pnpm-workspace.yaml
│   └── packages:
│       ├── 'plugins/mcp/*'      [All MCP plugins]
│       └── 'marketplace'        [Astro website]
│
├── package.json (ROOT)
│   └── devDependencies:
│       ├── typescript: ^5.5.0
│       ├── vitest: ^2.0.0
│       ├── eslint: ^9.0.0
│       ├── prettier: ^3.3.0
│       └── @types/node: ^20.19.21
│
│   └── scripts:
│       ├── pnpm dev              → Runs in ALL packages
│       ├── pnpm build            → Runs in ALL packages
│       ├── pnpm test             → Runs in ALL packages
│       ├── pnpm lint             → Runs in ALL packages
│       ├── pnpm typecheck        → Runs in ALL packages
│       └── pnpm sync-marketplace → Custom script
│
├── plugins/mcp/
│   │
│   ├── project-health-auditor/
│   │   ├── package.json          [Own dependencies]
│   │   ├── tsconfig.json
│   │   ├── src/                  [TypeScript]
│   │   └── dist/                 [Compiled JS]
│   │
│   ├── conversational-api-debugger/
│   │   └── [same structure]
│   │
│   └── [other MCP plugins...]
│
└── marketplace/
    ├── package.json              [Astro dependencies]
    ├── tsconfig.json
    ├── astro.config.mjs
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── layouts/
    │   └── styles/
    └── dist/                     [Built website]

Commands:
├── pnpm dev                       → All packages dev mode (parallel)
├── pnpm build                     → All packages build
├── pnpm --filter project-health-auditor build
│                                 → Single package only
└── pnpm --filter '*' typecheck   → All packages typecheck
```

---

## 6. CI/CD Pipeline

```
GITHUB ACTIONS WORKFLOW

┌────────────────────────────────────────────────────────────┐
│ TRIGGER EVENTS                                             │
└────────────────────────────────────────────────────────────┘

1. Pull Request to main
   └─ validate-plugins.yml ──┐
                              │
2. Push to main               │
   └─ validate-plugins.yml ───┤
      security-audit.yml ─────┼────┐
      deploy-marketplace.yml ──┤    │
                              │    │
3. Manual dispatch            │    │
   └─ release.yml ────────────┼────┤
                              │    │
┌─────────────────────────────┼────┼──────────────────────┐
│ VALIDATE PLUGINS.YML (runs every time)                  │
├─────────────────────────────┼────┼──────────────────────┤
│ Step 1: Sync Marketplace   │    │                       │
│   - Check marketplace.json sync status                  │
│   - Fail if manual edits detected                       │
│                                                          │
│ Step 2: JSON Validation                                │
│   - Parse all .json files with jq                       │
│   - Validate plugin.json schema                         │
│                                                          │
│ Step 3: Plugin Structure                               │
│   - Check .claude-plugin/plugin.json exists            │
│   - Check README.md exists                             │
│   - Check LICENSE file exists                          │
│                                                          │
│ Step 4: Script Permissions                             │
│   - Verify chmod +x on all .sh files                   │
│   - Fail if any scripts not executable                 │
│                                                          │
│ Step 5: Markdown Frontmatter                           │
│   - Validate YAML in commands/agents                   │
│   - Check required fields                              │
│                                                          │
│ Result: ✓ PASS or ✗ FAIL                               │
│ ├─ PASS  → Allow PR merge                              │
│ └─ FAIL  → Block PR, show errors                       │
└─────────────────────────────────────────────────────────┘
   │    │    │
   │    │    └─────────────────────────────────────────┐
   │    │                                              │
   │    ├─ deploy-marketplace.yml (if on main)        │
   │    │  ├─ Run validate (as above)                 │
   │    │  ├─ npm run build (marketplace/)            │
   │    │  ├─ Deploy dist/ to GitHub Pages            │
   │    │  └─ Live at claudecodeplugins.io            │
   │    │                                              │
   │    └─ security-audit.yml (if on main)            │
   │       ├─ CodeQL analysis                         │
   │       └─ npm audit (dependencies)                │
   │                                                   │
   └─ release.yml (manual dispatch)                   │
      ├─ Create GitHub release                        │
      ├─ Generate changelog                           │
      └─ Tag semantic version                         │
```

---

## 7. Plugin Component Relationships

```
COMPLETE PLUGIN EXAMPLE

plugins/security/my-security-plugin/
│
├── .claude-plugin/plugin.json
│   └── Metadata: name, version, description, author
│
├── README.md
│   └── Documentation: features, usage, examples
│
├── LICENSE
│   └── MIT or Apache-2.0
│
├── commands/
│   ├── audit.md              → Claude registers /audit command
│   │   YAML Frontmatter:
│   │   - title
│   │   - description
│   │   - keywords
│   │
│   └── compliance.md         → Claude registers /compliance command
│
├── agents/
│   ├── security-expert.md    → Specialized security analysis agent
│   │   YAML Frontmatter:
│   │   - title
│   │   - description
│   │   - systemPrompt
│   │
│   └── threat-modeler.md     → Threat modeling agent
│
├── hooks/hooks.json
│   ├── PostToolUse           → Triggers after tool execution
│   ├── PreToolUse            → Triggers before tool execution
│   └── OnFileChange          → Triggers when file edited
│
├── scripts/
│   ├── security-scan.sh      → chmod +x required
│   └── generate-report.sh    → chmod +x required
│
└── mcp/ (if MCP-enabled)
    ├── tools.json            → MCP tool definitions
    └── config.json           → MCP configuration

REGISTRATION FLOW:
└─ User: /plugin install my-security-plugin
   ├─ Claude reads .claude-plugin/plugin.json
   ├─ Register commands (commands/*.md)
   ├─ Register agents (agents/*.md)
   ├─ Register hooks (hooks/hooks.json)
   ├─ Connect MCP tools (mcp/*.json)
   └─ Make scripts available
```

---

## 8. Deployment Architecture

```
┌───────────────────────────────────────────────────────────┐
│ LOCAL DEVELOPMENT ENVIRONMENT                             │
├───────────────────────────────────────────────────────────┤
│                                                            │
│  Developer Machine                                         │
│  ├── pnpm install                                         │
│  ├── pnpm dev                                             │
│  │   ├── Marketplace: localhost:4321                      │
│  │   └── MCP Plugins: watch mode                          │
│  │                                                         │
│  └── ./scripts/validate-all.sh                            │
│      └── Pre-commit validation                            │
│                                                            │
└───────────────────────────────────────────────────────────┘
                      ↓
┌───────────────────────────────────────────────────────────┐
│ GITHUB REPOSITORY (Main)                                  │
├───────────────────────────────────────────────────────────┤
│                                                            │
│  Branches:                                                 │
│  ├── main                   [Production]                  │
│  ├── feature/plugin-name    [Development]                │
│  └── bugfix/fix-description [Hotfixes]                   │
│                                                            │
│  On Push to main:                                         │
│  ├─ Trigger GitHub Actions                               │
│  ├─ Run validate-plugins.yml                             │
│  ├─ Run security-audit.yml                               │
│  └─ Run deploy-marketplace.yml                           │
│                                                            │
└───────────────────────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────────────────────┐
│ GITHUB PAGES HOSTING                                    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Repository: claude-code-plugins/dist                  │
│  ├─ Builds from: marketplace/ directory                │
│  ├─ Static files in dist/                              │
│  ├─ Auto-deployed via deploy-marketplace.yml           │
│  └─ Served at: https://claudecodeplugins.io            │
│                                                          │
└──────────────────────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────────────────────┐
│ CLAUDE CLI DISTRIBUTION                                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  User: /plugin marketplace add ...                      │
│  ├─ Claude CLI reads marketplace.json from GitHub      │
│  │  ├─ URL: .claude-plugin/marketplace.json            │
│  │  └─ Source: github raw content URL                  │
│  │                                                      │
│  └─ User: /plugin install plugin-name@...              │
│     ├─ Claude CLI fetches plugin directory             │
│     ├─ Installs to user's .claude/ directory           │
│     └─ Registers commands/agents/hooks                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 9. Technology Stack Layers

```
┌─────────────────────────────────────────────────────────┐
│ FRONTEND (User Interface)                               │
├─────────────────────────────────────────────────────────┤
│ Astro 5.14.5                                            │
│ ├─ Static site generation                              │
│ ├─ React components in Astro                           │
│ └─ Zero JavaScript shipping (optimized)                │
│                                                         │
│ Tailwind CSS 4.1.14                                    │
│ ├─ Utility-first CSS framework                         │
│ └─ Responsive design system                            │
│                                                         │
│ HTML5 / CSS3                                           │
│ └─ Semantic markup                                     │
└─────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────┐
│ BUILD LAYER                                             │
├─────────────────────────────────────────────────────────┤
│ pnpm 9+                                                 │
│ ├─ Workspace manager                                   │
│ ├─ Fast dependency installation                        │
│ └─ Workspaces: MCP plugins + marketplace               │
│                                                         │
│ TypeScript 5.5.0                                       │
│ ├─ Type-safe JavaScript                               │
│ ├─ Compilation to JavaScript                          │
│ └─ Used by: root + MCP plugins                         │
│                                                         │
│ Node.js 20+ Scripts                                    │
│ ├─ sync-marketplace.cjs                                │
│ ├─ validate-all.sh                                     │
│ ├─ check-frontmatter.py                                │
│ └─ test-installation.sh                                │
└─────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────┐
│ RUNTIME LAYER                                           │
├─────────────────────────────────────────────────────────┤
│ Node.js 20+                                             │
│ ├─ Runs MCP server plugins                             │
│ ├─ Executes npm scripts                                │
│ └─ CLI tools (@modelcontextprotocol/sdk)               │
│                                                         │
│ MCP Protocol                                            │
│ └─ Bi-directional communication with Claude            │
│                                                         │
│ Claude CLI                                              │
│ └─ Plugin installation & management                    │
└─────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────┐
│ DATA LAYER                                              │
├─────────────────────────────────────────────────────────┤
│ JSON Catalogs                                           │
│ ├─ marketplace.extended.json  [Source of truth]        │
│ ├─ marketplace.json           [Generated CLI catalog]   │
│ └─ plugin.json                [Per-plugin metadata]     │
│                                                         │
│ Markdown Documentation                                  │
│ ├─ Commands (commands/*.md)                            │
│ ├─ Agents (agents/*.md)                                │
│ └─ README files                                         │
│                                                         │
│ GitHub Repository                                       │
│ └─ Single source of truth                              │
└─────────────────────────────────────────────────────────┘
```

---

## 10. Validation & Quality Assurance Pipeline

```
QUALITY GATES (Multi-layer validation)

Developer writes code
        ↓
┌─────────────────────────────────────────┐
│ LOCAL PRE-COMMIT VALIDATION             │
│ ./scripts/validate-all.sh               │
│ ├─ JSON syntax check                    │
│ ├─ Plugin structure check               │
│ ├─ Script permissions check             │
│ ├─ Frontmatter validation               │
│ └─ Status: PASS/FAIL                    │
└─────────────────────────────────────────┘
        ↓ (Pass) ↓ (Fail)
        │         └─ Fix & retry
        │
   Push to GitHub
        ↓
┌─────────────────────────────────────────┐
│ CI VALIDATION (validate-plugins.yml)    │
│ ├─ Sync check (marketplace.json)        │
│ ├─ JSON validation                      │
│ ├─ Structure check                      │
│ ├─ Permissions check                    │
│ ├─ Frontmatter validation               │
│ └─ Status: REQUIRED CHECK                │
└─────────────────────────────────────────┘
        ↓ (Pass) ↓ (Fail)
        │         └─ Block merge
        │
   Code Review
        ↓
┌─────────────────────────────────────────┐
│ SECURITY SCANNING (security-audit.yml)  │
│ ├─ CodeQL analysis                      │
│ ├─ npm audit                            │
│ └─ Dependency vulnerability check       │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ MERGE TO MAIN                           │
│ ├─ All checks must pass                 │
│ ├─ Code review approved                 │
│ └─ Ready for deployment                 │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ DEPLOYMENT (deploy-marketplace.yml)     │
│ ├─ Build website                        │
│ ├─ Deploy to GitHub Pages               │
│ ├─ Make plugins available               │
│ └─ Live at claudecodeplugins.io         │
└─────────────────────────────────────────┘
```

---

**Last Updated:** October 16, 2025  
**Diagram Version:** 1.0
