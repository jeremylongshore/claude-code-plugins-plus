# Usage Examples

This guide shows how to use the **project-health-auditor** MCP server.

## Installation

```bash
# Install the plugin
/plugin install project-health-auditor@claude-code-plugins-plus
```

## Using MCP Tools Directly

### 1. List Repository Files

```typescript
// Discover all TypeScript files
list_repo_files({
  repoPath: "/path/to/repo",
  globs: ["**/*.{ts,tsx}"],
  exclude: ["node_modules/**", "dist/**"]
})

// Response:
{
  repoPath: "/path/to/repo",
  totalFiles: 245,
  files: ["src/auth.ts", "src/utils.ts", ...],
  patterns: ["**/*.{ts,tsx}"],
  excluded: ["node_modules/**", "dist/**"]
}
```

### 2. Analyze File Metrics

```typescript
// Analyze complexity and health
file_metrics({
  filePath: "/path/to/repo/src/auth.ts"
})

// Response:
{
  file: "src/auth.ts",
  size: 2048,
  lines: 78,
  complexity: {
    cyclomatic: 25,
    functions: 2,
    averagePerFunction: 13
  },
  comments: {
    lines: 3,
    ratio: 3.85
  },
  healthScore: 45  // Poor - needs refactoring
}
```

### 3. Check Git Churn

```typescript
// Find frequently changing files
git_churn({
  repoPath: "/path/to/repo",
  since: "6 months ago"
})

// Response:
{
  repoPath: "/path/to/repo",
  since: "6 months ago",
  totalCommits: 234,
  filesChanged: 89,
  topChurnFiles: [
    {
      file: "src/auth.ts",
      commits: 18,
      authors: ["Alice", "Bob"],
      authorCount: 2
    }
  ],
  summary: {
    highChurn: 5,    // >10 commits
    mediumChurn: 12,  // 5-10 commits
    lowChurn: 72      // <5 commits
  }
}
```

### 4. Map Test Coverage

```typescript
// Find files missing tests
map_tests({
  repoPath: "/path/to/repo"
})

// Response:
{
  repoPath: "/path/to/repo",
  summary: {
    totalSourceFiles: 156,
    totalTestFiles: 97,
    testedFiles: 97,
    coverageRatio: 62.18
  },
  coverage: {
    "src/utils.ts": ["src/utils.test.ts"]
  },
  missingTests: [
    "src/auth.ts",
    "src/legacy.ts"
  ],
  recommendations: [
    " CRITICAL: Test coverage is below 80% (currently 62.18%)",
    "Add tests for 59 untested files",
    "Prioritize testing high-complexity files: src/auth.ts"
  ]
}
```

## Using the /analyze Command

The `/analyze` command combines all 4 tools into a comprehensive workflow:

```bash
/analyze /path/to/my-project
```

This will:
1. List all source files
2. Analyze complexity of key files
3. Check git churn patterns
4. Map test coverage
5. Generate prioritized recommendations

## Using the Reviewer Agent

Activate the reviewer agent for detailed refactoring recommendations:

```
I need code health recommendations for my project at /path/to/repo
```

The reviewer agent will:
- Identify technical debt hot spots (high complexity + high churn + no tests)
- Provide specific, actionable refactoring steps
- Estimate effort required
- Prioritize by business impact

## Real-World Workflow

### Scenario: New Team Member Onboarding

```bash
# 1. Get repository overview
/analyze /path/to/codebase

# 2. Review specific complex file
Use file_metrics on src/services/payment-processor.ts

# 3. Understand change patterns
Use git_churn to see which files change most frequently

# 4. Identify testing gaps
Use map_tests to find untested critical files

# 5. Get recommendations
Activate reviewer agent for prioritized refactoring plan
```

### Scenario: Technical Debt Sprint Planning

```bash
# 1. Analyze entire codebase
/analyze /path/to/repo

# 2. Get reviewer recommendations
"What are the top 5 files we should refactor this sprint?"

# 3. Deep dive on specific hot spots
Use file_metrics on each recommended file

# 4. Create sprint tasks
Use reviewer agent to break down refactoring into tasks
```

## Example Output from Sample Repo

Running `/analyze examples/sample-repo/`:

```
 Repository Overview
- Total files: 3
- Average health score: 65
- Test coverage: 33%

 URGENT - Technical Debt Hot Spots

1. src/auth.ts
   - Complexity: 25 (Severe) 
   - Health Score: 45 (Poor)
   - Tests: None 

   Actions:
   1. Add authentication flow tests TODAY
   2. Extract validateToken logic to separate functions
   3. Simplify nested conditionals
   4. Reduce cyclomatic complexity from 25 to <10

   Effort: 2-3 days
   Impact: High (auth is security-critical)

 GOOD PRACTICES

1. src/utils.ts
   - Complexity: 5 (Good)
   - Health Score: 95 (Excellent)
   - Tests:  Full coverage

   Use as reference for well-structured code!

 RECOMMENDATIONS

1.  Add tests for src/auth.ts (URGENT)
2. ️ Improve test coverage to 80%+ (currently 33%)
3.  Document complex authentication logic
```

## Tips

- **Start broad**: Use `list_repo_files` to discover the codebase
- **Focus**: Use `file_metrics` on files >300 lines or core business logic
- **Context**: Use `git_churn` to understand which files are unstable
- **Safety**: Use `map_tests` before refactoring to ensure coverage
- **Action**: Use reviewer agent to turn metrics into concrete tasks
