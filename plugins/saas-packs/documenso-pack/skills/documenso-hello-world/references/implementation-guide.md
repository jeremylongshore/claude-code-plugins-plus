# Documenso Hello World - Implementation Guide

# Documenso Hello World

## Overview
Minimal working example demonstrating core Documenso document signing functionality.

## Prerequisites
- Completed `documenso-install-auth` setup
- Valid API credentials configured
- A PDF file to upload (or use built-in test)

## Instructions

### Step 1: Create Entry File

Create a new file `documenso-hello.ts` (or `.py` for Python).

### Step 2: Create Your First Document

**TypeScript:**
```typescript
import { Documenso } from "@documenso/sdk-typescript";
import { openAsBlob } from "node:fs";

const documenso = new Documenso({
  apiKey: process.env.DOCUMENSO_API_KEY ?? "",
});

async function createFirstDocument() {
  // Create a document with a title
  const document = await documenso.documents.createV0({
    title: "My First Document",
  });

  console.log("Document created!");
  console.log(`Document ID: ${document.documentId}`);
  console.log(`Status: Draft`);

  return document;
}

createFirstDocument().catch(console.error);
```

### Step 3: Upload PDF and Add Recipient

**TypeScript (Complete Example):**
```typescript
import { Documenso } from "@documenso/sdk-typescript";
import { openAsBlob } from "node:fs";

const documenso = new Documenso({
  apiKey: process.env.DOCUMENSO_API_KEY ?? "",
});

async function createAndSendDocument() {
  // Step 1: Create document with PDF upload
  const pdfBlob = await openAsBlob("./contract.pdf");

  const document = await documenso.documents.createV0({
    title: "Contract Agreement",
    file: pdfBlob,
  });

  console.log(`Created document: ${document.documentId}`);

  // Step 2: Add a recipient (signer)
  const recipient = await documenso.documentsRecipients.createV0({
    documentId: document.documentId!,
    email: "signer@example.com",
    name: "John Doe",
    role: "SIGNER",
  });

  console.log(`Added recipient: ${recipient.recipientId}`);

  // Step 3: Add signature field
  await documenso.documentsFields.createV0({
    documentId: document.documentId!,
    recipientId: recipient.recipientId!,
    type: "SIGNATURE",
    page: 1,
    positionX: 100,
    positionY: 600,
    width: 200,
    height: 60,
  });

  console.log("Added signature field");

  // Step 4: Send for signing
  await documenso.documents.sendV0({
    documentId: document.documentId!,
  });

  console.log("Document sent for signing!");
  console.log(`Recipient will receive email at: signer@example.com`);

  return document;
}

createAndSendDocument().catch(console.error);
```

### Python Example

```python
import os
from documenso_sdk import Documenso

documenso = Documenso(api_key=os.environ.get("DOCUMENSO_API_KEY"))

def create_and_send_document():
    # Step 1: Create document
    with open("./contract.pdf", "rb") as f:
        pdf_content = f.read()

    document = documenso.documents.create_v0(
        title="Contract Agreement",
        file=pdf_content,
    )
    print(f"Created document: {document.document_id}")

    # Step 2: Add recipient
    recipient = documenso.documents_recipients.create_v0(
        document_id=document.document_id,
        email="signer@example.com",
        name="John Doe",
        role="SIGNER",
    )
    print(f"Added recipient: {recipient.recipient_id}")

    # Step 3: Add signature field
    documenso.documents_fields.create_v0(
        document_id=document.document_id,
        recipient_id=recipient.recipient_id,
        type="SIGNATURE",
        page=1,
        position_x=100,
        position_y=600,
        width=200,
        height=60,
    )
    print("Added signature field")

    # Step 4: Send for signing
    documenso.documents.send_v0(document_id=document.document_id)
    print("Document sent for signing!")

    return document

if __name__ == "__main__":
    create_and_send_document()
```

## Output
- Working code file with Documenso client initialization
- Created document in Documenso dashboard
- Recipient added with signature field
- Email sent to recipient for signing
- Console output showing:
```
Created document: doc_abc123
Added recipient: rec_xyz789
Added signature field
Document sent for signing!
Recipient will receive email at: signer@example.com
```

## Field Types Available

| Type | Description |
|------|-------------|
| `SIGNATURE` | Electronic signature |
| `INITIALS` | Initials field |
| `NAME` | Full name |
| `EMAIL` | Email address |
| `DATE` | Date field |
| `TEXT` | Free text input |
| `NUMBER` | Number input |
| `CHECKBOX` | Checkbox/Boolean |
| `DROPDOWN` | Dropdown selection |
| `RADIO` | Radio button group |

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Verify with `npm list @documenso/sdk-typescript` |
| Auth Error | Invalid credentials | Check environment variable is set |
| File Not Found | PDF path incorrect | Verify PDF file exists |
| Invalid Field Position | Coordinates off page | Check page dimensions |
| Recipient Exists | Duplicate email | Use existing recipient or update |

## Resources
- [Documenso Getting Started](https://docs.documenso.com/developers)
- [API Reference](https://openapi.documenso.com/)
- [Document Operations](https://github.com/documenso/sdk-typescript/blob/main/docs/sdks/documents/README.md)

## Next Steps
Proceed to `documenso-local-dev-loop` for development workflow setup.
