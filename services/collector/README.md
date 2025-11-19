# Data Collector Service (Planned)

**Status**: 🚧 Scaffold Only - Not Production Ready

## Current State

This is a placeholder directory for future microservice extraction. The Collector service is currently **not functional** and exists only as a structural placeholder.

## Actual Implementation

👉 **All data collection functionality currently lives in `apps/api/`**

- Web scraping and crawling logic in `apps/api/`
- API polling mechanisms in services layer
- File parsing (Excel, PDF, CSV, JSON, XML, HTML)
- Data validation and transformation pipelines
- Scheduled job management via Airflow and Redis

## Planned Features (Future Extraction)

When extracted as a microservice, this service will handle:

- Web scraping (Scrapy + BeautifulSoup)
- REST API polling with retry logic
- Multi-format file parsing (Excel, PDF, CSV, JSON, XML, HTML)
- Scheduled jobs (Airflow + Celery)
- Data validation, transformation, and enrichment
- Event streaming to Kafka/Redis for other services

## Roadmap

- **Phase 1**: Consolidate collection logic in `apps/api/` (Current)
- **Phase 2**: Extract to standalone service (Post-v10.0.0)
- **Phase 3**: Scale collection with distributed workers
- **Phase 4**: Deploy independently to Kubernetes

Estimated extraction: **Q2 2025** (After v10 stabilization)

See `docs/planning/MICROSERVICES_ROADMAP.md` for complete strategy.

## DO NOT USE

**This service is not functional and will return errors if deployed.**

- No implementation files
- No endpoint handlers
- No Scrapy/polling logic
- No job scheduling

## Related Documentation

- **Data Collection Architecture**: `docs/DATA_COLLECTOR_ARCHITECTURE.md`
- **API Endpoints**: `docs/reference/API_DOCUMENTATION.md`
- **Web Crawling**: `tests/test_advanced_crawling.py`

---

**Last Updated**: 2025-11-19  
**Target Extraction**: Post-v10.0.0
