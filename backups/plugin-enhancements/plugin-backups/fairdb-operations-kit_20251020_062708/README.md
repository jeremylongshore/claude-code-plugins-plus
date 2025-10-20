# FairDB Operations Kit

A comprehensive Claude Code plugin suite for managing FairDB PostgreSQL as a Service operations. This plugin automates VPS provisioning, PostgreSQL management, backup configuration, customer onboarding, and monitoring workflows.

## Overview

FairDB is a managed PostgreSQL-as-a-Service platform built on Contabo VPS infrastructure with pgBackRest backups to Wasabi S3 storage. This plugin kit provides Claude with the ability to execute complex operational tasks through natural language commands.

## Features

- **VPS Provisioning**: Automated Contabo VPS setup with security hardening
- **PostgreSQL Management**: Install, configure, and optimize PostgreSQL 16
- **Backup System**: pgBackRest configuration with Wasabi S3 integration
- **Customer Provisioning**: Automated database and user creation workflows
- **Monitoring**: Health checks, performance monitoring, and alerting
- **Incident Response**: Guided troubleshooting and recovery procedures
- **Intelligent Automation**: AI-powered agent for proactive management

## Installation

```bash
/plugin install fairdb-operations-kit@claude-code-plugins-plus
```

## Commands

### Infrastructure Setup

- `/fairdb-provision-vps` - Complete VPS setup with security hardening (implements SOP-001)
- `/fairdb-install-postgres` - Install and configure PostgreSQL 16 for production (implements SOP-002)
- `/fairdb-setup-backup` - Configure pgBackRest with Wasabi S3 storage (implements SOP-003)

### Customer Management

- `/fairdb-onboard-customer` - Complete customer provisioning workflow
  - Creates database and users
  - Configures network access
  - Sets up backups
  - Generates SSL certificates
  - Provides connection documentation

### Operations & Monitoring

- `/fairdb-health-check` - Comprehensive system health verification
  - Server resources check
  - Database performance metrics
  - Backup status verification
  - Security audit

- `/fairdb-emergency-response` - Critical incident response procedures
  - Service recovery
  - Data integrity checks
  - Performance triage
  - Root cause analysis

## Agent Capabilities

The `fairdb-automation-agent` provides intelligent automation for:

- **Proactive Monitoring**: Continuous analysis and prediction of issues
- **Automated Problem Resolution**: Pattern-based diagnosis and fixes
- **Resource Optimization**: Dynamic parameter tuning and workload balancing
- **Automated Operations**: Routine maintenance and backup management

## Skills

### FairDB Backup Manager

An Agent Skill that automatically activates when working with backups:
- Manages pgBackRest configurations
- Executes scheduled backups
- Performs test restores
- Monitors backup health
- Optimizes storage costs

## Architecture

```
FairDB Infrastructure Stack
├── Contabo VPS
│   ├── Ubuntu 24.04 LTS
│   ├── PostgreSQL 16
│   ├── pgBackRest
│   └── Monitoring (Prometheus/Grafana)
├── Wasabi S3 Storage
│   ├── Full backups (weekly)
│   ├── Differential backups (daily)
│   └── WAL archives (continuous)
└── Security Layer
    ├── UFW Firewall
    ├── Fail2ban IPS
    ├── SSL/TLS encryption
    └── Key-based SSH
```

## Standard Operating Procedures

This plugin implements three core SOPs:

### SOP-001: VPS Hardening
- OS security updates
- Firewall configuration (UFW)
- Intrusion prevention (Fail2ban)
- SSH hardening
- Monitoring setup

### SOP-002: PostgreSQL Installation
- PostgreSQL 16 from official repos
- Production configuration tuning
- SSL certificate generation
- User and permission management
- Performance optimization

### SOP-003: Backup Configuration
- pgBackRest installation
- Wasabi S3 integration
- Retention policy setup
- Automated scheduling
- Recovery testing

## Configuration

Required environment variables:

```bash
# Contabo API
CONTABO_API_KEY=<your-api-key>

# Wasabi S3
WASABI_ACCESS_KEY=<access-key>
WASABI_SECRET_KEY=<secret-key>
WASABI_BUCKET=<bucket-name>
WASABI_ENDPOINT=<region-endpoint>

# PostgreSQL
FAIRDB_ADMIN_USER=<admin-username>
FAIRDB_ADMIN_PASS=<admin-password>

# Monitoring
FAIRDB_MONITORING_WEBHOOK=<webhook-url>
```

## Usage Examples

### Complete New Customer Setup

```
User: "I need to onboard Acme Corp as a new FairDB customer"

Claude: I'll help you onboard Acme Corp. Let me use the fairdb-onboard-customer command...

[Executes complete workflow]:
✅ Database created: acme_corp_db
✅ Users created with secure passwords
✅ Network access configured for customer IPs
✅ Backups scheduled (daily at 3 AM)
✅ SSL certificates generated
✅ Monitoring enabled
✅ Connection documentation generated

Customer can now connect using:
postgresql://acme_corp_user:<password>@fairdb.example.com:5432/acme_corp_db?sslmode=require
```

### Emergency Response

```
User: "Critical: customers reporting connection failures!"

Claude: Initiating emergency response with fairdb-emergency-response...

[STEP 1] SERVICE STATUS CHECK
❌ CRITICAL: PostgreSQL is DOWN
Attempting emergency restart...
✅ PostgreSQL restarted successfully

[STEP 2] CONNECTION DIAGNOSTICS
Connections: 198/200 (99% utilized)
Terminating idle connections...
✅ Freed 47 connections

[STEP 3] PERFORMANCE TRIAGE
Found 3 long-running queries (>30 minutes)
Cancelling problematic queries...
✅ Performance restored

Root Cause: Connection pool exhaustion due to application bug
Resolution: Service restored, customer notified, RCA documented
```

### Health Monitoring

```
User: "Run a health check on FairDB infrastructure"

Claude: Running comprehensive health check with fairdb-health-check...

[1/10] SERVER RESOURCES
✅ CPU: 42% | Memory: 68% | Disk: 71%

[2/10] POSTGRESQL SERVICE
✅ Running | Version: 16.1 | Uptime: 47 days

[3/10] DATABASE CONNECTIONS
Active: 87/200 (43.5%)

[4/10] BACKUP STATUS
✅ Last backup: 2 hours ago
✅ All customer stanzas current

[10/10] OVERALL HEALTH: GOOD
```

## Best Practices

### Security
- Always use SSL/TLS connections
- Rotate passwords quarterly
- Keep IP allowlists updated
- Regular security audits
- Encrypted backups only

### Performance
- Monitor connection pools
- Regular VACUUM ANALYZE
- Index optimization
- Query performance reviews
- Resource usage tracking

### Reliability
- Test restores monthly
- Document all procedures
- Maintain runbooks
- Practice incident response
- Keep backups current

## Troubleshooting

### Common Issues

**PostgreSQL Won't Start**
```bash
# Check logs
sudo journalctl -u postgresql -n 50

# Verify data directory
sudo -u postgres pg_ctl -D /var/lib/postgresql/16/main status

# Check port conflicts
sudo netstat -tulpn | grep 5432
```

**Backup Failures**
```bash
# Check pgBackRest status
sudo -u postgres pgbackrest --stanza=fairdb check

# Verify S3 connectivity
aws s3 ls s3://bucket --endpoint-url=https://s3.wasabisys.com

# Review backup logs
tail -f /var/log/pgbackrest/fairdb-backup.log
```

**High Connection Usage**
```bash
# View active connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Kill idle connections
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < NOW() - INTERVAL '10 minutes';"
```

## Support & Contributions

- **Issues**: Report via GitHub Issues
- **Documentation**: See command help for details
- **Updates**: Check for plugin updates regularly
- **Contributing**: PRs welcome for improvements

## License

MIT License - See LICENSE file for details

## Author

Jeremy Longshore (jeremy@intentsolutions.io)

## Acknowledgments

- PostgreSQL community for excellent documentation
- pgBackRest team for reliable backup solution
- Wasabi for cost-effective S3 storage
- Contabo for reliable VPS infrastructure

---

*Part of the Claude Code Plugins ecosystem - https://claudecodeplugins.io*