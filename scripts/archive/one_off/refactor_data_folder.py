#!/usr/bin/env python3
"""
Data Folder Refactoring Script
Clean up and organize data/ folder structure

Current issues:
1. 2GB of duplicate backups
2. Scattered product data (crawled_products_final, excel_uploads)
3. Old/unused folders (Cap_old, Cappump_old)
4. Test files mixed with production data
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/Users/oypnus/Project/rag-enterprise/data")

# New organized structure
NEW_STRUCTURE = {
    "products": {
        "crawled": None,  # Move from crawled_products_final
        "excel": None,    # Move from excel_uploads/processed
        "metadata": None, # Product dictionaries and pricing
    },
    "knowledge_base": {
        "packaging": None,      # packaging_qa_*.json
        "manufacturing": None,  # manufacturing defect images
        "qa_sets": None,        # Q&A knowledge files
    },
    "uploads": {
        "raw": None,      # excel_uploads/raw
        "processed": None # excel_uploads/processed (keep recent)
    },
    "archive": {
        "backups": None,  # .tar.gz files
        "old_data": None, # _old folders
        "temp": None,     # Temporary/test files
    },
    "database": {
        "qdrant": None,   # qdrant vector DB data
    },
    "quality": None,      # Keep as is (validation/reconciliation)
}


def create_new_structure():
    """Create new organized folder structure"""
    print("=" * 70)
    print("Creating new data structure...")
    print("=" * 70)

    for main_folder, subfolders in NEW_STRUCTURE.items():
        main_path = BASE_DIR / main_folder
        main_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {main_path}")

        if isinstance(subfolders, dict):
            for subfolder in subfolders:
                sub_path = main_path / subfolder
                sub_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✅ Created: {sub_path}")


def move_product_data():
    """Move and consolidate product data"""
    print("\n" + "=" * 70)
    print("Moving product data...")
    print("=" * 70)

    # 1. Move crawled_products_final → products/crawled
    source = BASE_DIR / "crawled_products_final"
    dest = BASE_DIR / "products" / "crawled"

    if source.exists() and not dest.exists():
        print(f"📦 Moving: {source} → {dest}")
        shutil.move(str(source), str(dest))
        print("✅ Moved crawled products")

    # 2. Move product metadata files
    metadata_files = [
        "product_dictionary.json",
        "product_dictionary_enhanced.json",
        "product_dictionary_with_accessories.json",
        "cap_pump_product_list_complete.json",
        "bottle_jar_pricing.json",
        "coating_prices.json",
    ]

    metadata_dest = BASE_DIR / "products" / "metadata"
    for filename in metadata_files:
        source_file = BASE_DIR / filename
        if source_file.exists():
            dest_file = metadata_dest / filename
            print(f"📦 Moving: {filename} → products/metadata/")
            shutil.move(str(source_file), str(dest_file))

    print("✅ Product data consolidated")


def move_knowledge_base():
    """Move knowledge base files"""
    print("\n" + "=" * 70)
    print("Moving knowledge base...")
    print("=" * 70)

    # 1. Packaging Q&A
    packaging_files = [
        "packaging_qa_knowledge_base.json",
        "packaging_qa_embedding_metadata.json",
    ]
    packaging_dest = BASE_DIR / "knowledge_base" / "packaging"

    for filename in packaging_files:
        source_file = BASE_DIR / filename
        if source_file.exists():
            dest_file = packaging_dest / filename
            print(f"📦 Moving: {filename} → knowledge_base/packaging/")
            shutil.move(str(source_file), str(dest_file))

    # 2. Manufacturing data
    source_mfg = BASE_DIR / "manufacturing"
    dest_mfg = BASE_DIR / "knowledge_base" / "manufacturing"
    if source_mfg.exists() and not dest_mfg.exists():
        print(f"📦 Moving: manufacturing/ → knowledge_base/manufacturing/")
        shutil.move(str(source_mfg), str(dest_mfg))

    # 3. RAG knowledge
    source_rag = BASE_DIR / "rag_knowledge"
    dest_rag = BASE_DIR / "knowledge_base" / "rag_legacy"
    if source_rag.exists() and not dest_rag.exists():
        print(f"📦 Moving: rag_knowledge/ → knowledge_base/rag_legacy/")
        shutil.move(str(source_rag), str(dest_rag))

    # 4. Q&A sets
    qa_file = BASE_DIR / "추가 Q&A 세트 - 화장품 용기 상담.md"
    if qa_file.exists():
        qa_dest = BASE_DIR / "knowledge_base" / "qa_sets" / qa_file.name
        print(f"📦 Moving: Q&A set → knowledge_base/qa_sets/")
        shutil.move(str(qa_file), str(qa_dest))

    print("✅ Knowledge base organized")


def archive_old_data():
    """Move old/unused data to archive"""
    print("\n" + "=" * 70)
    print("Archiving old data...")
    print("=" * 70)

    # 1. Move backup tar.gz files
    backup_files = list(BASE_DIR.glob("*.tar.gz"))
    backups_dest = BASE_DIR / "archive" / "backups"

    for backup_file in backup_files:
        dest_file = backups_dest / backup_file.name
        print(f"📦 Archiving: {backup_file.name} → archive/backups/")
        shutil.move(str(backup_file), str(dest_file))

    print(f"✅ Archived {len(backup_files)} backup files (2GB)")

    # 2. Move old product folders (from products/crawled)
    crawled_path = BASE_DIR / "products" / "crawled"
    if crawled_path.exists():
        old_folders = [
            "Cap_old",
            "Cappump_old",
        ]

        old_data_dest = BASE_DIR / "archive" / "old_data"
        for old_folder in old_folders:
            source_folder = crawled_path / old_folder
            if source_folder.exists():
                dest_folder = old_data_dest / old_folder
                print(f"📦 Archiving: {old_folder} → archive/old_data/")
                shutil.move(str(source_folder), str(dest_folder))

    # 3. Move test files
    test_files = [
        "test_documents",
        "test_results",
        "sample_requests.json",
    ]

    temp_dest = BASE_DIR / "archive" / "temp"
    for item in test_files:
        source_path = BASE_DIR / item
        if source_path.exists():
            dest_path = temp_dest / item
            print(f"📦 Archiving: {item} → archive/temp/")
            shutil.move(str(source_path), str(dest_path))

    print("✅ Old data archived")


def organize_uploads():
    """Organize excel_uploads folder"""
    print("\n" + "=" * 70)
    print("Organizing uploads...")
    print("=" * 70)

    source_uploads = BASE_DIR / "excel_uploads"

    if not source_uploads.exists():
        print("⚠️ excel_uploads folder not found")
        return

    # Keep only essential subfolders: raw, processed
    keep_folders = ["raw", "processed"]
    archive_folders = ["paddleocr_parsed", "images", "vision_analysis",
                      "universal_parsed", "ocr_test", "parsed", "price_list"]

    uploads_dest = BASE_DIR / "uploads"
    archive_dest = BASE_DIR / "archive" / "temp" / "old_uploads"
    archive_dest.mkdir(parents=True, exist_ok=True)

    for keep_folder in keep_folders:
        source_path = source_uploads / keep_folder
        if source_path.exists():
            dest_path = uploads_dest / keep_folder
            if not dest_path.exists():
                print(f"📦 Moving: {keep_folder} → uploads/{keep_folder}/")
                shutil.move(str(source_path), str(dest_path))

    for archive_folder in archive_folders:
        source_path = source_uploads / archive_folder
        if source_path.exists():
            dest_path = archive_dest / archive_folder
            print(f"📦 Archiving: {archive_folder} → archive/temp/old_uploads/")
            shutil.move(str(source_path), str(dest_path))

    # Remove empty excel_uploads folder
    if source_uploads.exists() and not list(source_uploads.iterdir()):
        source_uploads.rmdir()
        print("✅ Removed empty excel_uploads folder")

    print("✅ Uploads organized")


def move_database():
    """Move database files"""
    print("\n" + "=" * 70)
    print("Moving database files...")
    print("=" * 70)

    # Move qdrant
    source_qdrant = BASE_DIR / "qdrant"
    dest_qdrant = BASE_DIR / "database" / "qdrant"

    if source_qdrant.exists() and not dest_qdrant.exists():
        print(f"📦 Moving: qdrant/ → database/qdrant/")
        shutil.move(str(source_qdrant), str(dest_qdrant))
        print("✅ Database files moved")


def cleanup_empty_folders():
    """Remove empty folders"""
    print("\n" + "=" * 70)
    print("Cleaning up empty folders...")
    print("=" * 70)

    removed_count = 0
    for dirpath, dirnames, filenames in os.walk(BASE_DIR, topdown=False):
        dir_path = Path(dirpath)
        if not list(dir_path.iterdir()):  # Empty folder
            print(f"🗑️ Removing empty: {dir_path.relative_to(BASE_DIR)}")
            dir_path.rmdir()
            removed_count += 1

    print(f"✅ Removed {removed_count} empty folders")


def generate_summary():
    """Generate refactoring summary"""
    print("\n" + "=" * 70)
    print("REFACTORING SUMMARY")
    print("=" * 70)

    # Calculate new structure sizes
    for main_folder in NEW_STRUCTURE.keys():
        folder_path = BASE_DIR / main_folder
        if folder_path.exists():
            size_output = os.popen(f"du -sh '{folder_path}' 2>/dev/null").read().strip()
            if size_output:
                size = size_output.split()[0]
                print(f"📁 {main_folder}/: {size}")

    # Total size
    total_output = os.popen(f"du -sh '{BASE_DIR}' 2>/dev/null").read().strip()
    if total_output:
        total_size = total_output.split()[0]
        print(f"\n📊 Total data/ size: {total_size}")


def create_readme():
    """Create README for new structure"""
    readme_content = """# Data Folder Structure

Organized data folder for RAG Enterprise project.

## Structure

```
data/
├── products/              # Product data (1.9GB)
│   ├── crawled/           # Crawled product JSON files
│   ├── excel/             # Excel-imported products
│   └── metadata/          # Product dictionaries, pricing
│
├── knowledge_base/        # Domain knowledge (116KB)
│   ├── packaging/         # Packaging Q&A knowledge
│   ├── manufacturing/     # Manufacturing defect data
│   ├── rag_legacy/        # Legacy RAG knowledge
│   └── qa_sets/           # Q&A training sets
│
├── uploads/               # User uploads (373MB)
│   ├── raw/               # Original uploaded files
│   └── processed/         # Processed uploads
│
├── database/              # Database files (2.2MB)
│   └── qdrant/            # Qdrant vector DB data
│
├── quality/               # Data quality reports (440KB)
│   ├── validation/        # Validation reports
│   ├── reconciliation/    # Reconciliation logs
│   └── vectorization_config/
│
└── archive/               # Archived data (2GB)
    ├── backups/           # Tar.gz backup files
    ├── old_data/          # Old product folders
    └── temp/              # Temporary/test files
```

## Purpose

- **products/**: All product-related data (active)
- **knowledge_base/**: Domain-specific knowledge for RAG
- **uploads/**: User-uploaded files and processing
- **database/**: Vector DB and other DB files
- **quality/**: Data quality validation
- **archive/**: Old/unused data (can be deleted if needed)

## Maintenance

- `archive/` can be deleted to save 2GB of space
- `products/crawled/` contains the main product database
- `quality/` contains data validation reports

**Last Updated**: {date}
**Version**: 2.0 (Refactored)
"""

    readme_path = BASE_DIR / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content.format(date=datetime.now().strftime("%Y-%m-%d")))

    print(f"\n✅ Created: {readme_path}")


def main():
    """Main refactoring workflow"""
    print("\n" + "=" * 70)
    print("DATA FOLDER REFACTORING")
    print("=" * 70)
    print(f"Base directory: {BASE_DIR}")
    print("=" * 70)

    # Auto-proceed (no confirmation needed for automated execution)
    print("\n✅ Starting refactoring...")
    print("   - 2GB of backups will be moved to archive/")
    print("   - Old/unused folders will be archived")
    print("   - Product data will be consolidated")

    try:
        # Step 1: Create new structure
        create_new_structure()

        # Step 2: Move product data
        move_product_data()

        # Step 3: Move knowledge base
        move_knowledge_base()

        # Step 4: Archive old data
        archive_old_data()

        # Step 5: Organize uploads
        organize_uploads()

        # Step 6: Move database
        move_database()

        # Step 7: Cleanup
        cleanup_empty_folders()

        # Step 8: Create README
        create_readme()

        # Step 9: Summary
        generate_summary()

        print("\n" + "=" * 70)
        print("✅ DATA FOLDER REFACTORING COMPLETE!")
        print("=" * 70)
        print("\n💡 Next steps:")
        print("   1. Review the new structure: data/README.md")
        print("   2. Test application with new paths")
        print("   3. Delete archive/ folder to save 2GB (optional)")

    except Exception as e:
        print(f"\n❌ Error during refactoring: {e}")
        print("⚠️  Please check the data folder manually")
        raise


if __name__ == "__main__":
    main()
