# Legal RAG System — Monthly Cost Estimation (INR)

> Exchange Rate Used: 1 USD = 84 INR
> Region: us-east-1 (N. Virginia)
> Pricing as of March 2026

---

## Usage Assumptions

| Parameter | Value |
|-----------|-------|
| Total Users | 1,000 |
| Queries per User per Day | 50 |
| Total Queries per Day | 50,000 |
| Total Queries per Month (30 days) | 1,500,000 |
| Working Hours per Day | 8 hours |
| Avg Queries per Second (sustained) | ~1.74 QPS |
| Peak Queries per Second (burst 5x) | ~8-10 QPS |
| Estimated Concurrent Connections | 10-20 |
| New Documents Uploaded per Month | ~500 documents |
| Avg Document Size | 20 pages (~5,000 words) |
| Avg Chunks per Document | 50 |
| Total Stored Chunks | ~25,000+ |

---

## 1. AWS Bedrock — Embedding Model (Titan Embed Text v1)

**Pricing:** $0.10 per 1 Million input tokens

### Query Embeddings (Pipeline 2)
| Item | Calculation | Monthly |
|------|-------------|---------|
| Queries | 1,500,000 queries/month |  |
| Avg tokens per query | ~50 tokens |  |
| Total tokens | 75,000,000 (75M) |  |
| Cost (USD) | 75M × $0.10/1M | **$7.50** |
| **Cost (INR)** | | **₹630** |

### Document Embedding (Pipeline 1)
| Item | Calculation | Monthly |
|------|-------------|---------|
| New documents | 500 docs × 50 chunks |  |
| Avg tokens per chunk | ~200 tokens |  |
| Total tokens | 5,000,000 (5M) |  |
| Cost (USD) | 5M × $0.10/1M | **$0.50** |
| **Cost (INR)** | | **₹42** |

### Total Bedrock Embedding: ₹672/month ($8.00)

---

## 2. AWS Bedrock — LLM Model (Amazon Nova Lite v1)

**Pricing:**
- Input: $0.06 per 1 Million input tokens
- Output: $0.24 per 1 Million output tokens

### Per Query Token Breakdown
| Component | Tokens |
|-----------|--------|
| System prompt | ~100 |
| Context chunks (5 × 300 tokens) | ~1,500 |
| User query | ~50 |
| **Total Input per Query** | **~1,650** |
| **Avg Output per Query** | **~300** |

### Monthly LLM Cost
| Item | Calculation | Monthly |
|------|-------------|---------|
| Total Input Tokens | 1,500,000 × 1,650 = 2,475M |  |
| Input Cost (USD) | 2,475M × $0.06/1M | **$148.50** |
| Total Output Tokens | 1,500,000 × 300 = 450M |  |
| Output Cost (USD) | 450M × $0.24/1M | **$108.00** |
| **Total LLM (USD)** | | **$256.50** |
| **Total LLM (INR)** | | **₹21,546** |

---

## 3. AWS OpenSearch Service

### Current Setup (Dev/Test — t3.small)
| Item | Spec | Monthly Cost |
|------|------|-------------|
| Instance | t3.small.search (2 vCPU, 2 GB) | $0.036/hr |
| Monthly | 730 hours | $26.28 |
| EBS (gp3) | 20 GB × $0.08/GB | $1.60 |
| **Total (USD)** | | **$27.88** |
| **Total (INR)** | | **₹2,342** |

### Recommended Production Setup (1,000 Users)

For 1,000 users at 50 queries/day with k-NN vector search, the recommended setup is:

| Item | Spec | Monthly Cost |
|------|------|-------------|
| Data Nodes | 2× m6g.large.search (2 vCPU, 8 GB each) | $0.128/hr × 2 |
| Instance Cost | 730 hours × 2 nodes | $186.88 |
| EBS Storage (gp3) | 50 GB × 2 nodes × $0.08/GB | $8.00 |
| Dedicated Master (optional) | 3× m6g.large.search | $280.32 |
| **Without Dedicated Master (USD)** | | **$194.88** |
| **Without Dedicated Master (INR)** | | **₹16,370** |
| **With Dedicated Master (USD)** | | **$475.20** |
| **With Dedicated Master (INR)** | | **₹39,917** |

> **Why m6g.large?**
> - k-NN (vector) search is memory-intensive; 8 GB per node ensures vectors stay in memory
> - 2 nodes provide high availability (1 replica)
> - m6g (Graviton) instances are ~20% cheaper than equivalent x86 instances
> - Handles 10-20 concurrent k-NN QPS comfortably

---

## 4. AWS S3

| Item | Calculation | Monthly Cost |
|------|-------------|-------------|
| Storage (Standard) | ~10 GB × $0.023/GB | $0.23 |
| PUT Requests | 25,000 chunks × $0.005/1,000 | $0.13 |
| GET Requests | ~5,000 × $0.0004/1,000 | $0.002 |
| **Total (USD)** | | **$0.36** |
| **Total (INR)** | | **₹30** |

---

## 5. Compute — Backend Server (EC2)

The FastAPI backend needs to handle 1,000 users. Options:

### Option A: Single EC2 Instance
| Item | Spec | Monthly Cost |
|------|------|-------------|
| Instance | t3.large (2 vCPU, 8 GB) | $0.0832/hr |
| Monthly | 730 hours | $60.74 |
| **Total (INR)** | | **₹5,102** |

### Option B: ECS Fargate (Auto-scaling, Recommended)
| Item | Spec | Monthly Cost |
|------|------|-------------|
| Tasks | 2 tasks × 1 vCPU × 2 GB each | |
| vCPU | 2 × $0.04048/hr × 730 hr | $59.10 |
| Memory | 4 GB × $0.004445/GB/hr × 730 hr | $12.98 |
| **Total (USD)** | | **$72.08** |
| **Total (INR)** | | **₹6,055** |

### Option C: AWS Lambda (Pay-per-request)
| Item | Spec | Monthly Cost |
|------|------|-------------|
| Requests | 1,500,000 × $0.20/1M | $0.30 |
| Duration | 1,500,000 × 5s × 512 MB | ~$62.50 |
| **Total (USD)** | | **$62.80** |
| **Total (INR)** | | **₹5,275** |

---

## 6. Data Transfer

| Item | Calculation | Monthly Cost |
|------|-------------|-------------|
| Intra-region (OpenSearch ↔ EC2) | Free | $0.00 |
| Internet egress (API responses) | 1.5M × ~2 KB = ~3 GB | Free (first 100 GB) |
| **Total (INR)** | | **₹0** |

---

## Total Monthly Cost Summary

### Scenario 1: Development / Small Scale (Current Setup)

| Service | USD | INR |
|---------|-----|-----|
| Bedrock Embeddings | $8.00 | ₹672 |
| Bedrock LLM (Nova Lite) | $256.50 | ₹21,546 |
| OpenSearch (t3.small, 1 node) | $27.88 | ₹2,342 |
| S3 | $0.36 | ₹30 |
| EC2 (t3.large) | $60.74 | ₹5,102 |
| Data Transfer | $0.00 | ₹0 |
| **TOTAL** | **$353.48** | **₹29,692** |

### Scenario 2: Production (Recommended for 1,000 Users)

| Service | USD | INR |
|---------|-----|-----|
| Bedrock Embeddings | $8.00 | ₹672 |
| Bedrock LLM (Nova Lite) | $256.50 | ₹21,546 |
| OpenSearch (2× m6g.large, no master) | $194.88 | ₹16,370 |
| S3 | $0.36 | ₹30 |
| ECS Fargate (2 tasks) | $72.08 | ₹6,055 |
| Data Transfer | $0.00 | ₹0 |
| **TOTAL** | **$531.82** | **₹44,673** |

### Scenario 3: Production High-Availability (Enterprise)

| Service | USD | INR |
|---------|-----|-----|
| Bedrock Embeddings | $8.00 | ₹672 |
| Bedrock LLM (Nova Lite) | $256.50 | ₹21,546 |
| OpenSearch (2× m6g.large + 3 masters) | $475.20 | ₹39,917 |
| S3 | $0.36 | ₹30 |
| ECS Fargate (3 tasks + ALB) | $130.00 | ₹10,920 |
| CloudWatch Monitoring | $15.00 | ₹1,260 |
| Data Transfer | $0.00 | ₹0 |
| **TOTAL** | **$885.06** | **₹74,345** |

---

## Concurrency & Throughput Estimates

### For 1,000 Users × 50 Queries/Day

| Metric | Value |
|--------|-------|
| Total daily queries | 50,000 |
| Avg QPS (over 24 hrs) | 0.58 |
| Avg QPS (8 working hours) | 1.74 |
| Peak QPS (5× burst) | 8-10 |
| Max concurrent connections | 10-20 |
| Avg response latency | 2-4 seconds |
| P95 response latency | 5-8 seconds |

### Latency Breakdown per Query

| Step | Estimated Time |
|------|---------------|
| Query embedding (Titan Embed v1) | 100-200 ms |
| OpenSearch k-NN search | 50-150 ms |
| OpenSearch BM25 search | 30-80 ms |
| Re-ranking logic | 5-10 ms |
| LLM generation (Nova Lite) | 1.5-3.5 seconds |
| Network overhead | 50-100 ms |
| **Total per query** | **~2-4 seconds** |

### Scaling Limits by OpenSearch Instance Type

| Instance | Max k-NN QPS | Max Users (50 q/day) | Monthly Cost (INR) |
|----------|-------------|---------------------|-------------------|
| t3.small.search (1 node) | 5-10 | ~500 | ₹2,342 |
| m6g.large.search (2 nodes) | 20-40 | ~2,000 | ₹16,370 |
| m6g.xlarge.search (2 nodes) | 50-80 | ~5,000 | ₹32,740 |
| r6g.xlarge.search (3 nodes) | 100-150 | ~10,000 | ₹58,200 |

---

## Cost Optimization Tips

1. **Use Bedrock Batch Inference** for document ingestion — up to 50% cheaper for bulk embedding jobs
2. **Switch to Nova Micro** instead of Nova Lite — ~60% cheaper ($0.035/$0.14 per 1M tokens) with slightly lower quality
3. **Use OpenSearch Serverless** if traffic is bursty — pay only for active OCUs
4. **Reserved Instances** for OpenSearch — save 30-40% with 1-year commitment
5. **Caching layer (ElastiCache/Redis)** — cache frequent queries to reduce Bedrock calls by 20-40%
6. **Reduce Top-K from 5 to 3** — fewer context tokens = lower LLM cost per query
7. **Use Graviton instances** (m6g/r6g) — 20% cheaper than equivalent Intel instances

### Potential Savings with Optimizations

| Optimization | Monthly Savings (INR) |
|-------------|----------------------|
| Nova Micro instead of Nova Lite | ~₹12,900 |
| OpenSearch 1-yr Reserved | ~₹5,700 |
| Redis cache (30% hit rate) | ~₹6,700 |
| Top-K = 3 instead of 5 | ~₹4,300 |
| **Total Potential Savings** | **~₹29,600** |
| **Optimized Production Cost** | **~₹15,073/month** |

---

## Per-Query Cost Breakdown

| Component | Cost per Query (INR) |
|-----------|---------------------|
| Embedding (Titan Embed v1) | ₹0.00042 |
| LLM Input (Nova Lite) | ₹0.0083 |
| LLM Output (Nova Lite) | ₹0.0060 |
| OpenSearch (amortized) | ₹0.0109 |
| Compute (amortized) | ₹0.0040 |
| **Total per Query** | **₹0.0296** |
| **Cost per 1,000 Queries** | **₹29.60** |

---

*Last updated: 15 March 2026*
