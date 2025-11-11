#!/usr/bin/env python3
"""
Camera-Robot Hand-Eye Calibration Script
v7.2.0 - Edge Computing Platform

Performs hand-eye calibration to map camera pixel coordinates to robot base coordinates.

Usage:
    python calibrate_camera_robot.py --robot-ip 192.168.1.100 --camera-url http://192.168.1.102:5000 --num-points 15
"""

import argparse
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict

import numpy as np
import cv2
import requests

try:
    import urx
except ImportError:
    print("ERROR: urx library not installed. Install: pip install urx")
    sys.exit(1)


class CameraRobotCalibration:
    """Hand-eye calibration for camera-robot system"""

    def __init__(
        self,
        robot_ip: str,
        camera_url: str,
        num_points: int = 15,
        checkerboard_size: Tuple[int, int] = (8, 6),
        square_size_mm: float = 25.0
    ):
        """
        Initialize calibration

        Args:
            robot_ip: UR10e IP address
            camera_url: Camera server URL (e.g., http://192.168.1.102:5000)
            num_points: Number of calibration points to collect
            checkerboard_size: Checkerboard pattern size (columns, rows)
            square_size_mm: Size of checkerboard squares in mm
        """
        self.robot_ip = robot_ip
        self.camera_url = camera_url
        self.num_points = num_points
        self.checkerboard_size = checkerboard_size
        self.square_size_mm = square_size_mm

        # Robot connection
        self.robot = None

        # Calibration data
        self.robot_positions = []  # Robot base coordinates
        self.image_points = []  # Pixel coordinates
        self.transformation_matrix = None

        print("=" * 60)
        print("Camera-Robot Hand-Eye Calibration")
        print("=" * 60)
        print(f"Robot IP: {robot_ip}")
        print(f"Camera URL: {camera_url}")
        print(f"Calibration points: {num_points}")
        print(f"Checkerboard: {checkerboard_size[0]}x{checkerboard_size[1]}")
        print(f"Square size: {square_size_mm}mm")
        print("=" * 60)
        print()

    def connect_robot(self) -> bool:
        """Connect to UR10e robot"""
        print("[1/4] Connecting to robot...")
        try:
            self.robot = urx.Robot(self.robot_ip)
            print(f"✓ Connected to robot at {self.robot_ip}")
            print(f"  Current pose: {self.robot.getl()}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to robot: {e}")
            return False

    def test_camera(self) -> bool:
        """Test camera connection"""
        print("\n[2/4] Testing camera connection...")
        try:
            response = requests.get(f"{self.camera_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ Camera server is running")

                # Capture test image
                response = requests.get(f"{self.camera_url}/capture", timeout=10)
                if response.status_code == 200:
                    print(f"✓ Successfully captured test image")
                    return True
                else:
                    print(f"✗ Failed to capture image: {response.status_code}")
                    return False
            else:
                print(f"✗ Camera server not healthy: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Cannot reach camera server: {e}")
            return False

    def capture_image(self) -> np.ndarray:
        """Capture image from camera"""
        response = requests.get(f"{self.camera_url}/capture", timeout=10)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to capture image: {response.status_code}")

        # Decode JPEG
        img_array = np.frombuffer(response.content, dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        return image

    def detect_checkerboard(self, image: np.ndarray) -> Tuple[bool, np.ndarray]:
        """
        Detect checkerboard pattern in image

        Returns:
            (found, corners): Found status and corner coordinates
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Find checkerboard corners
        ret, corners = cv2.findChessboardCorners(
            gray,
            self.checkerboard_size,
            None
        )

        if ret:
            # Refine corner positions
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

        return ret, corners

    def move_robot_to_position(self, position: List[float], speed: float = 0.1):
        """Move robot to position"""
        print(f"  Moving to position: {position[:3]}")
        self.robot.movel(position, acc=0.1, vel=speed)
        time.sleep(0.5)  # Wait for robot to stabilize

    def collect_calibration_data(self):
        """Collect calibration data points"""
        print("\n[3/4] Collecting calibration data...")
        print("This will take approximately 3-5 minutes.")
        print()

        # Define calibration workspace (above the robot workspace)
        # Positions in robot base frame (x, y, z, rx, ry, rz)
        workspace_center = [0.3, 0.0, 0.3, 0, 0, 0]
        workspace_range = {
            'x': 0.2,  # ±10cm in X
            'y': 0.2,  # ±10cm in Y
            'z': 0.1,  # ±5cm in Z
        }

        # Generate grid of positions
        points_per_axis = int(np.ceil(self.num_points ** (1/2)))
        x_positions = np.linspace(
            workspace_center[0] - workspace_range['x'] / 2,
            workspace_center[0] + workspace_range['x'] / 2,
            points_per_axis
        )
        y_positions = np.linspace(
            workspace_center[1] - workspace_range['y'] / 2,
            workspace_center[1] + workspace_range['y'] / 2,
            points_per_axis
        )
        z_positions = np.linspace(
            workspace_center[2] - workspace_range['z'] / 2,
            workspace_center[2] + workspace_range['z'] / 2,
            max(2, points_per_axis // 2)
        )

        positions = []
        for z in z_positions:
            for y in y_positions:
                for x in x_positions:
                    positions.append([x, y, z, 0, 0, 0])
                    if len(positions) >= self.num_points:
                        break
                if len(positions) >= self.num_points:
                    break
            if len(positions) >= self.num_points:
                break

        # Collect data at each position
        collected = 0
        for i, position in enumerate(positions[:self.num_points]):
            print(f"Point {i+1}/{self.num_points}:")

            # Move robot
            try:
                self.move_robot_to_position(position)
            except Exception as e:
                print(f"  ✗ Failed to move robot: {e}")
                continue

            # Get robot position
            robot_pos = self.robot.getl()

            # Capture image
            try:
                image = self.capture_image()
            except Exception as e:
                print(f"  ✗ Failed to capture image: {e}")
                continue

            # Detect checkerboard
            found, corners = self.detect_checkerboard(image)

            if found:
                # Get center of checkerboard
                center = corners.mean(axis=0)[0]
                pixel_x, pixel_y = center

                self.robot_positions.append(robot_pos[:3])  # Only X, Y, Z
                self.image_points.append([pixel_x, pixel_y])

                print(f"  ✓ Pattern found at pixel ({pixel_x:.1f}, {pixel_y:.1f})")
                collected += 1
            else:
                print(f"  ✗ Pattern not found")

            time.sleep(0.2)

        print()
        print(f"Collected {collected}/{self.num_points} valid calibration points")

        if collected < 4:
            print("ERROR: Not enough valid points for calibration (minimum 4 required)")
            return False

        return True

    def compute_transformation(self):
        """Compute transformation matrix from pixel to robot coordinates"""
        print("\n[4/4] Computing transformation matrix...")

        if len(self.robot_positions) < 4:
            print("ERROR: Not enough calibration points")
            return False

        # Convert to numpy arrays
        robot_points = np.array(self.robot_positions)  # Nx3 (x, y, z)
        pixel_points = np.array(self.image_points)  # Nx2 (u, v)

        # Add homogeneous coordinate to pixel points
        pixel_points_homo = np.column_stack([pixel_points, np.ones(len(pixel_points))])

        # Solve for transformation matrix using least squares
        # For each axis (x, y, z), solve: robot_coord = A * [u, v, 1]^T

        transform_x, _, _, _ = np.linalg.lstsq(pixel_points_homo, robot_points[:, 0], rcond=None)
        transform_y, _, _, _ = np.linalg.lstsq(pixel_points_homo, robot_points[:, 1], rcond=None)
        transform_z, _, _, _ = np.linalg.lstsq(pixel_points_homo, robot_points[:, 2], rcond=None)

        # Combine into 3x3 transformation matrix
        self.transformation_matrix = np.array([
            transform_x,
            transform_y,
            transform_z
        ])

        print("✓ Transformation matrix computed")
        print()
        print("Transformation matrix (pixel → robot):")
        print(self.transformation_matrix)
        print()

        # Compute calibration error
        errors = []
        for i, (pixel, robot) in enumerate(zip(pixel_points, robot_points)):
            # Transform pixel to robot coordinates
            robot_predicted = self.transformation_matrix @ np.array([pixel[0], pixel[1], 1])

            # Compute error
            error = np.linalg.norm(robot_predicted - robot)
            errors.append(error)

        mean_error = np.mean(errors) * 1000  # Convert to mm
        max_error = np.max(errors) * 1000

        print(f"Calibration accuracy:")
        print(f"  Mean error: {mean_error:.2f} mm")
        print(f"  Max error:  {max_error:.2f} mm")
        print()

        if mean_error < 2.0:
            print("✓ Calibration is excellent (<2mm error)")
        elif mean_error < 5.0:
            print("✓ Calibration is good (<5mm error)")
        else:
            print("⚠ Calibration error is high. Consider recalibrating.")

        return True

    def save_calibration(self, output_path: str):
        """Save calibration to file"""
        calibration_data = {
            "robot_ip": self.robot_ip,
            "camera_url": self.camera_url,
            "timestamp": datetime.now().isoformat(),
            "num_points": len(self.robot_positions),
            "transformation_matrix": self.transformation_matrix.tolist(),
            "robot_positions": self.robot_positions,
            "image_points": self.image_points,
            "checkerboard_size": self.checkerboard_size,
            "square_size_mm": self.square_size_mm
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(calibration_data, f, indent=2)

        print(f"✓ Calibration saved to: {output_file}")

    def cleanup(self):
        """Close connections"""
        if self.robot:
            try:
                self.robot.close()
                print("✓ Robot connection closed")
            except:
                pass


def main():
    parser = argparse.ArgumentParser(description="Camera-Robot Hand-Eye Calibration")
    parser.add_argument("--robot-ip", default="192.168.1.100", help="UR10e IP address")
    parser.add_argument("--camera-url", default="http://192.168.1.102:5000", help="Camera server URL")
    parser.add_argument("--num-points", type=int, default=15, help="Number of calibration points")
    parser.add_argument("--output", default="data/manufacturing/calibration/camera_to_robot.json",
                        help="Output calibration file")

    args = parser.parse_args()

    # Create calibration object
    calibration = CameraRobotCalibration(
        robot_ip=args.robot_ip,
        camera_url=args.camera_url,
        num_points=args.num_points
    )

    try:
        # Step 1: Connect to robot
        if not calibration.connect_robot():
            sys.exit(1)

        # Step 2: Test camera
        if not calibration.test_camera():
            sys.exit(1)

        # Step 3: Collect calibration data
        if not calibration.collect_calibration_data():
            sys.exit(1)

        # Step 4: Compute transformation
        if not calibration.compute_transformation():
            sys.exit(1)

        # Save calibration
        calibration.save_calibration(args.output)

        print()
        print("=" * 60)
        print("Calibration Complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. The calibration file is ready to use")
        print("  2. You can now run pick-and-place operations")
        print("  3. Test accuracy with: scripts/test_calibration.py")
        print()

    except KeyboardInterrupt:
        print("\n\nCalibration interrupted by user")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        calibration.cleanup()


if __name__ == "__main__":
    main()
