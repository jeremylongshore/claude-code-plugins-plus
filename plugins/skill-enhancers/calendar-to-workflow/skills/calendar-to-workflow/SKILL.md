---
name: calendar-to-workflow
description: |
  Converts calendar events and schedules into Claude Code workflows, meeting prep
  documents, and standup notes. Use when the user mentions calendar events, meeting
  prep, standup generation, or scheduling workflows. Trigger with phrases like
  "prep for my meetings", "generate standup notes", "create workflow from calendar",
  or "summarize today's schedule".
allowed-tools: Read, Write, Edit, Bash(git:*), Bash(gh:*), Bash(chmod:*), Glob, Grep
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex
tags: [calendar, automation, meetings, productivity, workflow]
---

# Calendar to Workflow

Automate meeting preparation, standup generation, and workflow creation from calendar data.

## Overview

This skill transforms calendar events and scheduling data into actionable Claude Code workflows. Rather than manually reviewing your calendar and preparing for each meeting, this skill reads calendar exports (ICS files, JSON feeds, or pasted event details) and produces structured outputs: meeting briefings with participant context, standup notes summarizing yesterday's activity, and repeatable workflow scripts that integrate calendar triggers with development tasks.

The skill bridges the gap between time management and development workflows. It understands meeting types (standup, sprint planning, 1:1, design review) and tailors its output accordingly, pulling in relevant repository activity, recent commits, and open PRs to provide full context for each event.

## Instructions

1. **Provide calendar data** in one of these formats:
   - Paste raw ICS/iCal content directly into the conversation
   - Point to an `.ics` file on disk: "read my calendar export at `~/calendar.ics`"
   - Describe events manually: "I have a standup at 9am, sprint planning at 10am, and a 1:1 with Sarah at 2pm"

2. **Specify the desired output** by telling Claude what you need:
   - "Prep for today's meetings" -- generates a briefing document for each event
   - "Create standup notes from yesterday" -- summarizes git activity and calendar events
   - "Build a weekly workflow" -- creates a repeatable workflow script

3. **Add context** to improve the output:
   - Mention the repository or project: "for the payments-api repo"
   - Specify participants: "Sarah is the engineering manager"
   - Note priorities: "focus on the deployment blockers"

4. **Review and refine** the generated output. The skill produces Markdown documents or shell scripts that you can edit, commit, or execute directly.

## Output

The skill produces one or more of the following depending on the request:

- **Meeting Briefing Document** (Markdown): For each meeting, includes the event title, time, participants, agenda items inferred from context, relevant recent commits or PRs, and suggested talking points.
- **Standup Notes** (Markdown): A formatted summary covering what was done yesterday (from git log and calendar), what is planned today (from upcoming events), and any blockers identified from open issues or failing CI.
- **Workflow Script** (Bash/Markdown): A repeatable workflow that can be triggered on a schedule, combining calendar checks with development tasks like running tests, updating dashboards, or posting summaries to Slack.

## Examples

### Example 1: Daily Meeting Prep

**User:** "I have a sprint planning at 10am with the backend team and a design review at 2pm. Prep briefings for both."

The skill will:
1. Create a sprint planning briefing listing open sprint issues, velocity from the last sprint, and items ready for estimation.
2. Create a design review briefing pulling recent UI/UX changes from git history, linking to relevant Figma or mockup files found in the repo, and summarizing outstanding design-related issues.
3. Output both as a single Markdown document with clear section headers.

### Example 2: Standup Notes from Git Activity

**User:** "Generate standup notes for today based on yesterday's work."

The skill will:
1. Run `git log --since="yesterday" --oneline` to gather recent commits.
2. Check for any open PRs with `gh pr list --author @me`.
3. Identify any failing CI checks with `gh run list --limit 5`.
4. Format the output as: "Yesterday I... / Today I plan to... / Blockers: ..."

### Example 3: Weekly Recurring Workflow

**User:** "Create a Monday morning workflow that preps me for the week."

The skill will generate a script that:
1. Reads the week's calendar events from an ICS file.
2. Summarizes each day's meetings with participant counts and estimated time commitment.
3. Pulls the current sprint board status.
4. Outputs a weekly overview document to `docs/weekly-prep.md`.

## Error Handling

- **No calendar data provided:** Prompts the user to paste events, point to an ICS file, or describe their schedule.
- **Unrecognized format:** Attempts best-effort parsing and asks the user to confirm the extracted events.
- **Missing git context:** Skips repository-specific sections and notes which parts were omitted.
- **Permission errors:** Suggests checking file permissions or GitHub CLI authentication status.

## Prerequisites

- Calendar data in ICS format, JSON, or plain text event descriptions
- Git repository context for commit-aware standup generation
- GitHub CLI (`gh`) authenticated for PR and CI status lookups

## Resources

- [iCalendar (ICS) specification](https://datatracker.ietf.org/doc/html/rfc5545) — event format reference
- [GitHub CLI manual](https://cli.github.com/manual/) — `gh pr list`, `gh run list` commands
- [Git log formatting](https://git-scm.com/docs/git-log) — options for activity summaries
