#!/usr/bin/env python3
"""
Backup Script Generator

Generates production-ready backup scripts for PostgreSQL, MySQL, MongoDB, and SQLite.
Includes compression, encryption, and retention policy support.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class BackupConfig:
    """Backup script configuration."""

    db_type: str
    database: str
    host: str
    port: int
    user: str
    backup_dir: str
    compression: str
    encryption: Optional[str]
    retention_days: int


POSTGRESQL_TEMPLATE = """#!/bin/bash
# PostgreSQL Backup Script
# Generated: {timestamp}
# Database: {database}

set -euo pipefail

# Configuration
BACKUP_DIR="{backup_dir}"
DB_HOST="{host}"
DB_PORT="{port}"
DB_USER="{user}"
DB_NAME="{database}"
RETENTION_DAYS={retention_days}

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${{BACKUP_DIR}}/${{DB_NAME}}_${{DATE}}.dump"
LOG_FILE="${{BACKUP_DIR}}/backup.log"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

log() {{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}}

log "Starting PostgreSQL backup of $DB_NAME"

# Perform backup
if PGPASSWORD="${{PGPASSWORD:-}}" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \\
    --format=custom \\
    --compress=9 \\
    --verbose \\
    --file="$BACKUP_FILE" 2>> "$LOG_FILE"; then

    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup completed: $BACKUP_FILE ($SIZE)"

    # Verify backup
    if pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1; then
        log "Backup verification passed"
    else
        log "ERROR: Backup verification failed"
        exit 1
    fi
{encryption_block}
else
    log "ERROR: Backup failed"
    exit 1
fi

# Cleanup old backups
log "Cleaning backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name "*.dump*" -mtime "+$RETENTION_DAYS" -delete

log "Backup process completed"
"""

MYSQL_TEMPLATE = """#!/bin/bash
# MySQL Backup Script
# Generated: {timestamp}
# Database: {database}

set -euo pipefail

# Configuration
BACKUP_DIR="{backup_dir}"
DB_HOST="{host}"
DB_PORT="{port}"
DB_USER="{user}"
DB_NAME="{database}"
RETENTION_DAYS={retention_days}

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${{BACKUP_DIR}}/${{DB_NAME}}_${{DATE}}.sql{compression_ext}"
LOG_FILE="${{BACKUP_DIR}}/backup.log"

mkdir -p "$BACKUP_DIR"

log() {{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}}

log "Starting MySQL backup of $DB_NAME"

# Perform backup
if mysqldump -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"${{MYSQL_PWD:-}}" \\
    --single-transaction \\
    --routines \\
    --triggers \\
    --events \\
    --quick \\
    "$DB_NAME" 2>> "$LOG_FILE" {compression_pipe} > "$BACKUP_FILE"; then

    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup completed: $BACKUP_FILE ($SIZE)"

    # Verify backup
    if {verify_command}; then
        log "Backup verification passed"
    else
        log "ERROR: Backup verification failed"
        exit 1
    fi
{encryption_block}
else
    log "ERROR: Backup failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Cleanup old backups
log "Cleaning backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name "*.sql*" -mtime "+$RETENTION_DAYS" -delete

log "Backup process completed"
"""

MONGODB_TEMPLATE = """#!/bin/bash
# MongoDB Backup Script
# Generated: {timestamp}
# Database: {database}

set -euo pipefail

# Configuration
BACKUP_DIR="{backup_dir}"
MONGO_URI="${{MONGO_URI:-mongodb://{host}:{port}}}"
DB_NAME="{database}"
RETENTION_DAYS={retention_days}

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${{BACKUP_DIR}}/${{DB_NAME}}_${{DATE}}"
LOG_FILE="${{BACKUP_DIR}}/backup.log"

mkdir -p "$BACKUP_DIR"

log() {{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}}

log "Starting MongoDB backup of $DB_NAME"

# Perform backup
if mongodump --uri="$MONGO_URI" \\
    --db="$DB_NAME" \\
    {compression_flag} \\
    --out="$BACKUP_PATH" 2>> "$LOG_FILE"; then

    SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
    log "Backup completed: $BACKUP_PATH ($SIZE)"

    # Verify backup
    BSON_COUNT=$(find "$BACKUP_PATH" -name "*.bson*" | wc -l)
    if [ "$BSON_COUNT" -gt 0 ]; then
        log "Backup verification passed ($BSON_COUNT collections)"
    else
        log "WARNING: No BSON files found"
    fi

    # Create tar archive
    log "Creating archive..."
    tar -cf "${{BACKUP_PATH}}.tar" -C "$BACKUP_DIR" "${{DB_NAME}}_${{DATE}}"
    rm -rf "$BACKUP_PATH"
    log "Archive created: ${{BACKUP_PATH}}.tar"
{encryption_block}
else
    log "ERROR: Backup failed"
    rm -rf "$BACKUP_PATH"
    exit 1
fi

# Cleanup old backups
log "Cleaning backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name "*.tar*" -mtime "+$RETENTION_DAYS" -delete

log "Backup process completed"
"""

SQLITE_TEMPLATE = """#!/bin/bash
# SQLite Backup Script
# Generated: {timestamp}
# Database: {database}

set -euo pipefail

# Configuration
DB_PATH="{database}"
BACKUP_DIR="{backup_dir}"
RETENTION_DAYS={retention_days}

DB_NAME=$(basename "$DB_PATH" .db)
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${{BACKUP_DIR}}/${{DB_NAME}}_${{DATE}}.db"
LOG_FILE="${{BACKUP_DIR}}/backup.log"

mkdir -p "$BACKUP_DIR"

log() {{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}}

log "Starting SQLite backup of $DB_PATH"

# Check database exists
if [ ! -f "$DB_PATH" ]; then
    log "ERROR: Database not found: $DB_PATH"
    exit 1
fi

# Check integrity before backup
if ! sqlite3 "$DB_PATH" "PRAGMA integrity_check;" | grep -q "^ok$"; then
    log "WARNING: Database integrity check failed"
fi

# Perform backup using online backup API
if sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'" 2>> "$LOG_FILE"; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup completed: $BACKUP_FILE ($SIZE)"

    # Verify backup
    if sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" | grep -q "^ok$"; then
        log "Backup verification passed"
    else
        log "ERROR: Backup verification failed"
        exit 1
    fi

    # Compress backup
    {compression_command}
{encryption_block}
else
    log "ERROR: Backup failed"
    exit 1
fi

# Cleanup old backups
log "Cleaning backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name "*.db*" -mtime "+$RETENTION_DAYS" -delete

log "Backup process completed"
"""


def get_encryption_block(encryption: Optional[str], backup_var: str = "BACKUP_FILE") -> str:
    """Generate encryption block for backup script."""
    if not encryption:
        return ""

    if encryption == "gpg":
        return f"""
    # Encrypt backup with GPG
    log "Encrypting backup..."
    if gpg --symmetric --cipher-algo AES256 --batch --passphrase-file /etc/backup.key "${{{backup_var}}}"; then
        rm "${{{backup_var}}}"
        log "Encryption completed: ${{{backup_var}}}.gpg"
    else
        log "ERROR: Encryption failed"
        exit 1
    fi"""
    elif encryption == "openssl":
        return f"""
    # Encrypt backup with OpenSSL
    log "Encrypting backup..."
    if openssl enc -aes-256-cbc -salt -pbkdf2 -in "${{{backup_var}}}" -out "${{{backup_var}}}.enc" -pass file:/etc/backup.key; then
        rm "${{{backup_var}}}"
        log "Encryption completed: ${{{backup_var}}}.enc"
    else
        log "ERROR: Encryption failed"
        exit 1
    fi"""
    return ""


def generate_postgresql_script(config: BackupConfig) -> str:
    """Generate PostgreSQL backup script."""
    return POSTGRESQL_TEMPLATE.format(
        timestamp=datetime.now().isoformat(),
        database=config.database,
        host=config.host,
        port=config.port,
        user=config.user,
        backup_dir=config.backup_dir,
        retention_days=config.retention_days,
        encryption_block=get_encryption_block(config.encryption),
    )


def generate_mysql_script(config: BackupConfig) -> str:
    """Generate MySQL backup script."""
    compression_pipe = "| gzip" if config.compression == "gzip" else ""
    compression_ext = ".gz" if config.compression == "gzip" else ""
    verify_command = (
        'gunzip -t "$BACKUP_FILE"' if config.compression == "gzip" else 'head -1 "$BACKUP_FILE" | grep -q "MySQL dump"'
    )

    return MYSQL_TEMPLATE.format(
        timestamp=datetime.now().isoformat(),
        database=config.database,
        host=config.host,
        port=config.port,
        user=config.user,
        backup_dir=config.backup_dir,
        retention_days=config.retention_days,
        compression_pipe=compression_pipe,
        compression_ext=compression_ext,
        verify_command=verify_command,
        encryption_block=get_encryption_block(config.encryption),
    )


def generate_mongodb_script(config: BackupConfig) -> str:
    """Generate MongoDB backup script."""
    compression_flag = "--gzip" if config.compression == "gzip" else ""

    return MONGODB_TEMPLATE.format(
        timestamp=datetime.now().isoformat(),
        database=config.database,
        host=config.host,
        port=config.port,
        backup_dir=config.backup_dir,
        retention_days=config.retention_days,
        compression_flag=compression_flag,
        encryption_block=get_encryption_block(config.encryption, "BACKUP_PATH.tar"),
    )


def generate_sqlite_script(config: BackupConfig) -> str:
    """Generate SQLite backup script."""
    if config.compression == "gzip":
        compression_command = '''gzip "$BACKUP_FILE"
    log "Compressed to: ${BACKUP_FILE}.gz"'''
    else:
        compression_command = "# No compression"

    return SQLITE_TEMPLATE.format(
        timestamp=datetime.now().isoformat(),
        database=config.database,
        backup_dir=config.backup_dir,
        retention_days=config.retention_days,
        compression_command=compression_command,
        encryption_block=get_encryption_block(config.encryption),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate database backup scripts for PostgreSQL, MySQL, MongoDB, or SQLite"
    )
    parser.add_argument(
        "--db-type", "-t", required=True, choices=["postgresql", "mysql", "mongodb", "sqlite"], help="Database type"
    )
    parser.add_argument("--database", "-d", required=True, help="Database name (or path for SQLite)")
    parser.add_argument("--host", "-H", default="localhost", help="Database host (default: localhost)")
    parser.add_argument("--port", "-P", type=int, help="Database port (default: depends on db type)")
    parser.add_argument("--user", "-u", default="root", help="Database user (default: root)")
    parser.add_argument("--backup-dir", "-b", default="/var/backups", help="Backup directory (default: /var/backups)")
    parser.add_argument(
        "--compression", "-c", choices=["none", "gzip"], default="gzip", help="Compression type (default: gzip)"
    )
    parser.add_argument(
        "--encryption", "-e", choices=["none", "gpg", "openssl"], default="none", help="Encryption type (default: none)"
    )
    parser.add_argument("--retention", "-r", type=int, default=7, help="Retention days (default: 7)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    args = parser.parse_args()

    # Default ports
    default_ports = {
        "postgresql": 5432,
        "mysql": 3306,
        "mongodb": 27017,
        "sqlite": 0,
    }
    port = args.port or default_ports[args.db_type]

    config = BackupConfig(
        db_type=args.db_type,
        database=args.database,
        host=args.host,
        port=port,
        user=args.user,
        backup_dir=args.backup_dir,
        compression=args.compression,
        encryption=None if args.encryption == "none" else args.encryption,
        retention_days=args.retention,
    )

    generators = {
        "postgresql": generate_postgresql_script,
        "mysql": generate_mysql_script,
        "mongodb": generate_mongodb_script,
        "sqlite": generate_sqlite_script,
    }

    script = generators[args.db_type](config)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(script)
        output_path.chmod(0o755)
        print(f"Generated backup script: {output_path}")
    else:
        print(script)

    return 0


if __name__ == "__main__":
    sys.exit(main())
