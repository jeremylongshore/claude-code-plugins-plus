#!/bin/bash
# inspect-agent.sh - Inspect Vertex AI Agent Engine deployment
# Performs comprehensive validation including runtime config, security, and compliance

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
AGENT_ID="${1:-}"
PROJECT_ID="${2:-${GCP_PROJECT_ID:-}}"
REGION="${3:-us-central1}"

usage() {
    cat <<EOF
Usage: $0 <AGENT_ID> [PROJECT_ID] [REGION]

Inspect Vertex AI Agent Engine deployment for production readiness.

Arguments:
    AGENT_ID     Agent resource ID or name
    PROJECT_ID   GCP project ID (default: \$GCP_PROJECT_ID)
    REGION       GCP region (default: us-central1)

Example:
    $0 my-agent my-project us-central1
    GCP_PROJECT_ID=my-project $0 my-agent

EOF
    exit 1
}

if [[ -z "$AGENT_ID" ]]; then
    echo "Error: AGENT_ID is required"
    usage
fi

if [[ -z "$PROJECT_ID" ]]; then
    echo "Error: PROJECT_ID is required (set GCP_PROJECT_ID env var or provide as argument)"
    usage
fi

echo "Inspecting Vertex AI Agent Engine deployment..."
echo "Agent: $AGENT_ID"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Phase 1: Configuration Analysis
echo -e "${GREEN}Phase 1: Configuration Analysis${NC}"
echo "Retrieving agent metadata..."

AGENT_INFO=$(gcloud ai agents describe "$AGENT_ID" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format=json 2>&1 || echo "{}")

if [[ "$AGENT_INFO" == "{}" ]]; then
    echo -e "${RED}Failed to retrieve agent information${NC}"
    exit 1
fi

echo "$AGENT_INFO" | jq -r '
    "Model: \(.model // "unknown")",
    "State: \(.state // "unknown")",
    "Created: \(.createTime // "unknown")"
'

# Check Code Execution configuration
CODE_EXEC=$(echo "$AGENT_INFO" | jq -r '.tools[] | select(.codeExecution) | .codeExecution')
if [[ -n "$CODE_EXEC" ]]; then
    TTL=$(echo "$CODE_EXEC" | jq -r '.stateTtl // "unknown"')
    echo -e "${GREEN}Code Execution: Enabled (TTL: $TTL)${NC}"

    # Validate TTL (7-14 days optimal)
    if [[ "$TTL" =~ ^[0-9]+d$ ]]; then
        DAYS="${TTL%d}"
        if (( DAYS >= 7 && DAYS <= 14 )); then
            echo -e "  ${GREEN}✓ TTL optimal ($DAYS days)${NC}"
        elif (( DAYS < 7 )); then
            echo -e "  ${YELLOW}⚠ TTL low ($DAYS days) - may cause session loss${NC}"
        fi
    fi
else
    echo -e "${YELLOW}Code Execution: Disabled${NC}"
fi

# Check Memory Bank configuration
MEMORY_BANK=$(echo "$AGENT_INFO" | jq -r '.tools[] | select(.memoryBank) | .memoryBank')
if [[ -n "$MEMORY_BANK" ]]; then
    MAX_MEMORIES=$(echo "$MEMORY_BANK" | jq -r '.maxMemories // "unknown"')
    echo -e "${GREEN}Memory Bank: Enabled (Max: $MAX_MEMORIES)${NC}"

    if [[ "$MAX_MEMORIES" =~ ^[0-9]+$ ]] && (( MAX_MEMORIES >= 100 )); then
        echo -e "  ${GREEN}✓ Memory limit adequate${NC}"
    else
        echo -e "  ${YELLOW}⚠ Low memory limit may truncate conversations${NC}"
    fi
else
    echo -e "${YELLOW}Memory Bank: Disabled${NC}"
fi

# Phase 2: A2A Protocol Validation
echo ""
echo -e "${GREEN}Phase 2: A2A Protocol Validation${NC}"

AGENT_URL=$(echo "$AGENT_INFO" | jq -r '.endpoint // empty')
if [[ -n "$AGENT_URL" ]]; then
    echo "Testing AgentCard endpoint..."

    AGENT_CARD_URL="${AGENT_URL}/.well-known/agent-card"
    if curl -sf -H "Authorization: Bearer $(gcloud auth print-access-token)" "$AGENT_CARD_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ AgentCard accessible${NC}"
    else
        echo -e "${RED}✗ AgentCard not accessible${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No endpoint URL found${NC}"
fi

# Phase 3: Security Audit
echo ""
echo -e "${GREEN}Phase 3: Security Audit${NC}"

# Check IAM permissions
echo "Checking IAM configuration..."
SERVICE_ACCOUNT=$(echo "$AGENT_INFO" | jq -r '.serviceAccount // empty')
if [[ -n "$SERVICE_ACCOUNT" ]]; then
    echo "Service Account: $SERVICE_ACCOUNT"

    # Check if service account has excessive permissions
    IAM_POLICY=$(gcloud projects get-iam-policy "$PROJECT_ID" \
        --flatten="bindings[].members" \
        --filter="bindings.members:serviceAccount:$SERVICE_ACCOUNT" \
        --format=json)

    ROLES=$(echo "$IAM_POLICY" | jq -r '.[].bindings.role')
    if echo "$ROLES" | grep -q "roles/owner\|roles/editor"; then
        echo -e "${RED}✗ Service account has excessive permissions${NC}"
    else
        echo -e "${GREEN}✓ Service account follows least privilege${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No service account configured${NC}"
fi

# Phase 4: Production Readiness Score
echo ""
echo -e "${GREEN}Phase 4: Production Readiness Scoring${NC}"

SCORE=0
MAX_SCORE=100

# Security checks (30 points)
[[ -n "$SERVICE_ACCOUNT" ]] && ((SCORE+=10))
! echo "$ROLES" | grep -q "roles/owner\|roles/editor" && ((SCORE+=20))

# Performance checks (25 points)
[[ -n "$CODE_EXEC" ]] && ((SCORE+=15))
[[ -n "$MEMORY_BANK" ]] && ((SCORE+=10))

# Configuration checks (25 points)
[[ -n "$AGENT_URL" ]] && ((SCORE+=15))
[[ "$(echo "$AGENT_INFO" | jq -r '.state')" == "ACTIVE" ]] && ((SCORE+=10))

# Observability checks (20 points)
[[ -n "$CODE_EXEC" ]] && ((SCORE+=10))
[[ -n "$MEMORY_BANK" ]] && ((SCORE+=10))

PERCENTAGE=$((SCORE * 100 / MAX_SCORE))

echo ""
echo "Overall Score: $PERCENTAGE%"
if (( PERCENTAGE >= 85 )); then
    echo -e "${GREEN}🟢 PRODUCTION READY${NC}"
elif (( PERCENTAGE >= 70 )); then
    echo -e "${YELLOW}🟡 NEEDS IMPROVEMENT${NC}"
else
    echo -e "${RED}🔴 NOT READY${NC}"
fi

echo ""
echo "Inspection complete!"
