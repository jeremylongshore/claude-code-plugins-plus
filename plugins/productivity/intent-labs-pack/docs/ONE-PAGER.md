# intent-labs-pack

**Public home for Intent Solutions labs skills that the nightly signed eval roster must check out.**

## Problem

`audit-tests` and `validate-skillmd` lived only under `~/.claude/skills`. CI cannot see that path, so the dogfood loop never graded our own gates.

## Solution

Ship both skills as a productivity pack on the marketplace, with j-rig eval-specs, so one git pin feeds the nightly roster.

## W5

| | |
| --- | --- |
| **Who** | Nightly roster + engineers dogfooding IS tooling |
| **What** | `audit-tests` + `validate-skillmd` pack |
| **When** | Install anytime; roster runs ~03:30 UTC |
| **Where** | Claude Code marketplace + j-rig CI |
| **Why** | Same surface we grade; one pin, proven roster mechanics |

## Stack

- Claude Code plugins
- j-rig eval-spec.yaml
- `@intentsolutions/audit-harness` (audit-tests enforcement target)
