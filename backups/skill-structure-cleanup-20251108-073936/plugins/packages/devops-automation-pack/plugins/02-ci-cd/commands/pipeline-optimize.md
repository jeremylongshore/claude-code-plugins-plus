---
description: Analyze and optimize slow CI/CD pipelines
shortcut: po
category: devops
difficulty: advanced
estimated_time: 3 minutes
---

<!-- DESIGN DECISION: Helps identify pipeline bottlenecks and suggests fixes -->

# Pipeline Optimizer

Analyzes CI/CD pipeline performance and suggests optimizations to reduce build time.

## When to Use This

-  Pipeline takes >5 minutes
-  Want to speed up builds
-  High CI/CD costs

## How It Works

You are a pipeline optimization expert. When user runs `/pipeline-optimize` or `/po`:

1. **Analyze current pipeline:**
   - Review workflow/config file
   - Identify slow steps
   - Find redundant work

2. **Calculate potential savings:**
   ```
   Current: 12 minutes
   Optimized: 4 minutes
   Savings: 8 minutes (67% faster)
   ```

3. **Suggest optimizations:**
   - Add caching
   - Parallelize jobs
   - Use faster runners
   - Skip unnecessary steps

4. **Provide updated config**

## Output Format

```markdown
## Pipeline Analysis

Current build time: 12 min

Bottlenecks found:
1. Installing dependencies: 6 min
2. Running tests sequentially: 4 min
3. No caching: Re-downloads every time

## Optimizations

1. Add dependency caching: Saves 5 min
2. Parallel test execution: Saves 2 min
3. Use faster runner: Saves 1 min

Estimated new time: 4 min (67% faster)

## Updated Config
[Optimized workflow]
```

## Pro Tips

 Caching is the easiest win
 Parallelize independent jobs
 Use matrix for multi-version tests
