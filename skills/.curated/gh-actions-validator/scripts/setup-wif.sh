#!/bin/bash
# setup-wif.sh - Setup Workload Identity Federation for GitHub Actions

set -euo pipefail

PROJECT_ID="${1:-}"
REPO_OWNER="${2:-}"
REPO_NAME="${3:-}"

if [[ -z "$PROJECT_ID" ]] || [[ -z "$REPO_OWNER" ]] || [[ -z "$REPO_NAME" ]]; then
    cat <<EOF
Usage: $0 <PROJECT_ID> <REPO_OWNER> <REPO_NAME>

Setup Workload Identity Federation for GitHub Actions GCP authentication.

Example:
    $0 my-project jeremylongshore my-repo

EOF
    exit 1
fi

echo "Setting up Workload Identity Federation"
echo "Project: $PROJECT_ID"
echo "Repository: $REPO_OWNER/$REPO_NAME"
echo ""

# Create workload identity pool
echo "Creating workload identity pool..."
gcloud iam workload-identity-pools create "github-pool" \
    --project="$PROJECT_ID" \
    --location="global" \
    --display-name="GitHub Actions Pool" || echo "Pool may already exist"

# Create OIDC provider
echo "Creating OIDC provider..."
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
    --project="$PROJECT_ID" \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
    --attribute-condition="assertion.repository=='$REPO_OWNER/$REPO_NAME'" || echo "Provider may already exist"

# Get WIF provider name
WIF_PROVIDER="projects/$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-pool/providers/github-provider"

echo ""
echo "✓ Workload Identity Federation configured"
echo ""
echo "Add these secrets to your GitHub repository:"
echo "  WIF_PROVIDER: $WIF_PROVIDER"
echo "  GCP_PROJECT_ID: $PROJECT_ID"
echo ""
echo "Create a service account and grant it access:"
echo "  gcloud iam service-accounts create github-actions --project=$PROJECT_ID"
echo "  gcloud iam service-accounts add-iam-policy-binding github-actions@$PROJECT_ID.iam.gserviceaccount.com \\"
echo "    --role=roles/iam.workloadIdentityUser \\"
echo "    --member=\"principalSet://iam.googleapis.com/$WIF_PROVIDER/attribute.repository/$REPO_OWNER/$REPO_NAME\""
