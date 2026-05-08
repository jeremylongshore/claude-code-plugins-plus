# Official Anthropic plugin.json Schema (2026 Spec)

Source: https://code.claude.com/docs/en/plugins-reference · Last synced: 2026-03-21

---

## 1. Required Fields

Only one field is required by the Anthropic spec:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | string | Non-empty, no whitespace | Plugin identifier. Must be unique within a given installation scope. |

Example:

```json
{
  "name": "my-plugin"
}
```

---

## 2. Metadata Fields (Optional)

Seven optional fields provide discovery, attribution, and versioning metadata.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `version` | string | Semver format `X.Y.Z` (e.g., `"1.0.0"`, `"2.3.1"`) | Plugin version. Pre-release and build metadata segments are valid semver but discouraged. |
| `description` | string | Non-empty when present | Human-readable summary of what the plugin does. Used by CLI search and marketplace listings. |
| `author` | string \| object | Object form: `{name: string, email?: string, url?: string}` | Plugin author. String form (e.g., `"Jane Doe <jane@example.com>"`) and object form are both valid. |
| `homepage` | string | Valid URL | Link to the plugin's landing page or documentation site. |
| `repository` | string | Valid URL | Link to the plugin's source code repository. |
| `license` | string | SPDX identifier (e.g., `"MIT"`, `"Apache-2.0"`, `"Proprietary"`) | License governing plugin use. |
| `keywords` | array | Array of non-empty strings | Discovery keywords for CLI search and marketplace indexing. |

**Enterprise recommendation:** Our CI policy recommends all seven metadata fields for published plugins. The validator grades completeness accordingly.

---

## 2.5 Intent Solutions Extension Fields (Optional)

Two provenance fields outside Anthropic's spec, set by `/skill-creator --forge` to flag the plugin's origin. These are NOT part of Anthropic's published spec — they are an Intent Solutions extension. CI accepts them; CLI consumers ignore them.

| Field | Type | Set by | Purpose |
|---|---|---|---|
| `generated` | boolean | `/skill-creator --forge` | `true` when the plugin was produced by the forge pipeline (NOI gate + ecosystem absorb + mandatory validation). Hand-authored plugins omit this field or set `false`. |
| `author_type` | enum (`"human"` \| `"forge"`) | `/skill-creator --forge` (sets `"forge"`) | Coarser provenance — same information as `generated`, in enum form. The marketplace renders a "Forge-generated" pill when either flag indicates forge origin. |

**Anti-spam moat (rationale):** the marketplace surfaces a visual provenance flag for forge-generated plugins so reviewers and end users can distinguish them from human-authored work. Combined with the rate-limit + human-review-queue gating in the contribution workflow, this is the quality moat against the failure mode where a public `--forge` flag floods the catalog with low-quality wrappers.

**NOT in plugin.json** (intentional separation of concerns):

- `tagline` — marketplace-website display field. Lives in `marketplace.extended.json` per-plugin entry, NOT in `plugin.json`. Stripped from `marketplace.json` (CLI-safe) by `scripts/sync-marketplace.cjs`.
- `jrig` — JRig behavioral-eval verdict. Computed by JRig CLI, persisted to `freshie/inventory.sqlite` `forge_proofs` table, joined into the marketplace data at build time. Not authored by hand and not stored in `plugin.json`.

---

## 3. Component Path Fields (Optional)

Seven fields define where Claude discovers plugin components. Each accepts flexible types to support single-directory, multi-directory, and inline-object configurations.

| Field | Type | Description |
|-------|------|-------------|
| `commands` | string \| array | Path(s) to directories containing command markdown files (e.g., `"./commands"` or `["./commands", "./extra-commands"]`). Legacy — prefer `skills/` for new plugins. |
| `agents` | string \| array | Path(s) to directories containing agent markdown files. |
| `skills` | string \| array | Path(s) to directories containing skill subdirectories (each with a `SKILL.md`). |
| `hooks` | string \| array \| object | Hook configuration. Can be a path to `hooks.json`, an array of paths, or an inline hook object. |
| `mcpServers` | string \| array \| object | MCP server configurations. Can be a path to `.mcp.json`, an array of paths, or an inline server definition object. |
| `outputStyles` | string \| array | Path(s) to output style definition files. |
| `lspServers` | string \| array \| object | LSP server configurations. Can be a path to `.lsp.json`, an array of paths, or an inline server definition object. |

When component path fields are omitted, Claude auto-discovers components using the standard directory structure (see section 5).

---

## 4. Complete Field Reference (All 15 Fields)

| # | Field | Required | Type | Category |
|---|-------|----------|------|----------|
| 1 | `name` | Yes | string | Identity |
| 2 | `version` | No | string | Metadata |
| 3 | `description` | No | string | Metadata |
| 4 | `author` | No | string \| object | Metadata |
| 5 | `homepage` | No | string | Metadata |
| 6 | `repository` | No | string | Metadata |
| 7 | `license` | No | string | Metadata |
| 8 | `keywords` | No | array | Metadata |
| 9 | `commands` | No | string \| array | Component Path |
| 10 | `agents` | No | string \| array | Component Path |
| 11 | `skills` | No | string \| array | Component Path |
| 12 | `hooks` | No | string \| array \| object | Component Path |
| 13 | `mcpServers` | No | string \| array \| object | Component Path |
| 14 | `outputStyles` | No | string \| array | Component Path |
| 15 | `lspServers` | No | string \| array \| object | Component Path |

**Anthropic spec floor**: only the 15 fields above are part of Anthropic's published `plugin.json` spec. Two additional fields are valid as Intent Solutions extensions and are documented in section 2.5: `generated` (boolean) and `author_type` (`"human"` | `"forge"`). Both are forge-provenance flags set by `/skill-creator --forge`.

---

## 5. Plugin Directory Structure (Anthropic Official)

```
plugin-root/
├── .claude-plugin/plugin.json   # Manifest (optional but recommended)
├── commands/                    # Command markdown files (legacy — use skills/)
├── agents/                      # Agent markdown files
├── skills/                      # Skill directories
│   └── skill-name/
│       └── SKILL.md             # Skill definition with YAML frontmatter
├── hooks/
│   └── hooks.json               # Hook configuration
├── .mcp.json                    # MCP server definitions
├── .lsp.json                    # LSP server configurations
├── settings.json                # Default plugin settings
├── scripts/                     # Utility scripts
├── LICENSE
└── CHANGELOG.md
```

Notes:
- The `.claude-plugin/` directory is the canonical manifest location.
- Claude auto-discovers `commands/`, `agents/`, and `skills/` by convention when component path fields are omitted from `plugin.json`.
- `hooks.json`, `.mcp.json`, and `.lsp.json` are discovered at the plugin root by default.

---

## 6. Invalid Fields (Not in Anthropic Spec)

These fields are **not** part of the official Anthropic spec and will be rejected by CI:

| Invalid Field | Reason | Correct Alternative |
|---------------|--------|---------------------|
| `displayName` | Not in spec | Use `name` |
| `category` | Marketplace-only metadata | Not stored in plugin.json |
| `tags` | Marketplace-only metadata | Use `keywords` in plugin.json |
| `requires` | Not in spec | No equivalent — document in README |
| `documentation` | Not in spec | Use `homepage` |
| `mcp_servers` | Wrong case (snake_case) | Use `mcpServers` (camelCase) |
| `lsp_servers` | Wrong case (snake_case) | Use `lspServers` (camelCase) |

---

## 7. Validation Rules

### Structural rules
- The 15 Anthropic spec fields (section 4) and the 2 IS-extension fields (section 2.5) are accepted. Other unknown fields are flagged but not currently rejected by CI — see `.github/workflows/validate-plugins.yml` for the current enforced gate (JSON validity + README existence + script executability + source path existence).
- `plugin.json` must be valid JSON (no trailing commas, no comments).
- File must be located at `.claude-plugin/plugin.json` relative to plugin root.

### Field-level rules
- **`name`**: Required. Non-empty string. No whitespace characters.
- **`version`**: Must match semver format `X.Y.Z` where X, Y, Z are non-negative integers.
- **`description`**: Non-empty string when present.
- **`author`**: String form or object form `{name, email?, url?}`. When object, `name` is required.
- **`homepage`**: Valid URL (must start with `http://` or `https://`).
- **`repository`**: Valid URL (must start with `http://` or `https://`).
- **`license`**: Non-empty string. SPDX identifiers recommended.
- **`keywords`**: Array of non-empty strings. No duplicates.

### Component path rules
- When a component path is specified, the referenced directory or file must exist.
- String values are treated as single paths; array values as multiple paths.
- Object values (for `hooks`, `mcpServers`, `lspServers`) are treated as inline configuration.

### Enterprise policy (recommended, not Anthropic-required)
- All seven metadata fields (`version`, `description`, `author`, `repository`, `homepage`, `license`, `keywords`) should be present for published plugins.
- The enterprise validator grades completeness on a 100-point scale.

---

## 8. Example plugin.json (Complete)

```json
{
  "name": "my-awesome-plugin",
  "version": "2.1.0",
  "description": "A full-featured plugin demonstrating all metadata fields",
  "author": {
    "name": "Jane Developer",
    "email": "jane@example.com",
    "url": "https://jane.dev"
  },
  "homepage": "https://github.com/jane/my-awesome-plugin#readme",
  "repository": "https://github.com/jane/my-awesome-plugin",
  "license": "MIT",
  "keywords": ["devops", "automation", "ci-cd"],
  "commands": "./commands",
  "agents": "./agents",
  "skills": "./skills",
  "hooks": "./hooks/hooks.json",
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["./dist/index.js"]
    }
  },
  "outputStyles": "./styles",
  "lspServers": {
    "my-lsp": {
      "command": "node",
      "args": ["./lsp/server.js"],
      "languages": ["typescript"]
    }
  }
}
```

Minimal valid example (only the required field):

```json
{
  "name": "minimal-plugin"
}
```
