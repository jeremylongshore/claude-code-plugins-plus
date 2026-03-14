# Validate Plugin

Validates full Claude Code plugin directory structure against the official Anthropic spec and Intent Solutions enterprise standard.

## What It Validates

- **plugin.json** - All 15 official Anthropic fields (metadata + component paths)
- **SKILL.md** - Frontmatter schema, body structure, 100-point grading
- **commands/*.md** - Frontmatter, name conventions, shortcuts
- **agents/*.md** - Frontmatter, capabilities, description quality
- **File references** - Scripts, references, assets all resolve correctly

## Installation

```bash
/plugin install validate-plugin@claude-code-plugins
```

## Usage

Say "validate this plugin" or "/validate-plugin" pointing at any plugin directory.

## License

MIT
