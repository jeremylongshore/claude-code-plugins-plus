# Sample Repository

This is an example repository to demonstrate the **project-health-auditor** MCP server.

## Files

- **`src/auth.ts`** - High complexity file (cyclomatic complexity >20) with no tests
- **`src/utils.ts`** - Low complexity, well-maintained utility functions
- **`src/utils.test.ts`** - Test file demonstrating good coverage

## Expected Analysis Results

When analyzed with the MCP server:

### File Metrics
- `auth.ts`: High complexity (~25), low health score (<50), missing tests
- `utils.ts`: Low complexity (~5), high health score (>80), has tests

### Git Churn
If you commit changes to `auth.ts` multiple times, it will show high churn.

### Test Coverage
- `utils.ts`: ✅ Has test file
- `auth.ts`: ❌ Missing test file

### Recommendations
The analyzer should recommend:
1. 🚨 **URGENT**: Add tests for `auth.ts` (high complexity + no tests)
2. ⚠️ **Refactor**: Break down `validateToken()` and `login()` methods in `auth.ts`
3. ✅ **Good**: Keep `utils.ts` as reference for well-structured code
