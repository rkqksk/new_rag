"""
MES Connectors - v7.4.0
Real MES system connectors (SAP, Oracle, Siemens, etc.)
"""

from typing import List, Dict, Optional, Any, Union
from enum import Enum
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import asyncio

# Database connectors
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

try:
    import cx_Oracle
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False

try:
    import pymssql
    MSSQL_AVAILABLE = True
except ImportError:
    MSSQL_AVAILABLE = False

# API clients
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from pyrfc import Connection as SAPConnection
    SAP_RFC_AVAILABLE = True
except ImportError:
    SAP_RFC_AVAILABLE = False


class MESConnectionError(Exception):
    """MES connection error"""
    pass


class MESQueryError(Exception):
    """MES query error"""
    pass


class BaseMESConnector(ABC):
    """
    Base MES connector

    All MES connectors inherit from this base class
    """

    def __init__(
        self,
        host: str,
        port: int,
        database: Optional[str],
        username: str,
        password: str,
        timeout: int = 30
    ):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.timeout = timeout
        self.connection = None

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to MES"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from MES"""
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test MES connection"""
        pass

    @abstractmethod
    async def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query"""
        pass

    @abstractmethod
    async def get_materials(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get materials from MES"""
        pass

    @abstractmethod
    async def get_work_orders(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get work orders from MES"""
        pass


class SAPMESConnector(BaseMESConnector):
    """
    SAP MES Connector

    Connects to SAP ERP/MES systems via:
    - RFC (Remote Function Call) for real-time data
    - Database queries (MSSQL/HANA) for batch data
    """

    def __init__(
        self,
        host: str,
        port: int,
        client: str,  # SAP client (e.g., "100")
        sysnr: str,   # SAP system number (e.g., "00")
        username: str,
        password: str,
        use_rfc: bool = True,
        database: Optional[str] = None,
        timeout: int = 30
    ):
        super().__init__(host, port, database, username, password, timeout)
        self.client = client
        self.sysnr = sysnr
        self.use_rfc = use_rfc
        self.rfc_connection = None
        self.db_connection = None

    async def connect(self) -> bool:
        """Connect to SAP"""
        try:
            if self.use_rfc:
                if not SAP_RFC_AVAILABLE:
                    raise ImportError("pyrfc not installed. Run: pip install pyrfc")

                # Connect via RFC
                loop = asyncio.get_event_loop()
                self.rfc_connection = await loop.run_in_executor(
                    None,
                    lambda: SAPConnection(
                        ashost=self.host,
                        sysnr=self.sysnr,
                        client=self.client,
                        user=self.username,
                        passwd=self.password
                    )
                )
            else:
                # Connect via database
                if not PYODBC_AVAILABLE:
                    raise ImportError("pyodbc not installed. Run: pip install pyodbc")

                connection_string = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={self.host},{self.port};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password}"
                )
                loop = asyncio.get_event_loop()
                self.db_connection = await loop.run_in_executor(
                    None,
                    lambda: pyodbc.connect(connection_string, timeout=self.timeout)
                )

            return True

        except Exception as e:
            raise MESConnectionError(f"SAP connection failed: {str(e)}")

    async def disconnect(self) -> bool:
        """Disconnect from SAP"""
        try:
            if self.rfc_connection:
                self.rfc_connection.close()
            if self.db_connection:
                self.db_connection.close()
            return True
        except Exception as e:
            return False

    async def test_connection(self) -> Dict[str, Any]:
        """Test SAP connection"""
        start_time = datetime.now()

        try:
            if self.use_rfc and self.rfc_connection:
                # Test RFC connection
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.rfc_connection.call("RFC_PING")
                )
                success = True
            else:
                # Test database connection
                loop = asyncio.get_event_loop()
                cursor = await loop.run_in_executor(None, self.db_connection.cursor)
                await loop.run_in_executor(None, cursor.execute, "SELECT 1")
                await loop.run_in_executor(None, cursor.close)
                success = True

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            return {
                "success": success,
                "message": "SAP connection successful",
                "response_time_ms": response_time,
                "connection_type": "RFC" if self.use_rfc else "Database",
                "tested_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tested_at": datetime.now().isoformat()
            }

    async def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute SQL query on SAP database"""
        if not self.db_connection:
            raise MESConnectionError("Database connection not established")

        try:
            loop = asyncio.get_event_loop()
            cursor = await loop.run_in_executor(None, self.db_connection.cursor)

            if params:
                await loop.run_in_executor(None, cursor.execute, query, params)
            else:
                await loop.run_in_executor(None, cursor.execute, query)

            columns = [column[0] for column in cursor.description]
            rows = await loop.run_in_executor(None, cursor.fetchall)

            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))

            await loop.run_in_executor(None, cursor.close)

            return results

        except Exception as e:
            raise MESQueryError(f"SAP query failed: {str(e)}")

    async def get_materials(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get materials from SAP MARA table"""
        query = """
        SELECT
            M.MATNR as material_code,
            T.MAKTX as material_name,
            M.MTART as material_type,
            M.MEINS as uom,
            M.BRGEW as weight,
            M.GEWEI as weight_unit,
            M.ERSDA as created_date,
            M.LAEDA as changed_date
        FROM MARA M
        LEFT JOIN MAKT T ON M.MATNR = T.MATNR AND T.SPRAS = 'E'
        WHERE 1=1
        """

        # Add filters
        if filters:
            if "material_type" in filters:
                query += f" AND M.MTART = '{filters['material_type']}'"
            if "date_from" in filters:
                query += f" AND M.ERSDA >= '{filters['date_from']}'"

        query += " ORDER BY M.MATNR"

        return await self.query(query)

    async def get_work_orders(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get work orders from SAP (AFKO table)"""
        query = """
        SELECT
            A.AUFNR as order_number,
            A.PLNBEZ as material_number,
            A.GAMNG as planned_quantity,
            A.GLTRP as basic_finish_date,
            A.GSTRP as basic_start_date,
            A.AUFPL as routing_number
        FROM AFKO A
        WHERE 1=1
        """

        if filters:
            if "status" in filters:
                query += f" AND A.STATUS = '{filters['status']}'"
            if "date_from" in filters:
                query += f" AND A.GSTRP >= '{filters['date_from']}'"

        query += " ORDER BY A.AUFNR DESC"

        return await self.query(query)


class OracleMESConnector(BaseMESConnector):
    """
    Oracle MES Connector

    Connects to Oracle E-Business Suite / Manufacturing Cloud
    """

    def __init__(
        self,
        host: str,
        port: int,
        service_name: str,
        username: str,
        password: str,
        timeout: int = 30
    ):
        super().__init__(host, port, service_name, username, password, timeout)
        self.service_name = service_name

    async def connect(self) -> bool:
        """Connect to Oracle"""
        try:
            if not ORACLE_AVAILABLE:
                raise ImportError("cx_Oracle not installed. Run: pip install cx_Oracle")

            dsn = cx_Oracle.makedsn(self.host, self.port, service_name=self.service_name)
            loop = asyncio.get_event_loop()
            self.connection = await loop.run_in_executor(
                None,
                lambda: cx_Oracle.connect(
                    user=self.username,
                    password=self.password,
                    dsn=dsn,
                    encoding="UTF-8"
                )
            )
            return True

        except Exception as e:
            raise MESConnectionError(f"Oracle connection failed: {str(e)}")

    async def disconnect(self) -> bool:
        """Disconnect from Oracle"""
        try:
            if self.connection:
                self.connection.close()
            return True
        except Exception:
            return False

    async def test_connection(self) -> Dict[str, Any]:
        """Test Oracle connection"""
        start_time = datetime.now()

        try:
            loop = asyncio.get_event_loop()
            cursor = await loop.run_in_executor(None, self.connection.cursor)
            await loop.run_in_executor(None, cursor.execute, "SELECT 1 FROM DUAL")
            await loop.run_in_executor(None, cursor.close)

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            return {
                "success": True,
                "message": "Oracle connection successful",
                "response_time_ms": response_time,
                "tested_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tested_at": datetime.now().isoformat()
            }

    async def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute SQL query on Oracle"""
        if not self.connection:
            raise MESConnectionError("Oracle connection not established")

        try:
            loop = asyncio.get_event_loop()
            cursor = await loop.run_in_executor(None, self.connection.cursor)

            if params:
                await loop.run_in_executor(None, cursor.execute, query, params)
            else:
                await loop.run_in_executor(None, cursor.execute, query)

            columns = [col[0] for col in cursor.description]
            rows = await loop.run_in_executor(None, cursor.fetchall)

            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))

            await loop.run_in_executor(None, cursor.close)

            return results

        except Exception as e:
            raise MESQueryError(f"Oracle query failed: {str(e)}")

    async def get_materials(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get materials from Oracle (MTL_SYSTEM_ITEMS_B)"""
        query = """
        SELECT
            MSI.SEGMENT1 as material_code,
            MSI.DESCRIPTION as material_name,
            MSI.ITEM_TYPE as material_type,
            MSI.PRIMARY_UOM_CODE as uom,
            MSI.UNIT_WEIGHT as weight,
            MSI.WEIGHT_UOM_CODE as weight_unit,
            MSI.CREATION_DATE as created_date,
            MSI.LAST_UPDATE_DATE as changed_date
        FROM MTL_SYSTEM_ITEMS_B MSI
        WHERE MSI.ORGANIZATION_ID = :org_id
        """

        if filters:
            if "material_type" in filters:
                query += f" AND MSI.ITEM_TYPE = '{filters['material_type']}'"
            if "date_from" in filters:
                query += " AND MSI.CREATION_DATE >= :date_from"

        query += " ORDER BY MSI.SEGMENT1"

        params = {"org_id": filters.get("organization_id", 1) if filters else 1}
        if filters and "date_from" in filters:
            params["date_from"] = filters["date_from"]

        return await self.query(query, params)

    async def get_work_orders(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get work orders from Oracle (WIP_DISCRETE_JOBS)"""
        query = """
        SELECT
            WDJ.WIP_ENTITY_NAME as order_number,
            WDJ.PRIMARY_ITEM_ID as material_id,
            MSI.SEGMENT1 as material_code,
            WDJ.START_QUANTITY as planned_quantity,
            WDJ.SCHEDULED_START_DATE as start_date,
            WDJ.SCHEDULED_COMPLETION_DATE as completion_date,
            WDJ.STATUS_TYPE as status
        FROM WIP_DISCRETE_JOBS WDJ
        LEFT JOIN MTL_SYSTEM_ITEMS_B MSI
            ON WDJ.PRIMARY_ITEM_ID = MSI.INVENTORY_ITEM_ID
            AND WDJ.ORGANIZATION_ID = MSI.ORGANIZATION_ID
        WHERE WDJ.ORGANIZATION_ID = :org_id
        """

        if filters:
            if "status" in filters:
                query += f" AND WDJ.STATUS_TYPE = {filters['status']}"
            if "date_from" in filters:
                query += " AND WDJ.SCHEDULED_START_DATE >= :date_from"

        query += " ORDER BY WDJ.SCHEDULED_START_DATE DESC"

        params = {"org_id": filters.get("organization_id", 1) if filters else 1}
        if filters and "date_from" in filters:
            params["date_from"] = filters["date_from"]

        return await self.query(query, params)


class SiemensMESConnector(BaseMESConnector):
    """
    Siemens Opcenter MES Connector

    Connects to Siemens Opcenter via REST API
    """

    def __init__(
        self,
        host: str,
        port: int,
        api_base_url: str,
        api_key: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
        timeout: int = 30
    ):
        super().__init__(host, port, None, username, password, timeout)
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.client = None
        self.auth_token = None

    async def connect(self) -> bool:
        """Connect to Siemens Opcenter"""
        try:
            if not HTTPX_AVAILABLE:
                raise ImportError("httpx not installed. Run: pip install httpx")

            self.client = httpx.AsyncClient(
                base_url=self.api_base_url,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            # Authenticate
            auth_response = await self.client.post(
                "/api/auth/login",
                json={
                    "username": self.username,
                    "password": self.password
                },
                headers={"X-API-Key": self.api_key}
            )
            auth_response.raise_for_status()

            self.auth_token = auth_response.json().get("token")

            return True

        except Exception as e:
            raise MESConnectionError(f"Siemens Opcenter connection failed: {str(e)}")

    async def disconnect(self) -> bool:
        """Disconnect from Siemens Opcenter"""
        try:
            if self.client:
                await self.client.aclose()
            return True
        except Exception:
            return False

    async def test_connection(self) -> Dict[str, Any]:
        """Test Siemens Opcenter connection"""
        start_time = datetime.now()

        try:
            response = await self.client.get(
                "/api/health",
                headers=self._get_headers()
            )
            response.raise_for_status()

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            return {
                "success": True,
                "message": "Siemens Opcenter connection successful",
                "response_time_ms": response_time,
                "tested_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tested_at": datetime.now().isoformat()
            }

    async def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute OData query"""
        # Siemens Opcenter uses OData queries
        # This is a simplified implementation
        raise NotImplementedError("Use specific methods like get_materials() instead")

    async def get_materials(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get materials from Siemens Opcenter"""
        endpoint = "/api/odata/Materials"

        # Build OData filter
        odata_filter = []
        if filters:
            if "material_type" in filters:
                odata_filter.append(f"MaterialType eq '{filters['material_type']}'")
            if "date_from" in filters:
                odata_filter.append(f"CreatedDate ge {filters['date_from']}")

        params = {}
        if odata_filter:
            params["$filter"] = " and ".join(odata_filter)

        response = await self.client.get(
            endpoint,
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()

        data = response.json()
        return data.get("value", [])

    async def get_work_orders(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get work orders from Siemens Opcenter"""
        endpoint = "/api/odata/ProductionOrders"

        odata_filter = []
        if filters:
            if "status" in filters:
                odata_filter.append(f"Status eq '{filters['status']}'")
            if "date_from" in filters:
                odata_filter.append(f"ScheduledStartDate ge {filters['date_from']}")

        params = {}
        if odata_filter:
            params["$filter"] = " and ".join(odata_filter)
        params["$expand"] = "Material"  # Include material details

        response = await self.client.get(
            endpoint,
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()

        data = response.json()
        return data.get("value", [])

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }


# Connector factory
def create_mes_connector(
    mes_system: str,
    **kwargs
) -> BaseMESConnector:
    """
    Factory function to create MES connector

    Args:
        mes_system: MES system type (sap_mes, oracle_mes, siemens_opcenter)
        **kwargs: Connection parameters

    Returns:
        MES connector instance
    """
    connectors = {
        "sap_mes": SAPMESConnector,
        "oracle_mes": OracleMESConnector,
        "siemens_opcenter": SiemensMESConnector
    }

    if mes_system not in connectors:
        raise ValueError(f"Unsupported MES system: {mes_system}")

    return connectors[mes_system](**kwargs)
