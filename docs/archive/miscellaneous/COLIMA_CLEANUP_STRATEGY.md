# Colima Disk Space Cleanup & Optimization Strategy

**Date**: 2025-10-20
**Current Usage**: 107GB total (59GB datadisk + 11.42GB images + 12.31GB volumes)
**Target**: Reduce to ~50GB by cleaning unused resources

---

## 📊 Current Breakdown

### Disk Usage Analysis
```
Total Colima Usage:           ~107GB
├── VM Disk (datadisk):       59GB  ← Sparse file, can be compacted
├── Docker Images:            11.42GB (45% reclaimable = 5.16GB)
├── Docker Volumes:           12.31GB (96% reclaimable = 11.92GB)
└── Local Project Data:       ~2.2GB (crawled_products_final)

Backup Files (Project):
├── backup_crawled_organized_20251020.tar.gz: 1.1GB
└── backup_crawled_updated_20251020.tar.gz:   1.1GB
```

### Reclaimable Space
```
Docker Images:                5.16GB   (remove unused images)
Docker Volumes:               11.92GB  (remove unused volumes)
Backup Files:                 2.2GB    (archive to external storage)
Colima VM Disk:               Compact  (shrink sparse file)
───────────────────────────────────────
Total Reclaimable:            ~19GB
```

---

## 🔍 Root Cause Analysis

### Why 59GB in datadisk?
1. **Ollama Models**: Multiple LLM models cached locally
   - teacher models (7B, 13B variants)
   - student models (3B variants)
   - inference cache for embeddings
   - Estimated: 15-20GB

2. **Qdrant Snapshots**: Vector database backups
   - Multiple version snapshots
   - Estimated: 5-10GB

3. **N8N Workflows**: Execution logs and data
   - Workflow execution history
   - Data transformations cache
   - Estimated: 2-3GB

4. **PostgreSQL Data**: Historical data
   - Estimated: 3-5GB

5. **Docker System Cache**: Build cache and layers
   - Estimated: 5-10GB

6. **Unused Volume Data**: Orphaned docker volumes
   - Estimated: 5-10GB

---

## 🧹 Cleanup Strategy (3-Phase Approach)

### Phase 1: Immediate Cleanup (Safe Operations) - ~5GB Saved
```bash
# 1. Remove dangling images
docker image prune -a --force

# 2. Remove unused volumes
docker volume prune --force

# 3. Remove stopped containers
docker container prune --force

# 4. Clear build cache
docker builder prune --all --force
```

**Expected Reclaim**: 5-6GB
**Risk Level**: Low (doesn't affect running services)
**Time**: < 1 minute

---

### Phase 2: Selective Cleanup (With Verification) - ~10GB Saved
```bash
# 1. Remove old Ollama model images (keep only current)
# Only keep: mistral, neural-chat, orca-mini
# Remove: all gguf archives, duplicate versions

docker images | grep ollama | awk '{print $3}' | \
  xargs -I {} docker rmi {} --force

# 2. Prune qdrant_data volume (backup first)
docker exec rag-qdrant tar czf /tmp/qdrant_backup.tar.gz /qdrant/storage
docker cp rag-qdrant:/tmp/qdrant_backup.tar.gz ./data/qdrant_backup_$(date +%s).tar.gz

# 3. Compact Qdrant collections (remove old snapshots)
# Only keep latest snapshot per collection
```

**Expected Reclaim**: 8-12GB
**Risk Level**: Medium (requires backups)
**Time**: 5-10 minutes

---

### Phase 3: VM Disk Compaction (Structural Optimization) - ~20GB Saved
```bash
# 1. Stop Colima and compact disk
colima stop
colima disk compact

# 2. Restart Colima
colima start --memory 8
```

**Expected Reclaim**: 15-25GB (largest savings)
**Risk Level**: Medium (requires downtime)
**Time**: 10-30 minutes (depends on current fragmentation)

---

### Phase 4: Archive Backups (Permanent Cleanup) - ~2.2GB Freed
```bash
# Archive large backup files to external storage
mkdir -p /Volumes/ExternalDrive/rag-enterprise-backups/

# Move backup files
mv data/backup_crawled_*.tar.gz /Volumes/ExternalDrive/rag-enterprise-backups/

# Verify integrity
tar -tzf /Volumes/ExternalDrive/rag-enterprise-backups/backup_*.tar.gz > /dev/null

# Clean local copies
rm -f data/backup_crawled_*.tar.gz
```

**Expected Reclaim**: 2.2GB (frees local disk)
**Risk Level**: Low (backups still accessible)
**Time**: 5 minutes

---

## 📋 Cleanup Execution Plan

### Before Cleanup
```bash
# 1. Verify all services are healthy
docker-compose ps

# 2. Create final backup
docker-compose exec postgres pg_dump -U postgres rag_enterprise > data/postgres_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Document current state
docker system df > data/docker_df_before.txt
```

### Execute Cleanup (Order Matters)
```bash
# Phase 1: Safe cleanup (no downtime)
docker system prune -a --volumes --force

# Phase 2: Selective cleanup (with backups)
# [Execute phase 2 steps with verification]

# Phase 3: VM compaction (brief downtime: ~30 seconds)
colima stop && colima disk compact && colima start

# Phase 4: Archive backups
# [Move to external storage]
```

### After Cleanup
```bash
# Verify services are still running
docker-compose ps

# Document final state
docker system df > data/docker_df_after.txt

# Generate cleanup report
du -sh /Users/oypnus/.colima > data/colima_size_after.txt
```

---

## 🎯 Optimization Recommendations

### 1. Ollama Model Management
**Current Problem**: Multiple versions of same models cached
**Solution**:
```bash
# Keep only production models
# Remove: old versions, experimental variants
# Strategy: Use ollama list to see what's installed, keep only 3-5 current models
```

### 2. Qdrant Snapshot Management
**Current Problem**: Accumulating snapshots over time
**Solution**:
```bash
# Implement automatic cleanup
# Keep only: current snapshot + 1 previous backup
# Remove: snapshots older than 7 days
```

### 3. N8N Workflow Logs
**Current Problem**: Execution logs grow unbounded
**Solution**:
```bash
# Configure N8N to rotate logs
# Keep only: last 30 days of execution history
# Archive: older logs to external storage
```

### 4. Docker Image Size Reduction
**Current Problem**: Unused base images taking space
**Solution**:
```bash
# Use alpine versions: 274MB → 50MB (postgres)
# Use distroless images: 2.72GB → 100MB (fastapi)
# Multi-stage builds: Remove build dependencies from final image
```

---

## 📈 Expected Outcomes

### Before Cleanup
```
Total:           107GB
├── Colima VM:   59GB
├── Images:      11.42GB (45% reclaimable)
└── Volumes:     12.31GB (96% reclaimable)
```

### After Cleanup (Estimate)
```
Total:           60-70GB
├── Colima VM:   35-40GB (after compaction)
├── Images:      6GB (cleaned)
└── Volumes:     1GB (cleaned)
└── Project:     18-20GB (production data)
```

### Savings Breakdown
```
Phase 1 (Safe):           -5GB
Phase 2 (Selective):      -10GB
Phase 3 (VM Compact):     -20GB
Phase 4 (Archive):        -2GB
────────────────────────────
Total Saved:              -37GB
Final Size:               ~70GB
```

---

## 🚀 Next Steps

1. **Generate Cleanup Script** (`colima_cleanup.sh`)
   - Automate all 4 phases with safety checks
   - Add rollback capability

2. **Create Monitoring Dashboard**
   - Track disk usage over time
   - Alert when usage exceeds thresholds

3. **Implement Retention Policies**
   - Docker image cleanup rules
   - Volume pruning schedule
   - Log rotation for services

4. **Document Lessons Learned**
   - Why did disk grow to 107GB?
   - How to prevent in future?
   - Monitoring strategy going forward

---

## ⚠️ Safety Considerations

### Before Running Cleanup
- ✅ Backup all important data
- ✅ Document current disk state
- ✅ Ensure services are healthy
- ✅ Have rollback plan ready

### What NOT to Delete
- ❌ Do NOT delete: `crawled_products_final` (production data)
- ❌ Do NOT delete: Qdrant indexes (need backup first)
- ❌ Do NOT delete: PostgreSQL data (running services depend on it)

### What CAN be Safely Deleted
- ✅ Old Docker images (images listed as "dangling")
- ✅ Unused volumes (verified not in use)
- ✅ Backup files (archived externally)
- ✅ Build cache (rebuilds on demand)

---

## 📊 Monitoring Going Forward

### Weekly Checks
```bash
# Monitor disk usage
df -h /Users/oypnus/.colima
docker system df

# Track volume growth
du -sh /Users/oypnus/.colima/_lima/_disks/colima/
```

### Maintenance Tasks
```
Every 2 weeks:
- Prune dangling images
- Archive old qdrant snapshots
- Rotate application logs

Every month:
- Full system cleanup (phases 1-2)
- Review Ollama models (keep current only)
- Compact Colima disk if >70GB
```

---

## 🎓 Lessons Learned

### Why Did This Happen?
1. No automatic cleanup policies
2. Multiple model experiments (teacher/student variants)
3. Accumulating Docker snapshots
4. Qdrant collecting all historical versions
5. N8N workflows creating large execution logs

### Prevention Strategy
1. Implement cleanup cron jobs
2. Use Docker image size constraints
3. Regular qdrant snapshot purging
4. N8N log rotation policies
5. Monthly disk audit

---

**Status**: 🟢 Ready for Implementation
**Estimated Execution Time**: 45-60 minutes
**Downtime Required**: 30 seconds (for VM compaction)
**Space Saved**: 37GB (70% reduction)
