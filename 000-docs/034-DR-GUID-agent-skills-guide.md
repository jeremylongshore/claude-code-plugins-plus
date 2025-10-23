# How Agent Skills Actually Work

**Date:** 2025-10-17
**Purpose:** Explain the logic and workflow of Agent Skills system

---

## The Confusion: What Are Agent Skills?

❌ **NOT:** Skills we're giving TO the plugins
❌ **NOT:** A way to discover new plugins
❌ **NOT:** Plugin functionality or features

✅ **YES:** Instruction manuals that teach **Claude Code** how to use **already installed** plugins

---

## The Real Flow: 4 Steps

### Step 1: Plugin Discovery (Marketplace Website)

**Location:** https://claudecodeplugins.io

- User browses 229 plugins on the marketplace
- Reads plugin descriptions, categories, README files
- **Manually decides:** "I need this plugin"
- Runs installation command:

```bash
/plugin install ansible-playbook-creator@claude-code-plugins-plus
```

**At this point:** Plugin is just files on disk. Claude doesn't know when or how to use it.

---

### Step 2: Plugin Installation (Files Copied Locally)

**Location:** User's local machine

Plugin files get copied to user's Claude Code plugins directory:

```
~/.config/claude/plugins/ansible-playbook-creator/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── create-playbook.md
├── skills/
│   └── skill-adapter/
│       └── SKILL.md          ← This is the Agent Skill!
└── README.md
```

**At this point:** Plugin is installed, but Claude still doesn't know when to activate it automatically.

---

### Step 3: Skill Loading (Claude Learns About It)

**Time:** Claude Code startup

Claude Code automatically:

1. **Scans** all installed plugins for `skills/*/SKILL.md` files
2. **Reads** YAML frontmatter from each SKILL.md (~100 tokens per skill)
3. **Loads** into Claude's working memory

**Example loaded metadata:**

```yaml
---
name: Creating Ansible Playbooks
description: |
  Automates Ansible playbook creation. Use when you need to
  automate server configurations or deployments. Trigger with
  "ansible playbook" or "create playbook for [task]".
---
```

**At this point:** Claude now knows:
- ✅ This plugin exists
- ✅ It's for Ansible automation
- ✅ Trigger phrases: "ansible playbook", "create playbook"
- ✅ When to activate it automatically

---

### Step 4: Skill Activation (User Triggers It)

**User says:** "Create an Ansible playbook to install Apache"

**Without Agent Skills:**
```
Claude: "Hmm, I have 229 installed plugins. Let me manually search...
         Oh, there's ansible-playbook-creator. Let me read the README
         to figure out how to use it..."
```

**With Agent Skills:**
```
Claude: *Sees "ansible playbook" matches installed skill's trigger*
        *Reads full SKILL.md body for detailed instructions*
        "Perfect! I know exactly how to handle this."
        *Activates plugin with correct workflow*
```

---

## What SKILL.md Actually Contains

### 1. YAML Frontmatter (Always Loaded - 100 tokens)

```yaml
---
name: Creating Ansible Playbooks
description: |
  This skill creates Ansible playbooks for automating configuration
  management tasks. Use when you need to automate server configurations,
  software deployments, or infrastructure management. Trigger by
  requesting "ansible playbook" or "automate [task] setup".
---
```

**Purpose:**
- Metadata for discovery (always in Claude's memory)
- Trigger phrases for automatic activation
- WHEN to use this plugin

### 2. Skill Body (Loaded On-Demand - <5k tokens)

```markdown
## Overview
Brief explanation of what this enables

## How It Works
1. Step 1: What happens first
2. Step 2: What happens second
3. Step 3: What happens third

## When to Use This Skill
- Scenario 1
- Scenario 2
- Scenario 3

## Examples
### Example 1: Realistic Use Case
User request: "Create ansible playbook for Apache"

The skill will:
1. Generate Ansible playbook
2. Configure Apache web server
3. Present ready-to-deploy code

## Best Practices
- Tip 1
- Tip 2
- Tip 3

## Integration
How this works with other tools
```

**Purpose:**
- Detailed workflow instructions
- Realistic examples with exact user phrases
- Best practices for effective use

---

## The Problem We're Solving

### Before Agent Skills:

**User installs 50 plugins:**

```
User: "Create ansible playbook"
Claude: "I have ansible-playbook-creator installed somewhere,
         but I don't know WHEN to use it or HOW to use it.
         Let me read through files manually..."
```

Result:
- ❌ Plugins sit unused
- ❌ User has to explicitly name plugins
- ❌ Claude can't automatically route tasks
- ❌ No intelligent plugin selection

### After Agent Skills:

**User installs 50 plugins:**

```
User: "Create ansible playbook"
Claude: *Instantly recognizes "ansible playbook" trigger*
        *Reads SKILL.md for instructions*
        "I'll use ansible-playbook-creator for this!"
        *Automatically applies best workflow*
```

Result:
- ✅ Plugins activate automatically
- ✅ Claude picks the right plugin
- ✅ Follows best practices from SKILL.md
- ✅ User just describes what they want

---

## Example: Real Generated SKILL.md

**Plugin:** web-to-github-issue

**SKILL.md Content:**

```markdown
---
name: Creating GitHub Issues from Web Research
description: |
  Automates web research and converts findings into GitHub issues.
  Use when you need to research a topic and create a tracking issue.
  Trigger by requesting "research [topic] and create a ticket" or
  "find [information] and generate a GitHub issue".
---

## Overview
Streamlines research-to-implementation workflow by integrating
web search with GitHub issue creation.

## How It Works
1. **Web Search**: Claude searches the web for specified topic
2. **Information Extraction**: Extracts key findings and evidence
3. **GitHub Issue Creation**: Creates formatted issue with summary,
   recommendations, and source links

## When to Use This Skill
- Investigate technical topics and create implementation tickets
- Track security vulnerabilities with remediation steps
- Research competitor features and create feature requests

## Examples

### Example 1: Researching Security Best Practices

User request: "research Docker security best practices and create a ticket in myorg/backend"

The skill will:
1. Search web for Docker security best practices
2. Extract recommendations and mitigation strategies
3. Create GitHub issue with summary, checklist, and resource links

### Example 2: Investigating API Rate Limiting

User request: "find articles about API rate limiting, create issue with label performance"

The skill will:
1. Search for articles on API rate limiting
2. Extract techniques, pros/cons, and examples
3. Create labeled issue with findings and source links

## Best Practices
- **Specify Repository**: Mention repo name for correct placement
- **Use Labels**: Add labels for categorization and tracking
- **Provide Context**: Include context to guide search and ensure relevant results

## Integration
Integrates with Claude's web search and requires GitHub authentication.
Can be combined with other skills to automate workflows.
```

**How Claude Uses This:**

1. **Sees trigger phrases** in description: "research [topic] and create a ticket"
2. **Matches user request:** "research Docker security and create ticket"
3. **Reads full SKILL.md** for workflow details
4. **Executes:** Web search → Extract info → Create GitHub issue
5. **Applies best practices:** Asks for repo name, suggests labels

---

## Why ONE Skill Per Plugin?

Each plugin gets **exactly ONE** SKILL.md file:

```
plugins/ansible-playbook-creator/
└── skills/
    └── skill-adapter/
        └── SKILL.md          ← ONE skill teaching Claude about this plugin
```

**Why not multiple skills per plugin?**

- Each SKILL.md represents the **entire plugin's capability**
- One comprehensive instruction manual is better than fragmented ones
- Anthropic's system design: one skill = one plugin capability
- Simpler for Claude to understand and activate

---

## The Generation Logic

### What Vertex AI Reads (Plugin Context)

For each plugin, we feed the AI:

1. **plugin.json** - Plugin metadata (name, description, category)
2. **README.md** - First 3000 characters of documentation
3. **commands/*.md** - Sample commands (up to 2 files, 600 chars each)
4. **agents/*.md** - Sample agents (up to 2 files, 600 chars each)

**Total context:** ~4000-5000 tokens per plugin

### What Vertex AI Generates (SKILL.md)

Using official Anthropic guidelines:

**YAML Frontmatter:**
- `name`: Gerund form, max 64 chars ("Creating Ansible Playbooks")
- `description`: Third person, max 1024 chars, includes WHAT, WHEN, and trigger phrases

**Body Content:**
- Overview (2-3 sentences)
- How It Works (3-5 step workflow)
- When to Use (3+ trigger scenarios)
- Examples (2+ realistic use cases with exact user phrases)
- Best Practices (3+ actionable tips)
- Integration (ecosystem context)

**Constraints:**
- Under 500 lines (Anthropic recommendation)
- No placeholder text ([TODO], [INSERT])
- Specific to this plugin (not generic)
- Realistic examples in plugin's domain

---

## Validation: 8-Point Quality Check

Before saving any SKILL.md, we validate:

1. ✅ Has YAML frontmatter (starts with `---`)
2. ✅ Valid frontmatter structure (three `---` delimiters)
3. ✅ Required fields present (`name` and `description`)
4. ✅ NO forbidden fields (`allowed-tools`, `version`, `author`)
5. ✅ Character limits enforced (name ≤ 64, description ≤ 1024)
6. ✅ Line count check (warns if > 500 lines)
7. ✅ Minimum content length (body > 100 characters)
8. ✅ No placeholder text ([TODO], [INSERT], [PLACEHOLDER])

**If validation fails:** Automatically retry up to 3 times with refined prompt

---

## Current Status

### Generated Skills: 4/227

✅ **web-to-github-issue** (skill-enhancers)
- 3,162 chars, 52 lines
- Triggers: "research [topic] and create a ticket"

✅ **sugar** (devops)
- 2,975 chars, 54 lines
- Triggers: DevOps automation tasks

✅ **git-commit-smart** (devops)
- 2,666 chars, 53 lines
- Triggers: Smart git commit workflows

✅ **ansible-playbook-creator** (devops)
- 2,756 chars, 50 lines
- Triggers: "ansible playbook", "automate [task]"

### Statistics

- **Success Rate:** 4 successes, 2 quota errors
- **Avg Generation Time:** 6.0 seconds
- **Avg Line Count:** 52 lines (well under 500 limit)
- **Validation Pass Rate:** 100% (no validation failures)

### Remaining Work

- **Priority Plugins:** 157 (devops, security, testing, ai-ml, performance, database)
- **All Plugins:** 227 total
- **Estimated Time:** ~19 minutes for priority (with 5s rate limiting)
- **Estimated Cost:** ~$0.157 for priority, ~$0.23 for all

---

## What Agent Skills Are NOT

❌ **NOT plugin features** - They don't add functionality to plugins
❌ **NOT for discovering plugins** - Only work for installed plugins
❌ **NOT multiple skills per plugin** - One comprehensive skill per plugin
❌ **NOT visible to end users** - They're internal to Claude Code
❌ **NOT for marketing** - They're for automatic activation

---

## What Agent Skills ARE

✅ **Instruction manuals for Claude** - Teaching when and how to use plugins
✅ **Automatic activation triggers** - Claude recognizes user intent
✅ **Workflow documentation** - Step-by-step usage patterns
✅ **Best practices guide** - Tips for effective plugin use
✅ **Example library** - Realistic use cases with exact phrases

---

## The Bigger Picture

### The Plugin Problem

You create 229 amazing plugins, but:
- Users install 50+ plugins
- Claude doesn't know when to use them
- Plugins sit dormant
- Users have to explicitly name plugins: `/ansible-playbook-creator create playbook`

### The Agent Skills Solution

With SKILL.md files:
- Claude automatically reads metadata at startup
- User says: "Create ansible playbook"
- Claude recognizes trigger phrase
- Automatically activates correct plugin
- Follows best practices from SKILL.md

**Result:** Plugins become truly intelligent and self-activating.

---

## Summary: The Complete Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. MARKETPLACE (Discovery)                                  │
│    User browses claudecodeplugins.io                        │
│    Finds ansible-playbook-creator                           │
│    Runs: /plugin install ansible-playbook-creator           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. INSTALLATION (Files Copied)                              │
│    Plugin files copied to local disk                        │
│    Including skills/skill-adapter/SKILL.md                  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. STARTUP (Skill Loading)                                  │
│    Claude Code scans installed plugins                      │
│    Reads YAML frontmatter from all SKILL.md files           │
│    Loads trigger phrases and descriptions                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. USAGE (Automatic Activation)                             │
│    User: "Create ansible playbook for Apache"               │
│    Claude: Recognizes trigger "ansible playbook"            │
│    Claude: Reads full SKILL.md for workflow                 │
│    Claude: Activates plugin with best practices             │
└─────────────────────────────────────────────────────────────┘
```

---

## Why This Matters

**Before Agent Skills:**
- 229 plugins exist
- Users install them manually
- Claude treats them as dumb files
- No automatic routing or intelligence

**After Agent Skills:**
- 229 plugins with instruction manuals
- Claude learns about each at startup
- Automatic recognition and activation
- Intelligent routing based on user intent

**Impact:**
- 🚀 Plugins become self-activating
- 🎯 Claude picks the right tool automatically
- 📚 Best practices built into every activation
- 💡 Users just describe what they want

---

## Technical Details

### File Structure

```
plugins/{plugin-name}/
├── .claude-plugin/
│   └── plugin.json
├── commands/              ← What the plugin can do
│   └── *.md
├── agents/                ← Specialized behaviors
│   └── *.md
├── skills/                ← How Claude should use it
│   └── skill-adapter/
│       └── SKILL.md       ← Generated by Vertex AI
└── README.md
```

### Anthropic's Agent Skills Specification

**Official Guidelines:**
- YAML frontmatter with ONLY `name` and `description`
- Name: Max 64 characters, gerund form
- Description: Max 1024 characters, third person
- Body: Under 500 lines recommended
- Content: Concise, specific, consistent terminology
- No time-sensitive information (dates, versions)

**Loading Behavior:**
- Level 1 (Startup): YAML frontmatter (~100 tokens)
- Level 2 (Triggered): Full SKILL.md body (<5k tokens)
- Level 3 (As Needed): Additional reference files

---

**Last Updated:** 2025-10-17
**Generated Skills:** 4/227
**System Status:** Production Ready ✅
**Next Step:** Continue batch processing with 5s rate limiting
