# Juicebox Upgrade Migration - Implementation

## Version Check

```bash
npm list @juicebox/sdk | grep juicebox
npm view @juicebox/sdk version  # latest available
```

## Safe Migration Pattern

```typescript
async function runMigration(from: string, to: string): Promise<void> {
  const client = new JuiceboxClient({ apiKey: process.env.JUICEBOX_API_KEY! });

  // 1. Backup
  const snapshot = await client.createSnapshot({ label: `pre-migration-${to}` });
  console.log(`Snapshot: ${snapshot.id}`);

  // 2. Run
  try {
    const runner = new MigrationRunner(client);
    const results = await runner.migrate(from, to);
    if (results.errors.length > 0) throw new Error(`${results.errors.length} errors`);
    console.log(`Applied ${results.applied} migrations`);
  } catch (err) {
    // 3. Rollback on failure
    await client.restoreSnapshot(snapshot.id);
    throw err;
  }
}
```

## Breaking Changes Audit

```bash
# Find deprecated v1 API calls
grep -r "juicebox\.v1\." src/ --include="*.ts"
# Replace with v2 equivalents per migration guide
```

## Rollback via API

```bash
curl -X POST "https://api.juicebox.io/v1/snapshots/$SNAPSHOT_ID/restore" \
  -H "Authorization: Bearer $JUICEBOX_API_KEY"
# Returns: {"status":"restoring","eta_seconds":30}
```

## Version Compatibility Matrix

| SDK Version | API Version | Node.js | Notes |
|-------------|-------------|---------|-------|
| 1.x | v1 | 14+ | Legacy, EOL 2025 |
| 2.x | v2 | 16+ | Current stable |
| 3.x | v2 + v3 | 18+ | Latest, recommended |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
