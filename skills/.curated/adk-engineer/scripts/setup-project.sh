#!/bin/bash
# setup-project.sh - Setup ADK agent development project

set -euo pipefail

PROJECT_NAME="${1:-adk-agent-project}"
LANGUAGE="${2:-python}"

echo "Setting up ADK Agent Development Project"
echo "Name: $PROJECT_NAME"
echo "Language: $LANGUAGE"
echo ""

mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

if [[ "$LANGUAGE" == "python" ]]; then
    # Python project structure
    mkdir -p src/{agents,tools,orchestrators,config,utils}
    mkdir -p tests/{unit,integration,e2e}
    mkdir -p deployment/{terraform,kubernetes}
    mkdir -p .github/workflows

    # Create __init__.py files
    touch src/__init__.py
    touch src/agents/__init__.py
    touch src/tools/__init__.py
    touch src/orchestrators/__init__.py
    touch src/config/__init__.py
    touch src/utils/__init__.py

    # Create requirements.txt
    cat > requirements.txt <<'EOF'
google-adk>=0.1.0
google-cloud-aiplatform>=1.40.0
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
mypy>=1.0.0
EOF

    # Create pyproject.toml
    cat > pyproject.toml <<EOF
[project]
name = "$PROJECT_NAME"
version = "1.0.0"
description = "ADK Agent Application"
requires-python = ">=3.11"
dependencies = [
    "google-adk>=0.1.0",
    "google-cloud-aiplatform>=1.40.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "mypy>=1.0.0"
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
EOF

    # Create README.md
    cat > README.md <<EOF
# $PROJECT_NAME

ADK Agent Application

## Setup

\`\`\`bash
pip install -r requirements.txt
\`\`\`

## Run

\`\`\`bash
python -m src.agents.main_agent
\`\`\`

## Test

\`\`\`bash
pytest tests/
\`\`\`
EOF

    echo "✓ Python project created"

elif [[ "$LANGUAGE" == "go" ]]; then
    # Go project structure
    mkdir -p cmd/{agent,cli}
    mkdir -p pkg/{agents,tools,config}
    mkdir -p internal/{handlers,middleware}
    mkdir -p deployments

    # Create go.mod
    cat > go.mod <<EOF
module github.com/yourusername/$PROJECT_NAME

go 1.21

require (
    google.golang.org/adk v0.1.0
)
EOF

    echo "✓ Go project created"
fi

echo ""
echo "Project created: $PROJECT_NAME/"
echo "Next steps:"
echo "  cd $PROJECT_NAME"
echo "  pip install -r requirements.txt  # Python"
echo "  go mod tidy                      # Go"
