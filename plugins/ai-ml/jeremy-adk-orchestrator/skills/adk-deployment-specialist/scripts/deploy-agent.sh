#!/bin/bash
# deploy-agent.sh - Deploy ADK agent to Vertex AI Agent Engine
# Uses the Python SDK (vertexai.Client) since there is no gcloud CLI for Agent Engine.

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
AGENT_DIR="${1:-}"
PROJECT_ID="${2:-${GCP_PROJECT_ID:-}}"
REGION="${3:-us-central1}"
DISPLAY_NAME="${4:-}"

usage() {
    cat <<EOF
Usage: $0 <AGENT_DIR> [PROJECT_ID] [REGION] [DISPLAY_NAME]

Deploy ADK agent to Vertex AI Agent Engine using the Python SDK.

NOTE: There is no gcloud CLI for Agent Engine. This script uses the
vertexai Python SDK (vertexai.Client.agent_engines.create).

Arguments:
    AGENT_DIR     Directory containing agent code (must have agent.py)
    PROJECT_ID    GCP project ID (default: \$GCP_PROJECT_ID)
    REGION        GCP region (default: us-central1)
    DISPLAY_NAME  Agent display name (default: directory name)

Example:
    $0 ./my-agent my-project us-central1 my-agent
    GCP_PROJECT_ID=my-project $0 ./agent

Requirements:
    pip install google-adk>=1.15.1 google-cloud-aiplatform>=1.120.0

EOF
    exit 1
}

if [[ -z "$AGENT_DIR" ]]; then
    echo "Error: AGENT_DIR is required"
    usage
fi

if [[ ! -d "$AGENT_DIR" ]]; then
    echo -e "${RED}Error: Agent directory not found: $AGENT_DIR${NC}"
    exit 1
fi

if [[ -z "$PROJECT_ID" ]]; then
    echo "Error: PROJECT_ID is required (set GCP_PROJECT_ID env var or provide as argument)"
    usage
fi

# Default display name to directory basename
if [[ -z "$DISPLAY_NAME" ]]; then
    DISPLAY_NAME=$(basename "$AGENT_DIR")
fi

echo -e "${GREEN}Deploying ADK Agent to Vertex AI Agent Engine${NC}"
echo "Agent Dir: $AGENT_DIR"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Display Name: $DISPLAY_NAME"
echo ""

# Check Python SDK is installed
if ! python3 -c "import vertexai" 2>/dev/null; then
    echo -e "${YELLOW}Vertex AI SDK not found. Installing...${NC}"
    pip install 'google-cloud-aiplatform[agent_engines]>=1.120.0' 'google-adk>=1.15.1'
fi

# Validate agent files
echo "Validating agent directory..."
if [[ ! -f "$AGENT_DIR/agent.py" ]]; then
    echo -e "${RED}Error: agent.py not found in $AGENT_DIR${NC}"
    exit 1
fi

if ! python3 -m py_compile "$AGENT_DIR/agent.py"; then
    echo -e "${RED}Error: agent.py has syntax errors${NC}"
    exit 1
fi
echo -e "${GREEN}Agent files valid${NC}"

# Check for requirements.txt
REQUIREMENTS_FILE="$AGENT_DIR/requirements.txt"
if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
    echo -e "${YELLOW}Warning: No requirements.txt found. Using default ADK dependencies.${NC}"
fi

# Deploy using Python SDK
echo ""
echo "Deploying agent via vertexai.Client.agent_engines.create()..."
echo ""

python3 -c "
import sys
sys.path.insert(0, '${AGENT_DIR}')

import vertexai

# Import the agent from the agent directory
from agent import root_agent

# Initialize client
client = vertexai.Client(project='${PROJECT_ID}', location='${REGION}')

# Read requirements if available
requirements = ['google-adk>=1.15.1']
try:
    with open('${REQUIREMENTS_FILE}', 'r') as f:
        requirements = [
            line.strip() for line in f
            if line.strip() and not line.startswith('#')
        ]
except FileNotFoundError:
    pass

# Deploy to Agent Engine
print('Creating reasoning engine...')
remote_agent = client.agent_engines.create(
    agent_engine=root_agent,
    requirements=requirements,
    display_name='${DISPLAY_NAME}',
)

print()
print('Agent deployed successfully!')
print(f'Resource Name: {remote_agent.resource_name}')
print()
print('To query this agent:')
print(f\"  python3 -c \\\"import vertexai; c = vertexai.Client(project='{PROJECT_ID}', location='{REGION}'); a = c.agent_engines.get(name='{{}}'.format(remote_agent.resource_name)); print(a.query(input='Hello'))\\\"\")
print()
print('To list all agents:')
print(f\"  python3 -c \\\"import vertexai; c = vertexai.Client(project='{PROJECT_ID}', location='{REGION}'); [print(a.display_name, a.resource_name) for a in c.agent_engines.list()]\\\"\")
"

DEPLOY_STATUS=$?

if [[ $DEPLOY_STATUS -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}Deployment complete${NC}"
else
    echo ""
    echo -e "${RED}Deployment failed (exit code: $DEPLOY_STATUS)${NC}"
    echo "Check logs for details. Common issues:"
    echo "  - Missing IAM roles (need roles/aiplatform.admin)"
    echo "  - Quota exceeded (default: 10 reasoning engines per project)"
    echo "  - Invalid agent definition (check tool function signatures)"
    exit 1
fi
