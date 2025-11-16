# Requirements Files Reference

## Primary Files (Keep)
- **requirements.txt** - Main production dependencies
- **requirements-test.txt** - Testing dependencies
- **requirements-nexa.txt** - NexaAI SDK dependencies

## Specialized Files (Keep)
- **requirements-airflow.txt** - Airflow/ETL dependencies
- **config/requirements/*.txt** - Environment-specific deps

## Deprecated Files (To Remove)
- **requirements-updated.txt** - Duplicate of requirements.txt
- **requirements-lock.txt** - Not used (use pip freeze instead)
- **requirements_crawler.txt** - Old naming convention

## Usage
```bash
# Install production
pip install -r requirements.txt

# Install with testing
pip install -r requirements.txt -r requirements-test.txt

# Install with NexaAI
pip install -r requirements.txt -r requirements-nexa.txt
```
