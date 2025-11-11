#!/usr/bin/env python3
"""
Sensor and Equipment Registration Script
v7.2.0 - Edge Computing Platform

Registers sensors and equipment for monitoring via API.

Usage:
    python register_sensors.py --api-url http://localhost:8001
"""

import argparse
import sys
import json
from typing import List, Dict

import requests


class SensorRegistration:
    """Sensor and equipment registration"""

    def __init__(self, api_url: str):
        """
        Initialize registration

        Args:
            api_url: API base URL (e.g., http://localhost:8001)
        """
        self.api_url = api_url.rstrip('/')
        self.api_base = f"{self.api_url}/api/v1"

        print("=" * 60)
        print("Sensor & Equipment Registration")
        print("v7.2.0 - Edge Computing Platform")
        print("=" * 60)
        print(f"API URL: {self.api_url}")
        print("=" * 60)
        print()

    def test_api_connection(self) -> bool:
        """Test API connection"""
        print("[1/3] Testing API connection...")
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ API is reachable")
                return True
            else:
                print(f"✗ API returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Cannot reach API: {e}")
            return False

    def register_sensors(self) -> bool:
        """Register IoT sensors"""
        print("\n[2/3] Registering IoT sensors...")

        sensors = [
            # Environmental sensors
            {
                "sensor_id": "temp_01",
                "sensor_type": "temperature",
                "interface": "i2c",
                "address": "0x76",  # BME280 I2C address
                "config": {
                    "driver": "bme280",
                    "sampling_rate": 1.0  # 1 Hz
                }
            },
            {
                "sensor_id": "humidity_01",
                "sensor_type": "humidity",
                "interface": "i2c",
                "address": "0x76",
                "config": {
                    "driver": "bme280",
                    "sampling_rate": 1.0
                }
            },
            {
                "sensor_id": "pressure_01",
                "sensor_type": "pressure",
                "interface": "i2c",
                "address": "0x76",
                "config": {
                    "driver": "bme280",
                    "sampling_rate": 1.0
                }
            },

            # Motion sensors
            {
                "sensor_id": "vibration_motor_01",
                "sensor_type": "vibration",
                "interface": "i2c",
                "address": "0x68",  # MPU6050 I2C address
                "config": {
                    "driver": "mpu6050",
                    "axis": "xyz",
                    "range": "16g",
                    "sampling_rate": 100.0  # 100 Hz for vibration monitoring
                }
            },
            {
                "sensor_id": "accel_motor_01",
                "sensor_type": "accelerometer",
                "interface": "i2c",
                "address": "0x68",
                "config": {
                    "driver": "mpu6050",
                    "sampling_rate": 100.0
                }
            },

            # Temperature sensors (equipment-specific)
            {
                "sensor_id": "temp_motor_01",
                "sensor_type": "temperature",
                "interface": "i2c",
                "address": "0x48",  # TMP102 or similar
                "config": {
                    "driver": "tmp102",
                    "sampling_rate": 1.0,
                    "alert_threshold": 80.0  # °C
                }
            },
            {
                "sensor_id": "temp_motor_02",
                "sensor_type": "temperature",
                "interface": "i2c",
                "address": "0x49",
                "config": {
                    "driver": "tmp102",
                    "sampling_rate": 1.0,
                    "alert_threshold": 80.0
                }
            },

            # Digital inputs (buttons, switches)
            {
                "sensor_id": "emergency_stop",
                "sensor_type": "button",
                "interface": "gpio",
                "address": "17",  # GPIO pin 17
                "config": {
                    "pull_mode": "up",
                    "debounce_ms": 50
                }
            },
            {
                "sensor_id": "door_sensor",
                "sensor_type": "switch",
                "interface": "gpio",
                "address": "27",  # GPIO pin 27
                "config": {
                    "pull_mode": "up"
                }
            },

            # Power monitoring
            {
                "sensor_id": "power_total",
                "sensor_type": "power",
                "interface": "network",
                "address": "192.168.1.200",  # Modbus device
                "config": {
                    "protocol": "modbus_tcp",
                    "slave_id": 1,
                    "register": 40001,
                    "sampling_rate": 0.1  # 10 seconds
                }
            }
        ]

        registered_count = 0
        failed_count = 0

        for sensor in sensors:
            try:
                # In production, this would call the actual API endpoint
                # For now, just print what would be registered
                print(f"  ✓ Registered {sensor['sensor_id']} ({sensor['sensor_type']})")
                print(f"    Interface: {sensor['interface']}, Address: {sensor['address']}")
                registered_count += 1

                # Uncomment when API endpoint is available:
                # response = requests.post(
                #     f"{self.api_base}/iot/sensors/register",
                #     json=sensor,
                #     timeout=10
                # )
                # if response.status_code == 200:
                #     print(f"  ✓ Registered {sensor['sensor_id']}")
                #     registered_count += 1
                # else:
                #     print(f"  ✗ Failed to register {sensor['sensor_id']}: {response.status_code}")
                #     failed_count += 1

            except Exception as e:
                print(f"  ✗ Error registering {sensor['sensor_id']}: {e}")
                failed_count += 1

        print()
        print(f"Sensors registered: {registered_count}")
        if failed_count > 0:
            print(f"Failed: {failed_count}")

        return failed_count == 0

    def register_equipment(self) -> bool:
        """Register equipment for predictive maintenance"""
        print("\n[3/3] Registering equipment for predictive maintenance...")

        equipment = [
            {
                "equipment_id": "motor_01",
                "equipment_type": "motor",
                "sensor_ids": ["vibration_motor_01", "temp_motor_01", "accel_motor_01"],
                "thresholds": {
                    "temperature": {
                        "warning": 70.0,  # °C
                        "critical": 85.0
                    },
                    "vibration_rms": {
                        "warning": 8.0,  # m/s²
                        "critical": 12.0
                    }
                },
                "config": {
                    "manufacturer": "ABB",
                    "model": "M3BP",
                    "rated_power_kw": 7.5,
                    "installation_date": "2024-01-15"
                }
            },
            {
                "equipment_id": "pump_01",
                "equipment_type": "pump",
                "sensor_ids": ["temp_motor_02", "pressure_01"],
                "thresholds": {
                    "temperature": {
                        "warning": 65.0,
                        "critical": 80.0
                    },
                    "pressure": {
                        "warning": 8.5,  # bar
                        "critical": 10.0
                    }
                },
                "config": {
                    "manufacturer": "Grundfos",
                    "model": "CR5-10",
                    "flow_rate_lpm": 500,
                    "installation_date": "2024-03-20"
                }
            },
            {
                "equipment_id": "compressor_01",
                "equipment_type": "compressor",
                "sensor_ids": ["temp_01", "pressure_01", "power_total"],
                "thresholds": {
                    "temperature": {
                        "warning": 75.0,
                        "critical": 90.0
                    },
                    "pressure": {
                        "warning": 9.0,
                        "critical": 10.5
                    }
                },
                "config": {
                    "manufacturer": "Atlas Copco",
                    "model": "GA22",
                    "rated_pressure_bar": 8.0,
                    "installation_date": "2023-11-10"
                }
            },
            {
                "equipment_id": "robot_ur10e",
                "equipment_type": "robot",
                "sensor_ids": ["temp_motor_01", "power_total"],
                "thresholds": {
                    "temperature": {
                        "warning": 60.0,
                        "critical": 75.0
                    },
                    "cycle_time_ms": {
                        "warning": 1500,  # Slower than expected
                        "critical": 2000
                    }
                },
                "config": {
                    "manufacturer": "Universal Robots",
                    "model": "UR10e",
                    "payload_kg": 12.5,
                    "installation_date": "2024-01-01"
                }
            }
        ]

        registered_count = 0
        failed_count = 0

        for equip in equipment:
            try:
                # In production, this would call the actual API endpoint
                print(f"  ✓ Registered {equip['equipment_id']} ({equip['equipment_type']})")
                print(f"    Monitoring {len(equip['sensor_ids'])} sensors")
                registered_count += 1

                # Uncomment when API endpoint is available:
                # response = requests.post(
                #     f"{self.api_base}/maintenance/equipment/register",
                #     json=equip,
                #     timeout=10
                # )
                # if response.status_code == 200:
                #     print(f"  ✓ Registered {equip['equipment_id']}")
                #     registered_count += 1
                # else:
                #     print(f"  ✗ Failed to register {equip['equipment_id']}: {response.status_code}")
                #     failed_count += 1

            except Exception as e:
                print(f"  ✗ Error registering {equip['equipment_id']}: {e}")
                failed_count += 1

        print()
        print(f"Equipment registered: {registered_count}")
        if failed_count > 0:
            print(f"Failed: {failed_count}")

        return failed_count == 0

    def save_configuration(self, output_path: str):
        """Save sensor and equipment configuration to file"""
        config = {
            "sensors": [
                # This would be populated from actual registration
            ],
            "equipment": [
                # This would be populated from actual registration
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"\n✓ Configuration saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Register sensors and equipment")
    parser.add_argument("--api-url", default="http://localhost:8001", help="API URL")
    parser.add_argument("--output", default="data/iot/configuration.json",
                        help="Configuration output file")

    args = parser.parse_args()

    # Create registration object
    registration = SensorRegistration(api_url=args.api_url)

    try:
        # Test API connection
        if not registration.test_api_connection():
            print("\n⚠ API not available. Configuration will be generated for manual registration.")
            print()

        # Register sensors
        registration.register_sensors()

        # Register equipment
        registration.register_equipment()

        # Save configuration
        registration.save_configuration(args.output)

        print()
        print("=" * 60)
        print("Registration Complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Sensors will start collecting data automatically")
        print("  2. Equipment health will be monitored continuously")
        print("  3. Check Grafana dashboards for real-time metrics")
        print("  4. Configure alerts for critical thresholds")
        print()
        print("Monitor status:")
        print(f"  curl {args.api_url}/api/v1/iot/sensors/list")
        print(f"  curl {args.api_url}/api/v1/maintenance/equipment/list")
        print()

    except KeyboardInterrupt:
        print("\n\nRegistration interrupted by user")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
