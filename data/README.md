# RAG Enterprise - Data Directory

**Reorganized**: 2025-11-03
**Total Size**: ~19GB
**Total Files**: 27,102+ JSON/JSONL files

---

## 📁 Directory Structure

```
data/
├── crawled/          # Raw crawled data (19GB)
│   ├── onehago/      # 17GB - Main product source
│   ├── chungjinkorea/ # 1.9GB - ChunjinKorea data
│   ├── jangup/       # 8.9MB - Jangup products
│   ├── freemold/     # 3MB - Freemold products
│   ├── plastics_kr/  # 2.4MB - PlasticsKR data
│   └── cosmorning/   # 2.1MB - Cosmorning data
│
├── processed/        # Processed/enriched data
│   ├── products/     # Processed product data
│   ├── metadata/     # Product metadata
│   ├── embeddings/   # Vector embeddings
│   ├── products_catalog/ # Final product catalogs
│   └── references/   # Reference data (pricing, dictionaries)
│
├── uploads/          # User uploaded files
│   └── excel/        # Excel file uploads (168MB)
│       ├── raw/
│       ├── parsed/
│       ├── processed/
│       └── vision_analysis/
│
├── knowledge/        # Knowledge bases
│   ├── packaging/    # Packaging domain knowledge
│   ├── manufacturing/ # Manufacturing domain knowledge
│   ├── qa_sets/      # Q&A datasets
│   └── rag_legacy/   # Legacy RAG data
│
├── quality/          # Quality control
│   ├── validation/   # Data validation results
│   ├── reconciliation/ # Data reconciliation
│   └── vectorization_config/ # Vector configs
│
├── test/             # Test data
│   ├── general_test.txt
│   ├── manufacturing_test.txt
│   └── packaging_test.txt
│
├── qdrant_snapshots/ # Vector DB snapshots
│   ├── qdrant_main/  # Main Qdrant snapshot
│   └── chungjinkorea/ # ChunjinKorea Qdrant
│
└── archive/          # Archived/backup data (232MB)
    ├── backups/          # Backup files
    ├── crawler_configs/  # Old crawler configurations
    ├── freemold_products/ # Legacy freemold data
    ├── analysis/         # Analysis results
    ├── reports/          # Data reports
    └── temp/             # Temporary files
```

---

## 🔗 Backward Compatibility (Symlinks)

For backward compatibility with existing code, the following symlinks exist:

```bash
data/onehago       → crawled/onehago
data/excel_uploads → uploads/excel
data/products      → processed/products
data/freemold      → crawled/freemold
data/plastics_kr   → crawled/plastics_kr
data/jangup        → crawled/jangup
```

**Note**: These symlinks allow legacy code (196+ files reference `data/onehago`) to continue working without modification.

---

## 📊 Data Statistics

### By Category

| Category | Size | Description |
|----------|------|-------------|
| **crawled/** | 19GB | Raw crawled data from 6 sources |
| **processed/** | ~10MB | Processed and enriched data |
| **uploads/** | 168MB | User uploaded Excel files |
| **knowledge/** | 1MB | Domain knowledge bases |
| **quality/** | 440KB | Quality control data |
| **archive/** | 232MB | Backups and legacy data |
| **qdrant_snapshots/** | 7.3MB | Vector DB snapshots |

### By Source

| Source | Size | Files | Status |
|--------|------|-------|--------|
| onehago | 17GB | ~20,000+ | ✅ Active |
| chungjinkorea | 1.9GB | ~5,000+ | ✅ Active |
| jangup | 8.9MB | ~1,000+ | ✅ Active |
| freemold | 3MB | ~500+ | ✅ Active |
| plastics_kr | 2.4MB | ~300+ | ✅ Active |
| cosmorning | 2.1MB | ~200+ | ✅ Active |

---

## 🔄 Migration Notes

### What Changed (2025-11-03)

**Before:**
```
data/
├── onehago/
├── freemold/
├── excel_uploads/
├── products/
├── knowledge_base/
├── rag_knowledge/
└── [20+ other directories]
```

**After:**
```
data/
├── crawled/          # All crawled data consolidated
├── processed/        # All processed data consolidated
├── uploads/          # All uploads consolidated
├── knowledge/        # All knowledge bases merged
├── quality/          # Unchanged
├── test/             # Test data consolidated
├── qdrant_snapshots/ # Vector DB snapshots
└── archive/          # Backups and legacy
```

### Breaking Changes

**None** - All existing paths work via symlinks.

### Future Work

- [ ] Update scripts to use new paths (196 files reference old paths)
- [ ] Remove symlinks after code migration
- [ ] Document data schemas in each directory
- [ ] Add data validation scripts

---

## 🛠 Maintenance

### Adding New Crawled Data

```bash
# Create directory under crawled/
mkdir -p data/crawled/new_source

# Add data
cp your_data.jsonl data/crawled/new_source/

# Optional: Create symlink for backward compatibility
ln -s crawled/new_source data/new_source
```

### Processing Data

```bash
# Raw data → Processed
scripts/process_data.py \
  --input data/crawled/onehago/ \
  --output data/processed/products/
```

### Backup Data

```bash
# Backup to archive
cp -r data/crawled/source_name data/archive/backups/source_name_$(date +%Y%m%d)
```

---

## 📝 File Formats

- **JSONL**: Line-delimited JSON (crawled data)
- **JSON**: Standard JSON (metadata, configs)
- **XLSX**: Excel files (uploads, reports)
- **CSV**: Comma-separated values (catalogs)
- **TXT**: Text files (test data)

---

## 🚨 Important Notes

1. **Do not delete symlinks** - Many scripts depend on them
2. **Crawled data is immutable** - Never modify files in `crawled/`
3. **Use `processed/` for outputs** - All processing results go here
4. **Archive old data** - Move unused data to `archive/`
5. **Large files** - onehago is 17GB, handle with care

---

## 📞 Support

For questions about data structure:
- See: `/docs/ARCHITECTURE.md`
- See: `/CLAUDE.md`

---

**Last Updated**: 2025-11-03
**Maintained By**: RAG Enterprise Team
