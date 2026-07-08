# Tests

These are **behavioral evals of the PortalJS agentic skills**, not unit tests. The skills are markdown (`.claude/commands/*.md`); what matters is whether a realistic user prompt makes the right skill fire. So the tests run the real agent and inspect what it does.

## skill-triggering

Checks, per skill: *does a **naive** prompt — one that never names the skill — trigger the correct skill?* This is what guards against the failure modes that silently break skills: a vague or overlapping `description`, or a skill that isn't registered in the plugin manifest.

```text
tests/skill-triggering/
  prompts/<skill>.txt   # a realistic, indirect user prompt per skill
  run-test.sh           # run one (skill, prompt) → PASS/FAIL
  run-all.sh            # run them all and summarize
```

### How it works

`run-test.sh <skill> <prompt-file>` runs the prompt headlessly through Claude Code with the PortalJS skills loaded, captures the JSON transcript, and asserts the expected skill's `Skill` tool-call appears:

```bash
claude -p "<prompt>" --plugin-dir <repo-root> --max-turns 2 --output-format stream-json
# PASS iff the transcript contains a Skill call for <skill>
```

`--max-turns` is intentionally low: we only need the **skill invocation** to show up, not for the skill to finish (some skills scaffold files, deploy, or install). Each run executes in a throwaway `mktemp` directory so nothing touches your working tree.

### Requirements

- The `claude` CLI on `PATH`
- `ANTHROPIC_API_KEY` set

These run the live model, so they **cost tokens and are non-deterministic** — run them **manually**, not as gating CI:

```bash
tests/skill-triggering/run-all.sh
# or one skill:
tests/skill-triggering/run-test.sh portaljs-new-portal tests/skill-triggering/prompts/portaljs-new-portal.txt
# robustness check on a smaller model:
CLAUDE_MODEL=claude-haiku-4-5 tests/skill-triggering/run-all.sh
```

When you add or rename a skill, add a matching `prompts/<skill>.txt` and an entry in `run-all.sh`'s `SKILLS` list — and make sure the skill is registered in `.claude-plugin/plugin.json`.
