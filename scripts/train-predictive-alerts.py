#!/usr/bin/env python3
"""
Train Predictive Alerting Models

Fetches historical metrics from Prometheus and trains prediction models.
"""

import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import requests
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.monitoring.predictive_alerts import (
    PredictiveAlerter,
    MetricData,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_prometheus_metrics(
    prometheus_url: str,
    metric_query: str,
    hours_back: int = 168,  # 1 week
) -> List[MetricData]:
    """
    Fetch metrics from Prometheus

    Args:
        prometheus_url: Prometheus server URL
        metric_query: PromQL query
        hours_back: How many hours of data to fetch

    Returns:
        List of MetricData points
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours_back)

    # Query Prometheus
    params = {
        "query": metric_query,
        "start": start_time.timestamp(),
        "end": end_time.timestamp(),
        "step": "10m",  # 10 minute intervals
    }

    try:
        response = requests.get(f"{prometheus_url}/api/v1/query_range", params=params)
        response.raise_for_status()
        data = response.json()

        if data["status"] != "success":
            logger.error(f"Prometheus query failed: {data}")
            return []

        # Parse results
        metric_data = []
        for result in data["data"]["result"]:
            metric_name = result["metric"].get("__name__", "unknown")
            labels = result["metric"]

            for timestamp, value in result["values"]:
                metric_data.append(
                    MetricData(
                        timestamp=datetime.fromtimestamp(float(timestamp)),
                        value=float(value),
                        metric_name=metric_name,
                        labels=labels,
                    )
                )

        logger.info(f"Fetched {len(metric_data)} data points for {metric_query}")
        return metric_data

    except Exception as e:
        logger.error(f"Failed to fetch metrics: {e}")
        return []


def main():
    """Main training function"""
    print("🤖 Training Predictive Alert Models")
    print("====================================")
    print("")

    # Configuration
    PROMETHEUS_URL = "http://localhost:9090"

    # Metrics to train on
    metric_queries = {
        "api_latency_p95": 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))',
        "api_error_rate": 'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])',
        "cpu_usage": 'avg(rate(container_cpu_usage_seconds_total{container="api"}[5m])) * 100',
        "memory_usage": 'avg(container_memory_working_set_bytes{container="api"}) / avg(container_spec_memory_limit_bytes{container="api"}) * 100',
        "queue_length": 'redis_queue_length{queue="rag_tasks"}',
        "active_connections": 'sum(websocket_connections)',
    }

    # Fetch historical data
    print("📊 Fetching historical metrics...")
    historical_data: Dict[str, List[MetricData]] = {}

    for metric_name, query in metric_queries.items():
        print(f"   Fetching {metric_name}...")
        data = fetch_prometheus_metrics(PROMETHEUS_URL, query, hours_back=168)

        if data:
            historical_data[metric_name] = data
        else:
            logger.warning(f"No data for {metric_name}")

    if not historical_data:
        print("❌ No metrics data fetched. Is Prometheus running?")
        print(f"   URL: {PROMETHEUS_URL}")
        return 1

    print(f"\n✅ Fetched data for {len(historical_data)} metrics")

    # Train models
    print("\n🧠 Training prediction models...")
    alerter = PredictiveAlerter()

    try:
        alerter.train(historical_data)
        print("✅ Training complete!")

        # Show auto-tuned thresholds
        print("\n📊 Auto-tuned Alert Thresholds:")
        print("=" * 60)
        for metric_name, thresholds in alerter.thresholds.items():
            if metric_name in historical_data:
                print(f"\n{metric_name}:")
                print(f"  Warning:  {thresholds.get('warning', 'N/A')}")
                print(f"  Critical: {thresholds.get('critical', 'N/A')}")

    except Exception as e:
        logger.error(f"Training failed: {e}")
        return 1

    # Test prediction
    print("\n🔮 Testing predictions...")
    test_metric = "api_latency_p95"

    if test_metric in historical_data:
        recent_data = historical_data[test_metric][-24:]  # Last 4 hours
        alerts = alerter.predict_and_alert(
            test_metric, recent_data, forecast_horizon_minutes=60
        )

        if alerts:
            print(f"\n⚠️  Generated {len(alerts)} test alerts:")
            for alert in alerts:
                print(f"\n{alert.message}")
                print(f"Severity: {alert.severity.upper()}")
                print(f"Recommended: {alert.recommended_action}")
        else:
            print("✅ No issues predicted (system healthy)")

    print("\n" + "=" * 60)
    print("✅ Training complete! Models saved to: models/alerts/")
    print("\nNext steps:")
    print("  1. Integrate with monitoring system")
    print("  2. Set up alerting endpoints (email, Slack, PagerDuty)")
    print("  3. Schedule regular retraining (weekly)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
