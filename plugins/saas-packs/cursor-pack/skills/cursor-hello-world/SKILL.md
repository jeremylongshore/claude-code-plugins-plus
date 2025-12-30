---
name: cursor-hello-world
description: |
  Create your first project with Cursor AI features. Triggers on "cursor hello world",
  "first cursor project", "cursor getting started", "try cursor ai", "cursor basics".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Hello World - First AI-Powered Project

## Quick Start (5 Minutes)

### 1. Create New Project
```bash
mkdir my-cursor-project
cd my-cursor-project
cursor .
```

### 2. Try Tab Completion
Create a new file and start typing:
```python
# app.py
def calculate_fibonacci(n):
    # Press Tab to accept AI suggestion
```

The AI will suggest the complete implementation.

### 3. Try AI Chat (Cmd/Ctrl + L)
Ask questions about your code:
```
"How can I make this function handle negative numbers?"
"Add error handling to this function"
"Write tests for this code"
```

### 4. Try Composer (Cmd/Ctrl + I)
For multi-file edits:
```
"Create a Flask API with:
- GET /fibonacci/{n} endpoint
- Error handling
- Basic tests"
```

## Key Features to Explore

### Tab Completion
- Start typing and wait for ghost text
- Press Tab to accept
- Press Esc to dismiss
- Press Ctrl+Right to accept word-by-word

### AI Chat (Cmd/Ctrl + L)
- Ask questions about selected code
- Request explanations
- Get refactoring suggestions
- Debug help

### Composer (Cmd/Ctrl + I)
- Multi-file code generation
- Project scaffolding
- Large refactors
- Feature implementation

### Inline Edit (Cmd/Ctrl + K)
- Quick edits without chat
- Select code → describe change
- AI applies changes inline

## Sample Exercises

### Exercise 1: Code Completion
```javascript
// Type this and let AI complete:
function validateEmail(email) {
  // AI completes regex validation
}
```

### Exercise 2: Chat Refactor
```python
# Select this code, press Cmd+L, ask "make this async"
def fetch_data(url):
    response = requests.get(url)
    return response.json()
```

### Exercise 3: Composer Generation
```
Prompt: "Create a todo list app with:
- Add/remove tasks
- Mark complete
- Local storage persistence
- Clean UI with Tailwind"
```

## Understanding the AI

### Context Window
- Cursor sends relevant code context
- Recent edits are prioritized
- Open files influence suggestions

### Model Selection
- GPT-4: Best quality, slower
- GPT-3.5 Turbo: Faster, good for simple tasks
- Claude: Great for explanations

### Privacy Modes
- **Privacy Mode Off**: Code sent to AI
- **Privacy Mode On**: Code stays local (limited features)

## Next Steps

After completing hello world:
1. Configure `.cursorrules` for project-specific behavior
2. Set up codebase indexing for large projects
3. Customize keybindings
4. Explore extensions compatibility
