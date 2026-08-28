# Upload-Post Skills

> Anthropic Agent Skills that teach Claude (and other MCP-compatible AI agents) how to *operate* social media — not just talk about it.

This repository bundles every official Upload-Post skill in a single place. Each skill is a self-contained subdirectory with its own `SKILL.md`, references, and (where relevant) scripts. Drop the whole repo into your agent's skills directory and Claude will load every skill independently.

## The 5 skills

| # | Skill | What it teaches Claude to do | When to use it |
|---|---|---|---|
| 1 | **[larry-marketing](./skills/larry-marketing/)** | Run a complete TikTok / Instagram slideshow marketing pipeline based on the Larry methodology — competitor research, AI image generation, text overlays, multi-platform posting, analytics tracking, and a closed-loop hook/CTA optimizer | Marketing an app or product on TikTok + Instagram; needs measurable growth, not one-off posts |
| 2 | **[comment-funnel](./skills/comment-funnel/)** | Turn Instagram comments into private DM leads — monitors a post for keyword triggers and sends personalized DMs to convert engagement into pipeline | Lead-gen funnels, lead magnets, "comment INFO to get the PDF" workflows |
| 3 | **[viraloop](./skills/viraloop/)** | Convert any URL into a 6-slide carousel for TikTok + Instagram with visual coherence, auto-trending music, and a built-in analytics feedback loop | Repurposing a blog post, landing page or product page into a viral-shaped carousel without manual design work |
| 4 | **[autoshorts](./skills/autoshorts/)** | A daily pipeline that finds every viral short-form moment in a long video (Whisper transcription + Gemini multimodal selection), cuts each one with FFmpeg, overlays a hook, and publishes the approved clips to TikTok / Reels / Shorts | Content repurposing from podcasts, interviews, livestreams or long-form videos into a steady stream of shorts |
| 5 | **[upload-post](./skills/upload-post/)** | Foundational knowledge of the Upload-Post API surface — endpoints, profile model, scheduling semantics, platform-specific overrides | Lower-level integration when the higher-level skills above don't cover the use case; mostly automatic when paired with the Upload-Post MCP connector |

## How to install

This repo is packaged as a **plugin** for both Codex and Claude Code (manifests in `.codex-plugin/` and `.claude-plugin/`), and the five skills live under `skills/`. Pick the path for your agent.

### OpenAI Codex (plugin)

The repo ships a marketplace manifest at `.agents/plugins/marketplace.json`. Add it as a marketplace, then install the `upload-post` plugin. The plugin bundles all five skills plus the Upload-Post MCP server (`.mcp.json`), so Codex gets the tools and the workflows in one install.

```bash
git clone https://github.com/Upload-Post/upload-post-skills
# point Codex at the bundled marketplace at the repo root (.agents/plugins/marketplace.json)
```

(Public Codex Plugin Directory publishing is rolling out — until then, install from the repo or share within your workspace.)

### Claude Code (plugin)

```bash
git clone https://github.com/Upload-Post/upload-post-skills
/plugin install ./upload-post-skills
```

Claude Code reads `.claude-plugin/plugin.json`, auto-discovers every skill under `skills/`, and wires up the MCP connector from `.mcp.json`.

### Manual / Cursor / Windsurf / OpenClaw / any skills-compatible agent

The skills follow the open [Agent Skills standard](https://agentskills.io), so they work in any compatible client. Copy the skill folders into whatever directory your agent treats as its skills root:

```bash
git clone https://github.com/Upload-Post/upload-post-skills
cp -r upload-post-skills/skills/* ~/.claude/skills/   # or your agent's skills dir
```

Each folder under `skills/` is a separately discoverable skill — the agent reads each `SKILL.md` frontmatter to decide when to activate it.

## Pairs with the Upload-Post MCP connector

These skills work standalone (they document how to call the Upload-Post API directly over HTTP), but become **significantly more powerful** when paired with the [Upload-Post MCP connector](https://github.com/Upload-Post/upload-post-mcp). With the connector enabled:

- Each skill's "call the API" instructions are automatically routed through MCP tool invocations (`upload_video`, `get_analytics`, `send_dm`, …) instead of raw `curl`.
- Claude sees the same operations with native tool annotations (`readOnlyHint`, `destructiveHint`) and can surface confirmation prompts before destructive actions.
- No API key handling inside prompts — OAuth flow stores the credential once at the connector level.

Add the connector at `https://mcp.upload-post.com/mcp` in any MCP-compatible client. See the [connector docs](https://docs.upload-post.com/guides/mcp-server-integration) for setup.

## Picking a skill — quick decision guide

```
Do you want to grow on TikTok + Instagram with slideshow ads?            → larry-marketing
Do you want comments on a specific post to trigger personalized DMs?     → comment-funnel
Do you want to turn a URL into a viral 6-slide carousel?                 → viraloop
Do you have long-form videos and want a steady stream of shorts/reels?   → autoshorts
You're integrating the API at a lower level and need the reference?      → upload-post
```

Claude will usually choose correctly on its own — these descriptions are also in each skill's `SKILL.md` frontmatter.

## Compatibility

All five skills work with:

- **Claude Code** (Anthropic's official CLI)
- **Claude Desktop** (with MCP enabled)
- **Cursor** (MCP-compatible)
- **OpenClaw / ClawHub**
- **Windsurf** and any other agent that loads Anthropic Agent Skills

## Source repositories

Each skill is also published as a standalone repository for users who want only one:

| Skill | Standalone repo |
|---|---|
| larry-marketing | https://github.com/Upload-Post/upload-post-larry-marketing-skill |
| comment-funnel | https://github.com/mutonby/upload-post-comment-funnel |
| viraloop | https://github.com/mutonby/viraloop |
| autoshorts | https://github.com/mutonby/skill-autoshorts |
| upload-post | https://github.com/Upload-Post/upload-post-skill |

This monorepo is the canonical, single-install entry point. The standalone repos remain available for backwards compatibility.

## Contributing

Issues and pull requests welcome at https://github.com/Upload-Post/upload-post-skills/issues. For Upload-Post API support: info@upload-post.com.

## License

MIT — see [LICENSE](./LICENSE). Each subdirectory may carry its own license file with additional details; the top-level MIT applies to the bundle as a whole.
