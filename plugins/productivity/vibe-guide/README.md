# Vibe Guide

Non-technical progress summaries for Claude Code work. Hides diffs, logs, and technical noise so you can pair program with AI without being overwhelmed by implementation details.

## What's New in This Package

Vibe Guide introduces a completely new way to interact with Claude Code:

- **Stepwise Execution**: Instead of running everything at once, work happens in small, reviewable steps
- **Plain Language Updates**: No more walls of code diffs - you get friendly summaries of what changed
- **Error Checklists**: When something breaks, you get a numbered list of what to do, not a stack trace
- **Learning Mode**: Optional educational micro-explanations teach concepts as you go
- **Session Persistence**: Progress is saved to `.vibe/` so you can pause and resume anytime
- **Auto-Summarization**: Hook automatically condenses verbose command output

This plugin is perfect for:
- Non-technical founders working with AI to build products
- Designers reviewing code changes
- Product managers pairing on implementations
- Anyone who wants to understand what's happening without reading code

## Installation

### Option 1: Install from Marketplace (Recommended)

```bash
# Step 1: Add the marketplace to Claude Code
/plugin marketplace add jeremylongshore/claude-code-plugins

# Step 2: Install vibe-guide
/plugin install vibe-guide@claude-code-plugins-plus

# Step 3: Verify installation
/vibe-guide:guide
```

### Option 2: Install via CLI

```bash
# Using the Claude Code CLI
claude plugin install vibe-guide@claude-code-plugins-plus
```

### Option 3: Local Development

```bash
# Clone the repository
git clone https://github.com/jeremylongshore/claude-code-plugins.git

# Run Claude with the plugin directory
claude --plugin-dir ./claude-code-plugins/plugins/productivity/vibe-guide
```

## Commands

| Command | Description |
|---------|-------------|
| `/vibe-guide:vibe <goal>` | 🚀 Start a new session with a goal |
| `/vibe-guide:status` | 📊 Show current progress |
| `/vibe-guide:continue` | ⏭️ Run the next step |
| `/vibe-guide:stop` | ⏸️ Pause or resume the session |
| `/vibe-guide:details on\|off` | 🔍 Toggle technical details |
| `/vibe-guide:learn on\|off` | 📚 Toggle educational explanations |
| `/vibe-guide:guide` | ❓ Show usage help with examples |

## Quick Start

```bash
# Start a session with your goal
/vibe-guide:vibe Build a WNBA stats table page

# Check progress anytime
/vibe-guide:status

# Keep going step by step
/vibe-guide:continue

# Want to learn as you go?
/vibe-guide:learn on

# Need help?
/vibe-guide:guide
```

## Progressive Workflow

Vibe Guide uses a **stepwise approach** - each command does ONE thing:

```
/vibe-guide:vibe "Add dark mode"     ← Start session, run step 1
         ↓
/vibe-guide:continue                  ← Run step 2
         ↓
/vibe-guide:continue                  ← Run step 3
         ↓
      ... repeat ...
         ↓
      ✅ Done!
```

This gives you control - review each step before moving on.

## Example Transcripts

### Happy Path

```
> /vibe-guide:vibe Add a dark mode toggle to settings

1) Where we are
   Starting a new task: adding dark mode toggle to settings.

2) What changed
   - Created session tracking folder
   - Analyzed the project structure
   - Found the Settings component

3) What I checked
   - Project uses React
   - Settings page exists

4) What's next
   Add the toggle component to the settings page.

5) Do you need to do anything?
   No, nothing needed right now.

> /vibe-guide:continue

1) Where we are
   Added the toggle switch to the settings page.

2) What changed
   - Created a new toggle component
   - Added it to the Settings page
   - Connected it to save preferences

3) What I checked
   - Toggle renders correctly
   - Click changes the value

4) What's next
   Add the actual dark theme styles.

5) Do you need to do anything?
   No, nothing needed right now.
```

### Polling Path (Multiple Continues)

```
> /vibe-guide:vibe Build a WNBA stats table page

1) Where we are
   Starting a new task: building a WNBA stats table page.

2) What changed
   - Set up session tracking
   - Analyzed project structure

3) What I checked
   - Found existing pages folder
   - Identified data fetching pattern

4) What's next
   Create the stats page component.

5) Do you need to do anything?
   No, nothing needed right now.

> /vibe-guide:continue

1) Where we are
   Created the basic stats page.

2) What changed
   - Added new stats page
   - Set up the route

3) What I checked
   - Page loads correctly
   - Route works

4) What's next
   Add the data table component.

5) Do you need to do anything?
   No, nothing needed right now.

> /vibe-guide:continue

1) Where we are
   Added the stats table with sample data.

2) What changed
   - Created table component
   - Added column headers
   - Displayed sample WNBA data

3) What I checked
   - Table renders
   - Data displays correctly

4) What's next
   Connect to real data source.

5) Do you need to do anything?
   No, nothing needed right now.
```

### Error Path

```
> /vibe-guide:vibe Connect to the Postgres database

1) Where we are
   Setting up database connection.

[... continues ...]

> /vibe-guide:continue

Something went wrong, but it's fixable.

What happened: Couldn't connect to the database server.

To fix this:
1. Check if PostgreSQL is running (run: pg_isready)
2. Verify your DATABASE_URL in the .env file
3. Make sure the database exists

After you've done that, run /vibe-guide:status to continue.
```

## Plugin Structure

```
📁 vibe-guide/
├── 📁 .claude-plugin/
│   └── 📄 plugin.json          🏷️  Plugin manifest
├── 📖 README.md                 📚 This file
├── 📁 agents/
│   ├── 🤖 worker.md            ⚙️  Executes tiny steps
│   ├── 🗣️ explainer.md         💬 Plain language output
│   └── 🎓 explorer.md          💡 Learning micro-lessons
├── 📁 commands/
│   ├── 🚀 vibe.md              ▶️  Start session
│   ├── 📊 status.md            👀 Check progress
│   ├── ⏭️ continue.md          🔄 Run next step
│   ├── ⏸️ stop.md              ⏯️  Pause/resume
│   ├── 🔍 details.md           🔧 Toggle verbosity
│   ├── 📚 learn.md             🎯 Toggle learning
│   └── ❓ guide.md             📖 Show usage help
└── 📁 hooks/
    └── 🪝 hooks.json           🧹 Auto-summarize verbose output
```

## Session Files

Vibe Guide stores state in `.vibe/` at your project root:

| File | Purpose |
|------|---------|
| `session.json` | Goal, settings, pause state |
| `status.json` | Current step, progress, errors |
| `changelog.md` | Human-readable log of all steps |

This folder is automatically added to `.gitignore`.

## Requirements

- Claude Code (any recent version)
- No additional dependencies

## Troubleshooting

### Plugin not found after install
```bash
# Verify the marketplace is added
/plugin marketplace list

# Re-add if needed
/plugin marketplace add jeremylongshore/claude-code-plugins
```

### Commands not working
```bash
# Check plugin is installed
/plugin list

# Reinstall if needed
/plugin uninstall vibe-guide@claude-code-plugins-plus
/plugin install vibe-guide@claude-code-plugins-plus
```

### Session stuck or corrupted
```bash
# Remove the .vibe folder and start fresh
rm -rf .vibe/
/vibe-guide:vibe <your goal>
```

## Contributors

- Intent Solutions - Initial development
- Jeremy Longshore - Plugin integration

## License

MIT
