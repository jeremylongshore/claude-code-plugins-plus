# System Readiness Checklist

## System Readiness Checklist

**CRITICAL: Partial functionality ≠ working.** Never declare Gas Town "ready" until the FULL flow is verified.

### After Installation

Run BOTH diagnostics:

```bash
gt doctor                    # Gas Town health
bd doctor                    # Beads health
```

**BLOCKERS** (must fix before proceeding):

- [ ] No prefix mismatch errors
- [ ] No missing routes.jsonl entries
- [ ] Beads daemon responding
- [ ] No critical errors in either doctor output

### After Rig Creation

Every new rig needs verification:

```bash
gt rig list                  # Rig appears
gt doctor                    # No new errors
bd list --prefix <rig-prefix>  # Beads exist for this rig
```

**BLOCKERS:**

- [ ] Patrol molecules exist (Deacon, Witness, Refinery patrols)
- [ ] Prefix routing configured in routes.jsonl
- [ ] Refinery started: `gt refinery start`

If patrols don't exist: `gt doctor --fix`

### Before Slinging Work

```bash
gt up                        # Engine running
gt status                    # All systems green
gt refinery status           # Refinery active
```

**BLOCKERS:**

- [ ] Engine is up
- [ ] No prefix mismatch warnings
- [ ] Patrol cycles active (not just templates)

### Full Flow Verification

**Before declaring the system working, test the COMPLETE flow:**

```
1. Create test bead          bd create --title "Test task"
2. Sling to polecat          gt sling <bead> <rig>
3. Polecat completes         gt peek <polecat> (watch for completion)
4. Witness marks ready       Check mail or gt witness status
5. Refinery processes        gt refinery queue (should be processing)
6. Code lands on main        git log in rig shows merge
```

If ANY step fails → investigate and fix before moving on.
Do NOT present partial functionality as complete.

### Error Severity Guide

| Error Type | Severity | Action |
|------------|----------|--------|
| Prefix mismatch | **BLOCKER** | Fix with `gt doctor --fix` or edit routes.jsonl |
| Missing patrol molecules | **BLOCKER** | Run `gt doctor --fix` |
| Refinery not running | **BLOCKER** | Start with `gt refinery start` |
| Daemon timeout warning | WARNING | May work in direct mode, but investigate |
| Beads sync issues | WARNING | Run `bd sync`, continue if successful |

**Golden Rule:** If `gt doctor` or `bd doctor` shows errors, fix them before slinging work.
