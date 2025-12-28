# Git Commit Smart

**AI-powered conventional commit message generator** that analyzes your staged changes and creates professional, standardized commit messages automatically.

## Features

-  **AI-Powered Analysis**: Understands your code changes and generates contextual messages
-  **Conventional Commits**: Follows the conventional commits standard automatically
-  **Fast Workflow**: Generate commits in seconds with `/gc` shortcut
-  **Smart Categorization**: Automatically determines commit type (feat, fix, docs, etc.)
-  **Breaking Change Detection**: Identifies and documents breaking changes
-  **Interactive Confirmation**: Review and edit before committing

## Installation

```bash
# Add this marketplace to Claude Code
/plugin marketplace add jeremylongshore/claude-code-plugins

# Install the plugin
/plugin install git-commit-smart@claude-code-plugins-plus
```

## Usage

### Basic Usage

1. Stage your changes:
```bash
git add .
```

2. Generate commit message:
```bash
/commit-smart
# or use the shortcut:
/gc
```

3. Review the generated message and confirm

### Example Session

```bash
# Stage changes
git add src/auth/login.js src/api/users.js

# Generate commit
/gc

# Claude analyzes and proposes:
feat(auth): add OAuth2 Google login support

Implements Google OAuth2 authentication flow using Passport.js.
Users can now sign in with their Google account instead of
creating a new password.

Closes #123

# Commit with this message? (yes/no/edit)
yes

# Committed! 
```

## Commit Types

The plugin automatically selects the appropriate type:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style/formatting (no logic change)
- `refactor`: Code restructure (no behavior change)
- `perf`: Performance improvement
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

## Requirements

- Git repository with staged changes
- Claude Code editor

## Configuration

No configuration needed! The plugin works out of the box.

### Optional Context

You can provide additional context:
```bash
/gc - emphasize that this fixes a security vulnerability
```

## Pro Tips

 **Stage related changes together** - Commit logical units, not random files

 **Use the /gc shortcut** - Saves typing and speeds up workflow

 **Review before committing** - Always check the generated message makes sense

 **Add issue references** - Plugin will detect and include "Closes #123" when appropriate

 **Break up large changes** - Multiple focused commits are better than one massive commit

## When NOT to Use

 **Merge commits** - Use git's default merge message instead
 **No staged changes** - Stage changes first with `git add`
 **Emergency hotfixes** - When you need to commit immediately without review

## Troubleshooting

### "No changes staged for commit"
**Solution**: Run `git add <files>` first to stage your changes

### "Merge in progress detected"
**Solution**: For merge commits, use `git commit --no-edit` instead

### Commit message too generic
**Solution**: Add more context when calling the command: `/gc - this fixes the login bug`

## Examples

### Bug Fix
```
fix(api): correct typo in email normalization

Changed tolowerCase() to toLowerCase() to fix TypeError
when processing user emails.
```

### New Feature
```
feat(search): add global search functionality

Implements full-text search across products, users, and orders.
New SearchBar component provides real-time suggestions as user types.

Closes #45
```

### Breaking Change
```
refactor(auth)!: change login to use email instead of username

BREAKING CHANGE: login() now requires email parameter instead of username.
Clients must update their authentication calls:
- Before: login(username, password)
- After: login(email, password)
```

## License

MIT License - see [LICENSE](../../../000-docs/001-BL-LICN-license.txt) for details

## Contributing

Contributions welcome! See [CONTRIBUTING.md](../../../000-docs/007-DR-GUID-contributing.md) for guidelines.

## Support

- **Issues**: [GitHub Issues](https://github.com/jeremylongshore/claude-code-plugins/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jeremylongshore/claude-code-plugins/discussions)

---

**Made with ️ for developers who want better commit messages without the hassle**
