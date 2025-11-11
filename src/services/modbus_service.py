"""
Modbus Gateway Service - Industrial Protocol

v7.2.0 - Edge Computing Platform
Modbus RTU/TCP gateway for industrial equipment communication

Supported:
- Modbus TCP (Ethernet)
- Modbus RTU (Serial RS-485/RS-232)
- Read/Write registers
- Coils and discrete inputs
- Multiple slave devices

Features:
- Auto-reconnect
- Request batching
- Error handling
- Data caching
- Register mapping
"""

import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from enum import Enum
import time
import threading

try:
    from pymodbus.client import ModbusTcpClient, ModbusSerialClient
    from pymodbus.exceptions import ModbusException
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ModbusProtocol(str, Enum):
    """Modbus protocol types"""
    TCP = "tcp"  # Modbus TCP over Ethernet
    RTU = "rtu"  # Modbus RTU over Serial


class RegisterType(str, Enum):
    """Modbus register types"""
    COIL = "coil"  # Read/Write 1-bit (0x01, 0x05, 0x0F)
    DISCRETE_INPUT = "discrete_input"  # Read-only 1-bit (0x02)
    HOLDING_REGISTER = "holding_register"  # Read/Write 16-bit (0x03, 0x06, 0x10)
    INPUT_REGISTER = "input_register"  # Read-only 16-bit (0x04)


class ModbusStatus(str, Enum):
    """Modbus connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class ModbusDevice:
    """Modbus device configuration"""

    def __init__(
        self,
        device_id: str,
        slave_id: int,
        register_map: Optional[Dict] = None
    ):
        self.device_id = device_id
        self.slave_id = slave_id
        self.register_map = register_map or {}
        self.last_read = None
        self.read_count = 0
        self.error_count = 0


class ModbusService:
    """
    Modbus Gateway Service

    Manages Modbus communication with:
    - TCP and RTU protocols
    - Multiple slave devices
    - Auto-reconnect
    - Data caching
    """

    def __init__(
        self,
        protocol: ModbusProtocol = ModbusProtocol.TCP,
        host: str = "localhost",
        port: int = 502,
        serial_port: Optional[str] = None,
        baudrate: int = 9600,
        timeout: int = 3,
        cache_ttl: int = 1
    ):
        """
        Initialize Modbus Service

        Args:
            protocol: Modbus protocol (TCP or RTU)
            host: Host address (for TCP)
            port: Port number (for TCP)
            serial_port: Serial port path (for RTU, e.g., /dev/ttyUSB0)
            baudrate: Serial baudrate (for RTU)
            timeout: Request timeout in seconds
            cache_ttl: Cache time-to-live in seconds
        """
        if not MODBUS_AVAILABLE:
            raise ImportError("pymodbus not installed. Install: pip install pymodbus")

        self.protocol = protocol
        self.host = host
        self.port = port
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.timeout = timeout
        self.cache_ttl = cache_ttl

        # Connection state
        self.status = ModbusStatus.DISCONNECTED
        self.connected = False
        self.client = None

        # Device registry
        self.devices: Dict[int, ModbusDevice] = {}  # slave_id -> device

        # Data cache
        self.cache: Dict[str, Dict] = {}  # cache_key -> {value, timestamp}
        self.cache_lock = threading.Lock()

        # Statistics
        self.stats = {
            "read_operations": 0,
            "write_operations": 0,
            "errors": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

        logger.info(f"Modbus Service initialized (protocol={protocol})")

    # ========================================================================
    # Connection Management
    # ========================================================================

    def connect(self) -> bool:
        """
        Connect to Modbus device(s)

        Returns:
            Success status
        """
        if self.connected:
            logger.warning("Already connected")
            return True

        try:
            self.status = ModbusStatus.CONNECTING

            if self.protocol == ModbusProtocol.TCP:
                logger.info(f"Connecting to Modbus TCP: {self.host}:{self.port}")
                self.client = ModbusTcpClient(
                    host=self.host,
                    port=self.port,
                    timeout=self.timeout
                )
            elif self.protocol == ModbusProtocol.RTU:
                if not self.serial_port:
                    raise ValueError("Serial port required for Modbus RTU")

                logger.info(f"Connecting to Modbus RTU: {self.serial_port} @ {self.baudrate}")
                self.client = ModbusSerialClient(
                    port=self.serial_port,
                    baudrate=self.baudrate,
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported protocol: {self.protocol}")

            # Establish connection
            success = self.client.connect()

            if success:
                self.connected = True
                self.status = ModbusStatus.CONNECTED
                logger.info("Modbus connected")
                return True
            else:
                self.status = ModbusStatus.ERROR
                logger.error("Modbus connection failed")
                return False

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.status = ModbusStatus.ERROR
            return False

    def disconnect(self):
        """Disconnect from Modbus"""
        if not self.connected:
            return

        try:
            if self.client:
                self.client.close()
            self.connected = False
            self.status = ModbusStatus.DISCONNECTED
            logger.info("Modbus disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

    def is_connected(self) -> bool:
        """Check if connected"""
        return self.connected

    # ========================================================================
    # Device Management
    # ========================================================================

    def register_device(
        self,
        device_id: str,
        slave_id: int,
        register_map: Optional[Dict] = None
    ) -> ModbusDevice:
        """
        Register Modbus device

        Args:
            device_id: Device identifier
            slave_id: Modbus slave/unit ID (1-247)
            register_map: Register mapping {name: {address, type, count}}

        Returns:
            ModbusDevice object
        """
        device = ModbusDevice(
            device_id=device_id,
            slave_id=slave_id,
            register_map=register_map
        )

        self.devices[slave_id] = device

        logger.info(f"Registered device: {device_id} (slave_id={slave_id})")
        return device

    def get_device(self, slave_id: int) -> Optional[ModbusDevice]:
        """Get device by slave ID"""
        return self.devices.get(slave_id)

    # ========================================================================
    # Read Operations
    # ========================================================================

    def read_coils(
        self,
        slave_id: int,
        address: int,
        count: int = 1,
        use_cache: bool = True
    ) -> Optional[List[bool]]:
        """
        Read coils (function code 0x01)

        Args:
            slave_id: Modbus slave ID
            address: Starting address
            count: Number of coils to read
            use_cache: Use cached data if available

        Returns:
            List of boolean values or None on error
        """
        cache_key = f"coil_{slave_id}_{address}_{count}"

        # Check cache
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                self.stats["cache_hits"] += 1
                return cached

        self.stats["cache_misses"] += 1

        if not self.connected:
            logger.error("Not connected to Modbus")
            return None

        try:
            response = self.client.read_coils(
                address=address,
                count=count,
                slave=slave_id
            )

            if response.isError():
                logger.error(f"Read coils error: {response}")
                self.stats["errors"] += 1
                return None

            values = response.bits[:count]
            self.stats["read_operations"] += 1

            # Update device stats
            if slave_id in self.devices:
                device = self.devices[slave_id]
                device.read_count += 1
                device.last_read = datetime.now()

            # Cache result
            self._set_cached(cache_key, values)

            return values

        except ModbusException as e:
            logger.error(f"Modbus exception reading coils: {e}")
            self.stats["errors"] += 1
            return None
        except Exception as e:
            logger.error(f"Error reading coils: {e}")
            self.stats["errors"] += 1
            return None

    def read_discrete_inputs(
        self,
        slave_id: int,
        address: int,
        count: int = 1,
        use_cache: bool = True
    ) -> Optional[List[bool]]:
        """
        Read discrete inputs (function code 0x02)

        Args:
            slave_id: Modbus slave ID
            address: Starting address
            count: Number of inputs to read
            use_cache: Use cached data if available

        Returns:
            List of boolean values or None on error
        """
        cache_key = f"discrete_{slave_id}_{address}_{count}"

        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                self.stats["cache_hits"] += 1
                return cached

        self.stats["cache_misses"] += 1

        if not self.connected:
            return None

        try:
            response = self.client.read_discrete_inputs(
                address=address,
                count=count,
                slave=slave_id
            )

            if response.isError():
                self.stats["errors"] += 1
                return None

            values = response.bits[:count]
            self.stats["read_operations"] += 1

            if slave_id in self.devices:
                self.devices[slave_id].read_count += 1
                self.devices[slave_id].last_read = datetime.now()

            self._set_cached(cache_key, values)
            return values

        except Exception as e:
            logger.error(f"Error reading discrete inputs: {e}")
            self.stats["errors"] += 1
            return None

    def read_holding_registers(
        self,
        slave_id: int,
        address: int,
        count: int = 1,
        use_cache: bool = True
    ) -> Optional[List[int]]:
        """
        Read holding registers (function code 0x03)

        Args:
            slave_id: Modbus slave ID
            address: Starting address
            count: Number of registers to read
            use_cache: Use cached data if available

        Returns:
            List of register values or None on error
        """
        cache_key = f"holding_{slave_id}_{address}_{count}"

        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                self.stats["cache_hits"] += 1
                return cached

        self.stats["cache_misses"] += 1

        if not self.connected:
            return None

        try:
            response = self.client.read_holding_registers(
                address=address,
                count=count,
                slave=slave_id
            )

            if response.isError():
                self.stats["errors"] += 1
                return None

            values = response.registers
            self.stats["read_operations"] += 1

            if slave_id in self.devices:
                self.devices[slave_id].read_count += 1
                self.devices[slave_id].last_read = datetime.now()

            self._set_cached(cache_key, values)
            return values

        except Exception as e:
            logger.error(f"Error reading holding registers: {e}")
            self.stats["errors"] += 1
            return None

    def read_input_registers(
        self,
        slave_id: int,
        address: int,
        count: int = 1,
        use_cache: bool = True
    ) -> Optional[List[int]]:
        """
        Read input registers (function code 0x04)

        Args:
            slave_id: Modbus slave ID
            address: Starting address
            count: Number of registers to read
            use_cache: Use cached data if available

        Returns:
            List of register values or None on error
        """
        cache_key = f"input_{slave_id}_{address}_{count}"

        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                self.stats["cache_hits"] += 1
                return cached

        self.stats["cache_misses"] += 1

        if not self.connected:
            return None

        try:
            response = self.client.read_input_registers(
                address=address,
                count=count,
                slave=slave_id
            )

            if response.isError():
                self.stats["errors"] += 1
                return None

            values = response.registers
            self.stats["read_operations"] += 1

            if slave_id in self.devices:
                self.devices[slave_id].read_count += 1
                self.devices[slave_id].last_read = datetime.now()

            self._set_cached(cache_key, values)
            return values

        except Exception as e:
            logger.error(f"Error reading input registers: {e}")
            self.stats["errors"] += 1
            return None

    # ========================================================================
    # Write Operations
    # ========================================================================

    def write_coil(
        self,
        slave_id: int,
        address: int,
        value: bool
    ) -> bool:
        """
        Write single coil (function code 0x05)

        Args:
            slave_id: Modbus slave ID
            address: Coil address
            value: Boolean value to write

        Returns:
            Success status
        """
        if not self.connected:
            return False

        try:
            response = self.client.write_coil(
                address=address,
                value=value,
                slave=slave_id
            )

            if response.isError():
                self.stats["errors"] += 1
                return False

            self.stats["write_operations"] += 1

            # Invalidate cache
            cache_key = f"coil_{slave_id}_{address}_1"
            self._invalidate_cache(cache_key)

            return True

        except Exception as e:
            logger.error(f"Error writing coil: {e}")
            self.stats["errors"] += 1
            return False

    def write_register(
        self,
        slave_id: int,
        address: int,
        value: int
    ) -> bool:
        """
        Write single register (function code 0x06)

        Args:
            slave_id: Modbus slave ID
            address: Register address
            value: Value to write (0-65535)

        Returns:
            Success status
        """
        if not self.connected:
            return False

        try:
            response = self.client.write_register(
                address=address,
                value=value,
                slave=slave_id
            )

            if response.isError():
                self.stats["errors"] += 1
                return False

            self.stats["write_operations"] += 1

            # Invalidate cache
            cache_key = f"holding_{slave_id}_{address}_1"
            self._invalidate_cache(cache_key)

            return True

        except Exception as e:
            logger.error(f"Error writing register: {e}")
            self.stats["errors"] += 1
            return False

    def write_coils(
        self,
        slave_id: int,
        address: int,
        values: List[bool]
    ) -> bool:
        """
        Write multiple coils (function code 0x0F)

        Args:
            slave_id: Modbus slave ID
            address: Starting address
            values: List of boolean values

        Returns:
            Success status
        """
        if not self.connected:
            return False

        try:
            response = self.client.write_coils(
                address=address,
                values=values,
                slave=slave_id
            )

            if response.isError():
                self.stats["errors"] += 1
                return False

            self.stats["write_operations"] += 1

            # Invalidate cache
            cache_key = f"coil_{slave_id}_{address}_{len(values)}"
            self._invalidate_cache(cache_key)

            return True

        except Exception as e:
            logger.error(f"Error writing coils: {e}")
            self.stats["errors"] += 1
            return False

    def write_registers(
        self,
        slave_id: int,
        address: int,
        values: List[int]
    ) -> bool:
        """
        Write multiple registers (function code 0x10)

        Args:
            slave_id: Modbus slave ID
            address: Starting address
            values: List of register values

        Returns:
            Success status
        """
        if not self.connected:
            return False

        try:
            response = self.client.write_registers(
                address=address,
                values=values,
                slave=slave_id
            )

            if response.isError():
                self.stats["errors"] += 1
                return False

            self.stats["write_operations"] += 1

            # Invalidate cache
            cache_key = f"holding_{slave_id}_{address}_{len(values)}"
            self._invalidate_cache(cache_key)

            return True

        except Exception as e:
            logger.error(f"Error writing registers: {e}")
            self.stats["errors"] += 1
            return False

    # ========================================================================
    # High-Level Device Operations
    # ========================================================================

    def read_device_registers(
        self,
        slave_id: int,
        register_name: str
    ) -> Optional[Any]:
        """
        Read device register by name (using register map)

        Args:
            slave_id: Modbus slave ID
            register_name: Register name from device's register map

        Returns:
            Register value(s) or None
        """
        device = self.get_device(slave_id)
        if not device:
            logger.error(f"Device not found: slave_id={slave_id}")
            return None

        if register_name not in device.register_map:
            logger.error(f"Register not found: {register_name}")
            return None

        reg_info = device.register_map[register_name]
        address = reg_info["address"]
        reg_type = reg_info.get("type", RegisterType.HOLDING_REGISTER)
        count = reg_info.get("count", 1)

        # Read based on type
        if reg_type == RegisterType.COIL:
            return self.read_coils(slave_id, address, count)
        elif reg_type == RegisterType.DISCRETE_INPUT:
            return self.read_discrete_inputs(slave_id, address, count)
        elif reg_type == RegisterType.HOLDING_REGISTER:
            return self.read_holding_registers(slave_id, address, count)
        elif reg_type == RegisterType.INPUT_REGISTER:
            return self.read_input_registers(slave_id, address, count)
        else:
            logger.error(f"Unsupported register type: {reg_type}")
            return None

    # ========================================================================
    # Cache Management
    # ========================================================================

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if still valid"""
        with self.cache_lock:
            if key not in self.cache:
                return None

            cached = self.cache[key]
            age = (datetime.now() - cached["timestamp"]).total_seconds()

            if age > self.cache_ttl:
                # Expired
                del self.cache[key]
                return None

            return cached["value"]

    def _set_cached(self, key: str, value: Any):
        """Store value in cache"""
        with self.cache_lock:
            self.cache[key] = {
                "value": value,
                "timestamp": datetime.now()
            }

    def _invalidate_cache(self, key: str):
        """Invalidate cached value"""
        with self.cache_lock:
            if key in self.cache:
                del self.cache[key]

    def clear_cache(self):
        """Clear all cached data"""
        with self.cache_lock:
            self.cache.clear()
            logger.info("Cache cleared")

    # ========================================================================
    # Utilities
    # ========================================================================

    def get_stats(self) -> Dict:
        """Get Modbus statistics"""
        return {
            **self.stats,
            "status": self.status,
            "connected": self.connected,
            "devices": len(self.devices),
            "cache_size": len(self.cache)
        }

    def list_devices(self) -> List[Dict]:
        """List registered devices"""
        devices_list = []

        for slave_id, device in self.devices.items():
            devices_list.append({
                "device_id": device.device_id,
                "slave_id": device.slave_id,
                "read_count": device.read_count,
                "error_count": device.error_count,
                "last_read": device.last_read.isoformat() if device.last_read else None,
                "registers": list(device.register_map.keys())
            })

        return devices_list


# Global singleton
_modbus_service: Optional[ModbusService] = None


def get_modbus_service(**kwargs) -> ModbusService:
    """Get or create Modbus Service singleton"""
    global _modbus_service
    if _modbus_service is None:
        _modbus_service = ModbusService(**kwargs)
    return _modbus_service
