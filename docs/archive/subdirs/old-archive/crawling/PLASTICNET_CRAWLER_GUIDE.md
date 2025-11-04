# 🚀 Plasticnet Interactive Knowledge Crawler Guide

## Overview

This tool provides **interactive, individual category crawling** for plasticnet.kr with full pagination support and proper URL handling.

## Quick Start

### 1. Prerequisites

```bash
# Selenium is already installed
pip3 install selenium

# You also need ChromeDriver (already installed on your Mac)
which chromedriver
```

### 2. Run the Interactive Crawler

```bash
cd /Users/oypnus/Project/rag-enterprise
python3 scripts/crawl_plasticnet_selenium_interactive.py
```

### 3. Menu Options

```
================================================================================
🚀 PLASTICNET INTERACTIVE CRAWLER
================================================================================

📚 Available Categories to Crawl:

  [1] 폴리프로필렌/PP 재료
  [2] 파이렉/PFA 재료
  [3] 플라스틱 가이드
  [4] 폴리에틸렌 이더
  [5] Webzine #1
  [6] Webzine #2
  [7] Webzine #3
  [8] Webzine #4

  [a] Crawl All Categories
  [s] Show Stats
  [q] Quit

👉 Select category (or command):
```

## Usage Examples

### Example 1: Crawl Category 1 (PP Materials)
```bash
# When prompted:
👉 Select category (or command): 1

# The crawler will:
# 1. Fetch the category page
# 2. Discover all pagination pages
# 3. Extract all article links from each page
# 4. Crawl each article and extract knowledge
# 5. Save to plastic_technical_knowledge.jsonl
# 6. Update the index

# After completion:
👉 Press Enter to return to menu...
```

### Example 2: Crawl Multiple Categories Sequentially
```bash
👉 Select category (or command): 1
# ... crawling completes ...
👉 Press Enter to return to menu...

👉 Select category (or command): 2
# ... crawling completes ...
👉 Press Enter to return to menu...

👉 Select category (or command): 3
# ... and so on ...
```

### Example 3: Crawl All Categories at Once
```bash
👉 Select category (or command): a

# The crawler will automatically process all 8 categories
# and pause after each one for you to check progress
```

### Example 4: View Statistics
```bash
👉 Select category (or command): s

# Shows:
# - Total Knowledge Items
# - Total Articles Crawled
# - Materials Indexed (9+ types)
# - Standards Indexed (5+ types)
# - Properties Indexed (6+ types)
```

## How It Works

### Browser Automation (Selenium)
- Opens a real Chrome browser instance
- Navigates to each URL automatically
- Waits for JavaScript rendering (3 second delay)
- Falls back to requests library if Selenium fails

### Pagination Discovery
The crawler automatically:
1. Detects pagination links on category pages
2. Extracts all `?page=X` parameters
3. Crawls each page sequentially
4. Extracts articles from all pages

### Article Extraction
For each article, the crawler extracts:
- **Title** (h1, h2, or h3)
- **Content** (all text from main content area)
- **Materials** (PET, HDPE, PP, PVC, etc.)
- **Standards** (ASTM, ISO, JIS, DIN, BS, KS, GB)
- **Properties** (strength, elasticity, density, heat resistance, etc.)
- **Tables** (specification tables up to 10)
- **Lists** (bullet points up to 20)
- **Metadata** (URL, crawl time, word count)

## Output Files

```
/Users/oypnus/Project/rag-enterprise/data/plasticnet/

├── plastic_technical_knowledge.jsonl    # All extracted knowledge (JSONL format)
├── knowledge_index.json                 # Indexed materials, standards, properties
├── crawl_progress.json                  # Crawling statistics and progress
├── crawled_urls.json                    # Set of already crawled URLs (for resuming)
└── logs/
    └── plasticnet_selenium_YYYYMMDD_HHMMSS.log    # Detailed crawl logs
```

### Knowledge Entry Example
```json
{
  "article_title": "PP 물성 비교 분석",
  "url": "https://plasticnet.kr/found/market/mbwshop/board_view_info1.php?...",
  "crawled_at": "2025-11-01T20:45:30.123456",
  "content_preview": "폴리프로필렌의 물성 비교 분석...",
  "materials_mentioned": ["PP", "HDPE"],
  "testing_standards": {
    "ASTM": "American Society for Testing and Materials",
    "ISO": "International Organization for Standardization"
  },
  "properties": ["강도", "탄성", "경도", "밀도", "내열성"],
  "tables": [[["Property", "PP", "HDPE"], ["Density", "0.91", "0.96"]]],
  "lists": ["MP는 탁월한 화학적 내성...", "온도 저항성이 우수함..."],
  "word_count": 1250
}
```

### Index File Example
```json
{
  "total_knowledge_items": 42,
  "materials": {
    "PP": 15,
    "HDPE": 8,
    "PC": 6,
    "PA": 5,
    "PVC": 4
  },
  "standards": {
    "ASTM": 25,
    "ISO": 18,
    "JIS": 12,
    "DIN": 8,
    "BS": 6
  },
  "properties": {
    "강도": 30,
    "탄성": 28,
    "밀도": 26,
    "내열성": 22
  },
  "crawled_at": "2025-11-01T20:45:30.123456"
}
```

## Features

### ✅ What's Implemented

- **Interactive Menu**: Choose categories individually
- **Full Pagination**: Auto-discovers and crawls all pages
- **Proper URL Handling**: Maintains `/found/market/mbwshop/` path prefix
- **Resumable Crawling**: Tracks crawled URLs to avoid duplicates
- **Korean Encoding**: Handles EUC-KR/CP949 encoding correctly
- **Fallback Support**: Uses requests library if Selenium fails
- **Progress Tracking**: Real-time logging and statistics
- **Index Building**: Automatically creates searchable index
- **Rate Limiting**: Respectful 0.5-1s delays between requests

### ⚠️ Limitations

- Selenium requires ChromeDriver (already available on your Mac)
- Each category may take 5-30+ minutes depending on pagination
- Browser window stays visible during crawling (you can work meanwhile)
- Requires active internet connection

## Troubleshooting

### Issue: "Selenium not installed"
```bash
pip3 install selenium
```

### Issue: "ChromeDriver not found"
```bash
# Check if installed
which chromedriver

# If not installed:
brew install chromedriver  # macOS

# Or download: https://chromedriver.chromium.org/
```

### Issue: "Connection timeout"
- Check your internet connection
- The site may be temporarily down (try again later)
- Try a smaller category first (Webzine pages are smaller)

### Issue: "404 errors on article links"
- This means the extracted URL format is incorrect
- The crawler has fallback logic but may skip some articles
- Check the log file: `data/plasticnet/logs/plasticnet_selenium_*.log`

## Advanced Usage

### Add a Custom Category

Edit `crawl_plasticnet_selenium_interactive.py` and add to `PLASTICNET_CATEGORIES`:

```python
PLASTICNET_CATEGORIES = {
    # ... existing categories ...
    "9": {
        "name": "Your Custom Category Name",
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?..."
    }
}
```

### Extend Material Keywords

Edit `PLASTIC_MATERIALS` to add new materials or aliases:

```python
PLASTIC_MATERIALS = {
    # ... existing ...
    'POM': ['polyoxymethylene', '폴리옥시메틸렌'],  # New material
}
```

### Change Rate Limiting

Search for `time.sleep()` calls and adjust the delays (in seconds):
- `time.sleep(0.5)` between articles
- `time.sleep(1)` between pages
- `time.sleep(3)` Selenium page load wait

## Integration with Freemold RAG

The extracted plasticnet knowledge can enhance Freemold product recommendations:

```python
# Load the knowledge base
with open('data/plasticnet/knowledge_index.json') as f:
    plastic_knowledge = json.load(f)

# Link to Freemold products
# When recommending a PP plastic container:
# 1. Find "PP" materials in plastic_knowledge
# 2. Extract properties and standards
# 3. Include in recommendation context
```

## Performance Notes

### Crawling Speed
- Small category (< 5 pages, < 20 articles): ~5-10 minutes
- Medium category (5-15 pages, 20-50 articles): ~15-30 minutes
- Large category (15+ pages, 50+ articles): 30+ minutes

### Data Size
- Per article: ~2-10 KB (depending on content length)
- Per category: ~50 KB - 500 KB
- Total knowledge base: Expected to reach 200+ MB with all categories

### Recommendations
- Start with one category to test
- Run larger categories overnight if needed
- Monitor `data/plasticnet/knowledge_index.json` to see growth

## Support

For issues or questions about the crawler:
1. Check the log file: `data/plasticnet/logs/plasticnet_selenium_*.log`
2. Verify ChromeDriver is installed: `which chromedriver`
3. Test manually visiting one of the category URLs
4. Review the "Troubleshooting" section above

---

**Ready to start?**

```bash
python3 scripts/crawl_plasticnet_selenium_interactive.py
```

Then select a category by typing its number (1-8) or command (a/s/q)!
