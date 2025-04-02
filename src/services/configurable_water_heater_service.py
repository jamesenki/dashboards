"""
Configurable service for water heater devices.
"""
import uuid
import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Type

from src.models.device import DeviceStatus
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterStatus,
    WaterHeaterReading,
    WaterHeaterDiagnosticCode
)
from src.repositories.water_heater_repository import (
    WaterHeaterRepository,
    MockWaterHeaterRepository,
    SQLiteWaterHeaterRepository
)
from src.utils.dummy_data import dummy_data  # Keep for backward compatibility with tests
from src.config import config

# Setup logging
logger = logging.getLogger(__name__)

# Import PostgreSQL repository if available
try:
    from src.repositories.water_heater_repository import PostgresWaterHeaterRepository
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
    logger.warning("PostgreSQL repository not available. Install required dependencies for production use.")

class ConfigurableWaterHeaterService:
    """Service for water heater operations with configurable data source."""
    
    def __init__(self, repository: Optional[WaterHeaterRepository] = None):
        """
        Initialize the service with a repository.
        
        Args:
            repository: Water heater repository implementation.
                        If None, uses configuration to determine repository.
                        
        Raises:
            Exception: If database connection fails and fallback is disabled.
        """
        if repository:
            self.repository = repository
        else:
            # Check for backward compatibility with USE_MOCK_DATA environment variable
            use_mock_data_env = os.environ.get("USE_MOCK_DATA", "").lower() in ["true", "1", "yes"]
            
            # Get configuration settings
            use_mock_data_config = config.get("services.water_heater.use_mock_data", False)
            db_type = config.get("database.type", "sqlite").lower()
            fallback_enabled = config.get("database.fallback_to_mock", True)
            
            # Use mock data if explicitly configured or set by environment variable
            if use_mock_data_env or use_mock_data_config:
                logger.info("Using mock data repository for water heaters (as configured)")
                self.repository = MockWaterHeaterRepository()
            else:
                # Try to connect to the configured database
                try:
                    if db_type == "postgres" and HAS_POSTGRES:
                        # Get PostgreSQL connection parameters
                        host = config.get("database.host", "localhost")
                        port = config.get("database.port", 5432)
                        database = config.get("database.name", "iotsphere")
                        user = config.get("database.credentials.username", "postgres")
                        password = config.get("database.credentials.password", "")
                        
                        logger.info(f"Using PostgreSQL repository for water heaters on {host}:{port}")
                        self.repository = PostgresWaterHeaterRepository(
                            host=host,
                            port=port,
                            database=database,
                            user=user,
                            password=password
                        )
                    else:
                        # Default to SQLite
                        logger.info("Using SQLite repository for water heaters")
                        self.repository = SQLiteWaterHeaterRepository()
                        
                except Exception as e:
                    # If database connection fails, check if fallback is enabled
                    if fallback_enabled:
                        logger.warning(f"Database connection failed: {e}. Falling back to mock data.")
                        self.repository = MockWaterHeaterRepository()
                    else:
                        logger.error(f"Database connection failed and fallback is disabled: {e}")
                        raise
    
    async def get_water_heaters(self) -> List[WaterHeater]:
        """Get all water heaters."""
        return await self.repository.get_water_heaters()
    
    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        """Get a specific water heater by ID."""
        return await self.repository.get_water_heater(device_id)
    
    async def create_water_heater(self, water_heater: WaterHeater) -> WaterHeater:
        """Create a new water heater."""
        return await self.repository.create_water_heater(water_heater)
        
    async def update_water_heater(self, device_id: str, updates: Dict[str, Any]) -> Optional[WaterHeater]:
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
    
    async def update_target_temperature(self, device_id: str, temperature: float) -> Optional[WaterHeater]:
        """Update a water heater's target temperature."""
        # Validate temperature
        if temperature < 30.0 or temperature > 80.0:
            raise ValueError("Temperature must be between 30°C and 80°C")
        
        try:
            # Try to get the water heater with more robust error handling
            water_heater = await self.repository.get_water_heater(device_id)
            if not water_heater:
                logger.warning(f"Water heater with ID {device_id} not found during temperature update")
                
                # Check if this is a case of repository inconsistency by trying to fetch all heaters
                all_heaters = await self.repository.get_water_heaters()
                logger.info(f"Repository has {len(all_heaters)} water heaters")
                
                # Check if the heater exists in the list
                found_heater = next((h for h in all_heaters if h.id == device_id), None)
                if found_heater:
                    logger.info(f"Found water heater {device_id} in full list but not by direct lookup")
                    water_heater = found_heater
                else:
                    # Water heater truly not found
                    return None
            
            # Update target temperature and mode if needed
            updates = {
                "target_temperature": temperature
            }
            
            # If the current temperature is significantly below target, set to heating
            if water_heater.current_temperature and water_heater.current_temperature < temperature - 2.0:
                updates["heater_status"] = WaterHeaterStatus.HEATING
            elif water_heater.heater_status == WaterHeaterStatus.HEATING and water_heater.current_temperature >= temperature:
                updates["heater_status"] = WaterHeaterStatus.STANDBY
            
            # Log the update operation
            logger.info(f"Updating water heater {device_id} temperature to {temperature}°C")
            
            # Perform the update
            return await self.repository.update_water_heater(device_id, updates)
            
        except Exception as e:
            logger.error(f"Error updating temperature for water heater {device_id}: {e}")
            # Return the original water heater if we found it but the update failed
            if water_heater:
                logger.warning(f"Returning unmodified water heater due to update failure")
                return water_heater
            return None
    
    async def update_mode(self, device_id: str, mode: WaterHeaterMode) -> Optional[WaterHeater]:
        """Update a water heater's operational mode."""
        water_heater = await self.repository.get_water_heater(device_id)
        if not water_heater:
            return None
        
        # Update mode and adjust temperature if mode has specific requirements
        updates = {
            "mode": mode
        }
        
        # Adjust target temperature based on mode
        if mode == WaterHeaterMode.ECO and (not water_heater.target_temperature or water_heater.target_temperature > 55.0):
            updates["target_temperature"] = 55.0  # Eco mode caps at 55°C for energy saving
        elif mode == WaterHeaterMode.OFF:
            updates["target_temperature"] = 40.0  # Off mode maintains minimal heating
        elif mode == WaterHeaterMode.BOOST and (not water_heater.target_temperature or water_heater.target_temperature < 65.0):
            updates["target_temperature"] = 65.0  # Boost mode heats to higher temperature
        
        return await self.repository.update_water_heater(device_id, updates)
    
    async def add_reading(
        self, 
        device_id: str, 
        temperature: float, 
        pressure: Optional[float] = None,
        energy_usage: Optional[float] = None,
        flow_rate: Optional[float] = None
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
            timestamp=datetime.now()
        )
        
        # Add reading and update water heater status
        return await self.repository.add_reading(device_id, reading)
    
    async def get_readings(self, device_id: str, limit: int = 24) -> List[WaterHeaterReading]:
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
                "actions": ["Check device connectivity"]
            }
        
        # Get the most recent reading
        latest_reading = water_heater.readings[0]
        
        violations = []
        actions = []
        
        # Check temperature thresholds
        if latest_reading.temperature > 75.0:
            violations.append({"type": "temperature", "value": latest_reading.temperature, "threshold": 75.0, "severity": "critical"})
            actions.append("Reduce temperature immediately")
        elif latest_reading.temperature > 70.0:
            violations.append({"type": "temperature", "value": latest_reading.temperature, "threshold": 70.0, "severity": "warning"})
            actions.append("Consider reducing temperature")
        
        # Check pressure if available
        if latest_reading.pressure is not None:
            if latest_reading.pressure > 6.0:
                violations.append({"type": "pressure", "value": latest_reading.pressure, "threshold": 6.0, "severity": "critical"})
                actions.append("Check pressure relief valve")
            elif latest_reading.pressure > 5.0:
                violations.append({"type": "pressure", "value": latest_reading.pressure, "threshold": 5.0, "severity": "warning"})
                actions.append("Monitor pressure closely")
        
        # Check energy usage if available
        if latest_reading.energy_usage is not None and latest_reading.energy_usage > 3000:
            violations.append({"type": "energy_usage", "value": latest_reading.energy_usage, "threshold": 3000, "severity": "warning"})
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
            "actions": actions
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
                "recommendations": ["Device not found"]
            }
        
        issues = []
        recommendations = []
        
        # Check last maintenance date
        if water_heater.last_maintenance:
            days_since_maintenance = (datetime.now() - water_heater.last_maintenance).days
            if days_since_maintenance > 365:
                issues.append({"type": "maintenance_overdue", "description": f"Last maintenance was {days_since_maintenance} days ago"})
                recommendations.append("Schedule annual maintenance inspection")
        else:
            issues.append({"type": "no_maintenance_record", "description": "No maintenance records found"})
            recommendations.append("Schedule initial maintenance inspection")
        
        # Check diagnostic codes
        if water_heater.diagnostic_codes:
            active_codes = [code for code in water_heater.diagnostic_codes if not code.resolved]
            for code in active_codes:
                issues.append({"type": "diagnostic_code", "code": code.code, "description": code.description, "severity": code.severity})
                recommendations.append(f"Address diagnostic code {code.code}: {code.description}")
        
        # Check warranty status
        if water_heater.warranty_expiry:
            days_to_expiry = (water_heater.warranty_expiry - datetime.now()).days
            if days_to_expiry < 0:
                issues.append({"type": "warranty_expired", "description": f"Warranty expired {abs(days_to_expiry)} days ago"})
            elif days_to_expiry < 30:
                issues.append({"type": "warranty_expiring", "description": f"Warranty expires in {days_to_expiry} days"})
                recommendations.append("Consider warranty extension options")
        
        # Check age of unit
        if water_heater.installation_date:
            age_in_years = (datetime.now() - water_heater.installation_date).days / 365
            if age_in_years > 10:
                issues.append({"type": "unit_age", "description": f"Unit is approximately {int(age_in_years)} years old"})
                recommendations.append("Consider replacement options for aging unit")
        
        # Determine overall status
        status = "good"
        if any(issue.get("severity") == "Critical" for issue in issues):
            status = "critical"
        elif any(issue.get("severity") == "Warning" for issue in issues) or len(issues) > 2:
            status = "warning"
        elif issues:
            status = "attention"
        
        return {
            "device_id": device_id,
            "status": status,
            "issues": issues,
            "recommendations": recommendations,
            "next_maintenance_due": water_heater.last_maintenance.isoformat() if water_heater.last_maintenance else None
        }
