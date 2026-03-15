# Legal RAG System with AWS Services

## Project Overview

A Legal RAG (Retrieval-Augmented Generation) system with two core pipelines:
1. **Document Ingestion Pipeline** — Upload, process, embed, and store legal documents
2. **Query Pipeline** — Chat interface for querying legal documents with re-ranking and LLM response generation

All AWS infrastructure (S3, Bedrock, OpenSearch) is provisioned automatically via IAM credentials and AWS CLI.

---

## Architecture

```
Pipeline 1: Document Ingestion
┌──────────┐    ┌────────┐    ┌─────────────────┐    ┌──────────────┐    ┌────────────┐
│  Web UI  │───>│   S3   │───>│  Middleware      │───>│  Bedrock     │───>│ OpenSearch │
│ (Upload) │    │ Bucket │    │ (dedup + process)│    │ (Embeddings) │    │  (Store)   │
└──────────┘    └────────┘    └─────────────────┘    └──────────────┘    └────────────┘

Pipeline 2: Query / Chat
┌──────────┐    ┌──────────────┐    ┌────────────┐    ┌───────────┐    ┌──────────────┐    ┌──────────┐
│ Chat UI  │───>│   Bedrock    │───>│ OpenSearch  │───>│ Re-Ranker │───>│   Bedrock    │───>│ Chat UI  │
│ (Query)  │    │ (Embed query)│    │ (Top-K=5)   │    │ (Hybrid)  │    │   (LLM)      │    │(Response)│
└──────────┘    └──────────────┘    └────────────┘    └───────────┘    └──────────────┘    └──────────┘
```

---

## Tech Stack

| Layer              | Technology                              |
|--------------------|-----------------------------------------|
| Frontend           | React (Vite) or Streamlit               |
| Backend API        | Python (FastAPI)                        |
| Storage            | AWS S3                                  |
| Embeddings         | AWS Bedrock (see model options below)   |
| LLM                | AWS Bedrock (see model options below)   |
| Vector Store       | AWS OpenSearch Service (with k-NN)      |
| Infrastructure     | Boto3 (automated provisioning via IAM)  |
| Document Parsing   | PyPDF2 / python-docx / unstructured     |

---

## AWS Bedrock Model Options (User to Choose)

### Embedding Models
| Option | Model ID | Dimensions | Max Tokens | Notes |
|--------|----------|------------|------------|-------|
| A | `amazon.titan-embed-text-v2:0` | 256 / 512 / 1024 | 8,192 | AWS-native, cost-effective, configurable dimensions |
| B | `amazon.titan-embed-text-v1` | 1536 | 8,192 | Proven, stable |
| C | `cohere.embed-english-v3` | 1024 | 512 | Strong semantic quality, supports search/classification input types |
| D | `cohere.embed-multilingual-v3` | 1024 | 512 | Multi-language support if needed |

### LLM Models (for final answer generation)
| Option | Model ID | Context Window | Notes |
|--------|----------|---------------|-------|
| A | `anthropic.claude-3-sonnet-20240229-v1:0` | 200K | Good balance of quality and cost |
| B | `anthropic.claude-3-haiku-20240307-v1:0` | 200K | Fastest, cheapest |
| C | `anthropic.claude-3-5-sonnet-20241022-v2:0` | 200K | Highest quality |
| D | `amazon.titan-text-premier-v1:0` | 32K | AWS-native option |
| E | `meta.llama3-70b-instruct-v1:0` | 8K | Open-source option |

**Please select one embedding model and one LLM model before I begin implementation.**

---

## Project Structure

```
legalragwithaws/
├── CLAUDE.md
├── requirements.txt
├── .env.example                  # AWS credentials template
├── infrastructure/
│   ├── setup_s3.py               # Auto-create and configure S3 bucket
│   ├── setup_opensearch.py       # Auto-create OpenSearch domain with k-NN
│   ├── setup_bedrock.py          # Verify/enable Bedrock model access
│   └── setup_all.py              # Orchestrator: provisions all AWS resources
├── backend/
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Centralized config (env vars, constants)
│   ├── routes/
│   │   ├── upload.py             # Document upload endpoints
│   │   └── chat.py               # Chat/query endpoints
│   ├── services/
│   │   ├── s3_service.py         # S3 upload, list, download operations
│   │   ├── document_processor.py # PDF/DOCX parsing, chunking, metadata
│   │   ├── embedding_service.py  # Bedrock embedding calls
│   │   ├── opensearch_service.py # Index management, insert, search
│   │   ├── dedup_middleware.py   # File hash comparison, duplicate detection
│   │   ├── reranker.py           # Hybrid re-ranking (semantic + keyword)
│   │   └── llm_service.py        # Bedrock LLM calls for answer generation
│   └── models/
│       ├── document.py           # Document schema / metadata model
│       └── chat.py               # Chat request/response models
├── frontend/
│   ├── app.py                    # Streamlit app (upload + chat UI)
│   └── ... (or React app)
└── tests/
    ├── test_ingestion.py
    ├── test_query.py
    └── test_dedup.py
```

---

## Pipeline 1: Document Ingestion (Detailed)

### Step 1 — Upload via UI
- User uploads PDF or DOCX through web interface
- File is sent to FastAPI backend

### Step 2 — Store in S3
- File uploaded to S3 bucket under `documents/{timestamp}_{filename}`
- S3 metadata includes: upload time, original filename, content hash (SHA-256)

### Step 3 — Deduplication Middleware
- Compute SHA-256 hash of uploaded file
- Check against a tracking index in OpenSearch (`processed_files` index)
- Fields tracked: `file_hash`, `filename`, `s3_key`, `processed_at`, `status`
- If hash already exists → skip processing, notify user "file already processed"
- If new → proceed to processing

### Step 4 — Document Processing
- Parse PDF (PyPDF2 / pdfplumber) or DOCX (python-docx)
- Extract text with page numbers and section headers
- Chunk text using recursive character splitting (chunk size ~1000 tokens, overlap ~200 tokens)
- Each chunk retains metadata:
  - `source_file`: original filename
  - `s3_key`: S3 object key
  - `page_number`: page(s) the chunk spans
  - `chunk_index`: position in document
  - `section_header`: nearest heading (if extractable)
  - `file_hash`: SHA-256 for traceability
  - `citation`: formatted citation string (e.g., "Document X, Page Y")
  - `uploaded_at`: timestamp

### Step 5 — Generate Embeddings
- Send each chunk to Bedrock embedding model
- Receive vector representation

### Step 6 — Store in OpenSearch
- Index: `legal_documents`
- Each document in the index contains:
  - `embedding` (k-NN vector field)
  - `text` (raw chunk text, for keyword search)
  - `metadata` (all fields from Step 4)
- Before insertion: check if chunk with same `file_hash + chunk_index` exists → prevent duplicates
- Mark file as processed in `processed_files` index

---

## Pipeline 2: Query / Chat (Detailed)

### Step 1 — User Query
- User types question in chat interface

### Step 2 — Query Embedding
- Convert query text to embedding using same Bedrock model as Pipeline 1

### Step 3 — OpenSearch Retrieval (Top-K = 5)
- Perform two searches in parallel:
  - **Semantic search**: k-NN vector similarity on `embedding` field
  - **Keyword search**: BM25 text match on `text` field
- Retrieve top-K results from each

### Step 4 — Hybrid Re-Ranking
Custom re-ranking strategy combining both search types:

```
final_score = (alpha * semantic_score) + ((1 - alpha) * keyword_score)
```

- `alpha` configurable (default 0.7 — favoring semantic similarity)
- Normalize scores from each method to [0, 1] before combining
- Deduplicate results (same chunk appearing in both lists)
- Sort by `final_score` descending
- Return top 5 results

### Step 5 — LLM Response Generation
- Construct prompt with:
  - System instruction: "You are a legal assistant. Answer based only on the provided context. Include citations."
  - Retrieved context chunks with citation info
  - User's original question
- Send to Bedrock LLM
- Return response with citations to the user

---

## AWS Infrastructure Automation

All infrastructure is provisioned via Python scripts using Boto3, triggered by a single command:

```bash
python infrastructure/setup_all.py
```

### What gets provisioned:
1. **S3 Bucket**: Created with versioning enabled, server-side encryption (AES-256), and appropriate bucket policy
2. **OpenSearch Domain**: Created with k-NN plugin enabled, appropriate instance type, EBS storage, and fine-grained access control
3. **Bedrock**: Verify model access is enabled for chosen embedding + LLM models

### Required IAM Permissions
The provided IAM user/role needs:
- `s3:*` (scoped to the project bucket)
- `es:*` (OpenSearch)
- `bedrock:InvokeModel`, `bedrock:ListFoundationModels`
- `iam:PassRole` (if needed for OpenSearch service-linked role)

### Configuration
All AWS settings managed via `.env` file:
```
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
S3_BUCKET_NAME=legal-rag-documents
OPENSEARCH_DOMAIN_NAME=legal-rag-search
BEDROCK_EMBEDDING_MODEL_ID=
BEDROCK_LLM_MODEL_ID=
```

---

## Key Design Decisions

1. **Chunking strategy**: Recursive character splitting preserves context boundaries better than fixed-size splitting for legal text
2. **Hybrid search**: Combining semantic + keyword search handles both conceptual queries ("what are the termination clauses?") and exact term queries ("Section 4.2.1")
3. **Citation preservation**: Every chunk carries source file + page number metadata so answers can cite specific locations
4. **Deduplication at two levels**: File-level (hash check before processing) and chunk-level (hash+index check before OpenSearch insertion)
5. **Configurable re-ranking alpha**: Allows tuning the semantic vs keyword balance based on query patterns

---

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Provision all AWS infrastructure
python infrastructure/setup_all.py

# Run backend
uvicorn backend.main:app --reload --port 8000

# Run frontend
streamlit run frontend/app.py
```

---

## Status

**Implementation in progress.**
- [x] Embedding model: `amazon.titan-embed-text-v1` (1536 dims, 8K tokens)
- [x] LLM model: `amazon.titan-text-premier-v1:0` (32K context)
- [x] Frontend: Streamlit
- [ ] User provides AWS credentials
