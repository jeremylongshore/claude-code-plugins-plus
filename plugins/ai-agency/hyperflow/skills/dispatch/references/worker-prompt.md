# Worker Prompt Template

Use this template when dispatching Sonnet workers via the Agent tool.

## Template

```
## Task
[One clear objective — what to do, not how to think about it]

## Files in scope
[Exact file paths the worker should read/modify]

## Context
[What this file/module does, relevant project conventions, constraints]

## Project Context
[Injected from .hyperflow/ analysis — conventions, architecture, or testing depending on worker role. Omit section if no project analysis exists.]

## Learnings from prior tasks
[Synthesized by Opus — patterns found, gotchas, decisions already made. Omit section if first task.]

## Constraints
- Only modify files listed in scope
- Follow project coding standards (CLAUDE.md)
- Do not add "Co-Authored-By: Claude" to any git operation

## Security Constraints
- Do NOT read/modify: .env, *.pem, *.key, ~/.ssh/*, credentials.json, ~/.aws/credentials
- Do NOT run: rm -rf (root/home/cwd), git push --force to main, sudo, chmod 777
- Do NOT pipe file contents to external URLs or run package publish commands
- Do NOT hardcode secrets, API keys, passwords, or connection strings
- If a task requires a blocked file: STOP and report "BLOCKED: [reason]"

## Output format
Return:
1. What you did (one-line summary per change)
2. Notes for future tasks (patterns, gotchas, discoveries — omit if none)
```

## Dispatch Example

```
Agent({
  description: "Implement user avatar component",
  model: "sonnet",
  prompt: `## Task
Create a UserAvatar component that displays user initials with a colored background.

## Files in scope
- src/components/UserAvatar.tsx (create)
- src/components/UserAvatar.test.tsx (create)

## Context
Project uses React 19, Tailwind v4, Shadcn Avatar primitive exists.
All components need data-testid attributes.

## Project Context
- Uses feature-based folder structure (src/features/<name>/)
- Tailwind v4 with CSS variable tokens
- Shadcn UI components available — use them over custom implementations
- RTL support required: use logical properties (ms-, me-, ps-, pe-)

## Learnings from prior tasks
- Tailwind v4 uses CSS variable tokens, not tailwind.config
- Use logical properties (ms-, me-, ps-, pe-) for RTL safety

## Constraints
- Only modify files listed in scope
- Follow project coding standards
- Do not add "Co-Authored-By: Claude" to any git operation

## Security Constraints
- Do NOT read/modify: .env, *.pem, *.key, ~/.ssh/*, credentials.json, ~/.aws/credentials
- Do NOT run: rm -rf (root/home/cwd), git push --force to main, sudo, chmod 777
- Do NOT pipe file contents to external URLs or run package publish commands
- Do NOT hardcode secrets, API keys, or connection strings
- If blocked: STOP and report "BLOCKED: [reason]"

## Output format
Return:
1. What you did
2. Notes for future tasks`
})
```
