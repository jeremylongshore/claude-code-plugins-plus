---
title: "Self-Hosting n8n on Contabo VPS: Enterprise Automation for $0/Month"
description: "Self-Hosting n8n on Contabo VPS: Enterprise Automation for $0/Month"
date: "2025-10-04"
tags: ["n8n", "self-hosting", "automation", "devops", "caddy", "ssl", "docker"]
featured: false
---
We just deployed a production-ready n8n instance at `n8n.intentsolutions.io` with zero monthly software costs. Here's the complete technical architecture and deployment process.

## The Business Case

**Before:** Paying $20+/month for n8n Cloud
**After:** $0/month on existing Contabo VPS
**Setup Time:** 2 hours
**ROI:** Infinite (one-time setup, zero recurring cost)

## Architecture Overview

```
┌─────────────────────────────────────┐
│   n8n.intentsolutions.io (DNS)      │
│   ↓                                  │
│   194.113.67.242:443 (HTTPS)        │
│   ↓                                  │
│   Caddy Reverse Proxy               │
│   - Auto SSL (Let's Encrypt)        │
│   - Port 443 (HTTPS)                │
│   ↓                                  │
│   Docker Container: n8n             │
│   - Port 5678 (internal)            │
│   - SQLite database                 │
│   - Persistent data: ./data         │
│   - Backups: ./backups              │
└─────────────────────────────────────┘
```

## Technical Challenge: Port Conflicts

The server was already running:

- **Port 80**: Apache2 (existing web server)
- **Port 443**: Needed for n8n HTTPS
- **Port 8080**: Caddy file browser

**Solution:** Configure Caddy with `auto_https disable_redirects` to handle HTTPS only without requiring port 80:

```caddyfile
{
    auto_https disable_redirects
}

n8n.intentsolutions.io:443 {
    reverse_proxy localhost:5678
}
```

## Docker Configuration

Key decisions for production stability:

**Network Mode:** `host` (avoids port mapping conflicts)

```yaml
services:
  n8n:
    image: n8nio/n8n:latest
    network_mode: "host"
    environment:
      - N8N_HOST=n8n.intentsolutions.io
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://n8n.intentsolutions.io/
```

**Database:** SQLite (perfect for single-user/small team)

```yaml
environment:
  - DB_TYPE=sqlite
  - DB_SQLITE_VACUUM_ON_STARTUP=true
```

## Workflow Import Process

Imported 15 workflows using n8n CLI:

```bash
# Prepare workflows (remove problematic fields)
jq 'del(.id, .versionId, .tags) | . + {active: false}' workflow.json > clean.json

# Copy to container
docker cp workflows/ n8n:/tmp/

# Import via CLI
docker exec -u node n8n n8n import:workflow --separate --input=/tmp/workflows/
```

**Result:** Successfully imported:

- Daily Energizer Article Generator V4
- Tech/AI News Pipeline
- Lead Follow-up System (with Bland.ai integration)
- AI Blog Journalist
- Upwork Proposal Generator
- Disposable Marketplace
- Gmail Drive Organizer

## SSL Certificate Automation

Caddy automatically obtains SSL certificates from Let's Encrypt on first HTTPS request. No manual certificate management required.

**Certificate Location:** `/var/lib/caddy/.local/share/caddy/certificates/`

## Security Hardening

1. **Basic Authentication:** Enabled with secure password
2. **HTTPS Enforced:** All traffic over SSL
3. **Firewall:** UFW configured for port 443
4. **Environment Variables:** Secrets stored in `.env` (not committed)
5. **API Token:** Generated for programmatic access

## Performance & Monitoring

**Resource Usage:**

- Memory: ~200MB (n8n container)
- CPU: Minimal (idle workflows)
- Storage: SSD on Contabo VPS

**Monitoring Commands:**

```bash
# Container health
docker ps | grep n8n

# Logs
docker logs -f n8n

# Disk usage
du -sh data/ backups/
```

## Cost Comparison

| Option | Monthly Cost | Setup Time | Maintenance |
|--------|--------------|------------|-------------|
| **n8n Cloud** | $20-50+ | 5 minutes | Zero |
| **Self-Hosted** | $0 | 2 hours | Minimal |
| **Annual Savings** | **$240-600** | One-time | Backups only |

## Backup Strategy

```bash
# Weekly backup script
tar -czf "n8n-backup-$(date +%Y%m%d).tar.gz" ./data
mv n8n-backup-*.tar.gz ./backups/

# Cleanup old backups (30 days)
find ./backups/ -name "n8n-backup-*.tar.gz" -mtime +30 -delete
```

## Lessons Learned

### 1. Use Existing Infrastructure

We had Caddy already running - adding n8n was just one more config block. Don't deploy redundant services.

### 2. Network Mode Matters

`host` networking avoided all port mapping complexity. Sometimes the simple solution is best.

### 3. SQLite is Underrated

For single-user or small team, SQLite is perfect. No PostgreSQL overhead needed.

### 4. CLI Import > API

The n8n CLI handled workflow imports reliably. The API had validation issues with exported JSON structure.

## Related Posts

- [Waygate MCP v2.1.0: Forensic Analysis to Production Enterprise Server](/posts/waygate-mcp-v2-1-0-forensic-analysis-to-production-enterprise-server/)
- [When Commands Don't Work: Debugging Journey Through Automated Content Systems](/posts/when-commands-dont-work-debugging-journey-through-automated-content-systems/)

## Next Steps

1. **Migrate to PostgreSQL** (if team grows beyond 5 users)
2. **Set up CI/CD** for workflow version control
3. **Configure monitoring/alerts** for workflow failures
4. **Implement automated backups** to cloud storage

## Conclusion

Self-hosting n8n on existing infrastructure eliminated $240-600/year in SaaS costs while maintaining full control over data and workflows. The 2-hour setup investment pays for itself in the first month.

**Business Impact:**

- ✅ Zero recurring automation costs
- ✅ Complete data ownership
- ✅ Custom domain with SSL
- ✅ 15 production workflows migrated
- ✅ Enterprise-grade infrastructure

**Repository:** n8n-workflows

*Want to eliminate your SaaS costs while maintaining enterprise capabilities? Let's talk about self-hosted automation architecture for your business.*
