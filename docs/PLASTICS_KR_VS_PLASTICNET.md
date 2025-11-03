# 📊 Plastics.kr vs Plasticnet: Complete Comparison

## Quick Reference

| Aspect | Plasticnet.kr | Plastics.kr |
|--------|---------------|------------|
| **Complexity** | 🔴 **HIGH** | 🟢 **LOW** |
| **HTML Type** | Legacy TABLE-based | Modern DIV-based |
| **Encoding** | EUC-KR/CP949 | UTF-8 |
| **Strategies** | 2 different | 1 unified |
| **Total Articles** | ~600 (8 categories) | ~1,138 (4 categories) |
| **Crawl Time** | 2-3 hours | ~1.5-2 hours |
| **Difficulty** | ⭐⭐⭐⭐⭐ | ⭐⭐ |

---

## 🔍 Structural Comparison

### Plasticnet.kr (What We Already Built)

```
HTML Structure (Complex)
├─ 35-46 TABLES per page
├─ 0 semantic HTML tags
├─ 20-21 article links per page
├─ Nested TABLE → TR → TD cells
└─ Legacy markup (pre-2010 style)

Content Types
├─ Categories 1-4: Material specifications (tables)
├─ Categories 5-8: Webzine articles (text)
└─ Different extraction needed per type

Encoding
├─ Primary: EUC-KR (Korean legacy)
├─ Secondary: CP949 (Windows Korean)
└─ Fallback: UTF-8

URL Structure
├─ /board_view_info1.php (products)
├─ /webzine_board_read.php (articles)
└─ ?page=X&bbs_no=Y parameters

Pagination
├─ Simple numeric links: 1, 2, 3, 4, 5...
└─ Up to 50 pages per category
```

**Result**: Two specialized extraction strategies needed
- `extract_material_specs()` for product specs (Categories 1-4)
- `extract_webzine_article()` for articles (Categories 5-8)

---

### Plastics.kr (What We Need to Build)

```
HTML Structure (Modern)
├─ 98 DIVs per page
├─ 4 ARTICLE semantic tags
├─ 18 list elements
├─ 0 TABLES (!)
├─ CSS classes: "item" (39), "auto-article" (4)
└─ Standard modern HTML

Content Type
├─ All categories: News articles
├─ Consistent structure
├─ Same extraction method for all
└─ No content variation

Encoding
├─ UTF-8 (standard, no workarounds needed)
└─ No legacy encoding issues

URL Structure
├─ /articleList.html (listing pages)
├─ /article_view.html (detail pages)
└─ ?sc_section_code=S1N#&page=X parameters

Pagination
├─ Numbered links in list: 1, 2, 3...
├─ S1N1: Up to 50 pages
├─ S1N2, S1N3: 2 pages each
└─ S1N4: Up to 5 pages
```

**Result**: Single unified extraction strategy works everywhere
- `extract_article_content()` handles all categories
- No special cases needed

---

## 🛠️ Extraction Complexity Comparison

### Plasticnet: Complex Multi-Strategy

**Material Specs Strategy (Categories 1-4)**:
```python
def extract_material_specs(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Navigate: TABLES → ROWS → CELLS
    title = extract_heading(soup)

    # Extract all table content (product specs)
    content_parts = []
    for table in soup.find_all('table'):
        # Complex table traversal
        for row in table.find_all('tr'):
            for cell in row.find_all('td'):
                # Extract cell content

    return {'title': title, 'content': '\n'.join(content_parts)}
```

**Webzine Article Strategy (Categories 5-8)**:
```python
def extract_webzine_article(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Different approach: text-based
    title = find_main_heading(soup)
    all_text = get_all_text(soup)
    lines = clean_and_remove_footer(all_text)

    return {'title': title, 'content': '\n'.join(lines)}
```

**Why Two Strategies?**
- Material specs in tables vs articles in text
- Different content structures
- Different extraction approaches
- Product pages vs article pages are fundamentally different

---

### Plastics.kr: Single Unified Strategy

**Unified Article Strategy (All Categories)**:
```python
def extract_article_content(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Same approach for all categories
    title = soup.find('h1', class_='title').get_text(strip=True)
    content_div = soup.find('div', class_='content')
    content = content_div.get_text(separator='\n', strip=True)

    return {'title': title, 'content': content, 'type': 'news_article'}
```

**Why One Strategy?**
- All content is news articles (not mixed types)
- Consistent HTML structure across all categories
- Same CSS classes everywhere
- Same extraction logic works for S1N1, S1N2, S1N3, S1N4

**Code Simplicity**:
- Plasticnet: ~400 lines (with 2 strategies + encoding workarounds)
- Plastics.kr: ~200 lines (single strategy + standard UTF-8)

---

## 📈 Coverage Comparison

### Plasticnet.kr

```
Categories: 8 (4 products + 4 webzine)
Articles per page: 10-21 (varies by type)
Pages per category: 2-5 (tested)

Estimated Coverage:
├─ Category 1 (Materials): 10 articles/page × 3 pages = 30
├─ Category 2 (Materials): 10 articles/page × 3 pages = 30
├─ Category 3 (Materials): 10 articles/page × 3 pages = 30
├─ Category 4 (Materials): 10 articles/page × 3 pages = 30
├─ Category 5 (Webzine): 21 articles/page × 3 pages = 63
├─ Category 6 (Webzine): 20 articles/page × 3 pages = 60
├─ Category 7 (Webzine): 20 articles/page × 3 pages = 60
└─ Category 8 (Webzine): 20 articles/page × 3 pages = 60

TOTAL: ~363 articles (at 3 pages per category)
```

### Plastics.kr

```
Categories: 4 (all news articles)
Articles per page: 112 (consistent!)
Estimated pages: 50 + 2 + 2 + 5 = 59 pages

Coverage Breakdown:
├─ S1N1 (Latest): 112 articles/page × 50 pages ≈ 992 articles
├─ S1N2 (News): 112 articles/page × 2 pages ≈ 32 articles
├─ S1N3 (Features): 112 articles/page × 2 pages ≈ 24 articles
└─ S1N4 (Media): 112 articles/page × 5 pages ≈ 90 articles

TOTAL: ~1,138 articles (all pages)
```

**Comparison**: Plastics.kr has **3x more articles** despite being simpler!

---

## ⏱️ Implementation Timeline

### Plasticnet: Full Refactoring (What We Did)

```
Phase 1: Structural Analysis
├─ Create analysis script
├─ Discover HTML patterns (tables vs semantic tags)
├─ Identify two content types
└─ Time: 30 minutes

Phase 2: Multi-Strategy Implementation
├─ Build material_specs extractor
├─ Build webzine_article extractor
├─ Implement TABLE parsing
├─ Add EUC-KR/CP949 encoding logic
├─ Time: 2-3 hours

Phase 3: Pagination & Resume
├─ Implement pagination detection
├─ Add URL deduplication
├─ Build progress tracking
├─ Time: 1-2 hours

Phase 4: Testing & Validation
├─ Test Category 1 (20 articles)
├─ Test Category 5 (42 articles)
├─ Validate encoding (Korean text)
└─ Time: 30 minutes

TOTAL EFFORT: ~5-6 hours
STATUS: ✅ COMPLETE AND TESTED
```

### Plastics.kr: Simple Implementation (What We Should Do)

```
Phase 1: Crawler Implementation
├─ Create crawl_plastics_kr.py
├─ Implement single extraction strategy
├─ Add pagination loop
├─ Add progress tracking
└─ Time: 1-2 hours

Phase 2: Testing & Validation
├─ Test on S1N4 (5 pages, ~90 articles)
├─ Verify extraction quality (10 samples)
├─ Check output format (JSONL)
└─ Time: 30 minutes

Phase 3: Full Crawl
├─ Run S1N4 → S1N3 → S1N2 → S1N1
├─ Monitor progress
├─ Validate 1,138 articles extracted
└─ Time: ~2 hours

TOTAL EFFORT: ~4 hours
STATUS: ✅ READY TO IMPLEMENT
```

---

## 🎯 Key Learnings from Plasticnet

The Plasticnet crawler taught us important patterns that apply to Plastics.kr:

### ✅ What Worked Well (Reuse These)
```python
# 1. Pagination loop structure
current_url = category_url
pages_crawled = 0
while pages_crawled < max_pages and current_url:
    # Process page
    current_url = get_next_page()
    pages_crawled += 1

# 2. URL deduplication to prevent re-crawling
crawled_urls = load_crawled_urls()
if url not in crawled_urls:
    # Process article
    crawled_urls.add(url)

# 3. Progress tracking for resumable crawling
progress = {
    'last_page': current_page,
    'articles_count': total_articles,
    'timestamp': datetime.now()
}
save_progress(progress)

# 4. JSONL output format (line-delimited JSON)
with open('output.jsonl', 'a') as f:
    for article in articles:
        f.write(json.dumps(article, ensure_ascii=False) + '\n')
```

### ❌ What We Can Skip (Plastics.kr Doesn't Need)
```python
# ❌ NO NEED: Legacy encoding workarounds
# Plastics.kr uses standard UTF-8
response.encoding = 'euc-kr'  # NOT NEEDED
response.encoding = 'cp949'   # NOT NEEDED

# ❌ NO NEED: Multiple extraction strategies
# Single strategy works for all categories
if strategy == 'material_specs':   # NOT NEEDED
    ...
elif strategy == 'webzine':       # NOT NEEDED
    ...

# ❌ NO NEED: Complex table parsing
# Plastics.kr uses simple DIV selectors
for table in soup.find_all('table'):  # NOT NEEDED
    for row in table.find_all('tr'):  # NOT NEEDED
        ...

# ✅ DO NEED: Simple DIV selector
for item in soup.find_all('div', class_='item'):  # ✅ SIMPLE
    ...
```

---

## 📋 Plastics.kr Crawler Checklist

**Ready to Implement** ✅

- [x] Structural analysis complete
- [x] HTML patterns identified
- [x] Extraction strategies defined
- [x] URL structure understood
- [x] Pagination logic designed
- [x] Encoding confirmed (UTF-8)
- [ ] **crawler script created** ← Next step
- [ ] **testing on S1N4** ← Then this
- [ ] **full crawl (all categories)** ← Then this
- [ ] **validation (1,138 articles)** ← Finally this

---

## 🚀 Recommended Implementation Order

### Step 1: Build Core Crawler (~1 hour)
```bash
scripts/crawl_plastics_kr.py
├── fetch_page(url)
├── extract_article_links(html)
├── extract_pagination_url(html)
├── extract_article_content(html)
├── crawl_category(category_code, max_pages)
└── main()
```

### Step 2: Test on Small Category (~10 minutes)
```bash
python3 scripts/crawl_plastics_kr.py S1N4
# Expected: ~90 articles in 10 minutes
```

### Step 3: Validate Sample (~10 minutes)
```bash
# Check 10 random articles for quality
head -10 data/plastics_kr/plastic_news_articles.jsonl | python3 -m json.tool
```

### Step 4: Run Full Crawl (~2 hours)
```bash
python3 scripts/crawl_plastics_kr.py all
# Expected: ~1,138 articles total
# Time: 90-110 minutes
```

---

## 📊 Success Criteria

**Implementation Complete When:**

✅ `crawl_plastics_kr.py` created and functional
✅ S1N4 test produces ~90 articles in 10 minutes
✅ Sample articles validated (title + content present)
✅ All 4 categories crawled successfully
✅ Final file contains ~1,138 articles
✅ JSONL format correct (one valid JSON per line)
✅ No encoding errors in Korean text
✅ Progress tracking enabled (resume capability)

---

**Status**: 📋 **STRATEGY COMPLETE**
**Next**: 🛠️ **IMPLEMENTATION PHASE**

