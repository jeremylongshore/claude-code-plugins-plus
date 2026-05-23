# gh-dash

GitHub PR dashboard for Claude Code.

## Features

- `/gh-dash:pr` - View PR status dashboard
- Visual CI/CD progress bar with live updates
- Bot comment detection (CodeRabbit, Cursor Bugbot, Coverage)
- Files changed and lines added/removed stats
- Merge PRs directly from terminal

## Installation

```bash
claude --plugin-dir /path/to/claude-code-gh-dash
```

Or install from marketplace:

```
/plugin install gh-dash
```

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated

## Usage

```
/gh-dash:pr              # View PR for current branch
/gh-dash:pr --merge      # Squash merge
/gh-dash:pr --merge merge    # Merge commit
/gh-dash:pr --merge rebase   # Rebase
```

## Links

- [Source Repository](https://github.com/jakozloski/claude-code-gh-dash)
- [Author](https://github.com/jakozloski)
