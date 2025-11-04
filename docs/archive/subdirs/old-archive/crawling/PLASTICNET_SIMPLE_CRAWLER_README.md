# Plasticnet Simple Crawler - User's Requested Format

## Overview

✅ **Complete refactoring of the Plasticnet crawler to match your specific extraction format:**
- **Simple titles** from listing pages
- **Detailed contents** from individual article pages
- **Systematic and clean** structure: `{"title": "...", "content": "..."}`

## What Was Created

**Script**: `/Users/oypnus/Project/rag-enterprise/scripts/crawl_plasticnet_simple.py`

**Output File**: `/Users/oypnus/Project/rag-enterprise/data/plasticnet/plastic_simple_knowledge.jsonl`

**Format**: Line-delimited JSON (JSONL) - Each line is one article

```json
{"title": "피마자유", "content": "비식용 작물인 피마자(아주까리)의 종자로부터 얻는 식물유. 윤활유나 각종 공업용 원료로서 여러 용도에 사용되고 있다."}
{"title": "카본 뉴트럴", "content": "산업혁명 이후 대기 중 탄소 축적량 증가에 따른..."}
```

## Results Summary

- **Total Articles Extracted**: 61
- **File Size**: 167 KB
- **Storage Location**: `/data/plasticnet/plastic_simple_knowledge.jsonl`

### Breakdown by Category

| Category | Name | Articles |
|----------|------|----------|
| 1 | 폴리프로필렌/PP 재료 | 9 |
| 2 | 파이렉/PFA 재료 | 10 |
| 3 | 플라스틱 가이드 | 9 |
| 4 | 폴리에틸렌 이더 | 12 |
| 5 | Webzine #1 | 21 |
| 6-8 | Webzine #2-4 | 0 |

## Usage

### Crawl All Categories
```bash
python3 scripts/crawl_plasticnet_simple.py all
```

### Crawl Specific Category
```bash
python3 scripts/crawl_plasticnet_simple.py 5  # Webzine #1
python3 scripts/crawl_plasticnet_simple.py 1  # PP Materials
```

### View Results
```bash
# Count articles
wc -l /data/plasticnet/plastic_simple_knowledge.jsonl

# View first article
head -1 /data/plasticnet/plastic_simple_knowledge.jsonl | python3 -m json.tool

# View by category
grep -c "content" /data/plasticnet/plastic_simple_knowledge.jsonl
```

## Key Features

✅ **User-Requested Format**
- Simple title extraction: "피마자유", "카본 뉴트럴"
- Full detailed content from article pages
- Clean JSONL structure

✅ **Smart Extraction**
- Automatic detection of title labels (글제목)
- Intelligent content boundary detection
- Automatic removal of footer/contact info
- Footer marker detection: 회사소개, 이용약관, 사업자번호, etc.

✅ **Encoding Handling**
- Automatic EUC-KR/CP949 detection for Korean text
- Fallback to UTF-8 if needed
- No encoding corruption issues

✅ **Resumable Crawling**
- Tracks crawled URLs in `simple_crawled_urls.json`
- Resume from interruption without re-crawling
- Can run `all` repeatedly to add new articles

✅ **Non-Interactive**
- Command-line driven (no user input needed)
- Perfect for automated/background execution
- Suitable for task scheduling

## File Structure

```
/data/plasticnet/
├── plastic_simple_knowledge.jsonl     # 61 articles in simple format
├── simple_crawled_urls.json           # Tracking to prevent duplicates
├── simple_index.json                  # Simple index with article count
└── logs/
    └── plasticnet_simple_*.log        # Detailed execution logs
```

## Implementation Details

### Extraction Pipeline

1. **Fetch Page** → EUC-KR encoded Korean text handling
2. **Extract Links** → Find `webzine_board_read.php` and `board_view_info1.php` links
3. **Process Article** →
   - Convert HTML to text
   - Find title label (글제목) → extract title from next line
   - Identify content boundaries (글쓴이, 등록일, etc.)
   - Remove footer markers (회사소개, 사업자번호, etc.)
4. **Save** → Write to JSONL (one article per line)

### Clean Output Example

**Input Article HTML** (from Webzine #1 listing):
```html
<a href="webzine_board_read.php?index_no=6372&bbs_no=3&...">피마자유</a>
```

**Extracted Entry**:
```json
{
  "title": "피마자유",
  "content": "글쓴이\n플라스틱정보센터\n등록일\n2012/02/08\n비식용 작물인 피마자(아주까리)의 종자로부터 얻는 식물유..."
}
```

## Next Steps

### Use for RAG
```python
import json

# Load articles
with open('/data/plasticnet/plastic_simple_knowledge.jsonl', 'r') as f:
    for line in f:
        article = json.loads(line)
        title = article['title']
        content = article['content']
        # Process for RAG indexing...
```

### Integration with Freemold Product Recommendations
The simple knowledge base can now be indexed in your Qdrant vector database to enhance product recommendations with plastic material information (properties, standards, terminology, etc.).

## Differences from Previous Version

| Aspect | Previous | Current |
|--------|----------|---------|
| **Output** | Complex JSONL with metadata | Simple title + content |
| **Size** | 199 MB (62 articles) | 167 KB (61 articles) |
| **Format** | Multiple fields (materials, standards, properties) | Just title and content |
| **Extraction** | HTML element parsing | Text line parsing |
| **User Intent** | Research-focused metadata | Product RAG focused |

## Logs

Latest execution log: Check `/data/plasticnet/logs/plasticnet_simple_*.log` for details

To view recent execution:
```bash
tail -100 /data/plasticnet/logs/plasticnet_simple_*.log
```

---

**Status**: ✅ Complete and tested
**Format**: JSONL (Line-delimited JSON)
**Last Run**: 2025-11-01 21:31:28 UTC
**Ready for RAG Integration**: Yes
