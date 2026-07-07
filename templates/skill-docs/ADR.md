# ADR: <skill-slug> — <short decision title>

> In this repo, ADRs are filed per skill in `000-docs/` as `NNN-AT-DECR-<skill-slug>.md`
> (next free `NNN`). In your own plugin, keep it at `docs/ADR.md` — the sync mirrors it as-is.

**Author:** <your name>
**Date:** <YYYY-MM-DD>
**Status:** Proposed | Accepted

## Context

_What situation forced a decision — the constraints, the PRD requirement it serves,
what breaks if you do nothing. 1–2 paragraphs._

<Describe the forces at play.>

## Decision

_The choice, stated as a decision ("We use X to do Y"), not a description of the code._

<State the decision.>

## Alternatives considered

_2–3 alternatives with why each was rejected. If nothing was rejected, no decision was made._

| Alternative     | Why rejected      |
| --------------- | ----------------- |
| <alternative 1> | <specific reason> |
| <alternative 2> | <specific reason> |

## Consequences

_Both directions. A decision with no negative consequences is a description, not a decision._

**Positive:**

- <what gets better>

**Negative / accepted tradeoffs:**

- <what gets worse or harder, and why that's acceptable>

## Tool-permission scope

_Which `allowed-tools` the skill declares and why each one is needed. Least privilege:
`Bash(git:_)`beats bare`Bash`. If a tool can't be justified here, remove it from the
frontmatter.\*

| Tool           | Why it's needed |
| -------------- | --------------- |
| <Read>         | <reason>        |
| <Bash(npm:\*)> | <reason>        |
