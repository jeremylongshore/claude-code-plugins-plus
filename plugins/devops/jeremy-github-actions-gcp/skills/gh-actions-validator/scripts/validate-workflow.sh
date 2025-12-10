#!/bin/bash
# validate-workflow.sh - Validate GitHub Actions workflows for GCP security

set -euo pipefail

WORKFLOW_DIR="${1:-.github/workflows}"

echo "Validating GitHub Actions Workflows"
echo "Directory: $WORKFLOW_DIR"
echo ""

ISSUES=0

# Check for WIF usage
echo "Checking for Workload Identity Federation..."
if grep -r "workload_identity_provider" "$WORKFLOW_DIR" 2>/dev/null; then
    echo "✓ Using Workload Identity Federation"
else
    echo "✗ No WIF configuration found - use WIF instead of JSON keys"
    ((ISSUES++))
fi

# Check for JSON keys (security issue)
echo "Checking for JSON service account keys..."
if grep -r "credentials_json\|service-account.*json" "$WORKFLOW_DIR" 2>/dev/null; then
    echo "✗ JSON keys detected - migrate to Workload Identity Federation"
    ((ISSUES++))
else
    echo "✓ No JSON keys found"
fi

# Check for OIDC permissions
echo "Checking for id-token permissions..."
if grep -r "id-token.*write" "$WORKFLOW_DIR" 2>/dev/null; then
    echo "✓ OIDC permissions configured"
else
    echo "⚠ Missing 'id-token: write' permission"
    ((ISSUES++))
fi

# Check for security scans
echo "Checking for security scans..."
if grep -r "trufflehog\|trivy\|snyk" "$WORKFLOW_DIR" 2>/dev/null; then
    echo "✓ Security scanning configured"
else
    echo "⚠ No security scanning detected"
fi

echo ""
if (( ISSUES == 0 )); then
    echo "✓ Workflows are secure"
    exit 0
else
    echo "✗ Found $ISSUES security issues"
    exit 1
fi
