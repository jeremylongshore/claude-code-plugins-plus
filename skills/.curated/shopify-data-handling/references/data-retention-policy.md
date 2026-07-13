Automatic data retention policy enforcement via daily cron job.

```typescript
// Automatic cleanup — run daily via cron
async function enforceRetentionPolicy(): Promise<void> {
  const now = new Date();

  // Delete API request logs older than 30 days
  await db.apiLogs.deleteMany({
    where: { createdAt: { lt: new Date(now.getTime() - 30 * 86400000) } },
  });

  // Delete webhook event logs older than 90 days
  await db.webhookLogs.deleteMany({
    where: { createdAt: { lt: new Date(now.getTime() - 90 * 86400000) } },
  });

  // Keep audit logs for 7 years (regulatory requirement)
  // Never auto-delete audit records

  console.log("Retention policy enforced");
}
```
