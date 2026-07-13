# ARD: Plugin Creator

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The Plugin Creator generates new plugin scaffolds within the claude-code-plugins monorepo, wiring them into the marketplace catalog and validation pipeline.

```
User Request ("Create a security plugin with skills")
       ↓
[Plugin Creator]
  ├── Creates: directory structure, plugin.json, README, LICENSE, components
  ├── Updates: marketplace.extended.json
  └── Runs: sync-marketplace, validate-all-plugins.sh
       ↓
CI-Ready Plugin
  ├── plugins/[category]/[name]/
  ├── Catalog entry in marketplace.extended.json
  └── Validation passing
```

## Data Flow

1. **Input**: Plugin name, category, type (commands/agents/skills/MCP/hybrid), description, keywords, and optional author override from the user request
2. **Processing**: Validate the name is unique and kebab-case, create the directory tree, generate all required files from templates, add the marketplace entry, run sync to regenerate `marketplace.json`, then execute the validation script to confirm the plugin is CI-ready
3. **Output**: Complete plugin directory with all required files, marketplace catalog entry, validation confirmation, and suggested next steps (implement logic, commit, push)

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Template-driven generation | Predefined templates for each file type | Ensures consistency; templates encode all CI requirements (field allowlist, frontmatter format) |
| Validation-last workflow | Create everything, then validate at the end | Single validation pass catches all issues at once; faster than validate-as-you-go |
| Kebab-case enforcement | Reject names that aren't kebab-case | Repository convention; CI enforces it; catching early saves a cycle |
| Default MIT license | MIT unless explicitly overridden | Most plugins in the marketplace use MIT; lowest friction for contributors |
| Minimum 2 keywords | Required in plugin.json template | Marketplace search and discovery depend on keywords; enforced by CI |
| Author defaults to repo owner | Use Jeremy Longshore when unspecified | Reduces friction for internal plugins; community contributors always specify |
| Category validation | Check against allowed category list | Invalid categories cause marketplace sync failure; catch early |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| Write | Create all plugin files: plugin.json, README.md, LICENSE, component files (commands/agents/skills/MCP) |
| Read | Check existing plugins for name conflicts; read marketplace.extended.json for entry addition |
| Grep | Search catalog for duplicate plugin names; verify naming conventions |
| Bash(cmd:*) | Run `jq` for JSON validation, `pnpm run sync-marketplace`, `./scripts/validate-all-plugins.sh`, `chmod +x` |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Duplicate plugin name | Grep finds existing entry in marketplace.extended.json | Suggest alternative names; show the existing plugin for disambiguation |
| Invalid category | Category not in the allowed set | List valid categories; suggest the closest match |
| JSON syntax error in generated files | `jq empty` returns non-zero | Re-generate the JSON file; parse the jq error to identify the broken field |
| Marketplace sync failure | `pnpm run sync-marketplace` exits non-zero | Check for schema violations in the new entry; verify required fields |
| Validation failure | `validate-all-plugins.sh` reports errors | Parse the validation output; fix each flagged issue; re-validate |

## Extension Points

- Custom templates: allow users to specify a template directory for org-specific plugin conventions
- Interactive mode: prompt for each field interactively when minimal input is provided
- Batch creation: generate multiple related plugins from a manifest file
- Post-create hooks: run custom scripts after plugin creation (e.g., initialize git, create branch)
- SaaS pack support: extend to create multi-skill packs with shared configuration
- Migration tool: convert existing non-standard plugins into the validated structure
