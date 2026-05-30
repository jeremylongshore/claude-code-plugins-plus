# Documenso SDK Patterns -- Implementation Reference

## Overview

Production-ready patterns for the Documenso API and SDK: document creation,
signer management, webhook handling, and status polling.

## Prerequisites

- Documenso API key (from Settings > API Keys)
- Python 3.9+ or Node.js 18+
- Documenso self-hosted or cloud instance

## Python Client Setup

```python
import os
import json
import urllib.request
import urllib.error
from typing import Any

DOCUMENSO_API_KEY = os.environ["DOCUMENSO_API_KEY"]
DOCUMENSO_BASE_URL = os.environ.get("DOCUMENSO_BASE_URL", "https://app.documenso.com")

def documenso_request(method: str, path: str, payload: dict = None) -> Any:
    headers = {
        "Authorization": f"Bearer {DOCUMENSO_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f"{DOCUMENSO_BASE_URL}/api/v1{path}",
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = json.loads(e.read() or b"{}")
        raise RuntimeError(f"Documenso API error {e.code}: {detail}")
```

## Create and Send Document

```python
import base64

def create_and_send_document(
    title: str,
    pdf_path: str,
    signers: list,
) -> dict:
    """
    Create a document and request signatures.

    signers: list of {"name": str, "email": str, "role": "SIGNER"|"CC"}
    """
    # 1. Read PDF bytes and base64-encode
    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode()

    # 2. Create document
    doc = documenso_request("POST", "/documents", {
        "title": title,
        "documentData": {
            "data": pdf_b64,
            "type": "BYTES_64",
        },
    })
    doc_id = doc["id"]
    print(f"Created document: {doc_id}")

    # 3. Add recipients
    for signer in signers:
        documenso_request("POST", f"/documents/{doc_id}/recipients", {
            "name": signer["name"],
            "email": signer["email"],
            "role": signer.get("role", "SIGNER"),
        })
        print(f"Added recipient: {signer['email']}")

    # 4. Send for signing
    result = documenso_request("POST", f"/documents/{doc_id}/send", {
        "sendEmail": True,
    })
    print(f"Document sent for signing")
    return result

# Usage
create_and_send_document(
    title="Service Agreement",
    pdf_path="contract.pdf",
    signers=[
        {"name": "Alice Smith", "email": "alice@example.com", "role": "SIGNER"},
        {"name": "Bob Jones", "email": "bob@example.com", "role": "CC"},
    ],
)
```

## Status Polling

```python
import time

def wait_for_completion(doc_id: str, timeout: int = 3600, interval: int = 30) -> dict:
    """Poll document status until all parties have signed or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        doc = documenso_request("GET", f"/documents/{doc_id}")
        status = doc.get("status")
        print(f"Document {doc_id} status: {status}")

        if status == "COMPLETED":
            return doc
        if status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"Document {doc_id} ended with status: {status}")

        time.sleep(interval)

    raise TimeoutError(f"Document {doc_id} did not complete within {timeout}s")

def get_signed_pdf(doc_id: str, output_path: str) -> None:
    """Download the completed signed document."""
    result = documenso_request("GET", f"/documents/{doc_id}/download")
    url = result.get("downloadUrl")
    if not url:
        raise ValueError(f"No download URL for document {doc_id}")

    with urllib.request.urlopen(url) as resp:
        with open(output_path, "wb") as f:
            f.write(resp.read())
    print(f"Saved signed document to {output_path}")
```

## TypeScript / Node.js SDK Pattern

```typescript
import fetch from 'node-fetch';

const BASE_URL = process.env.DOCUMENSO_BASE_URL || 'https://app.documenso.com';
const API_KEY = process.env.DOCUMENSO_API_KEY!;

async function documensoRequest<T>(method: string, path: string, body?: object): Promise<T> {
    const response = await fetch(`${BASE_URL}/api/v1${path}`, {
        method,
        headers: {
            Authorization: `Bearer ${API_KEY}`,
            'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(`Documenso ${response.status}: ${JSON.stringify(detail)}`);
    }

    return response.json() as Promise<T>;
}

async function listDocuments(status?: string) {
    const params = status ? `?status=${status}` : '';
    return documensoRequest<{ documents: any[] }>('GET', `/documents${params}`);
}

async function voidDocument(docId: string, reason: string) {
    return documensoRequest('DELETE', `/documents/${docId}`, { reason });
}
```

## Webhook Handler

```python
import hashlib
import hmac

WEBHOOK_SECRET = os.environ["DOCUMENSO_WEBHOOK_SECRET"]

def verify_documenso_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

# FastAPI example
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/documenso/webhook")
async def handle_webhook(
    request: Request,
    x_documenso_signature: str = Header(None),
):
    payload = await request.body()
    if not x_documenso_signature or not verify_documenso_signature(payload, x_documenso_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = json.loads(payload)
    event_type = event.get("event")

    if event_type == "document.completed":
        doc_id = event["payload"]["id"]
        print(f"Document completed: {doc_id}")

    return JSONResponse({"status": "ok"})
```

## Resources

- Documenso API Docs
- [Documenso GitHub](https://github.com/documenso/documenso)
- [Documenso Webhooks](https://docs.documenso.com/developers/webhooks)

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
