# Managing Large Codebases

## Managing Large Codebases

### Selective Indexing

```yaml
# .cursorignore - reduce indexed context
node_modules/
dist/
build/
*.log
*.lock
test/fixtures/
docs/
```

### Strategic @codebase Queries

```
Specific:
"@codebase where is handleUserLogin defined?"

Too broad:
"@codebase show me all the code"
```

### Using Summaries

```
For large files, ask for summary first:
"Summarize the main exports from @lib/utils.ts"

Then dive into specifics:
"Explain the dateFormatter function in detail"
```
