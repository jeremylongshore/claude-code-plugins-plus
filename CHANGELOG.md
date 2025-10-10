# Changelog

All notable changes to the Claude Code Plugins Marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-10-10

### 🎉 Initial Open-Source Release

**BREAKING CHANGE**: Complete repository restructure from commercial Gumroad model to open-source GitHub marketplace.

### Added

#### 🏆 Production Plugin
- **git-commit-smart** - AI-powered conventional commit message generator
  - Analyzes staged changes and generates contextual commit messages
  - Supports conventional commits standard (feat, fix, docs, etc.)
  - Interactive confirmation workflow
  - Breaking change detection
  - `/gc` shortcut for fast workflow
  - 1,500+ words of comprehensive documentation

#### 📚 Example Plugins (Educational)
- **hello-world** - Basic slash command demonstration
- **formatter** - PostToolUse hooks demonstration
- **security-agent** - Specialized AI subagent demonstration

#### 🎨 Plugin Templates
- **minimal-plugin** - Bare minimum plugin structure
- **command-plugin** - Plugin with slash commands
- **agent-plugin** - Plugin with AI subagent
- **full-plugin** - Complete plugin with commands, agents, and hooks

#### 🔍 Quality Assurance Tools
- `check-frontmatter.py` - Python YAML frontmatter validator
- `validate-all.sh` - Comprehensive plugin validation (JSON, frontmatter, shortcuts, permissions)
- `test-installation.sh` - Plugin installation testing in isolated environment

#### 📖 Documentation
- Comprehensive README.md with installation and usage
- CONTRIBUTING.md with community guidelines
- Detailed plugin development guide
- Security best practices
- Monetization alternatives guide

#### 🤝 GitHub Integration
- GitHub Actions workflow for plugin validation
- Issue templates (plugin submission, bug report)
- Pull request template
- GitHub Sponsors configuration (FUNDING.yml)

### Changed

- **Repository Model**: Pivoted from commercial plugin packs to open-source community marketplace
- **Monetization Strategy**: GitHub Sponsors + consulting/training instead of direct plugin sales
- **Distribution Model**: GitHub-based marketplace catalog (JSON) instead of Gumroad
- **Focus**: Community-driven growth and first-mover advantage

### Removed

- Commercial plugin packs infrastructure (`website/products/`)
- Gumroad sales integration (`website/marketing-site/`)
- Build automation for commercial distribution (`website/scripts/`)
- Internal business reports (`website/000-docs/`)

### Infrastructure

- Marketplace catalog: `.claude-plugin/marketplace.json` with 4 plugins
- Plugin validation CI/CD pipeline
- GitHub Sponsors monetization framework
- Community contribution workflow

### Metrics

- **Production Plugins**: 1 (git-commit-smart)
- **Example Plugins**: 3 (educational)
- **Templates**: 4 (starter templates)
- **Validation Scripts**: 3 (quality assurance)
- **Documentation Pages**: 6+ (comprehensive guides)

### Migration Notes

This release represents a complete pivot from a commercial model to an open-source community marketplace. The restructure was motivated by:

1. **Distribution Reality**: Claude Code plugin marketplace doesn't support commercial sales
2. **Community Value**: Open-source model better serves developer community
3. **First-Mover Advantage**: Launched days after Anthropic's plugin announcement (October 2025)
4. **Sustainable Model**: GitHub Sponsors + consulting provides sustainable revenue

All quality work (validation systems, templates, production plugin) was preserved and migrated to the new structure.

---

## Release Links

- [1.0.0 - 2025-10-10](#100---2025-10-10)

---

**Repository**: https://github.com/jeremylongshore/claude-code-plugins
**Installation**: `/plugin marketplace add jeremylongshore/claude-code-plugins`
**Flagship Plugin**: `/plugin install git-commit-smart@claude-code-plugins`
