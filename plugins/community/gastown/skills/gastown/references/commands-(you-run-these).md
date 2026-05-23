# Commands (You Run These)

## Commands (You Run These)

```
Engine Control
  gt up                    Fire up the engine
  gt down                  Graceful shutdown
  gt status                Overview

Work Management
  gt sling <bead> <rig>    Assign work to a rig
  gt convoy list           Show all convoys
  gt hook                  What's on your hook

Workers
  gt polecat list          List polecats
  gt crew list             List crew members
  gt peek <agent>          Check worker status
  gt nudge <agent> "msg"   Send message to worker

Diagnostics
  gt doctor                Gas Town health check
  gt doctor --fix          Auto-repair Gas Town issues
  bd doctor                Beads health check
  gt feed                  Activity stream

Beads (Work Tracking)
  bd list                  List beads
  bd show <id>             Show bead details
  bd sync                  Sync beads across clones

Refinery (Merge Pipeline)
  gt refinery start        Start the Refinery
  gt refinery status       Check Refinery status
  gt refinery queue        Show merge queue

Patrol Activation (Trigger Witness/Refinery)
  gt mail send <rig>/witness -s "Patrol" -m "Process completed work"
  gt mail send <rig>/refinery -s "Patrol" -m "Process merge queue"
```

**Note:** Witness and Refinery are Claude agents, not daemons. They respond to mail instructions.
