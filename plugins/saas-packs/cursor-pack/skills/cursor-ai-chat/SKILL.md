---
name: cursor-ai-chat
description: |
  Master Cursor AI chat interface for code assistance. Triggers on "cursor chat",
  "cursor ai chat", "ask cursor", "cursor conversation", "chat with cursor".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor AI Chat Mastery

## Chat Interface Overview

### Opening Chat
- **Cmd+L** (Mac) / **Ctrl+L** (Windows): Open chat
- **Cmd+Shift+L**: New chat conversation
- Click chat icon in sidebar

### Chat Panel Layout
```
┌─────────────────────────────────────────┐
│ Model Selector │ Context │ Settings    │
├─────────────────────────────────────────┤
│                                         │
│  Conversation History                   │
│                                         │
├─────────────────────────────────────────┤
│  Input Box                              │
│  [@files] [images] [code blocks]        │
└─────────────────────────────────────────┘
```

## Effective Chat Patterns

### Code Explanation
```
Select code → Cmd+L →
"Explain what this code does step by step"
"What's the time complexity of this function?"
"Are there any bugs in this code?"
```

### Code Generation
```
"Write a function that [description]"
"Create a class that [description]"
"Implement [algorithm/pattern] in [language]"
```

### Refactoring Requests
```
Select code → Cmd+L →
"Refactor this to use async/await"
"Make this more readable"
"Extract this into smaller functions"
"Convert to TypeScript with proper types"
```

### Debugging
```
"Why is this code throwing [error]?"
"Debug this function - it returns [wrong result]"
"Find the bug: expected [X] but got [Y]"
```

## Context Management

### Adding Context with @-mentions
```
@filename.py - Include specific file
@folder/ - Include folder contents
@codebase - Search entire codebase
@docs - Reference documentation
@web - Search the web
@git - Git history context
```

### Context Best Practices
```
Good: "@auth.py How does user authentication work?"
Good: "Looking at @utils/helpers.js, how can I optimize?"

Bad: "How does my code work?" (no context)
Bad: "Fix the bug" (too vague)
```

### Clearing Context
- Start new chat for fresh context
- Click "Clear" to reset conversation
- Context persists within conversation

## Chat Commands

### Special Commands
```
/edit - Enter edit mode
/explain - Explain selected code
/fix - Fix errors in selection
/test - Generate tests
/docs - Generate documentation
/commit - Generate commit message
```

## Model Selection

### Available Models
```
GPT-4 Turbo - Best quality, slower
GPT-4 - High quality
GPT-3.5 Turbo - Fast, good for simple tasks
Claude 3.5 Sonnet - Great for explanations
Claude 3 Opus - Highest quality Claude
```

### When to Use Each
```
Complex architecture → GPT-4 or Claude Opus
Quick fixes → GPT-3.5 Turbo
Explanations → Claude Sonnet
Code review → GPT-4 Turbo
```

## Advanced Chat Techniques

### Multi-Turn Conversations
```
Turn 1: "Create a user authentication system"
Turn 2: "Add password reset functionality"
Turn 3: "Include rate limiting"
Turn 4: "Write tests for all of this"
```

### Iterative Refinement
```
"Make it more efficient"
"Add error handling"
"Use a different approach"
"Simplify this"
```

### Code Application
```
After AI generates code:
- Click "Apply" to insert at cursor
- Click "Copy" to clipboard
- Click "Insert" to add to file
- Use Composer for multi-file changes
```

## Chat History

### Accessing History
- Scroll up in chat panel
- Chat history persists per session
- Export conversations if needed

### Managing History
```
- New Chat (Cmd+Shift+L) for fresh start
- Keep related questions in same chat
- Separate unrelated topics
```

## Tips for Better Responses

### Be Specific
```
Vague: "Make this better"
Specific: "Optimize this function for memory usage by avoiding array copies"
```

### Provide Context
```
Weak: "Fix the error"
Strong: "Fix this TypeError: cannot read property 'map' of undefined
        when calling processUsers with empty response"
```

### Break Down Complex Requests
```
Instead of: "Build a complete auth system"
Do:
1. "Design the database schema for users"
2. "Create the registration endpoint"
3. "Implement login with JWT"
4. "Add password reset flow"
```
