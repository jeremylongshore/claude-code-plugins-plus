# j-rig — Skill Refiner

The **Skill Refiner**: an eval-guided improvement loop for `SKILL.md` files,
delivered as a Claude Code plugin. Second product in the Intent Solutions
agent-rig stack — **J-Rig Skill Binary Eval (test) → Skill Refiner (improve) →
Rollout Gate (ship)**.

The refiner proposes safe, minimal, bounded edits (add / delete / replace ops)
to a skill and accepts an edit **only if a held-out eval score strictly
improves** with no regression on any other case. It is a **thin wrapper** over
the published [`@intentsolutions/refiner`](https://www.npmjs.com/package/@intentsolutions/refiner)
package (the `j-rig refine` command group in
[`@intentsolutions/jrig-cli`](https://www.npmjs.com/package/@intentsolutions/jrig-cli));
it does not reimplement refiner logic.

## Install

In Claude Code:

```
/plugin install j-rig@claude-code-plugins-plus
```

Then install the CLI the subcommands wrap:

```bash
npm install -g @intentsolutions/jrig-cli   # gives you the `j-rig` command
```

## Subcommands

Each `/j-rig` subcommand is a thin wrapper over a `j-rig refine` verb. Run them
against a skill directory (the folder containing the `SKILL.md`).

| Subcommand | Underlying CLI verb | Purpose |
| --- | --- | --- |
| `refine bootstrap <skill-dir>` | `j-rig refine bootstrap` | Synthesize a held-out eval set. |
| `refine score <skill-dir>` | `j-rig refine score` | Score via `j-rig eval` (Haiku/Sonnet; never Opus). |
| `refine propose <skill-dir>` | `j-rig refine propose` | Propose one bounded edit; shadow-validate it. |
| `refine promote <skill-dir>` | `j-rig refine apply` | Apply an accepted proposal → new version (human-gated). |
| `refine status <skill-id>` | `j-rig refine status` | Show the refiner store + event log. |

## The 3-layer cost-tiered hooks (sinker · line · hook)

| Layer | Event | Fires | Mechanism | Cost |
| --- | --- | --- | --- | --- |
| **Sinker (L1)** | `PostToolUse: Edit\|Write` | on any SKILL.md edit | deterministic `validate-skillmd` Tier-2 check | **$0** |
| **Line (L2)** | `Stop` | at end of turn | capture rollouts → background refiner after N | **$** |
| **Hook (L3)** | `PreToolUse: Bash` | before `git commit`/`push` on a staged SKILL.md | agentic gate, **can block** via exit 2 | **$$** (rate-limited) |

**Why L3 is `PreToolUse:Bash`:** only `PreToolUse` is in the Anthropic hooks
"Can block" allowlist. `PostToolUse:Bash` fires after the commit already ran and
cannot prevent it. The L3 Opus gate is rate-limited (default 5 min) to control
cost.

See [`skills/j-rig/SKILL.md`](skills/j-rig/SKILL.md) for the full reference.

## License

Apache-2.0 © Jeremy Longshore / Intent Solutions
