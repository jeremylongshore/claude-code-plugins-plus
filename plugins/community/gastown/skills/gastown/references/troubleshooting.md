# Gastown Troubleshooting Guide

**Internal Reference for Claude Code** - You diagnose and fix issues for the user.

## Core Principle

When the user reports a problem or something seems broken:
1. Run `gt doctor` to diagnose
2. Interpret the results
3. Run `gt doctor --fix` if appropriate
4. Report what you found and fixed in a warm voice

The user never sees raw error messages or runs commands themselves.

## Error Severity Guide

**CRITICAL: Not all errors are equal. Know which to fix immediately.**

| Severity | Description | Action |
|----------|-------------|--------|
| **BLOCKER** | Prevents core functionality | Must fix before slinging work |
| **WARNING** | Degraded but functional | Fix when convenient |
| **INFO** | Advisory only | Can ignore |

### BLOCKER Errors (Fix Immediately)

- **Prefix mismatch** - Work won't route correctly
- **Missing patrol molecules** - Refinery/Witness won't run
- **Refinery not running** - Merges won't process
- **Routes.jsonl missing entries** - Beads can't find database
- **bd doctor critical failures** - Beads system broken

### WARNING Errors (Fix Soon)

- **Daemon timeout** - Falls back to direct mode (slower)
- **Beads sync issues** - May resolve with `bd sync`
- **Agent bead missing** - Worker may not have full context

**Rule: If `gt doctor` or `bd doctor` shows BLOCKER-level errors, fix them before declaring setup complete or slinging work.**

## Table of Contents

1. [Running gt doctor](#running-gt-doctor)
2. [Doctor Checks Reference](#doctor-checks-reference)
3. [Common Error Messages](#common-error-messages)
4. [Prefix Mismatch Errors](#prefix-mismatch-errors)
5. [BEADS_NO_DAEMON Environment Variable](#beads_no_daemon-environment-variable)
6. [Session Errors](#session-errors)
7. [Git Errors](#git-errors)
8. [Beads Errors](#beads-errors)
9. [Tmux Errors](#tmux-errors)
10. [Config Version Errors](#config-version-errors)
11. [Recovery Procedures](#recovery-procedures)

---

## Running Diagnostics

**Always run BOTH diagnostic tools:**

```bash
# Gas Town diagnostics
gt doctor              # Check everything
gt doctor --fix        # Auto-fix issues
gt doctor --verbose    # Detailed output
gt doctor --check <name>  # Specific check

# Beads diagnostics
bd doctor              # Check beads health
```

**Why both?** Gas Town (`gt`) manages the engine. Beads (`bd`) manages work tracking. Problems in either can break slinging.

---

## Doctor Checks Reference

### Configuration Checks

#### config-version
**Description:** Verify config file versions are compatible

**Detects:**
- Config files with unsupported version numbers
- Missing required config files

**Error:** `unsupported config version: got %d, max supported %d`

**Fix:** Update config files to current schema version or regenerate with `gt init`

---

#### rig-config
**Description:** Validate rig configuration files

**Detects:**
- Invalid rig config type
- Missing required fields (name, git_url)
- Invalid merge queue settings

**Error:** `invalid config type: expected type 'rig', got '%s'`
**Error:** `missing required field: name`

**Fix:** Run `gt doctor --fix` or manually edit config files

---

#### crew-state
**Description:** Validate crew worker state.json files

**Detects:**
- Empty or incomplete state.json files
- Missing name, rig, or clone_path fields
- Invalid JSON in state files

**Symptoms:** "can't find pane/session" errors

**Error:** `invalid JSON in state.json`
**Error:** `missing name, missing rig, missing clone_path`

**Fix:** Run `gt doctor --fix` to regenerate state files with correct values

---

### Beads Checks

#### beads-routes
**Description:** Check beads routing configuration

**Detects:**
- Missing routes.jsonl file
- Duplicate prefix routes (conflicts)
- Invalid route entries

**Message:** `No routes.jsonl file (prefix routing not configured)`

**Fix:** Run `gt rig add` to configure routes for a rig

---

#### agent-beads-exist
**Description:** Verify agent beads exist for all agents

**Detects:**
- Missing beads for global agents (deacon, mayor)
- Missing beads for per-rig agents (witness, refinery)
- Missing beads for crew workers

**Error:** `%d agent bead(s) missing`

**FixHint:** `Run 'gt doctor --fix' to create missing agent beads`

**Agent bead naming convention:**
- Witness: `{prefix}-rig-{rigName}-witness`
- Refinery: `{prefix}-rig-{rigName}-refinery`
- Crew: `{prefix}-rig-{rigName}-crew-{workerName}`
- Deacon: `gt-deacon`
- Mayor: `gt-mayor`

---

### Tmux & Session Checks

#### daemon-tmux
**Description:** Check tmux availability for daemon

**Detects:**
- tmux not installed
- tmux server not running
- Incompatible tmux version

**Error:** `no tmux server running`

**Fix:** Install tmux or start tmux server with `tmux new-session -d`

---

#### orphan-sessions
**Description:** Detect orphaned tmux sessions

**Detects:**
- Sessions with `gt-` prefix not matching valid rigs
- Sessions for deleted polecats or crew members

**Valid session patterns:**
- `gt-mayor`
- `gt-deacon`
- `gt-{rig}-witness`
- `gt-{rig}-refinery`
- `gt-{rig}-{polecat}`
- `gt-{rig}-crew-{name}`

**FixHint:** `Run 'gt doctor --fix' to kill orphaned sessions`

**Note:** Crew sessions (`gt-{rig}-crew-{name}`) are protected from auto-cleanup

---

#### orphan-processes
**Description:** Detect orphaned Claude processes

**Detects:**
- Claude CLI processes without tmux parent
- Zombie processes from crashed sessions

**Error:** `Found %d orphaned Claude process(es)`

**FixHint:** `Run 'gt doctor --fix' to kill orphaned processes`

**Note:** Crew session processes are protected from auto-kill

---

#### themes
**Description:** Check tmux session theme configuration

**Detects:**
- Sessions with outdated theme format (brackets)

**FixHint:** `Run 'gt theme apply --all' or 'gt doctor --fix'`

---

### Boot & Daemon Checks

#### boot-health
**Description:** Check Boot watchdog health ("the vet checks on the dog")

**Detects:**
- Boot directory not present
- Session not running
- Last run errors
- Stale marker file (indicates crash)

**Messages:**
- `Boot directory not present`
- `Failed to load Boot status`
- `Boot last run had an error`
- `Boot marker is stale (possible crash)`
- `Boot watchdog healthy (degraded mode)` - running without tmux

**FixHint:** `Boot directory is created on first daemon run`

---

### Hook & Attachment Checks

#### hook-attachment-valid
**Description:** Verify attached molecules exist and are not closed

**Detects:**
- Hooks pointing to non-existent molecules
- Hooks pointing to closed issues

**Error:** `%s: attached molecule %s not found`
**Error:** `%s: attached molecule %s is closed`

**FixHint:** `Run 'gt doctor --fix' to detach invalid molecules, or 'gt mol detach <pinned-bead-id>' manually`

---

#### hook-singleton
**Description:** Ensure each agent has at most one handoff bead

**Detects:**
- Multiple pinned beads with same "{role} Handoff" title

**Error:** `"%s" has %d beads: %s`

**FixHint:** `Run 'gt doctor --fix' to close duplicates, or 'bd close <id>' manually`

---

#### orphaned-attachments
**Description:** Detect handoff beads for non-existent agents

**Detects:**
- Handoffs for deleted polecats
- Handoffs for removed crew members

**FixHint:** `Reassign with 'gt sling <id> <agent>', or close with 'bd close <id>'`

---

### Lifecycle Checks

#### lifecycle-hygiene
**Description:** Check for stale lifecycle messages and stuck state flags

**Detects:**
- Stale lifecycle messages in deacon inbox
- Stuck `requesting_*` flags in state.json files

**Error:** `%d stale lifecycle message(s) in deacon inbox`
**Error:** `%d agent(s) with stuck requesting_* flags`

**FixHint:** `Run 'gt doctor --fix' to clean up`

---

### Branch & Git Checks

#### persistent-role-branches
**Description:** Detect persistent roles not on main branch

**Detects:**
- Crew workers on feature branches
- Witness/refinery roles off main

**Error:** `%d persistent role(s) not on main branch`

**FixHint:** `Run 'gt doctor --fix' to switch to main, or manually: git checkout main && git pull`

---

#### beads-sync-orphans
**Description:** Detect orphaned code on beads-sync branch

**Detects:**
- Code changes on beads-sync that weren't merged to main

**FixHint:** `Review with: git diff main..beads-sync -- <file>`

---

#### clone-divergence
**Description:** Detect emergency divergence between git clones

**Detects:**
- Clones significantly behind origin/main (>10 commits = warning, >50 = error)

**Error:** `%d clone(s) critically diverged`

**FixHint:** `Run 'git pull --rebase' in affected directories`

---

### Patrol Checks

#### patrol-molecules-exist
**Description:** Check if patrol molecules exist for each rig

**Required molecules:**
- `Deacon Patrol`
- `Witness Patrol`
- `Refinery Patrol`

**FixHint:** `Run 'gt doctor --fix' to create missing patrol molecules`

---

#### patrol-hooks-wired
**Description:** Check if hooks trigger patrol execution

**Detects:**
- Missing daemon config
- Patrols not configured in daemon.json

**FixHint:** `Configure patrols in mayor/daemon.json or run 'gt deacon init'`

---

#### patrol-not-stuck
**Description:** Check for stuck patrol wisps (>1h in_progress)

**Detects:**
- In-progress wisps older than 1 hour

**FixHint:** `Manual review required - wisps may need to be burned or sessions restarted`

---

#### patrol-plugins-accessible
**Description:** Check if plugin directories exist and are readable

**FixHint:** `Run 'gt doctor --fix' to create missing directories`

---

### Wisp Checks

#### wisp-gc
**Description:** Detect and clean orphaned wisps (>1h old)

**Detects:**
- Wisps not closed and older than 1 hour

**Error:** `%d abandoned wisp(s) found (>1h old)`

**FixHint:** `Run 'gt doctor --fix' to garbage collect orphaned wisps`

**Fix command:** `bd --no-daemon mol wisp gc`

---

### Version Control Checks

#### town-git
**Description:** Verify town root is under version control

**Message:** `Town root is not under version control`

**FixHint:** `Run 'git init' in your town root to initialize a repository`

---

## Common Error Messages

### Config Errors

```
config file not found: %s
```
**Cause:** Required config file doesn't exist
**Fix:** Run `gt init` or create the missing config file

```
unsupported config version: got %d, max supported %d
```
**Cause:** Config file uses newer schema than gt supports
**Fix:** Upgrade gt or downgrade config version

```
invalid config type: expected type '%s', got '%s'
```
**Cause:** Config file has wrong type field
**Fix:** Correct the type field in the config file

```
missing required field: %s
```
**Cause:** Required field (name, role, etc.) not specified
**Fix:** Add the missing field to the config

---

### Session Errors

```
session already running
```
**Cause:** Attempting to start a session that's already active
**Fix:** Use `gt ps` to check running sessions, stop with `gt stop <name>`

```
session not found
```
**Cause:** Referenced session doesn't exist
**Fix:** Verify session name, check `tmux list-sessions`

```
polecat not found
```
**Cause:** Polecat worktree doesn't exist
**Fix:** Verify polecat name, check `gt polecat list`

```
invalid session name "%s": missing "%s" prefix
```
**Cause:** Session name doesn't start with expected prefix (gt-)
**Fix:** Use correct session naming convention

```
invalid session name "%s": empty after prefix
```
**Cause:** Session name has prefix but nothing after
**Fix:** Use complete session name like `gt-mayor`

```
invalid session name "%s": expected rig-role format
```
**Cause:** Session name doesn't follow rig-role pattern
**Fix:** Use format `gt-{rig}-{role}` or `gt-{rig}-{name}`

---

### Git Errors

```
not a git repository
```
**Cause:** Command run outside a git repository
**Fix:** Navigate to a git repository or initialize one

```
merge conflict
```
**Cause:** Git merge has conflicts requiring resolution
**Fix:** Resolve conflicts manually, then `git add` and `git commit`

```
authentication failed
```
**Cause:** Git authentication failed (SSH key, token, etc.)
**Fix:** Check SSH keys, refresh tokens, verify credentials

```
rebase conflict
```
**Cause:** Git rebase encountered conflicts
**Fix:** Resolve conflicts, `git add`, then `git rebase --continue`

---

### Mail & Routing Errors

```
unknown mailing list: %s
```
**Cause:** Mailing list not defined in messaging config
**Fix:** Add list to `config/messaging.json`

```
unknown queue: %s
```
**Cause:** Queue not defined in messaging config
**Fix:** Add queue to `config/messaging.json`

```
unknown announce channel: %s
```
**Cause:** Announce channel not defined
**Fix:** Add announce channel to messaging config

---

### Refinery Errors

```
refinery not running
```
**Cause:** Refinery session not active
**Fix:** Start with `gt refinery start`

```
refinery already running
```
**Cause:** Attempting to start refinery that's running
**Fix:** Stop existing refinery first

```
no items in queue
```
**Cause:** Merge queue is empty
**Fix:** Normal state, no action needed

```
merge request not found
```
**Cause:** Referenced MR doesn't exist
**Fix:** Verify MR ID, check with `gt mq ls`

```
invalid state transition: %s -> %s is not allowed
```
**Cause:** Attempted illegal MR state change
**Fix:** Follow valid state transitions

```
closed merge requests are immutable
```
**Cause:** Attempting to modify a closed MR
**Fix:** Closed MRs cannot be modified

---

### Deacon/Stuck Agent Errors

```
agent is in cooldown period after recent force-kill
```
**Cause:** Agent was recently force-killed and is in cooldown
**Fix:** Wait for cooldown to expire before restart

```
agent not found or session doesn't exist
```
**Cause:** Referenced agent has no active session
**Fix:** Start the agent session first

```
agent is responsive, no action needed
```
**Cause:** Health check found agent is working normally
**Fix:** No action needed

---

## Prefix Mismatch Errors

**⚠️ BLOCKER: Prefix mismatches must be fixed before slinging work.**

Prefix mismatches are one of the most common issues in multi-rig setups. They prevent work from routing correctly and will cause slinging to fail.

### Understanding Prefixes

Each rig can have a unique prefix for its beads:
- Default prefix: `gt-` (for gastown)
- Custom prefix: `bd-` (for beads project), `my-` (custom)

Prefixes are configured in `~/.beads/routes.jsonl`:
```json
{"prefix":"gt-","path":"gastown/mayor/rig"}
{"prefix":"bd-","path":"beads/mayor/rig"}
```

### Common Prefix Problems

#### 1. Wrong prefix in commands
**Error:** Commands fail silently or return "not found"

**Cause:** Using `gt-xyz` when bead is actually `bd-xyz`

**Diagnosis:**
```bash
# Check what prefixes are configured
cat ~/gt/.beads/routes.jsonl

# Check bead's actual prefix
bd show <full-id>
```

**Fix:** Use the correct prefix for the rig you're working with

#### 2. Agent beads created with wrong prefix
**Error:** Agent beads not found during health checks

**Cause:** Routes not configured before rig was added

**Diagnosis:**
```bash
gt doctor --check agent-beads-exist
```

**Fix:**
```bash
gt doctor --fix
```

#### 3. Conflicting prefix routes
**Error:** Multiple rigs claiming same prefix

**Diagnosis:**
```bash
# Check for duplicates
gt doctor --check beads-routes
```

**Fix:** Edit `routes.jsonl` to remove duplicate entries

### Prefix Resolution Flow

1. Command parses bead ID (e.g., `gt-abc12`)
2. Extracts prefix (`gt-`)
3. Looks up prefix in `routes.jsonl`
4. Routes to correct `.beads` directory

If the prefix isn't in routes, commands may fail or route incorrectly.

---

## BEADS_NO_DAEMON Environment Variable

### Why It's Critical

`BEADS_NO_DAEMON=1` prevents the beads daemon from committing to the wrong branch when running in worktrees (polecats, crew).

### When It's Required

- **Polecats** - Always (set automatically by gt)
- **Crew workers** - Always (set automatically by gt)
- **Refinery** - Always (set automatically by gt)
- **Manual bd commands in worktrees** - Must set manually

### What Happens Without It

1. Daemon process sees beads changes
2. Daemon commits from its own context (wrong branch)
3. Beads end up on wrong branch
4. Worktree gets out of sync

### Setting It

**Automatic (gt commands):**
```go
// From session/manager.go
_ = m.tmux.SetEnvironment(sessionID, "BEADS_NO_DAEMON", "1")
```

**Manual (shell):**
```bash
export BEADS_NO_DAEMON=1
bd create --title "My Issue"
```

### Verifying It's Set

In tmux session:
```bash
echo $BEADS_NO_DAEMON
# Should output: 1
```

Check tmux environment:
```bash
tmux show-environment -t gt-gastown-polecat1 BEADS_NO_DAEMON
```

---

## Session Errors

### Session Identity Parsing

Sessions follow strict naming conventions:

| Pattern | Example | Components |
|---------|---------|------------|
| `gt-mayor` | `gt-mayor` | role=mayor |
| `gt-deacon` | `gt-deacon` | role=deacon |
| `gt-{rig}-witness` | `gt-gastown-witness` | rig=gastown, role=witness |
| `gt-{rig}-refinery` | `gt-gastown-refinery` | rig=gastown, role=refinery |
| `gt-{rig}-crew-{name}` | `gt-gastown-crew-joe` | rig=gastown, role=crew, name=joe |
| `gt-{rig}-{polecat}` | `gt-gastown-nux` | rig=gastown, name=nux |

### Session State Issues

#### Session exists but unresponsive
**Symptoms:** Commands hang, no output

**Diagnosis:**
```bash
tmux has-session -t gt-gastown-nux && echo "exists"
tmux capture-pane -t gt-gastown-nux -p | tail -20
```

**Fix:**
```bash
gt stop gastown/nux --force
gt start gastown/nux
```

#### Session zombie (process dead, session exists)
**Symptoms:** Session shows in `tmux ls` but pane is empty

**Fix:**
```bash
tmux kill-session -t gt-gastown-nux
gt start gastown/nux
```

#### Multiple sessions for same agent
**Error:** Confused state, duplicate work

**Diagnosis:**
```bash
tmux list-sessions | grep gastown-nux
```

**Fix:** Kill all and restart cleanly
```bash
tmux kill-session -t gt-gastown-nux
# If duplicates with suffix:
tmux list-sessions | grep gastown-nux | cut -d: -f1 | xargs -I {} tmux kill-session -t {}
gt start gastown/nux
```

---

## Git Errors

### Common Git Issues

#### Worktree Already Exists
**Error:** `fatal: '<path>' already exists`

**Cause:** Previous worktree not cleaned up

**Fix:**
```bash
git worktree remove <path> --force
# Or manually:
rm -rf <path>
git worktree prune
```

#### Detached HEAD in Worktree
**Error:** Operations fail because not on branch

**Diagnosis:**
```bash
cd <worktree>
git status
# Shows "HEAD detached at..."
```

**Fix:**
```bash
git checkout <branch>
# Or create new branch:
git checkout -b <new-branch>
```

#### Unpushed Commits in Persistent Roles
**Warning:** Crew/witness/refinery have local commits

**Diagnosis:**
```bash
git log origin/main..HEAD --oneline
```

**Fix:**
```bash
git push origin main
```

---

## Beads Errors

### Redirect Issues

Beads uses redirect files for shared beads access across worktrees.

#### Circular Redirect
**Warning:** `circular redirect detected in %s (points to itself), ignoring redirect`

**Cause:** Redirect file points back to same directory

**Auto-fix:** The redirect file is automatically removed

**Manual fix:**
```bash
rm <path>/.beads/redirect
```

#### Redirect Chain
**Warning:** `redirect chain detected: %s -> %s (which also has a redirect)`

**Cause:** Multiple levels of redirection

**Fix:** Remove intermediate redirect:
```bash
rm <target>/.beads/redirect
```

#### Missing Redirect Target
**Symptom:** Beads commands fail in worktree

**Diagnosis:**
```bash
cat .beads/redirect
# Check if target exists
ls -la <target-path>
```

**Fix:** Recreate redirect or fix target path:
```bash
echo "../../mayor/rig/.beads" > .beads/redirect
```

### Routes File Issues

#### No Routes File
**Message:** `No routes.jsonl file (prefix routing not configured)`

**Cause:** Routes not configured (single-rig setup)

**Fix (if needed):**
```bash
# Routes are created by gt rig add
gt rig add <name> <git-url>
```

#### Invalid Route Entry
**Symptom:** Prefix lookup fails

**Diagnosis:**
```bash
cat ~/gt/.beads/routes.jsonl
# Look for malformed JSON lines
```

**Fix:** Edit to correct JSON format:
```json
{"prefix":"gt-","path":"gastown/mayor/rig"}
```

---

## Tmux Errors

### No Tmux Server
**Error:** `no tmux server running`

**Fix:**
```bash
tmux new-session -d -s scratch
# Or let gt commands start it automatically
```

### Session Already Exists
**Error:** `session already exists`

**Cause:** Tmux session with same name exists

**Fix:**
```bash
tmux kill-session -t <session-name>
# Then retry
```

### Session Not Found
**Error:** `session not found`

**Cause:** Session doesn't exist or was killed

**Fix:** Start the session:
```bash
gt start <agent>
```

### Linked Panes Crosstalk

**Symptom:** Commands sent to one pane affect another

**Cause:** Tmux panes sharing same shell process (rare)

**Diagnosis:**
```bash
tmux list-panes -t <session> -F '#{pane_id} #{pane_pid}'
# Check for duplicate PIDs
```

**Fix:**
```bash
tmux kill-session -t <session>
gt start <agent>
```

### Timeout Errors

```
timeout waiting for command (still running excluded command)
```
**Cause:** Long-running command blocking pane

**Fix:** Wait for command to complete or:
```bash
tmux send-keys -t <session> C-c
```

```
timeout waiting for shell
```
**Cause:** Shell not ready in pane

**Fix:** Check if process is stuck:
```bash
tmux capture-pane -t <session> -p
```

```
timeout waiting for Claude prompt
```
**Cause:** Claude not starting or hung

**Fix:**
```bash
gt stop <agent> --force
gt start <agent>
```

---

## Config Version Errors

### Version Mismatch

**Error:** `unsupported config version: got %d, max supported %d`

**Cause:** Config file from newer gt version

**Current versions:**
- TownConfig: Check `CurrentTownVersion` constant
- RigsConfig: Check `CurrentRigsVersion` constant
- RigConfig: Check `CurrentRigConfigVersion` constant
- RigSettings: Check `CurrentRigSettingsVersion` constant

**Fix options:**
1. Upgrade gt to newer version
2. Downgrade config version (if compatible)
3. Regenerate config with `gt init`

### Type Mismatch

**Error:** `invalid config type: expected type '%s', got '%s'`

**Cause:** Wrong config file used or corrupted type field

**Fix:** Correct the `type` field:
- Town config: `"type": "town"`
- Rig config: `"type": "rig"`
- Rig settings: `"type": "rig-settings"`
- Mayor config: `"type": "mayor-config"`
- Messaging config: `"type": "messaging"`

---

## Recovery Procedures

### Complete Reset

When everything is broken:

```bash
# 1. Stop all sessions
gt stop --all --force

# 2. Kill any orphaned tmux sessions
tmux list-sessions | grep '^gt-' | cut -d: -f1 | xargs -I {} tmux kill-session -t {}

# 3. Kill orphaned Claude processes
pkill -f "claude.*--dangerously-skip-permissions" || true

# 4. Run doctor with fix
gt doctor --fix

# 5. Restart daemon
gt deacon restart

# 6. Verify health
gt doctor
```

### Rig Recovery

When a single rig is broken:

```bash
# 1. Stop rig agents
gt stop <rig>/witness --force
gt stop <rig>/refinery --force

# 2. Check rig config
cat ~/gt/<rig>/settings/config.json

# 3. Verify worktrees
git -C ~/gt/<rig>/mayor/rig worktree list

# 4. Clean stale worktrees
git -C ~/gt/<rig>/mayor/rig worktree prune

# 5. Restart rig
gt start <rig>/witness
gt start <rig>/refinery
```

### Polecat Recovery

When a polecat is stuck:

```bash
# 1. Force stop
gt stop <rig>/<polecat> --force

# 2. Check worktree status
git -C ~/gt/<rig>/polecats/<polecat> status

# 3. Clean any locks
rm -f ~/gt/<rig>/polecats/<polecat>/.git/index.lock

# 4. Reset if needed
git -C ~/gt/<rig>/polecats/<polecat> reset --hard HEAD

# 5. Restart
gt start <rig>/<polecat>
```

### Crew Recovery

When a crew workspace is broken:

```bash
# 1. Check state file
cat ~/gt/<rig>/crew/<name>/state.json

# 2. If state is corrupted, regenerate
gt doctor --fix

# 3. Verify git status
git -C ~/gt/<rig>/crew/<name> status

# 4. If on wrong branch
git -C ~/gt/<rig>/crew/<name> checkout main

# 5. Restart if session was running
gt crew attach <rig>/<name>
```

### Beads Database Recovery

When beads are corrupted:

```bash
# 1. Backup current state
cp -r ~/gt/.beads ~/gt/.beads.backup

# 2. Check JSONL files for corruption
jq -c '.' ~/gt/.beads/issues.jsonl > /dev/null || echo "Corrupted"

# 3. If corrupted, try to recover valid lines
grep -E '^\{.*\}$' ~/gt/.beads/issues.jsonl > ~/gt/.beads/issues.jsonl.fixed
mv ~/gt/.beads/issues.jsonl.fixed ~/gt/.beads/issues.jsonl

# 4. Rebuild routes if needed
gt doctor --fix
```

### Daemon Recovery

When the daemon is unresponsive:

```bash
# 1. Check daemon status
gt deacon status

# 2. Check daemon logs
cat ~/gt/.beads/daemon.log

# 3. Stop daemon forcefully
gt deacon stop --force

# 4. Clean stale markers
rm -f ~/gt/mayor/boot/.marker

# 5. Restart daemon
gt deacon start

# 6. Verify
gt deacon status
```
