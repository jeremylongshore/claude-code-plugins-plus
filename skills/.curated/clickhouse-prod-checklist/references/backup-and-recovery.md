# Backup Configuration & Recovery

## Native BACKUP to S3

```sql
-- ClickHouse native BACKUP to S3
BACKUP TABLE analytics.events
    TO S3(
        'https://my-bucket.s3.us-east-1.amazonaws.com/backups/events',
        'ACCESS_KEY',
        'SECRET_KEY'
    )
    SETTINGS compression_method = 'zstd';

-- Incremental backup (base + delta)
BACKUP TABLE analytics.events
    TO S3('s3://my-bucket/backups/events-incremental')
    SETTINGS base_backup = S3('s3://my-bucket/backups/events-base');
```

**ClickHouse Cloud:** Backups are automatic. Configure retention and frequency
in the Cloud console under Service Settings.

## Backup readiness checklist

- [ ] Backup schedule configured (daily minimum)
- [ ] Backup restore tested and documented
- [ ] Point-in-time recovery possible (incremental backups)
- [ ] Backup stored in different region/account from primary

## Recovery notes

- A backup you have never restored is not a backup — schedule a periodic
  restore drill into a scratch database and time it.
- Incremental backups chain off a `base_backup`; keep the base reachable for the
  whole retention window or the deltas are unusable.
- Cross-region/cross-account storage protects against a single-account
  compromise or regional outage taking primary and backup down together.
