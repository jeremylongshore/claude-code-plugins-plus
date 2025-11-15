# Supplemental Reference: Cloud Run & Gemini Fine-Tuning

**Created:** November 13, 2025
**Purpose:** Consolidated reference documentation for Cloud Run deployment and Gemini model fine-tuning
**Sources:** Official Google Cloud documentation

---

## Cloud Run Overview

### What is Cloud Run?

Cloud Run is Google's **fully managed platform** for deploying and running containerized applications, functions, and code without managing infrastructure. Key principle:

> "You don't have to create a cluster or manage infrastructure to be productive."

### Core Philosophy

**Serverless Containers:**
- Deploy any containerized application
- No infrastructure management required
- Automatic scaling from zero to thousands of instances
- Pay only for actual usage
- Built-in security and compliance

**Language Agnostic:**
- Supports **any programming language** that can be containerized
- Source-based deployment for: Go, Node.js, Python, Java, .NET, Ruby
- Automatic container building following language best practices
- No container expertise required for supported languages

---

## Three Execution Models

### 1. Services (Request-Driven)

**Use Case:** Respond to HTTP requests via stable HTTPS endpoints

**Features:**
- Unique HTTPS endpoints per service
- Automatic TLS certificate management
- WebSocket, HTTP/2, and gRPC support
- Automatic scaling based on incoming traffic
- Scale to zero when idle (no traffic = no cost)
- Traffic splitting for gradual rollouts

**Example Scenarios:**
- REST APIs
- Web applications
- Microservices
- ADK agents deployed with UI
- Firebase Cloud Functions alternative

**Deployment:**
```bash
gcloud run deploy SERVICE_NAME \
    --source . \
    --region us-central1 \
    --allow-unauthenticated
```

### 2. Jobs (Task-Driven)

**Use Case:** Execute parallelizable tasks to completion, optionally on a schedule

**Features:**
- Run once, or on a schedule (cron)
- Parallel task execution
- Automatic retries on failure
- No persistent endpoint (tasks finish and shut down)
- Cost-effective for batch processing

**Example Scenarios:**
- Data processing pipelines
- Scheduled ETL jobs
- Batch inference for ML models
- Database migrations
- Report generation

**Deployment:**
```bash
gcloud run jobs create JOB_NAME \
    --source . \
    --region us-central1 \
    --task-timeout 1h \
    --max-retries 3
```

### 3. Worker Pools (Event-Driven)

**Use Case:** Handle continuous pull-based workloads

**Features:**
- Long-running processes
- Pull from Pub/Sub, Kafka, queues
- Maintain persistent connections
- Automatic scaling based on queue depth
- Always-on instances (minimum instance count)

**Example Scenarios:**
- Kafka consumers
- Pub/Sub message processors
- Queue workers (Redis, RabbitMQ)
- Stream processing
- Real-time data ingestion

**Deployment:**
```bash
gcloud run workers create WORKER_NAME \
    --source . \
    --region us-central1 \
    --min-instances 1 \
    --max-instances 10
```

---

## Key Service Features

### 1. Unique HTTPS Endpoints

**Automatic Infrastructure:**
- Each service gets a unique, stable HTTPS URL
- Automatic TLS certificate provisioning and renewal
- Global load balancing included
- Custom domain mapping support

**Protocol Support:**
- HTTP/1.1, HTTP/2, HTTP/3
- WebSocket connections
- gRPC (binary protocol)
- Server-Sent Events (SSE)

**Example URL:**
```
https://service-name-xyz123-uc.a.run.app
```

### 2. Auto-Scaling

**Dynamic Scaling:**
- Rapidly adjusts from **zero to thousands** of instances
- Based on incoming request volume
- CPU utilization
- Custom metrics (via Cloud Monitoring)

**Scaling Configuration:**
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: my-service
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "1000"
        autoscaling.knative.dev/target: "80"  # Target 80 concurrent requests per instance
```

**Scale to Zero:**
- No traffic = no running instances = no cost
- First request triggers cold start (~1-5 seconds)
- Keep warm with minimum instances if needed

### 3. Pay-Per-Use Pricing

**Billing Model:**
- Charge only for **actual usage** (not idle time)
- CPU and memory billed per 100ms increments
- Network egress charges apply
- Generous free tier:
  - 2 million requests/month
  - 360,000 vCPU-seconds/month
  - 180,000 GiB-seconds/month

**Cost Optimization:**
- Scale to zero when idle
- Right-size CPU and memory
- Use minimum instances sparingly
- Optimize cold start time

### 4. Disposable Containers

**Stateless Design:**
- Each instance has an in-memory filesystem
- Data does NOT persist across instances
- Instances can be replaced at any time
- No guaranteed execution order

**External Storage Required:**
- Use Cloud Storage for files
- Use Firestore/Cloud SQL for databases
- Use Memorystore for caching
- Use Pub/Sub for messaging

**Best Practices:**
```python
# ❌ BAD: Store data in local filesystem
with open('/tmp/user_data.json', 'w') as f:
    json.dump(data, f)

# ✅ GOOD: Store data in Cloud Storage
from google.cloud import storage
client = storage.Client()
bucket = client.bucket('my-bucket')
blob = bucket.blob('user_data.json')
blob.upload_from_string(json.dumps(data))
```

### 5. Traffic Management

**Gradual Rollouts:**
- Deploy new revision without sending traffic
- Split traffic between revisions (e.g., 90% old, 10% new)
- Monitor metrics and gradually increase traffic
- Instant rollback if issues detected

**Traffic Splitting Example:**
```bash
# Deploy new revision without traffic
gcloud run deploy SERVICE_NAME --source . --no-traffic

# Split traffic: 90% to revision-1, 10% to revision-2
gcloud run services update-traffic SERVICE_NAME \
    --to-revisions revision-1=90,revision-2=10
```

**Use Cases:**
- Canary deployments
- A/B testing
- Blue-green deployments
- Feature flags

---

## Integration Ecosystem

Cloud Run seamlessly integrates with **Google Cloud services** without managing connections:

### Database Integration

**Cloud SQL:**
- Private VPC connection
- Unix socket connections
- Connection pooling built-in

**Firestore:**
- Native SDK support
- Application Default Credentials
- No explicit connection management

**AlloyDB:**
- High-performance PostgreSQL
- Private Service Connect

### Storage Integration

**Cloud Storage:**
- Upload/download files
- Signed URLs for temporary access
- Object lifecycle management

### Messaging & Events

**Pub/Sub:**
- Push subscriptions to Cloud Run
- Pull via Worker Pools
- Ordered message delivery

**Eventarc:**
- Event-driven architecture
- Trigger on Cloud Storage events
- Audit log triggers
- Custom events

### AI/ML Integration

**Vertex AI:**
- ADK agent deployment target
- Gemini API calls
- Embeddings generation
- Model inference

**Firebase ML:**
- Custom model deployment
- AutoML integration

### Monitoring & Logging

**Cloud Logging:**
- Automatic log ingestion
- Structured logging support
- Log-based metrics

**Cloud Monitoring:**
- Request latency metrics
- Error rates
- Custom metrics

---

## ADK Deployment to Cloud Run

### Single Command Deployment

```bash
adk deploy cloud_run \
    --project PROJECT_ID \
    --region us-central1 \
    --service_name weather-agent \
    --session_service_uri=agentengine://AGENT_ENGINE_ID \
    --memory_service_uri=agentengine://AGENT_ENGINE_ID \
    --app_name weather_agent \
    --with_ui \
    . \
    -- --allow-unauthenticated \
    --no-user-output-enabled
```

### Key Parameters

**ADK-Specific:**
- `--session_service_uri`: Vertex AI Sessions service
- `--memory_service_uri`: Vertex AI Memory Bank
- `--app_name`: Agent application name
- `--with_ui`: Enable ADK Web UI for testing

**Cloud Run-Specific:**
- `--allow-unauthenticated`: Public access (testing only)
- `--no-user-output-enabled`: Disable user output logging

### Production Configuration

**For production deployments:**
1. **Require authentication**: Replace `--allow-unauthenticated` with `--no-allow-unauthenticated`
2. **Expose REST API or A2A endpoint** instead of Web UI
3. **Set resource limits**: `--memory 2Gi --cpu 2`
4. **Configure scaling**: `--min-instances 1 --max-instances 100`
5. **Enable VPC connector**: `--vpc-connector projects/PROJECT/locations/REGION/connectors/CONNECTOR`

---

## Gemini Model Supervised Fine-Tuning

### What is Supervised Fine-Tuning?

Supervised fine-tuning (SFT) **adapts Gemini models** using labeled datasets to:
- Adjust model weights
- Minimize prediction differences from actual labels
- Specialize model behavior for domain-specific tasks

### When to Use Fine-Tuning

**Ideal Use Cases:**
- Content differs significantly from model's original training data
- Prompts not producing expected results consistently
- Need for specific output formatting
- Domain-specific terminology and patterns
- Consistent behavioral patterns required

**Not Recommended When:**
- Few-shot prompting works well
- Simple formatting adjustments needed
- General-purpose responses sufficient

---

## Supported Models

### Current Fine-Tuning Support (November 2025)

**Gemini 2.x Family:**
- Gemini 2.5 Pro
- Gemini 2.5 Flash
- Gemini 2.5 Flash-Lite
- Gemini 2.0 Flash
- Gemini 2.0 Flash-Lite

**Note:** Gemini 1.5 models are NOT supported for fine-tuning.

---

## Key Use Cases for Fine-Tuning

### 1. Classification

**Task:** Generate single-word or phrase responses

**Example:**
```json
{
  "contents": [
    {"role": "user", "parts": [{"text": "Is this email spam? Subject: 'WINNER! Claim your prize now!'"}]},
    {"role": "model", "parts": [{"text": "spam"}]}
  ]
}
```

**Use Cases:**
- Content moderation
- Sentiment analysis
- Intent classification
- Entity recognition

### 2. Summarization

**Task:** Follow specific formats (e.g., remove PII, structured summaries)

**Example:**
```json
{
  "contents": [
    {"role": "user", "parts": [{"text": "Summarize this patient record: John Smith, DOB 01/15/1980, diagnosed with hypertension..."}]},
    {"role": "model", "parts": [{"text": "Patient diagnosed with hypertension. Treatment plan initiated."}]}
  ]
}
```

**Use Cases:**
- Medical record summarization (HIPAA-compliant)
- Legal document summaries
- Customer interaction summaries

### 3. Extractive Question Answering

**Task:** Return exact substrings from source material

**Example:**
```json
{
  "contents": [
    {"role": "user", "parts": [{"text": "What is the refund policy? Document: 'Refunds available within 30 days of purchase.'"}]},
    {"role": "model", "parts": [{"text": "Refunds available within 30 days of purchase."}]}
  ]
}
```

**Use Cases:**
- FAQ systems
- Document Q&A
- Contract analysis

### 4. Chat (Persona-Based)

**Task:** Implement specific personas or behavioral patterns

**Example:**
```json
{
  "contents": [
    {"role": "user", "parts": [{"text": "What's the weather like?"}]},
    {"role": "model", "parts": [{"text": "Arrr, the weather be fine today, matey! Clear skies ahead!"}]}
  ]
}
```

**Use Cases:**
- Brand-specific chatbots
- Character-based interactions
- Industry-specific assistants

---

## Technical Specifications

### Dataset Limitations (Gemini 2.5 Flash/Flash-Lite)

**Size Limits:**
- **Maximum training tokens per example:** 131,072 (128K context)
- **Maximum validation dataset:** 5,000 examples
- **Maximum file size:** 1GB (JSONL format)
- **Maximum dataset size:**
  - Text-only: 1,000,000 examples
  - Multimodal: 300,000 examples

**Format Requirements:**
- JSONL (JSON Lines) format
- One example per line
- Each example must follow the schema

### Adapter Sizes

**Gemini 2.5 Flash/Flash-Lite:**
- Available sizes: 1, 2, 4, 8, 16
- Larger adapters = more capacity but slower training
- Smaller adapters = faster training but less adaptation

**Gemini 2.5 Pro:**
- Available sizes: 1, 2, 4, 8
- Same trade-offs as Flash

**Recommendation:**
- Start with adapter size 4
- Increase if underfitting
- Decrease if overfitting or slow training

### Training Data Format

**Required Schema:**
```json
{
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "User prompt here"}]
    },
    {
      "role": "model",
      "parts": [{"text": "Expected model response"}]
    }
  ]
}
```

**Multi-Turn Conversations:**
```json
{
  "contents": [
    {"role": "user", "parts": [{"text": "First user message"}]},
    {"role": "model", "parts": [{"text": "First model response"}]},
    {"role": "user", "parts": [{"text": "Follow-up question"}]},
    {"role": "model", "parts": [{"text": "Follow-up response"}]}
  ]
}
```

**Multimodal Examples:**
```json
{
  "contents": [
    {
      "role": "user",
      "parts": [
        {"text": "What's in this image?"},
        {"inline_data": {"mime_type": "image/jpeg", "data": "base64_encoded_image"}}
      ]
    },
    {
      "role": "model",
      "parts": [{"text": "A cat sitting on a couch"}]
    }
  ]
}
```

---

## Fine-Tuning Workflow

### 1. Prepare Training Data

```python
import json

training_examples = []

for data_point in your_dataset:
    example = {
        "contents": [
            {"role": "user", "parts": [{"text": data_point['prompt']}]},
            {"role": "model", "parts": [{"text": data_point['completion']}]}
        ]
    }
    training_examples.append(example)

# Save as JSONL
with open('train_data.jsonl', 'w') as f:
    for example in training_examples:
        f.write(json.dumps(example) + '\n')
```

### 2. Upload to Cloud Storage

```bash
gsutil cp train_data.jsonl gs://YOUR_BUCKET/tuning_data/
gsutil cp validation_data.jsonl gs://YOUR_BUCKET/tuning_data/
```

### 3. Launch Fine-Tuning Job

```python
from google.genai import Client as VertexClient
from google.genai import types as genai_types

# Initialize Vertex AI client
vertex_client = VertexClient(vertexai=True, project=PROJECT_ID, location=REGION)

# Configure training
training_dataset = {"gcs_uri": "gs://YOUR_BUCKET/tuning_data/train_data.jsonl"}
validation_dataset = genai_types.TuningValidationDataset(
    gcs_uri="gs://YOUR_BUCKET/tuning_data/validation_data.jsonl"
)

# Start tuning job
tuning_job = vertex_client.tunings.tune(
    base_model="gemini-2.5-flash",
    training_dataset=training_dataset,
    config=genai_types.CreateTuningJobConfig(
        adapter_size="ADAPTER_SIZE_FOUR",
        epoch_count=3,
        tuned_model_display_name="my-tuned-model",
        validation_dataset=validation_dataset,
    ),
)

print(f"Tuning job created: {tuning_job.name}")
```

### 4. Monitor Job Progress

```python
import time

# Poll job status
while tuning_job.state in [
    genai_types.JobState.JOB_STATE_PENDING,
    genai_types.JobState.JOB_STATE_RUNNING,
]:
    print(f"Status: {tuning_job.state}")
    time.sleep(60)  # Check every minute
    tuning_job = vertex_client.tunings.get(name=tuning_job.name)

print(f"Final status: {tuning_job.state}")

if tuning_job.state == genai_types.JobState.JOB_STATE_SUCCEEDED:
    print(f"Tuned model endpoint: {tuning_job.tuned_model.endpoint}")
```

### 5. Evaluate Tuned Model

```python
# Query tuned model
response = vertex_client.models.generate_content(
    model=tuning_job.tuned_model.endpoint,
    contents=[{"role": "user", "parts": [{"text": "Test prompt"}]}],
    config={"temperature": 0.1, "max_output_tokens": 50},
)

print(response.text)
```

---

## Evaluation and Deployment

### Integrated Evaluation

**Gen AI Evaluation Service:**
- Automatic evaluation for supported models and regions
- Track quality metrics over time
- Compare base model vs. tuned model performance

**Evaluation Metrics:**
- Accuracy
- Precision/Recall (classification tasks)
- ROUGE scores (summarization)
- BLEU scores (translation)
- Custom metrics

### Deployment Options

**Inference Pricing:**
- Tuned models use **same pricing as base models**
- No additional inference cost
- Pay for tuning job compute time only

**Deployment Methods:**
1. **Direct API calls** via Vertex AI SDK
2. **Cloud Run deployment** for scalable serving
3. **Agent Engine integration** for agent-based apps

### Important Constraints

**⚠️ No Controlled Generation at Inference:**
> "Models aren't trained to handle controlled generation during tuning."

**What This Means:**
- Don't use JSON mode with tuned models
- Don't apply strict output constraints at inference
- Train the model to produce desired format instead

---

## Best Practices

### Data Preparation

1. **Quality over Quantity:**
   - 100 high-quality examples > 1,000 low-quality examples
   - Ensure consistency in formatting
   - Remove noisy or contradictory examples

2. **Balanced Dataset:**
   - Equal representation of classes (classification)
   - Diverse examples covering edge cases
   - Validation set should match test distribution

3. **Format Consistency:**
   - Consistent prompt structure
   - Consistent completion format
   - Follow JSONL schema exactly

### Training Configuration

1. **Start Small:**
   - Begin with adapter size 4
   - Use 3 epochs initially
   - Evaluate before scaling up

2. **Monitor Validation Loss:**
   - Track validation metrics during training
   - Stop early if overfitting detected
   - Use validation dataset for tuning decisions

3. **Regional Configuration:**
   - Choose region close to data source
   - Ensure data residency compliance
   - Consider latency requirements

### Evaluation Strategy

1. **Hold-Out Test Set:**
   - Never use test data for training or validation
   - Evaluate final model on unseen data
   - Report metrics on test set only

2. **Qualitative Review:**
   - Manually inspect model outputs
   - Check for edge cases and failure modes
   - Validate against business requirements

3. **A/B Testing:**
   - Compare tuned model vs. base model in production
   - Measure business metrics (conversion, satisfaction)
   - Roll back if tuned model underperforms

---

## Related jeremy-* Plugins

### jeremy-vertex-engine
- Vertex AI Agent Engine deployment and management
- Runtime configuration validation
- Production readiness checks

### jeremy-vertex-validator
- Validate fine-tuning datasets
- Check JSONL format compliance
- Production deployment validation

### jeremy-genkit-pro
- Firebase Genkit integration with tuned Gemini models
- Cloud Run deployment automation
- RAG with fine-tuned models

### jeremy-vertex-terraform
- Terraform infrastructure for tuning jobs
- Automated pipeline deployment
- Resource provisioning

### jeremy-adk-orchestrator
- ADK agents with fine-tuned Gemini models
- Multi-agent systems on Cloud Run
- Memory Bank integration

---

## Quick Reference

### Cloud Run Deployment
```bash
gcloud run deploy SERVICE_NAME --source . --region us-central1
```

### ADK to Cloud Run
```bash
adk deploy cloud_run --project PROJECT_ID --region REGION --service_name SERVICE
```

### Start Fine-Tuning Job
```python
tuning_job = vertex_client.tunings.tune(
    base_model="gemini-2.5-flash",
    training_dataset={"gcs_uri": "gs://bucket/train.jsonl"},
    config={"adapter_size": "ADAPTER_SIZE_FOUR", "epoch_count": 3}
)
```

### Check Tuning Job Status
```python
job = vertex_client.tunings.get(name=tuning_job.name)
print(job.state)
```

### Query Tuned Model
```python
response = vertex_client.models.generate_content(
    model=tuned_model_endpoint,
    contents=[{"role": "user", "parts": [{"text": "prompt"}]}]
)
```

---

**Documentation Version:** November 2025
**Last Updated:** 2025-11-13
**Status:** Production-Ready Reference
