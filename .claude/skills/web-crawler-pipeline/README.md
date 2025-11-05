# Web Crawler Pipeline Skill

Production-grade web crawling pipeline with authentication support, validation, deduplication, and data governance.

## ✨ Features

- **Complete Pipeline**: Crawl → Validate → Dedupe → Integrate → Publish
- **Authentication Support**: None, Cookie, Session, OAuth
- **3-Level Validation**: Schema (L1), Completeness (L2), Relationships (L3)
- **Checkpoint & Rollback**: Recovery from any pipeline stage
- **Auto-Repair**: Intelligent data quality fixing
- **Progress Tracking**: JSON-based checkpoint system

## 📦 Installation

The skill is already installed at:
```
.claude/skills/web-crawler-pipeline/
├── SKILL.md         # Comprehensive documentation (1000+ lines)
├── skill.py         # Executable wrapper
└── README.md        # This file
```

## 🚀 Quick Start

### 1. Initialize Pipeline

**For credential-free sites (like onehago.com):**
```bash
python3 .claude/skills/web-crawler-pipeline/skill.py init \
  --site onehago.com \
  --auth none
```

**For credential-required sites (like freemold.net):**
```bash
python3 .claude/skills/web-crawler-pipeline/skill.py init \
  --site freemold.net \
  --auth cookie \
  --auth-file data/freemold/credentials/cookies.json
```

### 2. Start Crawling

```bash
python3 .claude/skills/web-crawler-pipeline/skill.py crawl \
  --site onehago.com \
  --mode full \
  --workers 4
```

### 3. Validate Data (L1: Schema)

```bash
python3 .claude/skills/web-crawler-pipeline/skill.py validate \
  --site onehago.com \
  --level L1 \
  --auto-fix
```

### 4. Deduplicate

```bash
python3 .claude/skills/web-crawler-pipeline/skill.py dedupe \
  --site onehago.com \
  --strategy priority
```

### 5. Validate Completeness (L2)

```bash
python3 .claude/skills/web-crawler-pipeline/skill.py validate \
  --site onehago.com \
  --level L2
```

### 6. Integrate & Normalize

```bash
python3 .claude/skills/web-crawler-pipeline/skill.py integrate \
  --site onehago.com \
  --normalize
```

### 7. Validate Relationships (L3)

```bash
python3 .claude/skills/web-crawler-pipeline/skill.py validate \
  --site onehago.com \
  --level L3
```

### 8. Publish to Production

```bash
python3 .claude/skills/web-crawler-pipeline/skill.py publish \
  --site onehago.com \
  --target production
```

## 📊 Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `init` | Initialize pipeline structure | `--site example.com --auth none` |
| `crawl` | Execute web crawling | `--site example.com --workers 4` |
| `validate` | Run validation (L1/L2/L3/all) | `--level L1 --auto-fix` |
| `dedupe` | Remove duplicates | `--strategy priority` |
| `integrate` | Integrate and normalize | `--normalize` |
| `publish` | Publish to production | `--target production --dry-run` |
| `status` | Show pipeline status | `--site example.com` |
| `rollback` | Rollback to checkpoint | `--checkpoint-id crawl_completed` |
| `repair` | Auto-repair data issues | `--auto-fix` |
| `report` | Generate pipeline report | `--format json` |

## 🔐 Authentication Types

### 1. None (Public Sites)
```bash
--auth none
```
- No authentication required
- Simple HTTP requests
- Example: onehago.com

### 2. Cookie-Based
```bash
--auth cookie --auth-file cookies.json
```
- Browser-exported cookies
- Session persistence
- Example: freemold.net

### 3. Session-Based
```bash
--auth session --auth-file session.json
```
- Login credentials
- Automatic session management
- API token support

### 4. OAuth
```bash
--auth oauth --auth-file oauth_token.json
```
- OAuth 2.0 flow
- Token refresh handling

## 📁 Data Structure

After initialization, the pipeline creates:

```
data/{site_name}/
├── raw/                    # Raw crawled data
├── validated/              # L1 validated data
├── deduped/               # Deduplicated data
├── integrated/            # Integrated & normalized
├── production/            # Published data
├── checkpoints/           # Recovery checkpoints
├── logs/                  # Execution logs
└── config.json           # Pipeline configuration
```

## 🔍 Validation Levels

### L1: Schema Validation (Post-Crawl)
- Required fields check
- Data type validation
- JSON schema compliance
- **Output**: `validated/` directory

### L2: Completeness Check (Pre-Integration)
- Quality score calculation (0-100)
- Minimum 70% threshold
- Field coverage analysis
- **Output**: Completeness metrics

### L3: Relationship Integrity (Post-Integration)
- Referential integrity
- Foreign key validation
- Entity relationship checks
- **Output**: Relationship validation report

## 📈 Quality Scoring

Products are scored 0-100 based on:

| Field | Points | Description |
|-------|--------|-------------|
| Product Name | 20 | Must have valid name |
| Images | 30 | 20 for any images, +10 for 3+ |
| Specifications | 25 | 25 for 3+ specs, 15 for some |
| Company Info | 15 | Company name or ID |
| Valid URLs | 10 | Working HTTP/HTTPS URL |

**Completeness Threshold**: 70 points

## 🔄 Checkpoint & Recovery

### View Status
```bash
python3 skill.py status --site onehago.com
```

### Rollback to Checkpoint
```bash
python3 skill.py rollback \
  --site onehago.com \
  --checkpoint-id validate_L1_completed
```

### Auto-Repair Issues
```bash
python3 skill.py repair \
  --site onehago.com \
  --auto-fix
```

## 📊 Reports

### Text Format (Default)
```bash
python3 skill.py report --site onehago.com --format text
```

### JSON Format
```bash
python3 skill.py report --site onehago.com --format json
```

## 🎯 Use Cases

### Case 1: Credential-Free Site (Onehago)
```bash
# Initialize
python3 skill.py init --site onehago.com --auth none

# Crawl
python3 skill.py crawl --site onehago.com --workers 8

# Full validation
python3 skill.py validate --site onehago.com --level all --auto-fix

# Dedupe and integrate
python3 skill.py dedupe --site onehago.com --strategy priority
python3 skill.py integrate --site onehago.com --normalize

# Publish
python3 skill.py publish --site onehago.com --target production
```

### Case 2: Credential-Required Site (Freemold)
```bash
# Initialize with cookies
python3 skill.py init \
  --site freemold.net \
  --auth cookie \
  --auth-file data/freemold/credentials/cookies.json

# Crawl with authentication
python3 skill.py crawl \
  --site freemold.net \
  --workers 4 \
  --auth-file data/freemold/credentials/cookies.json

# Continue with validation and publishing...
python3 skill.py validate --site freemold.net --level all
python3 skill.py dedupe --site freemold.net --strategy merge
python3 skill.py integrate --site freemold.net --normalize
python3 skill.py publish --site freemold.net --target production
```

## 🔧 Advanced Options

### Deduplication Strategies

#### Priority Strategy (Default)
Keep the record with highest quality score:
```bash
--strategy priority
```

#### Merge Strategy
Combine data from all duplicates:
```bash
--strategy merge
```

### Dry Run Publishing
Preview what will be published:
```bash
--dry-run
```

### Multiple Validation Levels
Run all validations at once:
```bash
--level all
```

## 📝 Configuration File

Each site's `config.json` tracks:

```json
{
  "site": "onehago.com",
  "auth_type": "none",
  "created_at": "2025-01-25T10:00:00",
  "pipeline_version": "1.0.0",
  "stages": {
    "init": "completed",
    "crawl": "completed",
    "validate_L1": "completed",
    "dedupe": "pending",
    "validate_L2": "pending",
    "integrate": "pending",
    "validate_L3": "pending",
    "publish": "pending"
  },
  "published_at": null,
  "published_file": null
}
```

## 🐛 Troubleshooting

### Issue: Validation Fails
**Solution**: Use auto-fix
```bash
python3 skill.py validate --site example.com --level L1 --auto-fix
```

### Issue: Need to Restart Pipeline
**Solution**: Rollback to last good checkpoint
```bash
python3 skill.py status --site example.com  # Check available checkpoints
python3 skill.py rollback --site example.com --checkpoint-id crawl_completed
```

### Issue: Data Quality Issues
**Solution**: Run auto-repair
```bash
python3 skill.py repair --site example.com --auto-fix
```

### Issue: Check Progress
**Solution**: View status report
```bash
python3 skill.py status --site example.com
python3 skill.py report --site example.com --format text
```

## 📚 Documentation

- **Comprehensive Guide**: See `SKILL.md` (1000+ lines)
- **Pipeline Flow**: 11-stage detailed process
- **Authentication**: Complete auth handling patterns
- **Quality Metrics**: Scoring algorithms and thresholds
- **Best Practices**: Production deployment guidelines

## 🎓 Learning Resources

### Example 1: Complete Pipeline for Onehago
See SKILL.md section "Complete Workflow Example"

### Example 2: Authenticated Crawling for Freemold
See SKILL.md section "Authentication Workflow"

### Example 3: Recovery from Failures
See SKILL.md section "Checkpoint and Rollback"

## 🔗 Related Files

- `data/onehago/DATA_GOVERNANCE.md` - Validation, Integration, Relationship definitions
- `data/onehago/crawled/production/PACKAGING_DATA_STRUCTURE.md` - Data structure docs
- `scripts/validate_image_coverage.py` - Image validation script

## 📊 Performance

- **Initialization**: < 1 second
- **Validation L1**: ~1 second per 1000 products
- **Validation L2**: ~2 seconds per 1000 products
- **Deduplication**: ~3 seconds per 10,000 products
- **Integration**: ~2 seconds per 10,000 products

## 🌟 Success Criteria

✅ **Pipeline Complete When:**
- All stages show "completed" in status
- L1 validation pass rate > 95%
- L2 completeness rate > 70%
- L3 relationship integrity confirmed
- Production file successfully created

## 📮 Support

For issues or questions:
1. Check `SKILL.md` comprehensive documentation
2. Review checkpoint logs in `{site}/logs/`
3. Use `--help` for command-specific guidance

---

**Version**: 1.0.0
**Created**: 2025-01-25
**Author**: Web Crawler Pipeline Skill
**License**: MIT
