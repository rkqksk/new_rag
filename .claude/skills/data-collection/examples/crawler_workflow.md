# Data Collection Workflow Examples

## Example 1: OneHago Product Crawling

### Step 1: Generate Crawler
```bash
python .claude/skills/data-collection/scripts/create_crawler.py \
  --site onehago \
  --url https://onehago.com \
  --pages 50
```

### Step 2: Run Crawler
```bash
python scripts/crawlers/onehago_crawler.py
```

### Step 3: Process Results
```bash
# Parse Excel files
python .claude/skills/excel-processing/scripts/batch_process.py \
  --input data/crawled/ \
  --output data/processed/

# Index to RAG
python scripts/index_to_qdrant.py --input data/processed/
```

## Example 2: Scheduled Daily Crawling

### Create Airflow DAG
```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

dag = DAG(
    'daily_product_crawl',
    schedule_interval='0 2 * * *',  # 2 AM daily
    start_date=datetime(2025, 1, 1)
)

crawl = BashOperator(
    task_id='crawl_products',
    bash_command='python scripts/crawlers/onehago_crawler.py',
    dag=dag
)

process = BashOperator(
    task_id='process_data',
    bash_command='python scripts/process_crawled_data.py',
    dag=dag
)

index = BashOperator(
    task_id='index_to_qdrant',
    bash_command='python scripts/index_to_qdrant.py',
    dag=dag
)

crawl >> process >> index
```
