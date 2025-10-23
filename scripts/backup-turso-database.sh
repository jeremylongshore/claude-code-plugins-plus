#!/bin/bash
################################################################################
# Turso Plugin Backup System
# Backs up ALL plugins and enhancement data to Turso database
# Protects against GitHub lockout with off-site backup
################################################################################

set -e

# Configuration
TURSO_DB_NAME="claude-code-plugins-backup"
BACKUP_DIR="$(pwd)/backups/turso-sync"
PLUGINS_DIR="$(pwd)/plugins"
ENHANCEMENT_DB="$(pwd)/backups/plugin-enhancements/enhancements.db"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if logged in to Turso
check_turso_auth() {
    if ! turso db list &>/dev/null; then
        log_error "Not logged in to Turso!"
        echo ""
        echo "Please login first:"
        echo "  turso auth login"
        echo ""
        echo "Then run this script again."
        exit 1
    fi
    log_success "Turso authentication verified"
}

# Create Turso database if it doesn't exist
create_turso_db() {
    log_info "Checking if database '$TURSO_DB_NAME' exists..."

    if turso db list | grep -q "$TURSO_DB_NAME"; then
        log_success "Database '$TURSO_DB_NAME' already exists"
    else
        log_info "Creating database '$TURSO_DB_NAME'..."
        turso db create "$TURSO_DB_NAME"
        log_success "Database created successfully"
    fi
}

# Initialize backup directory
init_backup_dir() {
    mkdir -p "$BACKUP_DIR"/{metadata,plugins-archive,enhancement-data}
    log_success "Backup directory initialized: $BACKUP_DIR"
}

# Create backup metadata
create_metadata() {
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local plugin_count=$(find "$PLUGINS_DIR" -type d -name ".claude-plugin" | wc -l)

    cat > "$BACKUP_DIR/metadata/backup-info.json" <<EOF
{
  "timestamp": "$timestamp",
  "version": "$(cat VERSION 2>/dev/null || echo 'unknown')",
  "total_plugins": $plugin_count,
  "hostname": "$(hostname)",
  "repository": "claude-code-plugins",
  "backup_type": "full",
  "enhancement_db_included": true
}
EOF

    log_success "Metadata created: $plugin_count plugins"
}

# Create plugins archive
create_plugins_archive() {
    log_info "Creating plugins archive..."

    local archive_name="plugins-$(date +%Y%m%d-%H%M%S).tar.gz"
    local archive_path="$BACKUP_DIR/plugins-archive/$archive_name"

    tar -czf "$archive_path" -C "$PLUGINS_DIR" . 2>/dev/null

    local size=$(du -h "$archive_path" | cut -f1)
    log_success "Archive created: $archive_name ($size)"

    echo "$archive_path"
}

# Export enhancement database
export_enhancement_db() {
    if [ -f "$ENHANCEMENT_DB" ]; then
        log_info "Exporting enhancement database..."

        local export_path="$BACKUP_DIR/enhancement-data/enhancements-$(date +%Y%m%d-%H%M%S).db"
        cp "$ENHANCEMENT_DB" "$export_path"

        # Also export as SQL dump for easier inspection
        sqlite3 "$ENHANCEMENT_DB" .dump > "$BACKUP_DIR/enhancement-data/enhancements-dump.sql"

        log_success "Enhancement database exported"
        echo "$export_path"
    else
        log_warning "No enhancement database found at $ENHANCEMENT_DB"
    fi
}

# Create plugin inventory
create_inventory() {
    log_info "Creating plugin inventory..."

    local inventory_file="$BACKUP_DIR/metadata/plugin-inventory.json"

    # Start JSON array
    echo "[" > "$inventory_file"

    local first=true
    find "$PLUGINS_DIR" -type f -name "plugin.json" | while read plugin_json; do
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$inventory_file"
        fi

        # Extract plugin path relative to plugins dir
        local rel_path=$(dirname $(dirname "$plugin_json") | sed "s|$PLUGINS_DIR/||")

        # Add path info to plugin.json
        jq --arg path "$rel_path" '. + {relative_path: $path}' "$plugin_json" >> "$inventory_file"
    done

    # Close JSON array
    echo "]" >> "$inventory_file"

    log_success "Plugin inventory created"
}

# Upload to Turso
upload_to_turso() {
    log_info "Uploading backup data to Turso..."

    # Create backup summary table if not exists
    turso db shell "$TURSO_DB_NAME" <<EOF
CREATE TABLE IF NOT EXISTS backup_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    version TEXT,
    plugin_count INTEGER,
    archive_size INTEGER,
    backup_metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plugin_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plugin_name TEXT NOT NULL,
    category TEXT,
    version TEXT,
    relative_path TEXT,
    metadata_json TEXT,
    backup_id INTEGER,
    FOREIGN KEY (backup_id) REFERENCES backup_history(id)
);
EOF

    # Read metadata
    local metadata=$(cat "$BACKUP_DIR/metadata/backup-info.json")
    local plugin_count=$(echo "$metadata" | jq -r '.total_plugins')
    local version=$(echo "$metadata" | jq -r '.version')
    local timestamp=$(echo "$metadata" | jq -r '.timestamp')

    # Get archive size
    local archive_path=$(ls -t "$BACKUP_DIR/plugins-archive/"*.tar.gz | head -1)
    local archive_size=$(stat -f%z "$archive_path" 2>/dev/null || stat -c%s "$archive_path")

    # Insert backup record
    local backup_id=$(turso db shell "$TURSO_DB_NAME" <<EOF | tail -1
INSERT INTO backup_history (timestamp, version, plugin_count, archive_size, backup_metadata)
VALUES ('$timestamp', '$version', $plugin_count, $archive_size, '$(echo "$metadata" | sed "s/'/''/g")');
SELECT last_insert_rowid();
EOF
)

    log_success "Backup record created in Turso (ID: $backup_id)"

    # Upload plugin metadata
    log_info "Uploading plugin inventory to Turso..."

    cat "$BACKUP_DIR/metadata/plugin-inventory.json" | jq -c '.[]' | while read plugin; do
        local name=$(echo "$plugin" | jq -r '.name')
        local version=$(echo "$plugin" | jq -r '.version')
        local path=$(echo "$plugin" | jq -r '.relative_path')
        local category=$(echo "$path" | cut -d'/' -f1)

        turso db shell "$TURSO_DB_NAME" <<EOF >/dev/null
INSERT INTO plugin_metadata (plugin_name, category, version, relative_path, metadata_json, backup_id)
VALUES ('$name', '$category', '$version', '$path', '$(echo "$plugin" | sed "s/'/''/g")', $backup_id);
EOF
    done

    log_success "Plugin metadata uploaded to Turso"

    echo "$backup_id"
}

# Store file references in Turso
store_file_references() {
    local backup_id=$1

    log_info "Storing file references in Turso..."

    # Create files table if not exists
    turso db shell "$TURSO_DB_NAME" <<EOF
CREATE TABLE IF NOT EXISTS backup_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_id INTEGER NOT NULL,
    file_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_hash TEXT,
    storage_location TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (backup_id) REFERENCES backup_history(id)
);
EOF

    # Add archive reference
    local archive_path=$(ls -t "$BACKUP_DIR/plugins-archive/"*.tar.gz | head -1)
    local archive_name=$(basename "$archive_path")
    local archive_size=$(stat -f%z "$archive_path" 2>/dev/null || stat -c%s "$archive_path")
    local archive_hash=$(sha256sum "$archive_path" | cut -d' ' -f1)

    turso db shell "$TURSO_DB_NAME" <<EOF >/dev/null
INSERT INTO backup_files (backup_id, file_type, file_path, file_size, file_hash, storage_location)
VALUES ($backup_id, 'plugins_archive', '$archive_name', $archive_size, '$archive_hash', 'local:$archive_path');
EOF

    # Add enhancement DB reference if exists
    if [ -f "$ENHANCEMENT_DB" ]; then
        local db_path=$(ls -t "$BACKUP_DIR/enhancement-data/"*.db | head -1)
        local db_name=$(basename "$db_path")
        local db_size=$(stat -f%z "$db_path" 2>/dev/null || stat -c%s "$db_path")
        local db_hash=$(sha256sum "$db_path" | cut -d' ' -f1)

        turso db shell "$TURSO_DB_NAME" <<EOF >/dev/null
INSERT INTO backup_files (backup_id, file_type, file_path, file_size, file_hash, storage_location)
VALUES ($backup_id, 'enhancement_db', '$db_name', $db_size, '$db_hash', 'local:$db_path');
EOF
    fi

    log_success "File references stored in Turso"
}

# Display summary
display_summary() {
    local backup_id=$1

    echo ""
    echo "=================================="
    echo "  TURSO BACKUP COMPLETE"
    echo "=================================="
    echo ""
    echo "Backup ID: $backup_id"
    echo "Database: $TURSO_DB_NAME"
    echo "Timestamp: $(date)"
    echo ""
    echo "Backed up files:"
    ls -lh "$BACKUP_DIR/plugins-archive/" | tail -1
    if [ -f "$ENHANCEMENT_DB" ]; then
        ls -lh "$BACKUP_DIR/enhancement-data/" | tail -1
    fi
    echo ""
    echo "View backup in Turso:"
    echo "  turso db shell $TURSO_DB_NAME"
    echo "  SELECT * FROM backup_history WHERE id = $backup_id;"
    echo ""
    echo "To restore from this backup:"
    echo "  ./scripts/turso-plugin-restore.sh $backup_id"
    echo ""
}

# Main execution
main() {
    echo "=================================="
    echo "  TURSO PLUGIN BACKUP SYSTEM"
    echo "=================================="
    echo ""

    # Step 1: Check authentication
    check_turso_auth

    # Step 2: Create database
    create_turso_db

    # Step 3: Initialize backup directory
    init_backup_dir

    # Step 4: Create metadata
    create_metadata

    # Step 5: Create plugins archive
    create_plugins_archive

    # Step 6: Export enhancement database
    export_enhancement_db

    # Step 7: Create inventory
    create_inventory

    # Step 8: Upload to Turso
    backup_id=$(upload_to_turso)

    # Step 9: Store file references
    store_file_references "$backup_id"

    # Step 10: Display summary
    display_summary "$backup_id"

    log_success "Backup completed successfully!"
}

# Run main
main
