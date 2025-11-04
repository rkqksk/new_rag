# Cosmorning.com Website Architecture & Crawler Analysis

**Date**: 2025-10-31
**Website**: https://cosmorning.com/news/article_list_all.html
**Crawler Script**: `scripts/crawl_cosmorning.py`

---

## 📊 Website Architecture Overview

### 1. Site Structure

```
cosmorning.com
├── /news/
│   ├── article_list_all.html (main listing)
│   ├── article.html?no=[ID] (detail pages)
│   └── ajax.php (backend service)
├── /r_and_d/ (R&D section)
├── /people/ (People section)
├── /job/ (Job board)
├── /resource/ (Resources)
└── /exhibition/ (Online exhibition)
```

### 2. Article List Page Structure

**URL**: `https://cosmorning.com/news/article_list_all.html?page=[N]`

**Key Components**:
- Header with language selector (Korean/English/Chinese/Japanese)
- Navigation menu with main sections
- Main content area with article list (`<li>` elements)
- Pagination controls (1-10 with Previous/Next)
- Sidebar advertisements (rotating banners with Swiper/bxSlider)
- Footer with company info

**Pagination**:
- **Type**: Query parameter based (`?page=0`, `?page=1`, etc.)
- **Articles per page**: 10 articles
- **Maximum pages**: Unknown (need to test limits)
- **Navigation**: Previous/Next buttons + numbered links (1-10)

### 3. Article Item Structure

```html
<li>
  <a href="/news/article.html?no=[ARTICLE_ID]">
    <img src="/images/thumbnail_[ID].jpg" alt="">
    <h3>[ARTICLE_TITLE]</h3>
    <p>[EXCERPT]</p>
    <span class="author">[AUTHOR_NAME]</span>
    <span class="date">[YYYY-MM-DD HH:MM]</span>
  </a>
</li>
```

**Extracted Data per Article**:
- `article_id` (numeric ID from URL parameter `no=`)
- `title` (headline from `<h3>`)
- `author` (byline from `span.author`)
- `date` (publication date from `span.date`)
- `excerpt` (brief summary from `<p>`)
- `thumbnail_url` (image from `<img src>`)
- `article_url` (full URL to detail page)

### 4. Article Detail Page

**URL Format**: `/news/article.html?no=[ARTICLE_ID]`

**Example**: `/news/article.html?no=51531`

**Content Structure**:
- Article header with title, author, date
- Main content in `<div class="article_content">`
- Related articles or comments section (if present)
- Advertisement zones

---

## ⚠️ Technical Challenges & Solutions

### Challenge 1: AJAX-Based Content Loading
**Issue**: Pagination uses `ajaxGetSkinContent()` JavaScript function for sidebar updates
**Impact**: Simple HTTP requests should work, but dynamic content may require JavaScript rendering
**Solution**: Use BeautifulSoup with basic HTTP requests (works for static HTML). If needed, switch to Selenium/Playwright for dynamic content.

### Challenge 2: Rate Limiting
**Issue**: Unknown rate limiting on the website
**Impact**: Too many requests may result in IP blocking
**Solution**:
- Conservative request delay: 1.0 second between requests
- 8 parallel workers (not aggressive)
- User-Agent header to appear as legitimate browser
- Error handling for timeout/blocked responses

### Challenge 3: Korean Language Content
**Issue**: Content in Korean, timestamps in Korean format
**Impact**: Text extraction and date parsing need UTF-8 support
**Solution**:
- Set response encoding to UTF-8
- Use regex patterns for date extraction
- Handle Korean characters in database/storage

### Challenge 4: Image Dependencies
**Issue**: Thumbnail images may be CDN-hosted or rotated
**Impact**: Image URLs might change or become unavailable
**Solution**: Store URLs only (not downloading images), save locally if needed later

### Challenge 5: Advertisement & Banner Rotation
**Issue**: Multiple advertisement zones with auto-rotating carousels
**Impact**: May interfere with HTML parsing if not careful
**Solution**: Target specific CSS classes/IDs for article content, ignore ad zones

---

## 🎯 Crawler Design Decisions

### Architecture
```
Phase 1: Collect Article URLs (from list pages)
├─ Fetch each page (0-10)
├─ Parse HTML with BeautifulSoup
├─ Extract: article_id, title, author, date, excerpt, thumbnail, url
└─ Save to articles.jsonl (metadata only)

Phase 2: Extract Full Content (from detail pages)
├─ For each article in Phase 1
├─ Fetch detail page
├─ Parse article_content div
├─ Merge with Phase 1 data
└─ Save complete article to articles.jsonl
```

### Configuration
```python
ARTICLES_PER_PAGE = 10          # Static, confirmed from website
WORKERS = 8                      # Conservative threading
REQUEST_DELAY = 1.0             # Respectful rate limiting (1 request/sec)
CHECKPOINT_INTERVAL = 100       # Save progress every 100 articles
```

### Why These Settings?
- **8 workers**: News sites are often sensitive to bulk requests. 8 is a good balance between speed and politeness.
- **1.0 second delay**: ~10 requests/second total throughput, which is reasonable for a news site.
- **100 article checkpoint**: Progress tracking without excessive disk writes.

---

## 📈 Estimated Performance

### Crawling Time
- **Pages to crawl**: 10 pages × 10 articles = 100 articles (Phase 1)
- **Time per page**: ~2-3 seconds (fetch + parse)
- **Phase 1 time**: ~30 seconds

- **Phase 2 (full content)**:
  - 100 articles × 1 second delay = 100 seconds
  - Plus parsing time: ~200 seconds total
  - **Total time**: ~5-10 minutes for 100 articles

### Storage
- **Metadata per article**: ~0.5 KB
- **Full content per article**: ~5 KB average
- **100 articles total**: ~550 KB
- **1000 articles**: ~5.5 MB
- **10,000 articles**: ~55 MB

---

## 🚀 Running the Crawler

### Basic Usage
```bash
python3 scripts/crawl_cosmorning.py
```

### Output Files
```
data/cosmorning/
├── crawled/
│   ├── articles.jsonl         # All articles with full content
│   └── progress.json          # Crawl progress and statistics
└── logs/
    └── cosmorning_crawler_[timestamp].log
```

### Output Format (JSONL)
```json
{
  "article_id": "51531",
  "title": "더스킨팩토리 쿤달과 함께 하는 '컬리 뷰티 페스타 2025'",
  "author": "허강우 기자",
  "date": "2025-10-31 18:20",
  "excerpt": "Brief summary of article...",
  "article_url": "https://cosmorning.com/news/article.html?no=51531",
  "thumbnail_url": "https://cosmorning.com/images/thumbnail_51531.jpg",
  "page": 0,
  "discovered_at": "2025-10-31T23:10:00",
  "full_content": "Full article text extracted from detail page...",
  "content_length": 1234,
  "fetched_at": "2025-10-31T23:10:15",
  "success": true
}
```

---

## 🔧 Customization Options

### Adjust Max Pages
Edit line 43 in `crawl_cosmorning.py`:
```python
MAX_PAGES = 10  # Change to 20, 50, 100, etc.
```

### Adjust Workers & Rate Limit
```python
WORKERS = 8        # Change to 4 (slower) or 16 (faster)
REQUEST_DELAY = 1.0  # Change to 0.5 (faster) or 2.0 (slower)
```

### Extract Additional Data
Modify `get_article_list_page()` and `extract_article_content()` methods to parse additional HTML elements (comments, tags, categories, etc.)

---

## 📋 Feedback & Recommendations

### Strengths of Website Architecture
✅ **Simple, crawl-friendly structure**
- Clean pagination with query parameters
- Consistent HTML layout for articles
- No heavy JavaScript requirements for listing pages
- No authentication barriers

✅ **Stable content patterns**
- Fixed 10 articles per page
- Predictable article URL format
- Standard HTML elements (h3, p, span, a)

✅ **Good for archival**
- Article IDs appear stable
- Content seems persistent
- Date metadata provided

### Areas of Caution
⚠️ **Rate limiting sensitivity**
- Conservative request delay recommended (1 second)
- Monitor for 429/503 responses

⚠️ **Language considerations**
- Primarily Korean content
- UTF-8 encoding must be handled properly

⚠️ **JavaScript dependencies**
- Some page elements (ads, sidebars) are AJAX-loaded
- Main article listing is static HTML (good!)

⚠️ **Dynamic URLs**
- Thumbnail images may be CDN-hosted
- Image URLs might change over time

### Optimization Suggestions

1. **For higher throughput**:
   - Test actual rate limits with a pilot crawl (start with 5 requests/min)
   - Gradually increase WORKERS and decrease REQUEST_DELAY
   - Monitor for blocking responses (429, 403)

2. **For completeness**:
   - Estimate total number of pages
   - Add retry logic for failed requests
   - Implement progress resume capability

3. **For production**:
   - Add proxy rotation for large-scale crawling
   - Implement content deduplication
   - Store images separately with content hashing

---

## 🔍 Testing the Crawler

### Test Run (First 3 Pages)
```bash
# Edit MAX_PAGES = 3 temporarily
python3 scripts/crawl_cosmorning.py
```

### Monitor Progress
```bash
# Watch logs in real-time
tail -f data/cosmorning/logs/*.log
```

### Verify Output
```bash
# Check extracted data
head -5 data/cosmorning/crawled/articles.jsonl | python3 -m json.tool
```

---

**Report Created**: 2025-10-31
**Crawler Version**: 1.0 (Initial)
**Last Updated**: 2025-10-31
