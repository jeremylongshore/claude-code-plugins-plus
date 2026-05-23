# Directory Structure

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
