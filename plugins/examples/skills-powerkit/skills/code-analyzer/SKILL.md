---
name: Code Quality Analyzer
description: Automatically analyzes code for complexity, maintainability, and potential issues when user mentions code quality, code review, technical debt, refactoring, or code analysis. Provides actionable feedback with specific improvements.
allowed-tools: Read, Grep
---

# Code Quality Analyzer

## Purpose
Identifies code quality issues including high complexity, code smells, maintainability concerns, and anti-patterns in any programming language.

## Trigger Keywords
- "code quality"
- "code review"
- "analyze code"
- "technical debt"
- "refactor" or "refactoring"
- "complexity"
- "code smell"
- "maintainability"

## Analysis Process

When activated, I will:

1. **Scan the codebase** using Read and Grep tools
2. **Identify complexity hotspots** - functions/methods with high cyclomatic complexity
3. **Detect code smells**:
   - Long methods (>50 lines)
   - Deep nesting (>4 levels)
   - Duplicate code patterns
   - Large classes (>500 lines)
   - Too many parameters (>5)
   - Magic numbers without constants
4. **Check for anti-patterns**:
   - God objects
   - Circular dependencies
   - Improper error handling
   - Missing abstractions
5. **Provide actionable recommendations** with specific file:line references

## Output Format

I provide results in this structure:

### Priority Issues
- **Critical**: Immediate attention needed
- **High**: Should fix soon
- **Medium**: Technical debt to address
- **Low**: Nice-to-have improvements

### For Each Issue
- File path and line number
- Issue description
- Why it matters
- Suggested fix with code example

## Restrictions

- Read-only access (no file modifications)
- Uses only Read and Grep tools
- Safe for production codebases
- No external API calls

## Examples

**User says:** "Can you review the code quality in src/api/?"

**I automatically:**
1. Scan src/api/ directory
2. Analyze all files for issues
3. Generate prioritized report
4. Suggest specific improvements

**User says:** "This function feels complex, any refactoring ideas?"

**I automatically:**
1. Read the function
2. Calculate complexity
3. Identify improvement opportunities
4. Provide step-by-step refactor plan
