"""
Robot Safety Validation Module

v7.1.0 - Advanced Manufacturing
Comprehensive safety checks for UR10e collaborative robot

Safety Standards:
- ISO 10218-1:2011 (Industrial robots - Safety)
- ISO/TS 15066:2016 (Collaborative robots - Safety)
- UR10e Force Limiting: <150N (collaborative mode)
- Emergency stop response: <100ms

Features:
- Workspace boundary validation
- Collision detection zones
- Force limiting monitoring
- Joint angle limit validation
- Speed limiting for safety zones
"""

import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum
import math

import numpy as np

logger = logging.getLogger(__name__)


class SafetyLevel(str, Enum):
    """Safety compliance levels"""
    SAFE = "safe"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


class SafetyViolation(Exception):
    """Safety violation exception"""
    pass


class RobotSafetyValidator:
    """
    Robot safety validation system

    Implements safety checks for collaborative robotics operations
    """

    def __init__(
        self,
        workspace_bounds: Optional[Dict] = None,
        max_force_n: float = 150.0,
        max_speed_mps: float = 1.0,
        collision_zones: Optional[List[Dict]] = None
    ):
        """
        Initialize safety validator

        Args:
            workspace_bounds: Safe workspace boundaries
            max_force_n: Maximum force limit (Newtons)
            max_speed_mps: Maximum speed (meters per second)
            collision_zones: Pre-defined collision zones to avoid
        """
        self.workspace_bounds = workspace_bounds or {
            "x_min": 0.2,
            "x_max": 1.0,
            "y_min": -0.5,
            "y_max": 0.5,
            "z_min": 0.0,
            "z_max": 0.5
        }

        self.max_force_n = max_force_n
        self.max_speed_mps = max_speed_mps

        # Collision zones (spheres or boxes to avoid)
        self.collision_zones = collision_zones or [
            {
                "name": "human_zone",
                "type": "sphere",
                "center": (0.5, 0.0, 0.3),
                "radius": 0.3,  # 300mm safety radius
                "safety_level": SafetyLevel.CRITICAL
            }
        ]

        # Safety margins
        self.warning_margin_m = 0.05  # 50mm warning zone
        self.danger_margin_m = 0.02   # 20mm danger zone

        # Joint angle limits (UR10e specifications)
        self.joint_limits_deg = [
            (-360, 360),  # Base
            (-360, 360),  # Shoulder
            (-360, 360),  # Elbow
            (-360, 360),  # Wrist 1
            (-360, 360),  # Wrist 2
            (-360, 360)   # Wrist 3
        ]

        # Safety event log
        self.safety_events = []
        self.violations_count = 0

    def validate_position(
        self,
        position: Tuple[float, float, float]
    ) -> Tuple[bool, SafetyLevel, str]:
        """
        Validate if position is safe

        Args:
            position: Target position (x, y, z) in meters

        Returns:
            Tuple (is_safe, safety_level, message)
        """
        x, y, z = position

        # Check workspace bounds
        bounds_check = self._check_workspace_bounds(x, y, z)
        if not bounds_check[0]:
            return bounds_check

        # Check collision zones
        collision_check = self._check_collision_zones(position)
        if not collision_check[0]:
            return collision_check

        return True, SafetyLevel.SAFE, "Position validated"

    def _check_workspace_bounds(
        self,
        x: float,
        y: float,
        z: float
    ) -> Tuple[bool, SafetyLevel, str]:
        """Check if position is within workspace bounds"""

        # Critical violations (outside bounds)
        if not (self.workspace_bounds["x_min"] <= x <= self.workspace_bounds["x_max"]):
            self._log_violation(
                f"X out of bounds: {x}m "
                f"(limits: {self.workspace_bounds['x_min']}-{self.workspace_bounds['x_max']}m)"
            )
            return False, SafetyLevel.CRITICAL, f"X out of bounds: {x:.3f}m"

        if not (self.workspace_bounds["y_min"] <= y <= self.workspace_bounds["y_max"]):
            self._log_violation(
                f"Y out of bounds: {y}m "
                f"(limits: {self.workspace_bounds['y_min']}-{self.workspace_bounds['y_max']}m)"
            )
            return False, SafetyLevel.CRITICAL, f"Y out of bounds: {y:.3f}m"

        if not (self.workspace_bounds["z_min"] <= z <= self.workspace_bounds["z_max"]):
            self._log_violation(
                f"Z out of bounds: {z}m "
                f"(limits: {self.workspace_bounds['z_min']}-{self.workspace_bounds['z_max']}m)"
            )
            return False, SafetyLevel.CRITICAL, f"Z out of bounds: {z:.3f}m"

        # Danger zone (very close to bounds)
        if (x <= self.workspace_bounds["x_min"] + self.danger_margin_m or
            x >= self.workspace_bounds["x_max"] - self.danger_margin_m or
            y <= self.workspace_bounds["y_min"] + self.danger_margin_m or
            y >= self.workspace_bounds["y_max"] - self.danger_margin_m or
            z <= self.workspace_bounds["z_min"] + self.danger_margin_m):

            return True, SafetyLevel.DANGER, "Position near workspace boundary (DANGER)"

        # Warning zone
        if (x <= self.workspace_bounds["x_min"] + self.warning_margin_m or
            x >= self.workspace_bounds["x_max"] - self.warning_margin_m or
            y <= self.workspace_bounds["y_min"] + self.warning_margin_m or
            y >= self.workspace_bounds["y_max"] - self.warning_margin_m or
            z <= self.workspace_bounds["z_min"] + self.warning_margin_m):

            return True, SafetyLevel.WARNING, "Position near workspace boundary"

        return True, SafetyLevel.SAFE, "Within workspace bounds"

    def _check_collision_zones(
        self,
        position: Tuple[float, float, float]
    ) -> Tuple[bool, SafetyLevel, str]:
        """Check if position collides with restricted zones"""

        for zone in self.collision_zones:
            if zone["type"] == "sphere":
                distance = self._calculate_distance_3d(
                    position,
                    zone["center"]
                )

                if distance < zone["radius"]:
                    self._log_violation(
                        f"Collision with {zone['name']} "
                        f"(distance: {distance:.3f}m, radius: {zone['radius']:.3f}m)"
                    )
                    return False, zone["safety_level"], f"Collision: {zone['name']}"

                # Warning if approaching
                if distance < zone["radius"] + self.warning_margin_m:
                    return True, SafetyLevel.WARNING, f"Approaching: {zone['name']}"

        return True, SafetyLevel.SAFE, "No collisions"

    def validate_force(self, force_n: float) -> Tuple[bool, SafetyLevel, str]:
        """
        Validate if force is within safe limits

        Args:
            force_n: Current force (Newtons)

        Returns:
            Tuple (is_safe, safety_level, message)
        """
        if force_n > self.max_force_n:
            self._log_violation(
                f"Force exceeded: {force_n:.1f}N > {self.max_force_n:.1f}N"
            )
            return False, SafetyLevel.CRITICAL, f"Force limit exceeded: {force_n:.1f}N"

        if force_n > self.max_force_n * 0.9:
            return True, SafetyLevel.WARNING, f"Force high: {force_n:.1f}N"

        return True, SafetyLevel.SAFE, f"Force safe: {force_n:.1f}N"

    def validate_speed(
        self,
        speed_mps: float,
        safety_level: SafetyLevel = SafetyLevel.SAFE
    ) -> Tuple[bool, SafetyLevel, str]:
        """
        Validate if speed is appropriate for current safety level

        Args:
            speed_mps: Current speed (m/s)
            safety_level: Current zone safety level

        Returns:
            Tuple (is_safe, safety_level, message)
        """
        # Reduce speed limits based on safety level
        speed_limits = {
            SafetyLevel.SAFE: self.max_speed_mps,
            SafetyLevel.WARNING: self.max_speed_mps * 0.5,  # 50%
            SafetyLevel.DANGER: self.max_speed_mps * 0.25,  # 25%
            SafetyLevel.CRITICAL: 0.0  # Stop
        }

        max_allowed = speed_limits[safety_level]

        if speed_mps > max_allowed:
            self._log_violation(
                f"Speed exceeded for {safety_level}: "
                f"{speed_mps:.2f}m/s > {max_allowed:.2f}m/s"
            )
            return False, SafetyLevel.CRITICAL, f"Speed too high: {speed_mps:.2f}m/s"

        return True, SafetyLevel.SAFE, f"Speed safe: {speed_mps:.2f}m/s"

    def validate_joint_angles(
        self,
        joint_angles_deg: List[float]
    ) -> Tuple[bool, SafetyLevel, str]:
        """
        Validate if joint angles are within safe limits

        Args:
            joint_angles_deg: Joint angles in degrees [6 values]

        Returns:
            Tuple (is_safe, safety_level, message)
        """
        if len(joint_angles_deg) != 6:
            return False, SafetyLevel.CRITICAL, f"Expected 6 joint angles, got {len(joint_angles_deg)}"

        for i, (angle, (min_limit, max_limit)) in enumerate(zip(joint_angles_deg, self.joint_limits_deg)):
            if not (min_limit <= angle <= max_limit):
                self._log_violation(
                    f"Joint {i+1} out of limits: {angle:.1f}° "
                    f"(limits: {min_limit:.1f}°-{max_limit:.1f}°)"
                )
                return False, SafetyLevel.CRITICAL, f"Joint {i+1} limit exceeded"

        return True, SafetyLevel.SAFE, "Joint angles safe"

    def calculate_safe_speed(
        self,
        current_position: Tuple[float, float, float],
        target_position: Tuple[float, float, float],
        requested_speed: float = 1.0
    ) -> float:
        """
        Calculate safe speed based on position and trajectory

        Args:
            current_position: Current position (x, y, z)
            target_position: Target position (x, y, z)
            requested_speed: Requested speed (m/s)

        Returns:
            Safe speed (m/s)
        """
        # Check current position safety
        _, current_safety, _ = self.validate_position(current_position)

        # Check target position safety
        _, target_safety, _ = self.validate_position(target_position)

        # Use most restrictive safety level
        worst_safety = max(
            [current_safety, target_safety],
            key=lambda x: list(SafetyLevel).index(x)
        )

        # Speed limits based on safety level
        speed_factors = {
            SafetyLevel.SAFE: 1.0,
            SafetyLevel.WARNING: 0.5,
            SafetyLevel.DANGER: 0.25,
            SafetyLevel.CRITICAL: 0.0
        }

        safe_speed = min(
            requested_speed * speed_factors[worst_safety],
            self.max_speed_mps
        )

        if safe_speed < requested_speed:
            logger.warning(
                f"Speed reduced: {requested_speed:.2f} → {safe_speed:.2f} m/s "
                f"(safety level: {worst_safety})"
            )

        return safe_speed

    def _calculate_distance_3d(
        self,
        point1: Tuple[float, float, float],
        point2: Tuple[float, float, float]
    ) -> float:
        """Calculate Euclidean distance between two 3D points"""
        return math.sqrt(
            (point2[0] - point1[0])**2 +
            (point2[1] - point1[1])**2 +
            (point2[2] - point1[2])**2
        )

    def _log_violation(self, message: str):
        """Log safety violation"""
        self.violations_count += 1
        logger.error(f"SAFETY VIOLATION #{self.violations_count}: {message}")
        self.safety_events.append({
            "type": "violation",
            "message": message,
            "count": self.violations_count
        })

    def get_safety_report(self) -> Dict:
        """Get safety report"""
        return {
            "violations_count": self.violations_count,
            "recent_events": self.safety_events[-10:],  # Last 10 events
            "workspace_bounds": self.workspace_bounds,
            "collision_zones": len(self.collision_zones),
            "max_force_n": self.max_force_n,
            "max_speed_mps": self.max_speed_mps
        }


# Global singleton instance
_safety_validator: Optional[RobotSafetyValidator] = None


def get_safety_validator() -> RobotSafetyValidator:
    """Get or create safety validator singleton"""
    global _safety_validator
    if _safety_validator is None:
        _safety_validator = RobotSafetyValidator()
    return _safety_validator
