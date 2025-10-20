# Installation Guide - Fullstack Starter Pack

Complete installation instructions for the Fullstack Starter Pack Claude Code plugin collection.

---

## Prerequisites

**Required:**
- Claude Code CLI installed and configured
- Git (for version control)

**Recommended:**
- Node.js 18+ (for frontend/backend development)
- Docker Desktop (for containerized development)
- PostgreSQL 14+ or Docker (for database)
- Redis (optional, for caching)

---

## Method 1: Direct Installation (Recommended)

### Step 1: Add Marketplace

```bash
# Add the Claude Code Plugins marketplace
/plugin marketplace add jeremylongshore/claude-code-plugins
```

### Step 2: Install Pack

```bash
# Install Fullstack Starter Pack
/plugin install fullstack-starter-pack@claude-code-plugins-plus
```

### Step 3: Verify Installation

```bash
# List installed plugins
/plugin list

# Test a command
/component-generator "Test Button"

# Test an agent
Ask Claude: "Help me design a React component architecture"
# React Specialist agent should activate
```

---

## Method 2: Manual Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/jeremylongshore/claude-code-plugins.git
cd claude-code-plugins/products/fullstack-starter-pack
```

### Step 2: Install via Local Path

```bash
/plugin install /absolute/path/to/fullstack-starter-pack
```

---

## Method 3: Development Installation

For plugin development or customization:

```bash
# Clone repository
git clone https://github.com/jeremylongshore/claude-code-plugins.git
cd claude-code-plugins/products/fullstack-starter-pack

# Create symbolic link
ln -s $(pwd) ~/.claude/plugins/fullstack-starter-pack

# Or on Windows
mklink /D "%USERPROFILE%\.claude\plugins\fullstack-starter-pack" "C:\path\to\fullstack-starter-pack"
```

---

## Post-Installation Setup

### Frontend Development

**Install Node.js dependencies (one-time):**
```bash
# These will be installed automatically when you generate projects
# But you may want to pre-install common tools:
npm install -g npm@latest
npm install -g typescript
npm install -g vite
```

### Backend Development

**Database Setup:**
```bash
# Option 1: Docker (recommended for development)
docker run --name postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  -d postgres:15-alpine

# Option 2: Local PostgreSQL
# Install from https://www.postgresql.org/download/

# Option 3: Cloud database
# Use Railway, Supabase, Neon, or PlanetScale
```

**Redis Setup (Optional):**
```bash
# Docker
docker run --name redis -p 6379:6379 -d redis:7-alpine

# Or install locally
# macOS: brew install redis
# Ubuntu: sudo apt install redis-server
```

---

## Verification Steps

### 1. Test Commands

```bash
# Frontend commands
/component-generator "Button with loading state"  # or /cg
/css-utility-generator  # or /cug

# Backend commands
/express-api-scaffold "Task API"  # or /eas
/fastapi-scaffold "Blog API"  # or /fas

# Database commands
/prisma-schema-gen "Blog with users and posts"  # or /psg
/sql-query-builder "Get users with their posts"  # or /sqb

# Integration commands
/auth-setup jwt  # or /as
/env-config-setup  # or /ecs
/project-scaffold "My App"  # or /ps
```

### 2. Test Agents

Ask Claude:
- "Review this React component for performance issues" → React Specialist activates
- "Design a REST API for a blog" → API Builder activates
- "Help me design a database schema for e-commerce" → Database Designer activates
- "Set up CI/CD pipeline for my app" → Deployment Specialist activates

### 3. Check Installation

```bash
# Verify all plugins loaded
/plugin list | grep fullstack

# Should show:
# - react-specialist (agent)
# - ui-ux-expert (agent)
# - component-generator (command, /cg)
# - css-utility-generator (command, /cug)
# - api-builder (agent)
# - backend-architect (agent)
# - express-api-scaffold (command, /eas)
# - fastapi-scaffold (command, /fas)
# - database-designer (agent)
# - prisma-schema-gen (command, /psg)
# - sql-query-builder (command, /sqb)
# - deployment-specialist (agent)
# - auth-setup (command, /as)
# - env-config-setup (command, /ecs)
# - project-scaffold (command, /ps)
```

---

## Troubleshooting Installation

### Issue: Plugins not appearing

**Solution:**
```bash
# Reload Claude Code
# Restart Claude Code CLI

# Or reinstall
/plugin uninstall fullstack-starter-pack
/plugin install fullstack-starter-pack@claude-code-plugins-plus
```

### Issue: Commands not working

**Check:**
1. Plugin installed correctly: `/plugin list`
2. Shortcut conflicts: Check if shortcuts (`/cg`, `/eas`, etc.) conflict with other plugins
3. Claude Code version: Requires Claude Code >=0.1.0

### Issue: Agents not activating

**Solution:**
- Be explicit in requests: "I need help with React performance optimization"
- Use activation keywords: "react", "api", "database", "deployment"

---

## Optional Tools

### VS Code Extensions (Recommended)

```bash
# React/TypeScript development
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension bradlc.vscode-tailwindcss

# Database
code --install-extension Prisma.prisma

# Docker
code --install-extension ms-azuretools.vscode-docker
```

### CLI Tools

```bash
# Install useful CLI tools
npm install -g prisma
npm install -g tsx  # Run TypeScript directly
npm install -g dotenv-cli  # Environment variable management
```

---

## Upgrade Instructions

### Upgrading to New Version

```bash
# Check for updates
/plugin update fullstack-starter-pack

# Or reinstall
/plugin uninstall fullstack-starter-pack
/plugin install fullstack-starter-pack@claude-code-plugins-plus
```

---

## Uninstallation

```bash
# Uninstall pack
/plugin uninstall fullstack-starter-pack

# Remove marketplace (optional)
/plugin marketplace remove claude-code-plugins-plus
```

---

## Next Steps

1. **Read Quick Start Guide:** `docs/QUICK_START.md`
2. **Explore Use Cases:** `docs/USE_CASES.md`
3. **Generate Your First Project:** `/project-scaffold "My App"`

---

**Installation complete! Start building fullstack applications faster.** 
