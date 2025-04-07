"""
Configurable service for water heater devices.
"""
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from src.config import config
from src.models.device import DeviceStatus
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterDiagnosticCode,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
)
from src.repositories.water_heater_repository import (
    MockWaterHeaterRepository,
    SQLiteWaterHeaterRepository,
    WaterHeaterRepository,
)

# Import generic manufacturer-agnostic dummy data
from src.utils.dummy_data import dummy_data

# Setup logging
logger = logging.getLogger(__name__)

# Import PostgreSQL repository if available
try:
    # Import PostgreSQL repository from the correct module
    from src.repositories.postgres_water_heater_repository import (
        PostgresWaterHeaterRepository,
    )

    HAS_POSTGRES = True
except ImportError as e:
    HAS_POSTGRES = False
    logger.warning(
        f"PostgreSQL repository not available: {e}. Install required dependencies for production use."
    )


class ConfigurableWaterHeaterService:
    """Service for water heater operations with configurable data source."""

    # Class variable to track data source for UI indicator
    is_using_mock_data = False
    data_source_reason = ""

    def __init__(
        self, repository: Optional[WaterHeaterRepository] = None, message_bus=None
    ):
        """
        Initialize the service with a repository.

        Args:
            repository: Water heater repository implementation.
                        If None, uses configuration to determine repository.
            message_bus: Optional message bus for publishing telemetry updates

        Raises:
            Exception: If database connection fails and fallback is disabled.
        """
        # Reset class tracking variables
        ConfigurableWaterHeaterService.is_using_mock_data = False
        ConfigurableWaterHeaterService.data_source_reason = ""

        # Store message bus for telemetry publishing
        self.message_bus = message_bus
        if self.message_bus:
            logger.info("Using message bus for real-time telemetry updates")
        else:
            logger.info("No message bus provided, real-time telemetry updates disabled")

        # Log environment info and database configuration
        env = os.environ.get("IOTSPHERE_ENV", "development")
        logger.info(f"Environment: {env}")

        # Load database settings
        from src.db.config import db_settings

        logger.info(
            f"Database settings: type={db_settings.DB_TYPE}, host={db_settings.DB_HOST}, name={db_settings.DB_NAME}"
        )

        if repository:
            logger.info(f"Using provided repository: {type(repository).__name__}")
            ConfigurableWaterHeaterService.is_using_mock_data = isinstance(
                repository, MockWaterHeaterRepository
            )
            ConfigurableWaterHeaterService.data_source_reason = (
                "Explicitly provided repository"
            )
            self.repository = repository
        else:
            # Import database settings
            from src.db.config import db_settings

            # Get current environment
            env = os.environ.get("IOTSPHERE_ENV", "development")

            # Check for backward compatibility with USE_MOCK_DATA environment variable
            use_mock_data_env = os.environ.get("USE_MOCK_DATA", "").lower() in [
                "true",
                "1",
                "yes",
            ]

            # Legacy config settings for backward compatibility
            use_mock_data_config = config.get(
                "services.water_heater.use_mock_data", False
            )

            # Use db_settings for database configuration
            db_type = db_settings.DB_TYPE
            fallback_enabled = db_settings.FALLBACK_TO_MOCK

            # Use mock data if explicitly configured or set by environment variable
            if use_mock_data_env or use_mock_data_config:
                logger.warning(
                    f"Using mock data repository for water heaters because: \n"
                    f"  - USE_MOCK_DATA env var: {use_mock_data_env} \n"
                    f"  - use_mock_data config: {use_mock_data_config}"
                )
                ConfigurableWaterHeaterService.is_using_mock_data = True
                ConfigurableWaterHeaterService.data_source_reason = (
                    "Explicitly configured to use mock data"
                )
                self.repository = MockWaterHeaterRepository()
            else:
                # Try to connect to the configured database
                try:
                    # Use PostgreSQL as our primary database type
                    if db_type == "postgres" and HAS_POSTGRES:
                        # Get PostgreSQL connection parameters from database settings
                        host = db_settings.DB_HOST
                        port = db_settings.DB_PORT
                        database = db_settings.DB_NAME
                        user = db_settings.DB_USER
                        password = db_settings.DB_PASSWORD

                        logger.info(
                            f"Using PostgreSQL repository for water heaters ({env} environment)\n"
                            f"  Host: {host}:{port}\n"
                            f"  Database: {database}\n"
                            f"  User: {user}"
                        )

                        # Attempt PostgreSQL connection
                        try:
                            self.repository = PostgresWaterHeaterRepository(
                                host=host,
                                port=port,
                                database=database,
                                user=user,
                                password=password,
                            )
                            ConfigurableWaterHeaterService.is_using_mock_data = False
                            ConfigurableWaterHeaterService.data_source_reason = (
                                f"Connected to PostgreSQL database ({env} environment)"
                            )
                            logger.info("Successfully connected to PostgreSQL database")
                        except Exception as pg_error:
                            logger.error(f"PostgreSQL connection error: {pg_error}")
                            logger.error(
                                "Check that PostgreSQL is installed and running"
                            )
                            logger.error(
                                "Make sure the database and user exist with correct permissions"
                            )
                            raise  # Re-raise for outer exception handler
                    elif db_type == "memory":
                        # In-memory SQLite for testing
                        logger.info("Using in-memory SQLite for testing environment")
                        self.repository = SQLiteWaterHeaterRepository(in_memory=True)
                        ConfigurableWaterHeaterService.is_using_mock_data = False
                        ConfigurableWaterHeaterService.data_source_reason = (
                            "Using in-memory SQLite database for testing"
                        )

                    elif db_type == "sqlite":
                        # Default to SQLite as fallback or if explicitly configured
                        logger.info("Using SQLite repository for water heaters")
                        # Log database check
                        try:
                            import sqlite3

                            from src.db.real_database import get_database_path

                            db_path = get_database_path()
                            logger.info(f"SQLite database path: {db_path}")

                            # Check if database file exists
                            if not os.path.exists(db_path):
                                logger.error(f"Database file does not exist: {db_path}")

                            # Try to connect and check tables
                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            cursor.execute(
                                "SELECT name FROM sqlite_master WHERE type='table'"
                            )
                            tables = cursor.fetchall()
                            logger.info(
                                f"Found {len(tables)} tables in SQLite database"
                            )

                            # Check water_heaters table specifically
                            cursor.execute("SELECT COUNT(*) FROM water_heaters")
                            count = cursor.fetchone()[0]
                            logger.info(f"Found {count} records in water_heaters table")

                            conn.close()
                        except Exception as db_check_error:
                            logger.error(
                                f"Error checking SQLite database: {db_check_error}"
                            )

                        # Create repository
                        self.repository = SQLiteWaterHeaterRepository()
                        ConfigurableWaterHeaterService.is_using_mock_data = False
                        ConfigurableWaterHeaterService.data_source_reason = (
                            "Using SQLite database"
                        )

                    else:
                        # Unsupported database type
                        logger.error(f"Unsupported database type: {db_type}")
                        raise ValueError(f"Unsupported database type: {db_type}")

                except Exception as e:
                    # If database connection fails, check if fallback is enabled
                    logger.error(f"Database connection error: {e}")
                    logger.error(f"Exception type: {type(e).__name__}")
                    import traceback

                    logger.error(f"Traceback: {traceback.format_exc()}")

                    # Check if DATABASE_FALLBACK_ENABLED is explicitly set to False
                    explicit_fallback_disabled = os.environ.get(
                        "DATABASE_FALLBACK_ENABLED", ""
                    ).lower() in ["false", "0", "no"]

                    if fallback_enabled and not explicit_fallback_disabled:
                        logger.warning(
                            f"Database connection failed. Falling back to mock data.\n"
                            f"  - Error: {e}\n"
                            f"  - Fallback enabled in config: {fallback_enabled}\n"
                            f"  - DATABASE_FALLBACK_ENABLED env var: {os.environ.get('DATABASE_FALLBACK_ENABLED', 'Not set')}"
                        )
                        ConfigurableWaterHeaterService.is_using_mock_data = True
                        ConfigurableWaterHeaterService.data_source_reason = (
                            f"Database connection failed: {str(e)[:100]}"
                        )
                        self.repository = MockWaterHeaterRepository()
                    else:
                        logger.error(
                            f"Database connection failed and fallback is disabled:\n"
                            f"  - Error: {e}\n"
                            f"  - Fallback enabled in config: {fallback_enabled}\n"
                            f"  - DATABASE_FALLBACK_ENABLED env var: {os.environ.get('DATABASE_FALLBACK_ENABLED', 'Not set')}"
                        )
                        # Still track this in case error is caught higher up
                        ConfigurableWaterHeaterService.is_using_mock_data = True
                        ConfigurableWaterHeaterService.data_source_reason = (
                            f"Database error with fallback disabled: {str(e)[:100]}"
                        )
                        raise

    async def get_water_heaters(
        self, manufacturer: Optional[str] = None
    ) -> List[WaterHeater]:
        """Get all water heaters, optionally filtered by manufacturer.

        Args:
            manufacturer: Optional filter by manufacturer name (e.g., 'Rheem', 'AquaTherm')

        Returns:
            Tuple (List[WaterHeater], bool, str) containing:
            - List of water heaters, filtered if manufacturer is specified
            - Boolean indicating if data is from database (True) or not (False)
            - Error message if any, otherwise empty string
        """
        try:
            result = await self.repository.get_water_heaters(manufacturer=manufacturer)
            # Log data source information with result count
            logger.info(
                f"get_water_heaters returned {len(result)} items from "
                f"{'mock data' if ConfigurableWaterHeaterService.is_using_mock_data else 'database'}"
            )
            # Return tuple containing results, data source indicator, and empty error message
            return (result, not ConfigurableWaterHeaterService.is_using_mock_data, "")
        except Exception as e:
            error_msg = f"Database error: {str(e)}"
            logger.error(f"Error in get_water_heaters: {error_msg}")
            # In case of error, return empty list, database indicator false, and error message
            return ([], False, error_msg)

    @classmethod
    def get_data_source_info(cls) -> Dict[str, Any]:
        """Get information about the current data source.

        Returns:
            Dictionary with data source information including whether using mock data,
            the reason for the current data source, and a timestamp.
        """
        return {
            "is_using_mock_data": cls.is_using_mock_data,
            "data_source_reason": cls.data_source_reason,
            "timestamp": datetime.now().isoformat(),
        }

    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        """Get a specific water heater by ID.

        Returns:
            Tuple (water_heater, is_from_db) where:
              - water_heater is the water heater object or None if not found
              - is_from_db is a boolean indicating if data came from database (True) or mock data (False)
        """
        try:
            result = await self.repository.get_water_heater(device_id)
            # Log data source information
            if result:
                logger.info(
                    f"get_water_heater for {device_id} returned data from "
                    f"{'mock data' if ConfigurableWaterHeaterService.is_using_mock_data else 'database'}"
                )

                # Publish telemetry event to message bus if available
                if self.message_bus:
                    telemetry_data = {
                        "device_id": device_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": {
                            "current_temperature": result.current_temperature,
                            "target_temperature": result.target_temperature,
                            "mode": result.mode.value if result.mode else None,
                            "heater_status": result.heater_status.value
                            if result.heater_status
                            else None,
                            "status": result.status.value if result.status else None,
                        },
                        "simulated": ConfigurableWaterHeaterService.is_using_mock_data,
                    }
                    self.message_bus.publish("device.telemetry", telemetry_data)
                    logger.info(
                        f"Published telemetry for device {device_id} to message bus"
                    )
            else:
                logger.warning(f"get_water_heater for {device_id} found no device")

            # Return tuple containing results and data source indicator
            return (result, not ConfigurableWaterHeaterService.is_using_mock_data)
        except Exception as e:
            logger.error(f"Error in get_water_heater for {device_id}: {e}")
            # In case of error, return None with mock data indicator
            return (None, False)

    async def create_water_heater(self, water_heater: WaterHeater) -> WaterHeater:
        """Create a new water heater."""
        return await self.repository.create_water_heater(water_heater)

    async def update_water_heater(
        self, device_id: str, updates: Dict[str, Any]
    ) -> Optional[WaterHeater]:
        """Update water heater properties with the specified changes.

        Args:
            device_id: ID of the water heater to update
            updates: Dictionary of fields to update and their new values

        Returns:
            Updated water heater object or None if not found
        """
        # Get current water heater to ensure it exists
        water_heater = await self.repository.get_water_heater(device_id)
        if not water_heater:
            logger.warning(f"Cannot update non-existent water heater: {device_id}")
            return None

        # Apply updates to water heater
        logger.info(f"Updating water heater {device_id} with: {updates}")
        return await self.repository.update_water_heater(device_id, updates)

    async def update_target_temperature(
        self, device_id: str, temperature: float
    ) -> Optional[WaterHeater]:
        """Update a water heater's target temperature."""
        # Validate temperature
        if temperature < 30.0 or temperature > 80.0:
            raise ValueError("Temperature must be between 30°C and 80°C")

        try:
            # Try to get the water heater with more robust error handling
            water_heater = await self.repository.get_water_heater(device_id)
            if not water_heater:
                logger.warning(
                    f"Water heater with ID {device_id} not found during temperature update"
                )

                # Check if this is a case of repository inconsistency by trying to fetch all heaters
                all_heaters = await self.repository.get_water_heaters()
                logger.info(f"Repository has {len(all_heaters)} water heaters")

                # Check if the heater exists in the list
                found_heater = next((h for h in all_heaters if h.id == device_id), None)
                if found_heater:
                    logger.info(
                        f"Found water heater {device_id} in full list but not by direct lookup"
                    )
                    water_heater = found_heater
                else:
                    # Water heater truly not found
                    return None

            # Update target temperature and mode if needed
            updates = {"target_temperature": temperature}

            # If the current temperature is significantly below target, set to heating
            if (
                water_heater.current_temperature
                and water_heater.current_temperature < temperature - 2.0
            ):
                updates["heater_status"] = WaterHeaterStatus.HEATING
            elif (
                water_heater.heater_status == WaterHeaterStatus.HEATING
                and water_heater.current_temperature >= temperature
            ):
                updates["heater_status"] = WaterHeaterStatus.STANDBY

            # Log the update operation
            logger.info(
                f"Updating water heater {device_id} temperature to {temperature}°C"
            )

            # Perform the update
            return await self.repository.update_water_heater(device_id, updates)

        except Exception as e:
            logger.error(
                f"Error updating temperature for water heater {device_id}: {e}"
            )
            # Return the original water heater if we found it but the update failed
            if water_heater:
                logger.warning(
                    f"Returning unmodified water heater due to update failure"
                )
                return water_heater
            return None

    async def update_mode(
        self, device_id: str, mode: WaterHeaterMode
    ) -> Optional[WaterHeater]:
        """Update a water heater's operational mode."""
        water_heater = await self.repository.get_water_heater(device_id)
        if not water_heater:
            return None

        # Update mode and adjust temperature if mode has specific requirements
        updates = {"mode": mode}

        # Adjust target temperature based on mode
        if mode == WaterHeaterMode.ECO and (
            not water_heater.target_temperature
            or water_heater.target_temperature > 55.0
        ):
            updates[
                "target_temperature"
            ] = 55.0  # Eco mode caps at 55°C for energy saving
        elif mode == WaterHeaterMode.OFF:
            updates["target_temperature"] = 40.0  # Off mode maintains minimal heating
        elif mode == WaterHeaterMode.BOOST and (
            not water_heater.target_temperature
            or water_heater.target_temperature < 65.0
        ):
            updates[
                "target_temperature"
            ] = 65.0  # Boost mode heats to higher temperature

        return await self.repository.update_water_heater(device_id, updates)

    async def add_reading(
        self,
        device_id: str,
        temperature: float,
        pressure: Optional[float] = None,
        energy_usage: Optional[float] = None,
        flow_rate: Optional[float] = None,
    ) -> Optional[WaterHeater]:
        """Add a temperature reading to a water heater."""
        water_heater = await self.repository.get_water_heater(device_id)
        if not water_heater:
            return None

        # Create a new reading
        reading = WaterHeaterReading(
            id=str(uuid.uuid4()),
            temperature=temperature,
            pressure=pressure,
            energy_usage=energy_usage,
            flow_rate=flow_rate,
            timestamp=datetime.now(),
        )

        # Add reading and update water heater status
        return await self.repository.add_reading(device_id, reading)

    async def get_readings(
        self, device_id: str, limit: int = 24
    ) -> List[WaterHeaterReading]:
        """Get recent readings for a water heater."""
        return await self.repository.get_readings(device_id, limit)

    async def check_thresholds(self, device_id: str) -> Dict[str, Any]:
        """
        Check if a water heater's current state exceeds any thresholds.

        Returns a dictionary of threshold violations and suggested actions.
        """
        water_heater = await self.repository.get_water_heater(device_id)
        if not water_heater or not water_heater.readings:
            return {
                "device_id": device_id,
                "status": "unknown",
                "violations": [],
                "actions": ["Check device connectivity"],
            }

        # Get the most recent reading
        latest_reading = water_heater.readings[0]

        violations = []
        actions = []

        # Check temperature thresholds
        if latest_reading.temperature > 75.0:
            violations.append(
                {
                    "type": "temperature",
                    "value": latest_reading.temperature,
                    "threshold": 75.0,
                    "severity": "critical",
                }
            )
            actions.append("Reduce temperature immediately")
        elif latest_reading.temperature > 70.0:
            violations.append(
                {
                    "type": "temperature",
                    "value": latest_reading.temperature,
                    "threshold": 70.0,
                    "severity": "warning",
                }
            )
            actions.append("Consider reducing temperature")

        # Check pressure if available
        if latest_reading.pressure is not None:
            if latest_reading.pressure > 6.0:
                violations.append(
                    {
                        "type": "pressure",
                        "value": latest_reading.pressure,
                        "threshold": 6.0,
                        "severity": "critical",
                    }
                )
                actions.append("Check pressure relief valve")
            elif latest_reading.pressure > 5.0:
                violations.append(
                    {
                        "type": "pressure",
                        "value": latest_reading.pressure,
                        "threshold": 5.0,
                        "severity": "warning",
                    }
                )
                actions.append("Monitor pressure closely")

        # Check energy usage if available
        if (
            latest_reading.energy_usage is not None
            and latest_reading.energy_usage > 3000
        ):
            violations.append(
                {
                    "type": "energy_usage",
                    "value": latest_reading.energy_usage,
                    "threshold": 3000,
                    "severity": "warning",
                }
            )
            actions.append("Check for energy efficiency issues")

        # Determine overall status
        status = "normal"
        if any(v["severity"] == "critical" for v in violations):
            status = "critical"
        elif any(v["severity"] == "warning" for v in violations):
            status = "warning"

        return {
            "device_id": device_id,
            "status": status,
            "violations": violations,
            "actions": actions,
        }

    async def perform_maintenance_check(self, device_id: str) -> Dict[str, Any]:
        """
        Perform a maintenance check on a water heater.

        Returns a dictionary with maintenance status and recommendations.
        """
        water_heater = await self.repository.get_water_heater(device_id)
        if not water_heater:
            return {
                "device_id": device_id,
                "status": "unknown",
                "issues": [],
                "recommendations": ["Device not found"],
            }

        issues = []
        recommendations = []

        # Check last maintenance date
        if water_heater.last_maintenance:
            days_since_maintenance = (
                datetime.now() - water_heater.last_maintenance
            ).days
            if days_since_maintenance > 365:
                issues.append(
                    {
                        "type": "maintenance_overdue",
                        "description": f"Last maintenance was {days_since_maintenance} days ago",
                    }
                )
                recommendations.append("Schedule annual maintenance inspection")
        else:
            issues.append(
                {
                    "type": "no_maintenance_record",
                    "description": "No maintenance records found",
                }
            )
            recommendations.append("Schedule initial maintenance inspection")

        # Check diagnostic codes
        if water_heater.diagnostic_codes:
            active_codes = [
                code for code in water_heater.diagnostic_codes if not code.resolved
            ]
            for code in active_codes:
                issues.append(
                    {
                        "type": "diagnostic_code",
                        "code": code.code,
                        "description": code.description,
                        "severity": code.severity,
                    }
                )
                recommendations.append(
                    f"Address diagnostic code {code.code}: {code.description}"
                )

        # Check warranty status
        if water_heater.warranty_expiry:
            days_to_expiry = (water_heater.warranty_expiry - datetime.now()).days
            if days_to_expiry < 0:
                issues.append(
                    {
                        "type": "warranty_expired",
                        "description": f"Warranty expired {abs(days_to_expiry)} days ago",
                    }
                )
            elif days_to_expiry < 30:
                issues.append(
                    {
                        "type": "warranty_expiring",
                        "description": f"Warranty expires in {days_to_expiry} days",
                    }
                )
                recommendations.append("Consider warranty extension options")

        # Check age of unit
        if water_heater.installation_date:
            age_in_years = (datetime.now() - water_heater.installation_date).days / 365
            if age_in_years > 10:
                issues.append(
                    {
                        "type": "unit_age",
                        "description": f"Unit is approximately {int(age_in_years)} years old",
                    }
                )
                recommendations.append("Consider replacement options for aging unit")

        # Determine overall status
        status = "good"
        if any(issue.get("severity") == "Critical" for issue in issues):
            status = "critical"
        elif (
            any(issue.get("severity") == "Warning" for issue in issues)
            or len(issues) > 2
        ):
            status = "warning"
        elif issues:
            status = "attention"

        return {
            "device_id": device_id,
            "status": status,
            "issues": issues,
            "recommendations": recommendations,
            "next_maintenance_due": water_heater.last_maintenance.isoformat()
            if water_heater.last_maintenance
            else None,
        }
