# Gas Town Concepts Reference

**Internal Reference for Claude Code** - Domain knowledge for understanding Gas Town systems.

Comprehensive reference for all Gas Town roles, systems, and protocols.

---

## 1. Town (Workspace)

The **Town** is your Gas Town workspace - the root directory containing all rigs, agents, and shared state.

```
~/gt/                           Town root
├── .beads/                     Town-level beads (hq-* prefix, mail)
├── mayor/                      Mayor config and state
│   └── town.json
├── deacon/                     Deacon daemon
│   └── dogs/                   Deacon helpers
│       └── boot/               Health triage dog
└── <rig>/                      Project containers (one per repo)
```

A town provides:
- **Unified namespace** for all projects and agents
- **Shared beads** for cross-rig communication
- **Consistent identity** via BD_ACTOR format
- **Single daemon** managing all agent lifecycles

---

## 2. Rigs (Projects)

A **Rig** is a container for a git project and its associated agents. Each rig has its own witness, refinery, crew, and polecats.

```
~/gt/<rig>/                     Project container
├── config.json                 Rig identity and settings
├── .beads/                     Rig-level beads (symlink or redirect)
├── .repo.git/                  Bare repo (shared by worktrees)
├── mayor/rig/                  Mayor's clone (canonical beads)
├── refinery/rig/               Worktree on main
├── witness/                    No clone (monitors only)
├── crew/                       Persistent human workspaces
│   ├── joe/                    Local crew member
│   └── beads-wolf/             Cross-rig worktree
└── polecats/                   Ephemeral worker worktrees
    └── Toast/                  Individual polecat
```

Create rigs with: `gt rig add <name> <git-url>`

---

## 3. Overseer (Human)

The **Overseer** is the human operator who owns and directs the Gas Town workspace. This is YOU.

### Overseer Responsibilities

| Area | What the Overseer Does |
|------|------------------------|
| **Strategy** | Sets priorities, defines what work matters |
| **Review** | Reviews agent output, approves merges |
| **Escalation** | Handles issues agents cannot resolve |
| **Configuration** | Configures rigs, formulas, notification preferences |
| **Ownership** | All work credits the overseer (via git author email) |

### What the Overseer Asks For (You Execute)

When the overseer wants to operate, they say things like:
- "fire up the engine" → you run `gt up`
- "shut it down" → you run `gt down`
- "check the status" → you run `gt status`
- "show me the dashboard" → you run `gt convoy list`

### Identity Model

Agents execute work, but the **overseer owns it**:

```
GIT_AUTHOR_NAME="gastown/polecats/toast"   # Agent (executor)
GIT_AUTHOR_EMAIL="you@example.com"          # Overseer (owner)
```

Work credits accumulate to the overseer's CV, not the ephemeral agent names.

---

## 4. Mayor (Coordinator)

The **Mayor** is the global coordinator at the town root. Singleton, persistent.

```
                    ╔═════════════════╗
                    ║     MAYOR       ║
                    ║  (town-level)   ║
                    ╚════════╤════════╝
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
       ╔═════════╗      ╔═════════╗      ╔═════════╗
       ║  Rig A  ║      ║  Rig B  ║      ║  Rig C  ║
       ╚═════════╝      ╚═════════╝      ╚═════════╝
```

### Mayor Responsibilities

- Cross-rig work dispatch and coordination
- Convoy management (tracking batched work)
- Escalation handling (tier 2)
- Town-wide status reporting

### Mayor Identity

```
BD_ACTOR = mayor
```

### Startup Check

On `gt prime`, Mayor checks for pending escalations:

```
## PENDING ESCALATIONS

There are 3 escalation(s) awaiting attention:

  CRITICAL: 1
  HIGH: 1
  MEDIUM: 1
```

---

## 5. Deacon (Daemon)

The **Deacon** is the background supervisor daemon. Singleton, persistent. Manages agent lifecycles and runs plugins.

```
                    ╔═════════════════╗
                    ║     DEACON      ║
                    ║   (daemon)      ║
                    ╚════════╤════════╝
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
      ╔═════════╗      ╔═════════════╗   ╔═════════╗
      ║  Boot   ║      ║  Lifecycle  ║   ║ Plugins ║
      ║  (dog)  ║      ║  Management ║   ║         ║
      ╚═════════╝      ╚═════════════╝   ╚═════════╝
```

### Deacon Responsibilities

- Spawning and terminating agents
- Health monitoring via Boot dog
- Plugin execution
- Second-order monitoring (receives WITNESS_PING)
- Escalation handling (tier 1)

### Deacon Commands

```bash
gt deacon start                   # Start the deacon
gt deacon stop                    # Stop the deacon
gt deacon status                  # Check deacon health
```

### Deacon Identity

```
BD_ACTOR = deacon
```

---

## 6. Dogs (Deacon Helpers)

**Dogs** are the Deacon's helpers for infrastructure tasks. They are NOT workers.

| Aspect | Dogs | Workers (Crew/Polecats) |
|--------|------|-------------------------|
| **Owner** | Deacon | Human / Witness |
| **Purpose** | Infrastructure tasks | Project work |
| **Scope** | Narrow, focused utilities | General purpose |
| **Lifecycle** | Very short (single task) | Long-lived / transient |

### Common Mistake

Dogs are NOT for user work. If you need to do project work, use Crew or Polecats.

---

## 7. Boot (Deacon Watchdog)

**Boot** is the Deacon's health triage dog. It runs on daemon tick to verify Deacon health.

```
Deacon tick
    │
    ▼
┌─────────┐
│  Boot   │  ─── "Is Deacon healthy?"
└────┬────┘
     │
     ├── Healthy ──▶ Continue
     │
     └── Unhealthy ──▶ Alert / Recovery
```

### Boot Location

```
~/gt/deacon/dogs/boot/
```

Future dogs might handle: log rotation, garbage collection, health checks.

---

## 8. Witness (Per-Rig Monitor)

The **Witness** is the per-rig polecat lifecycle manager. One per rig, persistent.

```
╔═══════════════════════════════════════════╗
║                 WITNESS                   ║
║              (gastown/witness)            ║
╚═══════════════════╤═══════════════════════╝
                    │
      ┌─────────────┼─────────────┐
      │             │             │
      ▼             ▼             ▼
╔══════════╗  ╔══════════╗  ╔══════════╗
║  Toast   ║  ║  Furiosa ║  ║   Nux    ║
║(polecat) ║  ║(polecat) ║  ║(polecat) ║
╚══════════╝  ╚══════════╝  ╚══════════╝
```

### Witness Responsibilities

- Monitor polecat health and progress
- Nudge stuck workers
- Trigger cleanup on completion
- Send MERGE_READY to Refinery
- Handle POLECAT_DONE messages
- Escalate lifecycle issues to Mayor

### Witness Identity

```
BD_ACTOR = <rig>/witness
Example:  gastown/witness
```

### Witness Commands

```bash
gt witness attach                 # Jump into witness session
gt peek <polecat>                 # Check polecat health
```

---

## 9. Refinery (Per-Rig Merger)

The **Refinery** is the per-rig merge queue processor. One per rig, persistent.

```
       MERGE_READY                      MERGED
Witness ──────────▶ ┌───────────┐ ──────────▶ Witness
                    │ REFINERY  │
                    │  (queue)  │
                    └─────┬─────┘
                          │
                    ┌─────┴─────┐
                    │  main     │
                    │ (branch)  │
                    └───────────┘
```

### Refinery Responsibilities

- Process merge queue
- Run tests and builds
- Merge to main branch
- Send MERGED / MERGE_FAILED / REWORK_REQUEST messages
- Handle merge conflicts (request rebase)

### Refinery Identity

```
BD_ACTOR = <rig>/refinery
Example:  gastown/refinery
```

### Merge Flow

```
Polecat                    Witness                    Refinery
   │                          │                          │
   │ POLECAT_DONE             │                          │
   │─────────────────────────▶│                          │
   │                          │                          │
   │                    (verify clean)                   │
   │                          │                          │
   │                          │ MERGE_READY              │
   │                          │─────────────────────────▶│
   │                          │                          │
   │                          │                    (merge attempt)
   │                          │                          │
   │                          │ MERGED (success)         │
   │                          │◀─────────────────────────│
   │                          │                          │
   │                    (nuke polecat)                   │
```

---

## 10. Polecats (Ephemeral Workers)

**Polecats** are ephemeral workers with their own worktrees. Transient, Witness-managed.

```
╔══════════════════════════════════════════════╗
║                 POLECAT                      ║
║         (gastown/polecats/toast)             ║
╠══════════════════════════════════════════════╣
║  Lifecycle: spawn ──▶ work ──▶ disappear     ║
║  Worktree:  ~/gt/gastown/polecats/toast/     ║
║  Branch:    feature-toast-xyz                ║
║  Hook:      Work assigned via gt sling       ║
╚══════════════════════════════════════════════╝
```

### Polecat Characteristics

| Aspect | Description |
|--------|-------------|
| **Lifecycle** | Transient (Witness controls) |
| **Monitoring** | Witness watches, nudges, recycles |
| **Work assignment** | Slung via `gt sling` |
| **Git state** | Works on branch, Refinery merges |
| **Cleanup** | Automatic on completion |
| **Identity** | `<rig>/polecats/<name>` |

### When to Use Polecats

- Discrete, well-defined tasks
- Batch work (tracked via convoys)
- Parallelizable work
- Work that benefits from supervision

### Multi-Polecat Coordination

When running multiple polecats on the same project, **sequence foundational work**:

```
✅ GOOD: Sequential foundation, parallel features
   Polecat 1: "Set up SvelteKit" (merged first)
   Polecat 2: "Add auth feature" (builds on #1)
   Polecat 3: "Add dashboard" (builds on #1)

❌ BAD: Parallel foundation work
   Polecat 1: "Set up SvelteKit"
   Polecat 2: "Set up SvelteKit"  ← Merge conflicts!
```

**Rule:** First polecat does foundational setup (package.json, build config, framework init). Subsequent polecats build on that foundation.

### Polecat Identity

```
BD_ACTOR = <rig>/polecats/<name>
Example:  gastown/polecats/toast
```

### Session Naming Convention

Tmux sessions follow the pattern: `gt-<rig>-<name>`

```
Examples:
  gt-cognition-furiosa     Polecat "furiosa" in cognition rig
  gt-cognition-witness     Witness agent for cognition rig
  gt-cognition-refinery    Refinery agent for cognition rig
```

**Don't guess session names.** Use `gt polecat list` or `tmux list-sessions` to see actual names.

### Polecat Commands

```bash
gt sling <bead> <rig>             # Assign work to polecat
gt polecat done                   # Signal work completion
gt done --exit MERGED             # Exit with merge
gt done --exit ESCALATED          # Exit with escalation
```

---

## 11. Crew (Persistent Human Workspaces)

**Crew** are persistent workers with their own clones. Long-lived, user-managed. This is the role for humans working alongside agents.

```
╔══════════════════════════════════════════════╗
║                   CREW                       ║
║           (gastown/crew/joe)                 ║
╠══════════════════════════════════════════════╣
║  Lifecycle: Persistent (user controls)       ║
║  Clone:     ~/gt/gastown/crew/joe/           ║
║  Branch:    main (pushes directly)           ║
║  Work:      Human-directed or self-assigned  ║
╚══════════════════════════════════════════════╝
```

### Crew vs Polecats

| Aspect | Crew | Polecat |
|--------|------|---------|
| **Lifecycle** | Persistent (user controls) | Transient (Witness controls) |
| **Monitoring** | None | Witness watches, nudges, recycles |
| **Work assignment** | Human-directed or self-assigned | Slung via `gt sling` |
| **Git state** | Pushes to main directly | Works on branch, Refinery merges |
| **Cleanup** | Manual | Automatic on completion |
| **Identity** | `<rig>/crew/<name>` | `<rig>/polecats/<name>` |

### When to Use Crew

- Exploratory work
- Long-running projects
- Work requiring human judgment
- Tasks where you want direct control
- Interactive sessions with the human

### Crew Identity

```
BD_ACTOR = <rig>/crew/<name>
Example:  gastown/crew/joe
```

### Cross-Rig Crew Work

When a crew member needs to work on another rig, create a worktree:

```bash
# gastown/crew/joe needs to fix a beads bug
gt worktree beads
# Creates ~/gt/beads/crew/gastown-joe/
# Identity preserved: BD_ACTOR = gastown/crew/joe
```

Directory structure for cross-rig work:
```
~/gt/beads/crew/gastown-joe/     # joe from gastown working on beads
~/gt/gastown/crew/beads-wolf/    # wolf from beads working on gastown
```

---

## 12. Beads (Memory System)

**Beads** is the git-backed issue tracker and memory system. All work state lives in beads.

```
╔═════════════════════════════════════════════════╗
║                    BEADS                        ║
║           (git-backed ledger)                   ║
╠═════════════════════════════════════════════════╣
║  Issues:     bd create, bd close, bd list       ║
║  Molecules:  bd mol pour, bd mol current        ║
║  Mail:       Routed through beads               ║
║  Persistence: Survives crashes, restarts        ║
╚═════════════════════════════════════════════════╝
```

### Beads Features

| Feature | Description |
|---------|-------------|
| **Issues** | Work items with status, tags, relations |
| **Molecules** | Multi-step workflow instances |
| **Mail** | Inter-agent communication |
| **Events** | Activity logging with attribution |
| **Sync** | Git-backed, survives restarts |

### Key Beads Commands

```bash
bd create "Fix bug"               # Create issue
bd list --status=open             # List open issues
bd show <id>                      # View issue details
bd close <id>                     # Close issue
bd ready                          # Show available work
bd mol current                    # Where am I in molecule?
```

### Beads Locations

```
~/gt/.beads/                      # Town-level beads (hq-* prefix)
~/gt/<rig>/.beads/                # Rig-level beads (symlink to mayor/rig/.beads)
```

---

## 13. Hooks (Work Attachment)

A **Hook** is where work hangs for an agent. When an agent wakes, it checks its hook and executes immediately.

```
╔═════════════════════════════════════════════════╗
║                   HOOK                          ║
╠═════════════════════════════════════════════════╣
║  "If you find something on your hook, RUN IT."  ║
╚═════════════════════════════════════════════════╝

Agent wakes ──▶ Check hook ──▶ Work found? ──▶ EXECUTE
                                   │
                                   └── No work ──▶ Check mail
```

### Hook Semantics

- The hook IS your assignment - it was placed there deliberately
- No waiting for confirmation
- Execute immediately without asking
- Other agents may be blocked waiting on YOUR output

### Hook Commands

```bash
gt hook                           # What's on my hook?
bd show <hook-id>                 # Details of hooked work
```

### Hook vs Pinned

| Concept | Meaning |
|---------|---------|
| **Hooked** | Work assigned to you - execute it |
| **Pinned** | Permanent reference beads - don't execute |

---

## 14. Convoys (Work Tracking)

A **Convoy** is how you track batched work across rigs. The primary dashboard for work visibility.

```
                 ┌─────────────────────────────┐
                 │  CONVOY (hq-cv-abc)         │
                 │  "Feature X"                │
                 └──────────────┬──────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
       ┌─────────┐         ┌─────────┐         ┌─────────┐
       │ gt-xyz  │         │ gt-def  │         │ bd-abc  │
       │ gastown │         │ gastown │         │  beads  │
       └────┬────┘         └────┬────┘         └────┬────┘
            │                   │                   │
            ▼                   ▼                   ▼
       ┌─────────┐         ┌─────────┐         ┌─────────┐
       │   nux   │         │ furiosa │         │  amber  │
       │(polecat)│         │(polecat)│         │(polecat)│
       └─────────┘         └─────────┘         └─────────┘
                                │
                           "the swarm"
                           (ephemeral)
```

### Convoy vs Swarm

| Concept | Persistent? | ID | Description |
|---------|-------------|-----|-------------|
| **Convoy** | Yes | hq-cv-* | Tracking unit. What you create, track, get notified about. |
| **Swarm** | No | None | Ephemeral. "The workers currently on this convoy's issues." |

### Convoy Lifecycle

```
OPEN ──(all issues close)──▶ LANDED/CLOSED
  ↑                              │
  └──(add more issues)───────────┘
       (auto-reopens)
```

### Convoy Commands

```bash
gt convoy create "Feature X" gt-abc gt-def --notify overseer
gt convoy status hq-cv-abc        # Check progress
gt convoy list                    # Dashboard of active convoys
gt convoy list --all              # Include landed convoys
```

### Why Convoys Matter

- Single view of "what's in flight"
- Cross-rig tracking (convoy in hq-*, issues in gt-*, bd-*)
- Auto-notification when work lands
- Historical record of completed work

---

## 15. Molecules (Workflows)

**Molecules** are workflow templates that coordinate multi-step work.

### Molecule Lifecycle (States of Matter)

```
Formula (source TOML) ─── "Ice-9"
    │
    ▼ bd cook
Protomolecule (frozen template) ─── Solid
    │
    ├──▶ bd mol pour ──▶ Mol (persistent) ─── Liquid ──▶ bd squash ──▶ Digest
    │
    └──▶ bd mol wisp ──▶ Wisp (ephemeral) ─── Vapor ──┬▶ bd squash ──▶ Digest
                                                      └▶ bd burn ──▶ (gone)
```

### Molecule Concepts

| Term | Phase | Description |
|------|-------|-------------|
| **Formula** | Ice-9 | Source TOML template defining workflow steps |
| **Protomolecule** | Solid | Frozen template ready for instantiation |
| **Molecule (Mol)** | Liquid | Active workflow instance with trackable steps |
| **Wisp** | Vapor | Ephemeral molecule for patrol cycles (never synced) |
| **Digest** | - | Squashed summary of completed molecule |

### Molecule Operators

| Operator | From --> To | Effect |
|----------|-------------|--------|
| `cook` | Formula --> Protomolecule | Expand macros, flatten |
| `pour` | Proto --> Mol | Instantiate as persistent |
| `wisp` | Proto --> Wisp | Instantiate as ephemeral |
| `squash` | Mol/Wisp --> Digest | Condense to permanent record |
| `burn` | Wisp --> (gone) | Discard without record |

### Navigating Molecules

```bash
bd mol current                    # Where am I?
bd mol current gt-abc             # Status of specific molecule
```

Output:
```
You're working on molecule gt-abc (Feature X)

  [x] gt-abc.1: Design
  [x] gt-abc.2: Scaffold
  [x] gt-abc.3: Implement
  --> gt-abc.4: Write tests [in_progress] <- YOU ARE HERE
  [ ] gt-abc.5: Documentation
  [ ] gt-abc.6: Exit decision

Progress: 3/6 steps complete
```

### Seamless Step Transitions

```bash
bd close gt-abc.3 --continue      # Close and advance to next step
```

This replaces the old 3-command workflow:
```bash
# OLD (friction):
bd close gt-abc.3
bd ready --parent=gt-abc
bd update gt-abc.4 --status=in_progress

# NEW (propulsion):
bd close gt-abc.3 --continue
```

---

## 16. GUPP (Gas Town Universal Propulsion Principle)

The **GUPP** is the core operating principle for all Gas Town agents.

```
╔═════════════════════════════════════════════════════════════╗
║                                                             ║
║   "If you find something on your hook, YOU RUN IT."         ║
║                                                             ║
╚═════════════════════════════════════════════════════════════╝
```

### Why GUPP Matters

Gas Town is a steam engine. Agents are pistons. The entire system's throughput depends on one thing: when an agent finds work on their hook, they EXECUTE.

- There is no supervisor polling asking "did you start yet?"
- The hook IS your assignment - it was placed there deliberately
- Every moment you wait is a moment the engine stalls
- Other agents may be blocked waiting on YOUR output

### The Handoff Contract

When you were spawned, work was hooked for you. The system trusts that:

1. You will find it on your hook
2. You will understand what it is (`bd show` / `gt hook`)
3. You will BEGIN IMMEDIATELY

### The Propulsion Loop

```
1. gt hook                   # What's hooked?
2. bd mol current            # Where am I?
3. Execute step
4. bd close <step> --continue # Close and advance
5. GOTO 2
```

### The Failure Mode GUPP Prevents

```
Polecat restarts with work on hook
  --> Polecat announces itself
  --> Polecat waits for confirmation
  --> Witness assumes work is progressing
  --> Nothing happens
  --> Gas Town stops
```

### Startup Behavior

1. Check hook (`gt hook`)
2. Work hooked --> EXECUTE immediately
3. Hook empty --> Check mail for attached work
4. Nothing anywhere --> ERROR: escalate to Witness

---

## 17. Mail Protocol (Message Types)

Gas Town agents coordinate via mail messages routed through the beads system.

### Message Types Summary

| Type | Route | Purpose |
|------|-------|---------|
| `POLECAT_DONE` | Polecat --> Witness | Signal work completion |
| `MERGE_READY` | Witness --> Refinery | Branch ready for merge |
| `MERGED` | Refinery --> Witness | Merge successful, safe to nuke |
| `MERGE_FAILED` | Refinery --> Witness | Merge failed (tests/build) |
| `REWORK_REQUEST` | Refinery --> Witness | Rebase needed (conflicts) |
| `WITNESS_PING` | Witness --> Deacon | Second-order monitoring |
| `HELP` | Any --> escalation target | Request intervention |
| `HANDOFF` | Agent --> self/successor | Session continuity |

### Mail Address Format

```
<rig>/<role>           # greenplace/witness
<rig>/<type>/<name>    # greenplace/polecats/nux
mayor                  # Town-level Mayor
deacon                 # Town-level Deacon
```

### Mail Commands

```bash
gt mail inbox                     # Check inbox
gt mail read <msg-id>             # Read specific message
gt mail ack <msg-id>              # Mark as read
gt mail send <addr> -s "Subject" -m "Body"
```

### Polecat Completion Flow

```
Polecat                    Witness                    Refinery
   │                          │                          │
   │ POLECAT_DONE             │                          │
   │─────────────────────────▶│                          │
   │                          │ MERGE_READY              │
   │                          │─────────────────────────▶│
   │                          │                          │
   │                          │                    (merge attempt)
   │                          │                          │
   │                          │ MERGED                   │
   │                          │◀─────────────────────────│
   │                          │                          │
   │                    (nuke polecat)                   │
```

### Second-Order Monitoring

```
Witness-1 ──┐
            │ WITNESS_PING
Witness-2 ──┼────────────────▶ Deacon
            │
Witness-N ──┘
                                 │
                          (if no response)
                                 │
            ◀────────────────────┘
            Escalate to Mayor
```

---

## 18. Agent Communication Flow

Agents communicate through two mechanisms: **mail** (async, persistent) and **nudge/peek** (direct, session-based).

### Communication Methods Compared

| Method | Type | Use Case | Persistence |
|--------|------|----------|-------------|
| **Mail** | Async | Formal notifications, handoffs, escalations | Git-backed, survives restarts |
| **Nudge** | Direct | Real-time session messages | Session lifetime only |
| **Peek** | Direct | Read session output | Session lifetime only |

### The Nudge/Peek Pattern

For real-time agent coordination, use `gt nudge` to send and `gt peek` to read:

```
Agent A                                              Agent B
   │                                                    │
   │  gt nudge <target> "Check issue gt-xyz"           │
   │───────────────────────────────────────────────────▶│
   │                                                    │
   │                                         (B sees message
   │                                          in tmux pane)
   │                                                    │
   │  gt peek <target>                                  │
   │◀───────────────────────────────────────────────────│
   │                                                    │
   │  (A reads B's output)                              │
```

### Nudge Target Formats

| Target | Session | Example |
|--------|---------|---------|
| `mayor` | gt-mayor | Town-level coordinator |
| `deacon` | gt-deacon | Background daemon |
| `witness` | gt-{rig}-witness | Rig monitor |
| `refinery` | gt-{rig}-refinery | Rig merger |
| `{rig}/{polecat}` | gt-{rig}-polecat-{name} | Worker |
| `channel:{name}` | All channel members | Broadcast |

### Mail Routing Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Town (.beads/)                   │
│  ┌─────────────────────────────────────────────┐   │
│  │                 Mayor Inbox                 │   │
│  │  └── mayor/                                 │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │           <rig>/ (rig mailboxes)            │   │
│  │  ├── witness      ← <rig>/witness           │   │
│  │  ├── refinery     ← <rig>/refinery          │   │
│  │  ├── <polecat>    ← <rig>/<polecat>         │   │
│  │  └── crew/<name>  ← <rig>/crew/<name>       │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Mail Address Formats

| Address | Recipient |
|---------|-----------|
| `mayor/` | Mayor inbox |
| `<rig>/witness` | Rig's Witness |
| `<rig>/refinery` | Rig's Refinery |
| `<rig>/<polecat>` | Polecat (e.g., greenplace/Toast) |
| `<rig>/crew/<name>` | Crew worker (e.g., greenplace/crew/max) |
| `--human` | Human overseer (special) |

### When to Use Each Method

**Use Mail for:**
- Formal notifications (POLECAT_DONE, MERGE_READY)
- Handoff messages (session continuity)
- Escalation requests
- Anything that must survive restarts

**Use Nudge for:**
- Quick "are you there?" checks
- Status queries
- Immediate attention requests
- Debugging/monitoring

### DND (Do Not Disturb)

Agents can enable DND to block nudges during focused work:

```bash
gt dnd on                         # Enable DND
gt dnd off                        # Disable DND
gt nudge <target> --force         # Override DND (use sparingly)
```

---

## 19. Gates (Async Coordination)

**Gates** are async checkpoints that block work until a condition is met. They enable agents to wait for external events without spinning.

### Gate Types

| Gate Type | Awaits | Example |
|-----------|--------|---------|
| `gh:run` | GitHub Actions run completion | CI pipeline |
| `gh:pr` | Pull request merge/close | PR review |
| `timer` | Time duration | Rate limiting |
| `human` | Human acknowledgment | Design approval |
| `mail` | Message arrival | Response from agent |

### Gate Lifecycle

```
       bd gate create
            │
            ▼
      ┌───────────┐
      │  PENDING  │ ◀─── Gate created, condition not met
      └─────┬─────┘
            │
            ▼ (condition met)
      ┌───────────┐
      │ SATISFIED │ ◀─── Gate resolved, work can continue
      └─────┬─────┘
            │
            ▼ (agent resumes)
      ┌───────────┐
      │  CLOSED   │ ◀─── Gate consumed
      └───────────┘
```

### The Park/Resume Pattern

Agents use `gt park` to save state and `gt resume` to continue after a gate resolves:

```
Polecat                              Gate                           External
   │                                   │                               │
   │ gt park --gate gh:run:12345       │                               │
   │──────────────────────────────────▶│                               │
   │                                   │                               │
   │ (polecat goes to sleep)           │                               │
   │                                   │                               │
   │                                   │  (CI completes)               │
   │                                   │◀──────────────────────────────│
   │                                   │                               │
   │                            (gate satisfied)                       │
   │                                   │                               │
   │ gt resume (or auto-resume)        │                               │
   │◀──────────────────────────────────│                               │
   │                                   │                               │
   │ (polecat continues)               │                               │
```

### Gate Commands

```bash
# Create a gate
bd gate create gh:run:12345 "Wait for CI"

# Park work on a gate
gt park --gate gh:pr:456 --message "Waiting for review"

# Check gate status
bd gate status <gate-id>

# Resume when gate satisfied
gt resume

# Check for handoff messages on resume
gt resume --check-handoff
```

### Handoff Messages

When parking, agents can leave handoff messages for their successor (or themselves after restart):

```bash
gt park --gate timer:1h --handoff "Remember to check test results first"
```

On resume:
```bash
gt resume
# Outputs: "Handoff message: Remember to check test results first"
```

### Why Gates Matter

Gates prevent the anti-pattern of busy-waiting:

```
❌ BAD: Busy-wait loop
   while ! check_ci_status; do
     sleep 60
   done

✅ GOOD: Gate-based wait
   gt park --gate gh:run:12345
   # Agent sleeps, system notifies on completion
   gt resume
```

Gates also:
- Track what work is blocked on what
- Enable the system to auto-resume work
- Provide audit trail of async coordination
- Let agents sleep without consuming resources

---

## 20. Escalation (How Agents Ask for Help)

The **Escalation Protocol** is how agents request intervention when automated resolution is not possible.

### Escalation Tiers

```
Worker encounters issue
    │
    ▼
gt escalate --type <category>
    │
    ▼
╔═════════════════════════════════════════════════════════════╗
║ TIER 1: DEACON                                              ║
║   Can resolve? --> Updates issue, re-slings work            ║
║   Cannot resolve? --> Forward to Mayor                      ║
╚═════════════════════════════════════════════════════════════╝
    │
    ▼
╔═════════════════════════════════════════════════════════════╗
║ TIER 2: MAYOR                                               ║
║   Can resolve? --> Updates issue, re-slings work            ║
║   Cannot resolve? --> Forward to Overseer                   ║
╚═════════════════════════════════════════════════════════════╝
    │
    ▼
╔═════════════════════════════════════════════════════════════╗
║ TIER 3: OVERSEER (Human)                                    ║
║   Final resolution                                          ║
╚═════════════════════════════════════════════════════════════╝
```

### Severity Levels

| Level | Priority | Description | Examples |
|-------|----------|-------------|----------|
| **CRITICAL** | P0 | System-threatening, immediate | Data corruption, security breach |
| **HIGH** | P1 | Important blocker, needs human soon | Unresolvable merge conflict |
| **MEDIUM** | P2 | Standard escalation | Design decision needed |

### Escalation Categories

| Category | Description | Default Route |
|----------|-------------|---------------|
| `decision` | Multiple valid paths, need choice | Deacon --> Mayor |
| `help` | Need guidance or expertise | Deacon --> Mayor |
| `blocked` | Waiting on unresolvable dependency | Mayor |
| `failed` | Unexpected error, can't proceed | Deacon |
| `emergency` | Security or data integrity issue | Overseer (direct) |
| `gate_timeout` | Gate didn't resolve in time | Deacon |
| `lifecycle` | Worker stuck or needs recycle | Witness |

### Escalation Commands

```bash
# Basic escalation
gt escalate "Database migration failed"

# With severity
gt escalate -s CRITICAL "Data corruption detected"

# With category
gt escalate --type decision "Which auth approach?"

# With explicit routing
gt escalate --to mayor "Cross-rig coordination needed"
gt escalate --to overseer "Human judgment required"

# Forward from one tier to next
gt escalate --forward --to mayor "Deacon couldn't resolve"
```

### Structured Decision Pattern

```bash
gt escalate --type decision \
  --question "Which authentication approach?" \
  --options "JWT tokens,Session cookies,OAuth2" \
  --context "Admin panel needs login" \
  --issue bd-xyz
```

This updates the issue with a structured decision format that can be resolved asynchronously.

### When to Escalate

**SHOULD escalate:**
- System errors (database corruption, disk full)
- Security issues (unauthorized access, credential exposure)
- Unresolvable conflicts (merge conflicts)
- Ambiguous requirements (unclear spec)
- Design decisions (architectural choices)
- Stuck loops (no progress)
- Gate timeouts

**Should NOT escalate:**
- Normal workflow that can proceed
- Recoverable/transient errors
- Information queries answerable from context

---

## Role Hierarchy Summary

```
                           ┌──────────────┐
                           │   OVERSEER   │  (Human - YOU)
                           │   (owner)    │
                           └──────┬───────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
        ┌───────────┐       ┌───────────┐       ┌───────────┐
        │   MAYOR   │       │  DEACON   │       │   CREW    │
        │ (coord)   │       │ (daemon)  │       │ (human    │
        └─────┬─────┘       └─────┬─────┘       │  workers) │
              │                   │             └───────────┘
              │                   │
              │             ┌─────┴─────┐
              │             │   DOGS    │
              │             │  (Boot)   │
              │             └───────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────┐       ┌─────────┐
│  RIG A  │       │  RIG B  │
└────┬────┘       └────┬────┘
     │                 │
  ┌──┴──┐           ┌──┴──┐
  │     │           │     │
  ▼     ▼           ▼     ▼
┌────┐ ┌────┐    ┌────┐ ┌────┐
│WITN│ │REF │    │WITN│ │REF │
│ESS │ │INE │    │ESS │ │INE │
└──┬─┘ └────┘    └──┬─┘ └────┘
   │                │
   ▼                ▼
┌──────────┐    ┌──────────┐
│ POLECATS │    │ POLECATS │
│(workers) │    │(workers) │
└──────────┘    └──────────┘
```

---

## Quick Reference: Identity Formats

| Role | BD_ACTOR Format | Example |
|------|-----------------|---------|
| Mayor | `mayor` | `mayor` |
| Deacon | `deacon` | `deacon` |
| Witness | `{rig}/witness` | `gastown/witness` |
| Refinery | `{rig}/refinery` | `gastown/refinery` |
| Crew | `{rig}/crew/{name}` | `gastown/crew/joe` |
| Polecat | `{rig}/polecats/{name}` | `gastown/polecats/toast` |

---

## Quick Reference: Commands You Run

### When Overseer Asks To Operate

| User Says | You Run |
|-----------|---------|
| "fire up the engine" | `gt up` |
| "shut it down" | `gt down` |
| "check the status" | `gt status` |
| "show me the dashboard" | `gt convoy list` |
| "sling this work" | `gt sling <bead> <rig>` |

### Commands Agents Use Internally

These are used by worker agents (polecats, crew), not run by you directly:

```bash
gt hook                           # Check my hook
bd mol current                    # Where am I in workflow?
bd close <step> --continue        # Complete step, advance
gt mail inbox                     # Check messages
gt escalate --type <cat> "msg"    # Ask for help
gt handoff                        # Request session cycle
```
