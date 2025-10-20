# AI Commit Generator

**Never write commit messages manually again.** Let AI analyze your git diff and generate perfect conventional commit messages instantly.

---

## 🎯 What This Plugin Does

Analyzes your code changes and generates professional commit messages following conventional commit standards. No more staring at `git commit -m "..."` wondering what to write.

**Before** (manual):
```bash
git add .
git status  # what did I change again?
git diff    # scroll through changes
git commit -m "updated stuff"  # 😞
```

**After** (with AI):
```bash
git add .
/commit
# ✨ Get 3 AI-generated options instantly
# ✅ Commit with one click
```

---

## 🚀 Quick Start

### Installation
```bash
/plugin install ai-commit-gen@claude-code-plugins-plus
```

### Usage
```bash
# Make your changes
git add .

# Generate commit message
/commit

# That's it! AI analyzes and commits for you.
```

---

## 💡 Features

### Instant Analysis
- Analyzes git diff automatically
- Identifies type of changes (feat/fix/docs/etc)
- Determines scope and impact
- Suggests breaking change warnings

### 3 Generated Options
1. **Concise**: Subject line only (for quick commits)
2. **Detailed**: Subject + body explaining changes
3. **Comprehensive**: Subject + body + footer (with issue refs)

### Conventional Commits
All messages follow [Conventional Commits](https://www.conventionalcommits.org/) standard:
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types Supported
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code formatting
- `refactor`: Code restructuring
- `perf`: Performance improvements
- `test`: Test updates
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Maintenance tasks

---

## 📚 Examples

### Example 1: New Feature
**Your changes**: Added user authentication

**AI generates**:
```
Option 1: feat(auth): add user authentication

Option 2: feat(auth): add user authentication

Implement JWT-based authentication with email/password login.
Includes password hashing with bcrypt and token refresh logic.

Option 3: feat(auth): add user authentication

Implement JWT-based authentication with email/password login.
Includes password hashing with bcrypt and token refresh logic.

Closes #42
```

### Example 2: Bug Fix
**Your changes**: Fixed null pointer error

**AI generates**:
```
Option 1: fix(auth): handle null user in validation

Option 2: fix(auth): handle null user in validation

Previously crashed when user was null. Now returns proper
error message and 401 status code.

Option 3: fix(auth): handle null user in validation

Previously crashed when user was null. Now returns proper
error message and 401 status code.

Fixes #89
```

### Example 3: Documentation
**Your changes**: Updated README

**AI generates**:
```
Option 1: docs(readme): add installation instructions

Option 2: docs(readme): add installation instructions

Include step-by-step setup guide with prerequisites
and troubleshooting section.
```

---

## 🎓 How It Works

1. **Analyzes git diff** - Reads all staged and unstaged changes
2. **Identifies patterns** - Determines type, scope, and impact
3. **Generates messages** - Creates 3 commit message options
4. **You choose** - Pick option 1, 2, 3, or customize
5. **Commits automatically** - Runs `git commit` with your choice

---

## ⚡ Quick Mode

Already know what you want? Pass a custom message:

```bash
/commit "fix: resolve login timeout bug"
```

Commits immediately with your message (no analysis).

---

## 🔧 Advanced Usage

### Amend Last Commit
```bash
/commit --amend
```
Regenerates message for the last commit.

### Breaking Changes
AI automatically detects breaking changes and adds:
```
BREAKING CHANGE: API response format changed.
All clients must update to use response.data field.
```

### Issue References
AI includes issue references when mentioned in code:
```
Closes #42
Fixes #89
```

### Multiple Files
If changes span multiple areas, AI suggests splitting into separate commits:
```
⚠️  Changes affect multiple areas:
  - Authentication (src/auth/)
  - Database (src/db/)

Suggestion: Commit separately for cleaner history
```

---

## 🎯 Best Practices

The AI follows these commit message best practices:

1. **Imperative mood**: "add feature" not "added feature"
2. **Lowercase subject**: After the type
3. **No period**: At end of subject line
4. **50 char limit**: For subject line
5. **72 char wrap**: For body text
6. **Explain why**: Not just what changed
7. **Reference issues**: Link to issue tracker

---

## 💭 Why This Plugin?

**Problem**: Writing good commit messages is tedious and inconsistent
- Takes mental energy after coding
- Easy to write lazy messages like "fix stuff"
- Hard to remember conventional commit format
- Boring to explain obvious changes

**Solution**: AI analyzes changes and generates professional messages
- Instant generation (no thinking required)
- Always follows best practices
- Identifies scope and type automatically
- Explains changes clearly

---

## 📊 Comparison

| Task | Manual | With AI Commit Gen | Time Saved |
|------|--------|-------------------|------------|
| Analyze changes | 2 min | 0 sec | 2 min |
| Write message | 3 min | 5 sec | ~3 min |
| Format correctly | 1 min | 0 sec | 1 min |
| **Total** | **6 min** | **5 sec** | **~6 min** |

**Per day** (10 commits): Save ~60 minutes
**Per month**: Save ~20 hours
**Per year**: Save ~240 hours

---

## 🚀 Get Started Now

```bash
# Install
/plugin install ai-commit-gen@claude-code-plugins-plus

# Use
git add .
/commit

# Done! ✨
```

---

## 🤝 Related Plugins

Works great with:
- **git-commit-smart** - Advanced git workflows
- **devops-automation-pack** - Complete DevOps suite
- **overnight-dev** - Autonomous coding with auto-commits

---

**Version**: 1.0.0
**License**: MIT
**Author**: Jeremy Longshore

---

**Stop manually writing commit messages. Let AI handle it.** ⚡
