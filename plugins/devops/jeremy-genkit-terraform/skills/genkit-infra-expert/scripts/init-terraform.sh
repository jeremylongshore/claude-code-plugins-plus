#!/bin/bash
# init-terraform.sh - Initialize Terraform for Firebase Genkit infrastructure

set -euo pipefail

PROJECT_ID="${1:-${GCP_PROJECT_ID:-}}"
REGION="${2:-us-central1}"

if [[ -z "$PROJECT_ID" ]]; then
    echo "Usage: $0 <PROJECT_ID> [REGION]"
    exit 1
fi

echo "Initializing Terraform for Firebase Genkit Infrastructure"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

mkdir -p terraform/modules/genkit

cat > terraform/main.tf <<EOF
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "$PROJECT_ID"
  region  = "$REGION"
}

resource "google_project_service" "genkit_apis" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "cloudfunctions.googleapis.com"
  ])
  service = each.value
}
EOF

echo "✓ Terraform initialized for Genkit"
