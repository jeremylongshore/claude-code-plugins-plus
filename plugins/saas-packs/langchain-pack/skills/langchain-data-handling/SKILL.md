---
name: langchain-data-handling
description: |
  Implement LangChain RAG pipelines with document loaders, text splitters,
  embeddings, and vector stores (Chroma, Pinecone, FAISS).
  Trigger: "langchain RAG", "langchain documents", "langchain vector store",
  "langchain embeddings", "document loaders", "text splitters", "retrieval".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, llm, rag, vector-store]

---
# LangChain Data Handling: RAG & Document Processing

## Overview

Build Retrieval-Augmented Generation (RAG) pipelines: load documents, split into chunks, embed with OpenAI/Cohere, store in vector databases (FAISS, Chroma, Pinecone), and query with retrieval chains.

## Prerequisites

- `@langchain/core`, `@langchain/openai` installed
- For vector stores: `npm install @langchain/community` (FAISS) or `npm install @langchain/pinecone @pinecone-database/pinecone`

## Step 1: Document Loaders

```typescript
import { TextLoader } from "langchain/document_loaders/fs/text";
import { PDFLoader } from "@langchain/community/document_loaders/fs/pdf";
import { DirectoryLoader } from "langchain/document_loaders/fs/directory";
import { CSVLoader } from "@langchain/community/document_loaders/fs/csv";

// Load a single file
const textDocs = await new TextLoader("./data/readme.md").load();
const pdfDocs = await new PDFLoader("./data/manual.pdf").load();

// Load entire directory with type-based routing
const dirLoader = new DirectoryLoader("./data/", {
  ".txt": (path) => new TextLoader(path),
  ".pdf": (path) => new PDFLoader(path),
  ".csv": (path) => new CSVLoader(path),
});
const allDocs = await dirLoader.load();
console.log(`Loaded ${allDocs.length} documents`);
```

## Step 2: Text Splitting

```typescript
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";

const splitter = new RecursiveCharacterTextSplitter({
  chunkSize: 1000,       // max chars per chunk
  chunkOverlap: 200,     // overlap between chunks for context continuity
  separators: ["\n\n", "\n", ". ", " ", ""],  // split priority
});

const chunks = await splitter.splitDocuments(allDocs);
console.log(`Split into ${chunks.length} chunks`);

// Each chunk preserves metadata from the source document
// chunk.pageContent = "text content"
// chunk.metadata = { source: "./data/readme.md", loc: { lines: { from: 1, to: 20 } } }
```

## Step 3: Embeddings

```typescript
import { OpenAIEmbeddings } from "@langchain/openai";

const embeddings = new OpenAIEmbeddings({
  model: "text-embedding-3-small",   // $0.02/1M tokens, 1536 dims
  // model: "text-embedding-3-large", // $0.13/1M tokens, 3072 dims
});

// Embed a single query
const queryVector = await embeddings.embedQuery("What is LCEL?");
console.log(`Vector dimensions: ${queryVector.length}`); // 1536

// Embed multiple documents
const docVectors = await embeddings.embedDocuments([
  "LCEL is LangChain Expression Language",
  "Runnables are composable components",
]);
```

## Step 4: Vector Store (FAISS - Local)

```typescript
import { FaissStore } from "@langchain/community/vectorstores/faiss";
import { OpenAIEmbeddings } from "@langchain/openai";

const embeddings = new OpenAIEmbeddings({ model: "text-embedding-3-small" });

// Create from documents
const vectorStore = await FaissStore.fromDocuments(chunks, embeddings);

// Save to disk for reuse
await vectorStore.save("./faiss-index");

// Load from disk
const loaded = await FaissStore.load("./faiss-index", embeddings);

// Similarity search
const results = await loaded.similaritySearch("How do agents work?", 3);
results.forEach((doc) => {
  console.log(`[${doc.metadata.source}] ${doc.pageContent.slice(0, 100)}...`);
});
```

## Step 5: Vector Store (Pinecone - Cloud)

```typescript
import { PineconeStore } from "@langchain/pinecone";
import { Pinecone } from "@pinecone-database/pinecone";
import { OpenAIEmbeddings } from "@langchain/openai";

const pinecone = new Pinecone(); // reads PINECONE_API_KEY from env
const index = pinecone.Index("my-index");

const embeddings = new OpenAIEmbeddings({ model: "text-embedding-3-small" });

// Upsert documents
const vectorStore = await PineconeStore.fromDocuments(chunks, embeddings, {
  pineconeIndex: index,
  namespace: "docs-v1",
});

// Query with metadata filtering
const results = await vectorStore.similaritySearch("deployment guide", 5, {
  source: { $eq: "manual.pdf" },
});
```

## Step 6: RAG Chain (Full Pipeline)

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnablePassthrough, RunnableSequence } from "@langchain/core/runnables";

const model = new ChatOpenAI({ model: "gpt-4o-mini" });
const retriever = vectorStore.asRetriever({ k: 4 });

const ragPrompt = ChatPromptTemplate.fromTemplate(`
Answer the question based only on the following context.
If the answer is not in the context, say "I don't have that information."

Context:
{context}

Question: {question}

Answer:`);

// Format retrieved docs into a single string
function formatDocs(docs: any[]) {
  return docs.map((d) => d.pageContent).join("\n\n");
}

const ragChain = RunnableSequence.from([
  {
    context: retriever.pipe(formatDocs),
    question: new RunnablePassthrough(),
  },
  ragPrompt,
  model,
  new StringOutputParser(),
]);

const answer = await ragChain.invoke("How do I deploy to production?");
console.log(answer);
```

## Python RAG Equivalent

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load + split
docs = TextLoader("./data/readme.md").load()
chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)

# Embed + store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
store = FAISS.from_documents(chunks, embeddings)
retriever = store.as_retriever(search_kwargs={"k": 4})

# RAG chain
prompt = ChatPromptTemplate.from_template("Context:\n{context}\n\nQuestion: {question}")
chain = (
    {"context": retriever | (lambda docs: "\n\n".join(d.page_content for d in docs)),
     "question": RunnablePassthrough()}
    | prompt
    | ChatOpenAI(model="gpt-4o-mini")
    | StrOutputParser()
)

answer = chain.invoke("How do I deploy?")
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `FAISS index not found` | Index not saved/wrong path | Call `vectorStore.save()` first |
| `Dimension mismatch` | Embedding model changed | Rebuild index with same model |
| `Pinecone 404` | Index doesn't exist | Create index in Pinecone console |
| Empty retrieval results | Chunks too large or query too vague | Reduce `chunkSize`, improve query |

## Resources

- [RAG Tutorial](https://js.langchain.com/docs/tutorials/rag/)
- [Document Loaders](https://js.langchain.com/docs/integrations/document_loaders/)
- [Vector Stores](https://js.langchain.com/docs/integrations/vectorstores/)
- [Text Splitters](https://js.langchain.com/docs/how_to/recursive_text_splitter/)

## Next Steps

Use `langchain-security-basics` for securing your RAG pipeline.
