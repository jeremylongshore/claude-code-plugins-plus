# Gas Town

Multi-agent orchestrator for Claude Code. The Cognition Engine.

Track work with convoys; sling to agents.

## What It Does

Gas Town turns your Claude Code session into an AI-powered software factory:

```
Work Flow
═════════

  Work arrives → tracked as bead (gt-123) → joins a convoy
                                                  │
                                                  ▼
                              ┌─────────────────────────────────┐
                              │  gt sling <bead> <rig>          │
                              │  (you run this for the user)    │
                              └─────────────────────────────────┘
                                                  │
                                                  ▼
                         ┌────────────────────────────────────────┐
                         │  Worker spawns (polecat or crew)       │
                         │  Work lands on their HOOK              │
                         │  GUPP: If hook has work, RUN IT        │
                         └────────────────────────────────────────┘
```

## Characters

| Role | Icon | Job |
|------|------|-----|
| Mayor | 🦊 | Dispatches work, coordinates rigs |
| Witness | 🦅 | Watches workers, nudges when stuck |
| Refinery | 🦡 | Merges code, quality control |
| Polecats | 🦨 | Quick task workers (spawn & vanish) |
| Crew | 👷 | Persistent named helpers |
| Dogs | 🐕 | Health checks, diagnostics |
| Deacon | ⚙️ | Infrastructure daemon |
| Overseer | 👤 | **YOU** - driving the engine |

## Installation

### Via Claude Code Plugin Marketplace

```bash
/plugin install gastown@claude-code-plugins-plus
```

### Via n-skills Marketplace

```bash
/plugin marketplace add numman-ali/n-skills
/plugin install gastown@n-skills
```

## Requirements

- Go 1.21+ (for the `gt` and `bd` CLI tools)
- Claude Code with Opus (recommended for best results)
- GitHub access for rig management

## Usage

Just tell Claude what you want:

- "Set up gastown" - Installs and configures the engine
- "Sling this work" - Assigns tasks to polecats
- "Check on my polecats" - Status of running workers
- "Fire up the engine" - Start the orchestration system

Claude runs all commands. You just talk.

## Files

```
gastown/
├── .claude-plugin/
│   └── plugin.json         # Plugin metadata
├── skills/
│   ├── SKILL.md            # Main skill definition
│   └── references/
│       ├── commands.md     # Full command reference
│       ├── concepts.md     # Domain concepts (GUPP, hooks, etc.)
│       ├── setup.md        # Installation walkthrough
│       ├── troubleshooting.md  # Error diagnosis
│       └── tutorial.md     # Step-by-step learning journey
├── LICENSE                 # Apache 2.0
└── README.md               # This file
```

## The Propulsion Principle

> **If your hook has work, RUN IT.**

This is GUPP - the Gas Town Universal Propulsion Principle.

The engine runs because workers execute what's hooked. No waiting. No asking.
Work on hook → RUN.

## Resources

- **Gas Town CLI**: https://github.com/steveyegge/gastown
- **n-skills Marketplace**: https://github.com/numman-ali/n-skills

## License

Apache 2.0 - See LICENSE file
