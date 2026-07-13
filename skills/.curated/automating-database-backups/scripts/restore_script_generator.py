#!/usr/bin/env python3
"""
Restore Script Generator

Generates database restore scripts for PostgreSQL, MySQL, MongoDB, and SQLite.
Includes safety checks, verification, and rollback options.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass


@dataclass
class RestoreConfig:
    """Restore script configuration."""

    db_type: str
    database: str
    host: str
    port: int
    user: str
    backup_pattern: str
    backup_dir: str


POSTGRESQL_RESTORE_TEMPLATE = """#!/bin/bash
# PostgreSQL Restore Script
# Generated: {timestamp}
# Database: {database}

set -euo pipefail

# Configuration
BACKUP_DIR="{backup_dir}"
DB_HOST="{host}"
DB_PORT="{port}"
DB_USER="{user}"
DB_NAME="{database}"
BACKUP_PATTERN="{backup_pattern}"

# Find backup file
if [ -n "${{1:-}}" ]; then
    BACKUP_FILE="$1"
else
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/$BACKUP_PATTERN 2>/dev/null | head -1)
fi

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found"
    echo "Usage: $0 [backup_file]"
    echo "Or place backups matching '$BACKUP_PATTERN' in $BACKUP_DIR"
    exit 1
fi

echo "=================================================="
echo "PostgreSQL Restore"
echo "=================================================="
echo "Backup: $BACKUP_FILE"
echo "Target: $DB_HOST:$DB_PORT/$DB_NAME"
echo "User: $DB_USER"
echo ""

# Verify backup file
echo "Verifying backup..."
if ! pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1; then
    echo "ERROR: Invalid backup file format"
    exit 1
fi
echo "Backup verification: OK"

# Check if database exists
DB_EXISTS=$(PGPASSWORD="${{PGPASSWORD:-}}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" postgres 2>/dev/null || echo "0")

if [ "$DB_EXISTS" = "1" ]; then
    echo ""
    echo "WARNING: Database '$DB_NAME' already exists!"
    echo "Options:"
    echo "  1. Drop and recreate (DESTRUCTIVE)"
    echo "  2. Restore to new database '${DB_NAME}_restored'"
    echo "  3. Cancel"
    read -p "Choose [1/2/3]: " CHOICE

    case $CHOICE in
        1)
            echo "Dropping database $DB_NAME..."
            PGPASSWORD="${{PGPASSWORD:-}}" dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
            PGPASSWORD="${{PGPASSWORD:-}}" createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
            TARGET_DB="$DB_NAME"
            ;;
        2)
            TARGET_DB="${{DB_NAME}}_restored"
            echo "Creating database $TARGET_DB..."
            PGPASSWORD="${{PGPASSWORD:-}}" createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$TARGET_DB" || true
            ;;
        *)
            echo "Cancelled"
            exit 0
            ;;
    esac
else
    echo "Creating database $DB_NAME..."
    PGPASSWORD="${{PGPASSWORD:-}}" createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
    TARGET_DB="$DB_NAME"
fi

# Perform restore
echo ""
echo "Restoring to $TARGET_DB..."
START_TIME=$(date +%s)

if PGPASSWORD="${{PGPASSWORD:-}}" pg_restore \\
    -h "$DB_HOST" \\
    -p "$DB_PORT" \\
    -U "$DB_USER" \\
    -d "$TARGET_DB" \\
    --verbose \\
    --no-owner \\
    --no-privileges \\
    "$BACKUP_FILE"; then

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    echo "=================================================="
    echo "Restore completed successfully!"
    echo "Duration: $DURATION seconds"
    echo "Database: $TARGET_DB"
    echo "=================================================="

    # Verify restore
    echo ""
    echo "Verification:"
    PGPASSWORD="${{PGPASSWORD:-}}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$TARGET_DB" -c "\\dt" | head -20
else
    echo "ERROR: Restore failed"
    exit 1
fi
"""

MYSQL_RESTORE_TEMPLATE = """#!/bin/bash
# MySQL Restore Script
# Generated: {timestamp}
# Database: {database}

set -euo pipefail

# Configuration
BACKUP_DIR="{backup_dir}"
DB_HOST="{host}"
DB_PORT="{port}"
DB_USER="{user}"
DB_NAME="{database}"
BACKUP_PATTERN="{backup_pattern}"

# Find backup file
if [ -n "${{1:-}}" ]; then
    BACKUP_FILE="$1"
else
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/$BACKUP_PATTERN 2>/dev/null | head -1)
fi

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found"
    echo "Usage: $0 [backup_file]"
    exit 1
fi

echo "=================================================="
echo "MySQL Restore"
echo "=================================================="
echo "Backup: $BACKUP_FILE"
echo "Target: $DB_HOST:$DB_PORT/$DB_NAME"
echo "User: $DB_USER"
echo ""

# Detect compression
if [[ "$BACKUP_FILE" == *.gz ]]; then
    CAT_CMD="gunzip -c"
    echo "Compression: gzip"
else
    CAT_CMD="cat"
fi

# Check if database exists
DB_EXISTS=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"${{MYSQL_PWD:-}}" -e "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME='$DB_NAME'" 2>/dev/null | grep -c "$DB_NAME" || echo "0")

if [ "$DB_EXISTS" -gt 0 ]; then
    echo ""
    echo "WARNING: Database '$DB_NAME' already exists!"
    echo "Options:"
    echo "  1. Drop and recreate (DESTRUCTIVE)"
    echo "  2. Restore to new database '${DB_NAME}_restored'"
    echo "  3. Cancel"
    read -p "Choose [1/2/3]: " CHOICE

    case $CHOICE in
        1)
            echo "Dropping database $DB_NAME..."
            mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"${{MYSQL_PWD:-}}" -e "DROP DATABASE $DB_NAME"
            mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"${{MYSQL_PWD:-}}" -e "CREATE DATABASE $DB_NAME"
            TARGET_DB="$DB_NAME"
            ;;
        2)
            TARGET_DB="${{DB_NAME}}_restored"
            echo "Creating database $TARGET_DB..."
            mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"${{MYSQL_PWD:-}}" -e "CREATE DATABASE IF NOT EXISTS $TARGET_DB"
            ;;
        *)
            echo "Cancelled"
            exit 0
            ;;
    esac
else
    echo "Creating database $DB_NAME..."
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"${{MYSQL_PWD:-}}" -e "CREATE DATABASE $DB_NAME"
    TARGET_DB="$DB_NAME"
fi

# Perform restore
echo ""
echo "Restoring to $TARGET_DB..."
START_TIME=$(date +%s)

if $CAT_CMD "$BACKUP_FILE" | mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"${{MYSQL_PWD:-}}" "$TARGET_DB"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    echo "=================================================="
    echo "Restore completed successfully!"
    echo "Duration: $DURATION seconds"
    echo "Database: $TARGET_DB"
    echo "=================================================="

    # Verify restore
    echo ""
    echo "Verification:"
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"${{MYSQL_PWD:-}}" -e "SHOW TABLES" "$TARGET_DB" | head -20
else
    echo "ERROR: Restore failed"
    exit 1
fi
"""

MONGODB_RESTORE_TEMPLATE = """#!/bin/bash
# MongoDB Restore Script
# Generated: {timestamp}
# Database: {database}

set -euo pipefail

# Configuration
BACKUP_DIR="{backup_dir}"
MONGO_URI="${{MONGO_URI:-mongodb://{host}:{port}}}"
DB_NAME="{database}"
BACKUP_PATTERN="{backup_pattern}"

# Find backup
if [ -n "${{1:-}}" ]; then
    BACKUP_PATH="$1"
else
    BACKUP_PATH=$(ls -td "$BACKUP_DIR"/$BACKUP_PATTERN 2>/dev/null | head -1)
fi

if [ -z "$BACKUP_PATH" ]; then
    echo "ERROR: Backup not found"
    echo "Usage: $0 [backup_path]"
    exit 1
fi

echo "=================================================="
echo "MongoDB Restore"
echo "=================================================="
echo "Backup: $BACKUP_PATH"
echo "Target: $MONGO_URI/$DB_NAME"
echo ""

# Detect backup format
RESTORE_ARGS=""
if [ -f "$BACKUP_PATH" ]; then
    if [[ "$BACKUP_PATH" == *.tar ]]; then
        echo "Extracting archive..."
        EXTRACT_DIR=$(mktemp -d)
        tar -xf "$BACKUP_PATH" -C "$EXTRACT_DIR"
        BACKUP_PATH="$EXTRACT_DIR"
        RESTORE_ARGS="--gzip"
    elif [[ "$BACKUP_PATH" == *.gz ]]; then
        RESTORE_ARGS="--gzip --archive=$BACKUP_PATH"
    fi
elif [ -d "$BACKUP_PATH" ]; then
    # Check if it contains gzipped bson
    if ls "$BACKUP_PATH"/*/*.bson.gz > /dev/null 2>&1; then
        RESTORE_ARGS="--gzip"
    fi
fi

# Check if database exists
DB_EXISTS=$(mongosh "$MONGO_URI" --quiet --eval "db.getMongo().getDBNames().includes('$DB_NAME')" 2>/dev/null || echo "false")

if [ "$DB_EXISTS" = "true" ]; then
    echo ""
    echo "WARNING: Database '$DB_NAME' already exists!"
    echo "Options:"
    echo "  1. Drop and restore (DESTRUCTIVE)"
    echo "  2. Restore to new database '${DB_NAME}_restored'"
    echo "  3. Cancel"
    read -p "Choose [1/2/3]: " CHOICE

    case $CHOICE in
        1)
            TARGET_DB="$DB_NAME"
            RESTORE_ARGS="$RESTORE_ARGS --drop"
            ;;
        2)
            TARGET_DB="${{DB_NAME}}_restored"
            ;;
        *)
            echo "Cancelled"
            exit 0
            ;;
    esac
else
    TARGET_DB="$DB_NAME"
fi

# Perform restore
echo ""
echo "Restoring to $TARGET_DB..."
START_TIME=$(date +%s)

if mongorestore --uri="$MONGO_URI" \\
    --db="$TARGET_DB" \\
    --nsFrom="$DB_NAME.*" \\
    --nsTo="$TARGET_DB.*" \\
    $RESTORE_ARGS \\
    "$BACKUP_PATH/$DB_NAME" 2>&1; then

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    echo "=================================================="
    echo "Restore completed successfully!"
    echo "Duration: $DURATION seconds"
    echo "Database: $TARGET_DB"
    echo "=================================================="

    # Verify restore
    echo ""
    echo "Verification:"
    mongosh "$MONGO_URI/$TARGET_DB" --quiet --eval "db.getCollectionNames()"
else
    echo "ERROR: Restore failed"
    exit 1
fi

# Cleanup temp directory
[ -n "${{EXTRACT_DIR:-}}" ] && rm -rf "$EXTRACT_DIR"
"""

SQLITE_RESTORE_TEMPLATE = """#!/bin/bash
# SQLite Restore Script
# Generated: {timestamp}
# Database: {database}

set -euo pipefail

# Configuration
BACKUP_DIR="{backup_dir}"
DB_PATH="{database}"
BACKUP_PATTERN="{backup_pattern}"

# Find backup file
if [ -n "${{1:-}}" ]; then
    BACKUP_FILE="$1"
else
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/$BACKUP_PATTERN 2>/dev/null | head -1)
fi

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found"
    echo "Usage: $0 [backup_file]"
    exit 1
fi

echo "=================================================="
echo "SQLite Restore"
echo "=================================================="
echo "Backup: $BACKUP_FILE"
echo "Target: $DB_PATH"
echo ""

# Decompress if needed
RESTORE_FILE="$BACKUP_FILE"
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "Decompressing backup..."
    TEMP_FILE=$(mktemp)
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    RESTORE_FILE="$TEMP_FILE"
fi

# Verify backup
echo "Verifying backup..."
if ! sqlite3 "$RESTORE_FILE" "PRAGMA integrity_check;" | grep -q "^ok$"; then
    echo "ERROR: Backup integrity check failed"
    [ -n "${{TEMP_FILE:-}}" ] && rm -f "$TEMP_FILE"
    exit 1
fi
echo "Backup verification: OK"

# Check if database exists
if [ -f "$DB_PATH" ]; then
    echo ""
    echo "WARNING: Database '$DB_PATH' already exists!"
    echo "Options:"
    echo "  1. Replace existing (DESTRUCTIVE)"
    echo "  2. Restore to '${{DB_PATH}}.restored'"
    echo "  3. Cancel"
    read -p "Choose [1/2/3]: " CHOICE

    case $CHOICE in
        1)
            TARGET_PATH="$DB_PATH"
            # Backup existing
            echo "Backing up existing database..."
            cp "$DB_PATH" "${{DB_PATH}}.pre_restore.$(date +%Y%m%d_%H%M%S)"
            ;;
        2)
            TARGET_PATH="${{DB_PATH}}.restored"
            ;;
        *)
            echo "Cancelled"
            [ -n "${{TEMP_FILE:-}}" ] && rm -f "$TEMP_FILE"
            exit 0
            ;;
    esac
else
    TARGET_PATH="$DB_PATH"
fi

# Perform restore
echo ""
echo "Restoring to $TARGET_PATH..."
START_TIME=$(date +%s)

if cp "$RESTORE_FILE" "$TARGET_PATH"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    # Verify restored database
    if sqlite3 "$TARGET_PATH" "PRAGMA integrity_check;" | grep -q "^ok$"; then
        echo ""
        echo "=================================================="
        echo "Restore completed successfully!"
        echo "Duration: $DURATION seconds"
        echo "Database: $TARGET_PATH"
        echo "=================================================="

        # Show stats
        echo ""
        echo "Verification:"
        sqlite3 "$TARGET_PATH" "SELECT 'Tables: ' || COUNT(*) FROM sqlite_master WHERE type='table';"
        sqlite3 "$TARGET_PATH" ".tables" | head -5
    else
        echo "ERROR: Restored database failed integrity check"
        exit 1
    fi
else
    echo "ERROR: Restore failed"
    exit 1
fi

# Cleanup
[ -n "${{TEMP_FILE:-}}" ] && rm -f "$TEMP_FILE"
"""


def generate_restore_script(config: RestoreConfig) -> str:
    """Generate restore script based on database type."""
    templates = {
        "postgresql": POSTGRESQL_RESTORE_TEMPLATE,
        "mysql": MYSQL_RESTORE_TEMPLATE,
        "mongodb": MONGODB_RESTORE_TEMPLATE,
        "sqlite": SQLITE_RESTORE_TEMPLATE,
    }

    template = templates.get(config.db_type)
    if not template:
        raise ValueError(f"Unknown database type: {config.db_type}")

    return template.format(
        timestamp=datetime.now().isoformat(),
        database=config.database,
        host=config.host,
        port=config.port,
        user=config.user,
        backup_dir=config.backup_dir,
        backup_pattern=config.backup_pattern,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate database restore scripts for PostgreSQL, MySQL, MongoDB, or SQLite"
    )
    parser.add_argument(
        "--db-type", "-t", required=True, choices=["postgresql", "mysql", "mongodb", "sqlite"], help="Database type"
    )
    parser.add_argument("--database", "-d", required=True, help="Database name (or path for SQLite)")
    parser.add_argument("--host", "-H", default="localhost", help="Database host (default: localhost)")
    parser.add_argument("--port", "-P", type=int, help="Database port (default: depends on db type)")
    parser.add_argument("--user", "-u", default="root", help="Database user (default: root)")
    parser.add_argument("--backup-dir", "-b", default="/var/backups", help="Backup directory (default: /var/backups)")
    parser.add_argument("--backup-pattern", "-p", help="Backup file pattern (default: depends on db type)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    args = parser.parse_args()

    # Default ports
    default_ports = {
        "postgresql": 5432,
        "mysql": 3306,
        "mongodb": 27017,
        "sqlite": 0,
    }

    # Default backup patterns
    default_patterns = {
        "postgresql": "*.dump",
        "mysql": "*.sql*",
        "mongodb": "*_*",
        "sqlite": "*.db*",
    }

    port = args.port or default_ports[args.db_type]
    backup_pattern = args.backup_pattern or default_patterns[args.db_type]

    config = RestoreConfig(
        db_type=args.db_type,
        database=args.database,
        host=args.host,
        port=port,
        user=args.user,
        backup_dir=args.backup_dir,
        backup_pattern=backup_pattern,
    )

    script = generate_restore_script(config)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(script)
        output_path.chmod(0o755)
        print(f"Generated restore script: {output_path}")
    else:
        print(script)

    return 0


if __name__ == "__main__":
    sys.exit(main())
