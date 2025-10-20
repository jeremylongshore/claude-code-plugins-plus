---
description: Analyze code coverage metrics and identify untested code
shortcut: cov
---

# Test Coverage Analyzer

Analyze test coverage metrics, identify untested code paths, and generate comprehensive coverage reports.

## Capabilities

- **Line coverage** - Which lines are executed
- **Branch coverage** - Which branches taken
- **Function coverage** - Which functions called
- **Statement coverage** - Which statements executed
- **Uncovered code identification** - Find gaps
- **Coverage trends** - Track over time
- **Threshold enforcement** - Minimum coverage requirements

## Usage

```bash
/analyze-coverage                    # Analyze current coverage
/analyze-coverage --threshold 80     # Enforce 80% minimum
/analyze-coverage --detailed         # Detailed report
/cov                                 # Shortcut
```

## Report Format

```
Code Coverage Report
====================
Overall Coverage: 78.5%

By File:
  src/utils/validator.js     95.2%  
  src/api/users.js           82.1%  
  src/api/products.js        68.4%  ️
  src/services/payment.js    45.7%  

By Type:
  Lines:      78.5% (1,571 / 2,000)
  Branches:   72.3% (289 / 400)
  Functions:  85.1% (85 / 100)
  Statements: 78.2% (1,563 / 2,000)

Uncovered Lines:
  src/api/products.js:45-52 (error handling)
  src/api/products.js:78-82 (edge case)
  src/services/payment.js:23-67 (refund logic)

Recommendations:
  1. Add tests for payment service refund logic
  2. Test error handling in products API
  3. Cover edge cases in product filtering
```

## Best Practices

- Aim for 80%+ coverage
- 100% coverage != bug-free
- Focus on critical paths
- Cover edge cases
- Test error handling
- Track coverage trends
