#!/bin/bash

# ANTHROPIC CLAUDE CODE PLUGIN COMPLIANCE AUDIT SUITE
# Run all validation scripts in sequence

echo "=========================================="
echo "ANTHROPIC PLUGIN COMPLIANCE AUDIT SUITE"
echo "=========================================="
echo ""
echo "Starting comprehensive audit..."
echo ""

# Make all audit scripts executable
chmod +x audit-*.sh

# Run Phase 2: Plugin Manifests
echo "Running Phase 2: Plugin Manifest Validation..."
./audit-plugin-manifests.sh > audit-manifests.log 2>&1
echo "✓ Phase 2 complete (see audit-manifests.log)"
echo ""

# Run Phase 3: Directory Structures
echo "Running Phase 3: Directory Structure Validation..."
./audit-directory-structures.sh > audit-structures.log 2>&1
echo "✓ Phase 3 complete (see audit-structures.log)"
echo ""

# Run Phase 4: Slash Commands
echo "Running Phase 4: Slash Commands Validation..."
./audit-slash-commands.sh > audit-commands.log 2>&1
echo "✓ Phase 4 complete (see audit-commands.log)"
echo ""

# Run Phase 5: Agents
echo "Running Phase 5: Agents Validation..."
./audit-agents.sh > audit-agents.log 2>&1
echo "✓ Phase 5 complete (see audit-agents.log)"
echo ""

# Quick summary
echo "=========================================="
echo "AUDIT SUMMARY"
echo "=========================================="
echo ""

# Extract key metrics
manifest_rate=$(tail -1 audit-manifests.log | grep -oP '\d+(?=%)')
structure_rate=$(tail -1 audit-structures.log | grep -oP '\d+(?=%)')
command_rate=$(tail -1 audit-commands.log | grep -oP '\d+(?=%)')
agent_rate=$(tail -1 audit-agents.log | grep -oP '\d+(?=%)')

echo "Manifest Compliance: ${manifest_rate:-N/A}%"
echo "Structure Compliance: ${structure_rate:-N/A}%"
echo "Command Compliance: ${command_rate:-N/A}%"
echo "Agent Compliance: ${agent_rate:-N/A}%"
echo ""

# Check for critical issues
if grep -q "CRITICAL" audit-*.log; then
    echo "⚠️  CRITICAL ISSUES FOUND - Review logs for details"
else
    echo "✅ NO CRITICAL ISSUES FOUND"
fi

echo ""
echo "Full report available at: claudes-docs/ANTHROPIC_COMPLIANCE_AUDIT_REPORT.md"
echo "Individual logs saved as: audit-*.log"
echo ""
echo "Audit complete!"