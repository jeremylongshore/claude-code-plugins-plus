---
name: vertex-agent-builder
description: |
  Build and deploy production-ready generative AI agents using Vertex AI, Gemini models, and Google Cloud infrastructure with RAG, function calling, and multi-modal capabilities. Use when appropriate context detected. Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Vertex AI Agent Builder Skill



This skill provides automated assistance for vertex agent builder tasks.

## Prerequisites

- Appropriate file access permissions
- Required dependencies installed

## Instructions

1. Invoke this skill when the trigger conditions are met
2. Provide necessary context and parameters
3. Review the generated output
4. Apply modifications as needed

## Output

The skill produces structured output relevant to the task.

## Error Handling

- Invalid input: Prompts for correction
- Missing dependencies: Lists required components
- Permission errors: Suggests remediation steps
## Overview


This skill provides automated assistance for vertex agent builder tasks.
This skill provides production-ready scaffolding and deployment for generative AI agents using Google Cloud's Vertex AI platform. Built on actual Google Cloud source code from `GoogleCloudPlatform/generative-ai` and `agent-starter-pack` repositories, it offers:

- **Gemini Model Integration** (1.5 Pro, 1.5 Flash, experimental models)
- **Multi-modal Capabilities** (text, image, video, audio processing)
- **RAG Implementation** (Retrieval Augmented Generation with Vector Search)
- **Function Calling** (Tool use with Gemini models)
- **Production Deployment** (Cloud Run, Vertex AI Endpoints)
- **Evaluation Framework** (AutoSxS, ROUGE, custom metrics)
- **Observability** (Cloud Logging, Monitoring, Trace)

## Installation

```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Install Python SDK
pip install google-cloud-aiplatform>=1.38.0
pip install vertexai>=1.46.0
pip install google-generativeai>=0.3.2

# Clone source repositories
git clone https://github.com/GoogleCloudPlatform/generative-ai.git
git clone https://github.com/GoogleCloudPlatform/agent-starter-pack.git
git clone https://github.com/GoogleCloudPlatform/vertex-ai-samples.git

# Install this plugin
/plugin install jeremy-vertex-ai@jeremylongshore
```

## Quick Start (5 Minutes)

### Create Your First Vertex AI Agent

```python
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
from vertexai.preview.generative_models import grounding

# Initialize Vertex AI
vertexai.init(project="your-project-id", location="us-central1")

# Create Gemini model
model = GenerativeModel(
    "gemini-1.5-pro-002",
    system_instruction="""You are a helpful AI assistant that can:
    - Search the web for information
    - Analyze documents and images
    - Execute Python code
    - Call external APIs
    """
)

# Start chat session
chat = model.start_chat()

# Send message with grounding
response = chat.send_message(
    "What are the latest developments in quantum computing?",
    generation_config={
        "temperature": 0.3,
        "max_output_tokens": 2048,
        "top_p": 0.95,
    },
    safety_settings={
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
    },
    tools=[grounding.Tool(google_search_retrieval=grounding.GoogleSearchRetrieval())]
)

print(response.text)
```

## Agent Patterns

### 1. Production Agent with Agent Builder

Based on `GoogleCloudPlatform/agent-starter-pack`:

```python
from vertexai.preview import agents
from vertexai.preview.generative_models import Tool, FunctionDeclaration
import functions_framework

class ProductionAgent:
    """
    Production-ready agent using Vertex AI Agent Builder
    """

    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location

        # Initialize agent
        self.agent = agents.Agent.create(
            project=project_id,
            location=location,
            display_name="production-agent",
            description="Production-ready agent with tools and RAG",
            model="gemini-1.5-pro-002",
            tools=self._create_tools(),
            system_instruction=self._get_system_instruction()
        )

    def _create_tools(self):
        """Create function calling tools"""
        return [
            Tool(function_declarations=[
                FunctionDeclaration(
                    name="search_knowledge_base",
                    description="Search internal knowledge base",
                    parameters={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "top_k": {"type": "integer", "default": 5}
                        }
                    }
                ),
                FunctionDeclaration(
                    name="execute_sql",
                    description="Execute SQL query on BigQuery",
                    parameters={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "dataset": {"type": "string"}
                        }
                    }
                ),
                FunctionDeclaration(
                    name="send_email",
                    description="Send email notification",
                    parameters={
                        "type": "object",
                        "properties": {
                            "to": {"type": "string"},
                            "subject": {"type": "string"},
                            "body": {"type": "string"}
                        }
                    }
                )
            ])
        ]

    def _get_system_instruction(self):
        """Get system instruction for agent"""
        return """You are a production AI agent that helps users with:
        1. Information retrieval from knowledge bases
        2. Data analysis using BigQuery
        3. Automated communications

        Always verify user intent before executing critical operations.
        Provide clear explanations of what you're doing and why.
        """

    async def process_request(self, user_input: str):
        """Process user request"""
        session = self.agent.start_session()
        response = await session.send_message(user_input)

        # Handle function calls
        if response.function_calls:
            for func_call in response.function_calls:
                result = await self._execute_function(
                    func_call.name,
                    func_call.args
                )
                # Send function result back to model
                response = await session.send_message(
                    content=None,
                    function_responses=[{
                        "name": func_call.name,
                        "response": result
                    }]
                )

        return response.text

    async def _execute_function(self, name: str, args: dict):
        """Execute function call"""
        if name == "search_knowledge_base":
            return await self._search_kb(args["query"], args.get("top_k", 5))
        elif name == "execute_sql":
            return await self._execute_bigquery(args["query"], args["dataset"])
        elif name == "send_email":
            return await self._send_email(args["to"], args["subject"], args["body"])

# Deploy as Cloud Function
@functions_framework.http
def agent_endpoint(request):
    """HTTP Cloud Function for agent"""
    agent = ProductionAgent(
        project_id="your-project",
        location="us-central1"
    )

    request_json = request.get_json()
    response = agent.process_request(request_json["message"])

    return {"response": response}
```

### 2. RAG-Enhanced Agent

Based on `GoogleCloudPlatform/generative-ai/gemini/use-cases/retrieval-augmented-generation`:

```python
from vertexai.language_models import TextEmbeddingModel
from vertexai.preview import rag
from google.cloud import aiplatform

class RAGAgent:
    """
    Agent with Retrieval Augmented Generation using Vertex AI Search
    """

    def __init__(self, project_id: str, corpus_name: str):
        self.project_id = project_id

        # Create RAG corpus
        self.corpus = rag.create_corpus(
            display_name=corpus_name,
            description="Knowledge base for RAG"
        )

        # Initialize embedding model
        self.embedding_model = TextEmbeddingModel.from_pretrained(
            "text-embedding-004"
        )

        # Initialize Gemini model
        self.model = GenerativeModel("gemini-1.5-pro-002")

    async def import_documents(self, gcs_uris: list):
        """Import documents into RAG corpus"""
        import_job = rag.import_files(
            corpus_name=self.corpus.name,
            gcs_uris=gcs_uris,
            chunk_size=512,
            chunk_overlap=100
        )

        # Wait for import to complete
        import_job.wait()

        return import_job

    async def query_with_rag(self, query: str, similarity_top_k: int = 5):
        """Query with RAG retrieval"""

        # Retrieve relevant chunks
        retrieval_response = rag.retrieval_query(
            rag_resources=[
                rag.RagResource(
                    rag_corpus=self.corpus.name,
                    similarity_top_k=similarity_top_k
                )
            ],
            query=query
        )

        # Build context from retrieved chunks
        context = "\n\n".join([
            f"Source: {chunk.source}\nContent: {chunk.text}"
            for chunk in retrieval_response.contexts
        ])

        # Generate response with context
        prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {query}

Answer:"""

        response = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 1024,
            }
        )

        return {
            "answer": response.text,
            "sources": [chunk.source for chunk in retrieval_response.contexts],
            "confidence": retrieval_response.attribution_score
        }
```

### 3. Multi-Modal Agent

Based on `GoogleCloudPlatform/generative-ai/gemini/multimodality`:

```python
from vertexai.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models

class MultiModalAgent:
    """
    Agent that processes text, images, video, and audio
    """

    def __init__(self):
        self.model = GenerativeModel("gemini-1.5-flash-002")

    async def analyze_image(self, image_path: str, prompt: str):
        """Analyze image with text prompt"""
        image = Part.from_uri(
            uri=f"gs://your-bucket/{image_path}",
            mime_type="image/jpeg"
        )

        response = self.model.generate_content([prompt, image])
        return response.text

    async def analyze_video(self, video_path: str, prompt: str):
        """Analyze video content"""
        video = Part.from_uri(
            uri=f"gs://your-bucket/{video_path}",
            mime_type="video/mp4"
        )

        response = self.model.generate_content(
            [prompt, video],
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 2048,
            }
        )
        return response.text

    async def analyze_document(self, pdf_path: str):
        """Extract and analyze PDF document"""
        document = Part.from_uri(
            uri=f"gs://your-bucket/{pdf_path}",
            mime_type="application/pdf"
        )

        prompt = """Extract all key information from this document:
        1. Main topics covered
        2. Key findings or conclusions
        3. Important data or statistics
        4. Actionable recommendations
        """

        response = self.model.generate_content([prompt, document])
        return response.text

    async def generate_code(self, description: str, language: str = "python"):
        """Generate code from natural language"""
        prompt = f"""Generate {language} code for the following requirement:
        {description}

        Requirements:
        - Include proper error handling
        - Add comprehensive comments
        - Follow best practices for {language}
        - Make it production-ready
        """

        response = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 4096,
            }
        )
        return response.text
```

## Deployment Patterns

### 1. Cloud Run Deployment

```yaml
# cloudbuild.yaml
steps:
  # Build container
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/vertex-agent:$COMMIT_SHA', '.']

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/vertex-agent:$COMMIT_SHA']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'vertex-agent'
      - '--image'
      - 'gcr.io/$PROJECT_ID/vertex-agent:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--set-env-vars'
      - 'GCP_PROJECT=$PROJECT_ID'
```

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run as non-root user
RUN useradd -m -u 1000 agent && chown -R agent:agent /app
USER agent

EXPOSE 8080

CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "8", "--timeout", "0", "main:app"]
```

### 2. Vertex AI Endpoint Deployment

```python
from google.cloud import aiplatform

def deploy_to_vertex_endpoint():
    """Deploy model to Vertex AI Endpoint"""

    aiplatform.init(project="your-project", location="us-central1")

    # Upload model
    model = aiplatform.Model.upload(
        display_name="vertex-agent-model",
        artifact_uri="gs://your-bucket/model",
        serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-3:latest"
    )

    # Create endpoint
    endpoint = aiplatform.Endpoint.create(
        display_name="vertex-agent-endpoint",
    )

    # Deploy model to endpoint
    endpoint.deploy(
        model=model,
        deployed_model_display_name="vertex-agent-v1",
        machine_type="n1-standard-4",
        min_replica_count=1,
        max_replica_count=5,
        accelerator_type="NVIDIA_TESLA_T4",
        accelerator_count=1,
    )

    return endpoint
```

## Evaluation Framework

Based on `GoogleCloudPlatform/generative-ai/gemini/evaluation`:

```python
from vertexai.preview.evaluation import EvalTask, MetricPromptTemplate
import pandas as pd

class AgentEvaluator:
    """
    Evaluate agent performance using Vertex AI evaluation framework
    """

    def __init__(self):
        self.eval_dataset = self._load_eval_dataset()

    def _load_eval_dataset(self):
        """Load evaluation dataset"""
        return pd.DataFrame([
            {
                "prompt": "What is the capital of France?",
                "reference": "The capital of France is Paris.",
                "context": "France is a country in Western Europe."
            },
            # Add more test cases
        ])

    async def evaluate_accuracy(self, agent):
        """Evaluate agent accuracy"""
        eval_task = EvalTask(
            dataset=self.eval_dataset,
            metrics=[
                "rouge_l_sum",
                "bleu",
                "exact_match",
                MetricPromptTemplate(
                    metric="custom_factuality",
                    metric_prompt_template="""Rate the factual accuracy of the response.
                    Reference: {reference}
                    Response: {response}
                    Score (0-1):"""
                )
            ]
        )

        # Run evaluation
        results = []
        for _, row in self.eval_dataset.iterrows():
            response = await agent.process_request(row["prompt"])
            results.append({
                "prompt": row["prompt"],
                "reference": row["reference"],
                "response": response
            })

        eval_result = eval_task.evaluate(
            model=agent.model,
            response_column="response"
        )

        return eval_result.summary_metrics
```

## Monitoring & Observability

```python
from google.cloud import monitoring_v3
from google.cloud import logging
import time

class AgentMonitor:
    """
    Monitor agent performance and usage
    """

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.logging_client = logging.Client()
        self.logger = self.logging_client.logger("vertex-agent")

    def log_request(self, request_id: str, user_input: str, response: str, latency: float):
        """Log agent request"""
        self.logger.log_struct({
            "request_id": request_id,
            "timestamp": time.time(),
            "user_input": user_input,
            "response": response[:500],  # Truncate long responses
            "latency_ms": latency * 1000,
            "model": "gemini-1.5-pro-002",
            "success": True
        })

    def create_custom_metric(self, metric_name: str, value: float):
        """Create custom metric in Cloud Monitoring"""
        project_name = f"projects/{self.project_id}"

        series = monitoring_v3.TimeSeries()
        series.metric.type = f"custom.googleapis.com/agent/{metric_name}"

        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10 ** 9)
        interval = monitoring_v3.TimeInterval(
            {"end_time": {"seconds": seconds, "nanos": nanos}}
        )
        point = monitoring_v3.Point({
            "interval": interval,
            "value": {"double_value": value}
        })
        series.points = [point]

        self.monitoring_client.create_time_series(
            name=project_name,
            time_series=[series]
        )

    def create_dashboard(self):
        """Create monitoring dashboard"""
        # Dashboard configuration
        dashboard_config = {
            "displayName": "Vertex Agent Dashboard",
            "widgets": [
                {
                    "title": "Request Latency",
                    "xyChart": {
                        "dataSets": [{
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": 'metric.type="custom.googleapis.com/agent/latency"'
                                }
                            }
                        }]
                    }
                },
                {
                    "title": "Error Rate",
                    "xyChart": {
                        "dataSets": [{
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": 'metric.type="custom.googleapis.com/agent/errors"'
                                }
                            }
                        }]
                    }
                }
            ]
        }
        return dashboard_config
```

## Cost Optimization

```python
class CostOptimizedAgent:
    """
    Cost-optimized agent configuration
    """

    def __init__(self):
        # Model selection based on task complexity
        self.models = {
            "simple": "gemini-1.5-flash-002",  # Fastest and cheapest
            "standard": "gemini-1.5-pro-002",   # Balanced
            "complex": "gemini-1.5-pro-002",    # Most capable
        }

        # Caching for repeated queries
        self.response_cache = {}

    def select_model(self, query: str) -> str:
        """Select appropriate model based on query complexity"""
        # Simple heuristic based on query length and keywords
        complexity_score = len(query) / 100

        if "analyze" in query or "explain" in query:
            complexity_score += 0.3
        if "code" in query or "implement" in query:
            complexity_score += 0.4

        if complexity_score < 0.3:
            return self.models["simple"]
        elif complexity_score < 0.7:
            return self.models["standard"]
        else:
            return self.models["complex"]

    async def process_with_caching(self, query: str):
        """Process query with response caching"""
        # Check cache first
        cache_key = hashlib.md5(query.encode()).hexdigest()
        if cache_key in self.response_cache:
            return self.response_cache[cache_key]

        # Select optimal model
        model_name = self.select_model(query)
        model = GenerativeModel(model_name)

        # Process query
        response = model.generate_content(
            query,
            generation_config={
                "temperature": 0.1,  # Lower temperature for consistency
                "max_output_tokens": 1024,  # Limit output size
            }
        )

        # Cache response
        self.response_cache[cache_key] = response.text

        return response.text
```

## Integration with Google Cloud Services

### BigQuery Integration

```python
from google.cloud import bigquery

class BigQueryAgent:
    """Agent with BigQuery data access"""

    def __init__(self, project_id: str):
        self.bq_client = bigquery.Client(project=project_id)
        self.model = GenerativeModel("gemini-1.5-pro-002")

    async def nl2sql(self, natural_language_query: str, dataset: str):
        """Convert natural language to SQL"""

        # Get table schemas
        tables = self.bq_client.list_tables(dataset)
        schema_info = []
        for table in tables:
            table_ref = self.bq_client.get_table(table.reference)
            schema_info.append(f"Table: {table.table_id}\nSchema: {table_ref.schema}")

        prompt = f"""Convert this natural language query to SQL:
        Query: {natural_language_query}

        Available tables and schemas:
        {chr(10).join(schema_info)}

        Return only the SQL query, no explanation.
        """

        response = self.model.generate_content(prompt)
        sql_query = response.text.strip()

        # Execute query
        query_job = self.bq_client.query(sql_query)
        results = query_job.result()

        return {
            "sql": sql_query,
            "results": [dict(row) for row in results],
            "total_rows": results.total_rows
        }
```

### Cloud Storage Integration

```python
from google.cloud import storage

class StorageAgent:
    """Agent with Cloud Storage access"""

    def __init__(self, bucket_name: str):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)

    async def process_documents(self, prefix: str):
        """Process all documents in a GCS prefix"""
        blobs = self.bucket.list_blobs(prefix=prefix)

        results = []
        for blob in blobs:
            if blob.name.endswith(('.pdf', '.txt', '.docx')):
                # Download and process
                content = blob.download_as_text()
                analysis = await self.analyze_document(content)
                results.append({
                    "file": blob.name,
                    "analysis": analysis
                })

        return results
```

## Best Practices

### 1. Security

```python
from google.cloud import secretmanager

class SecureAgent:
    """Agent with security best practices"""

    def __init__(self, project_id: str):
        self.secret_client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id

    def get_secret(self, secret_id: str) -> str:
        """Get secret from Secret Manager"""
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
        response = self.secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")

    def sanitize_input(self, user_input: str) -> str:
        """Sanitize user input"""
        # Remove potential injection attempts
        sanitized = user_input.replace("```", "")
        sanitized = sanitized.replace("<script>", "")
        # Add more sanitization as needed
        return sanitized
```

### 2. Error Handling

```python
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

class ResilientAgent:
    """Agent with robust error handling"""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    async def process_with_retry(self, request):
        """Process with automatic retry"""
        try:
            response = await self._process(request)
            return response
        except Exception as e:
            logging.error(f"Processing failed: {e}")
            raise
```

## Examples Repository

Complete working examples from Google Cloud repositories:

1. **Text Generation** - `/gemini/function-calling/`
2. **RAG Implementation** - `/gemini/use-cases/retrieval-augmented-generation/`
3. **Multi-modal Processing** - `/gemini/multimodality/`
4. **Agent Builder** - `/agent-builder/`
5. **Production Templates** - From `agent-starter-pack`

## Resources

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Gemini API Reference](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini)
- [Agent Builder Guide](https://cloud.google.com/generative-ai-app-builder/docs/agent-builder)
- [GitHub: GoogleCloudPlatform/generative-ai](https://github.com/GoogleCloudPlatform/generative-ai)
- [GitHub: GoogleCloudPlatform/agent-starter-pack](https://github.com/GoogleCloudPlatform/agent-starter-pack)

---

**Version:** 1.0.0
**Last Updated:** October 2025
**Author:** Jeremy Longshore
**Based on:** Official Google Cloud repositories
**License:** MIT