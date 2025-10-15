# Contributing to Claude Code Plugins

Thank you for your interest in contributing! This marketplace thrives on community contributions. Whether you're submitting a plugin, improving documentation, or reporting bugs, your help makes this resource better for everyone.

##  Ways to Contribute

- **Submit new plugins** - Share your creations with the community
- **Improve existing plugins** - Bug fixes, enhancements, documentation
- **Write documentation** - Help others understand plugins
- **Report bugs** - Help us identify and fix issues
- **Suggest features** - Ideas for improving the marketplace
- **Review pull requests** - Help maintain quality standards

##  Submitting a Plugin

### Before You Start

Make sure your plugin:
- [ ] Solves a real problem or provides clear value
- [ ] Is well-documented with examples
- [ ] Has been tested thoroughly
- [ ] Follows security best practices
- [ ] Doesn't duplicate existing plugins (unless significantly different)

### Plugin Requirements

Your plugin **MUST** have:

1. **Valid `.claude-plugin/plugin.json`**
   - All required fields filled in
   - Valid JSON syntax (test with `jq`)
   - Accurate version number (semantic versioning)

2. **Comprehensive README.md**
   - What the plugin does
   - Installation instructions
   - Usage examples with code blocks
   - Requirements (dependencies, tools needed)
   - Files explanation
   - License information

3. **LICENSE file**
   - MIT or Apache-2.0 recommended
   - Must be compatible with marketplace license

4. **Working functionality**
   - Tested locally before submission
   - All commands work as documented
   - Hooks trigger correctly
   - Agents activate appropriately

5. **Security compliance**
   - No hardcoded secrets, API keys, or credentials
   - Use environment variables for sensitive data
   - Scripts validate inputs
   - No destructive operations without confirmation

6. **Proper permissions**
   - All shell scripts are executable: `chmod +x script.sh`
   - Appropriate file permissions

### Submission Process

#### 1. Fork the Repository

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/claude-code-plugins.git
cd claude-code-plugins
```

#### 2. Create Your Plugin

```bash
# Option A: Use a template
cp -r templates/command-plugin plugins/community/my-plugin

# Option B: Start from scratch
mkdir -p plugins/community/my-plugin/.claude-plugin
mkdir -p plugins/community/my-plugin/commands  # or agents, hooks, scripts
```

#### 3. Develop Your Plugin

- Create `.claude-plugin/plugin.json` with accurate metadata
- Add your commands, agents, hooks, or MCP servers
- Write comprehensive README.md
- Add LICENSE file
- Make scripts executable

#### 4. Test Locally

```bash
# Create test marketplace
mkdir -p ~/test-marketplace/.claude-plugin

# Create marketplace.json
cat > ~/test-marketplace/.claude-plugin/marketplace.json << 'EOF'
{
  "name": "test",
  "owner": {"name": "Test"},
  "plugins": [{
    "name": "my-plugin",
    "source": "/absolute/path/to/plugins/community/my-plugin"
  }]
}
EOF

# Add to Claude Code
/plugin marketplace add ~/test-marketplace

# Install and test
/plugin install my-plugin@test

# Test all functionality!
```

#### 5. Update Marketplace Catalog

Edit `.claude-plugin/marketplace.extended.json` and add your plugin:

```json
{
  "name": "my-plugin",
  "source": "./plugins/community/my-plugin",
  "description": "Clear, concise description of what it does",
  "version": "1.0.0",
  "category": "productivity",
  "keywords": ["relevant", "searchable", "keywords"],
  "author": {
    "name": "Your Name",
    "email": "[email protected]",
    "url": "https://github.com/yourusername"
  }
}
```

```bash
# Regenerate the CLI-facing marketplace catalog
pnpm run sync-marketplace  # or: npm run sync-marketplace
```

#### 6. Create Pull Request

```bash
# Create feature branch
git checkout -b add-my-plugin

# Add your changes
git add plugins/community/my-plugin/
git add .claude-plugin/marketplace.extended.json .claude-plugin/marketplace.json

# Commit with clear message
git commit -m "Add my-plugin: Brief description of what it does"

# Push to your fork
git push origin add-my-plugin
```

Then open a pull request on GitHub using our template.

### Plugin Categories

Choose the most appropriate category:

- **productivity** - Workflow optimization, automation, efficiency tools
- **security** - Security analysis, vulnerability scanning, compliance
- **testing** - Test automation, QA tools, test generation
- **deployment** - CI/CD, deployment automation, infrastructure
- **documentation** - Docs generation, API documentation, code comments
- **analysis** - Code analysis, metrics, quality checking
- **integration** - External service integrations, API connections
- **ai** - AI/ML specific tooling, model operations
- **example** - Educational and tutorial plugins
- **other** - Doesn't fit above categories (specify in description)

### Naming Conventions

**Plugin Names:**
- Use kebab-case: `my-awesome-plugin`
- Be descriptive and clear
- Avoid generic names: `tool`, `helper`, `utils`
- Check for existing plugins with similar names

**Files:**
- Commands: `commands/command-name.md`
- Agents: `agents/agent-name.md`
- Scripts: `scripts/descriptive-name.sh`

### Version Numbering

Use [Semantic Versioning](https://semver.org/):

- **Major (1.0.0)**: Breaking changes, incompatible updates
- **Minor (1.1.0)**: New features, backward compatible
- **Patch (1.1.1)**: Bug fixes, backward compatible

Start at `1.0.0` for initial release.

##  Reporting Bugs

Found a bug? Please report it!

1. **Search existing issues** - It might already be reported
2. **Create a new issue** using the bug report template
3. **Include details**:
   - Plugin name and version
   - Claude Code version (`claude --version`)
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages or logs

##  Improving Documentation

Documentation improvements are always welcome:

- Fix typos or clarify confusing sections
- Add more examples
- Improve formatting
- Translate to other languages (coming soon)

Submit changes via pull request.

##  Code Review Process

All submissions go through review:

### What We Check

- **Functionality** - Does it work as described?
- **Code quality** - Is the code clean and well-organized?
- **Security** - Any security concerns?
- **Documentation** - Is it well-documented?
- **Testing** - Has it been tested?
- **Style** - Does it follow conventions?

### Review Timeline

- Initial review: Within 7 days
- Feedback provided: Within 14 days
- Merge after approval: 1-3 days

### If Changes Are Requested

- Address feedback in your PR
- Push updates to your branch
- Request re-review when ready

##  Quality Standards

### Code Quality

- **Clear and readable** - Others should understand your code
- **Well-commented** - Explain complex logic
- **Error handling** - Handle edge cases gracefully
- **No warnings** - Code should run without warnings

### Documentation Quality

- **Clear installation steps** - Anyone should be able to install
- **Working examples** - Examples should be copy-paste ready
- **Accurate information** - No outdated or incorrect info
- **Proper formatting** - Use markdown correctly

### Security Standards

- **No secrets in code** - Use environment variables
- **Input validation** - Validate all user inputs
- **Principle of least privilege** - Request minimal permissions
- **Dependencies** - Keep dependencies minimal and updated

##  Style Guidelines

### Markdown Style

```markdown
# Headers use sentence case

## Use descriptive headings

**Bold** for emphasis, *italic* for terms

`code` for commands and file names

\`\`\`language
code blocks with language specified
\`\`\`
```

### JSON Style

```json
{
  "useTwoSpaces": true,
  "quotesDouble": true,
  "trailingCommas": false,
  "sortKeys": false
}
```

### Bash Script Style

```bash
#!/bin/bash
# Clear comment at top

# Use descriptive variable names
file_path="/path/to/file"

# Check for errors
if [[ ! -f "$file_path" ]]; then
  echo "Error: File not found"
  exit 1
fi

# Use functions for complex logic
function process_file() {
  local file="$1"
  # Processing logic
}
```

##  Community Guidelines

### Be Respectful

- Treat everyone with respect and kindness
- Welcome newcomers and help them learn
- Provide constructive feedback
- Assume good intentions

### Be Collaborative

- Share knowledge and help others
- Give credit where credit is due
- Be open to feedback on your work
- Celebrate others' contributions

### Be Professional

- Keep discussions on-topic
- Avoid inflammatory language
- Respect differing opinions
- Follow the code of conduct

##  Getting Help

Need help contributing?

- ** Discord**: [Claude Developers](https://discord.com/invite/6PPFFzqPDZ)
- ** Discussions**: [GitHub Discussions](https://github.com/jeremylongshore/claude-code-plugins/discussions)
- ** Email**: [email protected]

##  Recognition

Contributors are recognized in several ways:

- **README credits** - All contributors listed in main README
- **Plugin authorship** - You're credited as author in plugin.json
- **Community highlights** - Outstanding contributions featured
- **Maintainer status** - Active contributors may become maintainers

##  License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Quick Checklist

Before submitting, verify:

- [ ] Plugin tested locally and working
- [ ] README.md is comprehensive with examples
- [ ] LICENSE file included
- [ ] plugin.json is valid JSON
- [ ] All scripts are executable (`chmod +x`)
- [ ] No hardcoded secrets
- [ ] Marketplace.json updated
- [ ] Branch is up-to-date with main
- [ ] Commit messages are clear
- [ ] PR uses the template

---

**Thank you for contributing to Claude Code Plugins!** 

Your contributions help build a vibrant ecosystem that benefits the entire community.

[Submit a Plugin](#-submitting-a-plugin) | [Report a Bug](#-reporting-bugs) | [Join Discord](https://discord.com/invite/6PPFFzqPDZ)
