# Claude Code / Cowork ↔ Databricks MCP Integration — Architecture Scoping

**Date:** 2026-05-27
**Author:** Research pass for Intent Solutions
**Question:** From "I have a Databricks workspace" to "Claude can call Databricks tools" — what's the actual user pathway today, and is it frictionless?

---

## 1. Executive summary

**Databricks is NOT a built-in Anthropic connector.** Across every Anthropic surface — Claude.ai, Claude Desktop, Claude Code CLI, and Claude Cowork — Databricks lives in the **"custom connector"** lane. The user (or org admin) pastes a workspace-specific URL, supplies OAuth client credentials they generated in their own Databricks workspace, and completes a per-user OAuth handshake. There is no toggle-on-and-go flow comparable to Stripe / HubSpot / QuickBooks in Claude for Small Business.

The friction is concentrated in three places:

1. **The user must know they need three separate connectors**, not one. Databricks ships *managed MCP servers* (UC functions / Vector Search / Genie / SQL) each at its own URL path — every one is a discrete `Add custom connector` action.
2. **OAuth setup is on the user**, not Anthropic. The Databricks workspace admin must register an OAuth app, copy `claude.ai/api/mcp/auth_callback` (and `claude.com/...`) as redirect URIs, and hand the client_id/secret to whoever is registering the connector.
3. **Cowork's marketplace UI doesn't yet expose a "Databricks" tile** with a templated flow. It treats Databricks as a custom MCP URL like any other (or, in third-party broker pattern, lets `composio.dev/mcp` mediate). Per-user provisioning, not per-org auto-rollout.

**For Tons of Skills specifically**: the cowork-zip distribution path *cannot ship an MCP server*. `scripts/build-cowork-zips.mjs:51` explicitly excludes `category: mcp` plugins from zips because Cowork plugins are markdown + config only — no node_modules, no binaries. A Tons of Skills Databricks-aware skill can *reference* Databricks MCP tools and document the setup, but the user still does the connector registration manually in their Cowork / Claude.ai admin settings.

**The frictionless path doesn't exist yet.** What ships today is "frictionless once configured" — the OAuth handshake auto-refreshes, Unity Catalog permissions are honored, and tools surface naturally. Getting *to* configured takes a Databricks workspace admin, an OAuth app, and 3 manual connector additions per user.

---

## 2. Anthropic's Databricks integration story — what ships, what doesn't

### What ships from Anthropic

| Item | Status |
|---|---|
| Pre-vetted Databricks connector in the Anthropic Directory | **No.** 414 connectors listed (May 2026), Databricks is not among the one-click vetted set. |
| Built-in Cowork connector tile | **No.** Databricks is a "custom connector" everywhere. |
| Anthropic-published skill pack targeting Databricks | **No first-party skill.** Anthropic has a [tutorial article](https://claude.com/resources/tutorials/using-databricks-for-data-analysis) that walks through *manual* custom-connector setup. |
| Claude for Small Business Databricks toggle | **No.** SMB ships with QuickBooks, PayPal, HubSpot, Canva, DocuSign, Google Workspace, Microsoft 365. No Databricks. |
| Anthropic ↔ Databricks commercial deal | **Yes** (announced 2025; renewed/expanded). Claude models run *inside* Databricks (Mosaic AI). That's distribution-into-Databricks, not Databricks-into-Cowork. |

### What ships from Databricks

| Item | Status |
|---|---|
| Managed MCP servers | **Yes.** Pre-configured endpoints for Unity Catalog functions, Vector Search, Genie Spaces, Databricks SQL. No user setup of the server itself. |
| OAuth support for Claude.ai + Claude Desktop + Claude Code | **Yes.** Documented at `docs.databricks.com/aws/en/generative-ai/mcp/connect-external-services`. |
| PAT (Personal Access Token) auth | **Yes, Claude Desktop only.** Not supported for Claude.ai or Claude Code OAuth flows. |
| Per-user OAuth audit trail in Unity Catalog | **Yes.** Tool calls inherit the calling user's UC permissions. |

### The structural mismatch

Anthropic's connector-vetting machine ([Anthropic Directory](https://claude.ai/directory)) is built for **multi-tenant SaaS with a single OAuth tenant** (Stripe.com is one tenant; everyone OAuth-flows into the same `mcp.stripe.com`). Databricks managed MCPs live at **per-workspace hostnames** — `https://<your-workspace>.cloud.databricks.com/api/2.0/mcp/...`. A pre-vetted tile in the Directory would still need the user to substitute their workspace hostname. So the "custom connector" lane is structurally the right fit, even though it's higher-friction.

---

## 3. MCP registration flow per surface

### 3a. Claude Code CLI

**Three transport options**, with stdio/http/sse. For Databricks managed MCPs, always HTTP:

```bash
# OAuth flow (recommended) — Databricks managed Vector Search server
claude mcp add-json databricks-vsearch \
  '{"type":"http",
    "url":"https://<workspace>.cloud.databricks.com/api/2.0/mcp/vector-search/<catalog>/<schema>",
    "oauth":{"clientId":"<client-id>","callbackPort":8080}}' \
  --client-secret

# Then in-session
/mcp        # opens browser, completes OAuth, stores token in keychain
```

**Scopes** (where config lands):

| Scope | File | Purpose |
|---|---|---|
| `local` (default) | `~/.claude.json` under project path | Personal, current project only |
| `project` | `.mcp.json` at repo root | Team-shared, checked into git |
| `user` | `~/.claude.json` | Personal, all projects |

For Databricks specifically, **never use `project` scope with embedded client_secret** — the secret lives in the keychain via `--client-secret`, but the workspace hostname in a checked-in `.mcp.json` leaks org topology. Use `user` scope or `${WORKSPACE_HOST}` env-var expansion.

### 3b. Claude.ai / Claude.com (consumed by Cowork)

Settings → Connectors → Add custom connector. For Databricks the org admin (Team/Enterprise) does this once per managed MCP they want to expose; 3 separate connectors for UC / Vector Search / Genie. User-level installs use the Anthropic Directory; Databricks is not there, so it's admin-only territory.

**Per-user vs per-workspace:**

- **Org-installed connector**: Admin adds at `Admin settings > Connectors`, makes available to org members. Each member still completes their own OAuth handshake — token is per-user, not shared.
- **Individual user connector**: User adds at `claude.ai/customize/connectors`. Their own OAuth, their own token, their own scope.

**Cowork surface** consumes these — Cowork plugins automatically see whatever connectors the user / org has authorized. There's no separate "Cowork MCP registration" step distinct from Claude.ai connectors.

### 3c. Tons of Skills cowork-zip distribution

**Cowork-zip explicitly does not ship MCP servers.** From `scripts/build-cowork-zips.mjs`:

```javascript
const SKIP_CATEGORIES = new Set(['mcp']);
// MCP plugins need node_modules, not suitable for zip
// MCP servers cannot be installed by Cowork users (they need node)
```

What cowork-zip DOES ship: SKILL.md, commands/*.md, agents/*.md, plugin.json. Pure instruction content. A Tons of Skills "Databricks Operations" skill can:

- Reference Databricks MCP tools by name in its SKILL.md (`mcp__databricks-uc__query_table`)
- Document the connector setup steps the user must do in Cowork first
- Provide workflow logic that orchestrates Databricks tool calls

What it **cannot** do: pre-register the Databricks MCP endpoint, broker OAuth, or smuggle a `.mcp.json` into the user's Cowork install.

---

## 4. Auth + credential architecture

### Where credentials live

| Surface | Token storage | Refresh model |
|---|---|---|
| Claude Code (OAuth) | macOS keychain / Linux credentials file | Auto-refresh via OAuth refresh token |
| Claude Code (PAT in `.mcp.json`) | Plaintext in file (NOT recommended) | Manual rotation |
| Claude Desktop (OAuth) | OS keychain | Auto-refresh |
| Claude Desktop (PAT via `mcp-remote`) | Plaintext in `claude_desktop_config.json` | Manual rotation |
| Claude.ai / Cowork | Anthropic-side encrypted token vault, per-user | Auto-refresh via OAuth |

### OAuth flow — what the Databricks admin must set up

1. In Databricks workspace: `Settings → Identity and access → OAuth apps → Add OAuth application`.
2. Register redirect URIs:
   - `https://claude.ai/api/mcp/auth_callback` (Claude.ai)
   - `https://claude.com/api/mcp/auth_callback` (Claude.com domain)
   - `http://localhost:8080/callback` (Claude Code — port must match `callbackPort`)
3. Note the client_id; for confidential clients, generate a client_secret.
4. Distribute (client_id, optional secret, workspace hostname) to users.
5. Each user runs through the OAuth handshake on first connector use.

### Pre-vetted vs custom

Anthropic's Directory has a vetting bar (security review, terms acceptance, listing approval). Custom connectors bypass it — the user/admin asserts trust by typing the URL. **Databricks managed MCPs are not in the Directory**, so every Claude Code / Claude.ai / Cowork user is on the custom-connector path with the trust burden on themselves.

For Claude for Small Business, where "pre-vetted" means "appears in the SMB connector tile grid": Databricks is absent. SMB is positioned for the finance / ops / sales / HR persona; the Databricks persona (data engineer, analytics lead) is served by Claude Code + Databricks' own docs, not by SMB tile-clicking.

---

## 5. Distribution implications — if Tons of Skills publishes a Databricks-aware skill

### Scenario: A `databricks-analytics` plugin in the Tons of Skills marketplace

#### Path (a) — Claude Code CLI user

1. `claude plugin install databricks-analytics@tonsofskills` — installs the markdown skill + commands.
2. **Plugin-bundled MCP** (the elegant path): if the plugin ships a `.mcp.json` with the Databricks MCP URL pre-templated and uses `${DATABRICKS_WORKSPACE_HOST}` env-var expansion, the user only sets `DATABRICKS_WORKSPACE_HOST` + completes OAuth via `/mcp`. **Three-line setup**: env var, `/mcp`, browser.
3. **Without plugin-bundled MCP**: user manually runs `claude mcp add-json databricks-uc ...` per the docs. The skill works once they do; until then, every skill invocation that calls `mcp__databricks-uc__*` fails with "tool not found."

CLI user experience grade: **B+** with plugin-bundled MCP, **C** without.

#### Path (b) — Cowork user

1. User downloads cowork-zip from tonsofskills.com.
2. User uploads to Cowork via `Customize → Browse plugins`.
3. Skill is now active in their Cowork session.
4. **But**: the Databricks MCP is not registered. They must independently:
   - Get their Databricks workspace hostname + OAuth client_id/secret from their admin.
   - Open `Admin settings → Connectors → Add custom connector` (admin needs to do this for org-wide use, OR each user does it under `Customize → Connectors`).
   - Paste 3 URLs (UC, Vector Search, Genie) and complete OAuth for each.
5. Skill invocations work.

Cowork user experience grade: **D**. The skill is up but useless until the multi-step Anthropic-UI dance is done, and there is **no mechanism for the cowork-zip to automate or even pre-fill any of step 4**.

### The structural gap

Cowork plugins are markdown-instructions-only by design. MCP server registration is a separate Anthropic concept that lives in `Admin settings → Connectors` and is not exposed to plugin authors. Until Anthropic ships a "plugin declares required connectors → Cowork prompts user to authorize" UI flow (does not exist in May 2026), Tons of Skills can only ship the *instructions* half of a Databricks workflow.

---

## 6. Recommendation — how Tons of Skills should ship Databricks capabilities

### For CLI-first plugins (high-friction acceptable, max capability)

Ship a plugin with a templated `.mcp.json` using env-var expansion:

```json
{
  "mcpServers": {
    "databricks-uc": {
      "type": "http",
      "url": "${DATABRICKS_WORKSPACE_HOST}/api/2.0/mcp/functions/${DATABRICKS_CATALOG:-main}/${DATABRICKS_SCHEMA:-default}",
      "oauth": {
        "clientId": "${DATABRICKS_OAUTH_CLIENT_ID}",
        "callbackPort": 8765
      }
    },
    "databricks-genie": {
      "type": "http",
      "url": "${DATABRICKS_WORKSPACE_HOST}/api/2.0/mcp/genie/${DATABRICKS_GENIE_SPACE_ID}",
      "oauth": {
        "clientId": "${DATABRICKS_OAUTH_CLIENT_ID}",
        "callbackPort": 8766
      }
    }
  }
}
```

Then use the schema 3.6.0 `required_environment_variables` block in SKILL.md frontmatter to declare the 4 vars (`DATABRICKS_WORKSPACE_HOST`, `DATABRICKS_OAUTH_CLIENT_ID`, optional catalog/schema/genie_space). Document a single-command bootstrap that registers OAuth secret via `MCP_CLIENT_SECRET=... claude`.

**Target user experience**: 4 env vars + 1 `/mcp` browser handshake. ~90 seconds.

### For Cowork users (low friction is unattainable — manage expectations)

Ship a separate `databricks-analytics-cowork` plugin (markdown-only, no `.mcp.json` because cowork-zip strips it anyway). Include:

- A `commands/setup-databricks-connector.md` that walks the user through the Anthropic custom-connector UI step-by-step (screenshots optional).
- A note in `README.md` at the top: **"This plugin requires 3 custom connectors in your Cowork admin settings. See the setup command first."**
- SKILL.md that *checks for* the expected MCP tools (`mcp__databricks-uc__*`) at task start and provides a clear error message + setup-command pointer if they're missing.

**Target user experience**: download → install → run setup-command which prints the URLs → 5–10 min of clicking in Anthropic UI → skill works. ~10 min.

### Cross-surface skill identifier convention

Use server names that match Databricks' own conventions so a single SKILL.md works whether the user registered via CLI or Cowork:

- `databricks-uc` (Unity Catalog functions)
- `databricks-vsearch` (Vector Search)
- `databricks-genie` (Genie Spaces)
- `databricks-sql` (SQL Warehouse)

These map cleanly to the 4 managed MCP endpoint families and produce stable tool prefixes (`mcp__databricks-uc__list_functions`, etc.).

### Lobbying angle (longer game)

The friction here is **Anthropic-side**, not Tons-of-Skills-side. The fix would be: Cowork plugin manifest declares `requires_connectors: [databricks-uc, databricks-vsearch, ...]`, and Cowork UI surfaces a pre-fill dialog at install time. If Tons of Skills has any inbound channel to the Anthropic Cowork team (via the Enterprise cohort / partner network), this is the structural ask that converts D-grade Cowork UX → B+. Until then, Tons of Skills' Databricks story is "great CLI, mediocre Cowork, fundamentally rate-limited by what Anthropic exposes to plugin authors."

---

## 7. Sources

- [Claude Code MCP docs (code.claude.com/docs/en/mcp)](https://code.claude.com/docs/en/mcp) — CLI registration commands, scopes, OAuth flags
- [Databricks: Connect external services to MCPs](https://docs.databricks.com/aws/en/generative-ai/mcp/connect-external-services) — Claude Desktop / Claude.ai / Claude Code Databricks setup
- [Databricks: Managed MCP servers](https://docs.databricks.com/aws/en/generative-ai/mcp/managed-mcp) — UC / Vector Search / Genie / SQL endpoint catalog
- [Anthropic tutorial: Using Databricks for data analysis](https://claude.com/resources/tutorials/using-databricks-for-data-analysis) — Anthropic-published manual-setup walkthrough (custom-connector flow)
- [Anthropic news: Claude for Small Business](https://www.anthropic.com/news/claude-for-small-business) — SMB connector roster (no Databricks)
- [Anthropic Directory of connectors (claude.ai/directory)](https://claude.ai/directory) — 414 verified MCPs (May 2026), no Databricks tile
- [Composio: Databricks via Cowork](https://composio.dev/toolkits/databricks/framework/claude-cowork) — broker-pattern alternative (composio.dev/mcp as middleman)
- [Claude Cowork enterprise plugins guide (ALM Corp)](https://almcorp.com/blog/claude-cowork-plugins-enterprise-guide/) — Cowork admin plugin marketplace + GitHub-source plugins
- [Cowork connectors list (pluginsforcowork.com)](https://pluginsforcowork.com/guides/cowork-connectors/) — current 38+ built-in tile inventory
- [Tons of Skills cowork-zip builder](file:///home/jeremy/000-projects/claude-code-plugins/scripts/build-cowork-zips.mjs) — `SKIP_CATEGORIES = ['mcp']` line 51
- [Specializing Claude Code with Skills and MCP on Databricks (David Huang, Medium)](https://medium.com/@hiydavid/specializing-claude-code-a-quick-guide-to-agent-skills-and-mcp-on-databricks-c0cfdd43637d) — practitioner walkthrough
