# Claude + GitHub — Platform-Aware Guidance

How Claude works with GitHub across different platforms. Use this to set accurate expectations about what's possible in the user's current environment.

## Platform Capabilities Matrix

| Capability | Claude Code (CLI) | Cowork | Cursor / Windsurf / Cline | Claude AI (web/app) |
|-----------|-------------------|--------|--------------------------|-------------------|
| Run git commands | Yes — full terminal access | Via skills | Yes — integrated terminal | No |
| Create commits | Yes — directly | Via skills | Yes — directly | No (can draft messages) |
| Create branches | Yes — directly | Via skills | Yes — directly | No |
| Push to remote | Yes — directly | Via skills | Yes — directly | No |
| Create PRs | Yes — via `gh` CLI | Via skills | Yes — if `gh` CLI installed | No (can draft PR descriptions) |
| Resolve conflicts | Yes — edit files + git | Via skills | Yes — edit files + git | No (can advise) |
| Read git history | Yes — `git log`, `git diff` | Via skills | Yes — built-in or terminal | No |
| GitHub API access | Yes — via `gh` CLI | Limited | Yes — if `gh` CLI installed | No |
| Install GitHub Apps | No (browser task) | No | No | No |

## Claude Code (CLI)

**Full git and GitHub access.** Claude Code runs in a terminal and can execute any git or `gh` CLI command directly. This is the most powerful environment for GitHub workflows.

**Best for:** Developers who want full control, automation, and the ability to handle complex git operations (rebase, cherry-pick, bisect, etc.).

**How this skill works here:**

- All six modes (setup, save, share, understand, fix, learn) are fully supported
- Commands are executed directly — the AI runs git commands and shows results
- Real-time conflict resolution with file editing
- Full `gh` CLI access for PRs, issues, Actions, and more

## Cowork

**Plugin-based GitHub access.** Cowork runs skills that handle GitHub workflows. Users don't need terminal knowledge — the skill abstracts the complexity.

**Best for:** Non-technical users, teams that want a guided experience, people building with AI who need version control but don't want to learn git deeply.

**How this skill works here:**

- All six modes supported through the skill interface
- Setup mode is especially important — many Cowork users are GitHub beginners
- Save and Share modes abstract away terminal commands
- Learn mode teaches concepts through the skill's guided interface

## Cursor / Windsurf / Cline / Continue / Aider

**Integrated terminal access.** These AI-powered editors have built-in terminals and often have their own git integrations (GUI panels, inline diff views, etc.).

**Best for:** Developers who want AI-assisted coding with git integration in their editor.

**How this skill works here:**

- All six modes work through the terminal
- The skill complements the editor's built-in git GUI
- Some operations (like viewing diffs) may be better in the editor's visual interface
- The skill focuses on operations the GUI doesn't handle well (branching strategy, PR workflow, conflict resolution)

## Claude AI (Web / App)

**No direct git access.** Claude AI in the web interface or mobile app cannot run commands or access the filesystem. It can only work with information the user pastes in.

**Best for:** Quick help, learning, drafting commit messages or PR descriptions, code review advice on pasted code.

**What the user can do here:**

- Ask for help understanding git concepts
- Paste error messages and get troubleshooting advice
- Draft commit messages from described changes
- Draft PR descriptions and review comments
- Get advice on branching strategies and workflows
- Learn git through conversation (no hands-on exercises)

**What the user CANNOT do here:**

- Run any git commands
- Have the AI check their repo status
- Have the AI resolve conflicts
- Have the AI create PRs or push code

## Adapting Guidance by Platform

When the user's platform is known, adapt recommendations:

**Terminal-capable platforms (Claude Code, Cursor, etc.):**

- Run commands directly
- Show real output
- Hands-on exercises work fully

**Cowork:**

- Rely on skill abstractions
- Focus on concepts over commands
- Guide through the skill interface

**Claude AI (web/app):**

- Teach concepts conversationally
- Provide commands for the user to copy-paste into their terminal
- Draft artifacts (commit messages, PR descriptions) the user can use
- Recommend installing Claude Code or a terminal-capable platform for full access
