# intent-labs-pack

Public home for the Intent Solutions **labs skills** that the nightly
j-rig skill-eval roster needs to check out in CI:

| Skill | Role |
| --- | --- |
| `audit-tests` | 7-layer test-suite auditor (diagnostic only) |
| `validate-skillmd` | Four-tier SKILL.md validator / grader |

## Why this pack exists

These skills previously lived only under `~/.claude/skills` on founder
machines. A CI runner cannot check that path out, so they could not join
the signed nightly roster on `labs.intentsolutions.io`. Publishing them
here is the product decision for bead `bd_000-projects-184o.7` (option a —
marketplace publish, not a dedicated repo).

`skill-creator` already has a marketplace home under
`plugins/skill-enhancers/skill-creator` and is **not** duplicated here.

## Install

```text

/plugin install intent-labs-pack@claude-code-plugins-plus

```

Or install the individual skills from this pack's `skills/` directory.

## Nightly roster

j-rig `eval-roster/roster.json` pins skills by path under this repo. After
merge, the roster pin is advanced and the two skills are added alongside
the existing marketplace pack skills.

## License

MIT — Jeremy Longshore / Intent Solutions.
