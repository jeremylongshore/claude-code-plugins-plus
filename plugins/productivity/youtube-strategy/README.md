# YouTube Strategy Plugin

Complete YouTube content production workflow powered by AI. Research competitors, generate video ideas, build production briefs, craft optimized titles and thumbnails, and create detailed video outlines.

## Skills

| Skill | What It Does |
|-------|-------------|
| `yt-research` | Research competitor channels, niches, and trending topics |
| `yt-ideation` | Generate and validate video ideas aligned with content pillars |
| `yt-brief` | Refine a video idea into a structured production brief |
| `yt-packaging` | Create optimized titles and thumbnail concepts for maximum CTR |
| `yt-outline` | Build step-by-step video outlines with demo prep and visual planning |

## Commands

| Command | Description |
|---------|-------------|
| `/youtube-strategy` | See all available skills and choose what to work on |
| `/yt-pipeline` | Run the complete Research > Ideate > Brief > Package > Outline workflow |
| `/yt-research` | Research competitor channels and trending topics |
| `/yt-ideate` | Generate and validate video ideas |
| `/yt-brief` | Create a structured production brief |
| `/yt-package` | Create optimized titles and thumbnail concepts |
| `/yt-outline` | Build a detailed video outline with demo prep |

## Agents

| Agent | Purpose |
|-------|---------|
| `yt-scraper` | Orchestrate YouTube data scraping via Apify |
| `channel-analyzer` | Competitive intelligence analysis per channel batch |
| `idea-validator` | Validate video ideas against search demand and competition |

## Workflow

The recommended workflow follows these stages:

1. **Research** (`/yt-research`) - Analyze competitors, identify content gaps
2. **Ideation** (`/yt-ideate`) - Generate 15-20 ideas, validate against demand
3. **Brief** (`/yt-brief`) - Refine selected ideas into production briefs
4. **Packaging** (`/yt-package`) - Create title options and thumbnail concepts
5. **Outline** (`/yt-outline`) - Build detailed outlines with demo prep checklists

Use `/yt-pipeline` to run all stages in sequence with human checkpoints.

## Installation

```bash
/plugin install youtube-strategy@claude-code-plugins-plus
```
