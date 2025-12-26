# Vibe Guide Plugin Structure

```
📁 vibe-guide/
│
├── 📁 .claude-plugin/
│   └── 📄 plugin.json          🏷️  Plugin manifest (name, version, author)
│
├── 📖 README.md                 📚 Documentation with examples & install instructions
│
├── 📁 agents/
│   ├── 🤖 worker.md            ⚙️  Executes work in tiny steps, updates status.json
│   ├── 🗣️ explainer.md         💬 Translates progress into plain language (no jargon)
│   └── 🎓 explorer.md          💡 Educational micro-lessons when learning mode is on
│
├── 📁 commands/
│   ├── 🚀 vibe.md              ▶️  Start a session: /vibe-guide:vibe <goal>
│   ├── 📊 status.md            👀 Check progress: /vibe-guide:status
│   ├── ⏭️ continue.md          🔄 Run next step: /vibe-guide:continue
│   ├── ⏸️ stop.md              ⏯️  Pause/resume: /vibe-guide:stop
│   ├── 🔍 details.md           🔧 Toggle verbosity: /vibe-guide:details on|off
│   ├── 📚 learn.md             🎯 Toggle learning: /vibe-guide:learn on|off
│   └── ❓ guide.md             📖 Show usage help: /vibe-guide:guide
│
└── 📁 hooks/
    └── 🪝 hooks.json           🧹 Auto-summarizes verbose output (diffs, logs)
```

## What Each Component Does

### Agents

| Agent | Purpose |
|-------|---------|
| 🤖 **worker** | Does the actual work, one step at a time. Writes to `.vibe/status.json` |
| 🗣️ **explainer** | The friendly voice. Converts technical stuff to plain English |
| 🎓 **explorer** | Teaches concepts with simple analogies (only when learning mode on) |

### Commands

| Command | What It Does |
|---------|--------------|
| 🚀 `/vibe-guide:vibe` | Starts everything. Give it a goal, it creates the session |
| 📊 `/vibe-guide:status` | Shows where you are without doing more work |
| ⏭️ `/vibe-guide:continue` | Runs the next step and shows what happened |
| ⏸️ `/vibe-guide:stop` | Pauses work so you can take a break |
| 🔍 `/vibe-guide:details` | Shows slightly more info (still no raw code) |
| 📚 `/vibe-guide:learn` | Adds mini-lessons after each step |
| ❓ `/vibe-guide:guide` | Shows this usage guide with examples |

### Hook

| Hook | What It Does |
|------|--------------|
| 🪝 **PostToolUse** | Catches verbose Bash/Read/Grep output and summarizes it |

## Runtime Files (Created in Your Project)

```
📁 .vibe/                        🗂️  Session state folder (auto-added to .gitignore)
├── 📄 session.json             ⚙️  Goal, settings, pause state
├── 📄 status.json              📍 Current step, progress, errors
└── 📄 changelog.md             📝 Human-readable log of all steps
```
