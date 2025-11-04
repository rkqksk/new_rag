# Scripts Directory

**Reorganized**: 2025-11-03
**Active Scripts**: 12
**Archived Scripts**: 290+

---

## 🚀 Active Scripts (Production Ready)

### Deployment
```bash
deploy.sh          # Deploy application to production
rollback.sh        # Rollback to previous version
```

### Application Servers
```bash
run_chat_server.py      # Start chat/conversation server
run_comparison_server.py # Start product comparison server
```

### System Management
```bash
start_all.sh       # Start all services
start_frontend.sh  # Start frontend only
stop_all.sh        # Stop all services
```

### Documentation
```
README.md                        # This file
MONITOR_USAGE.md                 # Monitoring guide
PRODUCTION_CRAWLER_GUIDE.md      # Crawler operation guide
README_BACKGROUND_WORKERS.md     # Background worker guide
README_encoding_fix.md           # Encoding fix documentation
```

---

## 📁 Subdirectories

### crawlers/
Production crawler implementations (15 files)
- `chungjin_crawler.py` - ChunjinKorea crawler
- `complete_crawler.py` - Full-featured crawler
- `material_based_crawler.py` - Material-based crawling
- Browser automation utilities

### data_processing/
Data processing pipelines (3 files)
- Category organization scripts
- RAG embedding pipeline

### maintenance/
Maintenance utilities (1 file)
- Auto-documentation organizer

---

## 📦 Archive Structure

All legacy/experimental/test scripts have been moved to `archive/`:

```
archive/
├── crawlers/          # Old crawler versions (150+ files)
│   ├── onehago_*.py   # Onehago crawler iterations
│   ├── freemold_*.py  # Freemold crawler iterations
│   ├── crawl_*.py     # Various crawler experiments
│   └── phase*.py      # Phase-based crawlers
│
├── analysis/          # Analysis & test scripts (50+ files)
│   ├── analyze_*.py
│   ├── test_*.py
│   ├── debug_*.py
│   └── investigate_*.py
│
├── data_processing/   # Data processing one-offs (40+ files)
│   ├── fix_*.py
│   ├── update_*.py
│   ├── add_*.py
│   └── enhance_*.py
│
├── monitoring/        # Monitoring scripts (20+ files)
│   ├── monitor_*.py
│   ├── check_*.py
│   └── validation_*.py
│
├── deployment/        # Launcher scripts (30+ files)
│   ├── launch_*.sh
│   ├── run_*.sh
│   └── restart_*.sh
│
├── setup/             # Setup scripts (15+ files)
│   ├── setup_*.sh
│   ├── install_*.sh
│   └── cleanup.sh
│
├── one_off/           # One-time utilities (50+ files)
│   ├── batch_*.py
│   ├── calculate_*.py
│   ├── convert_*.py
│   └── reorganize_*.py
│
└── experiments/       # Experimental code (30+ files)
    ├── *_test.py
    ├── *_worker.py
    └── *_orchestrator.py
```

**Total Archived**: 290+ scripts

---

## 📊 Statistics

### Before Cleanup
- Total scripts: 300+
- Organization: Chaotic
- Find things: Hard
- Maintainability: Poor

### After Cleanup
- Active scripts: 12
- Archived scripts: 290+
- Organization: Clear
- Find things: Easy
- Maintainability: Excellent

### Breakdown by Category

| Category | Active | Archived | Total |
|----------|--------|----------|-------|
| Deployment | 2 | 30 | 32 |
| Servers | 2 | 0 | 2 |
| Management | 3 | 0 | 3 |
| Documentation | 5 | 0 | 5 |
| Crawlers | 0 (subdir) | 150+ | 150+ |
| Analysis | 0 | 50+ | 50+ |
| Data Processing | 0 (subdir) | 40+ | 40+ |
| Others | 0 | 20+ | 20+ |

---

## 🔄 Usage

### Running Active Scripts

```bash
# Start services
./start_all.sh

# Run chat server
python run_chat_server.py

# Deploy to production
./deploy.sh

# Stop services
./stop_all.sh
```

### Accessing Archived Scripts

If you need an archived script:

```bash
# Find script in archive
find archive -name "*pattern*.py"

# Copy back if needed
cp archive/crawlers/old_crawler.py .

# Or run directly
python archive/experiments/test_feature.py
```

---

## 🛠 Maintenance

### Adding New Scripts

**For production scripts:**
1. Add to root level
2. Make executable: `chmod +x script.sh`
3. Update this README

**For experimental scripts:**
1. Add to appropriate `archive/` subdirectory
2. Document in subdirectory README

**For specialized scripts:**
1. Add to appropriate subdirectory (crawlers/, data_processing/, maintenance/)
2. Update subdirectory documentation

### Archiving Scripts

When a script is no longer actively used:

```bash
# Move to appropriate archive category
mv old_script.py archive/experiments/

# Update this README if it was listed
```

---

## 📝 Script Naming Conventions

### Active Scripts
- **Deployment**: `deploy.sh`, `rollback.sh`
- **Servers**: `run_*.py`
- **Management**: `start_*.sh`, `stop_*.sh`

### Archived Scripts
- **Crawlers**: `crawl_*.py`, `*_crawler.py`
- **Analysis**: `analyze_*.py`, `test_*.py`
- **Processing**: `fix_*.py`, `update_*.py`, `add_*.py`
- **Utilities**: `calculate_*.py`, `generate_*.py`
- **Phase-based**: `phase*.py`

---

## 🚨 Important Notes

1. **Do not delete archive/** - Scripts may be needed for reference
2. **Keep root clean** - Only essential production scripts at root
3. **Use subdirectories** - Specialized scripts go in crawlers/, data_processing/, maintenance/
4. **Document changes** - Update this README when adding/removing scripts
5. **Test before deleting** - Always move to archive first, don't delete

---

## 📞 Support

For questions about scripts:
- See: `/docs/ARCHITECTURE.md`
- See: `/CLAUDE.md`
- Check: `PRODUCTION_CRAWLER_GUIDE.md`
- Check: `MONITOR_USAGE.md`

---

**Last Updated**: 2025-11-03
**Maintained By**: RAG Enterprise Team
