# Vertex AI Search & Ray on Vertex AI: Comprehensive Guide

**Created:** November 13, 2025
**Purpose:** Master guide for enterprise search, RAG applications, and distributed ML workloads on Google Cloud
**Status:** Production-Ready Reference

---

## Table of Contents

1. [Vertex AI Search Overview](#vertex-ai-search-overview)
2. [Vector Search vs Vertex AI Search](#vector-search-vs-vertex-ai-search)
3. [Data Store Types and Architecture](#data-store-types-and-architecture)
4. [RAG with Vertex AI Search and Gemini](#rag-with-vertex-ai-search-and-gemini)
5. [Ray on Vertex AI Overview](#ray-on-vertex-ai-overview)
6. [Distributed ML Workloads with Ray](#distributed-ml-workloads-with-ray)
7. [BigQuery Integration with Ray](#bigquery-integration-with-ray)
8. [Production Deployment Patterns](#production-deployment-patterns)

---

## Vertex AI Search Overview

### What It Is

**Vertex AI Search** is a Google Cloud platform that enables developers—regardless of ML expertise—to build **enterprise-grade generative AI applications** for search, recommendations, and conversational experiences. The platform combines:

> "Google's foundation models and search and recommendation expertise to deliver AI-enabled search, browse, answer generation, and recommendations capabilities."

### Product Evolution

**Historical Names:**
- AI Applications
- Agent Builder
- Vertex AI Search and Conversation
- Enterprise Search
- Generative AI App Builder

**Current Branding:** Vertex AI Search (as of 2025)

**API Backend:** Discovery Engine API (`discoveryengine.googleapis.com`)

### Core Capabilities

#### 1. Deep Information Retrieval
- Advanced natural language processing
- Semantic understanding of user intent
- Context-aware relevance ranking

#### 2. Foundation Model Integration
- Gemini 2.0 Flash (gemini-2.0-flash-001) for answer generation
- Context-based question answering
- Generative AI summarization

#### 3. Google-Quality Search
- Out-of-the-box natural language understanding
- Automated synonym recognition
- Spelling correction and auto-suggest
- Self-learning ranking models with clickstream analytics

#### 4. Retrieval Augmented Generation (RAG)
- Ground LLM responses with retrieved search results
- Combine enterprise data with foundation models
- Reduce hallucinations through fact-grounding

---

## Application Types

### 1. Search Applications

#### Custom Search
- **Purpose:** Search proprietary data or private websites
- **Data Sources:** Documents, PDFs, HTML, JSON, databases
- **Use Cases:** Internal knowledge bases, document repositories, corporate wikis

#### Media Search
- **Purpose:** Search movies, videos, music, and multimedia content
- **Data Sources:** Media catalogs, streaming libraries, content databases
- **Use Cases:** Streaming platforms, content discovery, media recommendations

#### Healthcare Search
- **Purpose:** Search FHIR R4 data and clinical records
- **Data Sources:** Cloud Healthcare API FHIR stores
- **Use Cases:** Patient record search, clinical decision support, medical literature search
- **Compliance:** HIPAA-compliant, healthcare-specific NLP

#### Website Search
- **Purpose:** Index and search public or private websites
- **Data Sources:** Website URLs, sitemaps
- **Use Cases:** Customer support portals, documentation sites, e-commerce catalogs

### 2. Recommendation Applications

#### Media Recommendations
- **Purpose:** Personalized content discovery
- **Data Sources:** User interaction history, media catalogs
- **Use Cases:** "Watch next" suggestions, playlist generation, content recommendations

#### Custom Recommendations (Preview)
- **Purpose:** Recommendations for non-media content
- **Data Sources:** Product catalogs, user behavior
- **Use Cases:** E-commerce product recommendations, article suggestions, resource discovery

---

## Key Features in Detail

### 1. Out-of-the-Box Natural Language Understanding

**Capabilities:**
- Semantic search (understand meaning, not just keywords)
- Multi-language support
- Entity recognition
- Intent classification

**Example:**
```
User query: "How do I reset my password?"
Semantic understanding: Password recovery, account access, authentication troubleshooting
Relevant results: Password reset guide, account security documentation, 2FA setup
```

### 2. Automated Search Enhancement

**Synonym Recognition:**
- Automatically detects synonyms and related terms
- Example: "car" → "automobile", "vehicle", "auto"

**Spelling Correction:**
- Suggests corrected spellings for misspelled queries
- Example: "pasword reset" → "password reset"

**Auto-Suggest:**
- Real-time query completion
- Based on popular searches and indexed content

### 3. Generative AI Capabilities

**Answer Generation:**
- Gemini 2.0 Flash model for context-based Q&A
- Extractive and abstractive summarization
- Conversational search experiences

**Example:**
```
User: "What are the benefits of our health plan?"
Generated Answer: "Our health plan provides comprehensive coverage including:
1. Medical, dental, and vision insurance
2. $0 copay for preventive care
3. Prescription drug coverage with low copays
4. Mental health and wellness support"
```

### 4. Self-Learning Ranking

**Clickstream Analytics:**
- Track user interactions with search results
- Learn from clicks, dwell time, and conversions
- Continuously improve result relevance

**Personalization:**
- User-specific ranking adjustments
- Contextual relevance based on history
- Adaptive search experiences

### 5. Embeddable Search Widget

**Integration Methods:**
- Iframe embed
- JavaScript widget
- REST API integration
- Custom UI with API backend

**Features:**
- Pre-built UI components
- Customizable styling
- Mobile-responsive design
- Accessibility compliance (WCAG 2.1)

---

## Data Store Types and Architecture

### Core Relationship Structure

Vertex AI Search organizes data through **apps** and **data stores**:

#### Apps
**Definition:** The interface through which users interact with search/recommendations

**Types:**
- Custom search apps
- Custom recommendations apps
- Media apps
- Healthcare apps

**Relationship Models:**
- **Custom search apps**: Many-to-many with data stores (blended search)
- **Custom recommendations apps**: One-to-one with data stores
- **Media/healthcare apps**: Many-to-one (multiple apps can share a data store)

**Important:** Once connected, **a data store cannot be disconnected** from an app.

#### Data Stores
**Definition:** Repositories that hold indexed data for search/recommendations

**Types:**
1. Structured data stores
2. Unstructured data stores
3. Website data stores
4. Media data stores
5. Healthcare data stores

---

### 1. Structured Data Stores

**Purpose:** Semantic search or recommendations over structured data

**Data Format:**
- Organized in defined schemas
- Rows in tables or JSON records
- Key-value pairs with consistent structure

**Supported Sources:**
- BigQuery tables
- Cloud Storage (JSON files)
- Manual JSON uploads via API

**Example Use Cases:**
- Hotel catalogs (name, location, price, amenities)
- Real estate listings (address, bedrooms, price, photos)
- Restaurant directories (cuisine, rating, hours, menu)
- Product catalogs (SKU, name, description, price, inventory)

**Example Schema:**
```json
{
  "id": "hotel-123",
  "name": "Grand Plaza Hotel",
  "location": "San Francisco, CA",
  "price_per_night": 250.00,
  "amenities": ["WiFi", "Pool", "Gym", "Restaurant"],
  "rating": 4.5,
  "availability": true
}
```

---

### 2. Unstructured Data Stores

**Purpose:** Semantic search over documents and images

**Supported File Types:**
- **Documents:** PDF, TXT, HTML, DOCX, PPTX, XLSX, XLSM
- **Images:** JPEG, PNG (for multimodal search)

**Data Sources:**
- Cloud Storage buckets
- BigQuery (with file URIs)

**Processing:**
- Automatic text extraction (OCR for images)
- Content chunking for large documents
- Embedding generation for semantic search

**Example Use Cases:**
- Corporate policy documents
- Technical manuals and user guides
- Research papers and articles
- Legal contracts and agreements
- Presentation decks and reports

**Example Document Structure:**
```
gs://my-bucket/documents/employee-handbook.pdf
├── Page 1: Introduction and Welcome
├── Page 2-5: Company Policies
├── Page 6-10: Benefits and Compensation
└── Page 11-15: Code of Conduct
```

---

### 3. Website Data Stores

**Purpose:** Index content from websites (public or private)

**Data Characteristics:**
- Primarily unstructured (HTML, text, images)
- Can include structured metadata (meta tags, schema.org, PageMap)

**Requirements:**
- **Domain verification** required for data store owners
- Accessible via HTTP/HTTPS
- Robots.txt compliance

**Indexing Methods:**
- **Standard indexing:** Basic crawl and index
- **Advanced indexing:** Enhanced understanding, requires verification

**Metadata Enhancement:**
```html
<!-- Schema.org structured data -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "How to Reset Your Password",
  "author": "Support Team",
  "datePublished": "2025-01-15"
}
</script>

<!-- PageMap for custom metadata -->
<PageMap>
  <DataObject type="document">
    <Attribute name="category">troubleshooting</Attribute>
    <Attribute name="difficulty">easy</Attribute>
  </DataObject>
</PageMap>
```

**Example Use Cases:**
- Customer support documentation
- Product documentation sites
- Corporate blogs and news
- E-commerce product pages

---

### 4. Media Data Stores

**Purpose:** Structured data stores with media-specific schemas

**Required Fields (5 media-related):**
- Title
- URI (content location)
- Categories/genres
- Duration (for videos/audio)
- Availability dates

**Optional Fields:**
- Thumbnail images
- Actors/artists
- Release date
- Rating/maturity level
- Language/subtitles

**Example Schema:**
```json
{
  "id": "movie-456",
  "title": "Example Movie",
  "uri": "https://streaming.example.com/watch/movie-456",
  "categories": ["Action", "Thriller"],
  "duration": "7200",
  "availabilityStartDate": "2025-01-01",
  "thumbnailUri": "https://cdn.example.com/thumbnails/movie-456.jpg",
  "rating": "PG-13"
}
```

---

### 5. Healthcare Data Stores

**Purpose:** Search FHIR R4 data from Cloud Healthcare API

**Data Source:**
- Cloud Healthcare API FHIR stores
- Supported FHIR R4 resources

**Compliance:**
- HIPAA-compliant infrastructure
- PHI (Protected Health Information) handling
- Audit logging for access

**Ingestion Methods:**
- Batch import into data stores
- Streaming import via data connectors

**Example Use Cases:**
- Patient record search
- Medication lookup
- Lab results retrieval
- Clinical decision support

**Example FHIR Resource:**
```json
{
  "resourceType": "Patient",
  "id": "patient-789",
  "name": [{
    "use": "official",
    "family": "Doe",
    "given": ["John"]
  }],
  "birthDate": "1980-05-15",
  "gender": "male"
}
```

---

## Data Ingestion Methods

### Cloud Storage Upload

**Supported Formats:**
- JSON, JSONL (for structured data)
- PDF, TXT, HTML, DOCX, PPTX, XLSX, XLSM (for unstructured data)
- JPEG, PNG (for images)

**Process:**
```bash
# 1. Upload files to Cloud Storage
gsutil cp documents/*.pdf gs://my-bucket/documents/

# 2. Create data store pointing to bucket
gcloud alpha discovery-engine data-stores create my-datastore \
    --location=global \
    --industry-vertical=GENERIC \
    --content-config=CONTENT_REQUIRED

# 3. Import documents
gcloud alpha discovery-engine documents import my-datastore \
    --location=global \
    --gcs-uri=gs://my-bucket/documents/*.pdf
```

### BigQuery Import

**Advantages:**
- Large-scale data ingestion
- Structured data from data warehouse
- Query-based data selection

**Process:**
```python
from google.cloud import discoveryengine_v1

client = discoveryengine_v1.DocumentServiceClient()

import_request = discoveryengine_v1.ImportDocumentsRequest(
    parent=f"projects/{PROJECT_ID}/locations/global/dataStores/{DATA_STORE_ID}/branches/default_branch",
    bigquery_source=discoveryengine_v1.BigQuerySource(
        project_id=PROJECT_ID,
        dataset_id="my_dataset",
        table_id="my_table",
        data_schema="document"
    )
)

operation = client.import_documents(request=import_request)
response = operation.result()
```

### Website Indexing

**Standard Indexing:**
```bash
# Create website data store
gcloud alpha discovery-engine data-stores create website-datastore \
    --location=global \
    --industry-vertical=GENERIC \
    --content-config=PUBLIC_WEBSITE

# Add website URLs
gcloud alpha discovery-engine target-sites create \
    --data-store=website-datastore \
    --location=global \
    --uris=https://example.com
```

**Advanced Indexing:**
- Requires domain verification
- Enhanced content understanding
- Better structured data extraction

### RESTful API Integration

**Real-time Updates:**
```python
# Create document via API
from google.cloud import discoveryengine_v1

document = discoveryengine_v1.Document(
    id="doc-123",
    struct_data={
        "title": "Product Manual",
        "content": "Detailed product information...",
        "category": "Documentation"
    }
)

client.create_document(
    parent=f"projects/{PROJECT_ID}/locations/global/dataStores/{DATA_STORE_ID}/branches/default_branch",
    document=document,
    document_id="doc-123"
)
```

---

## Blended Search: Multi-Data Store Apps

### What is Blended Search?

**Definition:** A single custom search app that searches across **multiple data stores** simultaneously.

**Benefits:**
- Unified search experience across different data types
- Single API endpoint for diverse content
- Centralized relevance ranking

**Example:**
```
Search Query: "company benefits"
├── Data Store 1: Employee Handbook (PDF documents)
├── Data Store 2: Benefits Portal (structured JSON)
├── Data Store 3: HR Website (website crawl)
└── Blended Results: Combined and ranked from all three sources
```

### Requirements and Limitations

**Minimum Requirements:**
- At least 2 data stores must be connected during app creation
- All data stores must be in the same location

**Limitations:**
- Maximum of **50 data stores per search app**
- Unstructured data imported via BigQuery is **NOT supported**
- Website data stores must have **advanced indexing enabled**
- All data stores must have **matching CMEK configurations** (if using customer-managed encryption)

**Configuration:**
```python
from google.cloud import discoveryengine_v1

# Create blended search app
engine = discoveryengine_v1.Engine(
    display_name="Blended Search App",
    solution_type=discoveryengine_v1.SolutionType.SOLUTION_TYPE_SEARCH,
    data_store_ids=[
        f"projects/{PROJECT_ID}/locations/global/dataStores/datastore-1",
        f"projects/{PROJECT_ID}/locations/global/dataStores/datastore-2",
        f"projects/{PROJECT_ID}/locations/global/dataStores/datastore-3"
    ]
)

client.create_engine(parent=f"projects/{PROJECT_ID}/locations/global/collections/default_collection", engine=engine)
```

---

## RAG with Vertex AI Search and Gemini

### What is Retrieval Augmented Generation (RAG)?

**Definition:** A technique that combines **information retrieval** (search) with **generative AI** (LLMs) to produce factually grounded, contextually accurate responses.

**Core Principle:**
> "Retrieve relevant information from a knowledge base, then use that information to augment the LLM's prompt for generating responses."

### Why RAG?

**Problem:**
- LLMs are trained on static datasets (knowledge cutoff date)
- Cannot access real-time or proprietary data
- Prone to hallucinations (generating false information)

**Solution with RAG:**
- Ground responses in retrieved facts
- Access up-to-date enterprise data
- Reduce hallucinations significantly
- Provide citations and sources

---

## RAG Architecture with Vertex AI Search and Gemini

### High-Level Workflow

```
1. User Query
   ↓
2. Query Embedding (Vertex AI Embeddings API)
   ↓
3. Semantic Search (Vertex AI Search)
   ↓
4. Retrieve Relevant Documents
   ↓
5. Augment Prompt with Retrieved Context
   ↓
6. Generate Response (Gemini 2.0 Flash)
   ↓
7. Return Grounded Answer with Citations
```

### Detailed Process

#### Step 1: User Query
```python
user_query = "What are the eligibility requirements for our health insurance plan?"
```

#### Step 2: Query Embedding
```python
from vertexai.language_models import TextEmbeddingModel

embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
query_embedding = embedding_model.get_embeddings([user_query])[0].values
```

#### Step 3: Semantic Search
```python
from google.cloud import discoveryengine_v1

search_request = discoveryengine_v1.SearchRequest(
    serving_config=f"projects/{PROJECT_ID}/locations/global/dataStores/{DATA_STORE_ID}/servingConfigs/default_config",
    query=user_query,
    page_size=5  # Top 5 results
)

response = search_client.search(search_request)
retrieved_documents = [result.document for result in response.results]
```

#### Step 4: Augment Prompt
```python
context = "\n\n".join([
    f"Document {i+1}: {doc.struct_data['content']}"
    for i, doc in enumerate(retrieved_documents)
])

augmented_prompt = f"""
Based on the following information from our company documents, answer the user's question.

Context:
{context}

User Question: {user_query}

Answer:
"""
```

#### Step 5: Generate Response
```python
from vertexai.preview.generative_models import GenerativeModel

model = GenerativeModel("gemini-2.0-flash-001")
response = model.generate_content(augmented_prompt)
answer = response.text
```

#### Step 6: Return with Citations
```python
final_response = {
    "answer": answer,
    "sources": [
        {"title": doc.struct_data['title'], "uri": doc.struct_data['uri']}
        for doc in retrieved_documents
    ]
}
```

---

## Multimodal RAG

### What is Multimodal RAG?

**Definition:** RAG that combines **text and visual data** (images, diagrams, charts) for richer context and more accurate responses.

**Capabilities:**
- Process text alongside images
- Understand diagrams and charts
- Extract information from visual content
- Cross-modal reasoning (text ↔ image)

### Use Cases

1. **Technical Documentation:**
   - Search manuals with diagrams
   - Extract information from flowcharts
   - Understand assembly instructions

2. **Healthcare:**
   - Medical imaging analysis with context
   - Radiology report generation
   - Clinical decision support with visual data

3. **E-commerce:**
   - Visual product search
   - Image-based recommendations
   - Style and similarity matching

4. **Education:**
   - Diagram explanations
   - Visual learning materials
   - Interactive textbook search

### Implementation Example

```python
from vertexai.preview.generative_models import GenerativeModel, Part

# Multimodal embeddings for both text and images
from vertexai.vision_models import MultiModalEmbeddingModel

mm_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

# Generate embeddings for images
image_embeddings = mm_model.get_embeddings(
    image=Part.from_uri("gs://my-bucket/product-diagram.png"),
    contextual_text="Product assembly instructions"
)

# Search with multimodal query
search_request = discoveryengine_v1.SearchRequest(
    serving_config=SERVING_CONFIG,
    query="How do I assemble the product?",
    # Include image in query for multimodal search
)

# Generate response with Gemini (multimodal)
model = GenerativeModel("gemini-2.0-flash-001")
response = model.generate_content([
    "Based on this diagram and text, explain the assembly process:",
    Part.from_uri("gs://my-bucket/product-diagram.png"),
    retrieved_text_context
])
```

---

## Grounding with Google Search

### What is Grounding?

**Definition:** Connecting LLM responses to **verifiable external sources** to reduce hallucinations and improve accuracy.

**Vertex AI Grounding Options:**
1. **Enterprise Data:** Vertex AI Search (your own data)
2. **Google Search:** Public web information
3. **Hybrid:** Combination of both

### When to Use Google Search Grounding

**Ideal For:**
- Current events and news
- General knowledge questions
- Public information verification
- Supplementing limited enterprise data

**Not Ideal For:**
- Proprietary company information
- Sensitive/confidential data
- Internal policies and procedures

### Implementation

```python
from vertexai.preview.generative_models import GenerativeModel, grounding

model = GenerativeModel("gemini-2.0-flash-001")

# Enable Google Search grounding
response = model.generate_content(
    "What are the latest developments in quantum computing?",
    generation_config={
        "temperature": 0.2,
    },
    tools=[grounding.GoogleSearchRetrieval()]
)

# Response includes grounding metadata
print(response.text)
print(response.grounding_metadata)
```

---

## Vector Search vs Vertex AI Search

### Vector Search

**What It Is:**
- Google Cloud's **vector similarity search engine**
- Built on the ScaNN (Scalable Nearest Neighbors) algorithm
- Optimized for **embedding-based search**

**Use Cases:**
- Semantic similarity search
- Recommendation systems
- Finding similar items (products, documents, images)
- RAG implementations (retrieval component)
- Real-time analytics

**Key Features:**
- Dense embeddings (semantic meaning)
- Sparse embeddings (keyword-based)
- Hybrid search (combining both)
- Low-latency queries (milliseconds)
- Billion-scale indexing

**Integration:**
- Vertex AI Embeddings API (generate embeddings)
- Vertex AI Feature Store (manage features)
- Vertex AI Pipelines (automate workflows)
- Vertex AI Ranking API (rerank results)

**Example:**
```python
from google.cloud import aiplatform

# Create Vector Search index
index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name="product-embeddings",
    dimensions=768,  # Embedding dimensions
    approximate_neighbors_count=10,
    shard_size="SHARD_SIZE_SMALL"
)

# Deploy index
index_endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
    display_name="product-search-endpoint"
)
index_endpoint.deploy_index(index=index)

# Query for similar items
query_embedding = [0.1, 0.2, ...]  # 768-dimensional vector
response = index_endpoint.find_neighbors(
    deployed_index_id=deployed_index_id,
    queries=[query_embedding],
    num_neighbors=10
)
```

### Vertex AI Search

**What It Is:**
- **End-to-end enterprise search platform**
- Combines retrieval, ranking, and generative AI
- Built on Discovery Engine API

**Use Cases:**
- Enterprise knowledge bases
- Document search with answer generation
- Conversational search experiences
- E-commerce product search
- Healthcare record search

**Key Features:**
- Out-of-the-box NLP and ranking
- Multiple data store types (structured, unstructured, website)
- Generative AI summarization
- Blended search across data sources
- Self-learning from clickstream data

**Integration:**
- Gemini models (answer generation)
- BigQuery (data import)
- Cloud Storage (document storage)
- Cloud Healthcare API (FHIR data)

**Example:**
```python
from google.cloud import discoveryengine_v1

# Search with answer generation
search_request = discoveryengine_v1.SearchRequest(
    serving_config=SERVING_CONFIG,
    query="What is our return policy?",
    content_search_spec=discoveryengine_v1.SearchRequest.ContentSearchSpec(
        summary_spec=discoveryengine_v1.SearchRequest.ContentSearchSpec.SummarySpec(
            summary_result_count=5,
            include_citations=True
        )
    )
)

response = search_client.search(search_request)
print(response.summary.summary_text)  # Generative AI answer
print(response.results)  # Source documents
```

### Comparison Matrix

| Feature | Vector Search | Vertex AI Search |
|---------|---------------|------------------|
| **Primary Use** | Embedding-based similarity | Enterprise search + answer generation |
| **Complexity** | Requires embedding generation | Out-of-the-box search |
| **Data Types** | Embeddings (vectors) | Structured, unstructured, websites |
| **Answer Generation** | No (retrieval only) | Yes (Gemini integration) |
| **Ranking** | Similarity-based | Learned ranking + NLP |
| **Setup Time** | Manual embedding pipeline | Quick (hours to days) |
| **Best For** | Custom ML applications | Business users, rapid deployment |

### When to Use Each

**Use Vector Search When:**
- Building custom ML applications
- Need fine-grained control over embeddings
- Require ultra-low latency (< 10ms)
- Have existing embedding infrastructure
- Building recommendation engines

**Use Vertex AI Search When:**
- Need enterprise search quickly
- Want out-of-the-box NLP and ranking
- Require answer generation (RAG)
- Have non-technical users
- Need blended search across data types

**Use Both Together:**
- Vector Search for retrieval
- Vertex AI Search for ranking and summarization
- Best of both worlds: precision + ease of use

---

## Ray on Vertex AI Overview

### What is Ray?

**Ray** is an **open-source framework** for scaling AI and Python applications. Developed by UC Berkeley's RISELab (now maintained by Anyscale), Ray provides:

> "A unified framework for distributed computing and parallel processing essential for machine learning workflows."

**Core Value Proposition:**
- Scale from laptop to cluster with minimal code changes
- Unified API for diverse workloads (training, serving, data processing)
- Python-native with strong ecosystem support

### What is Ray on Vertex AI?

**Ray on Vertex AI** is a **fully managed Ray cluster service** that:
- Handles cluster lifecycle management (creation, scaling, deletion)
- Integrates with Google Cloud services (BigQuery, Vertex AI, Cloud Storage)
- Provides enterprise features (VPC support, monitoring, logging)
- Eliminates infrastructure management overhead

**Key Differentiator:**
> "Use the same open-source Ray code with minimal changes, and integrate with Google Cloud services."

---

## Ray Architecture and Components

### Cluster Architecture

```
Ray Cluster on Vertex AI
├── Head Node (1)
│   ├── Ray Driver (submits jobs)
│   ├── Global Control Store (GCS)
│   ├── Scheduler
│   └── Ray Dashboard
└── Worker Nodes (0-2,000)
    ├── Worker Pool 1 (e.g., CPU-optimized)
    ├── Worker Pool 2 (e.g., GPU-accelerated)
    └── Worker Pool 3 (e.g., memory-optimized)
```

### Key Components

#### 1. Head Node
- **Purpose:** Cluster coordination and job submission
- **Responsibilities:**
  - Job scheduling
  - Resource allocation
  - Metadata management
  - Dashboard hosting

#### 2. Worker Nodes
- **Purpose:** Execute distributed tasks and actors
- **Characteristics:**
  - Up to 2,000 nodes per cluster
  - Up to 1,000 nodes per worker pool
  - Heterogeneous machine types supported

#### 3. Worker Pools
- **Purpose:** Group workers by machine type/configuration
- **Use Cases:**
  - CPU-intensive tasks (n1-standard-16)
  - GPU-accelerated training (a2-highgpu-1g)
  - Memory-intensive processing (n1-highmem-32)

---

## Connectivity Models

### 1. Public Connectivity

**Description:** Direct internet access to Ray cluster

**Access Method:**
```python
from google.cloud import aiplatform

aiplatform.init(project=PROJECT_ID, location=LOCATION)

# Connect via Ray Client
ray.init(f"ray://{cluster_endpoint}:10001")
```

**Use Cases:**
- Rapid development and experimentation
- Notebooks (Colab, Jupyter)
- Local development environments

**Pros:**
- Simple setup
- No network configuration required
- Quick iterations

**Cons:**
- Less secure (internet-exposed)
- Not suitable for production with sensitive data

### 2. VPC Integration

**Description:** Private network connections through VPC peering

**Access Method:**
```python
# Connect from Compute Engine VM in same VPC
ray.init(f"ray://{private_ip}:10001")
```

**Use Cases:**
- Enterprise security requirements
- On-premises connectivity (Cloud Interconnect)
- Production workloads with compliance needs

**Pros:**
- Secure (no internet exposure)
- Low latency (private network)
- Fine-grained access control (IAM + VPC)

**Cons:**
- Requires VPC configuration
- More complex setup

---

## Key Features of Ray on Vertex AI

### 1. Persistent Resources

**Unlike standard training jobs:**
- Clusters remain active until explicitly deleted
- No startup overhead for subsequent jobs
- Data caching across runs

**Benefit:**
> "Reduces startup time for iterative work from minutes to seconds."

**Use Case:**
- Hyperparameter tuning (multiple runs)
- Experiment tracking
- Interactive development

**Example:**
```python
# Create persistent cluster
cluster = aiplatform.RayCluster.create(
    display_name="ml-experiments",
    head_node_type="n1-standard-4",
    worker_node_types=["n1-standard-8"],
    # Cluster stays active for multiple jobs
)

# Job 1: Training
ray.init(f"ray://{cluster.endpoint}:10001")
train_model()

# Job 2: Hyperparameter tuning (reuses cluster)
tune_hyperparameters()

# Job 3: Evaluation
evaluate_model()

# Delete when done
cluster.delete()
```

### 2. Autoscaling

**Description:** Automatic adjustment of worker nodes based on demand

**Modes:**
1. **Autoscaling (Recommended):** Automatic based on Ray task/actor resource requirements
2. **Manual Scaling:** Fixed number of workers

**Configuration:**
```python
cluster = aiplatform.RayCluster.create(
    display_name="autoscaling-cluster",
    head_node_type="n1-standard-4",
    worker_node_types=[{
        "machine_type": "n1-standard-8",
        "min_replica_count": 1,  # Minimum workers
        "max_replica_count": 50,  # Maximum workers
        "accelerator_type": None
    }]
)
```

**Cost Optimization:**
- Scale down to minimum during idle periods
- Scale up for burst workloads
- Pay only for actual usage

### 3. BigQuery Integration

**Native Support:**
- Read from BigQuery tables
- Write results back to BigQuery
- Transform data within Ray

**Example:**
```python
import vertex_ray

# Read from BigQuery
ds = vertex_ray.data.read_bigquery(
    dataset="project.dataset.table",
    parallelism=10,
    query="SELECT * FROM table WHERE date > '2025-01-01'"
)

# Transform data
ds = ds.map(lambda row: preprocess(row))

# Write back to BigQuery
vertex_ray.data.write_bigquery(
    ds,
    dataset="project.dataset.processed_table"
)
```

### 4. Model Deployment Integration

**Vertex AI Inference:**
```python
import ray
from ray import serve
from google.cloud import aiplatform

@serve.deployment
class MyModel:
    def __init__(self):
        self.model = load_model()

    def __call__(self, request):
        return self.model.predict(request.json())

# Deploy to Ray on Vertex AI
serve.run(MyModel.bind(), route_prefix="/predict")

# Export to Vertex AI Endpoint
endpoint = aiplatform.Endpoint.create(display_name="my-model")
endpoint.deploy(
    model=my_model,
    traffic_percentage=100,
    machine_type="n1-standard-4"
)
```

### 5. Monitoring and Logging

**Built-in Integration:**
- **Cloud Logging:** Automatic log ingestion
- **Cloud Monitoring:** Metrics and dashboards
- **Ray Dashboard:** Real-time cluster visualization

**Access Ray Dashboard:**
```bash
# Get cluster info
gcloud ai ray-clusters describe CLUSTER_NAME \
    --location=LOCATION \
    --format="value(rayDashboardUrl)"

# Open in browser (requires authentication)
```

**Monitoring Metrics:**
- CPU/GPU utilization
- Memory usage
- Task throughput
- Queue depths
- Node health

---

## Distributed ML Workloads with Ray

### Use Cases

Ray on Vertex AI excels for:
1. **Repeated Jobs:** Leverage data caching
2. **Short-Lived Tasks:** Avoid startup overhead
3. **Large-Scale Training:** Distributed data parallelism
4. **Hyperparameter Tuning:** Parallel experiment execution
5. **Batch Inference:** Distribute prediction workload

---

## Common ML Workloads

### 1. Distributed Training with Ray Train

**XGBoost Example:**
```python
import ray
from ray import train
from ray.train.xgboost import XGBoostTrainer
from ray.train import ScalingConfig

# Define training function
def train_xgboost(config):
    import xgboost as xgb

    # Load data
    train_dataset = train.get_dataset_shard("train")

    # Train model
    dtrain = xgb.DMatrix(train_dataset.to_pandas())
    booster = xgb.train(
        params=config,
        dtrain=dtrain,
        num_boost_round=100
    )

    return booster

# Distributed training
trainer = XGBoostTrainer(
    train_loop_per_worker=train_xgboost,
    scaling_config=ScalingConfig(
        num_workers=4,
        use_gpu=False
    ),
    datasets={"train": ray.data.read_parquet("gs://bucket/train.parquet")},
    params={"max_depth": 5, "eta": 0.1}
)

result = trainer.fit()
```

**PyTorch Distributed Training:**
```python
import ray
from ray import train
from ray.train.torch import TorchTrainer
from ray.train import ScalingConfig
import torch
import torch.nn as nn

def train_func(config):
    model = nn.Linear(10, 1)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # Ray handles distribution automatically
    model = train.torch.prepare_model(model)

    for epoch in range(10):
        # Training loop
        loss = train_epoch(model, optimizer)
        train.report({"loss": loss})

trainer = TorchTrainer(
    train_loop_per_worker=train_func,
    scaling_config=ScalingConfig(
        num_workers=8,
        use_gpu=True,
        resources_per_worker={"GPU": 1}
    )
)

result = trainer.fit()
```

### 2. Hyperparameter Tuning with Ray Tune

**Parallel Experiments:**
```python
from ray import tune
from ray.tune.schedulers import ASHAScheduler

def objective(config):
    # Train model with config
    score = train_and_evaluate(config)
    return {"score": score}

# Define search space
config = {
    "learning_rate": tune.loguniform(1e-5, 1e-1),
    "batch_size": tune.choice([16, 32, 64, 128]),
    "hidden_layers": tune.randint(1, 5),
    "dropout": tune.uniform(0.1, 0.5)
}

# Run parallel tuning
analysis = tune.run(
    objective,
    config=config,
    num_samples=100,  # 100 different configurations
    scheduler=ASHAScheduler(metric="score", mode="max"),
    resources_per_trial={"cpu": 2, "gpu": 0}
)

print(f"Best config: {analysis.best_config}")
```

### 3. Fine-Tuning Gemma with Ray Train

**HuggingFace Transformers:**
```python
import ray
from ray.train.huggingface import TransformersTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer

def train_func():
    model = AutoModelForCausalLM.from_pretrained("google/gemma-2b-it")
    tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b-it")

    # Training loop
    for epoch in range(3):
        train_epoch(model, tokenizer, train_dataset)

    return model

trainer = TransformersTrainer(
    train_loop_per_worker=train_func,
    scaling_config=ScalingConfig(
        num_workers=4,
        use_gpu=True,
        resources_per_worker={"GPU": 1, "CPU": 4}
    )
)

result = trainer.fit()
```

### 4. Batch Inference at Scale

**Distributed Prediction:**
```python
import ray

@ray.remote
def predict_batch(model, batch):
    return model.predict(batch)

# Load model once per worker
@ray.remote
class ModelServer:
    def __init__(self):
        self.model = load_model()

    def predict(self, batch):
        return self.model.predict(batch)

# Create model servers
servers = [ModelServer.remote() for _ in range(10)]

# Distribute inference
batches = ray.data.read_parquet("gs://bucket/inference_data.parquet") \
    .repartition(100)

predictions = batches.map_batches(
    lambda batch: servers[hash(batch) % 10].predict.remote(batch)
)

predictions.write_parquet("gs://bucket/predictions.parquet")
```

---

## BigQuery Integration with Ray

### Reading from BigQuery

**Basic Read:**
```python
import vertex_ray

# Read entire table
ds = vertex_ray.data.read_bigquery(
    dataset="project.dataset.table",
    parallelism=20  # 20 parallel read tasks
)

# Read with SQL query
ds = vertex_ray.data.read_bigquery(
    dataset="project.dataset.table",
    parallelism=10,
    query="""
        SELECT user_id, features, label
        FROM `project.dataset.table`
        WHERE date >= '2025-01-01'
        AND label IS NOT NULL
    """
)

# Materialize data (load into memory/distributed storage)
ds.materialize()
```

### Writing to BigQuery

**Basic Write:**
```python
# Write Ray dataset back to BigQuery
vertex_ray.data.write_bigquery(
    ds,
    dataset="project.dataset.output_table"
)
```

### End-to-End ML Pipeline with BigQuery

**Chicago Taxi Tips Prediction:**
```python
import ray
import vertex_ray
from ray import train
from ray.train.xgboost import XGBoostTrainer

@ray.remote
def preprocess(batch):
    # Feature engineering
    batch['trip_miles_per_minute'] = batch['trip_miles'] / batch['trip_seconds'] * 60
    batch['fare_per_mile'] = batch['fare'] / batch['trip_miles']
    return batch

# 1. Read from BigQuery (public dataset)
ds = vertex_ray.data.read_bigquery(
    dataset="bigquery-public-data.chicago_taxi_trips.taxi_trips",
    parallelism=50,
    query="""
        SELECT
            trip_miles,
            trip_seconds,
            fare,
            tips,
            payment_type,
            company
        FROM `bigquery-public-data.chicago_taxi_trips.taxi_trips`
        WHERE trip_miles > 0
          AND trip_seconds > 0
          AND fare > 0
          AND tips >= 0
        LIMIT 1000000
    """
)

# 2. Preprocess data
ds = ds.map_batches(preprocess, batch_format="pandas")

# 3. Train/test split
train_ds, test_ds = ds.train_test_split(test_size=0.2)

# 4. Train XGBoost model
trainer = XGBoostTrainer(
    scaling_config=train.ScalingConfig(num_workers=10),
    label_column="tips",
    params={"max_depth": 6, "eta": 0.3},
    datasets={"train": train_ds, "test": test_ds}
)

result = trainer.fit()

# 5. Batch inference
predictions = test_ds.map_batches(
    lambda batch: result.checkpoint.get_model().predict(batch),
    batch_format="pandas"
)

# 6. Write predictions back to BigQuery
vertex_ray.data.write_bigquery(
    predictions,
    dataset="project.my_dataset.taxi_tips_predictions"
)
```

### Advanced: Data Transformation Pipeline

**Multi-Stage ETL:**
```python
import ray
import vertex_ray

# Read raw data
raw_ds = vertex_ray.data.read_bigquery(
    dataset="project.raw_data.events",
    parallelism=100
)

# Stage 1: Clean data
cleaned_ds = raw_ds.map_batches(
    lambda batch: batch.dropna(),
    batch_format="pandas"
)

# Stage 2: Feature engineering
features_ds = cleaned_ds.map_batches(
    lambda batch: engineer_features(batch),
    batch_format="pandas"
)

# Stage 3: Aggregate
aggregated_ds = features_ds.groupby("user_id").map_groups(
    lambda group: aggregate_user_features(group),
    batch_format="pandas"
)

# Stage 4: Write to BigQuery
vertex_ray.data.write_bigquery(
    aggregated_ds,
    dataset="project.processed_data.user_features"
)
```

---

## Production Deployment Patterns

### Pattern 1: Development → Staging → Production

**Development (Small Cluster):**
```python
dev_cluster = aiplatform.RayCluster.create(
    display_name="dev-cluster",
    head_node_type="n1-standard-4",
    worker_node_types=[{
        "machine_type": "n1-standard-4",
        "min_replica_count": 1,
        "max_replica_count": 5
    }],
    labels={"env": "development"}
)
```

**Staging (Medium Cluster):**
```python
staging_cluster = aiplatform.RayCluster.create(
    display_name="staging-cluster",
    head_node_type="n1-standard-8",
    worker_node_types=[{
        "machine_type": "n1-standard-16",
        "min_replica_count": 5,
        "max_replica_count": 20
    }],
    labels={"env": "staging"}
)
```

**Production (Large Cluster with GPU):**
```python
prod_cluster = aiplatform.RayCluster.create(
    display_name="prod-cluster",
    head_node_type="n1-standard-16",
    worker_node_types=[
        {
            "machine_type": "n1-highmem-32",
            "min_replica_count": 10,
            "max_replica_count": 100,
            "accelerator_type": None
        },
        {
            "machine_type": "a2-highgpu-1g",
            "min_replica_count": 2,
            "max_replica_count": 20,
            "accelerator_type": "NVIDIA_TESLA_A100"
        }
    ],
    labels={"env": "production"}
)
```

### Pattern 2: Ephemeral Clusters for Batch Jobs

**Create → Run → Delete:**
```python
def run_batch_job(data_path, output_path):
    # Create cluster
    cluster = aiplatform.RayCluster.create(
        display_name=f"batch-job-{timestamp}",
        head_node_type="n1-standard-8",
        worker_node_types=[{
            "machine_type": "n1-standard-16",
            "min_replica_count": 10,
            "max_replica_count": 50
        }]
    )

    try:
        # Run job
        ray.init(f"ray://{cluster.endpoint}:10001")
        result = process_data(data_path)
        save_results(result, output_path)
    finally:
        # Always clean up
        cluster.delete()
```

### Pattern 3: Persistent Cluster with Job Scheduling

**Long-Running Cluster:**
```python
# Create persistent cluster once
cluster = aiplatform.RayCluster.create(
    display_name="ml-platform",
    head_node_type="n1-standard-16",
    worker_node_types=[{
        "machine_type": "n1-standard-32",
        "min_replica_count": 5,
        "max_replica_count": 100
    }]
)

# Submit jobs throughout the day
def submit_training_job(config):
    ray.init(f"ray://{cluster.endpoint}:10001", ignore_reinit_error=True)

    result = train_model(config)

    # Don't disconnect - reuse connection
    return result

# Schedule jobs
for config in experiment_configs:
    result = submit_training_job(config)
    log_result(result)

# Delete at end of day (or keep for next day)
# cluster.delete()
```

---

## Cost Optimization Strategies

### 1. Autoscaling Configuration

**Aggressive Autoscaling (Cost-Optimized):**
```python
cluster = aiplatform.RayCluster.create(
    display_name="cost-optimized",
    worker_node_types=[{
        "machine_type": "n1-standard-8",
        "min_replica_count": 0,  # Scale to zero when idle
        "max_replica_count": 50,
        "idle_timeout": "300s"  # 5 minutes idle before scale-down
    }]
)
```

### 2. Spot/Preemptible Instances

**Use Preemptible VMs for Worker Nodes:**
```python
cluster = aiplatform.RayCluster.create(
    display_name="spot-cluster",
    worker_node_types=[{
        "machine_type": "n1-standard-16",
        "min_replica_count": 5,
        "max_replica_count": 50,
        "preemptible": True  # Up to 80% cost savings
    }]
)
```

### 3. Right-Sizing Machine Types

**Match Workload to Resources:**
- **CPU-bound:** n1-standard, n1-highcpu
- **Memory-bound:** n1-highmem, n2-highmem
- **GPU training:** a2-highgpu, g2-standard
- **Inference:** n1-standard (CPU) or t4 (GPU)

### 4. Data Caching

**Reuse Preprocessed Data:**
```python
# Cache preprocessed data in Ray object store
@ray.remote
def preprocess_data(path):
    return load_and_preprocess(path)

# Preprocess once
preprocessed_ref = preprocess_data.remote("gs://bucket/data.parquet")

# Reuse across multiple experiments
for config in configs:
    train_model(ray.get(preprocessed_ref), config)
```

---

## Related jeremy-* Plugins

### jeremy-vertex-engine
- Vertex AI Agent Engine integration
- RAG implementations with Vertex AI Search
- Gemini model deployment

### jeremy-vertex-validator
- Validate Vertex AI Search configurations
- Check Ray cluster health
- Production readiness validation

### jeremy-genkit-pro
- Firebase Genkit integration with Vertex AI Search
- RAG application templates
- Gemini API integration

### jeremy-vertex-terraform
- Terraform infrastructure for Vertex AI Search
- Ray cluster provisioning as code
- Automated deployment pipelines

### jeremy-bigquery-ops
- BigQuery data preparation for Vertex AI Search
- Ray + BigQuery pipeline automation
- Data quality validation

---

## Quick Reference

### Vertex AI Search

**Create Data Store:**
```bash
gcloud alpha discovery-engine data-stores create my-datastore \
    --location=global \
    --industry-vertical=GENERIC \
    --content-config=CONTENT_REQUIRED
```

**Search Query:**
```python
from google.cloud import discoveryengine_v1

response = search_client.search(
    discoveryengine_v1.SearchRequest(
        serving_config=SERVING_CONFIG,
        query="user query here",
        page_size=10
    )
)
```

### Ray on Vertex AI

**Create Cluster:**
```python
cluster = aiplatform.RayCluster.create(
    display_name="my-cluster",
    head_node_type="n1-standard-4",
    worker_node_types=[{"machine_type": "n1-standard-8", "max_replica_count": 10}]
)
```

**Connect to Cluster:**
```python
ray.init(f"ray://{cluster.endpoint}:10001")
```

**Read from BigQuery:**
```python
ds = vertex_ray.data.read_bigquery(dataset="project.dataset.table", parallelism=10)
```

---

**Documentation Version:** November 2025
**Last Updated:** 2025-11-13
**Status:** Production-Ready Reference
**Coverage:** Vertex AI Search, Vector Search, Ray on Vertex AI, RAG, BigQuery Integration
