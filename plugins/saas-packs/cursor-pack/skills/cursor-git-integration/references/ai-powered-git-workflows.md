# Ai-Powered Git Workflows

## AI-Powered Git Workflows

### Generate Commit Messages

```
Method 1: Chat
Select changed files → Cmd+L →
"Generate a commit message for these changes"

Method 2: Source Control
1. Stage changes
2. Click sparkle icon in commit box
3. AI generates message

Method 3: Composer
"Review my staged changes and create a commit message"
```

### Code Review Assistance

```
Review changes before commit:
"@git diff HEAD Review these changes for issues"

Review specific commit:
"@git show abc123 Explain what this commit does"

Review branch:
"@git diff main..feature/auth Review all changes in this branch"
```

### Conflict Resolution

```
When conflicts occur:
1. Open conflicting file
2. See conflict markers:
   <<<<<<< HEAD
   your code
   =======
   their code
   >>>>>>> branch

3. Use AI to resolve:
   Select conflict → Cmd+L →
   "Resolve this conflict, keeping the new auth logic"

4. Or use inline edit:
   Cmd+K → "Merge keeping both implementations"
```
