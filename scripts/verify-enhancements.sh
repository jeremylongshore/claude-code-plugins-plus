#!/bin/bash
################################################################################
# Enhancement Verification Script
# Validates quality of overnight plugin enhancement batch
# Run after overnight-plugin-enhancer.py completes
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
DB_PATH="backups/plugin-enhancements/enhancements.db"
PLUGINS_DIR="plugins"
MIN_SKILL_SIZE=8000
SAMPLE_SIZE=10

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

echo "============================================================"
echo "  ENHANCEMENT VERIFICATION REPORT"
echo "  Generated: $(date)"
echo "============================================================"
echo ""

################################################################################
# 1. Database Verification
################################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. DATABASE VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check database exists
if [ ! -f "$DB_PATH" ]; then
    log_error "Enhancement database not found: $DB_PATH"
    exit 1
fi
log_success "Enhancement database found"

# Count total enhancements
TOTAL=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM enhancements WHERE status = 'success';")
log_info "Total successful enhancements: $TOTAL"

if [ "$TOTAL" -ge 230 ]; then
    log_success "Achievement target met (≥230 plugins)"
else
    log_error "Achievement target not met ($TOTAL < 230 plugins)"
fi

# Check for failures
FAILURES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM enhancements WHERE status != 'success';")
if [ "$FAILURES" -eq 0 ]; then
    log_success "No failures recorded (100% success rate)"
else
    log_warning "Found $FAILURES failed enhancements"
    echo ""
    echo "Failed plugins:"
    sqlite3 "$DB_PATH" "SELECT plugin_name, error_message FROM enhancements WHERE status != 'success';" | while read line; do
        echo "  - $line"
    done
    echo ""
fi

# Average processing time
AVG_TIME=$(sqlite3 "$DB_PATH" "SELECT AVG(processing_time_seconds) FROM enhancements WHERE status = 'success';" | xargs printf "%.1f")
log_info "Average processing time: ${AVG_TIME}s per plugin"

echo ""

################################################################################
# 2. SKILL.md File Verification
################################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. SKILL.md FILE VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Find all SKILL.md files
SKILL_FILES=$(find "$PLUGINS_DIR" -path "*/skills/skill-adapter/SKILL.md" 2>/dev/null)
SKILL_COUNT=$(echo "$SKILL_FILES" | wc -l)

log_info "Found $SKILL_COUNT SKILL.md files"

# Check file sizes
UNDERSIZED=0
OVERSIZED=0
GOOD_SIZE=0

while IFS= read -r skill_file; do
    if [ -f "$skill_file" ]; then
        SIZE=$(wc -c < "$skill_file")
        if [ "$SIZE" -lt "$MIN_SKILL_SIZE" ]; then
            ((UNDERSIZED++))
        elif [ "$SIZE" -gt 20000 ]; then
            ((OVERSIZED++))
        else
            ((GOOD_SIZE++))
        fi
    fi
done <<< "$SKILL_FILES"

if [ "$UNDERSIZED" -eq 0 ]; then
    log_success "All SKILL.md files meet minimum size (≥${MIN_SKILL_SIZE} bytes)"
else
    log_warning "$UNDERSIZED SKILL.md files below ${MIN_SKILL_SIZE} bytes"
fi

if [ "$OVERSIZED" -gt 0 ]; then
    log_warning "$OVERSIZED SKILL.md files exceed 20KB (unusually large)"
fi

log_info "Size distribution: $GOOD_SIZE optimal, $UNDERSIZED small, $OVERSIZED large"

echo ""

################################################################################
# 3. Frontmatter Validation
################################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. FRONTMATTER VALIDATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

MISSING_FRONTMATTER=0
INVALID_FRONTMATTER=0

while IFS= read -r skill_file; do
    if [ -f "$skill_file" ]; then
        # Check if file starts with ---
        FIRST_LINE=$(head -1 "$skill_file")
        if [ "$FIRST_LINE" != "---" ]; then
            ((MISSING_FRONTMATTER++))
        else
            # Check if frontmatter is properly closed
            FRONTMATTER_CLOSE=$(sed -n '2,10p' "$skill_file" | grep -n "^---$" | head -1 | cut -d: -f1)
            if [ -z "$FRONTMATTER_CLOSE" ]; then
                ((INVALID_FRONTMATTER++))
            fi
        fi
    fi
done <<< "$SKILL_FILES"

if [ "$MISSING_FRONTMATTER" -eq 0 ] && [ "$INVALID_FRONTMATTER" -eq 0 ]; then
    log_success "All SKILL.md files have valid YAML frontmatter"
else
    [ "$MISSING_FRONTMATTER" -gt 0 ] && log_error "$MISSING_FRONTMATTER files missing frontmatter"
    [ "$INVALID_FRONTMATTER" -gt 0 ] && log_error "$INVALID_FRONTMATTER files have invalid frontmatter"
fi

echo ""

################################################################################
# 4. Random Sample Quality Check
################################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. RANDOM SAMPLE QUALITY CHECK ($SAMPLE_SIZE samples)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get random sample
SAMPLE=$(echo "$SKILL_FILES" | shuf -n "$SAMPLE_SIZE")

SAMPLE_NUM=0
while IFS= read -r skill_file; do
    ((SAMPLE_NUM++))
    PLUGIN_NAME=$(echo "$skill_file" | sed 's|.*/plugins/||; s|/.*||')
    SIZE=$(wc -c < "$skill_file" 2>/dev/null || echo "0")

    echo "Sample $SAMPLE_NUM: $PLUGIN_NAME"
    echo "  Path: $skill_file"
    echo "  Size: $SIZE bytes"

    # Check for key sections
    HAS_NAME=$(grep -c "^name:" "$skill_file" 2>/dev/null || echo "0")
    HAS_DESC=$(grep -c "^description:" "$skill_file" 2>/dev/null || echo "0")
    HAS_CONTENT=$(tail -n +10 "$skill_file" | wc -l)

    echo "  Has name field: $([ "$HAS_NAME" -gt 0 ] && echo "✓" || echo "✗")"
    echo "  Has description: $([ "$HAS_DESC" -gt 0 ] && echo "✓" || echo "✗")"
    echo "  Content lines: $HAS_CONTENT"

    if [ "$SIZE" -ge "$MIN_SKILL_SIZE" ] && [ "$HAS_NAME" -gt 0 ] && [ "$HAS_DESC" -gt 0 ]; then
        echo "  Status: ${GREEN}PASS${NC}"
    else
        echo "  Status: ${YELLOW}NEEDS REVIEW${NC}"
    fi

    echo ""
done <<< "$SAMPLE"

echo ""

################################################################################
# 5. Backup Verification
################################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. BACKUP VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

BACKUP_DIR="backups/plugin-enhancements/plugin-backups"
if [ -d "$BACKUP_DIR" ]; then
    BACKUP_COUNT=$(find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)
    log_info "Found $BACKUP_COUNT plugin backups"

    if [ "$BACKUP_COUNT" -ge "$TOTAL" ]; then
        log_success "Backup count matches or exceeds enhancement count"
    else
        log_warning "Backup count ($BACKUP_COUNT) less than enhancements ($TOTAL)"
    fi
else
    log_error "Backup directory not found: $BACKUP_DIR"
fi

# Check database backup
if [ -f "${DB_PATH}.backup" ] || [ -f "${DB_PATH}-backup" ]; then
    log_success "Database backup exists"
else
    log_warning "No database backup found"
fi

echo ""

################################################################################
# 6. Git Status Check
################################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. GIT STATUS CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

UNCOMMITTED=$(git status --porcelain | wc -l)
if [ "$UNCOMMITTED" -eq 0 ]; then
    log_success "No uncommitted changes (ready for release)"
else
    log_info "Found $UNCOMMITTED uncommitted changes"
    echo ""
    echo "Uncommitted files:"
    git status --short | head -20
    echo ""
fi

echo ""

################################################################################
# Final Summary
################################################################################
echo "============================================================"
echo "  VERIFICATION SUMMARY"
echo "============================================================"
echo ""
echo "Total checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
echo ""

if [ "$FAILED_CHECKS" -eq 0 ]; then
    echo -e "${GREEN}✓ ALL VERIFICATIONS PASSED${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review random sample output above"
    echo "  2. Run manual spot check: ./scripts/manual-spot-check.sh"
    echo "  3. Proceed with release: Follow RELEASE-PLAN-AGENT-SKILLS-v1.2.0.md"
    exit 0
else
    echo -e "${YELLOW}⚠ SOME VERIFICATIONS FAILED${NC}"
    echo ""
    echo "Review failures above before proceeding with release."
    exit 1
fi
