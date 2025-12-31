# perplexity-testing-framework

> Implement testing strategies for Perplexity integrations

## Directory Structure

```
perplexity-testing-framework/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── test_fixtures.py        # Test fixtures and mocks
    ├── mock_responses.py       # Mock Perplexity responses
    ├── integration_tests.py    # Integration test suite
    └── pytest.ini              # Pytest configuration
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with testing patterns |
| `test_fixtures.py` | Python | Reusable test fixtures and setup |
| `mock_responses.py` | Python | Mock Perplexity API responses |
| `integration_tests.py` | Python | Integration test examples |
| `pytest.ini` | Config | Pytest configuration for test suite |

## Summary

**Category:** cicd
**Target Audience:** Developer testing integrations
**Trigger Phrases:** `perplexity testing`, `test perplexity`, `perplexity mock`, `perplexity ci`

### What This Skill Does

This skill teaches testing for Perplexity integrations:

- Unit testing with mocked responses
- Integration testing with live API
- Mock response generation
- CI/CD pipeline integration
- Test coverage strategies

### Technical Success Criteria

- Comprehensive test coverage with mocking
- Integration tests passing reliably
- CI pipeline configured correctly

### Business Success Criteria

- Reliable deployments with quality gates
- Reduced production bugs
- Developer confidence in changes

## Related Skills

- `perplexity-sdk-patterns` - Test client implementations
- `perplexity-response-validation` - Test validation logic
- `perplexity-prod-checklist` - Testing as part of readiness
