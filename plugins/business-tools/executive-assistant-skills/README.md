# Executive Assistant Skills

AI-powered executive assistant skills for Claude Code that **fully replace a human EA**. These skills were born from a real experiment by Martin Gontovnikas ([@mgonto](https://github.com/mgonto)), Auth0's former VP of Marketing/Growth, who discovered that a set of well-crafted Claude Code skills could handle everything his executive assistant used to do — meeting prep, email drafting, action item tracking, and daily digests.

The result: a suite of 5 skills that autonomously research attendees before meetings, draft personalized emails, extract and manage action items in Todoist, and deliver a morning executive briefing — all without human intervention.

## Skills

| Skill | Description |
|-------|-------------|
| **meeting-prep** | Researches upcoming meeting attendees via OpenClaw, compiles background briefs with talking points, and surfaces relevant context from past interactions. |
| **action-items-todoist** | Extracts action items from meeting transcripts (Granola/Grain) and creates structured Todoist tasks with due dates, priorities, and project assignments. |
| **email-drafting** | Drafts context-aware emails using your communication style, past threads, and meeting notes. Sends via the `gog` Gmail CLI. |
| **executive-digest** | Generates a daily morning briefing covering your calendar, pending action items, priority emails, and key context for the day ahead. |
| **todoist-due-drafts** | Reviews Todoist tasks approaching their due dates, drafts follow-up emails or messages for items that need outreach, and queues them for review. |

> **Note:** The original repo includes a "humanizer" skill (originally by [biostartechnology](https://github.com/biostartechnology)) for rewriting AI-generated text in a more natural voice. It has been excluded from this plugin as it is a third-party contribution with a separate origin.

## Prerequisites

These skills rely on several external tools and services:

- **[OpenClaw](https://openclaw.com)** — People research API used by meeting-prep to look up attendee backgrounds, company info, and social profiles.
- **[gog CLI](https://github.com/mgonto/gog)** — Gmail on the Go, a CLI for sending and reading Gmail. Used by email-drafting and executive-digest.
- **[Granola](https://granola.ai) or [Grain](https://grain.com)** — Meeting transcript sources. Action-items-todoist parses transcripts from these tools to extract tasks.
- **[Todoist CLI](https://github.com/sachaos/todoist)** — Command-line interface for Todoist. Used by action-items-todoist and todoist-due-drafts to create and query tasks.

## Important: Configuration Required

These skills are **deeply personalized** to mgonto's specific workflow, integrations, and preferences. They will not work out of the box for other users.

To adapt them for your own use, you must create a `config/user.json` file in the plugin directory with your own settings, including:

- **Timezone** and locale
- **Email accounts** (personal, work, aliases)
- **Todoist project mappings** (which projects map to which areas of your life)
- **Meeting tools** configuration (Granola vs Grain, calendar source)
- **Communication style** preferences and signature
- **OpenClaw API key**

Each skill reads from this config to personalize its behavior. Without it, the skills will fall back to mgonto's defaults, which almost certainly won't match your setup.

See the [original repository](https://github.com/mgonto/executive-assistant-skills) for the full setup guide and example configuration.

## Author

**Martin Gontovnikas** ([@mgonto](https://github.com/mgonto)) — Auth0's former VP of Marketing/Growth, now at [Hypergrowth Partners](https://hypergrowthpartners.com). Martin built these skills after realizing that Claude Code, given the right instructions and tool access, could handle the full scope of executive assistant work autonomously.

## License

MIT
