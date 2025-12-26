---
name: validate-budget
description: Validate against performance budgets
---
# Performance Budget Validator

Create and validate performance budgets to prevent performance regressions.

## Budget Categories

1. **Page Load Times**: First Contentful Paint, Time to Interactive
2. **Bundle Sizes**: JavaScript, CSS, image sizes
3. **Request Counts**: Number of HTTP requests
4. **API Response Times**: Backend endpoint latency
5. **Lighthouse Scores**: Performance, accessibility, SEO scores

## Process

1. Analyze current performance metrics
2. Define performance budget thresholds
3. Create budget validation configuration
4. Implement CI/CD integration
5. Generate monitoring and alerting setup

## Output

Provide:
- Performance budget configuration file
- Validation scripts (Lighthouse CI, webpack-bundle-analyzer, etc.)
- CI/CD pipeline integration guide
- Dashboard for budget tracking
- Alert setup for budget violations
- Remediation workflow recommendations
