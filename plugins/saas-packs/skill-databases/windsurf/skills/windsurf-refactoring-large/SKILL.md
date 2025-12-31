---
name: windsurf-refactoring-large
description: |
  Execute large-scale refactoring with Cascade coordination. Activate when users mention
  "large refactoring", "codebase migration", "architecture refactor", "major refactoring",
  or "system-wide changes". Handles complex refactoring operations.
allowed-tools: Read,Write,Edit,Bash,Grep,Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Large-Scale Refactoring

Execute complex refactoring operations with Cascade AI coordination.

## Directory Structure

```
project-root/
    .windsurf/
        refactoring/
            plans/
                current-refactor.json        # Active refactoring plan
                    # Scope definition
                    # Phase breakdown
                    # Progress tracking

                migration-plan.json          # Migration roadmap
                    # Source patterns
                    # Target patterns
                    # Rollback strategy

            phases/
                phase-1-analysis.json        # Analysis phase
                    # Files affected
                    # Dependencies mapped
                    # Risk assessment

                phase-2-preparation.json     # Preparation phase
                    # Tests added
                    # Backups created
                    # Rollback tested

                phase-3-execution.json       # Execution phase
                    # Change sequence
                    # Validation checkpoints
                    # Progress tracking

                phase-4-verification.json    # Verification phase
                    # Test results
                    # Performance comparison
                    # Documentation updates

            checkpoints/
                pre-refactor-snapshot.json   # Pre-refactor state
                    # File hashes
                    # Test baselines
                    # Metric baselines

                progress/
                    checkpoint-001.json      # Progress checkpoints
                        # Completed changes
                        # Pending changes
                        # Issues encountered

            rollback/
                rollback-plan.json           # Rollback strategy
                    # Rollback triggers
                    # Recovery steps
                    # Verification process

                backups/
                    README.md                # Backup index
                        # File locations
                        # Restore procedures
```

## Refactoring Features

### Planning
- Impact analysis
- Dependency mapping
- Risk assessment
- Phase definition

### Execution
- Atomic changes
- Progress tracking
- Checkpoint creation
- Validation at each step

## Configuration Steps

1. **Analyze Scope**
   - Map affected files
   - Identify dependencies
   - Assess risks

2. **Create Plan**
   - Define phases
   - Set checkpoints
   - Plan rollback

3. **Execute with Cascade**
   - Apply changes incrementally
   - Validate at checkpoints
   - Track progress

4. **Verify Completion**
   - Run all tests
   - Compare performance
   - Update documentation

## Success Criteria

- All tests passing
- Zero runtime regressions
- Completed in days vs weeks
