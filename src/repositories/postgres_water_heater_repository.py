"""
PostgreSQL implementation of the water heater repository.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
from asyncpg import Connection, Pool

from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterDiagnosticCode,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
    WaterHeaterType,
)
from src.repositories.water_heater_repository import WaterHeaterRepository

# Setup logging
logger = logging.getLogger(__name__)


class PostgresWaterHeaterRepository(WaterHeaterRepository):
    """PostgreSQL implementation of water heater repository."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "iotsphere",
        user: str = "iotsphere",
        password: str = "iotsphere",
    ):
        """Initialize with PostgreSQL connection parameters."""
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool: Optional[Pool] = None
        self._initialized = False

        # Log initialization
        logger.info(
            f"PostgreSQL repository created for {database} on {host}:{port} (async init pending)"
        )

    async def _initialize(self) -> None:
        """Initialize the repository asynchronously."""
        if self._initialized:
            return

        # Initialize connection pool
        await self._init_pool()

        # Ensure tables exist
        await self._ensure_tables()

        self._initialized = True
        logger.info(
            f"PostgreSQL repository fully initialized for {self.database} on {self.host}:{self.port}"
        )

    async def _init_pool(self) -> None:
        """Initialize the connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=5,
                max_size=20,
            )
            logger.info("PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"Error creating PostgreSQL connection pool: {e}")
            raise

    async def _ensure_tables(self) -> None:
        """Ensure all required tables exist."""
        if not self.pool:
            raise ValueError("Database pool is not initialized")

        async with self.pool.acquire() as conn:
            await self._create_tables(conn)

    async def _create_tables(self, conn: Connection) -> None:
        """Create necessary tables if they don't exist."""
        # Create water_heaters table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS water_heaters (
                id TEXT PRIMARY KEY,
                name TEXT,
                manufacturer TEXT,
                brand TEXT,
                model TEXT,
                type TEXT,
                size TEXT,
                location TEXT,
                status TEXT,
                installation_date TEXT,
                warranty_expiry TEXT,
                last_maintenance TEXT,
                last_seen TEXT,
                current_temperature DOUBLE PRECISION,
                target_temperature DOUBLE PRECISION,
                efficiency_rating DOUBLE PRECISION,
                mode TEXT,
                health_status TEXT,
                series TEXT,
                features TEXT,
                operation_modes TEXT,
                metadata TEXT
            )
        """
        )

        # Create water_heater_readings table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS water_heater_readings (
                id TEXT PRIMARY KEY,
                water_heater_id TEXT REFERENCES water_heaters(id),
                timestamp TEXT,
                temperature DOUBLE PRECISION,
                pressure DOUBLE PRECISION,
                flow_rate DOUBLE PRECISION,
                energy_usage DOUBLE PRECISION
            )
        """
        )

        # Create water_heater_diagnostic_codes table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS water_heater_diagnostic_codes (
                id TEXT PRIMARY KEY,
                water_heater_id TEXT REFERENCES water_heaters(id),
                code TEXT,
                description TEXT,
                severity TEXT,
                timestamp TEXT,
                resolved INTEGER,
                resolved_at TEXT
            )
        """
        )

        # Create water_heater_health_config table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS water_heater_health_config (
                id TEXT PRIMARY KEY,
                metric TEXT,
                threshold DOUBLE PRECISION,
                description TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """
        )

        # Create water_heater_alert_rules table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS water_heater_alert_rules (
                id TEXT PRIMARY KEY,
                name TEXT,
                condition TEXT,
                severity TEXT,
                message TEXT,
                enabled INTEGER,
                created_at TEXT,
                updated_at TEXT
            )
        """
        )

        logger.info("PostgreSQL tables created or verified")

    async def get_water_heaters(
        self, manufacturer: Optional[str] = None
    ) -> List[WaterHeater]:
        """
        Get all water heaters from the database.

        Args:
            manufacturer: Optional filter by manufacturer name

        Returns:
            List of water heaters, optionally filtered by manufacturer
        """
        # Initialize repository if needed
        if not self._initialized:
            await self._initialize()

        query = "SELECT * FROM water_heaters"
        params = []

        if manufacturer:
            query += " WHERE manufacturer = $1"
            params.append(manufacturer)

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                water_heaters = []

                # Convert each row with error handling
                for row in rows:
                    try:
                        heater = self._row_to_water_heater(dict(row))
                        water_heaters.append(heater)
                    except Exception as e:
                        # Log error but continue with other records
                        logger.error(f"Error converting row to water heater: {e}")
                        logger.error(f"Problematic row: {row}")

                # Log count
                logger.info(
                    f"Retrieved {len(water_heaters)} water heaters from PostgreSQL"
                    + (f" for manufacturer '{manufacturer}'" if manufacturer else "")
                )

                return water_heaters
        except Exception as e:
            logger.error(f"Error getting water heaters from PostgreSQL: {e}")
            return []

    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        """Get a specific water heater by ID from the database."""
        # Initialize repository if needed
        if not self._initialized:
            await self._initialize()

        async with self.pool.acquire() as conn:
            # Get water heater data
            row = await conn.fetchrow(
                "SELECT * FROM water_heaters WHERE id = $1", device_id
            )

            if not row:
                logger.info(f"Water heater with ID {device_id} not found in PostgreSQL")
                return None

            # Convert to WaterHeater object
            water_heater = self._row_to_water_heater(dict(row))
            logger.info(f"Retrieved water heater {device_id} from PostgreSQL")
            return water_heater

    async def create_water_heater(self, water_heater: WaterHeater) -> WaterHeater:
        """Create a new water heater in the database."""
        # Initialize repository if needed
        if not self._initialized:
            await self._initialize()

        # Generate ID if not provided
        if not water_heater.id:
            water_heater.id = str(uuid.uuid4())

        # Set timestamp if not set
        if not water_heater.last_seen:
            water_heater.last_seen = datetime.now().isoformat()

        async with self.pool.acquire() as conn:
            # Insert water heater
            metadata_json = (
                json.dumps(water_heater.metadata) if water_heater.metadata else "{}"
            )

            # Convert features and operation_modes to JSON strings
            features_json = (
                json.dumps(water_heater.features) if water_heater.features else "[]"
            )
            operation_modes_json = (
                json.dumps(water_heater.operation_modes)
                if water_heater.operation_modes
                else "[]"
            )

            await conn.execute(
                """
                INSERT INTO water_heaters (
                    id, name, manufacturer, brand, model, type, size, location, status,
                    installation_date, warranty_expiry, last_maintenance, last_seen,
                    current_temperature, target_temperature, efficiency_rating, mode,
                    health_status, series, features, operation_modes, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
                )
            """,
                water_heater.id,
                water_heater.name,
                water_heater.manufacturer,
                water_heater.brand,
                water_heater.model,
                water_heater.type.value if water_heater.type else None,
                water_heater.size,
                water_heater.location,
                water_heater.status.value if water_heater.status else None,
                water_heater.installation_date,
                water_heater.warranty_expiry,
                water_heater.last_maintenance,
                water_heater.last_seen,
                water_heater.current_temperature,
                water_heater.target_temperature,
                water_heater.efficiency_rating,
                water_heater.mode.value if water_heater.mode else None,
                water_heater.health_status,
                water_heater.series,
                features_json,
                operation_modes_json,
                metadata_json,
            )

            logger.info(f"Created water heater {water_heater.id} in PostgreSQL")
            return water_heater

    async def update_water_heater(
        self, device_id: str, updates: Dict[str, Any]
    ) -> Optional[WaterHeater]:
        """Update a water heater in the database with specified changes."""
        # Initialize repository if needed
        if not self._initialized:
            await self._initialize()

        async with self.pool.acquire() as conn:
            # Check if water heater exists
            existing = await conn.fetchrow(
                "SELECT * FROM water_heaters WHERE id = $1", device_id
            )
            if not existing:
                logger.warning(f"Water heater {device_id} not found for update")
                return None

            # Build update query
            update_fields = []
            update_values = []

            for i, (key, value) in enumerate(updates.items(), start=1):
                # Handle special cases for enum values
                if key == "mode" and value is not None:
                    if isinstance(value, WaterHeaterMode):
                        value = value.value
                    elif isinstance(value, str) and not value.startswith(
                        "WaterHeaterMode."
                    ):
                        try:
                            value = WaterHeaterMode(value).value
                        except ValueError:
                            logger.warning(f"Invalid mode value: {value}")

                if key == "status" and value is not None:
                    if isinstance(value, WaterHeaterStatus):
                        value = value.value
                    elif isinstance(value, str) and not value.startswith(
                        "WaterHeaterStatus."
                    ):
                        try:
                            value = WaterHeaterStatus(value).value
                        except ValueError:
                            logger.warning(f"Invalid status value: {value}")

                # Special handling for metadata
                if key == "metadata" and value is not None:
                    value = json.dumps(value)

                update_fields.append(f"{key} = ${i}")
                update_values.append(value)

            # Add updated timestamp
            update_fields.append(f"last_seen = ${len(update_values) + 1}")
            update_values.append(datetime.now().isoformat())

            # Execute update
            query = f"UPDATE water_heaters SET {', '.join(update_fields)} WHERE id = ${len(update_values) + 1}"
            update_values.append(device_id)

            await conn.execute(query, *update_values)

            # Return updated water heater
            updated_row = await conn.fetchrow(
                "SELECT * FROM water_heaters WHERE id = $1", device_id
            )
            water_heater = self._row_to_water_heater(dict(updated_row))

            logger.info(f"Updated water heater {device_id} in PostgreSQL")
            return water_heater

    async def add_reading(self, device_id: str, reading: WaterHeaterReading) -> None:
        """Add a new reading to a water heater in the database."""
        # Initialize repository if needed
        if not self._initialized:
            await self._initialize()

        # Generate ID if not provided
        if not reading.id:
            reading.id = str(uuid.uuid4())

        # Set timestamp if not set
        if not reading.timestamp:
            reading.timestamp = datetime.now().isoformat()

        async with self.pool.acquire() as conn:
            # Check if water heater exists
            exists = await conn.fetchval(
                "SELECT 1 FROM water_heaters WHERE id = $1", device_id
            )
            if not exists:
                logger.warning(f"Water heater {device_id} not found for adding reading")
                return

            # Insert reading
            await conn.execute(
                """
                INSERT INTO water_heater_readings (
                    id, water_heater_id, timestamp, temperature, pressure, flow_rate, energy_usage
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                reading.id,
                device_id,
                reading.timestamp,
                reading.temperature,
                reading.pressure,
                reading.flow_rate,
                reading.energy_usage,
            )

            logger.info(
                f"Added reading {reading.id} to water heater {device_id} in PostgreSQL"
            )

            # Update water heater last_seen and current_temperature
            await conn.execute(
                """
                UPDATE water_heaters
                SET last_seen = $1, current_temperature = $2
                WHERE id = $3
            """,
                reading.timestamp,
                reading.temperature,
                device_id,
            )

    async def get_readings(
        self, device_id: str, limit: int = 24
    ) -> List[WaterHeaterReading]:
        """Get recent readings for a water heater from the database."""
        # Initialize repository if needed
        if not self._initialized:
            await self._initialize()

        async with self.pool.acquire() as conn:
            # Check if water heater exists
            exists = await conn.fetchval(
                "SELECT 1 FROM water_heaters WHERE id = $1", device_id
            )
            if not exists:
                logger.warning(
                    f"Water heater {device_id} not found for retrieving readings"
                )
                return []

            # Get readings ordered by timestamp
            rows = await conn.fetch(
                """
                SELECT * FROM water_heater_readings
                WHERE water_heater_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """,
                device_id,
                limit,
            )

            readings = [self._row_to_reading(dict(row)) for row in rows]
            logger.info(
                f"Retrieved {len(readings)} readings for water heater {device_id} from PostgreSQL"
            )
            return readings

    async def remove_reading(self, device_id: str, reading_id: str) -> bool:
        """
        Remove a reading from a water heater.

        Args:
            device_id: ID of the water heater
            reading_id: ID of the reading to remove

        Returns:
            True if successful, False otherwise
        """
        # Initialize repository if needed
        if not self._initialized:
            await self._initialize()

        async with self.pool.acquire() as conn:
            # Check if water heater exists
            exists = await conn.fetchval(
                "SELECT 1 FROM water_heaters WHERE id = $1", device_id
            )
            if not exists:
                logger.warning(
                    f"Water heater {device_id} not found for removing reading"
                )
                return False

            # Delete the reading
            result = await conn.execute(
                "DELETE FROM water_heater_readings WHERE id = $1 AND water_heater_id = $2",
                reading_id,
                device_id,
            )

            # Check if any rows were affected
            if result and "DELETE" in result:
                count = int(result.split()[1])
                if count > 0:
                    logger.info(
                        f"Removed reading {reading_id} from water heater {device_id}"
                    )
                    return True
                else:
                    logger.warning(
                        f"No reading with ID {reading_id} found for water heater {device_id}"
                    )
                    return False
            else:
                logger.warning(
                    f"Unexpected result format from delete operation: {result}"
                )
                return False

    async def get_health_configuration(self) -> Dict[str, Dict[str, Any]]:
        """Get health configuration for water heaters."""
        # Initialize repository if needed
        if not self._initialized:
            await self._initialize()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM water_heater_health_config")

            # Convert to dictionary with metric as key
            config = {}
            for row in rows:
                row_dict = dict(row)
                metric = row_dict.pop("metric")
                config[metric] = row_dict

            logger.info(
                f"Retrieved health configuration with {len(config)} metrics from PostgreSQL"
            )
            return config

    async def set_health_configuration(self, config: Dict[str, Dict[str, Any]]) -> None:
        """Set health configuration for water heaters."""
        # Initialize repository if needed
        if not self._initialized:
            await self._initialize()

        async with self.pool.acquire() as conn:
            # Clear existing config
            await conn.execute("DELETE FROM water_heater_health_config")

            # Insert new config
            now = datetime.now().isoformat()
            for metric, values in config.items():
                # Generate ID if not provided
                config_id = values.get("id", str(uuid.uuid4()))
                threshold = values.get("threshold", 0.0)
                description = values.get("description", "")
                status = values.get("status", "active")
                created_at = values.get("created_at", now)
                updated_at = values.get("updated_at", now)

                await conn.execute(
                    """
                    INSERT INTO water_heater_health_config (
                        id, metric, threshold, description, status, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    config_id,
                    metric,
                    threshold,
                    description,
                    status,
                    created_at,
                    updated_at,
                )

            logger.info(
                f"Set health configuration with {len(config)} metrics in PostgreSQL"
            )

    async def get_alert_rules(self) -> List[Dict[str, Any]]:
        """Get alert rules for water heaters."""
        # Initialize repository if needed
        if not self._initialized:
            await self._initialize()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM water_heater_alert_rules")

            rules = [dict(row) for row in rows]
            logger.info(f"Retrieved {len(rules)} alert rules from PostgreSQL")
            return rules

    async def add_alert_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new alert rule."""
        # Initialize repository if needed
        if not self._initialized:
            await self._initialize()

        # Generate ID if not provided
        rule_id = rule.get("id", str(uuid.uuid4()))

        # Set timestamps if not set
        now = datetime.now().isoformat()
        created_at = rule.get("created_at", now)
        updated_at = rule.get("updated_at", now)

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO water_heater_alert_rules (
                    id, name, condition, severity, message, enabled, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                rule_id,
                rule.get("name", ""),
                rule.get("condition", ""),
                rule.get("severity", "info"),
                rule.get("message", ""),
                1 if rule.get("enabled", True) else 0,
                created_at,
                updated_at,
            )

            logger.info(f"Added alert rule {rule_id} in PostgreSQL")

            # Return rule with ID
            rule["id"] = rule_id
            return rule

    async def update_alert_rule(
        self, rule_id: str, rule: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an existing alert rule."""
        # Initialize repository if needed
        if not self._initialized:
            await self._initialize()

        async with self.pool.acquire() as conn:
            # Check if rule exists
            exists = await conn.fetchval(
                "SELECT 1 FROM water_heater_alert_rules WHERE id = $1", rule_id
            )
            if not exists:
                logger.warning(f"Alert rule {rule_id} not found for update")
                return None

            # Update rule
            now = datetime.now().isoformat()
            await conn.execute(
                """
                UPDATE water_heater_alert_rules SET
                    name = $1, condition = $2, severity = $3, message = $4,
                    enabled = $5, updated_at = $6
                WHERE id = $7
            """,
                rule.get("name"),
                rule.get("condition"),
                rule.get("severity"),
                rule.get("message"),
                1 if rule.get("enabled", True) else 0,
                now,
                rule_id,
            )

            logger.info(f"Updated alert rule {rule_id} in PostgreSQL")

            # Return updated rule
            row = await conn.fetchrow(
                "SELECT * FROM water_heater_alert_rules WHERE id = $1", rule_id
            )
            return dict(row)

    async def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        # Initialize repository if needed
        if not self._initialized:
            await self._initialize()

        async with self.pool.acquire() as conn:
            # Check if rule exists
            exists = await conn.fetchval(
                "SELECT 1 FROM water_heater_alert_rules WHERE id = $1", rule_id
            )
            if not exists:
                logger.warning(f"Alert rule {rule_id} not found for deletion")
                return False

            # Delete rule
            await conn.execute(
                "DELETE FROM water_heater_alert_rules WHERE id = $1", rule_id
            )
            logger.info(f"Deleted alert rule {rule_id} from PostgreSQL")
            return True

    def _row_to_water_heater(self, row: Dict[str, Any]) -> WaterHeater:
        """Convert a database row to a WaterHeater object."""
        # Parse metadata from JSON
        metadata = {}
        if row.get("metadata"):
            try:
                metadata = json.loads(row["metadata"])
            except json.JSONDecodeError:
                logger.warning(
                    f"Failed to parse metadata for water heater {row.get('id')}"
                )

        # Map Water Heater Type to DeviceType enum
        type_value = row.get("type")
        device_type = DeviceType.WATER_HEATER  # Default to WATER_HEATER type

        # Map status values to DeviceStatus enum
        status_value = row.get("status")
        if status_value:
            # Handle direct DeviceStatus values first
            try:
                # Try to directly parse as DeviceStatus enum
                device_status = DeviceStatus(status_value)
            except ValueError:
                # If that fails, map from WaterHeaterStatus to DeviceStatus
                status_mapping = {
                    # WaterHeaterStatus enum values
                    "HEATING": DeviceStatus.ONLINE,
                    "IDLE": DeviceStatus.ONLINE,
                    "OFF": DeviceStatus.OFFLINE,
                    "MAINTENANCE": DeviceStatus.MAINTENANCE,
                    "ERROR": DeviceStatus.ERROR,
                    # Raw string values
                    "ONLINE": DeviceStatus.ONLINE,
                    "OFFLINE": DeviceStatus.OFFLINE,
                }
                # Get mapped status or default to ONLINE
                device_status = status_mapping.get(status_value, DeviceStatus.ONLINE)
                logger.info(f"Mapped status value '{status_value}' to {device_status}")
        else:
            device_status = DeviceStatus.ONLINE  # Default status

        # Parse water heater mode
        try:
            mode = WaterHeaterMode(row.get("mode")) if row.get("mode") else None
        except ValueError:
            logger.warning(f"Invalid mode value: {row.get('mode')}")
            mode = None

        # Parse water heater type from the 'type' column in database
        # For Rheem water heaters, the type column contains the actual type (Tank, Tankless, Hybrid)
        # For other water heaters, we need to provide a default to satisfy model validation

        # Default to Tank as a fallback value (required by model validation)
        heater_type = WaterHeaterType.TANK

        # The database column is named 'type'
        if type_value:
            # If the type is one of our known Rheem types, use it
            if type_value in [t.value for t in WaterHeaterType]:
                try:
                    heater_type = WaterHeaterType(type_value)
                    logger.debug(
                        f"Mapped database type '{type_value}' to WaterHeaterType '{heater_type}'"
                    )
                except ValueError:
                    logger.warning(
                        f"Unknown water heater type '{type_value}', using default {heater_type}"
                    )
            # Skip DeviceType.WATER_HEATER as that's not a valid heater_type
            elif type_value in ["WATER_HEATER", DeviceType.WATER_HEATER.value]:
                logger.debug(
                    f"Found device type '{type_value}', using default heater_type: {heater_type}"
                )

        # Parse features JSON
        features = []
        features_str = row.get("features")
        if features_str:
            try:
                features = json.loads(features_str)
            except json.JSONDecodeError:
                logger.warning(f"Invalid features JSON: {features_str}")
                # If can't parse, keep as string to avoid validation errors
                features = features_str

        # Parse operation_modes JSON
        operation_modes = []
        operation_modes_str = row.get("operation_modes")
        if operation_modes_str:
            try:
                operation_modes = json.loads(operation_modes_str)
            except json.JSONDecodeError:
                logger.warning(f"Invalid operation_modes JSON: {operation_modes_str}")
                # If can't parse, keep as string to avoid validation errors
                operation_modes = operation_modes_str

        # Parse metadata JSON
        metadata = None
        metadata_str = row.get("metadata")
        if metadata_str:
            try:
                metadata = json.loads(metadata_str)
            except json.JSONDecodeError:
                logger.warning(f"Invalid metadata JSON: {metadata_str}")
                # If can't parse, keep as None to avoid validation errors

        # Create WaterHeater object
        # Mapping database fields to model fields
        # In the database:
        # - 'id' is the primary key and device identifier
        # - 'type' contains water heater type (Tank, Tankless, Hybrid)
        water_heater = WaterHeater(
            id=row.get("id"),  # Use 'id' as both the primary key and device_id
            device_id=row.get("id"),  # Map 'id' to device_id as well (they're the same)
            name=row.get("name"),
            manufacturer=row.get("manufacturer"),
            brand=row.get("brand"),
            model=row.get("model"),
            type=device_type,  # This is DeviceType.WATER_HEATER
            heater_type=heater_type,  # Map database 'type' column to model 'heater_type' field
            size=row.get("size"),
            location=row.get("location"),
            status=device_status,  # Use mapped device status
            installation_date=row.get("installation_date"),
            warranty_expiry=row.get("warranty_expiry"),
            last_maintenance=row.get("last_maintenance"),
            last_seen=row.get("last_seen"),
            current_temperature=row.get("current_temperature"),
            target_temperature=row.get("target_temperature"),
            efficiency_rating=row.get("efficiency_rating"),
            mode=mode,
            health_status=row.get("health_status"),
            series=row.get("series"),
            features=features,
            operation_modes=operation_modes,
            metadata=metadata,
        )

        return water_heater

    def _row_to_reading(self, row: Dict[str, Any]) -> WaterHeaterReading:
        """Convert a database row to a WaterHeaterReading object."""
        return WaterHeaterReading(
            id=row.get("id"),
            timestamp=row.get("timestamp"),
            temperature=row.get("temperature"),
            pressure=row.get("pressure"),
            flow_rate=row.get("flow_rate"),
            energy_usage=row.get("energy_usage"),
        )

    def _row_to_diagnostic_code(self, row: Dict[str, Any]) -> WaterHeaterDiagnosticCode:
        """Convert a database row to a WaterHeaterDiagnosticCode object."""
        return WaterHeaterDiagnosticCode(
            id=row.get("id"),
            code=row.get("code"),
            description=row.get("description"),
            severity=row.get("severity"),
            timestamp=row.get("timestamp"),
            resolved=bool(row.get("resolved")),
            resolved_at=row.get("resolved_at"),
        )
