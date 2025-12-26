---
name: search
description: Search AI experiments and display formatted results
shortcut: sear
---
# Search AI Experiments

When the user runs `/search-exp [query]`, search through all AI experiments and display formatted terminal results.

## Search Behavior

Search across these fields:
- AI tool name
- Prompt text
- Result text
- Tags

## Usage Examples

```bash
/search-exp code                    # Search for "code"
/search-exp tool:ChatGPT           # Filter by tool
/search-exp tag:debugging          # Filter by tag
/search-exp rating:5               # Filter by rating
/search-exp "python function"      # Search phrase
```

## Output Format

```
╔══════════════════════════════════════════════════════════════╗
║              AI EXPERIMENTS - SEARCH RESULTS                 ║
╚══════════════════════════════════════════════════════════════╝

Found 12 experiments matching "code generation"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] Oct 13, 2:30 PM | ChatGPT o1-preview | ⭐⭐⭐⭐⭐

📝 Prompt:
Write a Python function to calculate Fibonacci numbers recursively

💡 Result:
Provided clean recursive implementation with base cases. Included
time complexity analysis (O(2^n)).

🏷️  Tags: code-generation, python, algorithms
🆔 ID: exp_1697234567890_abc123def

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[2] Oct 12, 4:15 PM | Claude Sonnet 3.5 | ⭐⭐⭐⭐

📝 Prompt:
Generate TypeScript interfaces from JSON schema

💡 Result:
Created well-typed interfaces with proper nested types and
optional fields.

🏷️  Tags: code-generation, typescript, types
🆔 ID: exp_1697148912345_xyz789abc

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 QUICK STATS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total results: 12 experiments
Average rating: 4.42 ⭐
Most common tool: ChatGPT o1-preview (7 experiments)
Most common tag: code-generation (12 experiments)
```

## Advanced Filters

Support combined filters:
```bash
/search-exp tool:ChatGPT rating:5 tag:python
```

Parse and apply each filter:
- `tool:X` → Filter by AI tool
- `rating:X` → Filter by rating (1-5)
- `tag:X` → Filter by tag
- `date:YYYY-MM-DD` → Filter by specific date
- `from:YYYY-MM-DD` → From date
- `to:YYYY-MM-DD` → To date

## Empty Results

```
╔══════════════════════════════════════════════════════════════╗
║              AI EXPERIMENTS - SEARCH RESULTS                 ║
╚══════════════════════════════════════════════════════════════╝

🔍 No experiments found matching "xyz123"

Try:
  • Broadening your search terms
  • Checking spelling
  • Using /ai-report to see all experiments
  • Using different filter criteria
```

## Sorting Options

Support sorting with suffix:
```bash
/search-exp code :date        # Sort by date (newest first)
/search-exp code :rating      # Sort by rating (highest first)
/search-exp code :tool        # Sort by tool name (alphabetical)
```

## Limit Results

Default to showing 10 results, with pagination hint:
```
Showing 10 of 45 results. Use filters to narrow down.
```

## Implementation

Use the `list_experiments` MCP tool with appropriate filters:
- `searchQuery` for text search
- `aiTool` for tool filter
- `rating` for rating filter
- `tags` for tag filter
- `dateFrom` / `dateTo` for date range

Format output to be readable in terminal with proper spacing and visual hierarchy.
