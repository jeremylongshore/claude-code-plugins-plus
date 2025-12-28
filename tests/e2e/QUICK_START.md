# E2E Tests - Quick Start Guide

Get started with E2E testing in 5 minutes.

## Prerequisites

- Node.js 20+
- pnpm 9.15.9+
- Access to repository root

## Installation

From repository root:

```bash
# Install all workspace dependencies (includes E2E tests)
pnpm install
```

## Running Tests

### All E2E Tests

```bash
# From repository root
pnpm test:e2e

# From tests/e2e directory
pnpm test
```

### Specific Test Suite

```bash
# Plugin installation tests only
pnpm test:e2e -- scenarios/plugin-install.test.ts

# Skill activation tests only
pnpm test:e2e -- scenarios/skill-activation.test.ts

# MCP communication tests only
pnpm test:e2e -- scenarios/mcp-communication.test.ts
```

### Watch Mode (Development)

```bash
# Auto-run tests on file changes
pnpm test:e2e:watch
```

### Coverage Report

```bash
# Generate coverage report
pnpm test:e2e:coverage

# Open HTML coverage report
open tests/e2e/coverage/index.html
```

### Debug Mode

```bash
# Verbose output with test artifacts preserved
pnpm test:e2e:debug
```

## Test Scenarios

### 1. Plugin Installation (15 tests)

**File:** `scenarios/plugin-install.test.ts`

Tests the complete plugin lifecycle:
- Installation from valid source
- File copying and validation
- Schema validation
- Duplicate installation handling
- Uninstallation and cleanup
- Multiple plugin management

**Run:**
```bash
pnpm test:e2e -- plugin-install
```

### 2. Skill Activation (18 tests)

**File:** `scenarios/skill-activation.test.ts`

Tests skill discovery and activation:
- Skill loading from plugins
- Frontmatter parsing
- Trigger phrase detection
- Tool permissions validation
- Multi-skill scenarios
- 2025 schema compliance

**Run:**
```bash
pnpm test:e2e -- skill-activation
```

### 3. MCP Server Communication (12 tests)

**File:** `scenarios/mcp-communication.test.ts`

Tests MCP server interactions:
- Server startup and shutdown
- Tool registration
- Tool invocation
- Error handling
- Concurrent operations

**Run:**
```bash
pnpm test:e2e -- mcp-communication
```

## Expected Output

### Successful Run

```
✓ tests/e2e/scenarios/plugin-install.test.ts (15 tests) 2.5s
✓ tests/e2e/scenarios/skill-activation.test.ts (18 tests) 3.1s
✓ tests/e2e/scenarios/mcp-communication.test.ts (12 tests) 4.2s

Test Files  3 passed (3)
     Tests  45 passed (45)
  Start at  13:45:23
  Duration  9.8s
```

### With Coverage

```
% Coverage report from v8
---------------------|---------|---------|---------|---------
File                 | % Stmts | % Branch| % Funcs | % Lines
---------------------|---------|---------|---------|---------
All files            |   85.32 |   78.45 |   82.11 |   85.32
 setup.ts            |   92.15 |   84.62 |   90.00 |   92.15
 plugin-install.ts   |   88.24 |   75.00 |   85.71 |   88.24
 skill-activation.ts |   84.62 |   77.78 |   80.00 |   84.62
 mcp-communication.ts|   79.41 |   71.43 |   76.92 |   79.41
---------------------|---------|---------|---------|---------
```

## Troubleshooting

### Tests Fail to Start

**Issue:** `Cannot find module 'vitest'`

**Solution:**
```bash
cd tests/e2e
pnpm install
```

### Permission Errors

**Issue:** `EACCES: permission denied`

**Solution:**
```bash
# Ensure /tmp directory is writable
chmod 1777 /tmp

# Or set custom test directory
E2E_TEST_DIR=/home/user/test-tmp pnpm test:e2e
```

### Timeout Errors

**Issue:** `Test timeout of 30000ms exceeded`

**Solution:**
```bash
# Increase timeout for slow systems
E2E_TEST_TIMEOUT=60000 pnpm test:e2e
```

### Old Test Artifacts

**Issue:** `/tmp/claude-e2e-test-*` directories accumulate

**Solution:**
```bash
# Tests auto-cleanup old directories (>1 hour)
# Manual cleanup:
rm -rf /tmp/claude-e2e-test-*

# Or keep artifacts for debugging:
E2E_KEEP_ARTIFACTS=true pnpm test:e2e
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `E2E_TEST_TIMEOUT` | `30000` | Test timeout in milliseconds |
| `E2E_DEBUG` | `false` | Enable verbose logging |
| `E2E_KEEP_ARTIFACTS` | `false` | Keep test directories after run |
| `E2E_TEST_DIR` | `/tmp` | Base directory for test environments |

## Test Fixtures

All test fixtures are in `fixtures/`:

- **test-plugin/** - Minimal valid plugin
  - `.claude-plugin/plugin.json` - Plugin manifest
  - `README.md` - Documentation
  - `skills/test-skill/SKILL.md` - Test skill
  - `commands/test-command.md` - Test command

## Development Workflow

### Adding New Tests

1. Choose appropriate scenario file or create new one
2. Follow Arrange-Act-Assert pattern
3. Use setup utilities from `setup.ts`
4. Ensure proper cleanup in `afterEach`
5. Test both success and error paths

### Example Test

```typescript
it('should install plugin successfully', async () => {
  // Arrange
  const env = await createTestEnv();
  const pluginPath = path.join(__dirname, 'fixtures/test-plugin');

  // Act
  const metadata = await installPlugin(env, pluginPath);

  // Assert
  expect(metadata.name).toBe('test-plugin');
  expect(env.installedPlugins.has('test-plugin')).toBe(true);

  // Cleanup
  await env.cleanup();
});
```

## CI/CD Integration

Tests run automatically in GitHub Actions on:
- Pull requests
- Push to main branch
- Manual workflow dispatch

See `.github/workflows/e2e-tests.yml` (to be created)

## Performance Targets

- Single test: < 5 seconds
- Full suite: < 60 seconds
- With coverage: < 90 seconds

## Next Steps

1. Read full documentation: `README.md`
2. Explore test scenarios in `scenarios/`
3. Review setup utilities in `setup.ts`
4. Add new test cases for your features

## Support

- GitHub Issues: https://github.com/jeremylongshore/claude-code-plugins/issues
- Documentation: `/tests/e2e/README.md`
- Email: jeremy@intentsolutions.io
