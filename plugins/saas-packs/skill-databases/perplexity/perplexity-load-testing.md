# perplexity-load-testing

> Load test Perplexity integrations for scale

## Directory Structure

```
perplexity-load-testing/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── locust_test.py          # Locust load test script
    ├── k6_test.js              # k6 load test script
    ├── load_profiles.yaml      # Load test profiles
    └── results_analyzer.py     # Analyze load test results
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with load testing patterns |
| `locust_test.py` | Python | Locust load testing implementation |
| `k6_test.js` | JavaScript | k6 load testing script |
| `load_profiles.yaml` | YAML | Define load test scenarios |
| `results_analyzer.py` | Python | Analyze and report on results |

## Summary

**Category:** cicd
**Target Audience:** Performance engineer
**Trigger Phrases:** `perplexity load test`, `perplexity performance`, `stress test perplexity`, `perplexity capacity`

### What This Skill Does

This skill teaches load testing for Perplexity:

- Designing load test scenarios
- Using Locust or k6 for testing
- Simulating production traffic patterns
- Analyzing bottlenecks and limits
- Capacity planning based on results

### Technical Success Criteria

- Performance validated under expected load
- Bottlenecks identified and documented
- Latency percentiles measured

### Business Success Criteria

- Confidence in system scalability
- Capacity planning data available
- Performance baselines established

## Related Skills

- `perplexity-rate-limits` - Understand limits during load
- `perplexity-caching-strategy` - Cache impact on performance
- `perplexity-monitoring-alerts` - Monitor during load tests
