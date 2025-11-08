# Monitoring Agent

**Purpose**: Performance monitoring - metrics, logs, alerts, profiling

**Version**: 1.0.0
**Status**: ✅ Production-Ready

---

## 🎯 Overview

Specialized sub-agent for system monitoring and performance analysis.

### Key Features

- ✅ **Performance monitoring** (Prometheus metrics)
- ✅ **Log analysis** (structured logs)
- ✅ **Metrics collection** (CPU, memory, latency)
- ✅ **Alerting** (threshold-based)
- ✅ **Profiling** (Python cProfile, line_profiler)

---

## 🚀 Usage

### Via Task Tool

```python
# Launch monitoring agent
Task(
    subagent_type="monitoring-agent",
    prompt="Analyze system performance and identify bottlenecks"
)
```

### Common Commands

```bash
# Check performance summary
curl http://localhost:8001/api/v1/debug/performance/summary

# View recent queries
curl http://localhost:8001/api/v1/debug/queries/recent

# Docker stats
docker stats

# Service logs
docker-compose logs -f api
```

---

## 🔧 Configuration

Located in `agent.json`:

```json
{
  "metrics_interval": 60,
  "log_retention_days": 30,
  "alert_threshold": 0.9,
  "profiling_enabled": true
}
```

---

## 📊 Monitoring Stack

| Tool | Purpose | Cost |
|------|---------|------|
| **Prometheus** | Metrics collection | $0/month |
| **Grafana** | Visualization | $0/month |
| **Python Profiler** | Code profiling | $0/month |
| **Docker Stats** | Container metrics | $0/month |

**Total Cost**: $0/month

---

## 📈 Metrics Tracked

- API response times
- Database query latency
- Vector search performance
- Memory usage
- CPU utilization
- Cache hit rates

---

## 📚 Related

- API: `/api/v1/debug/*` endpoints
- Docs: `docs/reference/DEBUG_SYSTEM.md`
- Config: `DEBUG_ENABLED=true` in `.env`

---

**Created**: 2025-11-08
**Last Updated**: 2025-11-08
