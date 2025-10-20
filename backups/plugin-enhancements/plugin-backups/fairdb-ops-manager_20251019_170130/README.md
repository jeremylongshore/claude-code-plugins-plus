# FairDB Operations Manager

**Comprehensive operations toolkit for managing FairDB managed PostgreSQL infrastructure**

A Claude Code plugin that provides guided SOPs, incident response procedures, monitoring tools, and automation scripts for running a production-grade managed PostgreSQL service.

---

## What is This?

FairDB Operations Manager is your complete operational toolkit for managing a fleet of PostgreSQL database servers. Whether you're setting up your first VPS or responding to a production incident, this plugin provides:

- **Step-by-step SOP guides** for setup and configuration
- **Autonomous agents** for incident response and auditing
- **Shell scripts** for health monitoring and backup management
- **Best practices** from production database operations

Perfect for solo operators, small teams, or anyone running managed PostgreSQL services.

---

## Features

### 📚 Standard Operating Procedures (SOPs)

Detailed, beginner-friendly guides for:

- **SOP-001:** VPS Initial Setup & Hardening (60 min)
  - System updates and user configuration
  - SSH hardening with key authentication
  - Firewall (UFW) and Fail2ban setup
  - Automatic security updates
  - Complete security verification

- **SOP-002:** PostgreSQL 16 Installation & Configuration (90 min)
  - PostgreSQL 16 installation
  - SSL/TLS encryption
  - Performance tuning for available RAM
  - pg_stat_statements monitoring
  - Health check automation

- **SOP-003:** Backup System Setup & Verification (120 min)
  - pgBackRest configuration with Wasabi S3
  - AES-256 encryption
  - Automated daily/weekly backups
  - **Backup restoration testing** (critical!)
  - Weekly verification automation

### 🤖 Autonomous Agents

Intelligent assistants that handle complex multi-step operations:

- **fairdb-setup-wizard:** Complete guided setup from bare VPS to production-ready
- **fairdb-incident-responder:** Autonomous incident response with diagnosis and recovery
- **fairdb-ops-auditor:** Compliance auditing with detailed remediation plans

### 🛠️ Operational Commands

Quick-access commands for daily operations:

- `/sop-001-vps-setup` - VPS hardening guide
- `/sop-002-postgres-install` - PostgreSQL setup guide
- `/sop-003-backup-setup` - Backup configuration guide
- `/daily-health-check` - Morning health check routine
- `/incident-p0-database-down` - Database down emergency response
- `/incident-p0-disk-full` - Disk space emergency procedures

### 📊 Shell Scripts (Deploy to VPS)

Production-ready scripts for server deployment:

- **pg-health-check.sh** - Automated PostgreSQL health monitoring
- **backup-status.sh** - Visual backup status dashboard
- **sop-checklist.sh** - Interactive SOP completion verification

---

## Installation

### From Your Private Repository

Since this is your personal plugin:

```bash
# Clone the repository locally if not already
git clone https://github.com/jeremylongshore/claude-code-plugins.git
cd claude-code-plugins

# Install the plugin directly from the local path
/plugin install ./plugins/community/fairdb-ops-manager
```

Or add as local marketplace:

```bash
# Create symbolic link to your plugin
/plugin marketplace add /path/to/claude-code-plugins

# Install the plugin
/plugin install fairdb-ops-manager@claude-code-plugins
```

---

## Quick Start

### 1. First Time Setup (New VPS)

Use the complete setup wizard for automated guidance:

```bash
# Launch the setup wizard agent
/agent fairdb-setup-wizard
```

The wizard will guide you through:
1. VPS hardening (SOP-001)
2. PostgreSQL installation (SOP-002)
3. Backup configuration (SOP-003)

**Total time:** 3-4 hours

### 2. Manual Step-by-Step Setup

If you prefer manual control:

```bash
# Step 1: Harden your VPS
/sop-001-vps-setup

# Step 2: Install PostgreSQL
/sop-002-postgres-install

# Step 3: Configure backups
/sop-003-backup-setup
```

### 3. Deploy Helper Scripts to VPS

Once your VPS is set up, deploy the monitoring scripts:

```bash
# SSH to your VPS
ssh admin@your-vps-ip -p 2222

# Create scripts directory (if not exists)
sudo mkdir -p /opt/fairdb/scripts

# Copy scripts from plugin directory
# (Transfer via scp, rsync, or copy-paste)

# Make scripts executable
sudo chmod +x /opt/fairdb/scripts/*.sh

# Schedule health checks
crontab -e
# Add: */5 * * * * /opt/fairdb/scripts/pg-health-check.sh
```

---

## Daily Operations

### Morning Health Check

```bash
# Run guided health check
/daily-health-check

# Or on VPS directly:
ssh your-vps
/opt/fairdb/scripts/pg-health-check.sh
```

### Check Backup Status

```bash
# On VPS:
/opt/fairdb/scripts/backup-status.sh

# Expected output:
# ✅ Backup repository accessible
# ✅ Last backup: 8 hours ago
# ✅ No recent errors
```

### Verify SOP Compliance

```bash
# Interactive checklist
ssh your-vps
/opt/fairdb/scripts/sop-checklist.sh

# Select:
# 4) ALL: Complete System Verification
```

---

## Incident Response

### P0: Database Down

```bash
# Launch incident responder
/incident-p0-database-down

# Or use autonomous agent
/agent fairdb-incident-responder
```

The responder will:
1. Classify severity
2. Run systematic diagnostics
3. Execute recovery procedures
4. Verify restoration
5. Generate incident report

### P0: Disk Space Emergency

```bash
/incident-p0-disk-full
```

Provides:
- Rapid space recovery procedures
- Safe cleanup strategies
- Long-term solutions

---

## Commands Reference

### Setup Commands

| Command | Description | Time |
|---------|-------------|------|
| `/sop-001-vps-setup` | VPS initial hardening | 60 min |
| `/sop-002-postgres-install` | PostgreSQL 16 setup | 90 min |
| `/sop-003-backup-setup` | Backup system configuration | 120 min |

### Operations Commands

| Command | Description | Time |
|---------|-------------|------|
| `/daily-health-check` | Morning health check routine | 10 min |
| `/incident-p0-database-down` | Database down emergency | Variable |
| `/incident-p0-disk-full` | Disk space emergency | Variable |

### Agents

| Agent | Description | Use Case |
|-------|-------------|----------|
| `/agent fairdb-setup-wizard` | Complete setup automation | New VPS setup |
| `/agent fairdb-incident-responder` | Autonomous incident response | Production emergencies |
| `/agent fairdb-ops-auditor` | Compliance auditing | Weekly/monthly audits |

---

## Shell Scripts

### pg-health-check.sh

**Purpose:** Automated PostgreSQL health monitoring

**Checks:**
- PostgreSQL service status
- Database connectivity
- Connection pool usage (warns at 90%)
- Disk space (warns at 80%)
- Long-running queries (>5 minutes)
- Recent backup errors

**Deployment:**
```bash
# Deploy to VPS
scp scripts/pg-health-check.sh admin@vps:/opt/fairdb/scripts/

# Make executable
ssh admin@vps "chmod +x /opt/fairdb/scripts/pg-health-check.sh"

# Schedule via cron
ssh admin@vps "crontab -e"
# Add: */5 * * * * /opt/fairdb/scripts/pg-health-check.sh
```

**Usage:**
```bash
/opt/fairdb/scripts/pg-health-check.sh
echo $?  # 0 = healthy, 1 = issues detected
```

### backup-status.sh

**Purpose:** Visual backup health dashboard

**Shows:**
- Repository status
- Recent backup activity
- Backup age analysis
- WAL archiving status
- Recent verification results
- Disk usage

**Usage:**
```bash
/opt/fairdb/scripts/backup-status.sh
```

### sop-checklist.sh

**Purpose:** Interactive SOP completion verification

**Features:**
- Menu-driven interface
- Automated verification checks
- Color-coded results
- Per-SOP or complete system checks

**Usage:**
```bash
/opt/fairdb/scripts/sop-checklist.sh

# Menu:
# 1) SOP-001: VPS Hardening
# 2) SOP-002: PostgreSQL
# 3) SOP-003: Backups
# 4) ALL: Complete verification
```

---

## Architecture & Design

### Plugin Structure

```
fairdb-ops-manager/
├── .claude-plugin/
│   └── plugin.json           # Plugin metadata
├── commands/                  # Slash commands
│   ├── sop-001-vps-setup.md
│   ├── sop-002-postgres-install.md
│   ├── sop-003-backup-setup.md
│   ├── daily-health-check.md
│   ├── incident-p0-database-down.md
│   └── incident-p0-disk-full.md
├── agents/                    # Autonomous agents
│   ├── fairdb-setup-wizard.md
│   ├── fairdb-incident-responder.md
│   └── fairdb-ops-auditor.md
├── scripts/                   # Shell scripts (deploy to VPS)
│   ├── pg-health-check.sh
│   ├── backup-status.sh
│   └── sop-checklist.sh
├── README.md                  # This file
└── LICENSE                    # MIT License
```

### Technology Stack

**VPS Environment:**
- Ubuntu 24.04 LTS
- PostgreSQL 16
- pgBackRest 2.x
- UFW firewall
- Fail2ban
- Wasabi S3 (backup storage)

**Plugin Components:**
- Claude Code commands (Markdown)
- Autonomous agents (Markdown)
- Bash scripts (Shell)

---

## Best Practices

### Security

✅ **DO:**
- Always use SSH key authentication
- Disable root login and password authentication
- Enable automatic security updates
- Use SSL/TLS for PostgreSQL connections
- Encrypt backups (AES-256)
- Run regular security audits

❌ **DON'T:**
- Skip backup restoration testing
- Run as root user
- Store passwords in plain text
- Allow remote root access
- Disable firewall or Fail2ban

### Backups

✅ **DO:**
- Test backup restoration regularly (weekly)
- Keep encryption passwords secure but accessible
- Monitor backup age (<48 hours)
- Verify automated backups are running
- Document backup procedures

❌ **DON'T:**
- Trust backups without testing restoration
- Delete only backup copies
- Skip weekly verification
- Ignore backup failure alerts

### Operations

✅ **DO:**
- Run daily health checks
- Document all changes
- Keep operations logs
- Update VPS inventory
- Review metrics regularly

❌ **DON'T:**
- Make undocumented changes
- Skip verification steps
- Ignore warning alerts
- Defer maintenance

---

## Troubleshooting

### Plugin Installation Issues

**Problem:** Plugin not found after installation

**Solution:**
```bash
# Verify installation
/plugin list | grep fairdb

# Reinstall if needed
/plugin uninstall fairdb-ops-manager
/plugin install ./plugins/community/fairdb-ops-manager
```

### SSH Connection Issues

**Problem:** Can't connect after hardening

**Solution:**
1. Use VNC console from provider (Contabo, etc.)
2. Revert SSH config: `sudo cp /etc/ssh/sshd_config.backup /etc/ssh/sshd_config`
3. Restart SSH: `sudo systemctl restart sshd`
4. Verify settings before trying again

### PostgreSQL Won't Start

**Problem:** Service fails after configuration changes

**Solution:**
```bash
# Check logs
sudo tail -100 /var/log/postgresql/postgresql-16-main.log

# Test config syntax
sudo -u postgres /usr/lib/postgresql/16/bin/postgres --check -D /var/lib/postgresql/16/main

# Restore backup config if needed
sudo cp /etc/postgresql/16/main/postgresql.conf.backup /etc/postgresql/16/main/postgresql.conf
sudo systemctl restart postgresql
```

### Backup Failures

**Problem:** pgBackRest cannot connect to Wasabi

**Solution:**
```bash
# Test internet connectivity
curl -I https://s3.wasabisys.com

# Verify credentials in /etc/pgbackrest.conf
sudo vim /etc/pgbackrest.conf

# Check pgBackRest logs
sudo tail -100 /var/log/pgbackrest/main-backup.log

# Test connection
sudo -u postgres pgbackrest --stanza=main check
```

---

## FAQ

### Q: Do I need to know PostgreSQL to use this?

**A:** No! The SOPs are designed for beginners. Each command is explained with WHY, not just HOW. The setup wizard provides hand-holding throughout the process.

### Q: How long does initial setup take?

**A:** 3-4 hours for complete setup (VPS hardening + PostgreSQL + Backups). You can take breaks between phases.

### Q: Can I use this for production?

**A:** Yes! This plugin is based on production best practices for managed PostgreSQL services. However, always test in a staging environment first.

### Q: What if something goes wrong during setup?

**A:** Each SOP has verification checkpoints. If something fails, restore from VPS snapshot and start fresh. The scripts include safety checks to prevent destructive actions.

### Q: Do I need Wasabi, or can I use AWS S3?

**A:** The SOPs use Wasabi (cheaper than AWS S3), but pgBackRest works with any S3-compatible storage. You can modify the configuration for AWS S3, Google Cloud Storage, Azure Blob, etc.

### Q: How much does this cost to run?

**A:** Example costs:
- Contabo VPS (8GB RAM, 200GB NVMe): ~$12/month
- Wasabi storage (first 1TB free, then $6.99/TB/month)
- **Total:** ~$12-20/month for single VPS

### Q: Can this manage multiple VPS instances?

**A:** Yes! Use the commands and agents for each VPS separately. The ops auditor can check compliance across your fleet.

### Q: Is this suitable for enterprise use?

**A:** This plugin is designed for small-to-medium operations (1-20 VPS instances). For enterprise scale, consider additional monitoring tools (Prometheus, Grafana) and orchestration (Ansible, Terraform).

---

## Roadmap

### Planned Features

- [ ] Additional incident response SOPs (SOP-201-206)
- [ ] Weekly maintenance procedures (SOP-301-304)
- [ ] Customer onboarding automation (SOP-102-103)
- [ ] Performance optimization guides
- [ ] Automated compliance reporting
- [ ] Integration with monitoring tools (Grafana, Datadog)

### Community Contributions

Since this is a personal plugin, contributions are managed directly. If you want similar functionality, feel free to fork and customize for your needs.

---

## Support & Contact

**Plugin Author:** Intent Solutions IO
**Email:** jeremy@intentsolutions.io
**Repository:** https://github.com/jeremylongshore/claude-code-plugins

**For issues or questions:**
1. Check the Troubleshooting section
2. Review the SOP documentation
3. Use the `/agent fairdb-ops-auditor` for compliance checks
4. Contact via email for complex issues

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Intent Solutions IO

---

## Acknowledgments

Built for **FairDB** - transparent, affordable, managed PostgreSQL as a service.

Based on production operational experience running managed database infrastructure.

Designed for Claude Code by Anthropic.

---

**Version:** 1.0.0
**Last Updated:** October 2025
**Status:** Production Ready (Personal Use)

---

## Quick Links

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands Reference](#commands-reference)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

**Ready to get started?**

```bash
# Install the plugin
/plugin install ./plugins/community/fairdb-ops-manager

# Launch the setup wizard
/agent fairdb-setup-wizard

# Or start with VPS hardening
/sop-001-vps-setup
```

**Happy database operations! 🚀**
