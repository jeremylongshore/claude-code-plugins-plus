# Smoke Test Runner

Quick smoke test suites to verify critical functionality after deployments.

## Installation

```bash
/plugin install smoke-test-runner@claude-code-plugins-plus
```

## Usage

```bash
/smoke-test
# or shortcut
/st
```

## Features

- **Fast Execution**: Complete suite runs in <5 minutes
- **Critical Path Focus**: Test only must-work functionality
- **Post-Deployment**: Automatic verification after deployments
- **Clear Results**: Fast pass/fail with rollback recommendations
- **Environment Validation**: Config and integration checks

## Example Workflow

```bash
# Generate smoke test suite
/smoke-test

# Claude creates:
#  Health checks
#  Authentication tests
#  Core feature validation
#  Integration checks
#  Post-deployment script
```

## Test Categories

- System Health (API, DB, Cache)
- Authentication
- Core Features
- External Integrations
- Configuration

## Files

- `commands/smoke-test.md` - Smoke testing command

## License

MIT
