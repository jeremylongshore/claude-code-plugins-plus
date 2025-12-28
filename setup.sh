#!/bin/bash
set -e

echo "🚀 Setting up Claude Code Plugins Repository"
echo "============================================"
echo ""

# Change to repository directory
cd "$(dirname "$0")"

# Make all shell scripts executable
echo "📝 Making scripts executable..."
find . -type f -name "*.sh" -exec chmod +x {} \;
echo "✅ Scripts are now executable"
echo ""

# Initialize git repository
if [ ! -d ".git" ]; then
  echo "🔧 Initializing git repository..."
  git init
  echo "✅ Git initialized"
else
  echo "ℹ️  Git repository already initialized"
fi
echo ""

# Add all files
echo "📦 Adding files to git..."
git add .
echo "✅ Files added"
echo ""

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: Claude Code Plugin Marketplace

- Complete marketplace structure with 3 example plugins
- hello-world: Basic slash command example
- auto-formatter: Hook-based code formatting
- security-reviewer: Specialized security agent
- 4 plugin templates for developers
- Comprehensive documentation (6 docs files)
- GitHub workflows and issue templates
- 000-docs/007-DR-GUID-contributing.md with submission guidelines
- Professional README with badges and clear structure

🚀 Generated with Claude Code" || echo "ℹ️  Commit already exists or nothing to commit"

echo ""
echo "✅ Repository setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Create repository on GitHub:"
echo "   https://github.com/new"
echo "   Name: claude-code-plugins"
echo "   Public, no README/license/gitignore"
echo ""
echo "2. Add remote and push:"
echo "   git remote add origin https://github.com/jeremylongshore/claude-code-plugins.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Test the marketplace:"
echo "   /plugin marketplace add jeremylongshore/claude-code-plugins"
echo "   /plugin install hello-world@claude-code-plugins-plus"
echo "   /hello"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📖 See 000-docs/017-DR-MANL-setup.md for detailed instructions"
echo ""
