# Legal RAG System with AWS

A production-ready Retrieval-Augmented Generation (RAG) system for legal document search and Q&A, powered by AWS Bedrock, OpenSearch, and S3.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [AWS Infrastructure Setup](#aws-infrastructure-setup)
- [Running the Application](#running-the-application)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Pipeline Details](#pipeline-details)
- [OpenSearch Dev Tools](#opensearch-dev-tools)
- [Cost Estimation](#cost-estimation)
- [Troubleshooting](#troubleshooting)

---

## Overview

This system enables legal teams to:

1. **Upload** legal documents (PDF/DOCX) through a web interface
2. **Automatically process** documents — parse, chunk, embed, and index
3. **Search and query** documents using natural language through a chat interface
4. **Get cited answers** with references to exact source documents and page numbers

Key features:
- Hybrid search (semantic + keyword) with custom re-ranking
- File-level and chunk-level deduplication
- Citation preservation throughout the pipeline
- Fully automated AWS infrastructure provisioning
- Support for Indian civil law documents

---

## Architecture

```
Pipeline 1: Document Ingestion
+----------+    +--------+    +-----------------+    +--------------+    +------------+
|  Web UI  |--->|   S3   |--->|  Middleware      |--->|  Bedrock     |--->| OpenSearch |
| (Upload) |    | Bucket |    | (dedup + process)|    | (Embeddings) |    |  (Store)   |
+----------+    +--------+    +-----------------+    +--------------+    +------------+

Pipeline 2: Query / Chat
+----------+    +--------------+    +------------+    +-----------+    +--------------+    +----------+
| Chat UI  |--->|   Bedrock    |--->| OpenSearch  |--->| Re-Ranker |--->|   Bedrock    |--->| Chat UI  |
| (Query)  |    | (Embed query)|    | (Top-K=5)  |    | (Hybrid)  |    |   (LLM)      |    |(Response)|
+----------+    +--------------+    +------------+    +-----------+    +--------------+    +----------+
```

---

## Tech Stack

| Layer              | Technology                                      |
|--------------------|-------------------------------------------------|
| Frontend           | Streamlit                                       |
| Backend API        | Python, FastAPI, Uvicorn                        |
| Object Storage     | AWS S3 (versioned, encrypted)                   |
| Embeddings         | AWS Bedrock — Amazon Titan Embed Text v1 (1536d)|
| LLM                | AWS Bedrock — Amazon Nova Lite v1                |
| Vector Store       | AWS OpenSearch Service (k-NN with HNSW)         |
| Document Parsing   | PyPDF2, python-docx                             |
| Infrastructure     | Boto3 (automated provisioning)                  |

---

## Prerequisites

1. **Python 3.10+** installed
2. **AWS Account** with the following:
   - IAM user with programmatic access (Access Key ID + Secret Access Key)
   - Permissions: `s3:*`, `es:*`, `bedrock:*`, `iam:PassRole`
3. **AWS Bedrock Model Access** enabled for:
   - `amazon.titan-embed-text-v1`
   - `amazon.nova-lite-v1:0`

   > To enable model access: Go to AWS Console -> Bedrock -> Model access -> Request access for both models.

4. **AWS CLI** (optional, for manual verification)

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd legalragwithaws
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-unique-bucket-name
OPENSEARCH_DOMAIN_NAME=legal-rag-search
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v1
BEDROCK_LLM_MODEL_ID=amazon.nova-lite-v1:0
OPENSEARCH_INSTANCE_TYPE=t3.small.search
OPENSEARCH_INSTANCE_COUNT=1
OPENSEARCH_EBS_SIZE=20
OPENSEARCH_MASTER_USER=admin
OPENSEARCH_MASTER_PASSWORD=YourSecurePassword@123
```

> **Important:** The OpenSearch master password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character. Minimum 8 characters.

> **Important:** S3 bucket names are globally unique. Choose a unique name like `legal-rag-docs-yourcompany-2026`.

---

## AWS Infrastructure Setup

Run the single setup command to automatically provision all AWS resources:

```bash
python infrastructure/setup_all.py
```

This will:
1. **Create S3 bucket** with versioning, encryption (AES-256), and public access blocked
2. **Verify Bedrock model access** and test both embedding and LLM models
3. **Create OpenSearch domain** with k-NN plugin, HTTPS enforcement, and fine-grained access control
4. **Create OpenSearch indices** (`legal_documents` for vectors, `processed_files` for tracking)
5. **Save the OpenSearch endpoint** to your `.env` file automatically

> **Note:** OpenSearch domain creation takes 15-20 minutes. The script will wait and poll automatically.

### Manual Setup (Individual Components)

If you prefer to set up components individually:

```bash
# S3 only
python infrastructure/setup_s3.py

# Bedrock verification only
python infrastructure/setup_bedrock.py

# OpenSearch only
python infrastructure/setup_opensearch.py
```

---

## Running the Application

### Start the Backend API

```bash
uvicorn backend.main:app --reload --port 8005
```

Verify it's running:
```bash
curl http://localhost:8005/
# Expected: {"message":"Legal RAG System API","status":"running"}
```

### Start the Frontend UI

In a separate terminal:

```bash
streamlit run frontend/app.py
```

This opens a browser at `http://localhost:8501` with:
- **Sidebar:** Document upload interface
- **Main area:** Chat interface for querying documents

> **Note:** If your backend runs on a port other than 8005, update `API_BASE` in `frontend/app.py`.

---

## Usage Guide

### Uploading Documents (Pipeline 1)

1. Open the Streamlit UI at `http://localhost:8501`
2. In the **sidebar**, click "Choose a file" and select a PDF or DOCX
3. Click **"Process Document"**
4. The system will:
   - Check for duplicates (SHA-256 hash comparison)
   - Upload the file to S3
   - Parse and chunk the document (preserving page numbers and citations)
   - Generate embeddings via Bedrock
   - Index all chunks in OpenSearch
5. You'll see a success message with the number of chunks created

### Querying Documents (Pipeline 2)

1. Type your question in the chat input at the bottom
2. Adjust settings in the sidebar:
   - **Top-K:** Number of results to retrieve (1-10, default 5)
   - **Semantic vs Keyword weight:** Alpha slider (0.0-1.0, default 0.7)
     - Higher = more semantic similarity
     - Lower = more keyword matching
3. The system will:
   - Convert your query to an embedding
   - Search OpenSearch (semantic + keyword, in parallel)
   - Re-rank results using hybrid scoring
   - Generate an answer using the LLM with citations
4. Click **"View Citations"** to see source documents, page numbers, and relevance scores

### Using the API Directly

```bash
# Upload a document
curl -X POST http://localhost:8005/api/upload \
  -F "file=@path/to/document.pdf"

# Query documents
curl -X POST http://localhost:8005/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the grounds for eviction?", "top_k": 5, "alpha": 0.7}'
```

---

## API Reference

### `POST /api/upload`

Upload and process a legal document.

**Request:** `multipart/form-data`
| Field | Type | Description |
|-------|------|-------------|
| file | File | PDF or DOCX file |

**Response:**
```json
{
  "message": "Document uploaded and processed successfully.",
  "filename": "case_001.pdf",
  "s3_key": "documents/20260315_case_001.pdf",
  "is_duplicate": false,
  "chunks_created": 12
}
```

### `POST /api/chat`

Query the legal document knowledge base.

**Request:** `application/json`
```json
{
  "query": "What compensation was awarded?",
  "top_k": 5,
  "alpha": 0.7
}
```

**Response:**
```json
{
  "answer": "The compensation awarded was...",
  "citations": [
    {
      "source_file": "case_004.pdf",
      "page_number": 3,
      "citation": "case_004.pdf, Page 3",
      "relevance_score": 0.8179,
      "text_snippet": "..."
    }
  ],
  "query": "What compensation was awarded?"
}
```

### `GET /`

Health check — returns API status.

### `GET /health`

Health check endpoint.

---

## Project Structure

```
legalragwithaws/
├── CLAUDE.md                         # Project architecture documentation
├── COST.md                           # Detailed cost estimation (INR)
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
├── .env                              # Your credentials (git-ignored)
├── .gitignore
│
├── infrastructure/                   # AWS auto-provisioning scripts
│   ├── setup_all.py                  # One-command full setup
│   ├── setup_s3.py                   # S3 bucket creation
│   ├── setup_opensearch.py           # OpenSearch domain + indices
│   └── setup_bedrock.py              # Bedrock model verification
│
├── backend/                          # FastAPI application
│   ├── main.py                       # App entry point, routes, CORS
│   ├── config.py                     # Centralized settings from .env
│   ├── models/
│   │   ├── document.py               # Document/chunk data models
│   │   └── chat.py                   # Chat request/response models
│   ├── routes/
│   │   ├── upload.py                 # POST /api/upload
│   │   └── chat.py                   # POST /api/chat
│   └── services/
│       ├── s3_service.py             # S3 operations + file hashing
│       ├── document_processor.py     # PDF/DOCX parsing + chunking
│       ├── embedding_service.py      # Bedrock Titan Embed v1 calls
│       ├── opensearch_service.py     # Index, search, bulk operations
│       ├── dedup_middleware.py        # Duplicate file detection
│       ├── reranker.py               # Hybrid re-ranking algorithm
│       └── llm_service.py            # Bedrock Nova Lite LLM calls
│
├── frontend/
│   └── app.py                        # Streamlit UI (upload + chat)
│
├── sample_documents/                 # Test documents
│   ├── case_001_property_dispute.pdf
│   ├── case_002_contract_breach.pdf
│   ├── case_003_tenant_eviction.pdf
│   ├── case_004_consumer_complaint.pdf
│   ├── case_005_specific_performance.pdf
│   └── real_cases/                   # Real Supreme Court of India judgments
│       ├── ghanshyam_v_yogendra.pdf
│       ├── k_gopi_v_sub_registrar.pdf
│       ├── rajendra_v_up_parishad.pdf
│       ├── saranga_v_bhavesh_consumer.pdf
│       └── state_ap_v_dr_rao.pdf
│
└── tests/                            # Unit tests
    ├── test_ingestion.py             # Chunking, hashing, parsing tests
    ├── test_query.py                 # Re-ranking algorithm tests
    └── test_dedup.py                 # Deduplication logic tests
```

---

## Pipeline Details

### Pipeline 1: Document Ingestion

```
Upload -> S3 -> Dedup Check -> Parse (PDF/DOCX) -> Chunk -> Embed -> Index in OpenSearch
```

| Step | Details |
|------|---------|
| Upload | File sent to FastAPI, stored in S3 with metadata |
| Dedup | SHA-256 hash compared against `processed_files` index |
| Parse | PyPDF2 (PDF) or python-docx (DOCX), preserves page numbers |
| Chunk | Recursive character splitting, 1000 tokens/chunk, 200 overlap |
| Metadata | source_file, s3_key, page_number, chunk_index, section_header, citation |
| Embed | Titan Embed v1 (1536 dimensions) |
| Index | Bulk insert into `legal_documents` index with k-NN vectors |

### Pipeline 2: Query / Chat

```
Query -> Embed -> Semantic Search + Keyword Search -> Hybrid Re-rank -> LLM -> Cited Answer
```

| Step | Details |
|------|---------|
| Embed Query | Same Titan Embed v1 model as ingestion |
| Semantic Search | k-NN vector similarity (cosine) via OpenSearch |
| Keyword Search | BM25 text match via OpenSearch |
| Re-ranking | `score = alpha * semantic + (1-alpha) * keyword`, default alpha=0.7 |
| LLM | Nova Lite generates answer with citations from top-5 chunks |

### Re-ranking Algorithm

```
final_score = (alpha * normalized_semantic_score) + ((1 - alpha) * normalized_keyword_score)
```

- Scores from each search are normalized to [0, 1] using min-max
- Duplicate chunks (appearing in both results) are merged
- Results sorted by final_score descending
- Alpha is configurable (default 0.7 favoring semantic similarity)

---

## OpenSearch Dev Tools

Access the OpenSearch Dashboards at:
```
https://<your-opensearch-endpoint>/_dashboards
```

Login with your master credentials, then navigate to **Dev Tools** in the left sidebar.

### Useful Queries

```json
# List all indices
GET _cat/indices?v

# Count indexed chunks
GET legal_documents/_count

# Browse chunks (without embedding vectors)
GET legal_documents/_search
{
  "size": 10,
  "query": { "match_all": {} },
  "_source": { "excludes": ["embedding"] }
}

# Keyword search
GET legal_documents/_search
{
  "size": 5,
  "query": {
    "match": { "text": "Hindu Succession Act" }
  },
  "_source": { "excludes": ["embedding"] }
}

# Filter by specific document
GET legal_documents/_search
{
  "query": {
    "term": { "source_file": "case_001_property_dispute.pdf" }
  },
  "_source": { "excludes": ["embedding"] }
}

# View all processed files
GET processed_files/_search
{
  "query": { "match_all": {} }
}

# Search by page number in a specific document
GET legal_documents/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "source_file": "k_gopi_v_sub_registrar.pdf" } },
        { "term": { "page_number": 4 } }
      ]
    }
  },
  "_source": { "excludes": ["embedding"] }
}
```

### Via curl

```bash
# Replace <endpoint> with your OpenSearch endpoint
# Replace <user>:<pass> with your credentials

curl -s -u "<user>:<pass>" "https://<endpoint>/legal_documents/_count?pretty"

curl -s -u "<user>:<pass>" "https://<endpoint>/legal_documents/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{"size": 5, "query": {"match_all": {}}, "_source": {"excludes": ["embedding"]}}'
```

---

## Cost Estimation

See [COST.md](COST.md) for a detailed breakdown. Summary for 1,000 users at 50 queries/day:

| Scenario | Monthly (INR) | Monthly (USD) |
|----------|--------------|---------------|
| Dev/Test | ~29,700 | ~$354 |
| Production | ~44,700 | ~$532 |
| Enterprise HA | ~74,300 | ~$885 |
| Optimized | ~15,100 | ~$179 |

Per-query cost: **~₹0.03** (less than 3 paise)

---

## Running Tests

```bash
# Run all tests
python tests/test_ingestion.py
python tests/test_query.py
python tests/test_dedup.py

# Or with pytest
pip install pytest
pytest tests/ -v
```

---

## Troubleshooting

### Common Issues

**1. S3 bucket name already exists**
```
BucketAlreadyExists: The requested bucket name is not available.
```
S3 bucket names are globally unique. Change `S3_BUCKET_NAME` in `.env` to something unique.

**2. Bedrock model not available**
```
ResourceNotFoundException: This model version has reached the end of its life.
```
Ensure you have access to the models in the Bedrock console. Go to AWS Console -> Bedrock -> Model access -> Request access.

**3. OpenSearch connection refused**
```
ConnectionError: Connection refused
```
- Verify `OPENSEARCH_ENDPOINT` is set correctly in `.env`
- Check that the domain is active (not still provisioning)
- Ensure the access policy allows your IP/IAM credentials

**4. Port already in use**
```
[Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)
```
Another service is using that port. Use a different port:
```bash
uvicorn backend.main:app --reload --port 8005
```
And update `API_BASE` in `frontend/app.py` accordingly.

**5. OpenSearch password rejected**
```
Security exception: Invalid credentials
```
Password must have: 1 uppercase, 1 lowercase, 1 digit, 1 special character, minimum 8 characters.

**6. Document upload fails**
- Ensure the file is PDF or DOCX (other formats are not supported)
- Check that the file is not empty
- Verify S3 bucket exists and credentials have write permissions

---

## Sample Documents Included

### Synthetic Indian Civil Cases (5)

| File | Case Type | Court | Key Laws |
|------|-----------|-------|----------|
| case_001 | Property Dispute | Delhi HC | Hindu Succession Act 1956 |
| case_002 | Contract Breach | Bombay HC | Indian Contract Act 1872 |
| case_003 | Tenant Eviction | Small Causes Chennai | TN Rent Control Act 1960 |
| case_004 | Consumer Complaint | NCDRC | Consumer Protection Act 2019 |
| case_005 | Specific Performance | Karnataka HC | Specific Relief Act 1963 |

### Real Supreme Court Judgments (5)

| File | Case | Year |
|------|------|------|
| ghanshyam_v_yogendra | Ghanshyam v. Yogendra Rathi | 2023 |
| k_gopi_v_sub_registrar | K. Gopi v. Sub-Registrar | 2025 |
| saranga_v_bhavesh_consumer | Saranga v. Bhavesh (Consumer) | 2025 |
| rajendra_v_up_parishad | Rajendra v. UP Avas Parishad | 2024 |
| state_ap_v_dr_rao | State of AP v. Dr. Rao | 2024 |

---

## Quick Start (TL;DR)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your AWS credentials

# 3. Provision AWS
python infrastructure/setup_all.py

# 4. Start backend
uvicorn backend.main:app --reload --port 8005

# 5. Start frontend (new terminal)
streamlit run frontend/app.py

# 6. Open browser at http://localhost:8501
# 7. Upload PDFs via sidebar, ask questions in chat
```
