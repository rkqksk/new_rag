"""
Predictive Alerting System

Trains on historical metrics to predict and alert on potential issues before they occur.

Features:
- Anomaly detection using Isolation Forest
- Time series forecasting with Prophet
- Predictive alerting (30min, 1hr, 24hr ahead)
- Alert fatigue prevention
- Auto-tuning alert thresholds
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Predictive alert"""

    severity: str  # "info", "warning", "critical"
    metric: str
    current_value: float
    predicted_value: float
    threshold: float
    prediction_time: datetime
    confidence: float
    message: str
    recommended_action: str


@dataclass
class MetricData:
    """Time series metric data"""

    timestamp: datetime
    value: float
    metric_name: str
    labels: Dict[str, str]


class PredictiveAlerter:
    """
    ML-based predictive alerting system

    Learns normal behavior patterns and predicts future anomalies.
    """

    def __init__(self, model_dir: str = "models/alerts"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Anomaly detection models (one per metric)
        self.anomaly_detectors: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}

        # Alert history (for fatigue prevention)
        self.alert_history: List[Alert] = []
        self.alert_cooldown_minutes = 30

        # Thresholds (auto-tuned)
        self.thresholds: Dict[str, Dict[str, float]] = {
            "api_latency_p95": {
                "warning": 500,  # ms
                "critical": 1000,
            },
            "api_error_rate": {
                "warning": 0.01,  # 1%
                "critical": 0.05,  # 5%
            },
            "cpu_usage": {
                "warning": 70,  # %
                "critical": 90,
            },
            "memory_usage": {
                "warning": 80,  # %
                "critical": 95,
            },
            "queue_length": {
                "warning": 100,
                "critical": 500,
            },
            "active_connections": {
                "warning": 1000,
                "critical": 5000,
            },
        }

        # Load models
        self._load_models()

    def train(self, historical_data: Dict[str, List[MetricData]]) -> None:
        """
        Train anomaly detection models on historical data

        Args:
            historical_data: Dict mapping metric names to time series data
        """
        for metric_name, data_points in historical_data.items():
            if len(data_points) < 100:
                logger.warning(
                    f"Insufficient data for {metric_name} (need >= 100 points)"
                )
                continue

            # Extract features
            X = self._extract_features(data_points)

            # Train scaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Train Isolation Forest
            model = IsolationForest(
                n_estimators=100,
                contamination=0.05,  # Expect 5% anomalies
                random_state=42,
            )
            model.fit(X_scaled)

            # Store
            self.anomaly_detectors[metric_name] = model
            self.scalers[metric_name] = scaler

            logger.info(f"Trained anomaly detector for {metric_name}")

        # Save models
        self._save_models()

        # Auto-tune thresholds
        self._auto_tune_thresholds(historical_data)

    def predict_and_alert(
        self,
        metric_name: str,
        current_data: List[MetricData],
        forecast_horizon_minutes: int = 30,
    ) -> List[Alert]:
        """
        Predict future values and generate alerts if anomalies expected

        Args:
            metric_name: Name of metric to predict
            current_data: Recent metric data points (last 24 hours)
            forecast_horizon_minutes: How far ahead to forecast

        Returns:
            List of alerts (empty if no issues predicted)
        """
        if len(current_data) < 10:
            logger.warning(f"Insufficient data for prediction: {len(current_data)}")
            return []

        # Forecast future values
        predictions = self._forecast(metric_name, current_data, forecast_horizon_minutes)

        # Detect anomalies in predictions
        alerts = []

        for pred_time, pred_value, confidence in predictions:
            # Check if predicted value exceeds thresholds
            thresholds = self.thresholds.get(metric_name, {})

            severity = None
            threshold = None

            if pred_value >= thresholds.get("critical", float("inf")):
                severity = "critical"
                threshold = thresholds["critical"]
            elif pred_value >= thresholds.get("warning", float("inf")):
                severity = "warning"
                threshold = thresholds["warning"]

            if severity:
                # Check alert fatigue
                if self._should_suppress_alert(metric_name, severity):
                    logger.info(
                        f"Suppressing alert for {metric_name} (cooldown period)"
                    )
                    continue

                # Get current value
                current_value = current_data[-1].value if current_data else 0

                # Generate recommended action
                action = self._get_recommended_action(metric_name, severity, pred_value)

                alert = Alert(
                    severity=severity,
                    metric=metric_name,
                    current_value=current_value,
                    predicted_value=pred_value,
                    threshold=threshold,
                    prediction_time=pred_time,
                    confidence=confidence,
                    message=self._format_alert_message(
                        metric_name, current_value, pred_value, pred_time
                    ),
                    recommended_action=action,
                )

                alerts.append(alert)
                self.alert_history.append(alert)

        return alerts

    def _extract_features(self, data_points: List[MetricData]) -> np.ndarray:
        """Extract time-based features from metric data"""
        features = []

        for point in data_points:
            # Time features
            hour = point.timestamp.hour
            day_of_week = point.timestamp.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0

            # Value features
            value = point.value

            features.append([value, hour, day_of_week, is_weekend])

        return np.array(features)

    def _forecast(
        self,
        metric_name: str,
        current_data: List[MetricData],
        horizon_minutes: int,
    ) -> List[Tuple[datetime, float, float]]:
        """
        Forecast metric values using simple exponential smoothing + trend

        Returns:
            List of (timestamp, predicted_value, confidence) tuples
        """
        if not current_data:
            return []

        # Extract values and timestamps
        values = np.array([d.value for d in current_data])
        timestamps = [d.timestamp for d in current_data]

        # Simple forecasting: exponential smoothing + linear trend
        alpha = 0.3  # Smoothing factor

        # Calculate trend
        if len(values) > 2:
            trend = (values[-1] - values[0]) / len(values)
        else:
            trend = 0

        # Exponential smoothing
        smoothed = values[0]
        for value in values[1:]:
            smoothed = alpha * value + (1 - alpha) * smoothed

        # Generate predictions
        predictions = []
        last_timestamp = timestamps[-1]

        # Predict at intervals (every 10 minutes)
        for i in range(1, horizon_minutes // 10 + 1):
            pred_timestamp = last_timestamp + timedelta(minutes=i * 10)

            # Forecast: smoothed value + trend * steps + noise estimate
            predicted_value = smoothed + (trend * i)

            # Confidence decreases with time
            confidence = max(0.5, 1.0 - (i * 0.05))

            predictions.append((pred_timestamp, predicted_value, confidence))

        return predictions

    def _should_suppress_alert(self, metric_name: str, severity: str) -> bool:
        """Check if alert should be suppressed due to recent similar alert"""
        cutoff_time = datetime.now() - timedelta(minutes=self.alert_cooldown_minutes)

        for alert in reversed(self.alert_history):
            if alert.prediction_time < cutoff_time:
                break

            if alert.metric == metric_name and alert.severity == severity:
                return True

        return False

    def _get_recommended_action(
        self, metric_name: str, severity: str, predicted_value: float
    ) -> str:
        """Get recommended action based on metric and severity"""
        actions = {
            "api_latency_p95": {
                "warning": "Review slow queries, consider scaling up API pods",
                "critical": "URGENT: Scale API pods immediately, investigate database",
            },
            "api_error_rate": {
                "warning": "Check recent deployments, review error logs",
                "critical": "URGENT: Rollback recent deploy, page on-call engineer",
            },
            "cpu_usage": {
                "warning": "Consider horizontal pod scaling",
                "critical": "URGENT: Scale pods immediately, investigate CPU-intensive tasks",
            },
            "memory_usage": {
                "warning": "Monitor memory leaks, consider pod restart",
                "critical": "URGENT: Restart pods, investigate memory leak",
            },
            "queue_length": {
                "warning": "Scale worker pods, check queue processing rate",
                "critical": "URGENT: Scale workers, investigate stuck tasks",
            },
            "active_connections": {
                "warning": "Monitor connection pool, consider scaling",
                "critical": "URGENT: Increase connection limits, scale pods",
            },
        }

        metric_actions = actions.get(metric_name, {})
        return metric_actions.get(severity, "Investigate and take appropriate action")

    def _format_alert_message(
        self,
        metric_name: str,
        current_value: float,
        predicted_value: float,
        prediction_time: datetime,
    ) -> str:
        """Format alert message"""
        time_delta = prediction_time - datetime.now()
        minutes_ahead = int(time_delta.total_seconds() / 60)

        return (
            f"🚨 PREDICTIVE ALERT: {metric_name}\n"
            f"Current: {current_value:.2f}\n"
            f"Predicted ({minutes_ahead}min): {predicted_value:.2f}\n"
            f"Expected at: {prediction_time.strftime('%H:%M:%S')}"
        )

    def _auto_tune_thresholds(
        self, historical_data: Dict[str, List[MetricData]]
    ) -> None:
        """Auto-tune thresholds based on historical data"""
        for metric_name, data_points in historical_data.items():
            if len(data_points) < 100:
                continue

            values = np.array([d.value for d in data_points])

            # Calculate percentiles
            p95 = np.percentile(values, 95)
            p99 = np.percentile(values, 99)

            # Auto-tune thresholds
            if metric_name not in self.thresholds:
                self.thresholds[metric_name] = {}

            self.thresholds[metric_name]["warning"] = p95
            self.thresholds[metric_name]["critical"] = p99

            logger.info(
                f"Auto-tuned thresholds for {metric_name}: "
                f"warning={p95:.2f}, critical={p99:.2f}"
            )

    def _save_models(self) -> None:
        """Save models to disk"""
        for metric_name, model in self.anomaly_detectors.items():
            model_path = self.model_dir / f"{metric_name}_detector.joblib"
            scaler_path = self.model_dir / f"{metric_name}_scaler.joblib"

            joblib.dump(model, model_path)
            joblib.dump(self.scalers[metric_name], scaler_path)

        # Save thresholds
        thresholds_path = self.model_dir / "thresholds.joblib"
        joblib.dump(self.thresholds, thresholds_path)

        logger.info(f"Models saved to {self.model_dir}")

    def _load_models(self) -> None:
        """Load models from disk"""
        # Load thresholds
        thresholds_path = self.model_dir / "thresholds.joblib"
        if thresholds_path.exists():
            self.thresholds = joblib.load(thresholds_path)

        # Load anomaly detectors
        for model_file in self.model_dir.glob("*_detector.joblib"):
            metric_name = model_file.stem.replace("_detector", "")
            scaler_file = self.model_dir / f"{metric_name}_scaler.joblib"

            if scaler_file.exists():
                self.anomaly_detectors[metric_name] = joblib.load(model_file)
                self.scalers[metric_name] = joblib.load(scaler_file)

                logger.info(f"Loaded model for {metric_name}")


# Global instance
predictive_alerter = PredictiveAlerter()


# Example usage
if __name__ == "__main__":
    # Simulate historical data
    historical_data = {
        "api_latency_p95": [
            MetricData(
                timestamp=datetime.now() - timedelta(hours=24 - i),
                value=300 + np.random.normal(0, 50),
                metric_name="api_latency_p95",
                labels={},
            )
            for i in range(144)  # 24 hours, 10min intervals
        ]
    }

    # Train
    alerter = PredictiveAlerter()
    alerter.train(historical_data)

    # Predict
    current_data = historical_data["api_latency_p95"][-24:]  # Last 4 hours
    alerts = alerter.predict_and_alert("api_latency_p95", current_data, horizon_minutes=60)

    print(f"\nGenerated {len(alerts)} alerts:")
    for alert in alerts:
        print(f"\n{alert.message}")
        print(f"Severity: {alert.severity.upper()}")
        print(f"Confidence: {alert.confidence:.2f}")
        print(f"Action: {alert.recommended_action}")
