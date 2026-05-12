# agency-os

> Run your work like an AI agency, from a single Notion board.

Turn Notion into the dashboard of your own AI agency. You discuss ideas with the agent, it clarifies scope and writes the plan into Notion, you approve, and agents ship the work in parallel - with result links back on the row.

## What you get

- **Agent-driven planning.** Talk through an idea in plain English. The agent asks questions, carves work into tasks and subtasks, sets dependencies, and writes the plan to Notion.
- **One board for everything.** Ideas, tasks, decisions, and finished work in one place.
- **Parallel execution.** Agents run Exec=Agent rows in parallel, respecting dependency order. Right model for the job - fast models for mechanical work, bigger ones for judgment tasks.
- **Operator-gated.** Nothing dispatches autonomously. Every run is opt-in; the board is honest about what's queued and why.

## Quick Start

1. Duplicate the [public Notion template](https://www.notion.so/35dd01a02a8081dea01cd8d42617f0c8) into your workspace.
2. Create a Notion integration at https://www.notion.so/my-integrations and share it with the duplicated page.
3. Add `NOTION_KEY=secret_...` to your `.env`.
4. Run `/agency-os scaffold` to wire the board.

Full setup guide: https://github.com/ratamaha-git/agency-os/blob/main/docs/harnesses/claude-code.md

## Skills

- `/agency-os suggest` - Drop an idea into the Notion inbox
- `/agency-os discuss` - Open a task for clarification with the agent
- `/agency-os approve` - Promote to To-Do (cascades subtasks)
- `/agency-os start` - Flip To-Do to In Progress and load the kickoff brief
- `/agency-os run --go` - Batch-execute all Exec=Agent To-Do rows
- `/agency-os done` - Close with a result link

## Learn more

- GitHub: https://github.com/ratamaha-git/agency-os
- Launch post: https://automatelab.tech/p/b3e8d44b-dd98-4e16-a888-9b1be7e9829c/

## License

MIT - AutomateLab
