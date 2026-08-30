# contributing-clanker

> Portable, least-authority workflow for respectful AI-assisted OSS contributions.

`contributing-clanker` helps contributors check upstream policy, avoid duplicate
work, prepare evidence, and publish only what a human has reviewed. It is
model-agnostic: Claude-specific helper agents are optional adapters, not runtime
requirements.

## Trust model at a glance

The plugin exposes three separately invoked skills:

| Skill | Default authority | What it can do |
|---|---|---|
| `contribute` | Read-only | Audit issues, pull requests, policies, and readiness |
| `contribute-prepare` | Local writes | Create explicitly scoped state/worktrees, drafts, tests, and gate evidence |
| `contribute-publish` | Reviewed GitHub write | Perform one exact action after fresh human approval |

Installing the plugin creates no state, clones, hooks, credentials, background
jobs, or GitHub objects. Invoking `contribute` also performs no writes.

## Thirty-second start

Start with the safe audit:

```text
/contribute qualify owner/repository#123
```

The result is `ready-to-prepare`, `needs-information`, `wait`, or `skip`, with
evidence and the next safe action.

If preparation is appropriate, choose two absolute paths inside your own
profile or workspace and initialize them explicitly:

```bash
export CONTRIBUTE_STATE_DIR=/your/profile/state/contributing-clanker
export CONTRIBUTE_WORKSPACE_DIR=/your/profile/worktrees/contributions

bash <contribute-prepare-skill-dir>/scripts/setup.sh \
  --state-dir "$CONTRIBUTE_STATE_DIR" \
  --workspace-dir "$CONTRIBUTE_WORKSPACE_DIR"
```

Then invoke `contribute-prepare`. It produces a review packet and states that no
external action occurred. Invoke `contribute-publish` separately only when you
want to review and approve a specific GitHub action.

## Why the split exists

Community skill installers should not inherit another operator's home layout,
persistent state, agents, credentials, or approval identity. The split makes the
authority boundary visible and enforceable:

- audit works without persistent state;
- preparation has no default paths and no GitHub mutation authority;
- publication cannot install dependencies or write local tracking state;
- authentication proves identity but never substitutes for approval; and
- repository instruction files apply only inside that repository.

The design responds directly to the Hermes interoperability report in
[issue #1321](https://github.com/jeremylongshore/tons-of-skills-marketplace/issues/1321).

## Local preparation model

After explicit setup, the chosen state directory contains:

```text
candidates/   Markdown records for selected issues
research/     Cached repository-policy dossiers
user-gates/   Optional user-authored deterministic gates
check-runs/   Gate evidence
test-logs/    Local test output
profile.md    User-selected languages and constraints
log.jsonl     Append-only local workflow events
```

The chosen workspace directory contains only repositories the user explicitly
selected. Bundled gates are read from the installed skill package; they are not
copied into a hidden home directory.

## Publication boundary

Before any comment, issue, branch push, or pull request, `contribute-publish`
must show:

- exact repository and target;
- complete content or refspec;
- commit SHA and changed files;
- tests, linters, and gate evidence; and
- CLA/DCO, AI disclosure, warnings, and overrides.

Fresh approval applies to that exact action only. The skill does not merge,
force-push, approve reviews, bypass repository rules, or delete branches without
a separate explicit review and approval.

## Requirements

- `git`
- `jq`
- GitHub CLI (`gh`) authenticated through the user's normal credential store
- Bash for the optional deterministic preparation scripts
- the target repository's own build/test dependencies, only when preparation is
  explicitly requested

No token value should be placed in plugin state or prompts.

## Verification

From the marketplace repository:

```bash
python3 scripts/validate-skills-schema.py --marketplace \
  plugins/community/contributing-clanker/skills/contribute/SKILL.md \
  plugins/community/contributing-clanker/skills/contribute-prepare/SKILL.md \
  plugins/community/contributing-clanker/skills/contribute-publish/SKILL.md

python3 scripts/validate-unicode-hygiene.py \
  plugins/community/contributing-clanker/skills/contribute/SKILL.md \
  plugins/community/contributing-clanker/skills/contribute-prepare/SKILL.md \
  plugins/community/contributing-clanker/skills/contribute-publish/SKILL.md
```

The preparation runtime includes focused shell regression tests under
`skills/contribute-prepare/scripts/test-*.sh`.

## Compatibility

The core contract is host-neutral. Hosts may load the optional definitions in
`contribute-prepare/agents/`, or perform those bounded roles inline. No
Claude-specific command, path, memory store, or subagent is required.

## License

MIT. Source project: https://github.com/jeremylongshore/contributing-clanker
