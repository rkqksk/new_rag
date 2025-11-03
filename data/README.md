# Data Folder Structure (Multi-Site)

**Version**: 3.0 (Site-based organization)
**Last Updated**: 2025-10-26

## Structure

```
data/
├── chungjinkorea/          # 청진코리아 데이터
│   ├── crawled_products_final/
│   ├── products/
│   ├── quality/
│   └── qdrant/
│
├── freemold/               # Freemold 데이터
│   ├── crawled_products/
│   ├── products/
│   └── quality/
│
├── knowledge_base/         # 공통 지식 베이스
│   ├── packaging/
│   ├── manufacturing/
│   └── qa_sets/
│
└── archive/                # 공통 아카이브
    ├── backups/
    └── old_data/
```

## Sites

### 1. Chungjinkorea (청진코리아)
- **URL**: http://chungjinkorea.com
- **Products**: ~1,245 (Bottle, Jar, Cap, Pump)
- **Status**: ✅ Active
- **Details**: See `chungjinkorea/README.md`

### 2. Freemold
- **URL**: https://www.freemold.net/
- **Products**: TBD
- **Status**: 🔄 Setting up
- **Details**: See `freemold/README.md`

## Common Folders

### knowledge_base/
Domain-specific knowledge shared across all sites:
- Packaging regulations (식약처, 환경부)
- Manufacturing standards (ISO, GMP)
- Q&A knowledge base

### archive/
Backup and old data:
- `backups/`: Tar.gz backup files
- `old_data/`: Deprecated data

## Usage

### Chungjinkorea Data
```bash
# Access chungjinkorea products
ls data/chungjinkorea/crawled_products_final/

# Load chungjinkorea to Qdrant
python3 scripts/load_to_qdrant.py --site chungjinkorea
```

### Freemold Data
```bash
# Crawl freemold products
python3 agents/crawlers/freemold_crawler.py

# Access freemold products
ls data/freemold/crawled_products/
```

## Maintenance

- Each site has independent data folders
- Common knowledge base shared across sites
- Archive folder for backups

**Version**: 3.0 (Site-based)
**Last Updated**: 2025-10-26
