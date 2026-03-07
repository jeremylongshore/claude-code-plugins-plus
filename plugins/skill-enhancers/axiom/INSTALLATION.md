# Axiom Installation Guide

## Quick Start

```bash
# 1. Navigate to your projects directory
cd /Users/Charles/Projects

# 2. The Axiom directory already exists with the plugin

# 3. Install the plugin locally
claude-code plugin add ./Axiom/plugins/axiom

# 4. Verify installation
claude-code plugin list
# Should show: axiom@0.1.0
```

## Skills Available

After installation, these skills are automatically available:

- `axiom:xcode-debugging` - Environment-first Xcode diagnostics
- `axiom:swift-concurrency` - Swift 6 concurrency patterns
- `axiom:database-migration` - Safe database schema evolution
- `axiom:memory-debugging` - Memory leak diagnosis
- `axiom:ui-testing` - Reliable XCTest patterns
- `axiom:build-troubleshooting` - Dependency resolution

## Using Skills

Skills are automatically suggested by Claude Code based on context, or you can invoke them manually:

```bash
# When you encounter a build error
/skill axiom:xcode-debugging

# When you see actor isolation errors
/skill axiom:swift-concurrency

# When adding database columns
/skill axiom:database-migration

# When debugging memory leaks
/skill axiom:memory-debugging

# When tests are flaky
/skill axiom:ui-testing

# When dependencies fail to resolve
/skill axiom:build-troubleshooting
```

## Testing the Installation

Try this example:

```bash
# In a Claude Code session:
# "I'm getting BUILD FAILED with no details in Xcode"

# Claude Code should automatically suggest axiom:xcode-debugging
# Or you can invoke it manually:
/skill axiom:xcode-debugging
```

## Documentation

- **Plugin README**: `plugins/axiom/README.md`
- **Skills Summary**: `SKILLS-SUMMARY.md`
- **VitePress Docs**: Run `npm run docs:dev` for full documentation site

## Troubleshooting

### Plugin not found
```bash
# Check plugin path is correct
ls -la /Users/Charles/Projects/Axiom/plugins/axiom/

# Should see claude-code.json and skills/ directory
```

### Skills not loading
```bash
# Restart Claude Code
# /restart

# Or check plugin is enabled
claude-code plugin list
```

### Need to update
```bash
# If you make changes to skills, reload the plugin
claude-code plugin reload axiom
```

## Development Setup

If you want to modify skills or contribute:

```bash
# 1. Make changes to skill files
vim plugins/axiom/skills/xcode-debugging.md

# 2. Test locally (skills reload automatically)
# No rebuild needed - just edit and use

# 3. Commit changes
git add plugins/axiom/skills/
git commit -m "Improve xcode-debugging skill"
```

## Publishing (Future)

When ready to publish to a marketplace:

```bash
# 1. Update version in claude-code.json
# 2. Create git tag
git tag v0.1.0
git push origin v0.1.0

# 3. Publish to marketplace (TBD)
```

## Requirements

- **Claude Code**: 2.0.13 or later
- **Platform**: macOS 12+ (for iOS development)
- **Tools**: Xcode Command Line Tools, Python 3

## Support

For issues or questions:
- Check `SKILLS-SUMMARY.md` for detailed documentation
- Review individual skill files in `plugins/axiom/skills/`
- File issues on GitHub (when repository is published)

---

**Installation complete!** Start using skills by invoking them in Claude Code sessions.
