# Gastown CLI Commands Reference

**Internal Reference for Claude Code** - You run all these commands for the user.

Complete reference for `gt` (gastown) CLI commands. All commands support `--help` for detailed usage.

## Command Groups

Commands are organized into functional groups:

| Group | Description |
|-------|-------------|
| **services** | Service lifecycle (up, down, stop) |
| **orchestration** | Work coordination (convoy, sling, broadcast) |
| **workers** | Worker management (polecat, crew, dog) |
| **workspace** | Workspace operations (init, rig, worktree) |
| **communication** | Inter-agent messaging (mail, escalate, handoff) |
| **diagnostics** | Status and debugging (status, prime, whoami, version) |

---

## Service Lifecycle Commands

### gt up

Bring up all Gas Town services (idempotent boot command).

**Syntax:**
```bash
gt up [flags]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `-q, --quiet` | Only show errors |
| `--restore` | Also restore crew (from settings) and polecats (from hooks) |

**Services Started:**
- Daemon - Go background process that pokes agents
- Deacon - Health orchestrator (monitors Mayor/Witnesses)
- Mayor - Global work coordinator
- Witnesses - Per-rig polecat managers
- Refineries - Per-rig merge queue processors

**Examples:**
```bash
gt up                  # Start all infrastructure
gt up --quiet          # Start silently, show only errors
gt up --restore        # Also start crew and polecats with pinned work
```

**Common Use Cases:**
- Starting your Gas Town workspace after boot
- Recovering after a system restart
- Ensuring all services are running before starting work

---

### gt down

Stop all Gas Town infrastructure services.

**Syntax:**
```bash
gt down [flags]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `-q, --quiet` | Only show errors |
| `-f, --force` | Force kill without graceful shutdown |
| `-a, --all` | Also kill the tmux server |

**What it stops:**
- Witnesses (per-rig polecat managers)
- Mayor (global work coordinator)
- Boot (Deacon's watchdog)
- Deacon (health orchestrator)
- Daemon (Go background process)

**Note:** Polecats are NOT stopped by `gt down`. Use `gt stop --all` for emergency polecat shutdown.

**Examples:**
```bash
gt down                  # Graceful shutdown of infrastructure
gt down --force          # Force immediate shutdown
gt down --all            # Also kill tmux server
```

**Common Use Cases:**
- Shutting down for the night
- Preparing for maintenance
- Clean restart of services

---

### gt stop

Emergency stop for polecat sessions.

**Syntax:**
```bash
gt stop [flags]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--all` | Stop all sessions across all rigs (required if no --rig) |
| `--rig <name>` | Stop all sessions in a specific rig |
| `--graceful` | Try graceful shutdown before force kill |

**Note:** Must specify either `--all` or `--rig`. This is for emergency polecat shutdown only.

**Examples:**
```bash
gt stop --all                # Kill ALL polecat sessions across all rigs
gt stop --rig wyvern         # Kill all sessions in the wyvern rig
gt stop --all --graceful     # Try graceful shutdown first
```

---

## Orchestration Commands

### gt convoy

Track batches of work across rigs. A convoy is a persistent tracking unit that monitors related issues.

**Syntax:**
```bash
gt convoy [subcommand] [flags]
```

**Parent Command Flags:**
| Flag | Description |
|------|-------------|
| `-i, --interactive` | Launch interactive TUI dashboard |

**Subcommands:**
| Subcommand | Description |
|------------|-------------|
| `create` | Create a new convoy |
| `list` | List convoys |
| `status` | Show convoy status |
| `add` | Add issues to an existing convoy |

**Flags for `convoy create`:**
| Flag | Description |
|------|-------------|
| `--molecule string` | Associated molecule ID |
| `--notify` | Address to notify on completion (default: mayor/) |

**Flags for `convoy list`:**
| Flag | Description |
|------|-------------|
| `--json` | Output as JSON |
| `--status string` | Filter by status (open, closed) |
| `--all` | Show all convoys (open and closed) |

**Flags for `convoy status`:**
| Flag | Description |
|------|-------------|
| `--json` | Output as JSON |

**Examples:**
```bash
gt convoy create "Deploy v2.0" gt-abc bd-xyz     # Create convoy tracking issues
gt convoy create "Release prep" gt-abc --notify  # Notify mayor on completion
gt convoy list                                   # List open convoys
gt convoy list --all                             # List all convoys
gt convoy status hq-cv-abc                       # Detailed convoy status
gt convoy status 1                               # Status by number (from list)
gt convoy add hq-cv-abc gt-new-issue             # Add issue to convoy
gt convoy -i                                     # Interactive TUI
```

**Common Use Cases:**
- Tracking batches of related work across rigs
- Monitoring progress of parallel tasks
- Getting notified when all tracked issues complete

---

### gt sling

Sling work onto an agent's hook and start working immediately. THE unified work dispatch command.

**Syntax:**
```bash
gt sling <bead-or-formula> [target] [flags]
```

**Target Resolution:**
- `gt sling gt-abc` - Self (current agent)
- `gt sling gt-abc crew` - Crew worker in current rig
- `gt sling gt-abc greenplace` - Auto-spawn polecat in rig
- `gt sling gt-abc greenplace/Toast` - Specific polecat
- `gt sling gt-abc mayor` - Mayor
- `gt sling gt-abc deacon/dogs` - Auto-dispatch to idle dog
- `gt sling gt-abc deacon/dogs/alpha` - Specific dog

**Flags:**
| Flag | Description |
|------|-------------|
| `-s, --subject string` | Context subject for the work |
| `-m, --message string` | Context message for the work |
| `-n, --dry-run` | Show what would be done |
| `--on string` | Apply formula to existing bead (implies wisp scaffolding) |
| `--var stringArray` | Formula variable (key=value), can be repeated |
| `-a, --args string` | Natural language instructions for the executor |
| `--naked` | No-tmux mode: assign work but skip session creation |
| `--create` | Create polecat if it doesn't exist |
| `--molecule string` | Molecule workflow to instantiate on the bead |
| `--force` | Force spawn even if polecat has unread mail |
| `--account string` | Claude Code account handle to use |
| `-q, --quality string` | Polecat workflow quality level (basic\|shiny\|chrome) |
| `--no-convoy` | Skip auto-convoy creation for single-issue sling |

**Examples:**
```bash
gt sling gt-abc greenplace                          # Auto-spawn polecat in rig
gt sling gt-abc greenplace --quality=shiny          # Use shiny workflow
gt sling gt-abc --args "patch release"              # With natural language args
gt sling mol-review --on gt-abc mayor               # Apply formula to existing work
gt sling gt-abc greenplace --naked                  # No-tmux mode (manual start)
gt sling gt-abc deacon/dogs --create                # Dispatch to dog pool
```

**Compare Related Commands:**
- `gt hook <bead>` - Just attach (no action)
- `gt sling <bead>` - Attach + start now (keep context)
- `gt handoff <bead>` - Attach + restart (fresh context)

---

### gt broadcast

Send a message to all workers.

**Syntax:**
```bash
gt broadcast <message> [flags]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--rig string` | Only broadcast to workers in this rig |
| `--all` | Include all agents (mayor, witness, etc.), not just workers |
| `--dry-run` | Show what would be sent without sending |

**Examples:**
```bash
gt broadcast "Check your mail"
gt broadcast --rig gastown "New priority work available"
gt broadcast --all "System maintenance in 5 minutes"
gt broadcast --dry-run "Test message"
```

**Common Use Cases:**
- Notifying workers of priority changes
- Announcing system maintenance
- Coordinating mass check-ins

---

### gt escalate

Escalate an issue to the human overseer.

**Syntax:**
```bash
gt escalate <topic> [flags]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `-s, --severity string` | Severity level: CRITICAL, HIGH, or MEDIUM (default: MEDIUM) |
| `-m, --message string` | Additional details about the escalation |
| `-n, --dry-run` | Show what would be done without executing |

**Severity Levels:**
| Level | Priority | Description |
|-------|----------|-------------|
| CRITICAL | P0 | System-threatening, immediate attention required |
| HIGH | P1 | Important blocker, needs human soon |
| MEDIUM | P2 | Standard escalation, human attention at convenience |

**Examples:**
```bash
gt escalate "Database migration failed"
gt escalate -s CRITICAL "Data corruption detected in user table"
gt escalate -s HIGH "Merge conflict cannot be resolved automatically"
gt escalate -s MEDIUM "Need clarification on API design" -m "Details here..."
```

**Common Use Cases:**
- Reporting blockers that require human decision
- Escalating security or data issues
- Requesting clarification on ambiguous requirements

---

### gt swarm

**DEPRECATED**: Use `gt convoy` instead.

Create swarm work units (legacy command).

**Syntax:**
```bash
gt swarm [flags]
```

**Note:** This command is deprecated. All swarm functionality has been migrated to the `gt convoy` command. Please use `gt convoy` for all new work.

---

## Worker Management Commands

### gt polecat

Manage polecat (transient worker) agents. Aliases: `cat`, `polecats`.

**Syntax:**
```bash
gt polecat <subcommand> [flags]
```

**Subcommands:**
| Subcommand | Description |
|------------|-------------|
| `list [rig]` | List polecats in a rig or all rigs |
| `add <rig> <name>` | Create a new polecat |
| `remove <rig/polecat>` | Remove polecat(s) |
| `status <rig/polecat>` | Show detailed polecat status |
| `sync <rig/polecat>` | Sync beads for polecat worktree |
| `done <rig/polecat>` | Mark polecat as done with work |
| `reset <rig/polecat>` | Force reset polecat to idle state |
| `gc <rig>` | Garbage collect stale polecat branches |
| `nuke <rig/polecat>` | Completely destroy polecat (session, worktree, branch, bead) |
| `git-state <rig/polecat>` | Show git state for pre-kill verification |
| `check-recovery <rig/polecat>` | Check if polecat needs recovery vs safe to nuke |

**Flags for `polecat list`:**
| Flag | Description |
|------|-------------|
| `--all` | List polecats in all rigs |
| `--json` | Output as JSON |

**Flags for `polecat remove`:**
| Flag | Description |
|------|-------------|
| `-f, --force` | Force removal, bypassing checks |
| `--all` | Remove all polecats in the rig |

**Flags for `polecat sync`:**
| Flag | Description |
|------|-------------|
| `--all` | Sync all polecats in the rig |
| `--from-main` | Pull only, no push |

**Flags for `polecat gc`:**
| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would be deleted without deleting |

**Flags for `polecat nuke`:**
| Flag | Description |
|------|-------------|
| `--all` | Nuke all polecats in the rig |
| `--dry-run` | Show what would be nuked without doing it |
| `-f, --force` | Force nuke, bypassing all safety checks (LOSES WORK) |

**Flags for `polecat status`, `git-state`, `check-recovery`:**
| Flag | Description |
|------|-------------|
| `--json` | Output as JSON |

**Examples:**
```bash
gt polecat list greenplace            # List polecats in rig
gt polecat list --all                 # List across all rigs
gt polecat add greenplace Toast       # Create polecat Toast in greenplace
gt polecat remove greenplace/Toast    # Remove single polecat
gt polecat remove greenplace --all    # Remove all polecats in rig
gt polecat status greenplace/Toast    # Show detailed status
gt polecat sync greenplace/Toast      # Sync beads for polecat
gt polecat gc greenplace --dry-run    # Preview branch cleanup
gt polecat nuke greenplace/Toast      # Nuclear cleanup (post-merge)
gt polecat nuke greenplace --all      # Nuke all polecats
```

**Common Use Cases:**
- Spawning workers for parallel tasks
- Cleaning up after convoy completion
- Inspecting worker status
- Post-merge cleanup with nuke

---

### gt crew

Manage crew (user-managed persistent workspaces within a rig).

Unlike polecats which are witness-managed and transient, crew workers are:
- **Persistent**: Not auto-garbage-collected
- **User-managed**: Overseer controls lifecycle
- **Long-lived identities**: Recognizable names like dave, emma, fred
- **Gas Town integrated**: Mail, handoff mechanics work
- **Tmux optional**: Can work in terminal directly

**Syntax:**
```bash
gt crew <subcommand> [flags]
```

**Subcommands:**
| Subcommand | Description |
|------------|-------------|
| `list` | List crew workspaces with status |
| `add <name...>` | Create new crew workspace(s) |
| `at [name]` | Attach to crew workspace session (alias: `attach`) |
| `remove <name...>` | Remove crew workspace(s) |
| `refresh <name>` | Context cycling with mail-to-self handoff |
| `restart [name...]` | Kill and restart session fresh (alias: `rs`) |
| `status [name]` | Show detailed workspace status |
| `rename <old> <new>` | Rename a crew workspace |
| `pristine [name]` | Sync crew workspaces with remote |
| `start [name...]` | Start crew workspace(s), creates if needed |
| `next` | Switch to next crew session in same rig |
| `prev` | Switch to previous crew session in same rig |

**Flags for `crew list`:**
| Flag | Description |
|------|-------------|
| `--rig string` | Filter by rig name |
| `--json` | Output as JSON |

**Flags for `crew add`:**
| Flag | Description |
|------|-------------|
| `--rig string` | Rig to create crew workspace in |
| `--branch` | Create a feature branch (crew/<name>) |

**Flags for `crew at`:**
| Flag | Description |
|------|-------------|
| `--rig string` | Rig to use |
| `--no-tmux` | Just print directory path |
| `-d, --detached` | Start session without attaching |
| `--account string` | Claude Code account handle to use |

**Flags for `crew remove`:**
| Flag | Description |
|------|-------------|
| `--rig string` | Rig to use |
| `--force` | Force remove (skip safety checks) |

**Flags for `crew restart`:**
| Flag | Description |
|------|-------------|
| `--rig string` | Rig to use (filter when using --all) |
| `--all` | Restart all running crew sessions |
| `--dry-run` | Show what would be restarted without restarting |

**Flags for `crew start`:**
| Flag | Description |
|------|-------------|
| `--rig string` | Rig to use |
| `--account string` | Claude Code account handle to use |

**Examples:**
```bash
gt crew list                          # List crew workers
gt crew add dave                      # Create crew worker 'dave'
gt crew add murgen croaker goblin     # Create multiple at once
gt crew at dave                       # Attach to dave's session
gt crew at dave --detached            # Start session without attaching
gt crew remove dave                   # Remove crew worker
gt crew status dave                   # Show detailed status
gt crew refresh dave -m "Working on gt-123"   # Cycle with handoff
gt crew restart dave                  # Kill and restart fresh
gt crew restart --all                 # Restart all crew sessions
gt crew pristine dave                 # Sync workspace with remote
gt crew start joe                     # Start joe (creates if needed)
gt crew next                          # Cycle to next worker
gt crew prev                          # Cycle to previous
```

**Common Use Cases:**
- Setting up long-running development agents
- Managing personal AI assistants per rig
- Switching between crew workers

---

### gt dog

Manage dogs (Deacon's helper workers for infrastructure tasks).

Dogs are reusable helper workers managed by the Deacon for infrastructure and cleanup tasks. Unlike polecats (single-rig, ephemeral), dogs handle cross-rig infrastructure work with worktrees into each rig.

**Syntax:**
```bash
gt dog <subcommand> [flags]
```

**Subcommands:**
| Subcommand | Description |
|------------|-------------|
| `list` | List all dogs in the kennel |
| `add <name>` | Create a new dog in the kennel |
| `remove <name>...` | Remove dogs from the kennel |
| `call [name]` | Wake idle dog(s) for work |
| `status [name]` | Show detailed dog status |

**Flags for `dog list`:**
| Flag | Description |
|------|-------------|
| `--json` | Output as JSON |

**Flags for `dog remove`:**
| Flag | Description |
|------|-------------|
| `-f, --force` | Force removal even if working |
| `--all` | Remove all dogs |

**Flags for `dog call`:**
| Flag | Description |
|------|-------------|
| `--all` | Wake all idle dogs |

**Flags for `dog status`:**
| Flag | Description |
|------|-------------|
| `--json` | Output as JSON |

**Examples:**
```bash
gt dog list                           # List all dogs
gt dog add alpha                      # Create dog 'alpha'
gt dog add bravo                      # Create dog 'bravo'
gt dog call alpha                     # Wake specific dog
gt dog call --all                     # Wake all idle dogs
gt dog call                           # Wake one idle dog
gt dog status alpha                   # Show dog status
gt dog status                         # Show pack summary
gt dog remove alpha                   # Remove dog
gt dog remove alpha bravo             # Remove multiple
gt dog remove --all                   # Remove all dogs
gt dog remove alpha --force           # Force remove working dog
```

**Common Use Cases:**
- Cross-rig infrastructure tasks
- Cleanup and maintenance operations
- Deacon-managed background work

---

## Merge Queue Commands

### gt mq

Manage the merge queue (refined work integration).

**Syntax:**
```bash
gt mq [subcommand] [flags]
```

**Subcommands:**
| Subcommand | Description |
|------------|-------------|
| `list` | List items in merge queue |
| `add <branch>` | Add a branch to the queue |
| `next` | Process next item in queue |
| `status` | Show queue status |
| `clear` | Clear the queue |

**Flags for `mq list`:**
| Flag | Description |
|------|-------------|
| `--rig string` | Target rig |
| `--json` | Output as JSON |
| `--all` | Show all statuses |

**Examples:**
```bash
gt mq list                            # List queue items
gt mq add feature/my-branch           # Add to queue
gt mq next                            # Process next item
gt mq status                          # Show queue status
gt mq clear                           # Clear the queue
```

---

### gt refinery

Manage refinery (merge processor) agents.

**Syntax:**
```bash
gt refinery <subcommand> [flags]
```

**Subcommands:**
| Subcommand | Description |
|------------|-------------|
| `status` | Show refinery status |
| `start` | Start the refinery |
| `stop` | Stop the refinery |
| `unclaimed` | Show unclaimed branches ready for processing |
| `queue` | Show the merge queue |

**Flags for `refinery unclaimed`:**
| Flag | Description |
|------|-------------|
| `--rig string` | Target rig |
| `--json` | Output as JSON |

**Examples:**
```bash
gt refinery status                    # Show status
gt refinery start                     # Start refinery
gt refinery stop                      # Stop refinery
gt refinery unclaimed                 # List unclaimed work
gt refinery queue                     # Show merge queue
```

**Common Use Cases:**
- Monitoring merge progress
- Checking for stalled merges
- Managing refinery lifecycle

---

## Workspace Commands

### gt init

Initialize a new Gas Town workspace.

**Syntax:**
```bash
gt init [flags]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--name string` | Town name (default: directory name) |
| `--path string` | Path to create workspace (default: ~/gt) |
| `--force` | Overwrite existing workspace |

**Examples:**
```bash
gt init                               # Initialize in ~/gt
gt init --name mytown                 # Custom name
gt init --path /custom/path           # Custom location
```

---

### gt rig

Manage rigs (isolated project workspaces).

**Syntax:**
```bash
gt rig <subcommand> [flags]
```

**Subcommands:**
| Subcommand | Description |
|------------|-------------|
| `list` | List all rigs |
| `add <name>` | Add a new rig |
| `remove <name>` | Remove a rig |
| `show <name>` | Show rig details |

**Flags for `rig add`:**
| Flag | Description |
|------|-------------|
| `--repo string` | Git repository URL |
| `--branch string` | Default branch (default: main) |
| `--prefix string` | Beads prefix for the rig |

**Examples:**
```bash
gt rig list                           # List all rigs
gt rig add myproject --repo git@github.com:user/repo.git
gt rig show gastown                   # Show rig details
gt rig remove oldproject              # Remove a rig
```

---

### gt worktree

Create worktrees in other rigs for cross-rig work.

**Syntax:**
```bash
gt worktree <rig> [flags]
gt worktree list
gt worktree remove <rig>
```

**Subcommands:**
| Subcommand | Description |
|------------|-------------|
| `list` | List all cross-rig worktrees owned by current crew member |
| `remove <rig>` | Remove a cross-rig worktree |

**Flags:**
| Flag | Description |
|------|-------------|
| `--no-cd` | Just print path (don't print cd command) |
| `-f, --force` | Force remove even with uncommitted changes (for remove) |

**Examples:**
```bash
gt worktree beads                     # Create worktree in beads rig
gt worktree gastown                   # Create worktree in gastown rig
gt worktree beads --no-cd             # Just print the path
gt worktree list                      # List your worktrees
gt worktree remove beads              # Remove beads worktree
gt worktree remove beads --force      # Force remove
```

**Common Use Cases:**
- Working on multiple rigs from a single identity
- Cross-rig dependency work
- Collaborative fixes across projects

---

## Communication Commands

### gt mail

Internal mail system for agent communication.

**Syntax:**
```bash
gt mail <subcommand> [flags]
```

**Subcommands:**
| Subcommand | Description |
|------------|-------------|
| `inbox` | Show inbox for current identity |
| `send` | Send a message |
| `read <id>` | Read a specific message |
| `check` | Check for new mail |
| `reply <id>` | Reply to a message |
| `archive <id>` | Archive a message |

**Flags for `mail inbox`:**
| Flag | Description |
|------|-------------|
| `--identity string` | Override identity |
| `--unread` | Show only unread messages |
| `--json` | Output as JSON |

**Flags for `mail send`:**
| Flag | Description |
|------|-------------|
| `--to string` | Recipient |
| `--subject string` | Subject line |
| `--body string` | Message body |
| `--priority string` | Priority (low, normal, high, urgent) |

**Examples:**
```bash
gt mail inbox                         # Check inbox
gt mail inbox --identity mayor        # Check Mayor's inbox
gt mail send --to mayor --subject "Update" --body "Work complete"
gt mail read msg-abc123               # Read message
gt mail reply msg-abc123              # Reply to message
gt mail check --inject                # Check and inject mail into context
```

---

### gt handoff

Hand off to a fresh session. Work continues from hook. The canonical way to end any agent session.

Handles all roles:
- Mayor, Crew, Witness, Refinery, Deacon: Respawns with fresh Claude instance
- Polecats: Calls `gt done --exit DEFERRED` (Witness handles lifecycle)

**Syntax:**
```bash
gt handoff [bead-or-role] [flags]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `-w, --watch` | Switch to new session (for remote handoff, default: true) |
| `-n, --dry-run` | Show what would be done without executing |
| `-s, --subject string` | Subject for handoff mail (optional) |
| `-m, --message string` | Message body for handoff mail (optional) |
| `-c, --collect` | Auto-collect state (status, inbox, beads) into handoff message |

**Examples:**
```bash
gt handoff                            # Hand off current session
gt handoff gt-abc                     # Hook bead, then restart
gt handoff gt-abc -s "Fix it"         # Hook with context, then restart
gt handoff -s "Context" -m "Notes"    # Hand off with custom message
gt handoff -c                         # Collect state into handoff message
gt handoff crew                       # Hand off crew session
gt handoff mayor                      # Hand off mayor session
```

**Note:** Any molecule on the hook will be auto-continued by the new session. The SessionStart hook runs `gt prime` to restore context.

---

### gt hook

Show or attach work on your hook.

The hook is the "durability primitive" - work on your hook survives session restarts, context compaction, and handoffs. When you restart (via gt handoff), your SessionStart hook finds the attached work and you continue from where you left off.

**Syntax:**
```bash
gt hook [bead-id] [flags]
```

**Subcommands:**
| Subcommand | Description |
|------------|-------------|
| (none) | Show what's on my hook |
| `status [target]` | Show what's slung on your hook |
| `show <agent>` | Show what's on an agent's hook (compact format) |

**Flags:**
| Flag | Description |
|------|-------------|
| `-s, --subject string` | Subject for handoff mail (optional) |
| `-m, --message string` | Message for handoff mail (optional) |
| `-n, --dry-run` | Show what would be done |
| `-f, --force` | Replace existing incomplete hooked bead |
| `--json` | Output as JSON (for status) |

**Examples:**
```bash
gt hook                               # Show what's on my hook
gt hook status                        # Same as above
gt hook gt-abc                        # Attach issue gt-abc to your hook
gt hook gt-abc -s "Fix the bug"       # With subject for handoff mail
gt hook show greenplace/polecats/nux  # What's nux working on?
gt hook show mayor                    # What's the mayor working on?
```

**Related commands:**
- `gt sling <bead>` - Hook + start now (keep context)
- `gt handoff <bead>` - Hook + restart (fresh context)
- `gt unsling` - Remove work from hook

---

## Diagnostic Commands

### gt seance

Talk to predecessor sessions. Resume and query previous agent sessions.

**Syntax:**
```bash
gt seance [flags]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--role string` | Filter by role (crew, polecat, witness, etc.) |
| `--rig string` | Filter by rig name |
| `-n, --recent int` | Number of recent sessions to show (default: 20) |
| `-t, --talk string` | Session ID to commune with |
| `-p, --prompt string` | One-shot prompt (with --talk) |
| `--json` | Output as JSON |

**Examples:**
```bash
gt seance                               # List recent sessions
gt seance --role crew                   # Filter by role
gt seance --rig gastown                 # Filter by rig
gt seance --recent 10                   # Last 10 sessions
gt seance --talk abc123                 # Talk to predecessor
gt seance --talk abc123 -p "Where is X?"  # One-shot question
```

**Common Use Cases:**
- Understanding predecessor decisions
- Finding where work was left off
- Debugging issues from previous sessions

---

### gt feed

Show real-time activity feed from beads and gt events.

**Syntax:**
```bash
gt feed [flags]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `-f, --follow` | Stream events in real-time |
| `--no-follow` | Show events once and exit |
| `-n, --limit int` | Maximum number of events (default: 100) |
| `--since string` | Show events since duration (e.g., 5m, 1h) |
| `--mol string` | Filter by molecule/issue ID prefix |
| `--type string` | Filter by event type |
| `--rig string` | Run from specific rig's beads directory |
| `-w, --window` | Open in dedicated tmux window |
| `--plain` | Use plain text output instead of TUI |

**Examples:**
```bash
gt feed                    # Launch TUI dashboard
gt feed --plain            # Plain text output
gt feed --window           # Open in dedicated tmux window
gt feed --since 1h         # Events from last hour
gt feed --rig gastown      # Use gastown rig's beads
gt feed --follow           # Real-time stream
```

**Common Use Cases:**
- Monitoring agent activity in real-time
- Watching merge queue progress
- Debugging issue state changes

---

### gt unsling

Remove work from an agent's hook (inverse of sling).

**Syntax:**
```bash
gt unsling [bead-id] [target]
```

**Aliases:** `unhook`

**Flags:**
| Flag | Description |
|------|-------------|
| `-n, --dry-run` | Show what would be done |
| `-f, --force` | Unsling even if work is incomplete |

**Arguments:**
- With no arguments: clears your own hook
- With bead ID only: only unslings if that specific bead is hooked
- With target only: operates on another agent's hook
- With both: unslings specific bead from specific agent

**Examples:**
```bash
gt unsling                          # Clear my hook
gt unsling gt-abc                   # Only unsling if gt-abc is hooked
gt unsling gastown/joe              # Clear joe's hook
gt unsling gt-abc gastown/joe       # Unsling gt-abc from joe
gt unsling --dry-run                # Preview action
gt unsling --force                  # Unsling incomplete work
```

**Common Use Cases:**
- Reassigning work from one agent to another
- Clearing stuck hooks
- Cleaning up after aborted work

---

### gt status

Show overall Gas Town status.

**Syntax:**
```bash
gt status [flags]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--json` | Output as JSON |
| `--watch` | Continuous status updates |
| `--rig string` | Focus on specific rig |

**Examples:**
```bash
gt status                             # Full status
gt status --json                      # JSON output
gt status --rig gastown               # Focus on rig
gt status --watch                     # Live updates
```

---

### gt prime

Output role context for current directory (used in agent initialization).

**Syntax:**
```bash
gt prime
```

**Role Detection:**
- Town root, mayor/, or `<rig>/mayor/` -> Mayor context
- `<rig>/witness/rig/` -> Witness context
- `<rig>/refinery/rig/` -> Refinery context
- `<rig>/polecats/<name>/` -> Polecat context
- `<rig>/crew/<name>/` -> Crew context
- deacon/ -> Deacon context

**Examples:**
```bash
gt prime                              # Output role context
```

**Common Use Cases:**
- Agent initialization on startup
- Role detection for scripts
- Context injection for Claude Code

---

### gt whoami

Show current identity for mail commands.

**Syntax:**
```bash
gt whoami
```

**Identity Detection:**
1. GT_ROLE env var (if set) - indicates an agent session
2. No GT_ROLE - you are the overseer (human)

**Examples:**
```bash
gt whoami                             # Show current identity
```

**Output includes:**
- Identity string
- Source of identity (GT_ROLE, cwd, etc.)
- Additional env vars (GT_RIG, GT_POLECAT, GT_CREW)

---

### gt version

Print version information.

**Syntax:**
```bash
gt version
```

**Output:**
```
gt version 0.1.1 (dev: main@abc123def)
```

---

### gt witness

Manage witness (polecat supervisor) agents.

**Syntax:**
```bash
gt witness [subcommand] [flags]
```

**Subcommands:**
| Subcommand | Description |
|------------|-------------|
| `status` | Show witness status |
| `patrol` | Run patrol cycle |
| `survey` | Survey all polecats |

**Examples:**
```bash
gt witness status                     # Show status
gt witness patrol                     # Run patrol
gt witness survey                     # Survey polecats
```

---

### gt done

Signal work ready for merge queue. A convenience command for polecats that:
1. Submits the current branch to the merge queue
2. Auto-detects issue ID from branch name
3. Notifies the Witness with the exit outcome

**Exit types:**
| Exit Type | Description |
|-----------|-------------|
| `COMPLETED` | Work done, MR submitted (default) |
| `ESCALATED` | Hit blocker, needs human intervention |
| `DEFERRED` | Work paused, issue still open |

**Syntax:**
```bash
gt done [flags]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--issue string` | Source issue ID (default: parse from branch name) |
| `-p, --priority int` | Override priority (0-4, default: inherit from issue) |
| `--exit string` | Exit type: COMPLETED, ESCALATED, or DEFERRED |

**Examples:**
```bash
gt done                               # Submit branch, notify COMPLETED
gt done --issue gt-abc                # Explicit issue ID
gt done --exit ESCALATED              # Signal blocker, skip MR
gt done --exit DEFERRED               # Pause work, skip MR
gt done --priority 1                  # Override priority
```

**Note:** This command requires the branch to be pushed. Run `git push -u origin <branch>` first.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GT_ROLE` | Agent role (mayor, witness, polecat, crew, etc.) |
| `GT_RIG` | Current rig name |
| `GT_POLECAT` | Polecat name (for polecat role) |
| `GT_CREW` | Crew worker name (for crew role) |
| `BD_ACTOR` | Actor identity for beads operations |

---

## Session Management

Gas Town uses tmux sessions for agent management:

| Session Pattern | Description |
|-----------------|-------------|
| `gt-mayor` | Mayor session |
| `gt-deacon` | Deacon session |
| `gt-<rig>-witness` | Witness for rig |
| `gt-<rig>-refinery` | Refinery for rig |
| `gt-<rig>-polecat-<name>` | Polecat session |
| `gt-<rig>-crew-<name>` | Crew session |

---

## Quick Reference

### Starting Work
```bash
gt up                    # Start all services
gt status                # Check everything is running
gt crew start max        # Start your crew worker
```

### Dispatching Work
```bash
gt sling crew/max gt-issue-123       # Assign work
gt convoy create -i                   # Create parallel convoy
gt broadcast "Check mail"             # Notify all workers
```

### Monitoring
```bash
gt status                # Overall status
gt polecat list          # List workers
gt mq list               # Check merge queue
gt mail inbox            # Check messages
```

### Cleanup
```bash
gt polecat gc            # Clean up idle polecats
gt down                  # Shutdown infrastructure
gt stop --all            # Emergency stop all polecats
```
