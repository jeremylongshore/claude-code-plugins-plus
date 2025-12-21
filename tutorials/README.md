# Interactive Learning Lab

**Learn Claude Code plugin development through hands-on Jupyter notebooks**

📚 **11 interactive tutorials** | 🎯 **Beginner → Advanced** | ⏱️ **~5 hours total**

---

## 🚀 Quick Start

1. **Install Jupyter**: `pip install jupyter nbformat`
2. **Choose your path**: Beginner? Start with [Skills](#skills-tutorials). Advanced? Jump to [MCP](#mcp-server-plugins).
3. **Open a notebook**: `jupyter notebook tutorials/skills/01-what-is-skill.ipynb`
4. **Run cells**: Execute code interactively and learn by doing

---

## 📖 Learning Paths

### Path 1: Plugin Creator (Beginner → Intermediate)
**Goal**: Create and publish your first Claude Code plugin

1. [What is SKILL.md?](skills/01-what-is-skill.ipynb) - 20 min
2. [Skill Anatomy](skills/02-skill-anatomy.ipynb) - 25 min
3. [Build Your First Skill](skills/03-build-your-first-skill.ipynb) - 45 min
4. [What is a Plugin?](plugins/01-what-is-plugin.ipynb) - 25 min
5. [Plugin Structure](plugins/02-plugin-structure.ipynb) - 30 min
6. [Build Your First Plugin](plugins/03-build-your-first-plugin.ipynb) - 45 min

**Time**: ~3 hours | **Output**: Production-ready plugin

---

### Path 2: Advanced Developer (Intermediate → Advanced)
**Goal**: Master advanced patterns and MCP servers

1. [Advanced Skill Patterns](skills/04-advanced-patterns.ipynb) - 45 min
2. [Skill Validation](skills/05-skill-validation.ipynb) - 30 min
3. [MCP Server Plugins](plugins/04-mcp-server-plugins.ipynb) - 60 min
4. [Mental Model](orchestration/01-mental-model.ipynb) - 30 min
5. [Orchestration Pattern](orchestration/02-orchestration-pattern.ipynb) - 45 min

**Time**: ~3.5 hours | **Output**: TypeScript MCP server, multi-agent orchestration

---

### Path 3: Quick Reference (Just-in-Time Learning)
**Goal**: Find specific answers fast

| Need | Tutorial | Time |
|------|----------|------|
| Understand SKILL.md basics | [01-what-is-skill](skills/01-what-is-skill.ipynb) | 20 min |
| Fix validation errors | [05-skill-validation](skills/05-skill-validation.ipynb) | 30 min |
| Build instruction plugin | [03-build-your-first-plugin](plugins/03-build-your-first-plugin.ipynb) | 45 min |
| Build MCP plugin | [04-mcp-server-plugins](plugins/04-mcp-server-plugins.ipynb) | 60 min |
| Multi-agent patterns | [02-orchestration-pattern](orchestration/02-orchestration-pattern.ipynb) | 45 min |

---

## 📚 Tutorial Catalog

### Skills Tutorials (5 notebooks)

Build skills that teach Claude new workflows.

| # | Title | Level | Time | What You'll Learn |
|---|-------|-------|------|-------------------|
| 01 | [What is SKILL.md?](skills/01-what-is-skill.ipynb) | Beginner | 20 min | SKILL.md format, discovery, basic structure |
| 02 | [Skill Anatomy](skills/02-skill-anatomy.ipynb) | Beginner | 25 min | Frontmatter, body structure, enterprise standards |
| 03 | [Build Your First Skill](skills/03-build-your-first-skill.ipynb) | Intermediate | 45 min | Create test-file-generator skill from scratch |
| 04 | [Advanced Skill Patterns](skills/04-advanced-patterns.ipynb) | Advanced | 45 min | Multi-phase, tool auth, sub-agents, orchestration |
| 05 | [Skill Validation](skills/05-skill-validation.ipynb) | Intermediate | 30 min | Enterprise standards (6767-c), validation tools |

**Total**: 165 minutes (2h 45m) | **Cells**: 77 interactive

---

### Plugins Tutorials (4 notebooks)

Package skills into shareable, versioned plugins.

| # | Title | Level | Time | What You'll Learn |
|---|-------|-------|------|-------------------|
| 01 | [What is a Plugin?](plugins/01-what-is-plugin.ipynb) | Beginner | 25 min | Plugin types, marketplace, when to use plugins |
| 02 | [Plugin Structure](plugins/02-plugin-structure.ipynb) | Intermediate | 30 min | Directory anatomy, plugin.json, validation |
| 03 | [Build Your First Plugin](plugins/03-build-your-first-plugin.ipynb) | Intermediate | 45 min | Create code-review-toolkit with skills & commands |
| 04 | [MCP Server Plugins](plugins/04-mcp-server-plugins.ipynb) | Advanced | 60 min | TypeScript MCP server, tools, Zod validation |

**Total**: 160 minutes (2h 40m) | **Cells**: 40 interactive

---

### Orchestration Tutorials (2 notebooks)

Master multi-agent coordination and complex workflows.

| # | Title | Level | Time | What You'll Learn |
|---|-------|-------|------|-------------------|
| 01 | [Mental Model](orchestration/01-mental-model.ipynb) | Intermediate | 30 min | Orchestration concepts, when to use sub-agents |
| 02 | [Orchestration Pattern](orchestration/02-orchestration-pattern.ipynb) | Advanced | 45 min | Multi-agent coordination, test harness example |

**Total**: 75 minutes (1h 15m) | **Cells**: 37 interactive

---

## 🎯 By Role

### I'm a Developer
**You want**: Build plugins for your team

**Start here**:
1. [Build Your First Skill](skills/03-build-your-first-skill.ipynb)
2. [Build Your First Plugin](plugins/03-build-your-first-plugin.ipynb)
3. [Skill Validation](skills/05-skill-validation.ipynb)

---

### I'm a Power User
**You want**: Automate workflows without coding

**Start here**:
1. [What is SKILL.md?](skills/01-what-is-skill.ipynb)
2. [Skill Anatomy](skills/02-skill-anatomy.ipynb)
3. [Build Your First Skill](skills/03-build-your-first-skill.ipynb)

---

### I'm an Enterprise Architect
**You want**: Understand standards and governance

**Start here**:
1. [Skill Validation](skills/05-skill-validation.ipynb) - Enterprise standards (6767-c)
2. [Plugin Structure](plugins/02-plugin-structure.ipynb) - Validation and security
3. [Advanced Skill Patterns](skills/04-advanced-patterns.ipynb) - Production patterns

---

### I'm a TypeScript Developer
**You want**: Build MCP servers with external integrations

**Start here**:
1. [What is a Plugin?](plugins/01-what-is-plugin.ipynb) - Understand plugin types
2. [MCP Server Plugins](plugins/04-mcp-server-plugins.ipynb) - Full TypeScript implementation
3. [Orchestration Pattern](orchestration/02-orchestration-pattern.ipynb) - Multi-agent coordination

---

## 🏆 Learning Outcomes

After completing all tutorials, you will:

✅ **Understand** SKILL.md format and Claude's discovery system
✅ **Create** enterprise-compliant skills following 6767-c standards
✅ **Build** complete plugins with skills, commands, and documentation
✅ **Validate** using automated tools and CI/CD pipelines
✅ **Implement** TypeScript MCP servers with external integrations
✅ **Orchestrate** multi-agent workflows for complex tasks
✅ **Publish** to marketplaces or share with your team

---

## 📊 Quick Stats

| Metric | Value |
|--------|-------|
| Total Tutorials | 11 notebooks |
| Interactive Cells | 154 code cells |
| Learning Time | ~6 hours |
| Difficulty Range | Beginner → Advanced |
| Standards Compliance | 6767-c (Enterprise) |
| Languages | Python, TypeScript, Markdown |

---

## 🛠️ Prerequisites

### Required
- **Jupyter**: `pip install jupyter nbformat`
- **Python 3.9+**: For running notebooks
- **Text editor**: VS Code, Vim, etc.

### Optional (for MCP tutorials)
- **Node.js 20+**: For TypeScript MCP servers
- **TypeScript**: `npm install -g typescript`
- **Claude Code CLI**: To test plugins

---

## 🚦 Getting Started

### Option 1: Run Locally

```bash
# Clone repository
git clone https://github.com/jeremylongshore/claude-code-plugins.git
cd claude-code-plugins/tutorials

# Install Jupyter
pip install jupyter nbformat

# Start Jupyter
jupyter notebook
```

### Option 2: Google Colab (Coming Soon)

Click the "Open in Colab" badge on any notebook to run in the cloud (no installation required).

---

## 📝 Tutorial Format

All tutorials follow this structure:

1. **Learning Goals** - What you'll accomplish
2. **Prerequisites** - What to know first
3. **Concepts** - Theory with examples
4. **Interactive Code** - Run and modify cells
5. **Hands-On Project** - Build something real
6. **Validation** - Check your work
7. **Next Steps** - Where to go next

---

## 🎓 Best Practices

### How to Use These Tutorials

1. **Run cells in order** - Each cell builds on previous ones
2. **Modify and experiment** - Change values, try different inputs
3. **Read error messages** - They teach you validation rules
4. **Save your work** - Use File → Download to keep your changes
5. **Ask questions** - Comments and issues welcome

### Learning Tips

- ✅ **Do the exercises** - Don't just read, actually build
- ✅ **Start simple** - Beginner tutorials first, even if experienced
- ✅ **Validate early** - Run validators to catch mistakes fast
- ✅ **Study examples** - Real marketplace plugins are best teachers
- ✅ **Share your work** - Publish plugins to get feedback

---

## 🔗 Additional Resources

### Documentation
- [Claude Code Official Docs](https://docs.claude.ai/code)
- [6767-c Enterprise Standard](../000-docs/6767-c-DR-STND-claude-code-extensions-standard.md)
- [Marketplace Catalog](../.claude-plugin/marketplace.json)

### Examples
- [258 Marketplace Plugins](../plugins/)
- [241 Agent Skills](../plugins/*/skills/)
- [MCP Server Examples](../plugins/mcp/)

### Community
- [GitHub Issues](https://github.com/jeremylongshore/claude-code-plugins/issues)
- [Discussions](https://github.com/jeremylongshore/claude-code-plugins/discussions)
- [Contributing Guide](../CONTRIBUTING.md)

---

## 🤝 Contributing

Found a typo? Have a suggestion? Want to add a tutorial?

1. **Report issues**: [GitHub Issues](https://github.com/jeremylongshore/claude-code-plugins/issues)
2. **Suggest tutorials**: [Discussions](https://github.com/jeremylongshore/claude-code-plugins/discussions)
3. **Submit PRs**: Fork, create branch, submit pull request

---

## 📜 License

All tutorials are licensed under **MIT License** - feel free to use, modify, and share.

---

## 🙏 Acknowledgments

Created by the Claude Code Plugins community. Special thanks to all contributors who made these tutorials possible.

---

**Ready to start learning?** Pick a path above and dive in! 🚀
