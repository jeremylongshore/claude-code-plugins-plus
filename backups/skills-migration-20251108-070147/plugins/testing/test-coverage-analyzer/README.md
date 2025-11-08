# Test Coverage Analyzer Plugin

Analyze code coverage metrics, identify untested code, and generate comprehensive coverage reports.

## Features

- **Multi-metric coverage** - Lines, branches, functions, statements
- **Untested code identification** - Find coverage gaps
- **Coverage trends** - Track improvements over time
- **Threshold enforcement** - Minimum coverage requirements
- **Detailed reports** - Per-file, per-function analysis
- **Visual coverage maps** - Highlight uncovered code

## Installation

```bash
/plugin install test-coverage-analyzer@claude-code-plugins-plus
```

## Usage

```bash
/analyze-coverage              # Full coverage analysis
/analyze-coverage --threshold 80
/cov                          # Shortcut
```

## Requirements

- Claude Code CLI
- Coverage tool (nyc, coverage.py, JaCoCo, etc.)

## License

MIT
