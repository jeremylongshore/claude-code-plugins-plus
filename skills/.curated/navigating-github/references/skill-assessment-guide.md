# Skill Assessment Guide

How the AI determines the user's GitHub skill level and adapts its behavior.

## Assessment Methodology

### Passive Signals (checked automatically)

**Note:** A fresh repo with few commits does not automatically indicate a beginner. Always cross-reference passive signals with the active assessment question. A new project from an experienced developer will show beginner-like passive signals.

| Signal | Beginner Indicator | Intermediate | Advanced | Expert |
|--------|-------------------|-------------|----------|--------|
| `gh auth status` | Not authenticated | Authenticated | Authenticated | Authenticated |
| `.git/` exists | No | Yes, few commits | Yes, many commits | Yes, complex history |
| Commit messages | N/A | "update", "fix", single words | Descriptive, conventional | Conventional commits, scoped |
| Branch count | 0-1 (just main)* | 1-2 (maybe one feature branch) | 3+ active branches | Branch naming conventions |
| `.gitignore` | Missing | Exists but basic | Comprehensive | Custom, project-specific |
| Remote config | None | HTTPS | SSH or HTTPS | Multiple remotes |
| PR history | None | Few, if any | Regular PRs | PRs with reviews, CI |

*A branch count of 0-1 in a new repo is inconclusive — defer to the active assessment question.

### Active Assessment Question

Asked once per session, on first GitHub-related interaction:

> How comfortable are you with GitHub? Pick the closest:
>
> 1. "What's GitHub?" — I'm brand new to this
> 2. "I can commit and push but that's about it" — I know the basics
> 3. "I use branches and PRs regularly" — I'm comfortable
> 4. "I manage teams/repos and want to optimize" — I'm advanced

The answer is combined with passive signals. Passive signals can override the self-assessment in either direction — someone who says "I'm advanced" but has no branches and single-word commits gets treated as intermediate.

## Adaptive Behavior Matrix

### Language Style

| Level | Style | Example |
|-------|-------|---------|
| Beginner | Analogies, zero jargon, encouraging | "Think of a branch like making a copy of your document before trying something risky" |
| Intermediate | Light jargon with brief definitions | "We'll create a feature branch — that's a separate line of development so main stays clean" |
| Advanced | Standard git/GitHub vocabulary | "I'll rebase your feature branch onto main to get a linear history" |
| Expert | Terse, technical, no hand-holding | "Rebase onto main, squash fixups, force-push the topic branch" |

### Explanation Depth

| Level | What Gets Explained | What Gets Skipped |
|-------|--------------------|--------------------|
| Beginner | Everything — what, why, and how | Nothing — assume zero knowledge |
| Intermediate | The "why" behind each step | Basic mechanics (what `git add` does) |
| Advanced | Rationale for non-obvious choices only | Standard operations |
| Expert | Nothing unless they ask | Everything |

### Autonomy Level

| Level | Who Does What |
|-------|--------------|
| Beginner | AI does everything, explains each step, waits for acknowledgment |
| Intermediate | AI does it, shows what it did, asks "does this look right?" |
| Advanced | AI suggests an approach, user approves, AI executes |
| Expert | User says what they want, AI does exactly that — no editorializing |

### Error Handling

| Level | How Errors Are Presented |
|-------|------------------------|
| Beginner | "Something went wrong, but don't worry — this is fixable. Here's what happened in simple terms..." |
| Intermediate | "Got a merge conflict in `src/app.js`. Two changes touched the same line. Let me walk you through resolving it." |
| Advanced | "Merge conflict in `src/app.js:42`. Both branches modified the auth check. Your change vs theirs shown below." |
| Expert | Raw error output + "Want me to resolve or will you handle it?" |

## Dynamic Level Adjustment

The skill level is not fixed. The AI continuously watches for signals that the user's level should be adjusted:

### Level-Up Signals

- User uses git terminology correctly without being taught
- User runs git commands independently
- User asks "can you just do X" instead of "what does X mean"
- User edits files confidently after seeing a diff
- User mentions workflows, CI/CD, or review processes

### Level-Down Signals (for specific topics only)

- User freezes or says "I don't understand"
- User asks "what does that mean?"
- User makes an error that suggests misunderstanding (e.g., thinking commit = push)
- User expresses anxiety or hesitation about an operation

When a level-down signal is detected, drop into teaching mode **for that specific topic only** — don't globally lower the level. Someone can be advanced at committing but confused about rebasing.

## Session Memory

Within a single session, remember:

- The assessed skill level
- Topics where the user needed extra help (topic-specific level overrides)
- Topics where the user showed advanced knowledge
- Whether the user prefers brevity or detail

This allows the skill to provide increasingly personalized guidance as the session progresses.
