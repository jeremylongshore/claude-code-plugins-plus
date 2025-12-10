#!/bin/bash
# init-genkit.sh - Initialize Firebase Genkit project

set -euo pipefail

PROJECT_NAME="${1:-my-genkit-app}"
RUNTIME="${2:-nodejs}"

echo "Initializing Firebase Genkit Project"
echo "Name: $PROJECT_NAME"
echo "Runtime: $RUNTIME"
echo ""

mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

if [[ "$RUNTIME" == "nodejs" ]]; then
    # Initialize Node.js project
    npm init -y
    npm install genkit @genkit-ai/googleai @genkit-ai/vertexai

    # Create basic flow
    cat > src/index.ts <<'EOF'
import { genkit } from 'genkit';
import { googleAI } from '@genkit-ai/googleai';

const ai = genkit({
  plugins: [googleAI()],
  model: 'googleai/gemini-2.0-flash',
});

export const greetingFlow = ai.defineFlow('greeting', async (name: string) => {
  const response = await ai.generate({
    prompt: `Say hello to ${name}`,
  });
  return response.text;
});
EOF

    cat > package.json <<'EOF'
{
  "name": "genkit-app",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "genkit start",
    "build": "tsc",
    "deploy": "gcloud run deploy"
  }
}
EOF

elif [[ "$RUNTIME" == "python" ]]; then
    # Initialize Python project
    pip install firebase-genkit

    cat > main.py <<'EOF'
from genkit import genkit
from genkit.googleai import GoogleAI

ai = genkit(
    plugins=[GoogleAI()],
    model='googleai/gemini-2.0-flash'
)

@ai.flow
def greeting(name: str) -> str:
    response = ai.generate(prompt=f"Say hello to {name}")
    return response.text
EOF
fi

echo "✓ Genkit project initialized"
echo ""
echo "Next steps:"
echo "  cd $PROJECT_NAME"
echo "  genkit start  # Start dev UI"
