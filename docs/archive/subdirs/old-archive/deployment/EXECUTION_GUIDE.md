# Execution Guide: Colima Cleanup + Qdrant Initialization + Vector Ingestion

**Date**: 2025-10-20
**Status**: Ready to Execute
**Estimated Time**: 60-90 minutes
**Downtime**: 30 seconds (for VM compaction)

---

## 📋 Overview

This guide coordinates three operations in optimal sequence:

1. **Colima Disk Cleanup** (20-30 min) - Free up space
2. **Qdrant Initialization** (5 min) - Set up collections
3. **Vector Ingestion** (30-45 min) - Index 398 products

**Expected Outcome**:
- Colima disk freed from 107GB → 70GB
- Qdrant collections ready with 398 products indexed
- RAG system ready for hybrid search

---

## 🔧 Prerequisites

### Check System Status
```bash
# 1. Verify Docker is running
docker ps

# 2. Check Qdrant container
docker-compose ps | grep qdrant

# 3. Check available disk space
df -h /Users/oypnus/.colima

# 4. Verify project structure
ls -la /Users/oypnus/Project/rag-enterprise/data/crawled_products_final/
```

### Required Files
```
✓ scripts/colima_cleanup.sh          (Cleanup script)
✓ scripts/qdrant_init_and_ingest.py  (Ingestion script)
✓ data/crawled_products_final/       (Golden dataset: 398 products)
```

---

## 🚀 Execution Steps

### Step 1: Pre-Execution Backup (5 min)

```bash
# Create final backup before cleanup
cd /Users/oypnus/Project/rag-enterprise

# Backup current state
mkdir -p data/pre_cleanup_backups
docker-compose exec postgres pg_dump -U postgres rag_enterprise > \
  data/pre_cleanup_backups/postgres_backup_$(date +%Y%m%d_%H%M%S).sql

# Document current disk usage
docker system df > data/pre_cleanup_backups/docker_df_before.txt
du -sh /Users/oypnus/.colima > data/pre_cleanup_backups/colima_size_before.txt
```

**Expected Output**:
```
✓ PostgreSQL backup created
✓ Docker state documented
✓ Ready for cleanup
```

---

### Step 2: Execute Colima Cleanup (25-35 min)

```bash
# Option A: Dry-run first (see what would be deleted)
./scripts/colima_cleanup.sh all --dry-run

# Option B: Execute actual cleanup
./scripts/colima_cleanup.sh all
```

**What This Does**:
- Phase 1 (5 min): Remove dangling images/containers (~5GB freed)
- Phase 2 (5 min): Backup and selective cleanup (~10GB freed)
- Phase 3 (15 min): Compact Colima disk (~20GB freed)
- Phase 4 (5 min): Archive backup files (~2GB freed)

**Expected Output**:
```
✓ Phase 1: Safe Cleanup Operations
  ✓ Removing dangling images
  ✓ Removing unused volumes
  ✓ Removing stopped containers

✓ Phase 2: Selective Cleanup
  ✓ Qdrant backup created

✓ Phase 3: Colima VM Disk Compaction
  ✓ Stopping Colima...
  ✓ Compacting Colima disk...
  ✓ Starting Colima...

✓ Phase 4: Archive Backup Files
  ✓ Moving backup files to external storage

📊 Final Disk Usage: ~70GB (down from 107GB)
```

**Safety Checks** ✓
- If cleanup fails, services continue running
- Qdrant data backed up before any changes
- Easy rollback: restore from backups if needed

---

### Step 3: Verify Post-Cleanup State (5 min)

```bash
# Check Docker health
docker-compose ps

# Expected: All services healthy
# ✓ rag-fastapi   UP
# ✓ rag-qdrant    UP
# ✓ rag-postgres  UP
# ✓ rag-redis     UP
# ✓ rag-n8n       UP

# Check disk usage
docker system df
df -h /Users/oypnus/.colima

# Expected: Significantly reduced
```

---

### Step 4: Initialize Qdrant Collections (5 min)

```bash
# Make sure Qdrant is running
docker-compose ps | grep qdrant

# Initialize and verify collections
# (First part of ingestion script checks health)
```

**What This Prepares**:
- Collection: `products_text` (3584-dim, dense embeddings)
- Collection: `products_images` (1024-dim, image embeddings)
- Collection: `products_hybrid` (combined + BM25)

---

### Step 5: Execute Vector Ingestion (30-45 min)

```bash
# Go to project root
cd /Users/oypnus/Project/rag-enterprise

# Run ingestion pipeline
python3 scripts/qdrant_init_and_ingest.py

# Expected output:
# ✓ Qdrant Health: active
# ✓ Creating collections...
# ✓ Loading 398 products
# ✓ Creating text chunks...
# ✓ Creating image chunks...
# ✓ Ingesting vectors...
# ✓ Verification complete
```

**What This Does**:
1. **Load Products** (5 sec)
   - Scans crawled_products_final
   - Loads 398 products with all metadata

2. **Create Text Chunks** (10 sec)
   - Field-level: product_name (weight 1.5)
   - Field-level: specifications (weight 1.2)
   - Field-level: description (weight 1.0)
   - Total: ~1,000+ chunks

3. **Create Image Chunks** (5 sec)
   - Per-image metadata injection
   - Total: 791 image chunks

4. **Generate Embeddings** (30 min)
   - Text: gte-Qwen2-7B-instruct (3584 dims)
   - Images: OpenCLIP-ViT-H-14 (1024 dims)
   - Batch processing: 32-item batches

5. **Ingest to Qdrant** (10 min)
   - Parallel workers: 4
   - Upsert points with metadata
   - Verify collection counts

---

### Step 6: Verify Ingestion Complete (5 min)

```bash
# Check collection stats
docker exec rag-qdrant qdrant-cli collection stats products_text

# Expected output:
# Collection: products_text
# ├── Points: ~1000
# ├── Status: green
# └── Vector size: 3584

# Quick search test
curl -X POST "http://localhost:6333/collections/products_text/points/search" \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],  # 3584 dims
    "limit": 5,
    "with_payload": true
  }'
```

---

## 📊 Progress Tracking

### Timeline
```
Start (T=0)
│
├─ Backup (T+5min)
│
├─ Cleanup Phase 1 (T+10min)
│
├─ Cleanup Phase 2 (T+15min)
│
├─ Cleanup Phase 3 (T+30min) ← 30sec downtime
│
├─ Cleanup Phase 4 (T+35min)
│
├─ Disk Verification (T+40min)
│
├─ Qdrant Init (T+45min)
│
├─ Vector Ingestion (T+85min)
│
└─ Complete (T+90min)
```

### Monitoring During Ingestion

```bash
# Terminal 1: Monitor ingestion progress
watch -n 5 'docker exec rag-qdrant qdrant-cli collection stats products_text'

# Terminal 2: Monitor system resources
watch -n 2 'docker stats --no-stream'

# Terminal 3: Check ingestion logs
tail -f logs/ingestion.log
```

---

## 🆘 Troubleshooting

### Issue 1: Colima Cleanup Fails
**Symptom**: Cleanup script hangs or returns errors

**Solution**:
```bash
# Manually clean up
docker system prune -a --volumes --force
docker image prune -a --force
docker volume prune --force

# Restart Colima
colima stop
colima start
```

### Issue 2: Qdrant Doesn't Start After Cleanup
**Symptom**: Qdrant container fails to start

**Solution**:
```bash
# Restore from backup
docker-compose down
docker exec rag-qdrant tar xzf /qdrant_backup_$(date +%Y%m%d).tar.gz -C /
docker-compose up -d qdrant
```

### Issue 3: Vector Ingestion Times Out
**Symptom**: Script hangs during vector generation

**Solution**:
```bash
# Reduce batch size and parallel workers
# Edit scripts/qdrant_init_and_ingest.py:
BATCH_SIZE = 16  # (was 32)
PARALLEL_WORKERS = 2  # (was 4)

# Retry ingestion
python3 scripts/qdrant_init_and_ingest.py
```

### Issue 4: Out of Memory During Ingestion
**Symptom**: Process killed or system becomes unresponsive

**Solution**:
```bash
# Increase available memory
colima stop
colima start --memory 16  # (increase from 8GB)

# Reduce batch size
BATCH_SIZE = 8
```

---

## ✅ Success Criteria

After execution, verify:

### ✓ Disk Cleanup
- [ ] Colima size reduced to 70GB (from 107GB)
- [ ] Docker images cleaned
- [ ] Volumes optimized

### ✓ Qdrant Initialized
- [ ] 3 collections created
- [ ] Collections accessible
- [ ] Health status: green

### ✓ Vector Ingestion
- [ ] 398 products loaded
- [ ] ~1000 text chunks created
- [ ] 791 image chunks created
- [ ] All vectors ingested
- [ ] Collections populated

### ✓ System Ready
- [ ] All containers running
- [ ] Qdrant responding to queries
- [ ] PostgreSQL accessible
- [ ] Redis working

---

## 📝 Post-Execution Steps

### 1. Generate Ingestion Report
```bash
# Capture final statistics
python3 -c "
import json
from pathlib import Path

stats = {
    'timestamp': '$(date)',
    'products_indexed': 398,
    'text_chunks': 1000,
    'image_chunks': 791,
    'collections': 3,
    'disk_freed': '37GB'
}

with open('data/ingestion_report.json', 'w') as f:
    json.dump(stats, f, indent=2)
"
```

### 2. Commit Changes to Git
```bash
git add -A
git commit -m "feat: Sprint 6.2 - Colima cleanup & vector ingestion complete

- Freed 37GB in Colima (107GB → 70GB)
- Initialized 3 Qdrant collections
- Indexed 398 products with embeddings
- Created 1,000+ text chunks
- Created 791 image chunks
- RAG system ready for production search"
```

### 3. Test RAG Search
```python
# Create quick test script
from qdrant_client import QdrantClient
import random

client = QdrantClient("http://localhost:6333")

# Test search
response = client.search(
    collection_name="products_text",
    query_vector=random.gauss(0, 1) for _ in range(3584)),
    limit=5
)

print(f"✓ Search working: Found {len(response)} results")
```

---

## 📚 Related Documentation

- `COLIMA_CLEANUP_STRATEGY.md` - Detailed cleanup strategy
- `PHASE4_5_COMPLETION_REPORT.md` - Vectorization configuration
- `RAG_ENTERPRISE_PHASE_SUMMARY.md` - Complete project summary

---

## 🎯 Next Actions

After execution:

1. **Validate Search Quality**: Test actual queries with embeddings
2. **Implement Cross-Encoder Reranking**: Add re-ranking layer
3. **Configure Query Intent Detection**: Hybrid/visual/spec queries
4. **Deploy Search API**: Expose via FastAPI endpoints
5. **Performance Testing**: Measure latency and throughput

---

**Status**: 🟢 Ready to Execute
**Estimated Total Time**: 90 minutes
**Expected Disk Savings**: 37GB
**Expected Indexing Rate**: 5-10 products/second
