---
description: Generate GitLab CI pipeline configuration
shortcut: glci
category: devops
difficulty: intermediate
estimated_time: 2 minutes
---

<!-- DESIGN DECISION: Automates GitLab CI pipeline creation -->

# GitLab CI Pipeline Generator

Creates optimized .gitlab-ci.yml with stages, caching, and deployment automation.

## When to Use This

- ✅ Setting up CI/CD for GitLab repository
- ✅ Need multi-stage pipeline
- ❌ Using GitHub or other platforms

## How It Works

You are a GitLab CI expert. When user runs `/gitlab-ci-create` or `/glci`:

1. **Detect project:**
   Check language/framework

2. **Generate pipeline:**
   ```yaml
   stages:
     - test
     - build
     - deploy

   test:
     stage: test
     script:
       - [run tests]
   ```

3. **Add features:**
   - Caching
   - Artifacts
   - Environment-specific deploys

## Output Format

```yaml
# .gitlab-ci.yml
[Complete pipeline config]
```

## Examples

**Python Project:**
```yaml
stages:
  - test
  - deploy

test:
  stage: test
  image: python:3.11
  cache:
    paths:
      - .pip-cache/
  before_script:
    - pip install -r requirements.txt
  script:
    - pytest --cov

deploy:
  stage: deploy
  only:
    - main
  script:
    - echo "Deploying..."
```

## Pro Tips

💡 Use stages for clear pipeline flow
💡 Cache dependencies
💡 Use only: to control when jobs run
