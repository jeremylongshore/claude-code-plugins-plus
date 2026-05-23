# Navigating GitHub

**Go from zero to GitHub in minutes, then learn git through hands-on lessons on your actual project.**

This skill does two things:

1. **Sets you up on GitHub** — from installing the CLI to pushing your first commit
2. **Teaches you git** — 9 progressive lessons, each one hands-on with real commands

No slides. No docs. No assumed knowledge. Run a command, see what happens, then understand why. The AI adapts to your level automatically.

## Setup — From Zero to GitHub

Say "set up my repo" or "help me with github" and the skill walks through everything:

1. **Connect to GitHub** — installs `gh` CLI, authenticates, configures git identity
2. **Initialize your repo** — `git init`, auto-generated `.gitignore`, first commit
3. **Create the remote** — `gh repo create`, push, shows the live URL

Skips anything already done. Complete beginners get full explanations ("GitHub is like Google Drive for code"). Experienced developers get it done in seconds.

## Learn — 9 Hands-On Lessons

Say "teach me github" or run `/github-learn` to start. Every lesson runs on your real project using **do-then-explain**: run the command, see the result, then understand why.

### Beginner

| Lesson | What You Do |
|--------|------------|
| **GitHub 101** | Make changes, commit, push — guided step by step |
| **Branching Basics** | Create a branch, make a change, switch back, see the difference |
| **Your First PR** | Branch, push, create a PR, see the diff, merge it |

### Intermediate

| Lesson | What You Do |
|--------|------------|
| **Branch Workflows** | Feature branches, naming conventions, keeping branches current |
| **PR Review Flow** | Review a PR, leave comments, approve or request changes |
| **Team Git** | Forking, upstream sync, co-authoring commits |

### Advanced

| Lesson | What You Do |
|--------|------------|
| **Rebase vs Merge** | Interactive rebase, squash commits, clean history |
| **GitHub Actions** | Write a CI workflow, push, watch it run |
| **Review Ecosystem** | Set up CodeRabbit, understand automated review tools |

Each lesson checks understanding before moving on. After each lesson, you get a summary, a challenge to try solo, and a suggestion for what to learn next.

## Adaptive Skill Level

The skill figures out your level from your environment — commit message quality, branch usage, auth state — not from a questionnaire. It only asks when signals are genuinely ambiguous.

| Level | What You Experience |
|-------|-------------------|
| **Beginner** | Analogies, zero jargon, full step-by-step. The AI does it and teaches as it goes. |
| **Intermediate** | Light jargon with definitions, explains the "why." Handles it, asks you to confirm. |
| **Advanced** | Standard git vocabulary, brief rationale. Suggests, you decide. |
| **Expert** | Terse and technical. You drive, the AI assists. |

## Install

```bash
# Claude Code
/plugin marketplace add jeremylongshore/navigating-github

# Manual
git clone https://github.com/jeremylongshore/navigating-github.git
```

Works with: **Claude Code**, **Cursor**, **Windsurf**, **Aider**, **Continue** — any AI coding tool with terminal access.

## Safety (During All Lessons)

- Never pushes to `main`/`master` — always branches first
- Never force pushes without explicit confirmation
- Never commits secrets (`.env`, API keys, credentials)
- Never runs destructive operations without showing impact first

## Contributing

PRs welcome. If you see a gap in the curriculum, a confusing explanation, or a missing lesson — open an issue or submit a PR.

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Jeremy Longshore](https://github.com/jeremylongshore) / [Intent Solutions](https://intentsolutions.io) for the [Tons of Skills](https://tonsofskills.com) marketplace.
