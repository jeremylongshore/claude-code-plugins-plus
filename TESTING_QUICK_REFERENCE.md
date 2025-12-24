# Testing Quick Reference Card

**Virtual Environment Testing Suite for claude-code-plugins**

## Three Test Options

### Option 1: Quick Test (1-2 minutes)
Perfect for development workflow
```bash
bash scripts/quick-test.sh
```
Tests: install → build → lint → validate

### Option 2: Clean Environment (2-5 minutes)
Full validation in isolated temp directory
```bash
bash scripts/test-clean-environment.sh
```
Tests: 11-stage pipeline (no Docker required)

### Option 3: Docker Test (5-10 min first, then 1-2 min)
Complete containerized testing
```bash
bash scripts/test-docker-suite.sh
bash scripts/test-docker-suite.sh --target production
bash scripts/test-docker-suite.sh --target all
```

## File Locations

| File | Purpose |
|------|---------|
| `Dockerfile.test` | Multi-stage Docker build |
| `.dockerignore` | Build context optimization |
| `docker-compose.test.yml` | Service orchestration |
| `scripts/test-clean-environment.sh` | Clean env testing |
| `scripts/test-docker-suite.sh` | Docker orchestration |
| `scripts/quick-test.sh` | Fast dev test |
| `TESTING.md` | Complete guide (6000+ words) |

## Test Coverage

- Tool verification (Node, npm, pnpm, jq, git, Python3)
- Project structure validation
- Dependency installation
- Build process
- Unit tests
- Linting
- Type checking
- Plugin validation
- Marketplace sync
- Performance metrics

## Results

All test output saved to `test-results/`
- `build-output.log`
- `test-output.log`
- `lint-output.log`
- `typecheck-output.log`
- `validation-output.log`

## Docker Compose Direct Usage

```bash
# Full test
docker-compose -f docker-compose.test.yml run test-full

# Production test
docker-compose -f docker-compose.test.yml run test-production

# Validation only
docker-compose -f docker-compose.test.yml run test-validation

# View logs
docker-compose -f docker-compose.test.yml logs -f test-full
```

## CI/CD Integration

```yaml
# GitHub Actions
- run: bash scripts/test-clean-environment.sh

# Or with Docker
- run: bash scripts/test-docker-suite.sh --docker-compose
```

## Pre-commit Integration

```bash
echo "bash scripts/quick-test.sh" >> .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| pnpm not found | `npm install -g pnpm@9.15.9` |
| Docker not found | Use native test: `bash scripts/test-clean-environment.sh` |
| Test hangs | Use timeout: `timeout 600 bash scripts/test-clean-environment.sh` |
| Permission denied | `chmod +x scripts/test-*.sh` |

## Performance

| Test Type | Duration | Disk | Memory |
|-----------|----------|------|--------|
| Quick | 1-2 min | ~500 MB | ~300 MB |
| Clean env | 2-5 min | ~1.5 GB | ~500 MB |
| Docker (1st) | 5-10 min | ~1.2 GB | ~1 GB |
| Docker (cached) | 1-2 min | 0 | ~500 MB |

## Documentation

- **Full Guide**: `TESTING.md` (12,500+ words)
- **Implementation**: `test-results/IMPLEMENTATION_REPORT.md`
- **File Reference**: `test-results/FILE_MANIFEST.md`

## Key Features

✅ Docker multi-stage builds
✅ 11-stage validation pipeline
✅ Cross-platform compatible
✅ Environment isolation
✅ Automatic cleanup
✅ CI/CD ready
✅ Detailed logging
✅ Performance metrics

---

**Quick Start**: `bash scripts/quick-test.sh`
**Full Guide**: `cat TESTING.md`
**Full Test**: `bash scripts/test-clean-environment.sh`
