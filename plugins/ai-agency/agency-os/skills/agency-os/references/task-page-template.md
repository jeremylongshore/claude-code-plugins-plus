<!--
Rendered into every task page body when created via /agency-os suggest or /agency-os add-subtask.
Toggleable H2 headings (Notion's `is_toggleable: true`) are used so the DB grid stays clean and
the operator opens what they need on click. If the MCP path can't set is_toggleable, fall back
to plain H2 — the operator can toggle blocks manually.
-->

> 🚀 **Launch this task**
>
> Paste in Claude Code: `/agency-os start {{TASK_ID}}`

## Description

{{NOTES}}

(Freeform context. What needs to be done, why, acceptance criteria. Link any docs/skills the
agent should read first. If the action is "run skill X", say so. This section is loaded into
every kickoff brief — keep it tight.)

## Subtasks
<!-- Linked DB view: filter Parent Task = this task, sort Created asc.
     Hidden if no subtasks exist; appears the moment add-subtask runs. -->

## Discussion log
<!-- Folded by default. The skill appends entries via /agency-os log <id> "<entry>".
     Each entry is a level-3 heading (### YYYY-MM-DD — short topic), then the body.
     Only the most recent entry is loaded into kickoff briefs; older entries are
     referenced by date and loaded on demand via
     /agency-os show <id> --section discussion --entry <date>. -->

## Done log
<!-- Folded by default. For one-time tasks, gets a single ### entry on close.
     For recurring tasks, gets one ### entry per occurrence (the task itself
     loops back to To-Do with Last Done updated). -->

## Related

- Corpus: [→ {{CORPUS_NAME}}]({{CORPUS_URL}})
- General guidance: [→ Guidance]({{GUIDANCE_URL}})
{{PARENT_LINE}}
