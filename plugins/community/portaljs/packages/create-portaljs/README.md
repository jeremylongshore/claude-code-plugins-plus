# create-portaljs

Scaffold a [PortalJS](https://github.com/datopian/portaljs) data portal in one command.

```bash
npm create portaljs@latest my-portal
# or: npx create-portaljs@latest my-portal · pnpm create portaljs · yarn create portaljs
```

It downloads the canonical `portaljs-catalog` template into `my-portal/`, substitutes your
project name/description, sets the namespace mode, and (optionally) runs `git init` +
`npm install`. Then:

```bash
cd my-portal
npm run dev      # → http://localhost:3000
```

You get the three surfaces — **Home**, a **Catalog** (`/search`), and a dataset **Showcase**
(`/@<namespace>/<slug>`) — over sample data. Plain, editable Next.js. No lock-in.

## Options

```
create-portaljs [directory] [options]

  --namespace <theme|owner>  Namespace mode (default: theme)
  --name <string>            Human project name (default: from directory)
  --description <string>     One-line description
  --ref <git-ref>            Template ref to fetch (default: main)
  --no-install               Skip npm install
  --no-git                   Skip git init
  -y, --yes                  Accept defaults, no prompts (CI-friendly)
  -h, --help                 Show help
```

Any option given on the CLI skips its prompt; `--yes` skips all prompts.

## What next

The PortalJS agentic skills are bundled into the new project's `.claude/commands/`,
so they work the moment you run `claude` in the portal directory — no separate
install. Build it out with them (or by hand — it's just Next.js):
`/portaljs-add-dataset`, `/portaljs-add-resource`, `/portaljs-add-chart`, `/portaljs-add-map`, `/portaljs-connect-ckan`, `/portaljs-deploy`.
See the [docs](https://www.portaljs.com/docs/quickstart).
