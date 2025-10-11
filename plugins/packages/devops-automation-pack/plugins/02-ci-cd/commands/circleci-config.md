---
description: Generate CircleCI configuration file
shortcut: cci
category: devops
difficulty: intermediate
estimated_time: 2 minutes
---

<!-- DESIGN DECISION: Automates CircleCI config creation -->

# CircleCI Config Generator

Creates optimized .circleci/config.yml with orbs, workflows, and caching.

## When to Use This

-  Setting up CircleCI for project
-  Want platform-agnostic CI/CD
-  Using GitHub Actions or GitLab CI

## How It Works

You are a CircleCI expert. When user runs `/circleci-config` or `/cci`:

1. **Detect project type**

2. **Generate config:**
   ```yaml
   version: 2.1
   orbs:
     [language]: [orb-name]
   workflows:
     build-test:
       jobs:
         - test
   ```

3. **Add optimizations:**
   - Orbs for common tasks
   - Caching
   - Parallelism

## Output Format

```yaml
# .circleci/config.yml
[Complete config]
```

## Examples

**Node.js with Orb:**
```yaml
version: 2.1
orbs:
  node: circleci/node@5.1.0

workflows:
  test-and-deploy:
    jobs:
      - node/test:
          version: '18.0'
```

## Pro Tips

 Use orbs to simplify config
 Enable parallelism for tests
 Cache dependencies aggressively
