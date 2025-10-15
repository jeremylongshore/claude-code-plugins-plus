# Snapshot Test Manager

Manage and update snapshot tests with intelligent diff analysis and selective updates.

## Installation

```bash
/plugin install snapshot-test-manager@claude-code-plugins-plus
```

## Usage

```bash
/snapshot-manager
# or shortcut
/sm
```

## Features

- **Intelligent Diff Analysis**: Distinguish intentional changes from regressions
- **Selective Updates**: Update specific snapshots while preserving others
- **Snapshot Validation**: Detect brittle or meaningless snapshots
- **Organization**: Clean up and organize snapshot files
- **Multi-Framework**: Jest, Vitest, Playwright, Storybook support

## Example Workflow

```bash
# After code changes cause snapshot failures
/snapshot-manager

# Claude analyzes diffs and recommends:
#  Update snapshots for intentional UI changes
#  Review snapshots with unexpected changes
#  Preserve snapshots that caught regressions
```

## Supported Frameworks

- Jest
- Vitest
- React Testing Library
- Playwright
- Storybook

## Files

- `commands/snapshot-manager.md` - Main snapshot management command

## License

MIT
