---
name: init-genkit-project
description: Initialize a new Firebase Genkit project with best practices, proper...
model: sonnet
---
# Initialize Genkit Project

Initialize a production-ready Firebase Genkit project with proper structure, configuration, and best practices.

## Step 1: Determine Project Language

Ask the user to choose the target language:
- **Node.js/TypeScript** (Genkit 1.0 - Stable, recommended for most use cases)
- **Python** (Alpha - Early adopters, Python ecosystem integration)
- **Go** (1.0 - High performance, backend services)

## Step 2: Initialize Project Structure

### For Node.js/TypeScript

```bash
# Create project directory
mkdir my-genkit-app && cd my-genkit-app

# Initialize npm project
npm init -y

# Install Genkit dependencies
npm install genkit @genkit-ai/googleai @genkit-ai/firebase zod

# Install dev dependencies
npm install --save-dev typescript @types/node

# Initialize TypeScript
npx tsc --init
```

Create `tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "node",
    "resolveJsonModule": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

Create `src/index.ts`:
```typescript
import { genkit, z } from 'genkit';
import { googleAI, gemini25Flash } from '@genkit-ai/googleai';
import { firebase } from '@genkit-ai/firebase';

const ai = genkit({
  plugins: [
    googleAI({
      apiKey: process.env.GOOGLE_API_KEY,
    }),
    firebase({
      projectId: process.env.GOOGLE_CLOUD_PROJECT,
    }),
  ],
  model: gemini25Flash,
  enableTracingAndMetrics: true,
});

// Example flow
const exampleFlow = ai.defineFlow(
  {
    name: 'exampleFlow',
    inputSchema: z.object({
      query: z.string(),
    }),
    outputSchema: z.object({
      response: z.string(),
    }),
  },
  async (input) => {
    const { text } = await ai.generate({
      model: gemini25Flash,
      prompt: `You are a helpful assistant. Respond to: ${input.query}`,
    });
    return { response: text };
  }
);

export { exampleFlow };
```

Create `package.json` scripts:
```json
{
  "scripts": {
    "dev": "genkit start -- tsx --watch src/index.ts",
    "build": "tsc",
    "deploy": "firebase deploy --only functions",
    "genkit:dev": "genkit start"
  }
}
```

### For Python

```bash
# Create project directory
mkdir my-genkit-app && cd my-genkit-app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Genkit
pip install genkit google-generativeai

# Create requirements.txt
pip freeze > requirements.txt
```

Create `main.py`:
```python
from genkit import genkit
from genkit.plugins import google_ai

ai = genkit(
    plugins=[
        google_ai.google_ai(api_key=os.environ.get("GOOGLE_API_KEY"))
    ],
    model="gemini-2.5-flash"
)

@ai.flow
async def example_flow(query: str) -> str:
    """Example Genkit flow."""
    response = await ai.generate(
        model="gemini-2.5-flash",
        prompt=f"You are a helpful assistant. Respond to: {query}"
    )
    return response.text

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(example_flow("Hello, Genkit!"))
    print(result)
```

### For Go

```bash
# Create project directory
mkdir my-genkit-app && cd my-genkit-app

# Initialize Go module
go mod init my-genkit-app

# Install Genkit
go get github.com/firebase/genkit/go/genkit
go get github.com/firebase/genkit/go/plugins/googleai
```

Create `main.go`:
```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"

    "github.com/firebase/genkit/go/genkit"
    "github.com/firebase/genkit/go/plugins/googleai"
)

func main() {
    ctx := context.Background()

    // Initialize Genkit with Google AI
    if err := genkit.Init(ctx, &genkit.Config{
        Plugins: []genkit.Plugin{
            googleai.Plugin(&googleai.Config{
                APIKey: os.Getenv("GOOGLE_API_KEY"),
            }),
        },
    }); err != nil {
        log.Fatal(err)
    }

    // Define a flow
    genkit.DefineFlow("exampleFlow", func(ctx context.Context, query string) (string, error) {
        response, err := genkit.Generate(ctx, &genkit.GenerateRequest{
            Model: googleai.Gemini25Flash,
            Prompt: genkit.Text(fmt.Sprintf("You are a helpful assistant. Respond to: %s", query)),
        })
        if err != nil {
            return "", err
        }
        return response.Text(), nil
    })

    // Start Genkit server
    if err := genkit.StartFlowServer(ctx, ""); err != nil {
        log.Fatal(err)
    }
}
```

## Step 3: Environment Configuration

Create `.env` file:
```bash
# Google API Key (for Google AI plugin)
GOOGLE_API_KEY=your_api_key_here

# Google Cloud Project (for Firebase/Vertex AI)
GOOGLE_CLOUD_PROJECT=your-project-id

# Environment
NODE_ENV=development
```

Create `.env.example` (committed to git):
```bash
GOOGLE_API_KEY=
GOOGLE_CLOUD_PROJECT=
NODE_ENV=development
```

## Step 4: Project Structure

Create recommended directory structure:

```
my-genkit-app/
├── src/                    # Source code
│   ├── flows/             # Flow definitions
│   ├── tools/             # Tool definitions
│   ├── retrievers/        # RAG retrievers
│   └── index.ts           # Main entry point
├── tests/                 # Test files
├── .env                   # Environment variables (gitignored)
├── .env.example           # Example env file (committed)
├── .gitignore             # Git ignore
├── tsconfig.json          # TypeScript config (for TS)
├── package.json           # Dependencies (for Node.js)
├── requirements.txt       # Dependencies (for Python)
├── go.mod                 # Dependencies (for Go)
└── README.md              # Project documentation
```

## Step 5: Configure Monitoring (Production)

For Firebase deployment with AI monitoring:

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase
firebase init

# Select:
# - Functions
# - Enable AI monitoring (when prompted)
```

Update `firebase.json`:
```json
{
  "functions": [
    {
      "source": ".",
      "codebase": "default",
      "runtime": "nodejs20",
      "ai": {
        "monitoring": {
          "enabled": true
        }
      }
    }
  ]
}
```

## Step 6: Local Development

Start Genkit Developer UI:

```bash
# Node.js
npm run genkit:dev

# Python
genkit start -- python main.py

# Go
genkit start -- go run .
```

Access UI at: `http://localhost:4000`

## Step 7: Testing

Create test file `tests/flows.test.ts`:
```typescript
import { describe, it, expect } from 'vitest';
import { exampleFlow } from '../src/index';

describe('exampleFlow', () => {
  it('should respond to queries', async () => {
    const result = await exampleFlow({ query: 'Hello!' });
    expect(result.response).toBeDefined();
    expect(result.response.length).toBeGreaterThan(0);
  });
});
```

## Best Practices Included

✅ **Environment Variables**: Secure API key management
✅ **TypeScript/Type Safety**: Strong typing for reliability
✅ **Monitoring**: AI monitoring enabled for production
✅ **Project Structure**: Organized codebase
✅ **Testing**: Test framework configured
✅ **Documentation**: README and code comments
✅ **Git**: Proper .gitignore configuration

## Next Steps

After initialization:
1. Review and customize the example flow
2. Add your specific business logic
3. Implement additional flows for your use case
4. Configure production deployment
5. Set up monitoring and alerting
6. Test thoroughly before deploying

## References

- Genkit Documentation: https://genkit.dev/
- Node.js Guide: https://genkit.dev/docs/get-started/
- Python Guide: https://firebase.blog/posts/2025/04/genkit-python-go/
- Go Guide: https://developers.googleblog.com/en/announcing-genkit-go-10/
