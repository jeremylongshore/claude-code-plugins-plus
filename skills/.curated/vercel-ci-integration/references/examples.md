## Examples

### Release Workflow

```yaml
on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    env:
      VERCEL_API_KEY: ${{ secrets.VERCEL_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Verify Vercel production readiness
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

### Branch Protection

```yaml
required_status_checks:
  - "test"
  - "vercel-integration"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
