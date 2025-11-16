"""
Camera-to-Robot Coordinate Transformation

v7.1.0 - Advanced Manufacturing
Hand-eye calibration and coordinate transformation for vision-guided robotics

Transformation Types:
- Eye-in-Hand: Camera mounted on robot end-effector
- Eye-to-Hand: Camera fixed in workspace (our configuration)

Calibration Method:
- Collect robot poses + corresponding image points
- Solve for transformation matrix using least squares
- Validate with test points

References:
- Zhang's calibration method
- OpenCV hand-eye calibration (cv2.calibrateHandEye)
- ISO 9283: Manipulating industrial robots - Performance criteria
"""

import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json
from datetime import datetime

import numpy as np
import cv2

logger = logging.getLogger(__name__)


class CoordinateTransform:
    """
    Camera-to-robot coordinate transformation system

    Supports:
    - Hand-eye calibration
    - Coordinate transformation
    - Calibration validation
    - Transformation persistence
    """

    def __init__(
        self,
        calibration_file: Optional[str] = None,
        camera_intrinsics: Optional[Dict] = None
    ):
        """
        Initialize coordinate transform

        Args:
            calibration_file: Path to saved calibration file
            camera_intrinsics: Camera intrinsic parameters
        """
        self.calibration_file = calibration_file or "data/manufacturing/calibration/camera_to_robot.json"

        # Camera intrinsic matrix and distortion coefficients
        self.camera_intrinsics = camera_intrinsics or {
            "fx": 800.0,  # Focal length X (pixels)
            "fy": 800.0,  # Focal length Y (pixels)
            "cx": 320.0,  # Principal point X
            "cy": 240.0,  # Principal point Y
            "k1": 0.0,    # Radial distortion
            "k2": 0.0,
            "p1": 0.0,    # Tangential distortion
            "p2": 0.0,
            "k3": 0.0
        }

        # Transformation matrix (4x4 homogeneous)
        # Maps camera frame to robot base frame
        self.camera_to_robot_matrix = np.eye(4)

        # Calibration data
        self.calibration_points = []  # List of (camera_point, robot_point) pairs
        self.calibration_error_mm = None
        self.is_calibrated = False

        # Load calibration if file exists
        self._load_calibration()

        logger.info("Coordinate transform initialized")
        if self.is_calibrated:
            logger.info(f"Calibration loaded: error={self.calibration_error_mm:.2f}mm")

    def add_calibration_point(
        self,
        camera_point: Tuple[float, float, float],
        robot_point: Tuple[float, float, float]
    ):
        """
        Add calibration point pair

        Args:
            camera_point: Point in camera frame (x, y, z) in meters
            robot_point: Corresponding point in robot frame (x, y, z) in meters
        """
        self.calibration_points.append({
            "camera": camera_point,
            "robot": robot_point
        })

        logger.info(
            f"Calibration point added: "
            f"camera={camera_point}, robot={robot_point}"
        )

    def calibrate(self, method: str = "least_squares") -> Dict:
        """
        Perform hand-eye calibration

        Args:
            method: Calibration method ("least_squares", "ransac")

        Returns:
            Calibration result dictionary
        """
        if len(self.calibration_points) < 4:
            raise ValueError(
                f"Need at least 4 calibration points, got {len(self.calibration_points)}"
            )

        logger.info(f"Calibrating with {len(self.calibration_points)} points...")

        # Extract points
        camera_points = np.array([p["camera"] for p in self.calibration_points])
        robot_points = np.array([p["robot"] for p in self.calibration_points])

        if method == "least_squares":
            # Compute transformation using least squares
            # Find R, t such that: robot_point = R * camera_point + t

            # Center points
            camera_centroid = np.mean(camera_points, axis=0)
            robot_centroid = np.mean(robot_points, axis=0)

            camera_centered = camera_points - camera_centroid
            robot_centered = robot_points - robot_centroid

            # Compute rotation matrix using SVD
            H = camera_centered.T @ robot_centered
            U, S, Vt = np.linalg.svd(H)
            R = Vt.T @ U.T

            # Ensure valid rotation matrix (det(R) = 1)
            if np.linalg.det(R) < 0:
                Vt[-1, :] *= -1
                R = Vt.T @ U.T

            # Compute translation
            t = robot_centroid - R @ camera_centroid

            # Build 4x4 transformation matrix
            self.camera_to_robot_matrix = np.eye(4)
            self.camera_to_robot_matrix[:3, :3] = R
            self.camera_to_robot_matrix[:3, 3] = t

        elif method == "ransac":
            # TODO: Implement RANSAC for robust calibration
            raise NotImplementedError("RANSAC calibration not yet implemented")

        else:
            raise ValueError(f"Unknown calibration method: {method}")

        # Validate calibration
        self.calibration_error_mm = self._compute_calibration_error()
        self.is_calibrated = True

        logger.info(f"Calibration complete: error={self.calibration_error_mm:.2f}mm")

        # Save calibration
        self._save_calibration()

        return {
            "success": True,
            "num_points": len(self.calibration_points),
            "error_mm": self.calibration_error_mm,
            "transformation_matrix": self.camera_to_robot_matrix.tolist(),
            "method": method,
            "timestamp": datetime.now().isoformat()
        }

    def _compute_calibration_error(self) -> float:
        """Compute RMS calibration error in millimeters"""
        errors = []

        for point_pair in self.calibration_points:
            camera_point = np.array(point_pair["camera"])
            robot_point = np.array(point_pair["robot"])

            # Transform camera point to robot frame
            transformed = self.camera_to_robot(
                camera_point[0],
                camera_point[1],
                camera_point[2]
            )

            # Compute error
            error_m = np.linalg.norm(np.array(transformed) - robot_point)
            errors.append(error_m)

        # RMS error in mm
        rms_error_mm = np.sqrt(np.mean(np.array(errors)**2)) * 1000
        return rms_error_mm

    def camera_to_robot(
        self,
        camera_x: float,
        camera_y: float,
        camera_z: float = 0.0
    ) -> Tuple[float, float, float]:
        """
        Transform point from camera frame to robot frame

        Args:
            camera_x: X coordinate in camera frame (meters)
            camera_y: Y coordinate in camera frame (meters)
            camera_z: Z coordinate in camera frame (meters)

        Returns:
            Tuple (robot_x, robot_y, robot_z) in meters
        """
        if not self.is_calibrated:
            logger.warning("Using uncalibrated transformation (identity matrix)")

        # Homogeneous coordinates
        camera_point = np.array([camera_x, camera_y, camera_z, 1.0])

        # Transform
        robot_point = self.camera_to_robot_matrix @ camera_point

        return tuple(robot_point[:3])

    def robot_to_camera(
        self,
        robot_x: float,
        robot_y: float,
        robot_z: float
    ) -> Tuple[float, float, float]:
        """
        Transform point from robot frame to camera frame (inverse)

        Args:
            robot_x: X coordinate in robot frame (meters)
            robot_y: Y coordinate in robot frame (meters)
            robot_z: Z coordinate in robot frame (meters)

        Returns:
            Tuple (camera_x, camera_y, camera_z) in meters
        """
        if not self.is_calibrated:
            logger.warning("Using uncalibrated transformation (identity matrix)")

        # Inverse transformation
        robot_to_camera_matrix = np.linalg.inv(self.camera_to_robot_matrix)

        # Homogeneous coordinates
        robot_point = np.array([robot_x, robot_y, robot_z, 1.0])

        # Transform
        camera_point = robot_to_camera_matrix @ robot_point

        return tuple(camera_point[:3])

    def pixel_to_camera(
        self,
        pixel_x: float,
        pixel_y: float,
        depth_m: float
    ) -> Tuple[float, float, float]:
        """
        Convert pixel coordinates to 3D camera frame coordinates

        Args:
            pixel_x: X coordinate in image (pixels)
            pixel_y: Y coordinate in image (pixels)
            depth_m: Depth measurement (meters, from depth sensor or known height)

        Returns:
            Tuple (camera_x, camera_y, camera_z) in meters
        """
        # Camera intrinsics
        fx = self.camera_intrinsics["fx"]
        fy = self.camera_intrinsics["fy"]
        cx = self.camera_intrinsics["cx"]
        cy = self.camera_intrinsics["cy"]

        # Back-project to 3D
        camera_x = (pixel_x - cx) * depth_m / fx
        camera_y = (pixel_y - cy) * depth_m / fy
        camera_z = depth_m

        return (camera_x, camera_y, camera_z)

    def pixel_to_robot(
        self,
        pixel_x: float,
        pixel_y: float,
        depth_m: float
    ) -> Tuple[float, float, float]:
        """
        Convert pixel coordinates directly to robot frame

        Args:
            pixel_x: X coordinate in image (pixels)
            pixel_y: Y coordinate in image (pixels)
            depth_m: Depth measurement (meters)

        Returns:
            Tuple (robot_x, robot_y, robot_z) in meters
        """
        # Pixel → Camera frame
        camera_point = self.pixel_to_camera(pixel_x, pixel_y, depth_m)

        # Camera frame → Robot frame
        robot_point = self.camera_to_robot(*camera_point)

        return robot_point

    def _save_calibration(self):
        """Save calibration to file"""
        calibration_path = Path(self.calibration_file)
        calibration_path.parent.mkdir(parents=True, exist_ok=True)

        calibration_data = {
            "calibrated": self.is_calibrated,
            "error_mm": self.calibration_error_mm,
            "num_points": len(self.calibration_points),
            "transformation_matrix": self.camera_to_robot_matrix.tolist(),
            "camera_intrinsics": self.camera_intrinsics,
            "calibration_points": self.calibration_points,
            "timestamp": datetime.now().isoformat()
        }

        with open(calibration_path, 'w') as f:
            json.dump(calibration_data, f, indent=2)

        logger.info(f"Calibration saved: {calibration_path}")

    def _load_calibration(self):
        """Load calibration from file"""
        calibration_path = Path(self.calibration_file)

        if not calibration_path.exists():
            logger.info("No calibration file found")
            return

        try:
            with open(calibration_path, 'r') as f:
                calibration_data = json.load(f)

            self.is_calibrated = calibration_data.get("calibrated", False)
            self.calibration_error_mm = calibration_data.get("error_mm")
            self.camera_to_robot_matrix = np.array(
                calibration_data["transformation_matrix"]
            )
            self.calibration_points = calibration_data.get("calibration_points", [])
            self.camera_intrinsics = calibration_data.get(
                "camera_intrinsics",
                self.camera_intrinsics
            )

            logger.info(f"Calibration loaded from: {calibration_path}")

        except Exception as e:
            logger.error(f"Failed to load calibration: {e}")

    def get_calibration_info(self) -> Dict:
        """Get calibration information"""
        return {
            "is_calibrated": self.is_calibrated,
            "calibration_error_mm": self.calibration_error_mm,
            "num_calibration_points": len(self.calibration_points),
            "transformation_matrix": self.camera_to_robot_matrix.tolist(),
            "camera_intrinsics": self.camera_intrinsics,
            "calibration_file": self.calibration_file
        }


# Global singleton instance
_coordinate_transform: Optional[CoordinateTransform] = None


def get_coordinate_transform() -> CoordinateTransform:
    """Get or create coordinate transform singleton"""
    global _coordinate_transform
    if _coordinate_transform is None:
        _coordinate_transform = CoordinateTransform()
    return _coordinate_transform
