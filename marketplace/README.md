# Claude Code Skills Hub - Marketplace Website

[![Version](https://img.shields.io/badge/version-3.0.0-brightgreen)](../CHANGELOG.md)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-244%20Skills-orange?logo=sparkles)](https://claudecodeplugins.io/skills/)
[![Plugins](https://img.shields.io/badge/Total%20Plugins-259-blue)](https://claudecodeplugins.io/)
[![Live Routes](https://img.shields.io/badge/Live%20Routes-521-success)](https://claudecodeplugins.io/)
[![Astro](https://img.shields.io/badge/Built%20with-Astro%205.16-FF5D01?logo=astro)](https://astro.build)
[![Tailwind CSS](https://img.shields.io/badge/Styled%20with-Tailwind%204.1-38B2AC?logo=tailwind-css)](https://tailwindcss.com)

### Technology Partners
[![Powered by Anthropic](https://img.shields.io/badge/Powered%20by-Anthropic%20Claude-5436DA?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMkM2LjQ4IDIgMiA2LjQ4IDIgMTJzNC40OCAxMCAxMCAxMCAxMC00LjQ4IDEwLTEwUzE3LjUyIDIgMTIgMnoiIGZpbGw9IiNmZmYiLz48L3N2Zz4=)](https://www.anthropic.com/)
[![Built on Google Cloud](https://img.shields.io/badge/Built%20on-Google%20Cloud-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/)
[![Ollama Compatible](https://img.shields.io/badge/Ollama-Compatible-000000?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMkM2LjQ4IDIgMiA2LjQ4IDIgMTJzNC40OCAxMCAxMCAxMCAxMC00LjQ4IDEwLTEwUzE3LjUyIDIgMTIgMnoiIGZpbGw9IiNmZmYiLz48L3N2Zz4=)](https://ollama.com/)
**Sponsored by [nixtla.io](https://nixtla.io)**

---

**Live Site:** [claudecodeplugins.io](https://claudecodeplugins.io)

Static site generator for the Claude Code plugins marketplace. Built with Astro 5.16, Tailwind CSS 4.1, and Fuse.js for instant search.

## Features

- **244 Searchable Skills** - Instant fuzzy search with Fuse.js
- **521 Static Routes** - Pre-rendered for maximum performance
- **Learning Hub** - Interactive tutorials and production workflows
- **Skills Directory** - Filterable, sortable catalog with metadata
- **Zero JavaScript Required** - Progressive enhancement only

## Quick Start

```bash
# Install dependencies
npm install

# Start dev server (localhost:4321)
npm run dev

# Generate skills catalog
npm run skills:generate

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
marketplace/
├── src/
│   ├── pages/              # Astro pages (static routes)
│   │   ├── index.astro     # Homepage
│   │   ├── skills/         # Skills directory
│   │   ├── learning/       # Learning hub
│   │   └── plugins/        # Plugin pages
│   ├── components/         # Reusable components
│   ├── data/              # Generated catalogs
│   │   └── skills-catalog.json
│   └── layouts/           # Page layouts
├── public/                # Static assets
├── scripts/               # Build scripts
│   └── discover-skills.mjs
└── package.json
```

## Build Process

1. **Skills Discovery** (`npm run skills:generate`)
   - Scans `../plugins/` for `SKILL.md` files
   - Extracts frontmatter metadata
   - Generates `src/data/skills-catalog.json`
   - 244 skills across 16 categories

2. **Astro Build** (`astro build`)
   - Generates 521 static HTML pages
   - Optimized CSS with Tailwind 4.1
   - Minimal JavaScript (search only)
   - Output: `dist/` directory

3. **Deployment** (automatic on push to main)
   - GitHub Actions workflow
   - Deploys to GitHub Pages
   - CDN: Cloudflare (auto-configured)

## Key Routes

- `/` - Homepage with hero, stats, CTA
- `/skills/` - Searchable skills catalog (244 skills)
- `/learning/` - Interactive tutorials and guides
- `/plugins/[name]/` - Individual plugin pages (259 plugins)
- `/playbooks/` - Production workflow playbooks

## Performance

- **Bundle Size:** 1.66 MB (40% reduction from 2.79 MB)
- **Lighthouse Score:** 98+ on all metrics
- **Load Time:** < 2s on 3G
- **Search:** < 50ms fuzzy search with Fuse.js

## Development Commands

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `npm install`             | Install dependencies                             |
| `npm run dev`             | Start dev server at `localhost:4321`             |
| `npm run skills:generate` | Regenerate skills catalog from plugins           |
| `npm run build`           | Build production site to `./dist/`               |
| `npm run preview`         | Preview production build locally                 |
| `npm run astro ...`       | Run Astro CLI commands                           |

## Technology Stack

- **Framework:** Astro 5.16.0 (static site generator)
- **Styling:** Tailwind CSS 4.1.17
- **Search:** Fuse.js 7.1.0 (fuzzy search)
- **Typography:** Poppins (headings) + Lora (body)
- **Icons:** SVG icons (inline)
- **Deployment:** GitHub Pages + Cloudflare CDN

## Design System

**Brand Colors:**
- Dark: `#141413`
- Light: `#faf9f5`
- Mid Gray: `#b0aea5`
- Orange: `#d97757` (primary accent)
- Blue: `#6a9bcc`
- Green: `#788c5d`

**Typography:**
- Headings: Poppins (sans-serif)
- Body: Lora (serif)
- Monospace: System default

## Contributing

See [../CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

## License

MIT License - see [../LICENSE](../LICENSE)

---

**Maintained by:** Intent Solutions IO
**Contact:** jeremy@intentsolutions.io
**Repository:** [github.com/jeremylongshore/claude-code-plugins](https://github.com/jeremylongshore/claude-code-plugins)
