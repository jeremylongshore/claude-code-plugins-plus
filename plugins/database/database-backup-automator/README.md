# Database Backup Automator Plugin

Automate database backups with scheduling, compression, encryption, and restore procedures.

## Installation

```bash
/plugin install database-backup-automator@claude-code-plugins-plus
```

## Usage

```bash
/backup
```

## Features

- **Multi-Database Support**: PostgreSQL, MySQL, MongoDB, SQLite
- **Automated Scheduling**: Cron-based backup automation
- **Compression & Encryption**: Secure backup storage
- **Retention Policies**: Automatic cleanup of old backups
- **Cloud Integration**: S3, GCS, Azure blob storage
- **Restore Procedures**: Complete recovery documentation

## Example

```bash
/backup
```

**Result:** Generates backup scripts, cron schedules, and restore procedures tailored to your database system.

## Requirements

- Database command-line tools (pg_dump, mysqldump, mongodump)
- Sufficient storage space
- Appropriate database permissions

## License

MIT
