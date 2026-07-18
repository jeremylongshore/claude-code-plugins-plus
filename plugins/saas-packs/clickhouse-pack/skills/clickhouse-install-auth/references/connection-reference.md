# ClickHouse Connection Reference

Full option table for `createClient()` and a Cloud-vs-self-hosted comparison.
`SKILL.md` links here so the workflow body stays lean.

## Connection Options Reference

| Option | Default | Description |
|--------|---------|-------------|
| `url` | `http://localhost:8123` | Full URL including protocol and port |
| `username` | `default` | ClickHouse user |
| `password` | `''` | User password |
| `database` | `default` | Default database for queries |
| `request_timeout` | `30000` | Query timeout in ms |
| `compression.request` | `false` | Compress request bodies (gzip) |
| `compression.response` | `true` | Decompress responses |
| `max_open_connections` | `10` | HTTP keep-alive pool size |
| `clickhouse_settings` | `{}` | Server-side settings per session |

## ClickHouse Cloud vs Self-Hosted

| Feature | Cloud | Self-Hosted |
|---------|-------|-------------|
| Port | 8443 (HTTPS) | 8123 (HTTP) / 8443 (HTTPS) |
| TLS | Required | Optional |
| Engine | SharedMergeTree | MergeTree family |
| Auth | User/password, Cloud API keys | User/password, LDAP, Kerberos |
