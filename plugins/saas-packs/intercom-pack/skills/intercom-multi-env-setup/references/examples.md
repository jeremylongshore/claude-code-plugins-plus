# Intercom Multi-Environment Setup — Worked Examples

Concrete, end-to-end scenarios that combine the pieces from
[implementation.md](implementation.md). Each shows the situation, the commands or
code you run, and the observable result.

## Example 1: Bootstrap a new staging workspace

Situation: production is live; you need an isolated staging workspace so QA can
exercise webhooks without touching real contacts.

```bash
# 1. Create the staging secret set (git-ignored locally)
cat > .env.staging <<'EOF'
INTERCOM_ACCESS_TOKEN=dG9rOnN0YWdpbmdfdG9rZW4=
INTERCOM_WEBHOOK_SECRET=staging-webhook-secret
NODE_ENV=staging
EOF

# 2. Mirror the secret into CI
gh secret set INTERCOM_STAGING_TOKEN --body "staging-token"

# 3. Boot the app against staging and let startup validation confirm the workspace
NODE_ENV=staging node dist/server.js
```

Expected output:

```text
[Intercom] Validating staging setup...
[Intercom] Connected to workspace (admin: QA Bot)
```

If the token is wrong you instead see `Setup validation FAILED for staging` and
the process keeps running (non-production does not fail fast — see Step 6).

## Example 2: Guard a destructive cleanup job

Situation: a nightly job deletes test contacts. It must never run against
production.

```typescript
import { EnvironmentGuard } from "./guards";
import { intercomConfig } from "./config/intercom";

const guard = new EnvironmentGuard(intercomConfig.environment);

async function nightlyCleanup() {
  guard.preventProduction("nightlyCleanup"); // throws if NODE_ENV=production
  await deleteAllTestContacts();
}
```

Run it in the wrong environment and the guard stops it before any API call:

```text
Error: nightlyCleanup is blocked in production for safety
```

## Example 3: Route webhooks per environment in CI

Situation: each environment points Intercom at a different webhook URL, and CI
must set `NODE_ENV` so the correct URL and token are selected.

```yaml
jobs:
  deploy:
    strategy:
      matrix:
        environment: [staging, production]
    runs-on: ubuntu-latest
    env:
      NODE_ENV: ${{ matrix.environment }}
      INTERCOM_ACCESS_TOKEN: ${{ secrets[format('INTERCOM_{0}_TOKEN', matrix.environment)] }}
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run deploy   # reads webhookUrls[NODE_ENV] at runtime
```

The `webhookUrls` map in Step 5 resolves `NODE_ENV` to the matching public URL,
so staging traffic reaches `staging.example.com` and production reaches
`api.example.com` with no code change between deploys.
