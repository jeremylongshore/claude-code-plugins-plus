# Evidence summary template

Compact block to embed in a Design Issue / PR body. Documents what was tested and how, in case the maintainer wants verification.

```markdown
## Evidence

**Repo state**: `{{git rev-parse --short HEAD}}` on branch `{{branch}}` (forked from `{{upstream}}@{{upstream_sha}}`)

**Tests run**:

`​`​`
{{paste test command + summary line, e.g. "pytest -q ... 142 passed in 18.4s"}}
`​`​`

Full log: `~/.contribute-system/test-logs/{{run_filename}}` (local — happy to gist on request)

**Lint / typecheck**:

`​`​`
{{ruff check . / pnpm typecheck / cargo clippy / etc.}}
`​`​`

**Manual verification** (if UI):

- {{step 1}}
- {{step 2}}

**asciinema** (optional): `~/.contribute/recordings/{{file}}.cast`
```

This block is for human reviewers, not bots — keep it human-readable. Don't include secrets, tokens, or anything beyond the test summary.
