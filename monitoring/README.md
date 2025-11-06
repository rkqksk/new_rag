# Production Monitoring Guide

Complete monitoring stack for RAG Enterprise using Prometheus and Grafana.

## Overview

The monitoring stack includes:
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notifications
- **Exporters**: PostgreSQL, Redis, Node metrics

## Architecture

```
┌──────────────┐
│  Grafana     │──┐
│  Dashboard   │  │
└──────────────┘  │
                  ▼
┌──────────────┐  ┌──────────────┐
│ Prometheus   │──│ Alertmanager │
│  Server      │  │              │
└──────┬───────┘  └──────────────┘
       │
       ├─────► RAG API (/metrics)
       ├─────► Qdrant (/metrics)
       ├─────► PostgreSQL Exporter
       ├─────► Redis Exporter
       └─────► Node Exporter
```

## Quick Deploy

```bash
# Deploy Prometheus
kubectl apply -f monitoring/prometheus-config.yaml

# Deploy Grafana
kubectl apply -f monitoring/grafana-deployment.yaml

# Access Grafana
kubectl port-forward -n rag-enterprise svc/grafana 3000:3000
# Visit: http://localhost:3000 (admin/admin)
```

## Metrics Collected

### API Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | Request latency |
| `search_queries_total` | Counter | Total search queries |
| `search_latency_seconds` | Histogram | Search latency |
| `vector_store_operations_total` | Counter | Vector store ops |
| `cache_hits_total` | Counter | Cache hits |
| `cache_misses_total` | Counter | Cache misses |

### Database Metrics

**Qdrant:**
- `qdrant_collections_total`
- `qdrant_vectors_total`
- `qdrant_memory_usage_bytes`

**PostgreSQL:**
- `pg_stat_database_*`
- `pg_stat_user_tables_*`
- `pg_connections`

**Redis:**
- `redis_connected_clients`
- `redis_used_memory_bytes`
- `redis_keyspace_hits_total`

### System Metrics

- `node_cpu_seconds_total`
- `node_memory_MemAvailable_bytes`
- `node_filesystem_avail_bytes`
- `node_network_receive_bytes_total`

## Dashboards

### 1. RAG Enterprise - Overview

Key metrics:
- Request rate (QPS)
- Error rate (4xx, 5xx)
- Response time (P50, P95, P99)
- Pod CPU and memory usage
- Active pods and service health

Import: `grafana-dashboards.json`

### 2. Database Performance

Key metrics:
- Qdrant collection stats
- PostgreSQL connections
- Redis memory usage
- Query performance

### 3. System Resources

Key metrics:
- Node CPU usage
- Node memory usage
- Disk I/O
- Network traffic

## Alerts

### Critical Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| APIDown | API unavailable for 1m | Page on-call |
| QdrantDown | Qdrant down for 1m | Page on-call |
| PostgreSQLDown | Postgres down for 1m | Page on-call |
| HighErrorRate | >5% error rate for 5m | Investigate |

### Warning Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| HighLatency | P95 > 1s for 5m | Monitor |
| HighMemoryUsage | >90% for 5m | Monitor |
| HighCPUUsage | >80% for 5m | Consider scaling |
| HighDiskUsage | >90% for 5m | Clean up or expand |

## Alert Configuration

### Slack Integration

```yaml
# alertmanager.yml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

route:
  receiver: 'slack'
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 4h
```

### PagerDuty Integration

```yaml
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
        description: '{{ .GroupLabels.alertname }}'

route:
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
```

## Custom Metrics

### Adding Metrics to API

```python
from prometheus_client import Counter, Histogram

# Counter
search_queries = Counter(
    'search_queries_total',
    'Total search queries',
    ['query_type']
)

# Histogram
search_latency = Histogram(
    'search_latency_seconds',
    'Search latency in seconds',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# Usage
search_queries.labels(query_type='semantic').inc()
with search_latency.time():
    results = await search(query)
```

### Expose Metrics Endpoint

```python
from fastapi import FastAPI
from prometheus_client import make_asgi_app

app = FastAPI()

# Add prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

## Querying Prometheus

### PromQL Examples

```promql
# Average request rate over 5 minutes
rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate percentage
sum(rate(http_requests_total{status=~"5.."}[5m])) /
sum(rate(http_requests_total[5m])) * 100

# CPU usage per pod
rate(container_cpu_usage_seconds_total{pod=~"rag-api-.*"}[5m])

# Memory usage percentage
container_memory_usage_bytes / container_spec_memory_limit_bytes * 100
```

## Grafana Setup

### 1. Add Prometheus Data Source

```bash
# Via UI
Settings → Data Sources → Add data source → Prometheus
URL: http://prometheus:9090
```

### 2. Import Dashboard

```bash
# Via UI
Create → Import → Upload JSON file
Select: grafana-dashboards.json
```

### 3. Create Alerts

```bash
# Via UI
Alert rules → Create alert rule
Query: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
Condition: WHEN max() OF query(A) IS ABOVE 0.05
```

## Retention and Storage

### Prometheus

```yaml
# Storage retention
--storage.tsdb.retention.time=30d
--storage.tsdb.retention.size=50GB
```

### Grafana

```yaml
# Dashboard retention in database
[dashboards]
versions_to_keep = 20
```

## Troubleshooting

### Prometheus Not Scraping

```bash
# Check targets
kubectl port-forward -n rag-enterprise svc/prometheus 9090:9090
# Visit: http://localhost:9090/targets

# Check service discovery
# Visit: http://localhost:9090/service-discovery
```

### Missing Metrics

```bash
# Check if metric exists
curl http://rag-api-service:8001/metrics | grep metric_name

# Check Prometheus config
kubectl get configmap prometheus-config -n rag-enterprise -o yaml
```

### High Cardinality

```bash
# Find high cardinality metrics
# Visit: http://localhost:9090/tsdb-status
```

## Performance Tuning

### Prometheus

```yaml
# Optimize scrape intervals
scrape_interval: 30s  # Increase if needed
scrape_timeout: 10s

# Limit retention
storage.tsdb.retention.time: 15d
```

### Grafana

```yaml
# Enable caching
[caching]
enabled = true

# Optimize query timeout
[dataproxy]
timeout = 30
```

## Security

### Authentication

```yaml
# Prometheus basic auth
basic_auth:
  username: admin
  password: $PROMETHEUS_PASSWORD

# Grafana OAuth
[auth.google]
enabled = true
client_id = YOUR_CLIENT_ID
client_secret = YOUR_CLIENT_SECRET
```

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: prometheus-network-policy
spec:
  podSelector:
    matchLabels:
      app: prometheus
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: grafana
```

## Best Practices

1. **Naming Conventions**: Use `_total` for counters, `_seconds` for durations
2. **Labels**: Keep cardinality low, avoid user IDs
3. **Aggregation**: Prefer recording rules for complex queries
4. **Retention**: Balance retention vs. storage costs
5. **Alerting**: Avoid alert fatigue, group related alerts

## Support

For issues:
- Check Prometheus logs: `kubectl logs -f deployment/prometheus -n rag-enterprise`
- Check Grafana logs: `kubectl logs -f deployment/grafana -n rag-enterprise`
- Review alert history: http://localhost:9090/alerts
