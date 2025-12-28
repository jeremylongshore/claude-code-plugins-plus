# Virtual Environment Testing Suite

Comprehensive testing infrastructure for claude-code-plugins supporting both Docker-based and native environment testing.

## Overview

This testing suite validates the codebase in isolated environments to ensure:

- Clean installation from scratch
- Build completeness and correctness
- Cross-platform compatibility
- Plugin validation and integrity
- Marketplace synchronization
- Resource optimization

## Quick Start

### Option 1: Clean Environment Testing (No Docker)

```bash
# Run clean environment tests
bash scripts/test-clean-environment.sh

# Run from specific directory
bash scripts/test-clean-environment.sh /path/to/repo

# View results
cat test-results/*.log
```

### Option 2: Docker-based Testing

```bash
# Full test suite
bash scripts/test-docker-suite.sh

# Production test only
bash scripts/test-docker-suite.sh --target production

# Build images without running tests
bash scripts/test-docker-suite.sh --build-only

# Use Docker Compose
bash scripts/test-docker-suite.sh --docker-compose

# Verbose output with cleanup
bash scripts/test-docker-suite.sh -v --cleanup
```

### Option 3: Docker Compose Direct

```bash
# Full test suite
docker-compose -f docker-compose.test.yml up test-full

# Production test
docker-compose -f docker-compose.test.yml up test-production

# Validation only
docker-compose -f docker-compose.test.yml up test-validation

# Interactive shell in test environment
docker-compose -f docker-compose.test.yml run --rm test-full bash
```

## Test Components

### 1. Clean Environment Test Script

**File**: `scripts/test-clean-environment.sh`

Tests that the project works in a completely clean environment without any pre-installed dependencies.

**What it tests:**
1. Required tools availability (Node, npm, pnpm, jq, git, Python3)
2. Project structure validation
3. Dependency installation from lock file
4. Full build process
5. Test suite execution
6. Linting checks
7. Type checking
8. Plugin validation
9. Marketplace sync verification
10. Environment metrics (disk usage, versions)
11. Python validation scripts

**Output**: Detailed log file with pass/fail status for each test

**Advantages:**
- No Docker required
- Works on any system with Node.js
- Fast execution
- Good for local development
- Cross-platform compatible

**Disadvantages:**
- Shares system packages
- May be affected by local configuration
- Less isolated than Docker

### 2. Dockerfile for Testing

**File**: `Dockerfile.test`

Multi-stage Dockerfile with three testing targets:

#### Target: `test`
Full test environment with all build and validation tools
- Node.js 20 Alpine
- Python 3, jq, git, curl
- Full dependency installation
- Build execution
- All validation scripts
- Test output available

#### Target: `production-test`
Minimal production environment
- Optimized for size
- Essential tools only
- Tests final distribution
- Health checks included
- Performance metrics

#### Target: `builder`
Build-only environment for continuous integration

**Build Command:**
```bash
docker build -f Dockerfile.test -t claude-plugins-test .
docker build -f Dockerfile.test -t claude-plugins-test-prod --target production-test .
```

**Run Command:**
```bash
docker run --rm -v ./test-results:/app/test-results claude-plugins-test
```

### 3. Docker Compose Configuration

**File**: `docker-compose.test.yml`

Defines three composable test services:

#### `test-full`
- Full build and validation pipeline
- Runs: build → test → lint → typecheck → validation
- Volume mounts for test results
- Environment: test mode

#### `test-production`
- Minimal production environment test
- Tests distribution footprint
- Health checks
- Performance metrics
- Volume mounts for results

#### `test-validation`
- Plugin validation only
- Faster execution
- Focused on catalog verification
- Isolated validation environment

**Usage:**
```bash
# Run specific service
docker-compose -f docker-compose.test.yml run test-full

# View logs
docker-compose -f docker-compose.test.yml logs -f test-full

# Stop all services
docker-compose -f docker-compose.test.yml down
```

### 4. Docker Test Suite Runner

**File**: `scripts/test-docker-suite.sh`

Orchestrates Docker-based testing with convenient CLI

**Features:**
- Multiple test targets (full, production, validation, all)
- Image building with caching
- Results aggregation
- Cleanup utilities
- Verbose logging
- Docker or Docker Compose backend

**Usage:**
```bash
bash scripts/test-docker-suite.sh [OPTIONS]

Options:
  -t, --target TESTNAME    Test target: full|production|validation|all
  -b, --build-only         Build images without running tests
  -c, --cleanup            Cleanup old containers/images after tests
  -v, --verbose            Verbose output
  --docker-compose         Use docker-compose instead of docker build
  -h, --help               Show help message
```

### 5. .dockerignore Configuration

**File**: `.dockerignore`

Optimizes Docker build context by excluding:
- Git history and configuration
- node_modules (installed fresh)
- Build artifacts
- Environment files
- IDE settings
- Test logs
- Archive and documentation

Reduces Docker build context size significantly.

## Test Execution Workflows

### Workflow 1: Local Development

```bash
# Before committing changes
bash scripts/test-clean-environment.sh

# Check output
cat test-results/validation-output.log

# Fix any issues
# ... make changes ...

# Verify marketplace sync
pnpm run sync-marketplace

# Test again
bash scripts/test-clean-environment.sh
```

### Workflow 2: Pre-Release Testing

```bash
# Build Docker images
bash scripts/test-docker-suite.sh --build-only

# Run all test targets
bash scripts/test-docker-suite.sh --target all

# Review results
ls -la test-results/

# Check specific log
cat test-results/validation-output.log | tail -50
```

### Workflow 3: Continuous Integration

```bash
# In CI/CD pipeline
bash scripts/test-clean-environment.sh

# Or with Docker
bash scripts/test-docker-suite.sh --docker-compose

# Fail if tests fail
exit $?
```

### Workflow 4: Cross-Platform Verification

```bash
# On Linux
bash scripts/test-clean-environment.sh

# On macOS
bash scripts/test-clean-environment.sh

# With Docker (cross-platform)
bash scripts/test-docker-suite.sh
```

## Test Results

### Log Files

Test results are saved to `test-results/` directory:

```
test-results/
├── build-output.log          # pnpm build output
├── test-output.log           # pnpm test output
├── lint-output.log           # pnpm lint output
├── typecheck-output.log      # TypeScript type checking
├── validation-output.log     # Plugin validation results
├── sync-output.log           # Marketplace sync check
├── python-validation.log     # Python script validation
└── test-full.log             # Docker test container output
```

### Interpreting Results

**Success indicators:**
```
✓ All critical tests passed!
```

**Warning indicators:**
```
⚠ Some validation warnings found (not critical)
```

**Failure indicators:**
```
✗ Build failed (see test-results/build-output.log)
```

### Common Issues & Solutions

#### Issue: pnpm not found
```bash
# Solution
npm install -g pnpm@9.15.9
bash scripts/test-clean-environment.sh
```

#### Issue: Docker not found
```bash
# Solution: Either
# 1. Install Docker
# 2. Use native test script instead
bash scripts/test-clean-environment.sh
```

#### Issue: Build fails in test environment
```bash
# Check detailed output
cat test-results/build-output.log

# Verify dependencies
pnpm ls | head -50

# Check for breaking changes
git diff HEAD~1 package.json
```

#### Issue: Validation fails
```bash
# Run validation directly
bash scripts/validate-all-plugins.sh

# Check specific plugin
bash scripts/validate-all-plugins.sh plugins/[category]/[name]/

# Review validation output
cat test-results/validation-output.log
```

## Performance Metrics

### Clean Environment Test
- **Duration**: 2-5 minutes (depends on system)
- **Disk Usage**: ~1.5 GB (node_modules)
- **Memory**: ~500 MB peak
- **Network**: One-time dependency download

### Docker Test
- **Build Time**: 5-10 minutes (first build)
- **Build Time**: 1-2 minutes (cached build)
- **Container Size**: ~800 MB (test target)
- **Container Size**: ~300 MB (production target)
- **Startup Time**: 30-60 seconds

## Environment Isolation

### Clean Environment Test
- Uses temporary `/tmp/` directory
- No pollution of global Node.js packages
- Automatic cleanup on completion
- Per-test isolation with PID suffix

### Docker-based Test
- Complete filesystem isolation
- No host system pollution
- Repeatable across machines
- Full reproducibility

## Multi-Platform Support

### Linux
```bash
# Native test
bash scripts/test-clean-environment.sh

# Docker test
docker build -f Dockerfile.test -t claude-plugins-test .
docker run --rm claude-plugins-test
```

### macOS
```bash
# Native test (Intel/Apple Silicon)
bash scripts/test-clean-environment.sh

# Docker test (multi-arch support)
docker buildx build -f Dockerfile.test -t claude-plugins-test .
```

### Windows (WSL2)
```bash
# In Windows Subsystem for Linux
bash scripts/test-clean-environment.sh

# Or use Docker Desktop
docker build -f Dockerfile.test -t claude-plugins-test .
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Environment

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Run clean environment test
        run: bash scripts/test-clean-environment.sh

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test-results/
```

### Docker-based CI/CD Example

```yaml
test:
  stage: test
  script:
    - bash scripts/test-docker-suite.sh --target all
  artifacts:
    paths:
      - test-results/
    when: always
```

## Customization

### Create Custom Test Script

```bash
#!/bin/bash
# custom-test.sh

# Source the base test script
source scripts/test-clean-environment.sh

# Add custom test
echo "Running custom validation..."
my_custom_test() {
    # Your test logic
}

my_custom_test
```

### Modify Docker Configuration

```bash
# Build with custom tag
docker build -f Dockerfile.test \
    -t my-registry/claude-plugins:test-1.0.0 \
    --target test .
```

### Extend docker-compose.test.yml

```yaml
services:
  test-custom:
    build:
      context: .
      dockerfile: Dockerfile.test
      target: test
    environment:
      CUSTOM_VAR: "value"
    command: bash -c "echo 'Custom test'"
```

## Troubleshooting

### Test Hangs
```bash
# Set timeout
timeout 600 bash scripts/test-clean-environment.sh

# Kill hanging Docker container
docker kill $(docker ps -q)
```

### Out of Disk Space
```bash
# Clean Docker images and containers
docker system prune -a

# Clean node_modules
rm -rf node_modules
pnpm install --frozen-lockfile
```

### Permission Issues

```bash
# Fix script permissions
chmod +x scripts/test-*.sh

# Fix Docker socket access (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

### Marketplace Sync Failures

```bash
# Run sync manually
pnpm run sync-marketplace

# Check git status
git status

# Verify JSON syntax
jq empty .claude-plugin/marketplace.extended.json
```

## Best Practices

1. **Run tests before committing**
   ```bash
   bash scripts/test-clean-environment.sh
   ```

2. **Use Docker for reproducibility**
   ```bash
   bash scripts/test-docker-suite.sh --target all
   ```

3. **Check test results regularly**
   ```bash
   tail -20 test-results/validation-output.log
   ```

4. **Clean up after tests**
   ```bash
   bash scripts/test-docker-suite.sh --cleanup
   ```

5. **Use verbose mode for debugging**
   ```bash
   bash scripts/test-docker-suite.sh -v
   ```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Node.js Best Practices](https://nodejs.org/en/docs/)
- [pnpm Documentation](https://pnpm.io/)
- [CONTRIBUTING.md](./000-docs/007-DR-GUID-contributing.md) - Contribution guidelines

## Support

For issues with the testing suite:

1. Check `TROUBLESHOOTING.md`
2. Review test logs in `test-results/`
3. Run with verbose flag: `-v` or `--verbose`
4. Check Docker logs: `docker logs <container-id>`

## Version History

- **v1.0.0** (2025-12-24) - Initial test suite implementation
  - Clean environment testing
  - Docker multi-stage support
  - Docker Compose orchestration
  - Comprehensive validation pipeline
