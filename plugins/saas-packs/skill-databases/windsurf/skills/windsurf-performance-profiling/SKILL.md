---
name: windsurf-performance-profiling
description: |
  Profile and optimize code with AI-assisted analysis. Activate when users mention
  "performance profiling", "optimize performance", "bottleneck analysis", "profiling",
  or "performance tuning". Handles performance analysis and optimization.
allowed-tools: Read,Write,Edit,Bash,Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Performance Profiling

Profile and optimize code with AI-assisted performance analysis.

## Directory Structure

```
project-root/
    .windsurf/
        performance/
            profiles/
                baseline.profile.json        # Baseline performance profile
                    # Metric baselines
                    # Execution times
                    # Memory usage

                current.profile.json         # Current performance data
                    # Latest metrics
                    # Comparison to baseline
                    # Trend analysis

            reports/
                bottleneck-analysis.md       # Bottleneck identification
                    # Hot paths
                    # Memory leaks
                    # I/O bottlenecks

                optimization-plan.md         # Optimization recommendations
                    # Priority ranking
                    # Expected impact
                    # Implementation effort

                before-after.md              # Improvement documentation
                    # Metrics comparison
                    # Changes made
                    # Lessons learned

            config/
                profiler-config.json         # Profiler settings
                    # Sampling rate
                    # Tracked metrics
                    # Output format

                thresholds.json              # Performance thresholds
                    # Response time limits
                    # Memory limits
                    # CPU limits

            benchmarks/
                benchmark-suite.json         # Benchmark definitions
                    # Test scenarios
                    # Expected values
                    # Tolerance ranges

                results/
                    YYYY-MM-DD.json          # Benchmark results
                        # Execution times
                        # Memory usage
                        # Comparison data

            optimizations/
                applied/
                    optimization-001.md      # Applied optimization log
                        # Problem description
                        # Solution applied
                        # Impact measured

                pending/
                    optimization-queue.json  # Pending optimizations
                        # Identified issues
                        # Priority ranking
                        # Implementation notes
```

## Profiling Features

### Analysis
- CPU profiling
- Memory profiling
- I/O analysis
- Network profiling

### Optimization
- Bottleneck identification
- AI-suggested fixes
- Impact prediction
- Before/after comparison

## Configuration Steps

1. **Establish Baseline**
   - Run profiler on current code
   - Document baseline metrics
   - Set thresholds

2. **Analyze Bottlenecks**
   - Identify hot paths
   - Find memory issues
   - Locate I/O problems

3. **Optimize with Cascade**
   - Get AI optimization suggestions
   - Apply targeted fixes
   - Measure improvements

4. **Validate Results**
   - Run benchmarks
   - Compare to baseline
   - Document changes

## Success Criteria

- 20%+ latency reduction
- Measurable improvements documented
- Performance SLAs consistently met
