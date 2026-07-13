# Examples — GCP Starter Examples

## Example 1: ADK Agent with Code Execution and Memory Bank

Create a production ADK agent deployed to Vertex AI Agent Engine.

### Project Setup

```bash
# Install ADK CLI and dependencies
pip install google-adk google-cloud-aiplatform

# Authenticate
gcloud auth application-default login
gcloud config set project my-gcp-project
gcloud services enable aiplatform.googleapis.com
```

### Agent Implementation

```python
# agent.py
from google.adk.agents import Agent
from google.adk.tools import CodeExecution, MemoryBank

# Define the agent with Code Execution Sandbox and Memory Bank
agent = Agent(
    model="gemini-2.5-flash",
    name="data-analyst",
    description="Analyzes datasets using code execution with persistent memory",
    system_instruction="""You are a data analyst agent.

CAPABILITIES:
- Execute Python code in a secure sandbox to analyze data
- Remember previous analyses and user preferences via Memory Bank
- Generate visualizations and statistical summaries

WORKFLOW:
1. Understand the user's data question
2. Check Memory Bank for relevant context from prior sessions
3. Write and execute Python code to analyze the data
4. Store key findings in Memory Bank for future reference
5. Return clear, actionable insights with visualizations

CONSTRAINTS:
- Always validate data before analysis
- Use pandas for tabular data, matplotlib/seaborn for plots
- Cap output to 20 rows for large datasets
- Store analysis summaries, not raw data, in Memory Bank
""",
    tools=[
        CodeExecution(
            sandbox_type="SECURE_ISOLATED",
            state_ttl_days=14,
        ),
        MemoryBank(
            enabled=True,
            retention_count=100,
        ),
    ],
)

# Local testing
if __name__ == "__main__":
    response = agent.run("Analyze the sales trends in Q4 from sales_data.csv")
    print(response.text)
```

### Deployment to Agent Engine

```bash
# Deploy to Vertex AI Agent Engine
adk deploy \
  --agent-file agent.py \
  --project-id my-gcp-project \
  --region us-central1 \
  --service-name data-analyst-agent \
  --min-instances 1 \
  --max-instances 5

# Verify deployment
gcloud run services list --project=my-gcp-project --region=us-central1
```

### Expected Output

```
Deploying agent 'data-analyst' to us-central1...
Agent deployed successfully.
  Name: projects/my-gcp-project/locations/us-central1/agents/data-analyst-agent
  Endpoint: https://us-central1-my-gcp-project.agent.vertexai.goog
  Status: ACTIVE
  Model: gemini-2.5-flash
  Tools: CodeExecution (SECURE_ISOLATED, 14d TTL), MemoryBank (100 memories)
```

---

## Example 2: Genkit RAG Flow with Firestore Vector Search

Build a retrieval-augmented generation system deployed to Cloud Run.

### Project Initialization

```bash
mkdir genkit-rag && cd genkit-rag
npm init -y
npm install genkit @genkit-ai/googleai @genkit-ai/firebase zod
npm install -D typescript @types/node tsx
```

### Flow Implementation

```typescript
// src/rag-flow.ts
import { genkit, z } from "genkit";
import { googleAI, gemini25Flash, textEmbedding004 } from "@genkit-ai/googleai";

const ai = genkit({
  plugins: [googleAI()],
});

// Define input/output schemas
const QuerySchema = z.object({
  question: z.string().min(1).describe("The user's question"),
  maxResults: z.number().min(1).max(20).default(5),
});

const AnswerSchema = z.object({
  answer: z.string(),
  sources: z.array(z.object({
    title: z.string(),
    snippet: z.string(),
    relevanceScore: z.number(),
  })),
  tokenUsage: z.object({
    prompt: z.number(),
    completion: z.number(),
  }),
});

// Define the retriever using text-embedding-004
const docRetriever = ai.defineRetriever(
  { name: "firestore-docs" },
  async (query: string, options?: { k?: number }) => {
    const k = options?.k ?? 5;

    // Generate embedding for the query
    const { embedding } = await ai.embed({
      embedder: textEmbedding004,
      content: query,
    });

    // Query Firestore vector index (using Admin SDK)
    const { Firestore } = await import("firebase-admin/firestore");
    const db = new Firestore();
    const snapshot = await db
      .collection("documents")
      .findNearest("embedding", embedding, { limit: k, distanceMeasure: "COSINE" })
      .get();

    return snapshot.docs.map((doc) => ({
      content: doc.data().content as string,
      metadata: {
        title: doc.data().title as string,
        source: doc.id,
        score: doc.data().score as number,
      },
    }));
  }
);

// Define the RAG flow
export const ragFlow = ai.defineFlow(
  {
    name: "rag-query",
    inputSchema: QuerySchema,
    outputSchema: AnswerSchema,
  },
  async (input) => {
    // Step 1: Retrieve relevant documents
    const docs = await ai.retrieve({
      retriever: docRetriever,
      query: input.question,
      options: { k: input.maxResults },
    });

    // Step 2: Build context from retrieved docs
    const context = docs
      .map((d, i) => `[${i + 1}] ${d.metadata?.title}: ${d.content}`)
      .join("\n\n");

    // Step 3: Generate grounded answer
    const { text, usage } = await ai.generate({
      model: gemini25Flash,
      prompt: `Answer the question using ONLY the provided context. Cite sources by number.

Context:
${context}

Question: ${input.question}

If the context doesn't contain enough information, say so clearly.`,
      config: { temperature: 0.3, maxOutputTokens: 1024 },
    });

    return {
      answer: text,
      sources: docs.map((d, i) => ({
        title: d.metadata?.title ?? `Source ${i + 1}`,
        snippet: d.content.substring(0, 200),
        relevanceScore: d.metadata?.score ?? 0,
      })),
      tokenUsage: {
        prompt: usage?.inputTokens ?? 0,
        completion: usage?.outputTokens ?? 0,
      },
    };
  }
);

// Start the Genkit server for local development and Cloud Run
ai.startFlowServer({ flows: [ragFlow] });
```

### Deployment to Cloud Run

```bash
# Build and deploy
gcloud run deploy genkit-rag \
  --source . \
  --region us-central1 \
  --memory 512Mi \
  --min-instances 2 \
  --max-instances 10 \
  --set-env-vars "GOOGLE_GENAI_API_KEY=$(gcloud secrets versions access latest --secret=genai-api-key)" \
  --allow-unauthenticated

# Test the deployed endpoint
curl -X POST https://genkit-rag-abc123-uc.a.run.app/rag-query \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I configure VPC Service Controls?", "maxResults": 3}'
```

### Expected Output

```json
{
  "answer": "To configure VPC Service Controls, follow these steps:\n\n1. Create a service perimeter in the Access Context Manager [1]\n2. Add your GCP project to the perimeter [2]\n3. Configure restricted services (e.g., aiplatform.googleapis.com) [1]\n4. Set up access levels for authorized identities [3]\n\nNote: Changes can take up to 30 minutes to propagate.",
  "sources": [
    {
      "title": "VPC-SC Setup Guide",
      "snippet": "VPC Service Controls create security perimeters around GCP resources...",
      "relevanceScore": 0.94
    },
    {
      "title": "Project Security Baseline",
      "snippet": "Every production project should be added to a VPC-SC perimeter...",
      "relevanceScore": 0.89
    },
    {
      "title": "Access Context Manager",
      "snippet": "Access levels define conditions under which access is granted...",
      "relevanceScore": 0.82
    }
  ],
  "tokenUsage": {
    "prompt": 1240,
    "completion": 185
  }
}
```

---

## Example 3: Gemini Multimodal Video Analysis

Analyze video content using Gemini 2.5 Pro with structured output.

```python
# video_analyzer.py
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting
import json

vertexai.init(project="my-gcp-project", location="us-central1")

model = GenerativeModel(
    "gemini-2.5-pro",
    generation_config={
        "temperature": 0.2,
        "max_output_tokens": 2048,
        "response_mime_type": "application/json",
    },
    safety_settings=[
        SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="BLOCK_ONLY_HIGH",
        ),
    ],
)

def analyze_video(video_uri: str, questions: list[str]) -> dict:
    """Analyze a video stored in GCS with specific questions."""

    video_part = Part.from_uri(video_uri, mime_type="video/mp4")

    prompt = f"""Analyze this video and answer the following questions.
Return a JSON object with this structure:
{{
  "duration_estimate": "estimated video duration",
  "scene_count": number,
  "answers": [
    {{"question": "...", "answer": "...", "confidence": 0.0-1.0, "timestamp": "MM:SS"}}
  ],
  "key_objects": ["list of notable objects/people/text seen"],
  "overall_summary": "2-3 sentence summary"
}}

Questions:
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(questions))}
"""

    response = model.generate_content([video_part, prompt])

    # Parse structured JSON output
    result = json.loads(response.text)

    # Add token usage for cost tracking
    result["usage"] = {
        "prompt_tokens": response.usage_metadata.prompt_token_count,
        "completion_tokens": response.usage_metadata.candidates_token_count,
        "estimated_cost_usd": (
            response.usage_metadata.prompt_token_count * 0.00000125
            + response.usage_metadata.candidates_token_count * 0.000005
        ),
    }

    return result


# Usage
result = analyze_video(
    video_uri="gs://my-bucket/product-demo.mp4",
    questions=[
        "What product is being demonstrated?",
        "How many people appear in the video?",
        "What is the main call to action?",
    ],
)

print(json.dumps(result, indent=2))
```

### Expected Output

```json
{
  "duration_estimate": "2 minutes 34 seconds",
  "scene_count": 5,
  "answers": [
    {
      "question": "What product is being demonstrated?",
      "answer": "A cloud-based project management tool with Kanban boards and time tracking",
      "confidence": 0.95,
      "timestamp": "00:15"
    },
    {
      "question": "How many people appear in the video?",
      "answer": "Two people: a presenter and a user demonstrating the interface",
      "confidence": 0.88,
      "timestamp": "00:05"
    },
    {
      "question": "What is the main call to action?",
      "answer": "Sign up for a free 14-day trial at the URL shown at 02:28",
      "confidence": 0.92,
      "timestamp": "02:28"
    }
  ],
  "key_objects": ["laptop", "Kanban board UI", "company logo", "pricing table", "QR code"],
  "overall_summary": "A product demo video showcasing a cloud project management tool. The presenter walks through Kanban board features, time tracking, and team collaboration tools before closing with a free trial offer.",
  "usage": {
    "prompt_tokens": 48200,
    "completion_tokens": 312,
    "estimated_cost_usd": 0.0619
  }
}
```

---

## Example 4: Terraform Module for Agent Engine Deployment

Infrastructure-as-code for reproducible agent deployments.

```hcl
# main.tf — Vertex AI Agent Engine with VPC-SC and monitoring
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" { type = string }
variable "region" { default = "us-central1" }
variable "agent_name" { type = string }

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "secretmanager.googleapis.com",
  ])
  project = var.project_id
  service = each.value
}

# Least-privilege service account
resource "google_service_account" "agent_sa" {
  account_id   = "${var.agent_name}-sa"
  display_name = "Agent Engine SA for ${var.agent_name}"
  project      = var.project_id
}

resource "google_project_iam_member" "agent_roles" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Monitoring alert for error rate > 5%
resource "google_monitoring_alert_policy" "agent_errors" {
  display_name = "${var.agent_name} Error Rate"
  project      = var.project_id

  conditions {
    display_name = "Error rate exceeds 5%"
    condition_threshold {
      filter          = "resource.type=\"aiplatform.googleapis.com/Agent\" AND metric.type=\"aiplatform.googleapis.com/agent/error_count\""
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      duration        = "300s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = []  # Add your notification channel IDs
}

output "service_account_email" {
  value = google_service_account.agent_sa.email
}
```

```bash
# Deploy
terraform init
terraform plan -var="project_id=my-gcp-project" -var="agent_name=data-analyst"
terraform apply -auto-approve -var="project_id=my-gcp-project" -var="agent_name=data-analyst"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
