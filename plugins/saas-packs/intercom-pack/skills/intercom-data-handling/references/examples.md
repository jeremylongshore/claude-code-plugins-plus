# Intercom Data Handling — Worked Examples

Concrete end-to-end usage of the functions defined in
[implementation.md](implementation.md).

## Example 1: Fulfil a DSAR (export everything for one user)

```typescript
// A user emails support asking for a copy of all their data.
const bundle = await exportContactData("5f3c9b2e8a1d4e0012ab34cd");

// Ship the bundle as JSON to the requester (or attach to a compliance ticket).
await fs.writeFile(
  `dsar/${bundle.contact.id}.json`,
  JSON.stringify(bundle, null, 2)
);

console.log(
  `Exported ${bundle.conversations.length} conversations, ` +
  `${bundle.tags.length} tags, ${bundle.events.length} events`
);
```

## Example 2: Honor a right-to-be-forgotten request

```typescript
// GDPR Article 17 — export for the audit trail, then purge everywhere.
const { deleted, auditRecord } = await deleteContactData(
  "5f3c9b2e8a1d4e0012ab34cd"
);

if (deleted) {
  // auditRecord proves the deletion happened without retaining PII.
  console.log("Purged:", auditRecord.data_sources_purged.join(", "));
  console.log("Conversations affected:", auditRecord.conversations_affected);
}
```

## Example 3: Bulk export a date range and wait for the CSV

```typescript
// Kick off a bulk message export and poll until the download URL is ready.
const jobId = await bulkExportMessages("2026-01-01", "2026-01-31");

let status = "pending";
let downloadUrl: string | undefined;
const deadline = Date.now() + 60 * 60 * 1000; // 1h timeout

while (status !== "complete") {
  if (Date.now() > deadline) throw new Error("Export timed out after 1h");
  await new Promise((r) => setTimeout(r, 30_000)); // poll every 30s
  ({ status, downloadUrl } = await checkExportStatus(jobId));
}

console.log("CSV ready at:", downloadUrl);
```

## Example 4: Redact PII before it reaches your logs

```typescript
const contact = await client.contacts.find({
  contactId: "5f3c9b2e8a1d4e0012ab34cd",
});

// Never log raw contact objects — always redact first.
console.log("Contact data:", redactIntercomData(contact));
// { id: "abc", email: "[REDACTED]", name: "[REDACTED]", role: "user" }
```

## Data Minimization

Only sync the fields you actually need. Storing less PII shrinks your DSAR /
deletion surface and your breach blast radius.

```typescript
// Only sync the fields you actually need from Intercom
async function syncContactMinimal(contactId: string) {
  const contact = await client.contacts.find({ contactId });

  // Store only necessary fields
  return {
    intercom_id: contact.id,
    external_id: contact.externalId,
    role: contact.role,
    plan: contact.customAttributes?.plan,
    last_seen_at: contact.lastSeenAt,
    // DO NOT store: email, name, phone, location
  };
}
```
