---
name: orchestrating-test-execution
description: |
  Test coordinate parallel test execution across multiple environments and frameworks.
  Use when performing specialized testing.
  Trigger with phrases like "orchestrate tests", "run parallel tests", or "coordinate test execution".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:orchestrate-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Test Orchestrator

## Overview

Coordinate parallel test execution across multiple test suites, frameworks, and environments. Manages test splitting, worker allocation, result aggregation, and intelligent retry strategies. Supports Jest `--shard`, pytest-xdist, Playwright sharding, and custom CI matrix configurations for maximum throughput.

## Prerequisites

- Test runner with parallel execution support (Jest, Vitest, pytest-xdist, Playwright, or JUnit 5)
- CI/CD platform configured (GitHub Actions, GitLab CI, CircleCI, or Jenkins)
- Test suite with consistent pass rates (flaky tests identified and tagged)
- Sufficient CI runner resources for parallel worker count
- Test result reporting tool (JUnit XML, Allure, or equivalent)

## Instructions

1. Analyze the existing test suite using Grep and Glob to catalog all test files, their framework, approximate run time, and dependency requirements.
2. Classify tests into execution tiers:
   - **Tier 1 (Fast)**: Unit tests with no I/O -- target under 30 seconds total.
   - **Tier 2 (Medium)**: Integration tests requiring local services -- target under 3 minutes.
   - **Tier 3 (Slow)**: E2E and browser tests -- target under 10 minutes.
3. Configure parallel execution for each tier:
   - Split unit tests across N workers using `jest --shard=i/N` or `pytest -n auto`.
   - Shard E2E tests by test file using Playwright `--shard=i/N` or Cypress parallelization.
   - Assign heavier integration tests to dedicated workers with more resources.
4. Create a CI pipeline configuration that runs tiers in parallel:
   - Tier 1 and Tier 2 run concurrently on separate jobs.
   - Tier 3 runs after a fast pre-check gate passes.
   - Each tier reports results to a unified collection step.
5. Implement intelligent retry logic for flaky tests:
   - Tag known flaky tests with `@flaky` or equivalent marker.
   - Retry failed tests up to 2 times before marking as failed.
   - Track flaky test frequency in a log file for triage.
6. Aggregate results from all parallel workers into a single report:
   - Merge JUnit XML files from each shard.
   - Calculate total pass/fail/skip counts and execution time.
   - Identify the slowest tests for optimization targets.
7. Write the orchestration configuration to the project's CI config file and validate it with a dry run.

## Output

- CI pipeline configuration file (`.github/workflows/test.yml`, `.gitlab-ci.yml`, or equivalent)
- Test sharding configuration with worker count and split strategy
- Merged test result report in JUnit XML or JSON format
- Execution timeline showing parallel job durations and bottlenecks
- Flaky test inventory with retry counts and failure patterns

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Shard produces zero tests | Uneven test distribution or incorrect shard index | Verify shard count matches actual test file count; use file-based splitting |
| Worker out of memory | Too many parallel processes on one runner | Reduce `--maxWorkers` or `-n` count; increase runner memory; use `--workerIdleMemoryLimit` |
| Test ordering dependency | Tests pass in isolation but fail in specific shard order | Add `--randomize` flag; fix shared state leaks; enforce test independence |
| Result aggregation mismatch | Missing shard results due to job timeout | Set job-level timeouts higher than test timeouts; add result upload as a separate step |
| CI cache miss slowing startup | Dependencies not cached between parallel jobs | Configure dependency caching per lockfile hash; use a shared setup job |

## Examples

**GitHub Actions matrix strategy for Jest sharding:**
```yaml
jobs:
  test:
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - run: npx jest --shard=${{ matrix.shard }}/4 --ci --reporters=jest-junit
      - uses: actions/upload-artifact@v4
        with:
          name: results-${{ matrix.shard }}
          path: junit.xml
  merge:
    needs: test
    steps:
      - uses: actions/download-artifact@v4
      - run: npx junit-merge -d results-* -o merged-results.xml
```

**pytest-xdist parallel execution:**
```bash
pytest -n auto --dist worksteal -q --junitxml=results.xml
```

**Playwright sharded execution:**
```bash
npx playwright test --shard=1/3 --reporter=junit
```

## Resources

- Jest sharding: https://jestjs.io/docs/cli#--shardshardindex-shardcount
- pytest-xdist: https://pytest-xdist.readthedocs.io/
- Playwright test sharding: https://playwright.dev/docs/test-sharding
- GitHub Actions matrix strategy: https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs
- JUnit XML merge tools: https://github.com/imsky/junit-merge
