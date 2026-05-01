---
title: "The Rubric Sits On Top Of The Spec: A Schema Validator Postmortem"
description: "Postmortem on a schema validator debacle: when a stricter enterprise rubric is built on top of a permissive open spec, the rubric must be additive, never the spec's floor."
date: "2026-04-28"
tags: ["architecture", "claude-code", "release-engineering", "devops", "schema-design"]
featured: false
---
When you author a stricter enterprise rubric on top of a permissive open spec, the rubric must sit additive on top of the spec — not replace its required-field set with the spec's floor. Demoting required-field errors to warnings to "realign with the underlying spec" breaks the marketplace gate it was built to enforce.

That sentence is the entire lesson from a multi-hour debacle on April 28th. The rest of this post explains how a confident plan to "realign the validator to Anthropic's authoritative sources" tore down a working enterprise rubric, what got caught mid-flight, what survived the rebuild, and the NON-NEGOTIABLES section now pinned at the top of `SCHEMA_CHANGELOG.md` so it doesn't happen again.

## Background: the IS rubric vs Anthropic's spec

Two specs were in play.

Anthropic's published skills spec at `code.claude.com/docs/en/skills` is intentionally permissive. Almost every frontmatter field is optional. Even `description` is only "recommended" — if absent, the loader falls back to the first paragraph of markdown. The spec is an interpreter contract, not a quality bar. Its job is to say what Claude Code will accept without erroring out.

The Intent Solutions enterprise rubric — which scores skills published to our marketplace — sits on top of that interpreter contract. Its 8-field `ALWAYS_REQUIRED` set is the original IS standard for marketplace-quality skills:

```python
# scripts/validate-skills-schema.py — the original 8-field set
ALWAYS_REQUIRED = {
    'name',
    'description',
    'allowed-tools',
    'version',
    'author',
    'license',
    'compatibility',   # was 'compatible-with' before this PR
    'tags',
}
```

This set isn't arbitrary. `name` and `description` are the Anthropic-spec basics. `version`, `author`, `license` are tracking metadata — required so the marketplace can attribute, version, and license-check at scale. `allowed-tools` makes the skill's tool surface explicit. `compatibility` is free-text describing where the skill is designed to run. `tags` powers discovery.

At marketplace tier the validator emits **errors** for any of these missing — not warnings. That's the marketplace gate. A skill that fails the gate doesn't ship.

This is the architecture that worked. It is also the architecture that got demolished, then partly rebuilt, in a single afternoon.

## The dance

The day started with a real problem: existing IS skills used a field called `compatible-with` that takes a CSV list of platforms (`claude-code, claude-desktop, ...`). Anthropic's actual skills spec uses a free-text field called `compatibility`. We were diverging from the published spec on a field name and shape, and that needed fixing.

A small autonomous task — rename the field, write a migration helper, deprecate the old name — turned into something much bigger. The plan that landed in the editor was titled "Realign skill validator + master spec to Anthropic's authoritative sources." The framing was that the IS rubric had drifted into "pure inventions" that "don't exist in any Anthropic spec or open standard," and the credible move was to bring the rubric back to the spec's floor.

So the validator's `ALWAYS_REQUIRED` got rewritten down to a 2-field minimum:

```python
# The wrong direction — schema 3.0.0
ALWAYS_REQUIRED = {'name', 'description'}

# version, author, license, allowed-tools, compatibility, tags
# all moved to MARKETPLACE_RECOMMENDED — which warns, not errors
```

And the marketplace tier's presence-check logic was relaxed from errors to warnings — under the reasoning that "the underlying Anthropic spec marks these optional, so erroring is over-specification."

That isn't realignment. It's the rubric replacing itself with the spec's floor.

## Why working off summaries failed

The deeper failure mode was the input: the plan was built from doc summaries, not from `code.claude.com/docs/en/skills` line by line. A summary of Anthropic's spec emphasizes its permissiveness — "everything optional, name and description recommended, the rest situational." That's accurate as a one-line description of the interpreter contract. It's also exactly the wrong frame for deciding what the marketplace rubric should require.

Three things get lost in summarization:

1. **The spec's job vs the rubric's job.** Anthropic's spec answers "will this load?" The IS rubric answers "is this fit to publish to a marketplace?" These are different questions with different correct answers. A summary that flattens both into "the requirements are X" hides that they have different audiences.
2. **The ladder beneath each field.** `version` is "optional" in Anthropic's spec because the loader doesn't need it. It's "required" in the IS rubric because the marketplace needs it for changelog tracking, dependency resolution, and conflict reporting. A summary that says "version is optional" is technically correct in the loader's frame and entirely wrong in the marketplace's frame.
3. **The conditional rules that don't fit a table.** Anthropic's spec documents `argument-hint` as a "no" in the required column, but the spec body says it's only meaningful when the skill is user-invocable — `user-invocable: false` makes the hint irrelevant because the skill is hidden from the `/` menu. A summary that flattens this to "argument-hint: optional" loses the conditional that the validator needs to encode. The body of the spec carries the rules; the table only carries the labels.

The corrective rule that came out of this is short. **Read primary source material line by line for any change to the required-fields set.** Summaries are fine for orientation; they're never enough to drive an architectural decision about what the rubric demands.

There's a meta-failure pattern under this one too. Summaries that come from a previous Claude session look authoritative because they're well-organized and quote the right field names. They are still summaries. The cost of re-reading a 4,000-word spec doc is roughly twenty minutes; the cost of building a multi-hour reframe on a summary that elided the conditional rules is the rest of the afternoon. The asymmetry is not subtle. Read the source.

## Caught mid-flight

The reframe got partway through the codebase before I called it. By that point:

- Validator was at schema 3.0.0 with the 2-field `ALWAYS_REQUIRED`.
- Master spec doc 6767-b had been bumped to v3.0.0 with a "name + description are the standard" framing.
- `frontmatter-spec.md` had been rewritten to teach the new minimum.
- Skill template had been pared down.
- The `compatibility` migration was in. The `when_to_use` non-deprecation was in. The YAML-list parsing for `allowed-tools` was in. The `arguments`, `paths`, `shell`, and `effort: xhigh` field acceptance was in.

Some of those were real bugs against Anthropic's spec — places where the validator was rejecting things Anthropic's docs explicitly accept. Those are the "spec-compliance bug fixes" that should land. The rest of the diff was the architectural reframe: the 8-field set torn down to 2, and marketplace tier presence checks demoted from errors to warnings.

The rebuild kept the bug fixes and reverted the reframe.

## What the rebuild looks like

Here's the validator after the restoration — schema 3.3.1, the version that shipped in PR #611:

```python
# scripts/validate-skills-schema.py — restored 8-field set, schema 3.3.1
SCHEMA_VERSION = "3.3.1"

ALWAYS_REQUIRED = {
    'name',
    'description',
    'allowed-tools',
    'version',
    'author',
    'license',
    'compatibility',   # the kept rename — was 'compatible-with'
    'tags',
}

DEPRECATED_FIELDS = {
    'compatible-with': "Use `compatibility` (free-text per AgentSkills.io spec) "
                       "instead. Example: `compatibility: Designed for Claude Code`.",
}
```

And the marketplace tier presence-check logic, restored to the strict form:

```python
def check_required_fields(frontmatter, tier):
    """At marketplace tier, missing ALWAYS_REQUIRED fields are ERRORS, not warnings."""
    missing = ALWAYS_REQUIRED - set(frontmatter.keys())
    if not missing:
        return []

    if tier == 'marketplace':
        return [Error(f"Missing required field: {field}") for field in missing]
    elif tier == 'standard':
        return [Warning(f"Missing recommended field: {field}") for field in missing]
```

Standard tier still warns — it mirrors Anthropic's spec floor for skills that aren't going to the IS marketplace. Marketplace tier errors, because the marketplace gate has a job to do.

What survived from the failed direction:

- `compatibility` replaces `compatible-with` as the canonical free-text field. CSV-platform lists are migrated automatically by `batch-remediate.py --migrate-compatible-with`.
- `when_to_use` is **not** deprecated. It's a documented Anthropic field that gets concatenated into the description for skill listings. Earlier validator versions had marked it deprecated; that was wrong.
- `allowed-tools` and `arguments` accept either a space-separated string or a YAML list. Anthropic's spec documents both forms; the validator now parses both.
- `paths`, `shell`, and `arguments` are now first-class accepted fields with type validation.
- `effort: xhigh` is in the value-validation allow-list (along with `low`, `medium`, `high`, `max`, `inherit`).
- Conditional-field rules: `argument-hint` no longer warns when `user-invocable: false` (skill is hidden from the `/` menu, so an autocomplete hint is irrelevant). Subagent fork context defaults to general-purpose if no `agent` is specified, matching Anthropic's documented behavior.

These are all real spec-compliance fixes. They land cleanly without touching the rubric's required-field set. The test for "is this a bug fix or an architectural change" is exactly that: does the diff modify what the rubric demands, or does it modify how the rubric reads documented Anthropic fields? If the answer is "how it reads," ship it. If the answer is "what it demands," stop and get approval.

A concrete example. The `allowed-tools` YAML-list parsing fix:

```python
# Before: only space-separated string was accepted
def parse_allowed_tools(value):
    return value.split(',')

# After: both Anthropic-canonical forms — string OR YAML list
def parse_allowed_tools(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        # Anthropic's spec: space-separated, comma is a typo we tolerate
        return value.replace(',', ' ').split()
    raise ValueError(f"allowed-tools must be string or list, got {type(value)}")
```

This is a bug fix. The rubric still requires `allowed-tools` at marketplace tier; the rubric still validates the resulting list against the known-tool registry; the rubric's contract is unchanged. What changed is that the validator now accepts the second form Anthropic's spec documents. Past validator versions would have errored on `allowed-tools: [Read, Edit, Bash]` even though the spec calls that out as canonical. That's a spec-compliance bug, autonomously fixable.

Compare to demoting marketplace-tier presence checks from errors to warnings. Same number of lines changed, same diff shape, completely different category. The first changes how a documented field is read. The second changes what the rubric demands. The first is a bug fix. The second is the dance.

## What the rubric does on top of the spec

The right mental model is two layers:

```
+---------------------------------------------------+
|  IS Marketplace Rubric (additive — strict)        |
|  - 8-field ALWAYS_REQUIRED set                    |
|  - Marketplace tier: missing = ERROR              |
|  - 100-point quality grade                        |
|  - Deep-eval dimensions                           |
+---------------------------------------------------+
|  Anthropic Skills Spec (interpreter — permissive) |
|  - name, description recommended                  |
|  - everything else optional                       |
|  - documented field types and value sets          |
|  - conditional-field semantics                    |
+---------------------------------------------------+
```

The rubric is **additive** on top of the spec. Every field the spec defines is honored — same names, same types, same value sets. The rubric adds three things:

1. **A required-field set for marketplace publication.** Tracking metadata (`version`, `author`, `license`) and discovery metadata (`tags`) are demanded because the marketplace needs them. The spec doesn't care; the marketplace does.
2. **Stricter validation for fields the spec accepts loosely.** A 1500-char description limit. Voice-and-tense regex enforcement. License-string format checks.
3. **Polish recommendations** that don't fail the build but show up in the grade — examples in the body, references-section structure, command-block formatting.

Because the rubric is additive, every skill that passes the rubric also passes the spec. The reverse isn't true — a spec-valid skill can fail the rubric, and that's the point. That's what "marketplace quality" means.

The reframe broke this layering by trying to push the rubric down to the spec's floor. A 2-field rubric would have meant any spec-valid skill passes the marketplace gate. There would be no gate.

## NON-NEGOTIABLES

The postmortem produced six rules that are now pinned at the top of `000-docs/SCHEMA_CHANGELOG.md`. They exist specifically to make this dance impossible to repeat:

```markdown
## NON-NEGOTIABLES (read before touching the validator)

1. ALWAYS_REQUIRED is the IS enterprise 8-field set:
   {name, description, allowed-tools, version, author, license,
    compatibility, tags}.
   Do NOT reduce it. Do NOT reframe as "marketplace polish."

2. Marketplace tier = ERRORS for missing required fields, not warnings.
   Demoting required-field errors to warnings breaks the marketplace gate.

3. The IS rubric SITS ON TOP of Anthropic's spec. Anthropic's spec is
   intentionally permissive (everything optional); the IS marketplace is
   intentionally strict. Don't try to "realign" the IS rubric to
   Anthropic's spec floor — that's the dance from 2026-04-28.

4. Tracking metadata (version, author, license) is REQUIRED at
   marketplace tier. Not optional polish. Reframing them as "tracking
   recommendations" or "polish" is the bad direction.

5. Bug fixes that bring the validator into spec compliance are OK to
   apply autonomously (e.g., accepting YAML lists for allowed-tools,
   fixing conditional-field rules). These are technical corrections,
   not architectural changes.

6. Architectural changes need explicit approval BEFORE the change lands.
   "Architectural" = required-fields set, tier model, error vs warning
   semantics, source-classification labels.
```

The split between rules 5 and 6 is the operational core. Spec-compliance bug fixes are fine to ship autonomously — the YAML-list parsing, the `effort: xhigh` allow-list, the conditional-field rules. They don't change the rubric's contract; they fix the validator's interpretation of fields it already validates.

Architectural changes — the required-fields set, the error/warning semantics, the tier model — need approval before code lands. These are decisions about what the rubric *is*, not about how it parses.

The global `~/.claude/CLAUDE.md` now has a "Claude Skills SOP" section that points directly at `SCHEMA_CHANGELOG.md` and lists the canonical sources by path:

```markdown
| Validator   | scripts/validate-skills-schema.py    |
| Schema log  | 000-docs/SCHEMA_CHANGELOG.md         |
| Master spec | 000-docs/6767-b-SPEC-DR-STND-...md   |
| Skill-creator | ~/.claude/skills/skill-creator/    |
| Anthropic primary | code.claude.com/docs/en/skills |
| AgentSkills.io   | agentskills.io/specification    |
```

The instruction is explicit: read primary sources, not summaries, before any required-fields-set change.

## Tradeoffs of additive layering

Additive layering isn't free. Three real costs:

**Coupling to Anthropic's spec evolution.** When Anthropic adds a field, the IS rubric has to decide whether to honor it, whether to add validation on top, and whether it should be required at marketplace tier. The migration from `compatible-with` to `compatibility` is the canonical example — Anthropic's choice of name and shape forced an IS rename and a migration helper. Sitting on top means moving when the foundation moves.

**Rubric inflation pressure.** Every time someone says "this field would be useful at the marketplace tier," the required-fields set wants to grow. Eight fields is already at the edge of what skill authors will accept without complaint. Adding a ninth needs a real reason. The SCHEMA_CHANGELOG entry for any change to `ALWAYS_REQUIRED` should answer "why does the marketplace fail without this field?" — not "wouldn't it be nicer if we had it?"

**Migration debt.** Renaming a required field — even with a deprecation alias and a migration helper — is expensive across 3,385 public-repo skill files. The `compatible-with` → `compatibility` migration is tracked as its own follow-up PR for exactly this reason. Each rename burns a release on bulk migration.

The alternative — a flat rubric that mirrors the spec's permissive shape — is cheaper to maintain and useless as a quality gate. The cost of additive layering is the price of having a marketplace at all.

There's a fourth cost worth naming: **cognitive load on skill authors.** A skill author who reads Anthropic's spec and a separate IS rubric has to hold both in their head. If the rubric is well-layered, this is fine — same field names, same value sets, just stricter requirements. If the rubric is poorly layered (renaming fields, redefining types), authors hit constant friction. The `compatible-with` → `compatibility` migration is the worst-case version of this: an IS-only field name that didn't match the spec, costing every skill author who learned both standards a moment of "wait, which one is which?" The rebuild is intentionally trying to bring the rubric closer to spec-canonical names everywhere it can, while keeping the strictness of the required-fields set intact.

## Versions and what landed

PR #611 squash-merged at commit `4dee593c7`, closing issue #610. The version trail tells the rebuild story:

- **3.0.0** — wrong direction. 2-field `ALWAYS_REQUIRED`, marketplace warnings instead of errors. Not shipped to anyone.
- **3.1.0** — partial reframe with `when_to_use` non-deprecation and field additions. Still on the wrong path for required-fields semantics.
- **3.2.0** — reframe artifacts cleaned up but still permissive at the marketplace tier.
- **3.3.0** — restoration. 8-field `ALWAYS_REQUIRED` back, errors at marketplace, all the kept technical fixes.
- **3.3.1** — `${CLAUDE_EFFORT}` substitution variable added to YAML allow-list, `argument-hint` conditional logic fixed for `user-invocable: false` and `disable-model-invocation: true`. The version that shipped.

Six files changed: 1,312 insertions, 203 deletions. New top-level doc: `000-docs/SCHEMA_CHANGELOG.md` with the NON-NEGOTIABLES section, the post-mortem narrative, and per-version entries from 3.0.0 through 3.3.1. The CHANGELOG.md got a single 4.29.2 entry that consolidated the failed-direction noise from earlier in the day into one clean release note.

## Also shipped

Several tracks ran in parallel that day. Quick summaries:

**SOW restructure for the Kobiton MCP plugin engagement.** Three milestones reorganized around the SOW's five evaluation criteria — usability/UX, suitability, setup/integration, functional completeness, spec/schema/standards. New labels (`sow:usability`, `sow:setup`, `sow:spec-standards`, etc.) tag every existing fork-audit issue (#1–9) and upstream filing (#11–20) so the SOW criterion each issue serves is explicit. Three IS demo PRs (#13–17) were filed to demonstrate the proposed schema/standards changes against real fork code.

**Kobiton fork audit and upstream governance.** The original validator-rubric framing in Kobiton issue #1 had been edited mid-debacle with the wrong "spec realignment" language. After the restoration, those edits got reverted to the enterprise-required-8-fields framing. A new governance audit on the upstream Kobiton repo (issue #21) covers fork-vs-upstream divergence and the contribution path back.

**CCA cohort intake.** Thirteen CCA applicants ran through parallel background-check agents — one agent per applicant, all dispatched at once. Twenty CRM populated with 13 People, 1 Opportunity, and 14 Notes from the runs. This is the kind of work parallel agents actually shine at: independent IO-bound tasks, no shared state, results aggregated in a CRM.

**Twenty SMTP diagnosis.** A separate side track — Twenty's email-send was failing intermittently. Root cause turned out to be a misconfigured `MESSAGE_QUEUE_TYPE` interacting with the SMTP worker pool. Diagnosis ticket filed; fix queued for the next sprint.

**Repo-sweep + snapshot tag.** End-of-day repo housekeeping — stale branches pruned, security scan clean, snapshot tag cut on `claude-code-plugins-plus-skills` to mark the post-restoration state.

## What I'd tell my past self

If the small-scope task is "rename a field," do not let it expand into "realign the rubric to the spec." Those are different decisions, with different evidence requirements, made by different mechanisms. Field renames can be autonomous. Required-field-set changes need primary-source verification and explicit approval — even when the framing seems credible, even when the summary makes it sound like alignment.

The marketplace gate exists because some quality bar above the spec floor is worth enforcing. The whole job of the rubric is to be stricter than the spec it sits on. When the rubric and the spec are saying the same thing, the rubric isn't doing anything.

The other thing I'd tell past me: when a plan title is "realign X to Y's authoritative sources," the framing itself is doing work. "Authoritative" sounds like the source of truth for *both* layers. It isn't. Anthropic's spec is the authoritative source of truth for the loader contract. The IS rubric is the authoritative source of truth for the marketplace gate. Realignment between two layers that legitimately disagree on requirements is not a goal; correct layering is.

The NON-NEGOTIABLES section exists to make this layering visible at the top of the file every time someone opens `SCHEMA_CHANGELOG.md` to plan a change. It's a guardrail, not a manifesto — short enough to read in thirty seconds, specific enough to refuse the dance.

## Related Posts

- [Design Tokens and Validator Parity: Marketplace Foundations](/posts/design-tokens-and-validator-parity-marketplace-foundations/) — the marketplace validator's role in the broader design-token system.
- [Nuclear Option Day: Validator Rewrite Across 414 Plugins](/posts/nuclear-option-day-validator-rewrite-414-plugins/) — when validator changes do warrant a bulk rewrite, and how to scope it.
- [Debugging a Critical Marketplace Schema Validation Failure](/posts/debugging-critical-marketplace-schema-validation-failure/) — earlier marketplace-validator failure mode and the gate's recovery path.

