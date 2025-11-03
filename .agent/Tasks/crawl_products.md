# Task: Crawl Products from Website

## Objective
웹사이트에서 제품 데이터를 크롤링하고 JSON 형식으로 저장

## Agent Delegation
**Primary Agent**: `agents/crawling_agent.py`
**Supporting Agents**: None (standalone task)

## Input Parameters
```json
{
  "site_name": "청진코리아",
  "categories": ["Bottle", "Jar", "Cap", "Pump"],
  "output_dir": "data/products/crawled/",
  "options": {
    "max_pages_per_category": 100,
    "delay_between_requests": 0.5,
    "retry_on_error": 3
  }
}
```

## Execution Steps

### Step 1: Validate Prerequisites
```bash
# Check Python dependencies
python3 -c "import bs4, requests, selenium" || echo "Missing dependencies"

# Check output directory
mkdir -p data/products/crawled/

# Verify site accessibility
curl -I http://chungjinkorea.com
```

### Step 2: Execute Crawling Agent
```bash
# Run crawling agent
python3 agents/crawling_agent.py \
  --site "청진코리아" \
  --categories Bottle,Jar \
  --output data/products/crawled/ \
  --verbose
```

**Python Code (Alternative)**:
```python
from agents.crawling_agent import CrawlingAgent, CrawlCategory, CrawlConfig

# Initialize agent
agent = CrawlingAgent()

# Configure crawling
config = CrawlConfig(
    site_name="청진코리아",
    site_url="http://chungjinkorea.com",
    output_dir="data/products/crawled/"
)

# Define categories to crawl
categories = [
    CrawlCategory(name="Bottle", url="http://chungjinkorea.com/bottle", pages=68),
    CrawlCategory(name="Jar", url="http://chungjinkorea.com/jar", pages=4)
]

# Execute crawling
results = await agent.crawl_site("청진코리아", categories)

print(f"✅ Crawled {results['total_products']} products")
print(f"✅ Saved to: {results['output_path']}")
```

### Step 3: Validate Output
```bash
# Count products crawled
find data/products/crawled/ -name "*.json" | wc -l

# Validate JSON structure
python3 scripts/validate_product_data.py data/products/crawled/

# Expected output:
# ✅ 1,245 products validated
# ✅ 100% have product_code
# ✅ 98% have complete specifications
# ⚠️ 23 products missing images
```

### Step 4: Generate Summary Report
```bash
# Create crawl report
python3 agents/crawling_agent.py --report data/products/crawled/

# Output: crawl_report_2025-10-26.csv
# Columns: category, products_count, success_rate, avg_time_per_product
```

## Expected Output

### File Structure
```
data/products/crawled/
├── Bottle/
│   ├── products/
│   │   ├── idx_0.json
│   │   ├── idx_1.json
│   │   └── ...
│   └── images/
│       ├── bottle_001.jpg
│       └── ...
├── Jar/
│   └── products/
└── crawl_report_2025-10-26.csv
```

### Sample JSON Output
```json
{
  "product_code": "BT-PET-50-24410",
  "product_name": "PET 50ml 보틀",
  "category": "Bottle",
  "specifications": {
    "capacity": "50ml",
    "material": "PET",
    "neck_size": "24/410",
    "dimensions": {
      "height": "120mm",
      "diameter": "35mm"
    }
  },
  "pricing": {
    "moq": 1000,
    "unit_price": "₩250",
    "coating_option": "UV coating available",
    "printing_option": "Silk screen, Hot stamping"
  },
  "images": [
    "http://chungjinkorea.com/images/bottle_001.jpg"
  ],
  "crawled_at": "2025-10-26T10:30:00Z"
}
```

## Success Criteria
- [ ] All target categories crawled
- [ ] >95% products have complete specifications
- [ ] All JSON files valid (parseable)
- [ ] Crawl report generated
- [ ] No duplicate products

## Error Handling

### Network Errors
```python
try:
    results = await agent.crawl_site(site, categories)
except NetworkError as e:
    print(f"⚠️ Network error: {e}")
    print("→ Retrying with exponential backoff...")
    results = await agent.crawl_site(site, categories, retry=True)
```

### Data Quality Issues
```bash
# If validation fails
if validation_score < 0.95:
    echo "⚠️ Data quality below threshold"
    echo "→ Review crawling logic: agents/crawling_agent.py"
    echo "→ Check site HTML changes"
fi
```

## Monitoring

### Real-time Progress
```bash
# Watch crawling progress
tail -f logs/crawling_agent.log

# Expected log entries:
# [INFO] Category: Bottle, Page: 1/68, Products: 18
# [INFO] Category: Bottle, Page: 2/68, Products: 36
```

### Performance Metrics
```python
# Track metrics during crawl
metrics = {
    "total_products": 1245,
    "success_rate": 0.98,
    "avg_time_per_product": 0.8,  # seconds
    "total_duration": 996  # seconds (~16 min)
}
```

## Next Task
**Trigger**: After successful crawl completion
**Next Task**: `Tasks/generate_embeddings.md`
**Automation**: Auto-trigger if configured in orchestration

---

**Task Type**: Data Ingestion
**Priority**: High
**Frequency**: Weekly (or on-demand)
**Estimated Time**: 15-20 minutes for full crawl
**Last Run**: 2025-10-26
