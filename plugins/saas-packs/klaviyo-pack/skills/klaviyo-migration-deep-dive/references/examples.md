# Klaviyo Migration — Worked Examples

Concrete end-to-end runs that stitch the building blocks in
[implementation.md](implementation.md) together. Each example is a scenario you
can adapt directly.

## Example 1: Mailchimp export → Klaviyo import

Take a Mailchimp CSV export, drop the suppressed contacts, and batch-import the
rest with progress tracking and rate limiting.

```typescript
import { ApiKeySession, ProfilesApi } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const profilesApi = new ProfilesApi(session);

// contacts loaded from the Mailchimp export and typed as CompetitorContact[]
// (see implementation.md Step 3 for the interface + transformToKlaviyo/migrateContacts)
const contacts: CompetitorContact[] = loadMailchimpExport('./mailchimp-export.csv');

const result = await migrateContacts(contacts);

console.log(`Imported: ${result.imported}`);
console.log(`Skipped (suppressed): ${result.skipped}`);
console.log(`Failed: ${result.failed.length}`);
if (result.failed.length) {
  console.log('Retry these emails:', result.failed);
}
```

Expected console output for a 10,000-contact list with 1,200 unsubscribed:

```text
Progress: 50/10000 (48 imported, 2 skipped)
Progress: 100/10000 (95 imported, 5 skipped)
...
Progress: 10000/10000 (8800 imported, 1200 skipped)
Imported: 8800
Skipped (suppressed): 1200
Failed: 0
```

## Example 2: Cut over v1 `identify` calls to `createOrUpdateProfile`

Before (deprecated v1 identify):

```typescript
// POST https://a.klaviyo.com/api/identify
// Body: { token: PUBLIC_KEY, properties: { $email, $first_name, plan } }
```

After (current REST API — note the field renames from the Step 2 mapping table):

```typescript
await profilesApi.createOrUpdateProfile({
  data: {
    type: 'profile',
    attributes: {
      email: 'user@example.com',   // was $email
      firstName: 'Jane',           // was $first_name
      properties: { plan: 'pro' }, // custom props unchanged
    },
  },
});
```

## Example 3: Gate the cutover behind a feature flag

Route 10% of event traffic to Klaviyo while keeping campaigns on the legacy
system until the flag reaches 100% (see the `MigrationRouter` in
implementation.md Step 4).

```typescript
const router = new MigrationRouter(
  legacyService,
  klaviyoService,
  () => Number(process.env.KLAVIYO_ROLLOUT_PCT ?? '0')  // start at 0, raise gradually
);

// KLAVIYO_ROLLOUT_PCT=10 → ~10% of events go to Klaviyo, campaigns stay legacy
await router.trackEvent({ metric: 'Placed Order', email: 'user@example.com' });
```

## Example 4: Gate deployment on a validation pass

Run `validateMigration` (implementation.md Step 5) and fail the deploy if any
check regresses:

```typescript
const report = await validateMigration(200);
for (const check of report.checks) {
  console.log(`${check.passed ? 'PASS' : 'FAIL'}  ${check.name}: ${check.details}`);
}
if (!report.passed) {
  throw new Error('Migration validation failed — do not decommission legacy system');
}
```
