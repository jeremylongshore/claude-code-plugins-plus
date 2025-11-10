#!/bin/bash
#
# Validate GitHub Actions workflow for Vertex AI / GCP best practices
# This script is called by hooks before writing/editing workflow files
#

set -e

WORKFLOW_FILE="$1"

echo "🔍 Validating GitHub Actions workflow: $WORKFLOW_FILE"

# Check 1: WIF - Must use workload_identity_provider, NOT credentials_json
if grep -q "credentials_json" "$WORKFLOW_FILE"; then
    echo "❌ SECURITY VIOLATION: JSON service account keys detected"
    echo "   Use Workload Identity Federation (WIF) instead:"
    echo "   workload_identity_provider: \${{ secrets.WIF_PROVIDER }}"
    echo "   service_account: \${{ secrets.WIF_SERVICE_ACCOUNT }}"
    exit 1
fi

# Check 2: OIDC Permissions - Must have id-token: write for WIF
if grep -q "workload_identity_provider" "$WORKFLOW_FILE"; then
    if ! grep -q "id-token: write" "$WORKFLOW_FILE"; then
        echo "❌ MISSING REQUIRED PERMISSION: id-token: write"
        echo "   Workload Identity Federation requires OIDC token permission:"
        echo ""
        echo "   permissions:"
        echo "     contents: read"
        echo "     id-token: write  # REQUIRED for WIF"
        exit 1
    fi
fi

# Check 3: IAM - No overly permissive roles
if grep -E "roles/owner|roles/editor" "$WORKFLOW_FILE"; then
    echo "❌ SECURITY VIOLATION: Overly permissive IAM roles detected"
    echo "   Use least privilege roles instead:"
    echo "   - roles/run.admin"
    echo "   - roles/iam.serviceAccountUser"
    echo "   - roles/aiplatform.user"
    exit 1
fi

# Check 4: Secrets - No hardcoded values
if grep -E "GOOGLE_APPLICATION_CREDENTIALS.*=|GCP_SA_KEY.*=" "$WORKFLOW_FILE"; then
    echo "❌ SECURITY VIOLATION: Hardcoded credentials detected"
    echo "   Use GitHub secrets: \${{ secrets.SECRET_NAME }}"
    exit 1
fi

# Check 5: Vertex AI deployments - Must have post-deployment validation
if grep -q "vertex" "$WORKFLOW_FILE" || grep -q "aiplatform" "$WORKFLOW_FILE"; then
    if ! grep -q "validate-deployment\|validate-agent" "$WORKFLOW_FILE"; then
        echo "⚠️  WARNING: Vertex AI deployment without validation step"
        echo "   Add post-deployment validation:"
        echo "   - name: Validate Deployment"
        echo "     run: python scripts/validate-deployment.py"
    fi
fi

# Check 6: Security scanning - Recommended for production workflows
if grep -q "deploy" "$WORKFLOW_FILE"; then
    if ! grep -q "trivy\|trufflehog" "$WORKFLOW_FILE"; then
        echo "⚠️  RECOMMENDATION: Add security scanning before deployment"
        echo "   - uses: aquasecurity/trivy-action@master"
        echo "   - uses: trufflesecurity/trufflehog@main"
    fi
fi

echo "✅ GitHub Actions workflow validation passed"
exit 0
