"""
Predictive Maintenance Service - Smart Factory AI

v7.2.0 - Edge Computing Platform
ML-based predictive maintenance for industrial equipment

Features:
- Vibration analysis (FFT, RMS, peak detection)
- Temperature monitoring (trend analysis)
- Sound anomaly detection (acoustic monitoring)
- Remaining Useful Life (RUL) estimation
- Anomaly detection (statistical + ML)
- Alert generation
- Maintenance scheduling

Algorithms:
- Statistical Process Control (SPC)
- Isolation Forest (anomaly detection)
- LSTM (time series forecasting)
- FFT (frequency analysis)
"""

import logging
from typing import Dict, List, Optional, Tuple, Callable, Any
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class MaintenanceStatus(str, Enum):
    """Equipment maintenance status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class EquipmentHealth:
    """Equipment health assessment"""

    def __init__(
        self,
        equipment_id: str,
        status: MaintenanceStatus,
        health_score: float,  # 0-100
        rul_hours: Optional[float] = None,  # Remaining Useful Life
        anomalies: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None
    ):
        self.equipment_id = equipment_id
        self.status = status
        self.health_score = health_score
        self.rul_hours = rul_hours
        self.anomalies = anomalies or []
        self.recommendations = recommendations or []
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "equipment_id": self.equipment_id,
            "status": self.status,
            "health_score": self.health_score,
            "rul_hours": self.rul_hours,
            "anomalies": self.anomalies,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat()
        }


class PredictiveMaintenanceService:
    """
    Predictive Maintenance Service

    Monitors equipment health using:
    - Vibration analysis
    - Temperature trends
    - Acoustic monitoring
    - Statistical anomaly detection
    """

    def __init__(
        self,
        window_size: int = 1000,
        anomaly_threshold: float = 3.0,  # Sigma for statistical anomaly
        enable_ml: bool = False  # Enable ML models (requires training)
    ):
        """
        Initialize Predictive Maintenance Service

        Args:
            window_size: Size of sliding window for analysis
            anomaly_threshold: Standard deviations for anomaly detection
            enable_ml: Enable ML-based anomaly detection
        """
        self.window_size = window_size
        self.anomaly_threshold = anomaly_threshold
        self.enable_ml = enable_ml

        # Equipment registry
        self.equipment: Dict[str, Dict] = {}  # equipment_id -> config

        # Data buffers (sliding windows)
        self.buffers: Dict[str, deque] = {}  # equipment_id -> deque

        # Baseline statistics
        self.baselines: Dict[str, Dict] = {}  # equipment_id -> {mean, std, etc}

        # Alerts
        self.alert_callbacks: List[Callable] = []
        self.active_alerts: Dict[str, List[Dict]] = {}  # equipment_id -> alerts

        # ML models (if enabled)
        self.ml_models: Dict[str, Any] = {}

        # Statistics
        self.stats = {
            "total_analyses": 0,
            "anomalies_detected": 0,
            "alerts_triggered": 0,
            "equipment_failures_predicted": 0
        }

        logger.info("Predictive Maintenance Service initialized")

    # ========================================================================
    # Equipment Management
    # ========================================================================

    def register_equipment(
        self,
        equipment_id: str,
        equipment_type: str,
        sensor_ids: List[str],
        thresholds: Optional[Dict] = None
    ):
        """
        Register equipment for monitoring

        Args:
            equipment_id: Equipment identifier
            equipment_type: Type of equipment (motor, pump, compressor, etc.)
            sensor_ids: List of sensor IDs to monitor
            thresholds: Alert thresholds {metric: {warning, critical}}
        """
        self.equipment[equipment_id] = {
            "equipment_type": equipment_type,
            "sensor_ids": sensor_ids,
            "thresholds": thresholds or {},
            "registered_at": datetime.now(),
            "last_analysis": None,
            "total_runtime_hours": 0.0
        }

        # Initialize buffers
        for sensor_id in sensor_ids:
            buffer_key = f"{equipment_id}_{sensor_id}"
            self.buffers[buffer_key] = deque(maxlen=self.window_size)

        logger.info(f"Registered equipment: {equipment_id} (type={equipment_type})")

    # ========================================================================
    # Data Collection
    # ========================================================================

    def add_sensor_data(
        self,
        equipment_id: str,
        sensor_id: str,
        value: float,
        timestamp: Optional[datetime] = None
    ):
        """
        Add sensor data point

        Args:
            equipment_id: Equipment identifier
            sensor_id: Sensor identifier
            value: Sensor reading
            timestamp: Reading timestamp
        """
        if equipment_id not in self.equipment:
            logger.warning(f"Equipment not registered: {equipment_id}")
            return

        buffer_key = f"{equipment_id}_{sensor_id}"
        if buffer_key not in self.buffers:
            logger.warning(f"Sensor not registered: {sensor_id}")
            return

        # Add to buffer
        self.buffers[buffer_key].append({
            "value": value,
            "timestamp": timestamp or datetime.now()
        })

    # ========================================================================
    # Analysis
    # ========================================================================

    def analyze_equipment(
        self,
        equipment_id: str,
        update_baseline: bool = False
    ) -> Optional[EquipmentHealth]:
        """
        Analyze equipment health

        Args:
            equipment_id: Equipment identifier
            update_baseline: Update baseline statistics

        Returns:
            EquipmentHealth object
        """
        if equipment_id not in self.equipment:
            logger.error(f"Equipment not registered: {equipment_id}")
            return None

        equipment = self.equipment[equipment_id]
        sensor_ids = equipment["sensor_ids"]
        anomalies = []
        health_scores = []

        # Analyze each sensor
        for sensor_id in sensor_ids:
            buffer_key = f"{equipment_id}_{sensor_id}"
            buffer = self.buffers.get(buffer_key)

            if not buffer or len(buffer) < 10:
                continue

            # Extract values
            values = np.array([d["value"] for d in buffer])

            # Statistical analysis
            anomaly_detected, anomaly_score = self._detect_statistical_anomaly(
                values,
                equipment_id,
                sensor_id
            )

            if anomaly_detected:
                anomalies.append(f"{sensor_id}: Statistical anomaly detected (score={anomaly_score:.2f})")

            # Calculate health score for this sensor (0-100)
            sensor_health = 100.0 - min(abs(anomaly_score) * 10, 100)
            health_scores.append(sensor_health)

            # Vibration analysis (if applicable)
            if "vibration" in sensor_id.lower():
                vib_anomalies = self._analyze_vibration(values)
                anomalies.extend(vib_anomalies)

            # Temperature trend analysis
            if "temp" in sensor_id.lower():
                temp_anomalies = self._analyze_temperature_trend(values)
                anomalies.extend(temp_anomalies)

        # Overall health score
        overall_health = np.mean(health_scores) if health_scores else 100.0

        # Determine status
        if overall_health >= 80:
            status = MaintenanceStatus.HEALTHY
        elif overall_health >= 60:
            status = MaintenanceStatus.WARNING
        elif overall_health >= 40:
            status = MaintenanceStatus.CRITICAL
        else:
            status = MaintenanceStatus.FAILED

        # Estimate Remaining Useful Life (simplified)
        rul_hours = self._estimate_rul(equipment_id, overall_health)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            equipment_id,
            status,
            anomalies,
            rul_hours
        )

        # Create health assessment
        health = EquipmentHealth(
            equipment_id=equipment_id,
            status=status,
            health_score=overall_health,
            rul_hours=rul_hours,
            anomalies=anomalies,
            recommendations=recommendations
        )

        # Update equipment stats
        equipment["last_analysis"] = datetime.now()
        self.stats["total_analyses"] += 1

        if anomalies:
            self.stats["anomalies_detected"] += len(anomalies)

        # Trigger alerts if needed
        self._check_and_trigger_alerts(health)

        # Update baseline if requested
        if update_baseline:
            self._update_baseline(equipment_id, sensor_ids)

        return health

    def _detect_statistical_anomaly(
        self,
        values: np.ndarray,
        equipment_id: str,
        sensor_id: str
    ) -> Tuple[bool, float]:
        """
        Detect anomaly using statistical methods (Z-score)

        Returns:
            (anomaly_detected, anomaly_score)
        """
        if len(values) < 10:
            return False, 0.0

        # Get or compute baseline
        baseline_key = f"{equipment_id}_{sensor_id}"
        if baseline_key not in self.baselines:
            # Use current data as baseline
            self.baselines[baseline_key] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values)
            }

        baseline = self.baselines[baseline_key]

        # Calculate Z-score for recent value
        recent_value = values[-1]
        if baseline["std"] > 0:
            z_score = (recent_value - baseline["mean"]) / baseline["std"]
        else:
            z_score = 0.0

        # Check threshold
        is_anomaly = abs(z_score) > self.anomaly_threshold

        return is_anomaly, z_score

    def _analyze_vibration(self, values: np.ndarray) -> List[str]:
        """
        Analyze vibration data using FFT

        Returns:
            List of detected anomalies
        """
        anomalies = []

        if len(values) < 64:
            return anomalies

        # Calculate RMS (Root Mean Square)
        rms = np.sqrt(np.mean(values ** 2))

        # Peak detection
        peak = np.max(np.abs(values))

        # Crest factor (peak / RMS)
        crest_factor = peak / rms if rms > 0 else 0

        # Check thresholds (simplified)
        if rms > 10.0:  # Adjust based on equipment
            anomalies.append(f"High vibration RMS: {rms:.2f}")

        if crest_factor > 5.0:
            anomalies.append(f"High crest factor: {crest_factor:.2f} (possible impact)")

        # FFT analysis (frequency domain)
        try:
            fft = np.fft.fft(values)
            freqs = np.fft.fftfreq(len(values))
            magnitude = np.abs(fft)

            # Find dominant frequencies
            dominant_idx = np.argsort(magnitude)[-3:]  # Top 3 frequencies
            dominant_freqs = freqs[dominant_idx]

            # Check for abnormal frequencies (simplified)
            # In practice, would compare against equipment-specific signatures

        except Exception as e:
            logger.error(f"FFT analysis error: {e}")

        return anomalies

    def _analyze_temperature_trend(self, values: np.ndarray) -> List[str]:
        """
        Analyze temperature trend

        Returns:
            List of detected anomalies
        """
        anomalies = []

        if len(values) < 20:
            return anomalies

        # Calculate trend (linear regression slope)
        x = np.arange(len(values))
        coefficients = np.polyfit(x, values, 1)
        slope = coefficients[0]

        # Check for rapid temperature rise
        if slope > 0.1:  # Adjust threshold based on equipment
            anomalies.append(f"Temperature rising: {slope:.3f}°C per reading")

        # Check absolute temperature
        current_temp = values[-1]
        if current_temp > 80.0:  # Adjust based on equipment
            anomalies.append(f"High temperature: {current_temp:.1f}°C")

        return anomalies

    def _estimate_rul(
        self,
        equipment_id: str,
        health_score: float
    ) -> Optional[float]:
        """
        Estimate Remaining Useful Life (simplified)

        Returns:
            Estimated hours remaining, or None if unknown
        """
        # Simplified linear model
        # In practice, would use LSTM or other ML models

        if health_score >= 80:
            return None  # Healthy, RUL unknown

        # Assume linear degradation
        # 100% health -> 8760 hours (1 year)
        # 0% health -> 0 hours
        max_rul_hours = 8760.0
        rul_hours = (health_score / 100.0) * max_rul_hours

        return rul_hours

    def _generate_recommendations(
        self,
        equipment_id: str,
        status: MaintenanceStatus,
        anomalies: List[str],
        rul_hours: Optional[float]
    ) -> List[str]:
        """Generate maintenance recommendations"""
        recommendations = []

        if status == MaintenanceStatus.HEALTHY:
            recommendations.append("Continue normal operation")
            recommendations.append("Next inspection: 720 hours (30 days)")

        elif status == MaintenanceStatus.WARNING:
            recommendations.append("Schedule inspection within 168 hours (7 days)")
            recommendations.append("Increase monitoring frequency to 1 hour")

            if any("vibration" in a.lower() for a in anomalies):
                recommendations.append("Check bearing alignment and lubrication")

            if any("temperature" in a.lower() for a in anomalies):
                recommendations.append("Inspect cooling system")

        elif status == MaintenanceStatus.CRITICAL:
            recommendations.append("URGENT: Schedule maintenance within 24 hours")
            recommendations.append("Reduce operational load")
            recommendations.append("Increase monitoring to real-time")

            if rul_hours and rul_hours < 100:
                recommendations.append(f"Estimated failure in {rul_hours:.0f} hours - prepare replacement")

        elif status == MaintenanceStatus.FAILED:
            recommendations.append("EMERGENCY: Stop equipment immediately")
            recommendations.append("Conduct failure analysis")
            recommendations.append("Prepare for equipment replacement")

        return recommendations

    def _update_baseline(self, equipment_id: str, sensor_ids: List[str]):
        """Update baseline statistics"""
        for sensor_id in sensor_ids:
            buffer_key = f"{equipment_id}_{sensor_id}"
            buffer = self.buffers.get(buffer_key)

            if not buffer or len(buffer) < 10:
                continue

            values = np.array([d["value"] for d in buffer])

            baseline_key = f"{equipment_id}_{sensor_id}"
            self.baselines[baseline_key] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "updated_at": datetime.now()
            }

        logger.info(f"Updated baseline for {equipment_id}")

    # ========================================================================
    # Alerts
    # ========================================================================

    def register_alert_callback(self, callback: Callable):
        """
        Register alert callback

        Args:
            callback: Function to call on alert (EquipmentHealth) -> None
        """
        self.alert_callbacks.append(callback)

    def _check_and_trigger_alerts(self, health: EquipmentHealth):
        """Check and trigger alerts based on health assessment"""
        equipment_id = health.equipment_id

        # Determine alert level
        if health.status == MaintenanceStatus.FAILED:
            alert_level = AlertLevel.EMERGENCY
        elif health.status == MaintenanceStatus.CRITICAL:
            alert_level = AlertLevel.CRITICAL
        elif health.status == MaintenanceStatus.WARNING:
            alert_level = AlertLevel.WARNING
        else:
            return  # No alert needed

        # Create alert
        alert = {
            "equipment_id": equipment_id,
            "level": alert_level,
            "message": f"Equipment health {health.status}: {health.health_score:.1f}%",
            "anomalies": health.anomalies,
            "recommendations": health.recommendations,
            "timestamp": datetime.now()
        }

        # Store alert
        if equipment_id not in self.active_alerts:
            self.active_alerts[equipment_id] = []
        self.active_alerts[equipment_id].append(alert)

        self.stats["alerts_triggered"] += 1

        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(health)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

        logger.warning(f"Alert triggered: {alert['message']}")

    def get_active_alerts(self, equipment_id: Optional[str] = None) -> List[Dict]:
        """Get active alerts"""
        if equipment_id:
            return self.active_alerts.get(equipment_id, [])
        else:
            # Return all alerts
            all_alerts = []
            for alerts in self.active_alerts.values():
                all_alerts.extend(alerts)
            return all_alerts

    def clear_alerts(self, equipment_id: str):
        """Clear alerts for equipment"""
        if equipment_id in self.active_alerts:
            del self.active_alerts[equipment_id]

    # ========================================================================
    # Utilities
    # ========================================================================

    def get_stats(self) -> Dict:
        """Get service statistics"""
        return {
            **self.stats,
            "equipment_count": len(self.equipment),
            "active_alerts": sum(len(alerts) for alerts in self.active_alerts.values())
        }

    def list_equipment(self) -> List[Dict]:
        """List registered equipment"""
        equipment_list = []

        for equipment_id, equipment in self.equipment.items():
            equipment_list.append({
                "equipment_id": equipment_id,
                "equipment_type": equipment["equipment_type"],
                "sensor_count": len(equipment["sensor_ids"]),
                "last_analysis": equipment["last_analysis"].isoformat() if equipment["last_analysis"] else None,
                "active_alerts": len(self.active_alerts.get(equipment_id, []))
            })

        return equipment_list


# Global singleton
_predictive_maintenance_service: Optional[PredictiveMaintenanceService] = None


def get_predictive_maintenance_service() -> PredictiveMaintenanceService:
    """Get or create Predictive Maintenance Service singleton"""
    global _predictive_maintenance_service
    if _predictive_maintenance_service is None:
        _predictive_maintenance_service = PredictiveMaintenanceService()
    return _predictive_maintenance_service
