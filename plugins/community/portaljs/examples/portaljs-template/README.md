# PortalJS Template

This is the canonical template used by the `/portaljs-new-portal` skill. It is a real Next.js project — you can run it directly.

## Running the template

```bash
cd examples/portaljs-template
npm install
npm run dev
```

## Placeholder tokens

Files contain `{{PLACEHOLDER}}` tokens that `/portaljs-new-portal` replaces at scaffold time:

| Token | Replaced with |
|-------|--------------|
| `__PROJECT_NAME__` | Human-readable portal name (e.g. "Auckland Open Data Portal") |
| `__PROJECT_SLUG__` | URL-safe slug (e.g. `auckland-open-data`) |
| `__DESCRIPTION__` | One-sentence portal description |

## Improving the boilerplate

1. Edit files in this directory directly
2. Run `npm run dev` to verify changes work
3. Commit — the next `/portaljs-new-portal` run picks up your changes automatically

No need to touch `.claude/commands/portaljs-new-portal.md` when changing page layouts, styles, or component usage. Only edit the skill file when changing *how* scaffolding works (steps, error handling, argument parsing).
