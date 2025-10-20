#!/bin/bash
################################################################################
# Auto-Trigger Post-Batch Automation
# Watches for batch completion and automatically runs verification/reporting
# Usage: ./scripts/auto-trigger-post-batch.sh
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

LOG_FILE="overnight-enhancement-all-plugins.log"
BATCH_COMPLETE_MARKER="BATCH COMPLETE"
CHECK_INTERVAL=60  # Check every 60 seconds

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Batch Completion Watcher${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${BLUE}Monitoring:${NC} $LOG_FILE"
echo -e "${BLUE}Looking for:${NC} '$BATCH_COMPLETE_MARKER'"
echo -e "${BLUE}Check interval:${NC} ${CHECK_INTERVAL}s"
echo ""

while true; do
    if grep -q "$BATCH_COMPLETE_MARKER" "$LOG_FILE" 2>/dev/null; then
        echo ""
        echo -e "${GREEN}✅ BATCH COMPLETE DETECTED!${NC}"
        echo ""
        echo -e "${BLUE}Starting post-batch automation...${NC}"
        echo ""

        # Run the post-batch automation script
        ./scripts/post-batch-automation.sh

        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  Auto-trigger completed successfully${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo "Morning review report has been generated."
        echo "Check for: MORNING-REVIEW-REPORT-*.md"

        break
    fi

    # Show status every check
    CURRENT_TIME=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[$CURRENT_TIME]${NC} Checking... (batch not complete yet)"

    sleep $CHECK_INTERVAL
done
