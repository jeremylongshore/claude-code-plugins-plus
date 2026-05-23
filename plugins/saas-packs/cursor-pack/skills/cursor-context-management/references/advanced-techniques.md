# Advanced Techniques

## Advanced Techniques

### Layered Context

```
Layer 1: .cursorrules (always present)
Layer 2: @-mentions (specific files)
Layer 3: Selection (immediate focus)
Layer 4: Prompt (your question)

Optimize each layer:
- .cursorrules: Essential patterns only
- @-mentions: Only truly needed files
- Selection: Exact code in question
- Prompt: Clear, concise question
```

### Context Priming

```
Start chat with context summary:
"Working on auth module. Using JWT, refresh tokens,
httpOnly cookies. Following patterns in @lib/auth.ts.
Need to add password reset."

Then ask specific questions:
"Create the reset token generation function"
```

### Reference vs Include

```
Reference (efficient):
"Follow the pattern in UserService"

Include (uses context):
"@services/UserService.ts create similar for Products"

Use references when AI already has indexed context
```
