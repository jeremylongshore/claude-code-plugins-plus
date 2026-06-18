# Gas Town Interactive Tutorial

**This is YOUR guide for running an interactive tutorial. Not a document for users.**

## How to Run This Tutorial

You lead the user through Gas Town step by step. Each section tells you:
- **SHOW**: What to display to the user
- **DO**: What commands to run (you run them)
- **ASK**: What AskUserQuestion to call next

### Golden Rules

1. **One thing at a time** - Don't overwhelm. Teach, confirm, move on.
2. **Actually do it** - Run real commands. Don't just explain.
3. **Always ask what's next** - Use AskUserQuestion between every section.
4. **Celebrate wins** - Use milestone boxes after each stage.
5. **Adapt** - If user wants to skip or explore, go with them.
6. **Visual first** - Lead with diagrams, follow with explanation.
7. **Verify understanding** - Occasionally ask learner to explain concepts back.
8. **Show progress** - Use the progress header on every major SHOW block.

### Progress Header Format

Use this header on major SHOW blocks to show where the learner is:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ⛽ STAGE 1: FOUNDATION                                    Lesson 1.3 [3/5] ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

This gives learners constant awareness of where they are in the journey.

### Dynamic Path Guidance

**If learner wants to skip ahead:**
- Show them the journey map, ask which stage interests them
- Jump to that stage, but note any prerequisites they missed

**If learner seems confused:**
- Pause and ask: "Want me to explain that differently?"
- Offer to re-show with a different example

**If learner wants to practice:**
- Create additional beads/convoys for hands-on work
- Don't rush to next lesson

**If learner asks "why?":**
- Always explain the reasoning, not just the what
- Connect to the bigger picture (GUPP, the cognition engine)

**Verify understanding occasionally:**
```json
{
  "questions": [{
    "question": "Quick check - can you explain what GUPP means?",
    "header": "Verify",
    "multiSelect": false,
    "options": [
      {"label": "It means...", "description": "I'll explain it back"},
      {"label": "Not quite sure", "description": "Please explain again"}
    ]
  }]
}
```

### Tutorial Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE JOURNEY MAP                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STAGE 1: FOUNDATION          Your first engine                            │
│  ════════════════════                                                       │
│  1.1 The Secret               SLING → HOOK → GUPP                          │
│  1.2 Installation             Get the tools                                │
│  1.3 Your First Rig           Hook up a project                            │
│  1.4 Your First Bead          Create work to track                         │
│  1.5 Your First Sling         Watch a polecat work                         │
│  🏆 MILESTONE: Engine Running!                                              │
│                                                                             │
│  STAGE 2: FLOW                Work moves through                           │
│  ═════════════════                                                          │
│  2.1 Meet the Cast            All the characters                           │
│  2.2 Convoys                  Batch your work                              │
│  2.3 Watching Workers         Peek, nudge, recover                         │
│  2.4 The Merge Pipeline       Refinery flow                                │
│  2.5 Mail & Communication     Inter-agent messaging                        │
│  🏆 MILESTONE: Work Flows!                                                  │
│                                                                             │
│  STAGE 3: MASTERY             Full control                                 │
│  ════════════════════                                                       │
│  3.1 Polecats vs Crew         When to use each                             │
│  3.2 Multi-Rig Work           Cross-project coordination                   │
│  3.3 Molecules                Multi-step workflows                         │
│  3.4 Escalation               When to ask for help                         │
│  3.5 Troubleshooting          gt doctor and recovery                       │
│  3.6 Gates                    Async coordination                           │
│  3.7 Park and Resume          Pause and continue work                      │
│  🏆 MILESTONE: Master Operator!                                             │
│                                                                             │
│  STAGE 4: EXPERT              Deep internals                               │
│  ═══════════════════                                                        │
│  4.1 Advanced Molecules       Pour, wisp, squash                           │
│  4.2 The Deacon               Infrastructure daemon                        │
│  4.3 Dogs                     Deacon's helpers                             │
│  4.4 Seance                   Talk to predecessors                         │
│  4.5 Custom Workflows         Build your own formulas                      │
│  🏆 MILESTONE: You ARE Gas Town.                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Starting the Tutorial

When user chooses tutorial, start here:

### SHOW:
```
Let's learn Gas Town together! ⛽

I'll guide you through building your own AI-powered software factory.
We'll go step by step - I'll do the work, you'll see it happen.

By the end, you'll have:
✓ A working Gas Town installation
✓ A project hooked up
✓ Work being tracked
✓ AI workers building for you

The journey has 4 stages. We'll start with the fundamentals.
```

### ASK:
```json
{
  "questions": [{
    "question": "Ready to begin?",
    "header": "Start",
    "multiSelect": false,
    "options": [
      {"label": "Let's go!", "description": "Start from the beginning"},
      {"label": "I have Gas Town installed", "description": "Skip to adding a project"},
      {"label": "Show me what's possible first", "description": "Preview the capabilities"}
    ]
  }]
}
```

---

# STAGE 1: FOUNDATION

## 1.1 The Secret

### SHOW:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ⛽ STAGE 1: FOUNDATION                                    Lesson 1.1 [1/5] ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

╔═══════════════════════════════════════════════════════════════════════════╗
║                              THE SECRET                                   ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║     YOU: "Fix the login bug"                                              ║
║           │                                                               ║
║           │  SLING ──────▶  Toss work to a worker                         ║
║           ▼                                                               ║
║        🦨 Polecat spawns                                                  ║
║           │                                                               ║
║           ▼                                                               ║
║       ┌────────┐                                                          ║
║       │  HOOK  │  ◀────────  Work hangs here (like a coat hook)           ║
║       │   🪝   │                                                          ║
║       └────────┘                                                          ║
║           │                                                               ║
║           ▼                                                               ║
║        GUPP: "If there's work on my hook, I RUN IT"                       ║
║           │                                                               ║
║           ▼                                                               ║
║        💨 Work gets done!                                                 ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

That's the whole system:

  SLING = toss work to a worker
  HOOK  = where work hangs
  GUPP  = "If there's work on my hook, I run it"

You sling. Work hooks. Workers run. The engine never stops.
```

### ASK:
```json
{
  "questions": [{
    "question": "Got it? Ready to install?",
    "header": "Next",
    "multiSelect": false,
    "options": [
      {"label": "Yes, install!", "description": "Let's get the tools"},
      {"label": "Tell me more", "description": "Explain SLING, HOOK, GUPP more"},
      {"label": "What's a polecat?", "description": "Explain the workers first"}
    ]
  }]
}
```

---

## 1.2 Installation

### SHOW:
```
Time to install Gas Town! ⚙️

Here's what we need:
┌──────────────────────────────────────────┐
│  gt   - Gas Town CLI (runs the engine)   │
│  bd   - Beads (tracks work)              │
└──────────────────────────────────────────┘

I'll check your system first, then install.
```

### DO:
1. Check prerequisites:
```bash
go version
git --version
```

2. If Go missing, help install it first.

3. Install the tools:
```bash
go install github.com/steveyegge/gastown/cmd/gt@latest
go install github.com/steveyegge/beads/cmd/bd@latest
```

4. Verify:
```bash
gt version
bd version
```

5. Initialize workspace:
```bash
gt install ~/gt
```

### SHOW (after success):
```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  ✓ INSTALLED!                                                             ║
║                                                                           ║
║  Your workshop is ready at ~/gt                                           ║
║                                                                           ║
║  ~/gt/                                                                    ║
║  ├── mayor/         (coordinator)                                         ║
║  └── .beads/        (work tracker)                                        ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### ASK:
```json
{
  "questions": [{
    "question": "Installed! Now let's hook up a project. Do you have a GitHub repo?",
    "header": "Project",
    "multiSelect": false,
    "options": [
      {"label": "Yes, I have a repo", "description": "I'll give you the URL"},
      {"label": "Create a test repo", "description": "Make a playground to learn with"},
      {"label": "Use an example repo", "description": "I'll provide one for practice"}
    ]
  }]
}
```

---

## 1.3 Your First Rig

### SHOW:
```
A RIG is a project container. Think of it as a workshop bay for one project.

    ╔═══════════════════════════════════════╗
    ║              YOUR RIG                 ║
    ╠═══════════════════════════════════════╣
    ║                                       ║
    ║  ~/gt/myproject/                      ║
    ║  ├── 🦅 witness/    (watches workers) ║
    ║  ├── 🦡 refinery/   (merges code)     ║
    ║  ├── 👷 crew/       (your helpers)    ║
    ║  └── 🦨 polecats/   (quick workers)   ║
    ║                                       ║
    ║  Each rig gets its own team.          ║
    ║                                       ║
    ╚═══════════════════════════════════════╝
```

### DO:
When user provides a GitHub URL:
```bash
gt rig add <name> <github-url>
```

**CRITICAL: Post-Rig Verification (DO ALL OF THESE):**
```bash
# 1. Confirm rig exists
gt rig list

# 2. Run BOTH health checks
gt doctor
bd doctor

# 3. Check for prefix routing (look for errors)
# If you see "prefix mismatch" or "routes.jsonl" errors → fix before continuing

# 4. Start the Refinery (REQUIRED for merge pipeline)
gt refinery start

# 5. Verify Refinery is running
gt refinery status
```

**BLOCKERS - Do not proceed if:**
- `gt doctor` shows critical errors
- `bd doctor` shows prefix mismatch errors
- Refinery failed to start

**If errors:** Run `gt doctor --fix` and retry.

### SHOW (after verification passes):
```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  ✓ RIG CREATED AND VERIFIED!                                              ║
║                                                                           ║
║  Project: <name>                                                          ║
║  Location: ~/gt/<name>/                                                   ║
║                                                                           ║
║  Verification complete:                                                   ║
║  • gt doctor: ✓ passed                                                    ║
║  • bd doctor: ✓ passed                                                    ║
║  • Refinery: ✓ running                                                    ║
║                                                                           ║
║  The team is ready to work.                                               ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### ASK:
```json
{
  "questions": [{
    "question": "Rig created! Ready to track some work?",
    "header": "Next",
    "multiSelect": false,
    "options": [
      {"label": "Create a bead", "description": "Track our first piece of work"},
      {"label": "Fire up the engine first", "description": "Start the infrastructure"},
      {"label": "What's a bead?", "description": "Explain work tracking"}
    ]
  }]
}
```

---

## 1.4 Your First Bead

### SHOW:
```
BEADS are work items. Like issues, but they survive crashes.

    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │   Every piece of work gets an ID:                       │
    │                                                         │
    │       mp-001  ──▶  "Fix login bug"                      │
    │       mp-002  ──▶  "Add dark mode"                      │
    │       mp-003  ──▶  "Update docs"                        │
    │                                                         │
    │   Beads are stored in git. If a worker crashes,         │
    │   the work survives. Another worker can pick it up.     │
    │                                                         │
    └─────────────────────────────────────────────────────────┘

Let's create your first bead!
```

### ASK:
```json
{
  "questions": [{
    "question": "What work should we track? (I'll create it for you)",
    "header": "Work",
    "multiSelect": false,
    "options": [
      {"label": "Fix a bug", "description": "I'll create 'Fix the login bug'"},
      {"label": "Add a feature", "description": "I'll create 'Add dark mode'"},
      {"label": "I'll describe it", "description": "Tell me what to create"}
    ]
  }]
}
```

### DO:
```bash
cd ~/gt/<rig>/mayor/rig
bd create --title "<title>"
bd list
```

### SHOW (after success):
```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  ✓ BEAD CREATED!                                                          ║
║                                                                           ║
║  ID: <prefix>-<id>                                                        ║
║  Title: <title>                                                           ║
║  Status: open                                                             ║
║                                                                           ║
║  This work is now tracked. Even if everything crashes,                    ║
║  this bead survives in git.                                               ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### ASK:
```json
{
  "questions": [{
    "question": "Now for the magic - let's sling this work to a polecat!",
    "header": "Sling",
    "multiSelect": false,
    "options": [
      {"label": "Sling it!", "description": "Toss this work to a worker"},
      {"label": "What happens when I sling?", "description": "Explain the flow first"}
    ]
  }]
}
```

---

## 1.5 Your First Sling

### SHOW:
```
This is the magic moment. Watch what happens:

    YOU: "sling <bead> to <rig>"
          │
          ▼
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │  1. A POLECAT spawns (new AI worker)                    │
    │  2. Work lands on its HOOK                              │
    │  3. GUPP kicks in: "Work on hook? RUN IT."              │
    │  4. Polecat starts working IMMEDIATELY                  │
    │                                                         │
    │  The Witness watches. If it gets stuck, I'll know.      │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
```

### DO:
First, start the infrastructure:
```bash
gt up
```

Then sling:
```bash
gt sling <bead-id> <rig>
```

Check status:
```bash
gt polecat list
gt status
```

### SHOW (after success):
```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  ✓ WORK SLUNG!                                                            ║
║                                                                           ║
║  A polecat named "<name>" spawned.                                        ║
║  Work is on their hook. They're working NOW.                              ║
║                                                                           ║
║  🦅 The Witness is watching.                                              ║
║  🦡 The Refinery is ready to merge when done.                             ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### SHOW (Stage 1 Complete):
```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                    🏆 STAGE 1 COMPLETE: FOUNDATION 🏆                     ║
║                                                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  You now have:                                                            ║
║                                                                           ║
║  ✓ Gas Town installed                                                     ║
║  ✓ A rig (project) hooked up                                              ║
║  ✓ Work being tracked in beads                                            ║
║  ✓ A polecat working on your first task                                   ║
║                                                                           ║
║  You understand:                                                          ║
║  • SLING = toss work to a worker                                          ║
║  • HOOK = where work hangs                                                ║
║  • GUPP = "If there's work on my hook, I run it"                          ║
║                                                                           ║
║  Your engine is RUNNING.                                                  ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

━━ ⛽ Gas Town | Learning ━━
```

### VERIFY (Optional - use if learner seems uncertain):
```json
{
  "questions": [{
    "question": "Quick check! What does GUPP stand for?",
    "header": "Verify",
    "multiSelect": false,
    "options": [
      {"label": "If there's work on my hook, I run it", "description": "The propulsion principle!"},
      {"label": "I'm not sure", "description": "Let me explain again"}
    ]
  }]
}
```

If they're not sure, re-explain:
```
GUPP = "Gas Town Universal Propulsion Principle"

It's the simple rule every worker follows:
   🪝 "If there's work on my hook, I RUN IT."

That's it. That's the whole engine. Work lands → workers run.
```

### ASK:
```json
{
  "questions": [{
    "question": "Stage 1 complete! What's next?",
    "header": "Continue",
    "multiSelect": false,
    "options": [
      {"label": "Stage 2: Flow", "description": "Learn how work moves through the system"},
      {"label": "Practice more", "description": "Create another bead and sling it"},
      {"label": "Check on my polecat", "description": "See how the work is going"},
      {"label": "Take a break", "description": "We can continue anytime"}
    ]
  }]
}
```

---

# STAGE 2: FLOW

## 2.1 Meet the Cast

### SHOW:
```
Time to meet everyone in your factory!

╔═══════════════════════════════════════════════════════════════════════════╗
║                           THE CAST                                        ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  👤 OVERSEER (You)                                                        ║
║  └── The boss. Sets priorities. Reviews output.                           ║
║                                                                           ║
║  🦊 MAYOR (Town Level)                                                    ║
║  └── Your assistant. Coordinates across all projects.                     ║
║                                                                           ║
║  ⚙️ DEACON (Background)                                                   ║
║  └── Keeps the infrastructure running. You rarely interact.               ║
║                                                                           ║
║  ───── Per Rig ─────                                                      ║
║                                                                           ║
║  🦅 WITNESS                                                               ║
║  └── Watches all polecats in this rig. Nudges stuck ones.                 ║
║                                                                           ║
║  🦡 REFINERY                                                              ║
║  └── Merges completed work to main. Quality control.                      ║
║                                                                           ║
║  🦨 POLECATS                                                              ║
║  └── Quick workers. Spawn, do one task, vanish.                           ║
║                                                                           ║
║  👷 CREW                                                                  ║
║  └── Persistent helpers. Stick around for ongoing work.                   ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### ASK:
```json
{
  "questions": [{
    "question": "Want to learn more about any character?",
    "header": "Learn",
    "multiSelect": false,
    "options": [
      {"label": "The Witness", "description": "How does it watch workers?"},
      {"label": "The Refinery", "description": "How does merging work?"},
      {"label": "Polecats vs Crew", "description": "When to use each?"},
      {"label": "Move on to Convoys", "description": "Learn batch work tracking"}
    ]
  }]
}
```

---

## 2.2 Convoys

### SHOW:
```
When you have multiple related tasks, use a CONVOY.

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                          CONVOY                                       ║
    ║                   "User Auth Feature"                                 ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║         ┌─────────┬─────────┬─────────┐                               ║
    ║         │ mp-001  │ mp-002  │ mp-003  │                               ║
    ║         │ login   │ signup  │ logout  │                               ║
    ║         │   ✓     │   ⏳    │   ○     │                               ║
    ║         │ done    │ working │ pending │                               ║
    ║         └────┬────┴────┬────┴────┬────┘                               ║
    ║              │         │         │                                    ║
    ║              ▼         ▼         ▼                                    ║
    ║           🦨 nux   🦨 toast  (waiting)                                ║
    ║                                                                       ║
    ║   Convoy gives you a dashboard. When all close, you get notified.    ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
```

### DO:
Show them how to create a convoy:
```bash
gt convoy create "My Feature" <bead-1> <bead-2>
gt convoy list
gt convoy status <convoy-id>
```

### ASK:
```json
{
  "questions": [{
    "question": "Want to create a convoy for some work?",
    "header": "Convoy",
    "multiSelect": false,
    "options": [
      {"label": "Create a convoy", "description": "I'll help you batch some work"},
      {"label": "See existing convoys", "description": "Check what's tracked"},
      {"label": "Move on", "description": "Learn about watching workers"}
    ]
  }]
}
```

---

## 2.3 Watching Workers

### SHOW:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ⛽ STAGE 2: FLOW                                          Lesson 2.3 [3/5] ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Your workers are running. Here's how to check on them:

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                     WATCHING WORKERS                                  ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║  "how's toast doing?"   ──▶  gt peek <rig>/polecats/toast             ║
    ║                              Shows what they're working on            ║
    ║                                                                       ║
    ║  "list the polecats"    ──▶  gt polecat list                          ║
    ║                              All workers and their status             ║
    ║                                                                       ║
    ║  "polecat stuck"        ──▶  gt nudge <agent> "What's blocking?"      ║
    ║                              Send a message to unstick them           ║
    ║                                                                       ║
    ║  "cancel that work"     ──▶  gt unsling <bead-id>                     ║
    ║                              Stop work on a bead, free the polecat    ║
    ║                                                                       ║
    ║  "activity feed"        ──▶  gt feed                                  ║
    ║                              Real-time stream of everything           ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝

The Witness does most of this automatically. But you can check anytime.
```

### DO:
Show them real status:
```bash
gt polecat list
gt status
gt feed --since 5m
```

---

## 2.4 The Merge Pipeline

### SHOW:
```
When a polecat finishes, here's what happens:

    Polecat                    Witness                    Refinery
       │                          │                          │
       │ "I'm done!"              │                          │
       │──────────────────────────▶│                          │
       │                          │                          │
       │                    (verifies work)                  │
       │                          │                          │
       │                          │ "Ready to merge"         │
       │                          │──────────────────────────▶│
       │                          │                          │
       │                          │                    (runs tests)
       │                          │                    (merges to main)
       │                          │                          │
       │                          │ "Merged!"                │
       │                          │◀──────────────────────────│
       │                          │                          │
       │                    (cleans up polecat)              │
       │                          │                          │

You don't have to do anything. The pipeline runs automatically.
```

### DO:
Show the merge queue:
```bash
gt refinery status
gt refinery queue
```

---

## 2.5 Mail & Communication

### SHOW:
```
Agents communicate via mail. You can read it too!

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                         MAIL SYSTEM                                   ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║  "check my mail"        ──▶  gt mail inbox                            ║
    ║                                                                       ║
    ║  "send a message"       ──▶  gt mail send --to <agent>                ║
    ║                              --subject "Hi" --body "..."              ║
    ║                                                                       ║
    ║  "broadcast to all"     ──▶  gt broadcast "Check your mail"           ║
    ║                                                                       ║
    ║  "hand this off"        ──▶  gt handoff <bead> --to <agent>           ║
    ║                              Transfer work to another worker          ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝

Mail is how agents coordinate. Escalations, handoffs, and status updates
all flow through mail.
```

### SHOW (Stage 2 Complete):
```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                    🏆 STAGE 2 COMPLETE: FLOW 🏆                           ║
║                                                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  You now understand:                                                      ║
║                                                                           ║
║  ✓ All the characters and their roles                                     ║
║  ✓ Convoys for batch work tracking                                        ║
║  ✓ How to watch and nudge workers                                         ║
║  ✓ The merge pipeline                                                     ║
║  ✓ The mail system                                                        ║
║                                                                           ║
║  Work flows through your engine like fuel through pipes.                  ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

━━ ⛽ Gas Town | Learning ━━
```

### ASK:
```json
{
  "questions": [{
    "question": "Stage 2 complete! Ready for mastery?",
    "header": "Continue",
    "multiSelect": false,
    "options": [
      {"label": "Stage 3: Mastery", "description": "Full control of your factory"},
      {"label": "Practice what I learned", "description": "Create convoys, check workers"},
      {"label": "Take a break", "description": "We can continue anytime"}
    ]
  }]
}
```

---

# STAGE 3: MASTERY

## 3.1 Polecats vs Crew

### SHOW:
```
╔═══════════════════════════════════════════════════════════════════════════╗
║                       POLECATS vs CREW                                    ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║   🦨 POLECATS                    │   👷 CREW                              ║
║   ───────────────────────────────│───────────────────────────────────     ║
║   One task, then vanish          │   Stick around forever                 ║
║   Witness manages them           │   You manage them                      ║
║   Auto-cleanup                   │   Manual cleanup                       ║
║   Work on feature branches       │   Work on main (usually)               ║
║   Refinery merges their work     │   Push directly                        ║
║                                  │                                        ║
║   USE FOR:                       │   USE FOR:                             ║
║   • Bug fixes                    │   • Exploratory work                   ║
║   • Small features               │   • Long projects                      ║
║   • Batch tasks                  │   • Interactive sessions               ║
║   • Parallel work                │   • Ongoing assistance                 ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### DO:
Show them how to create crew:
```bash
gt crew add joe
gt crew list
gt crew at joe    # Attach to crew session
```

---

## 3.2 Multi-Rig Work

### SHOW:
```
When you have multiple projects, workers can cross rigs.

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                      MULTI-RIG WORK                                   ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║  Joe from project-a needs to fix a bug in project-b:                  ║
    ║                                                                       ║
    ║     ~/gt/project-a/crew/joe/     (Joe's home)                         ║
    ║                │                                                      ║
    ║                │  gt worktree project-b                               ║
    ║                ▼                                                      ║
    ║     ~/gt/project-b/crew/project-a-joe/  (Joe working on project-b)    ║
    ║                                                                       ║
    ║  Identity preserved! Work credits still go to project-a/crew/joe      ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 3.3 Molecules

### SHOW:
```
For multi-step work, use MOLECULES (workflows).

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                        MOLECULE                                       ║
    ║                    "Feature Implementation"                           ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║   [✓] mp-001.1: Design                                                ║
    ║   [✓] mp-001.2: Scaffold                                              ║
    ║   [✓] mp-001.3: Implement                                             ║
    ║   [→] mp-001.4: Write tests        ◀── YOU ARE HERE                   ║
    ║   [ ] mp-001.5: Documentation                                         ║
    ║   [ ] mp-001.6: Review                                                ║
    ║                                                                       ║
    ║   Progress: 3/6 steps                                                 ║
    ║                                                                       ║
    ║   bd mol current           # Where am I?                              ║
    ║   bd close mp-001.4 --continue  # Complete and advance                ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝

Molecules guide work through defined steps. Progress survives crashes.
```

---

## 3.4 Escalation

### SHOW:
```
When workers hit a blocker, they escalate.

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                      ESCALATION TIERS                                 ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║   Worker hits problem                                                 ║
    ║         │                                                             ║
    ║         ▼                                                             ║
    ║   ╔═══════════╗                                                       ║
    ║   ║  DEACON   ║  Can fix? → Done                                      ║
    ║   ║  (Tier 1) ║  Can't? → Forward                                     ║
    ║   ╚═════╤═════╝                                                       ║
    ║         │                                                             ║
    ║         ▼                                                             ║
    ║   ╔═══════════╗                                                       ║
    ║   ║   MAYOR   ║  Can fix? → Done                                      ║
    ║   ║  (Tier 2) ║  Can't? → Forward                                     ║
    ║   ╚═════╤═════╝                                                       ║
    ║         │                                                             ║
    ║         ▼                                                             ║
    ║   ╔═══════════╗                                                       ║
    ║   ║ OVERSEER  ║  You decide                                           ║
    ║   ║  (Tier 3) ║  (That's you!)                                        ║
    ║   ╚═══════════╝                                                       ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝

Most issues resolve at Tier 1 or 2. You only see what truly needs you.
```

---

## 3.5 Troubleshooting

### SHOW:
```
When something breaks, I run diagnostics.

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                      TROUBLESHOOTING                                  ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║  "something's broken"    ──▶  gt doctor                               ║
    ║                               Checks everything, reports issues       ║
    ║                                                                       ║
    ║  "fix it"                ──▶  gt doctor --fix                         ║
    ║                               Auto-repairs common issues              ║
    ║                                                                       ║
    ║  "health check"          ──▶  gt status                               ║
    ║                               Quick overview of all systems           ║
    ║                                                                       ║
    ║  You never see raw errors. I diagnose and fix for you.                ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 3.6 Gates (Async Coordination)

### SHOW:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ⛽ STAGE 3: MASTERY                                       Lesson 3.6 [6/7] ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Sometimes work needs to WAIT for something external.

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                           GATES                                       ║
    ║               (Async Checkpoints That Block Work)                     ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║   Polecat working...                                                  ║
    ║         │                                                             ║
    ║         │  "I need CI to pass before I can merge"                     ║
    ║         ▼                                                             ║
    ║   ┌─────────────┐                                                     ║
    ║   │ GATE: gh:run│◀───── Work PARKS here                               ║
    ║   │  (waiting)  │                                                     ║
    ║   └──────┬──────┘                                                     ║
    ║          │                                                            ║
    ║          │  CI completes ✓                                            ║
    ║          ▼                                                            ║
    ║   Work RESUMES automatically                                          ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝

GATE TYPES:
┌──────────┬────────────────────────────────────────────────────────────────┐
│ gh:run   │ Wait for GitHub Actions workflow to complete                   │
├──────────┼────────────────────────────────────────────────────────────────┤
│ gh:pr    │ Wait for pull request to be merged or closed                   │
├──────────┼────────────────────────────────────────────────────────────────┤
│ timer    │ Wait for a duration (rate limiting, cooldown)                  │
├──────────┼────────────────────────────────────────────────────────────────┤
│ human    │ Wait for human approval/acknowledgment                         │
├──────────┼────────────────────────────────────────────────────────────────┤
│ mail     │ Wait for a message to arrive                                   │
└──────────┴────────────────────────────────────────────────────────────────┘

Gates let workers wait for the real world without blocking other work.
```

### ASK:
```json
{
  "questions": [{
    "question": "Gates are powerful! Want to see park/resume in action?",
    "header": "Next",
    "multiSelect": false,
    "options": [
      {"label": "Show me park/resume", "description": "How work pauses and continues"},
      {"label": "Move to troubleshooting", "description": "Skip to fixing problems"}
    ]
  }]
}
```

---

## 3.7 Park and Resume

### SHOW:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ⛽ STAGE 3: MASTERY                                       Lesson 3.7 [7/7] ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Work can be PARKED (paused) and RESUMED later.

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                      PARK AND RESUME                                  ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║   "pause this work"     ──▶  gt park <bead> --reason "waiting on X"   ║
    ║                              Work goes into suspended state           ║
    ║                              Polecat can be freed for other work      ║
    ║                                                                       ║
    ║   "resume that work"    ──▶  gt resume <bead>                         ║
    ║                              Work picks up where it left off          ║
    ║                              New polecat spawns with full context     ║
    ║                                                                       ║
    ║   ─────────────────────────────────────────────────────────────────   ║
    ║                                                                       ║
    ║   USE CASES:                                                          ║
    ║   • Waiting for external API/service                                  ║
    ║   • Blocked on human decision                                         ║
    ║   • Rate limiting                                                     ║
    ║   • End of day - resume tomorrow                                      ║
    ║   • Priority shift - work on something else first                     ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝

The key: work state survives in beads. Context is never lost.
```

### DO:
```bash
# Show any parked work
gt status --parked

# Example park command (show but don't run unless they have active work)
# gt park <bead-id> --reason "Waiting for design review"
```

---

### SHOW (Stage 3 Complete):
```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                   🏆 STAGE 3 COMPLETE: MASTERY 🏆                         ║
║                                                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  You now have full control:                                               ║
║                                                                           ║
║  ✓ When to use polecats vs crew                                           ║
║  ✓ Cross-rig work coordination                                            ║
║  ✓ Multi-step workflows with molecules                                    ║
║  ✓ Escalation patterns                                                    ║
║  ✓ Troubleshooting and recovery                                           ║
║  ✓ Gates for async coordination                                           ║
║  ✓ Park and resume for work lifecycle                                     ║
║                                                                           ║
║  You're a master operator.                                                ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

━━ ⛽ Gas Town | Learning ━━
```

### ASK:
```json
{
  "questions": [{
    "question": "You're a master! Want to go deeper?",
    "header": "Continue",
    "multiSelect": false,
    "options": [
      {"label": "Stage 4: Expert", "description": "Deep internals and advanced workflows"},
      {"label": "I'm good for now", "description": "Start using what I learned"},
      {"label": "Quick reference", "description": "Summary of commands"}
    ]
  }]
}
```

---

# STAGE 4: EXPERT

## 4.1 Advanced Molecules

### SHOW:
```
Molecules have phases, like states of matter.

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                     MOLECULE PHASES                                   ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║   FORMULA (Ice-9)        Source template (TOML file)                  ║
    ║       │                                                               ║
    ║       ▼ cook                                                          ║
    ║   PROTOMOLECULE (Solid)  Frozen, ready to use                         ║
    ║       │                                                               ║
    ║       ├──▶ pour ──▶ MOL (Liquid)    Persistent workflow               ║
    ║       │                             Tracked, survives crashes         ║
    ║       │                                                               ║
    ║       └──▶ wisp ──▶ WISP (Vapor)    Ephemeral workflow                ║
    ║                                     For patrol cycles, no sync        ║
    ║                                                                       ║
    ║   squash ──▶ DIGEST                 Compressed summary                ║
    ║   burn   ──▶ (gone)                 Discard without record            ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 4.2 The Deacon

### SHOW:
```
The Deacon is the background daemon that keeps everything alive.

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                        THE DEACON                                     ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║   ⚙️ DEACON                                                           ║
    ║      │                                                                ║
    ║      ├── Spawns and kills agents                                      ║
    ║      ├── Health monitoring                                            ║
    ║      ├── Plugin execution                                             ║
    ║      ├── Receives WITNESS_PING (second-order monitoring)              ║
    ║      └── Handles Tier 1 escalations                                   ║
    ║                                                                       ║
    ║   You rarely interact with the Deacon directly.                       ║
    ║   It just keeps the engine running.                                   ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 4.3 Dogs

### SHOW:
```
Dogs are the Deacon's helpers for infrastructure tasks.

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                          DOGS                                         ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║   🐕 Dogs are NOT workers. They're infrastructure helpers.            ║
    ║                                                                       ║
    ║   BOOT dog: Checks Deacon health on every tick                        ║
    ║                                                                       ║
    ║   Future dogs might handle:                                           ║
    ║   • Log rotation                                                      ║
    ║   • Garbage collection                                                ║
    ║   • Cross-rig cleanup                                                 ║
    ║                                                                       ║
    ║   gt boot status               # Check Boot (Deacon watchdog) status   ║
    ║   gt boot spawn                # Spawn Boot for triage                ║
    ║                                                                       ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 4.4 Seance

### SHOW:
```
Talk to predecessor sessions - see what they did.

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                         SEANCE                                        ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║   gt seance                      # List recent sessions               ║
    ║   gt seance --role crew          # Filter by role                     ║
    ║   gt seance --talk <id>          # Talk to predecessor                ║
    ║   gt seance --talk <id> -p "?"   # Ask one question                   ║
    ║                                                                       ║
    ║   Use cases:                                                          ║
    ║   • "What did the last polecat do?"                                   ║
    ║   • "Where did this work get left off?"                               ║
    ║   • "Why was this decision made?"                                     ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 4.5 Custom Workflows

### SHOW:
```
You can create your own formulas for repeated workflows.

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                    CUSTOM FORMULAS                                    ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║   Formulas are TOML files that define workflow steps:                 ║
    ║                                                                       ║
    ║   [formula]                                                           ║
    ║   name = "bug-fix"                                                    ║
    ║   description = "Standard bug fix workflow"                           ║
    ║                                                                       ║
    ║   [[step]]                                                            ║
    ║   name = "reproduce"                                                  ║
    ║   prompt = "Reproduce the bug and document steps"                     ║
    ║                                                                       ║
    ║   [[step]]                                                            ║
    ║   name = "fix"                                                        ║
    ║   prompt = "Implement the fix"                                        ║
    ║                                                                       ║
    ║   [[step]]                                                            ║
    ║   name = "test"                                                       ║
    ║   prompt = "Write tests to prevent regression"                        ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
```

### SHOW (Stage 4 Complete):
```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                    🏆 STAGE 4 COMPLETE: EXPERT 🏆                         ║
║                                                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  You understand the deep internals:                                       ║
║                                                                           ║
║  ✓ Molecule phases (formula → proto → mol/wisp → digest)                  ║
║  ✓ The Deacon and infrastructure                                          ║
║  ✓ Dogs as Deacon helpers                                                 ║
║  ✓ Seance for predecessor sessions                                        ║
║  ✓ Custom workflow formulas                                               ║
║                                                                           ║
║  You ARE Gas Town.                                                        ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

                    ╔═════════════════════════════════╗
                    ║                                 ║
                    ║   GUPP: If your hook has work,  ║
                    ║         YOU RUN IT.             ║
                    ║                                 ║
                    ╚═════════════════════════════════╝

            The Cognition Engine is yours. Fire it up and GO.

━━ ⛽ Gas Town | Learning ━━
```

---

# Going Forward

After the tutorial, show this to reinforce the ongoing relationship:

### SHOW:
```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                         GOING FORWARD                                     ║
║                                                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  You now understand Gas Town. But nothing changes about how we work:      ║
║                                                                           ║
║                    YOU TALK.  I OPERATE.                                  ║
║                                                                           ║
║  Just tell me what you want:                                              ║
║                                                                           ║
║    "sling that bug to myproject"                                          ║
║    "check on the polecats"                                                ║
║    "create a convoy for the auth feature"                                 ║
║    "how's toast doing?"                                                   ║
║    "something's broken, fix it"                                           ║
║                                                                           ║
║  I'll run the commands, watch the workers, handle the errors.             ║
║  You never touch the terminal. You just drive.                            ║
║                                                                           ║
║  The engine is yours. What shall we build?                                ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

━━ ⛽ Gas Town ━━
```

### ASK:
```json
{
  "questions": [{
    "question": "What would you like to do first?",
    "header": "Go",
    "multiSelect": false,
    "options": [
      {"label": "Check the status", "description": "See what's running"},
      {"label": "Create some work", "description": "Track a new task"},
      {"label": "Add another project", "description": "Hook up a new repo"},
      {"label": "Just explore", "description": "I'll poke around"}
    ]
  }]
}
```

---

# Quick Reference

Show this when user asks for a summary:

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                      GAS TOWN QUICK REFERENCE                             ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  CORE CONCEPT                                                             ║
║  ───────────                                                              ║
║  SLING work → lands on HOOK → GUPP: "If hook has work, RUN IT"            ║
║                                                                           ║
║  COMMANDS YOU ASK FOR          │  WHAT I RUN                              ║
║  ──────────────────────────────│──────────────────────────────────        ║
║  "fire up the engine"          │  gt up                                   ║
║  "shut it down"                │  gt down                                 ║
║  "check status"                │  gt status                               ║
║  "add my project"              │  gt rig add <name> <url>                 ║
║  "create work: <desc>"         │  bd create --title "<desc>"              ║
║  "sling <work> to <rig>"       │  gt sling <bead> <rig>                   ║
║  "cancel that work"            │  gt unsling <bead>                       ║
║  "list polecats"               │  gt polecat list                         ║
║  "how's <worker>?"             │  gt peek <agent>                         ║
║  "check my mail"               │  gt mail inbox                           ║
║  "hand this off to <agent>"    │  gt handoff <bead> --to <agent>          ║
║  "pause this work"             │  gt park <bead> --reason "..."           ║
║  "resume that work"            │  gt resume <bead>                        ║
║  "create convoy"               │  gt convoy create <name> <beads>         ║
║  "add crew member <name>"      │  gt crew add <name>                      ║
║  "something's broken"          │  gt doctor --fix                         ║
║                                                                           ║
║  CHARACTERS                                                               ║
║  ──────────                                                               ║
║  👤 Overseer (You)   🦊 Mayor   ⚙️ Deacon   🦅 Witness                    ║
║  🦡 Refinery   🦨 Polecats   👷 Crew   🐕 Dogs                            ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```
