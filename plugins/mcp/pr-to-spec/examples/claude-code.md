# Claude Code Integration

Add this to your project's `CLAUDE.md` to enable AI-assisted PR review using `pr-to-prompt`.

## CLAUDE.md Snippet

```markdown
## PR Review with pr-to-prompt

When reviewing PRs, always generate a structured spec first:

\`\`\`bash
pr-to-prompt --repo <owner/repo> --pr <number> --json
\`\`\`

### Review Protocol

1. Generate the spec with `--json` flag
2. Check `risk_flags` for high-severity items — these need careful review
3. Verify `constraints` are satisfied by the implementation
4. Review `acceptance_criteria` as a checklist
5. Use `decision_prompt` as your evaluation framework

### Quick Commands

\`\`\`bash
# Full spec for review
pr-to-prompt --repo owner/repo --pr 42 --json | jq .

# Just the risks
pr-to-prompt --repo owner/repo --pr 42 --field risk_flags --quiet

# Just the decision prompt
pr-to-prompt --repo owner/repo --pr 42 --field decision_prompt --quiet
\`\`\`

### Decision Framework

After reviewing the spec, respond with one of:
- **APPROVE** — Change is safe and well-implemented
- **REQUEST_CHANGES** — List specific issues that must be addressed
- **NEEDS_INFO** — List questions that must be answered before deciding
```

## How It Works

1. A developer asks Claude Code to review a PR
2. Claude runs `pr-to-prompt --json` to get the structured spec
3. Claude evaluates the spec against the project's conventions and constraints
4. Claude provides a review decision with rationale

## Example Interaction

```
User: Review PR #42

Claude: Let me generate a spec for this PR first.

> pr-to-prompt --repo owner/repo --pr 42 --json

Based on the spec:

**APPROVE** — This is a clean feature addition (rate limiting middleware) with:
- Appropriate test coverage (new test file added)
- No high-risk flags (only medium: security-headers)
- Scope limited to middleware and routes
- All acceptance criteria look achievable

One suggestion: Consider adding integration tests for the rate limit headers.
```
