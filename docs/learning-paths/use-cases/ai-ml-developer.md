# 🤖 AI/ML Developer Learning Path

**Goal**: Master AI/ML development from prompt engineering to production RAG systems and model deployment.

**Time**: 4-6 hours total
**Difficulty**: Beginner → Advanced

---

## Learning Journey

```mermaid
graph LR
    A[Prompts] --> B[LLM APIs]
    B --> C[RAG Systems]
    C --> D[Model Deploy]
    D --> E[Production]

    style A fill:#90EE90
    style B fill:#87CEEB
    style C fill:#FFB6C1
    style D fill:#DDA0DD
    style E fill:#F0E68C
```

---

## Table of Contents

1. [Prompt Engineering](#stage-1-prompt-engineering-1-hour) (1 hour)
2. [LLM API Integration](#stage-2-llm-api-integration-15-hours) (1.5 hours)
3. [RAG System Development](#stage-3-rag-system-development-2-hours) (2 hours)
4. [Model Training & Fine-tuning](#stage-4-model-training--fine-tuning-15-hours) (1.5 hours)
5. [Production Deployment](#stage-5-production-deployment-15-hours) (1.5 hours)

---

## Stage 1: Prompt Engineering (1 hour)

### Install AI/ML Pack
```bash
/plugin install ai-ml-engineering-pack@claude-code-plugins
```

**Includes 12 plugins**:
- Prompt optimization
- LLM integration
- RAG system builders
- Model deployment tools

### Master Prompt Crafting

**1. Prompt Architect Agent**
```bash
# Use the prompt-architect agent
# Available automatically with the pack
```

**Creates optimized prompts**:
```
Before (bad):
"Write code for authentication"

After (good):
"You are a senior backend engineer specializing in secure authentication.

Task: Implement a production-ready JWT authentication system.

Requirements:
- Use bcrypt for password hashing
- Implement token refresh mechanism
- Add rate limiting
- Include comprehensive error handling
- Follow OWASP security guidelines

Output format:
1. Code implementation
2. Security considerations
3. Testing strategy
```

**2. Prompt Optimization**
```bash
/prompt-optimize
```

**Analyzes prompts for**:
- Clarity and specificity
- Context sufficiency
- Output format definition
- Example inclusion
- Error handling

### Prompt Patterns

**Chain-of-Thought**:
```
Let's solve this step-by-step:
1. First, analyze the requirements
2. Then, design the architecture
3. Next, implement the solution
4. Finally, add tests and docs
```

**Few-Shot Learning**:
```
Example 1:
Input: User registration
Output: POST /api/users endpoint with validation

Example 2:
Input: User login
Output: POST /api/auth/login with JWT response

Now create:
Input: Password reset
Output: ...
```

**Practice**: Optimize prompts for your AI tasks

---

## Stage 2: LLM API Integration (1.5 hours)

### Integrate LLM APIs

**1. OpenAI Integration**
```bash
/llm-api-scaffold openai
```

**Generates**:
```python
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_response(prompt: str, model: str = "gpt-4") -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content
```

**2. Anthropic Claude Integration**
```bash
/llm-api-scaffold anthropic
```

**Generates**:
```python
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def generate_response(prompt: str, model: str = "claude-3-opus-20240229") -> str:
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text
```

**3. Model Selection Guide**
```bash
/model-selector
```

**Recommends models based on**:
- Task complexity
- Response time requirements
- Cost constraints
- Context window needs
- Multimodal requirements

**Practice**: Build a chatbot with LLM API

---

## Stage 3: RAG System Development (2 hours)

### Build Retrieval-Augmented Generation

**1. Generate RAG Pipeline**
```bash
/rag-pipeline-gen
```

**Creates complete system**:
```python
# Document Processing
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

loader = DirectoryLoader('./docs', glob="**/*.md")
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = text_splitter.split_documents(documents)

# Vector Store
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone

embeddings = OpenAIEmbeddings()
vectorstore = Pinecone.from_documents(
    chunks,
    embeddings,
    index_name="my-rag-index"
)

# Retrieval Chain
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(temperature=0, model="gpt-4")
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3})
)

# Query
response = qa_chain.run("What is the refund policy?")
```

**2. Vector Database Setup**
```bash
/vector-db-expert
```

**Configures**:
- Pinecone
- Weaviate
- Chroma
- Qdrant
- Milvus

**Includes**:
- Schema design
- Index optimization
- Similarity search
- Metadata filtering

**3. Embedding Strategies**
```bash
# Optimize embeddings
/embedding-optimizer
```

**Compares models**:
- OpenAI text-embedding-ada-002
- Cohere embed-english-v3.0
- Sentence Transformers
- Custom fine-tuned models

**Practice**: Build a RAG system for your docs

---

## Stage 4: Model Training & Fine-tuning (1.5 hours)

### Train Custom Models

**1. Model Training Pipeline**
```bash
/ml-model-trainer
```

**Sets up**:
```python
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer
)

# Load model
model = AutoModelForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels=3
)

# Training config
training_args = TrainingArguments(
    output_dir="./results",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    num_train_epochs=3,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="accuracy"
)

# Train
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    compute_metrics=compute_metrics
)

trainer.train()
```

**2. Hyperparameter Tuning**
```bash
/hyperparameter-tuner
```

**Optimizes**:
- Learning rate
- Batch size
- Number of epochs
- Optimizer selection
- Regularization

**Uses**:
- Optuna
- Ray Tune
- Weights & Biases

**3. Model Evaluation**
```bash
/model-evaluation-suite
```

**Metrics**:
- Accuracy, Precision, Recall, F1
- Confusion matrix
- ROC curves
- Calibration plots
- Error analysis

**Practice**: Fine-tune a model for your domain

---

## Stage 5: Production Deployment (1.5 hours)

### Deploy to Production

**1. Model Serving**
```bash
/model-deployment-helper
```

**Deployment options**:

**FastAPI Endpoint**:
```python
from fastapi import FastAPI
from pydantic import BaseModel
import torch

app = FastAPI()

class PredictionRequest(BaseModel):
    text: str

@app.post("/predict")
async def predict(request: PredictionRequest):
    # Load model (cached)
    model = load_model()

    # Inference
    with torch.no_grad():
        prediction = model(request.text)

    return {
        "prediction": prediction.tolist(),
        "confidence": float(prediction.max())
    }
```

**2. Monitoring & Observability**
```bash
/ai-monitoring-setup
```

**Sets up**:
- Model performance tracking
- Latency monitoring
- Error rate alerts
- Data drift detection
- A/B testing framework

**3. Scaling & Optimization**
```bash
/model-optimization
```

**Optimizations**:
- Model quantization (INT8, FP16)
- ONNX export
- TensorRT acceleration
- Batch inference
- Model caching

**Practice**: Deploy model with monitoring

---

## Real-World Scenario: Build Production AI System

### Complete AI Application (3 hours)

**1. Design System** (20 min)
```bash
# Use AI architect agent
# Design RAG-based customer support system
```

**2. Prompt Engineering** (30 min)
```bash
/prompt-optimize

# Create prompts for:
# - Intent classification
# - Response generation
# - Quality assessment
```

**3. LLM Integration** (30 min)
```bash
/llm-api-scaffold anthropic

# Integrate Claude API
# Add streaming responses
# Implement rate limiting
```

**4. RAG Pipeline** (60 min)
```bash
/rag-pipeline-gen

# Index support documentation
# Set up vector search
# Build retrieval chain
```

**5. Model Fine-tuning** (40 min)
```bash
/ml-model-trainer

# Fine-tune classifier
# Optimize for latency
# Evaluate accuracy
```

**6. Deploy** (40 min)
```bash
/model-deployment-helper

# Deploy to FastAPI
# Add monitoring
# Configure autoscaling
```

---

## Advanced AI Patterns

### Multi-Agent Systems
```python
from langchain.agents import initialize_agent, Tool

# Define agents
researcher = Agent(
    role="Research Analyst",
    goal="Find accurate information",
    tools=[search_tool, web_scrape_tool]
)

writer = Agent(
    role="Content Writer",
    goal="Create engaging content",
    tools=[llm_tool, grammar_tool]
)

# Orchestrate
result = crew.kickoff({
    "topic": "AI trends 2024",
    "length": "1000 words"
})
```

### Agentic Workflows
```bash
/agentic-workflow-builder

# Creates:
# - Task decomposition
# - Agent coordination
# - Tool selection
# - Result synthesis
```

### AI Safety & Ethics
```bash
/ai-ethics-validator

# Checks:
# - Bias detection
# - Harmful content filtering
# - Privacy compliance
# - Explainability
```

---

## Best Practices

### Prompt Engineering
```python
# ✅ Good prompt structure
system_prompt = """
You are a {role} with expertise in {domain}.

Your task: {task}

Guidelines:
- {guideline_1}
- {guideline_2}

Output format: {format}
"""

# ❌ Avoid vague prompts
bad_prompt = "Help me with this"
```

### RAG Optimization
```python
# ✅ Optimized chunking
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,           # Optimal for most embeddings
    chunk_overlap=50,         # 10% overlap
    separators=["\n\n", "\n", ". ", " ", ""]
)

# ✅ Hybrid search
results = vectorstore.similarity_search_with_score(
    query,
    k=5,
    filter={"category": "technical"}
)
```

### Model Serving
```python
# ✅ Efficient batching
@app.post("/batch-predict")
async def batch_predict(requests: List[PredictionRequest]):
    texts = [req.text for req in requests]

    # Batch inference
    with torch.no_grad():
        predictions = model(texts, batch_size=32)

    return predictions
```

---

## Plugin Reference

| Plugin | Use Case | Time to Learn |
|--------|----------|---------------|
| `prompt-architect` | Prompt optimization | 20 min |
| `llm-api-scaffold` | API integration | 30 min |
| `rag-pipeline-gen` | RAG systems | 60 min |
| `vector-db-expert` | Vector databases | 30 min |
| `ml-model-trainer` | Model training | 45 min |
| `hyperparameter-tuner` | Optimization | 30 min |
| `model-deployment-helper` | Production deploy | 40 min |
| `ai-monitoring-setup` | Observability | 25 min |
| `ai-ethics-validator` | AI safety | 20 min |

**Full Pack**: `ai-ml-engineering-pack` (12 plugins, 4 hours to master)

---

## Certification Path

**AI Developer** ✅
- [ ] Master prompt engineering
- [ ] Integrate LLM APIs
- [ ] Build RAG system

**ML Engineer** ✅
- [ ] Train custom models
- [ ] Optimize hyperparameters
- [ ] Deploy to production

**AI Architect** ✅
- [ ] Design multi-agent systems
- [ ] Implement AI safety
- [ ] Scale to millions of requests

---

## Next Steps

**Expand Your Skills**:
- [DevOps Path](./devops-engineer.md): Deploy AI infrastructure
- [Security Path](./security-specialist.md): Secure AI systems
- [Advanced Developer](../03-advanced-developer/): Build AI tools

**Resources**:
- [AI/ML Pack Docs](../../../plugins/packages/ai-ml-engineering-pack/)
- [LangChain Docs](https://python.langchain.com/)
- [Claude Code AI Guide](https://docs.claude.com/en/docs/claude-code/use-cases/ai-ml)

---

**Congratulations!** You're now a Claude Code AI/ML expert! 🤖
