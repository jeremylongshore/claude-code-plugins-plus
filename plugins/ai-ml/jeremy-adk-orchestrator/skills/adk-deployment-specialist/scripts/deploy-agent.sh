#!/bin/bash
# deploy-agent.sh - Deploy ADK agent to Vertex AI Agent Engine
# Handles deployment with Code Execution and Memory Bank configuration

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
AGENT_FILE="${1:-}"
PROJECT_ID="${2:-${GCP_PROJECT_ID:-}}"
REGION="${3:-us-central1}"
SERVICE_NAME="${4:-${AGENT_FILE%.py}}"

usage() {
    cat <<EOF
Usage: $0 <AGENT_FILE> [PROJECT_ID] [REGION] [SERVICE_NAME]

Deploy ADK agent to Vertex AI Agent Engine with A2A protocol support.

Arguments:
    AGENT_FILE    Python file containing agent definition
    PROJECT_ID    GCP project ID (default: \$GCP_PROJECT_ID)
    REGION        GCP region (default: us-central1)
    SERVICE_NAME  Agent service name (default: agent filename)

Example:
    $0 my_agent.py my-project us-central1 my-agent
    GCP_PROJECT_ID=my-project $0 deployment_agent.py

Environment Variables:
    GCP_PROJECT_ID    Default project ID
    ENABLE_CODE_EXEC  Enable Code Execution Sandbox (default: true)
    ENABLE_MEMORY     Enable Memory Bank (default: true)
    STATE_TTL         Code Execution state TTL (default: 14d)
    MAX_MEMORIES      Memory Bank max memories (default: 500)

EOF
    exit 1
}

if [[ -z "$AGENT_FILE" ]]; then
    echo "Error: AGENT_FILE is required"
    usage
fi

if [[ ! -f "$AGENT_FILE" ]]; then
    echo -e "${RED}Error: Agent file not found: $AGENT_FILE${NC}"
    exit 1
fi

if [[ -z "$PROJECT_ID" ]]; then
    echo "Error: PROJECT_ID is required (set GCP_PROJECT_ID env var or provide as argument)"
    usage
fi

# Get configuration from environment
ENABLE_CODE_EXEC="${ENABLE_CODE_EXEC:-true}"
ENABLE_MEMORY="${ENABLE_MEMORY:-true}"
STATE_TTL="${STATE_TTL:-14d}"
MAX_MEMORIES="${MAX_MEMORIES:-500}"

echo -e "${GREEN}Deploying ADK Agent to Vertex AI Agent Engine${NC}"
echo "Agent File: $AGENT_FILE"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"
echo ""
echo "Configuration:"
echo "  Code Execution: $ENABLE_CODE_EXEC (TTL: $STATE_TTL)"
echo "  Memory Bank: $ENABLE_MEMORY (Max: $MAX_MEMORIES)"
echo ""

# Check if ADK is installed
if ! command -v adk &> /dev/null; then
    echo -e "${YELLOW}ADK CLI not found. Installing...${NC}"
    pip install google-adk
fi

# Validate agent file
echo "Validating agent file..."
if ! python3 -m py_compile "$AGENT_FILE"; then
    echo -e "${RED}Error: Agent file has syntax errors${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Agent file valid${NC}"

# Build deployment command
DEPLOY_CMD="adk deploy"
DEPLOY_CMD="$DEPLOY_CMD --agent-file $AGENT_FILE"
DEPLOY_CMD="$DEPLOY_CMD --project-id $PROJECT_ID"
DEPLOY_CMD="$DEPLOY_CMD --region $REGION"
DEPLOY_CMD="$DEPLOY_CMD --service-name $SERVICE_NAME"

if [[ "$ENABLE_CODE_EXEC" == "true" ]]; then
    DEPLOY_CMD="$DEPLOY_CMD --enable-code-execution"
    DEPLOY_CMD="$DEPLOY_CMD --code-execution-ttl $STATE_TTL"
fi

if [[ "$ENABLE_MEMORY" == "true" ]]; then
    DEPLOY_CMD="$DEPLOY_CMD --enable-memory-bank"
    DEPLOY_CMD="$DEPLOY_CMD --max-memories $MAX_MEMORIES"
fi

# Deploy agent
echo ""
echo "Deploying agent..."
echo "Command: $DEPLOY_CMD"
echo ""

if eval "$DEPLOY_CMD"; then
    echo ""
    echo -e "${GREEN}✓ Agent deployed successfully!${NC}"

    # Get agent endpoint
    AGENT_URL=$(gcloud ai agents list \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --filter="displayName:$SERVICE_NAME" \
        --format="value(endpoint)" \
        --limit=1)

    if [[ -n "$AGENT_URL" ]]; then
        echo ""
        echo "Agent Endpoint: $AGENT_URL"
        echo "AgentCard: ${AGENT_URL}/.well-known/agent-card"
        echo "Task API: ${AGENT_URL}/v1/tasks:send"
        echo ""
        echo "Test with:"
        echo "  curl -X POST ${AGENT_URL}/v1/tasks:send \\"
        echo "    -H \"Authorization: Bearer \$(gcloud auth print-access-token)\" \\"
        echo "    -H \"Content-Type: application/json\" \\"
        echo "    -d '{\"message\": \"Hello from A2A protocol\"}'"
    fi

    # Save deployment info
    DEPLOY_INFO_FILE="${SERVICE_NAME}-deployment.json"
    cat > "$DEPLOY_INFO_FILE" <<DEPLOYMENT
{
  "agentName": "$SERVICE_NAME",
  "projectId": "$PROJECT_ID",
  "region": "$REGION",
  "agentFile": "$AGENT_FILE",
  "endpoint": "$AGENT_URL",
  "codeExecution": {
    "enabled": $ENABLE_CODE_EXEC,
    "stateTtl": "$STATE_TTL"
  },
  "memoryBank": {
    "enabled": $ENABLE_MEMORY,
    "maxMemories": $MAX_MEMORIES
  },
  "deployedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
DEPLOYMENT

    echo -e "${GREEN}Deployment info saved to: $DEPLOY_INFO_FILE${NC}"

else
    echo ""
    echo -e "${RED}✗ Deployment failed${NC}"
    echo "Check logs for details"
    exit 1
fi
