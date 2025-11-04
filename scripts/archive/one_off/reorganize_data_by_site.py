#!/usr/bin/env python3
"""
Data Folder Reorganization: Site-based Structure

Move all existing chungjinkorea data to data/chungjinkorea/
Create empty data/freemold/ structure for new site
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/Users/oypnus/Project/rag-enterprise/data")

def create_site_structure():
    """Create site-based folder structure"""
    print("=" * 70)
    print("CREATING SITE-BASED DATA STRUCTURE")
    print("=" * 70)

    # Site folders
    sites = {
        "chungjinkorea": {
            "crawled_products": None,
            "products": None,
            "quality": None,
            "embeddings": None,
        },
        "freemold": {
            "crawled_products": None,
            "products": None,
            "quality": None,
            "embeddings": None,
        }
    }

    for site, folders in sites.items():
        site_path = BASE_DIR / site
        site_path.mkdir(parents=True, exist_ok=True)
        print(f"\n✅ Created: {site}/")

        for folder in folders.keys():
            folder_path = site_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Created: {site}/{folder}/")


def move_existing_data_to_chungjinkorea():
    """Move all existing data to chungjinkorea folder"""
    print("\n" + "=" * 70)
    print("MOVING EXISTING DATA TO chungjinkorea/")
    print("=" * 70)

    # Folders to move to chungjinkorea
    folders_to_move = [
        "crawled_products_final",
        "products",
        "quality",
        "excel_uploads",
        "manufacturing",
        "qdrant",
    ]

    chungjin_path = BASE_DIR / "chungjinkorea"

    for folder in folders_to_move:
        source = BASE_DIR / folder
        if source.exists():
            dest = chungjin_path / folder

            if dest.exists():
                print(f"⚠️ Destination already exists: {folder}")
                continue

            print(f"📦 Moving: {folder} → chungjinkorea/{folder}")
            shutil.move(str(source), str(dest))

    print("\n✅ Moved all chungjinkorea data")


def create_readme():
    """Create README files for each site"""
    print("\n" + "=" * 70)
    print("CREATING README FILES")
    print("=" * 70)

    # Chungjinkorea README
    chungjin_readme = BASE_DIR / "chungjinkorea" / "README.md"
    chungjin_content = f"""# Chungjinkorea Data

**Source**: http://chungjinkorea.com
**Crawled**: 2025-10-18
**Products**: ~1,245 products (Bottle, Jar, Cap, Pump)

## Structure

```
chungjinkorea/
├── crawled_products_final/  # Raw crawled JSON files
├── products/
│   └── metadata/            # Product dictionaries, pricing
├── quality/                 # Data quality reports
├── excel_uploads/           # Excel-imported data
└── qdrant/                  # Qdrant vector DB (chungjinkorea collection)
```

## Categories

- **Bottle**: PET, PETG, PP bottles (68 pages)
- **Jar**: Cream containers (4 pages)
- **Cap**: Caps and closures (15 pages)
- **Pump**: Pump dispensers (8 pages)

**Last Updated**: {datetime.now().strftime("%Y-%m-%d")}
"""

    with open(chungjin_readme, 'w', encoding='utf-8') as f:
        f.write(chungjin_content)
    print(f"✅ Created: chungjinkorea/README.md")

    # Freemold README
    freemold_readme = BASE_DIR / "freemold" / "README.md"
    freemold_content = f"""# Freemold Data

**Source**: https://www.freemold.net/
**Crawled**: Not yet
**Products**: TBD

## Structure

```
freemold/
├── crawled_products/        # Raw crawled JSON files
├── products/
│   └── metadata/            # Product dictionaries, pricing
├── quality/                 # Data quality reports
└── embeddings/              # Vector embeddings
```

## Categories

TBD - To be determined after site analysis

**Last Updated**: {datetime.now().strftime("%Y-%m-%d")}
"""

    with open(freemold_readme, 'w', encoding='utf-8') as f:
        f.write(freemold_content)
    print(f"✅ Created: freemold/README.md")


def update_data_readme():
    """Update main data/README.md"""
    print("\n" + "=" * 70)
    print("UPDATING data/README.md")
    print("=" * 70)

    readme_content = f"""# Data Folder Structure (Multi-Site)

**Version**: 3.0 (Site-based organization)
**Last Updated**: {datetime.now().strftime("%Y-%m-%d")}

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
**Last Updated**: {datetime.now().strftime("%Y-%m-%d")}
"""

    readme_path = BASE_DIR / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"✅ Updated: data/README.md")


def generate_summary():
    """Generate reorganization summary"""
    print("\n" + "=" * 70)
    print("REORGANIZATION SUMMARY")
    print("=" * 70)

    # Calculate sizes
    for site in ["chungjinkorea", "freemold"]:
        site_path = BASE_DIR / site
        if site_path.exists():
            size_output = os.popen(f"du -sh '{site_path}' 2>/dev/null").read().strip()
            if size_output:
                size = size_output.split()[0]
                print(f"📁 {site}/: {size}")

    # Common folders
    for folder in ["knowledge_base", "archive"]:
        folder_path = BASE_DIR / folder
        if folder_path.exists():
            size_output = os.popen(f"du -sh '{folder_path}' 2>/dev/null").read().strip()
            if size_output:
                size = size_output.split()[0]
                print(f"📁 {folder}/: {size}")


def main():
    """Main reorganization workflow"""
    print("\n" + "=" * 70)
    print("DATA FOLDER REORGANIZATION: SITE-BASED STRUCTURE")
    print("=" * 70)
    print(f"Base directory: {BASE_DIR}")
    print("=" * 70)

    print("\n🎯 Goal: Separate chungjinkorea and freemold data")
    print("   - Move existing data → chungjinkorea/")
    print("   - Create empty structure → freemold/")
    print("   - Keep knowledge_base/ and archive/ as common")

    try:
        # Step 1: Create site-based structure
        create_site_structure()

        # Step 2: Move existing data to chungjinkorea
        move_existing_data_to_chungjinkorea()

        # Step 3: Create README files
        create_readme()

        # Step 4: Update main README
        update_data_readme()

        # Step 5: Summary
        generate_summary()

        print("\n" + "=" * 70)
        print("✅ DATA REORGANIZATION COMPLETE!")
        print("=" * 70)
        print("\n📁 New Structure:")
        print("   data/chungjinkorea/  ← All existing data")
        print("   data/freemold/       ← Ready for new data")
        print("\n💡 Next Steps:")
        print("   1. Verify: ls -la data/chungjinkorea/")
        print("   2. Crawl freemold: python3 agents/crawlers/freemold_crawler.py")

    except Exception as e:
        print(f"\n❌ Error during reorganization: {e}")
        print("⚠️  Please check the data folder manually")
        raise


if __name__ == "__main__":
    main()
