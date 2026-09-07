# Worked Examples

End-to-end walkthroughs composed from the operations documented in
`references/migration-guide.md`. Each shows the trigger, the commands run, and
the expected result.

## Example 1: Detect the current SDK and API version

```bash
$ npm list intercom-client
my-app@1.0.0
└── intercom-client@5.4.0

$ npm view intercom-client version
6.4.0

$ curl -s -D - -o /dev/null \
    -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
    https://api.intercom.io/me 2>/dev/null | grep -i intercom-version
intercom-version: 2.11
```

Result: the project is on v5.4.0 while v6.4.0 is available — a major upgrade
crossing the TypeScript rewrite boundary, so breaking changes are expected.

## Example 2: Migrate a user-creation call from v5 to v6

Starting code flagged by `npx tsc --noEmit`:

```typescript
// Before (v5) — TS error: Property 'users' does not exist
const Intercom = require("intercom-client");
const client = new Intercom.Client({ token: process.env.INTERCOM_ACCESS_TOKEN });
await client.users.create({ email: "test@example.com" });
```

Migrated code:

```typescript
// After (v6) — unified contacts API with explicit role
import { IntercomClient } from "intercom-client";
const client = new IntercomClient({ token: process.env.INTERCOM_ACCESS_TOKEN });
await client.contacts.create({ role: "user", email: "test@example.com" });
```

Result: `tsc --noEmit` passes for this call; the leftover `users`/`leads`
references are resolved the same way using the cheat sheet.

## Example 3: Full upgrade run on a branch

```bash
$ git checkout -b upgrade/intercom-client-v6
$ npm install intercom-client@latest
$ npx tsc --noEmit 2>&1 | grep "intercom"
src/inbox.ts(12,20): error TS2339: Property 'users' does not exist on type 'IntercomClient'.
src/inbox.ts(30,15): error TS2339: Property 'id' does not exist ...
# fix each per the cheat sheet, then re-run:
$ npx tsc --noEmit 2>&1 | grep "intercom"        # clean
$ npm test                                        # green
$ INTERCOM_ACCESS_TOKEN=$DEV_TOKEN npm run test:integration   # green against dev workspace
$ git add -A && git commit -m "chore: upgrade intercom-client to v6"
```

Result: a reviewable upgrade branch where TypeScript and the test suite both
confirm the migration is complete before the PR opens.
