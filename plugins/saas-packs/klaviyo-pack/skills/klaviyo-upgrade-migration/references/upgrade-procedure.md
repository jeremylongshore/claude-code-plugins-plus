# Klaviyo Upgrade & Rollback Procedure

The exact command sequence for a safe, reversible SDK upgrade. Pin the version with
`--save-exact` so a floating range can't drag in another breaking major during CI.

## Upgrade Procedure

```bash
# 1. Create upgrade branch
git checkout -b upgrade/klaviyo-api-v21

# 2. Install new version
npm install klaviyo-api@21.0.0 --save-exact

# 3. Run TypeScript compiler to find breaking changes
npx tsc --noEmit 2>&1 | grep -i "klaviyo\|error TS"

# 4. Fix all type errors, then run tests
npm test

# 5. Run integration tests against staging
KLAVIYO_TEST=1 npm run test:integration

# 6. Commit and deploy to staging first
git add package.json package-lock.json src/
git commit -m "upgrade: klaviyo-api to v21.0.0"
```

## Rollback Procedure

If error rates rise after the upgrade, reinstall the previous exact version and
revert the lockfile. Because the upgrade branch pinned versions, the rollback is a
clean reinstall — no dependency-resolution guesswork.

```bash
# If issues found after upgrade
npm install klaviyo-api@15.0.0 --save-exact
npm test
git add package.json package-lock.json
git commit -m "revert: rollback klaviyo-api to v15.0.0"
```

## Migration Checklist

- [ ] Backup current `package-lock.json`
- [ ] Read SDK changelog for target version
- [ ] Update `ApiKeySession` import (if changed)
- [ ] Fix property casing (camelCase in v21+)
- [ ] Update response access pattern (`response.body.data`)
- [ ] Verify all filter syntax still works
- [ ] Run full test suite
- [ ] Deploy to staging first
- [ ] Monitor error rates for 24 hours after production deploy
