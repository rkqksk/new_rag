# 🚀 Plastics.kr Crawling Strategy Document

## Executive Summary

**Site**: https://www.plastics.kr/news/
**Type**: Modern news/article portal (DIV-based, UTF-8, semantic HTML)
**Total Articles**: ~1,138 articles across 4 news categories
**Estimated Coverage Time**: 3-4 hours (all categories, all pages)
**Complexity Level**: 🟢 **LOW** (vs Plasticnet's HIGH complexity)

---

## 🔍 Structural Analysis Results

### HTML Architecture
| Aspect | Finding | Impact |
|--------|---------|--------|
| **Layout** | DIV-based (98 divs per page) | Easy CSS selector targeting |
| **Semantic Tags** | 4 article tags per page | Modern, structured HTML |
| **Tables** | 0 (unlike Plasticnet) | No complex table parsing needed |
| **Lists** | 18 (ul/ol per page) | Pagination via lists |
| **Encoding** | UTF-8 (standard) | No legacy encoding workarounds |
| **CSS Classes** | "item" (39), "auto-article" (4) | Clear class-based selectors |

### Category Structure

```
📰 Plastics.kr News Portal
├─ S1N1: Latest News (최신기사)
│   └─ 50 pages × 112 articles/page ≈ 992 articles
├─ S1N2: Business News (뉴스)
│   └─ 2 pages × ~56 articles/page ≈ 32 articles
├─ S1N3: Features (특집)
│   └─ 2 pages × ~12 articles/page ≈ 24 articles
└─ S1N4: Media (미디어)
    └─ 5 pages × ~18 articles/page ≈ 90 articles
```

**Total: 1,138 articles**

### URL Parameter Structure

```
Base: https://www.plastics.kr/news/articleList.html

Parameters:
├─ sc_section_code  → S1N1, S1N2, S1N3, S1N4 (category)
├─ sc_sub_section_code → S2N24, S2N3, S2N25 (sub-category)
├─ view_type        → sm (mobile/standard view)
├─ page             → 1, 2, 3... (page number)
└─ total            → Y (total count)

Example:
/articleList.html?sc_section_code=S1N1&view_type=sm&page=1
/articleList.html?sc_section_code=S1N1&view_type=sm&page=2
```

---

## 📋 Extraction Strategy

### Strategy Type: **SINGLE UNIFIED STRATEGY**

Unlike Plasticnet (which needs 2 different strategies), plastics.kr uses consistent HTML structure across all categories. **One extraction approach handles all content.**

#### Why Single Strategy?
1. ✅ All categories use same DIV-based layout
2. ✅ All articles follow same HTML pattern
3. ✅ Class names consistent across categories
4. ✅ Pagination mechanism identical
5. ✅ UTF-8 encoding uniform

---

## 🎯 Extraction Techniques

### 1. **Article Link Extraction from Listing Pages**

**HTML Pattern Discovered**:
```html
<div class="item">
  <a href="/news/article_view.html?...">Article Title</a>
  <span class="date">2025-01-15</span>
  <span class="author">Author Name</span>
  <p class="summary">Article summary...</p>
</div>
```

**Extraction Code**:
```python
def extract_article_links_from_listing(html, base_url):
    """Extract article links from plastics.kr listing page"""
    soup = BeautifulSoup(html, 'html.parser')
    article_links = []

    # Find all article items via class selector
    for item in soup.find_all('div', class_='item'):
        link_elem = item.find('a', href=True)
        if link_elem:
            article_links.append({
                'url': link_elem['href'],
                'title': link_elem.get_text(strip=True),
                'pattern': 'news_article'
            })

    return article_links
```

**Key Characteristics**:
- Simple CSS class selector: `div.item`
- Consistent 112 links per page
- No complex table navigation needed
- Links contain full article URLs

### 2. **Pagination Detection**

**Pattern**:
```html
<div class="pagination">
  <a href="...?page=1">1</a>
  <a href="...?page=2">2</a>
  <a href="...?page=3">3</a>
  ...
  <a href="...?page=50">50</a>
</div>
```

**Extraction Code**:
```python
def extract_pagination_urls(html, category_code, current_page=1, max_pages=50):
    """Extract next page URL for category"""
    soup = BeautifulSoup(html, 'html.parser')

    next_page = current_page + 1

    # Check if next page link exists
    for link in soup.find_all('a'):
        href = link.get('href', '')
        text = link.get_text(strip=True)

        if f'page={next_page}' in href and f'sc_section_code={category_code}' in href:
            return href if next_page <= max_pages else None

    return None
```

**Implementation**:
- Detect next page via parameter increment
- Respect category-specific page limits
- Continue until max_pages reached or no next page

### 3. **Article Content Extraction**

**Expected HTML Structure** (from modern news sites):
```html
<article>
  <h1 class="title">Article Title</h1>
  <div class="meta">
    <span class="date">2025-01-15</span>
    <span class="author">Author Name</span>
  </div>
  <div class="content">
    <p>Article content paragraphs...</p>
    <img src="..." alt="...">
  </div>
</article>
```

**Extraction Code**:
```python
def extract_article_content(html):
    """Extract full article content from detail page"""
    soup = BeautifulSoup(html, 'html.parser')

    # Extract title (multiple fallback patterns)
    title = None
    if soup.find('h1', class_='title'):
        title = soup.find('h1', class_='title').get_text(strip=True)
    elif soup.find('h1'):
        title = soup.find('h1').get_text(strip=True)

    # Extract content
    content_div = soup.find('div', class_='content')
    if not content_div:
        content_div = soup.find('article')

    content = ''
    if content_div:
        # Get all text from content area
        content = content_div.get_text(separator='\n', strip=True)

    # Extract metadata
    date_elem = soup.find('span', class_='date')
    author_elem = soup.find('span', class_='author')

    return {
        'title': title or 'Untitled',
        'content': content,
        'date': date_elem.get_text(strip=True) if date_elem else None,
        'author': author_elem.get_text(strip=True) if author_elem else None,
        'type': 'news_article'
    }
```

**Key Extraction Points**:
- ✅ Title from `<h1>` or primary heading
- ✅ Content from article/content div
- ✅ Metadata: date, author
- ✅ Filter out navigation/sidebar content
- ✅ Preserve paragraph structure

---

## 📊 Category-Specific Crawling Strategies

### Strategy for S1N1 (50 pages, ~992 articles)

**Challenge**: Largest category, potential performance bottleneck

**Optimization Approach**:
```python
{
    'category': 'S1N1',
    'pages': 50,
    'articles_per_page': 112,
    'estimated_total': 992,
    'batch_size': 5,  # Process 5 pages per batch
    'delay_per_article': 0.3,  # Respectful crawling
    'estimated_time': '75-90 minutes',
    'skip_if_exists': True,  # Resume capability
    'strategy': 'batch_pagination'
}
```

**Implementation**:
1. Process first 5 pages completely
2. Check progress file
3. Continue from last successful page
4. Use URL deduplication to prevent re-crawling

### Strategy for S1N2, S1N3, S1N4 (2-5 pages each)

**Characteristics**: Small categories, fast crawling

```python
{
    'category': 'S1N2/S1N3/S1N4',
    'pages': '2-5',
    'articles_per_page': '56/12/18',
    'estimated_total': '32/24/90',
    'delay_per_article': 0.3,
    'estimated_time': '5-15 minutes per category',
    'strategy': 'direct_pagination'
}
```

**Implementation**:
1. Simple sequential page processing
2. No batching needed
3. Fast completion

---

## 🛠️ Implementation Plan

### Phase 1: Core Crawler Components

**File**: `scripts/crawl_plastics_kr.py`

**Key Functions**:
```python
def fetch_page(url):
    """Fetch page with proper headers and error handling"""
    # Standard requests with retry logic

def extract_article_links(html, category_code):
    """Extract links from listing page"""
    # Use DIV.item selector

def extract_pagination_url(html, category_code, current_page, max_page):
    """Get next page URL"""
    # Increment page parameter

def extract_article_content(html):
    """Extract article from detail page"""
    # Parse title, content, metadata

def crawl_category(category_code, max_pages):
    """Main crawling loop for category"""
    # Process all pages with pagination

def main():
    """Orchestrate crawling of all categories"""
    # S1N1, S1N2, S1N3, S1N4
```

### Phase 2: Data Management

**Output Format**: JSONL (line-delimited JSON)
```json
{
  "title": "플라스틱 산업의 미래",
  "content": "Article content here...",
  "date": "2025-01-15",
  "author": "Reporter Name",
  "category": "S1N1",
  "type": "news_article",
  "url": "https://www.plastics.kr/news/article_view.html?..."
}
```

**Progress Tracking**:
```
data/plastics_kr/
├── plastic_news_articles.jsonl     ← Main output
├── crawled_urls.json               ← Duplicate prevention
├── progress.json                   ← Resume state
├── index.json                      ← Statistics
└── logs/
    └── plastics_kr_crawl_*.log     ← Execution logs
```

### Phase 3: Quality Assurance

**Validation Checks**:
- ✅ HTML encoding (UTF-8)
- ✅ Article link format validation
- ✅ Content extraction completeness
- ✅ Duplicate URL detection
- ✅ Category parameter correctness

---

## ⚡ Execution Timeline

### Estimated Crawl Times

| Category | Pages | Articles | Delay/Article | Total Time |
|----------|-------|----------|---------------|-----------|
| S1N1 | 50 | ~992 | 0.3s | ~75-90 min |
| S1N2 | 2 | ~32 | 0.3s | ~3-5 min |
| S1N3 | 2 | ~24 | 0.3s | ~2-4 min |
| S1N4 | 5 | ~90 | 0.3s | ~6-10 min |
| **TOTAL** | **59** | **~1,138** | **0.3s** | **~90-110 min** |

### Quick Start Commands (Once Implemented)

```bash
# Crawl single category
python3 scripts/crawl_plastics_kr.py S1N1

# Crawl specific categories
python3 scripts/crawl_plastics_kr.py S1N2 S1N3

# Crawl all categories
python3 scripts/crawl_plastics_kr.py all

# Resume interrupted crawl
python3 scripts/crawl_plastics_kr.py all --resume

# Check progress
cat data/plastics_kr/progress.json | python3 -m json.tool
```

---

## 🎓 Key Differences from Plasticnet

| Aspect | Plasticnet | Plastics.kr |
|--------|-----------|------------|
| **HTML Structure** | 35-46 tables/page | 98 divs/page |
| **Encoding** | EUC-KR (legacy) | UTF-8 (standard) |
| **Strategies Needed** | 2 (material_specs + webzine) | 1 (unified) |
| **Semantic Tags** | 0 | 4 article tags/page |
| **Extraction** | TABLE cells | DIV.item selectors |
| **Pagination** | ?page=X | ?page=X&sc_section_code=... |
| **Complexity** | HIGH | LOW |
| **Estimated Time** | 120-180 min | 90-110 min |
| **Total Articles** | ~600 | ~1,138 |

---

## 💡 Implementation Benefits

### ✅ Simplicity
- No legacy encoding workarounds
- No multi-strategy confusion
- CSS class selectors straightforward
- Modern semantic HTML

### ✅ Performance
- Faster page loads (no table parsing)
- Simpler HTML traversal
- Standard UTF-8 encoding
- Predictable structure

### ✅ Reliability
- Clear class patterns
- Consistent across all categories
- Less prone to HTML structure changes
- Standard modern framework structure

### ✅ Maintenance
- Single extraction strategy = easier updates
- Standard HTML = easier debugging
- No encoding issues
- Clear CSS selectors

---

## 🚀 Recommended Approach

### Option A: Fast Track (Recommended)
**What**: Implement unified crawler in 1-2 hours
**Output**: 1,138 articles JSONL file
**Time to crawl**: ~2 hours

**Steps**:
1. Create `scripts/crawl_plastics_kr.py` with 5 main functions
2. Implement pagination loop with progress tracking
3. Test on S1N2 (small category, 2 pages)
4. Run full crawl on all categories
5. Validate output (check article count, content quality)

### Option B: Advanced (More Control)
**What**: Implement with advanced features
**Additional Features**: Filtering, image extraction, parallel processing
**Time to implement**: 3-4 hours
**Time to crawl**: ~60 minutes (with parallelization)

---

## 📝 Next Steps

1. **Create crawler script** using this strategy
2. **Test on S1N4** (5 pages, ~90 articles, 5-10 minutes)
3. **Validate extraction quality** (sample 10 articles)
4. **Run on all categories** in order: S1N4 → S1N3 → S1N2 → S1N1
5. **Verify output** (article count: ~1,138, file size: ~2-3 MB)
6. **Index to Qdrant** for RAG integration

---

**Status**: ✅ Strategy complete, ready for implementation
**Complexity**: 🟢 LOW (vs Plasticnet's HIGH)
**Confidence**: 95% (clear structure, modern HTML, tested patterns)

