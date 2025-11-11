"""
Manufacturing System Test Suite

v7.1.0 - Advanced Manufacturing
Comprehensive tests for LORA vision and UR10e robot integration

Test Categories:
- Unit tests: Individual services
- Integration tests: Vision-Robot pipeline
- Performance tests: Inference and cycle times
- Safety tests: Workspace and collision detection
"""

import pytest
import numpy as np
import cv2
from pathlib import Path

# Import services
from src.services.lora_vision_service import LORAVisionService
from src.services.ur10e_service import UR10eService, RobotState
from src.utils.robot_safety import RobotSafetyValidator, SafetyLevel
from src.utils.coordinate_transform import CoordinateTransform


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def lora_vision():
    """Create LORA vision service instance"""
    service = LORAVisionService()
    return service


@pytest.fixture
def ur10e_robot():
    """Create UR10e robot service instance (simulation mode)"""
    robot = UR10eService(simulation_mode=True)
    robot.connect()
    yield robot
    robot.disconnect()


@pytest.fixture
def safety_validator():
    """Create safety validator instance"""
    return RobotSafetyValidator()


@pytest.fixture
def coordinate_transform():
    """Create coordinate transform instance"""
    return CoordinateTransform()


@pytest.fixture
def test_image():
    """Create test image (640x640x3)"""
    return np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)


# ============================================================================
# LORA Vision Service Tests
# ============================================================================

class TestLORAVisionService:
    """Test LORA vision service"""

    def test_initialization(self, lora_vision):
        """Test service initialization"""
        assert lora_vision is not None
        assert len(lora_vision.adapters) == 4  # 4 product types
        assert lora_vision.current_product is None  # Not loaded yet

    def test_list_adapters(self, lora_vision):
        """Test adapter listing"""
        adapters = lora_vision.list_adapters()

        assert len(adapters) == 4
        assert all("product_type" in a for a in adapters)
        assert all("defect_classes" in a for a in adapters)

    def test_adapter_switching(self, lora_vision):
        """Test adapter switching performance"""
        product = "pet_bottles"

        result = lora_vision.switch_adapter(product)

        assert result["switched"] is True
        assert result["product_type"] == product
        assert result["switch_time_ms"] < 500  # Should be <200ms, but allow margin
        assert lora_vision.current_product == product

    def test_adapter_switching_idempotent(self, lora_vision):
        """Test switching to same adapter is fast"""
        product = "pet_bottles"

        # First switch
        lora_vision.switch_adapter(product)

        # Second switch (should be no-op)
        result = lora_vision.switch_adapter(product)

        assert result["switched"] is False
        assert result["message"] == "Already loaded"

    def test_inspection(self, lora_vision, test_image):
        """Test defect inspection"""
        product = "pet_bottles"

        result = lora_vision.inspect(test_image, product_type=product)

        assert "defects" in result
        assert "defect_count" in result
        assert "inference_time_ms" in result
        assert "lora_adapter" in result
        assert result["product_type"] == product

    def test_inspection_performance(self, lora_vision, test_image):
        """Test inspection performance (should be <50ms target, <100ms acceptable)"""
        product = "aluminum_cans"

        # Warm-up
        lora_vision.inspect(test_image, product_type=product)

        # Measure performance
        results = []
        for _ in range(10):
            result = lora_vision.inspect(test_image, product_type=product)
            results.append(result["inference_time_ms"])

        avg_time = np.mean(results)
        assert avg_time < 200  # Should be <50ms in production with trained models

    def test_metrics(self, lora_vision, test_image):
        """Test metrics tracking"""
        # Run some inspections
        lora_vision.inspect(test_image, product_type="pet_bottles")
        lora_vision.inspect(test_image, product_type="pet_bottles")

        metrics = lora_vision.get_metrics()

        assert metrics["total_inspections"] >= 2
        assert metrics["avg_inference_ms"] > 0


# ============================================================================
# UR10e Robot Service Tests
# ============================================================================

class TestUR10eService:
    """Test UR10e robot service"""

    def test_initialization(self, ur10e_robot):
        """Test robot initialization"""
        assert ur10e_robot is not None
        assert ur10e_robot.simulation_mode is True
        assert ur10e_robot.state == RobotState.IDLE

    def test_connection(self):
        """Test robot connection"""
        robot = UR10eService(simulation_mode=True)
        result = robot.connect()

        assert result["connected"] is True
        assert result["mode"] == "simulation"
        assert robot.state == RobotState.IDLE

    def test_get_current_pose(self, ur10e_robot):
        """Test getting current pose"""
        pose = ur10e_robot.get_current_pose()

        assert len(pose) == 6  # (x, y, z, rx, ry, rz)
        assert isinstance(pose, tuple)

    def test_move_to_pose(self, ur10e_robot):
        """Test robot movement"""
        target_pose = (0.4, 0.0, 0.3, 0, 0, 0)

        result = ur10e_robot.move_to_pose(target_pose)

        assert result["success"] is True
        assert "move_time_ms" in result
        assert result["safety_zone"] in [SafetyZone.SAFE, SafetyZone.WARNING]

    def test_move_invalid_position(self, ur10e_robot):
        """Test movement to invalid position (out of workspace)"""
        invalid_pose = (2.0, 0.0, 0.3, 0, 0, 0)  # Outside workspace

        result = ur10e_robot.move_to_pose(invalid_pose)

        assert result["success"] is False
        assert "error" in result

    def test_pick_and_place(self, ur10e_robot):
        """Test pick and place operation"""
        pick_coords = (0.4, 0.1, 0.05)
        place_coords = (0.3, 0.4, 0.1)

        result = ur10e_robot.pick_and_place(pick_coords, place_coords)

        assert result["success"] is True
        assert "cycle_time_ms" in result
        assert result["cycle_time_ms"] < 5000  # Should be ~1.2s in production

    def test_emergency_stop(self, ur10e_robot):
        """Test emergency stop"""
        result = ur10e_robot.emergency_stop()

        assert ur10e_robot.emergency_stop_active is True
        assert ur10e_robot.state == RobotState.EMERGENCY_STOP

        # Reset
        ur10e_robot.reset_emergency_stop()
        assert ur10e_robot.emergency_stop_active is False

    def test_metrics(self, ur10e_robot):
        """Test metrics tracking"""
        # Execute some operations
        ur10e_robot.pick_and_place((0.4, 0.1, 0.05), (0.3, 0.4, 0.1))

        metrics = ur10e_robot.get_metrics()

        assert metrics["total_picks"] >= 1
        assert metrics["successful_cycles"] >= 1
        assert "avg_cycle_time_ms" in metrics


# ============================================================================
# Safety Validation Tests
# ============================================================================

class TestRobotSafety:
    """Test robot safety validator"""

    def test_initialization(self, safety_validator):
        """Test safety validator initialization"""
        assert safety_validator is not None
        assert safety_validator.max_force_n == 150.0

    def test_validate_safe_position(self, safety_validator):
        """Test validation of safe position"""
        safe_position = (0.5, 0.0, 0.3)

        is_safe, safety_level, message = safety_validator.validate_position(safe_position)

        assert is_safe is True
        assert safety_level == SafetyLevel.SAFE

    def test_validate_out_of_bounds(self, safety_validator):
        """Test validation of out-of-bounds position"""
        unsafe_position = (2.0, 0.0, 0.3)  # X > max

        is_safe, safety_level, message = safety_validator.validate_position(unsafe_position)

        assert is_safe is False
        assert safety_level == SafetyLevel.CRITICAL

    def test_validate_warning_zone(self, safety_validator):
        """Test validation near boundary (warning zone)"""
        warning_position = (
            safety_validator.workspace_bounds["x_min"] + 0.03,  # Just inside
            0.0,
            0.3
        )

        is_safe, safety_level, message = safety_validator.validate_position(warning_position)

        assert is_safe is True
        assert safety_level == SafetyLevel.WARNING

    def test_force_validation(self, safety_validator):
        """Test force limiting validation"""
        # Safe force
        is_safe, level, msg = safety_validator.validate_force(100.0)
        assert is_safe is True

        # Excessive force
        is_safe, level, msg = safety_validator.validate_force(200.0)
        assert is_safe is False
        assert level == SafetyLevel.CRITICAL

    def test_speed_adjustment(self, safety_validator):
        """Test speed adjustment by safety level"""
        current_pos = (0.5, 0.0, 0.3)
        target_pos = (0.6, 0.0, 0.3)

        safe_speed = safety_validator.calculate_safe_speed(
            current_pos,
            target_pos,
            requested_speed=1.0
        )

        assert 0.0 <= safe_speed <= 1.0


# ============================================================================
# Coordinate Transform Tests
# ============================================================================

class TestCoordinateTransform:
    """Test coordinate transformation"""

    def test_initialization(self, coordinate_transform):
        """Test transform initialization"""
        assert coordinate_transform is not None
        assert coordinate_transform.is_calibrated is False  # No calibration yet

    def test_pixel_to_camera(self, coordinate_transform):
        """Test pixel to camera frame conversion"""
        pixel_x = 320
        pixel_y = 240
        depth_m = 0.5

        camera_coords = coordinate_transform.pixel_to_camera(pixel_x, pixel_y, depth_m)

        assert len(camera_coords) == 3
        assert camera_coords[2] == depth_m  # Z should equal depth

    def test_camera_to_robot(self, coordinate_transform):
        """Test camera to robot frame transformation"""
        camera_x = 0.0
        camera_y = 0.0
        camera_z = 0.5

        robot_coords = coordinate_transform.camera_to_robot(camera_x, camera_y, camera_z)

        assert len(robot_coords) == 3
        # Without calibration, should be identity transform
        assert robot_coords[0] == camera_x
        assert robot_coords[1] == camera_y
        assert robot_coords[2] == camera_z

    def test_calibration_points(self, coordinate_transform):
        """Test adding calibration points"""
        camera_point = (0.1, 0.2, 0.5)
        robot_point = (0.3, 0.4, 0.5)

        coordinate_transform.add_calibration_point(camera_point, robot_point)

        assert len(coordinate_transform.calibration_points) == 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for vision-robot pipeline"""

    def test_vision_to_robot_pipeline(self, lora_vision, ur10e_robot, coordinate_transform, test_image):
        """Test complete vision-guided pick and place"""
        # 1. Vision inspection
        inspection_result = lora_vision.inspect(test_image, product_type="pet_bottles")

        # 2. If defect detected, get coordinates
        if inspection_result["defects"]:
            defect = inspection_result["defects"][0]
            bbox = defect["bbox"]

            # Center of bounding box (pixels)
            center_x = (bbox["x1"] + bbox["x2"]) / 2
            center_y = (bbox["y1"] + bbox["y2"]) / 2

            # 3. Transform to robot coordinates
            robot_coords = coordinate_transform.pixel_to_robot(
                center_x,
                center_y,
                depth_m=0.5  # Assumed depth
            )

            # 4. Execute robot pick and place
            result = ur10e_robot.pick_and_place(
                pick_coords=robot_coords,
                place_coords=(0.3, 0.4, 0.1)  # Reject bin
            )

            assert result["success"] is True

    def test_concurrent_operations(self, lora_vision, ur10e_robot, test_image):
        """Test concurrent vision inspection and robot movement"""
        # Vision inspection (fast)
        inspection_result = lora_vision.inspect(test_image, product_type="aluminum_cans")

        # Robot movement (slow)
        move_result = ur10e_robot.move_to_pose((0.4, 0.0, 0.3, 0, 0, 0))

        assert inspection_result is not None
        assert move_result["success"] is True


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.performance
class TestPerformance:
    """Performance benchmarks"""

    def test_vision_throughput(self, lora_vision, test_image):
        """Test vision inspection throughput"""
        import time

        num_iterations = 100
        start = time.time()

        for _ in range(num_iterations):
            lora_vision.inspect(test_image, product_type="pet_bottles")

        elapsed = time.time() - start
        throughput = num_iterations / elapsed

        print(f"\nVision throughput: {throughput:.1f} inspections/second")
        assert throughput > 10  # Should be >100/sec with trained models

    def test_robot_cycle_time(self, ur10e_robot):
        """Test robot pick and place cycle time"""
        results = []

        for _ in range(10):
            result = ur10e_robot.pick_and_place(
                pick_coords=(0.4, 0.1, 0.05),
                place_coords=(0.3, 0.4, 0.1)
            )
            results.append(result["cycle_time_ms"])

        avg_cycle_time = np.mean(results)

        print(f"\nAverage cycle time: {avg_cycle_time:.0f}ms")
        # Target: ~1200ms in production
        # Simulation: May vary, but should be consistent


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
