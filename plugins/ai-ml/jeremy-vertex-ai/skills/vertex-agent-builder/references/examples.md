# Vertex AI Agent Builder -- Usage Examples

## Example 1: RAG Support Bot with Document Ingestion and Citation

**Scenario**: Deploy an internal support agent that answers questions from company documentation stored in GCS, with every answer citing its source.

**Request**: "Build a support bot that answers from our docs in `gs://acme-docs/` with citations."

**Agent code** (`agent.py`):
```python
import vertexai
from vertexai.generative_models import GenerativeModel, Tool
from vertexai.preview import rag

vertexai.init(project="acme-prod", location="us-central1")

rag_resource = rag.RagResource(
    rag_corpus="projects/acme-prod/locations/us-central1/ragCorpora/support-corpus",
)
rag_retrieval_tool = Tool.from_retrieval(
    retrieval=rag.Retrieval(
        source=rag.VertexRagStore(rag_resources=[rag_resource], similarity_top_k=5),
    )
)

model = GenerativeModel(
    "gemini-2.0-flash",
    tools=[rag_retrieval_tool],
    system_instruction=(
        "You are a support agent. Answer questions using ONLY the retrieved documents. "
        "Cite the source document for every claim. If no relevant document is found, "
        "say 'I don't have information on that topic.'"
    ),
)

chat = model.start_chat()
response = chat.send_message("How do I reset my API key?")
print(response.text)
```

**Document ingestion** (`rag_config.py`):
```python
from vertexai.preview import rag

corpus = rag.create_corpus(display_name="support-corpus")
rag.import_files(
    corpus.name,
    paths=["gs://acme-docs/"],
    chunk_size=512,
    chunk_overlap=100,
    transformation_config=rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100),
    ),
)
```

---

## Example 2: Multimodal Extraction Agent for PDFs and Images

**Scenario**: Build an agent that extracts structured fields (invoice number, date, total, line items) from uploaded PDFs and images.

**Request**: "Build an extraction agent that pulls structured data from invoices in PDF and image format."

**Agent code**:
```python
import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
import json

vertexai.init(project="acme-prod", location="us-central1")

model = GenerativeModel(
    "gemini-2.5-pro",
    system_instruction=(
        "Extract structured invoice data from the provided document. "
        "Return valid JSON with fields: invoice_number, date, vendor, "
        "line_items (array of {description, quantity, unit_price, total}), "
        "subtotal, tax, grand_total. If a field is unreadable, set it to null."
    ),
    generation_config=GenerationConfig(
        response_mime_type="application/json",
        temperature=0.1,
    ),
)

# Process a PDF
pdf_part = Part.from_uri("gs://acme-invoices/inv-2026-001.pdf", mime_type="application/pdf")
response = model.generate_content([pdf_part, "Extract all invoice fields."])
invoice_data = json.loads(response.text)

# Process an image
image_part = Part.from_uri("gs://acme-invoices/receipt-photo.jpg", mime_type="image/jpeg")
response = model.generate_content([image_part, "Extract all invoice fields."])
```

**Output**: Structured JSON with `invoice_number`, `date`, `vendor`, `line_items` (array), `subtotal`, `tax`, `grand_total`. Unreadable fields set to `null`.

---

## Example 3: Function Calling with External APIs

**Scenario**: Set up an agent that checks order status, updates shipping, and sends notifications using function calling.

**Request**: "Build an agent with function calling for our order management API."

**Function declarations**:
```python
from vertexai.generative_models import (
    GenerativeModel, Tool, FunctionDeclaration,
)
import vertexai

vertexai.init(project="acme-prod", location="us-central1")

get_order = FunctionDeclaration(
    name="get_order_status",
    description="Look up the current status of a customer order by order ID.",
    parameters={
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "The order ID (e.g., ORD-12345)"},
        },
        "required": ["order_id"],
    },
)

update_shipping = FunctionDeclaration(
    name="update_shipping_address",
    description="Update the shipping address for an order that has not yet shipped.",
    parameters={
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "The order ID"},
            "address": {"type": "string", "description": "Full new shipping address"},
        },
        "required": ["order_id", "address"],
    },
)

order_tools = Tool(function_declarations=[get_order, update_shipping])
model = GenerativeModel("gemini-2.0-flash", tools=[order_tools])
chat = model.start_chat()

# Agent calls functions automatically; handle responses in a loop
response = chat.send_message("What's the status of order ORD-78901?")
for candidate in response.candidates:
    for part in candidate.content.parts:
        if part.function_call:
            # Route to your backend, return result
            result = call_order_api(part.function_call.name, part.function_call.args)
            response = chat.send_message(Part.from_function_response(
                name=part.function_call.name, response={"result": result}
            ))
```

---

## Example 4: Cost Guardrails and Monitoring

**Scenario**: Configure an existing agent with cost controls, usage monitoring, and alerting.

**Request**: "Add cost guardrails to my Vertex AI agent so we don't exceed $500/month."

**Token budget configuration**:
```python
from vertexai.generative_models import GenerativeModel, GenerationConfig

model = GenerativeModel(
    "gemini-2.0-flash",  # Flash first: ~$0.10/1M input tokens vs ~$1.25 for pro
    generation_config=GenerationConfig(
        max_output_tokens=1024,     # Cap per-response generation
        temperature=0.3,            # Lower temperature = fewer retries from bad output
    ),
)
```

**Budget alert**:
```bash
gcloud billing budgets create \
  --billing-account=BILLING_ACCT_ID \
  --display-name="vertex-ai-agent-budget" \
  --budget-amount=500 \
  --threshold-rule=percent=0.8,basis=CURRENT_SPEND \
  --threshold-rule=percent=1.0,basis=CURRENT_SPEND \
  --notifications-rule-pubsub-topic=projects/acme-prod/topics/billing-alerts
```

**Cost estimation** (per-query):
```
gemini-2.0-flash: ~$0.00028/query  ($500 budget = ~1.78M queries/month)
gemini-2.5-pro:   ~$0.00600/query  ($500 budget = ~83K queries/month)
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
