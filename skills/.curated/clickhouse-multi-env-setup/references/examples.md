# ClickHouse Multi-Environment Setup — Examples

Worked, end-to-end examples that combine the building blocks from
`implementation.md` into runnable flows.

## Example 1: Environment strategy at a glance

The three-tier layout this skill provisions:

| Environment | Instance | Purpose | Data |
|-------------|----------|---------|------|
| Development | Docker local | Fast iteration | Synthetic seed data |
| Staging | ClickHouse Cloud (Dev tier) | Pre-prod validation | Sampled prod copy |
| Production | ClickHouse Cloud (Prod tier) | Live traffic | Real data |

## Example 2: Full CI/CD deploy pipeline (Step 7)

Staging deploys automatically; production is gated behind `needs: deploy-staging`
plus a GitHub `environment: production` that requires manual approval. Each job
injects only its own environment's secrets, and `schema:apply` runs before the
deploy so the database is migrated in lockstep with the code.

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    env:
      NODE_ENV: staging
      CLICKHOUSE_HOST: ${{ secrets.CLICKHOUSE_HOST_STAGING }}
      CLICKHOUSE_USER: ${{ secrets.CLICKHOUSE_USER_STAGING }}
      CLICKHOUSE_PASSWORD: ${{ secrets.CLICKHOUSE_PASSWORD_STAGING }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npm run schema:apply   # Apply schema changes
      - run: npm run test:integration  # Run against staging CH
      - run: npm run deploy:staging

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production   # Requires manual approval
    env:
      NODE_ENV: production
      CLICKHOUSE_HOST: ${{ secrets.CLICKHOUSE_HOST_PROD }}
      CLICKHOUSE_USER: ${{ secrets.CLICKHOUSE_USER_PROD }}
      CLICKHOUSE_PASSWORD: ${{ secrets.CLICKHOUSE_PASSWORD_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npm run schema:apply
      - run: npm run deploy:production
```

## Example 3: Querying from application code

Once the client factory is in place, application code never touches
environment logic — it just asks for the client and the config module resolves
the right instance from `NODE_ENV`.

```typescript
import { getClient } from './clickhouse/client';

// Resolves to app_dev / app_staging / app_prod automatically
const rows = await getClient().query({
  query: 'SELECT count() AS c FROM events WHERE date = today()',
  format: 'JSONEachRow',
});
console.log(await rows.json());
```
