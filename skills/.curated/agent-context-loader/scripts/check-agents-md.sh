#!/bin/bash
#
# Agent Context Manager - Directory Change Hook
#
# This script runs automatically when:
# - Starting a new Claude Code session
# - Changing directories during a session
#
# Purpose: Detect AGENTS.md files and remind Claude to load agent-specific context
#

set -e

# Get current working directory
CWD=$(pwd)

# ANSI color codes for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AGENTS.md exists in current directory
if [ -f "${CWD}/AGENTS.md" ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}📋 AGENTS.md detected in current directory${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}⚡ Agent Context Manager is active${NC}"
    echo ""
    echo "The agent-context-loader skill will automatically load"
    echo "agent-specific instructions from AGENTS.md"
    echo ""
    echo -e "${BLUE}Location:${NC} ${CWD}/AGENTS.md"
    echo ""
    echo -e "${YELLOW}What happens next:${NC}"
    echo "  1. Claude will read AGENTS.md automatically"
    echo "  2. Agent-specific rules will be incorporated"
    echo "  3. Instructions will be active for this session"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Return success to indicate AGENTS.md was found
    exit 0
else
    # AGENTS.md not found - silent exit (no error)
    # This is normal for directories without agent-specific rules
    exit 0
fi
