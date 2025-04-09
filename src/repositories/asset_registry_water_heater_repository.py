"""
Asset Registry-based implementation of the water heater repository.

This repository uses the Asset Registry and Device Shadow services to retrieve
water heater information, providing a bridge between the manufacturer-agnostic API
and the already-populated asset registry.
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models.device import DeviceStatus
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
    WaterHeaterType,
)
from src.repositories.water_heater_repository import WaterHeaterRepository
from src.services.asset_registry import AssetRegistryService
from src.services.device_shadow import DeviceShadowService

logger = logging.getLogger(__name__)


class AssetRegistryWaterHeaterRepository(WaterHeaterRepository):
    """Repository implementation that gets water heaters from the Asset Registry and Shadow Service."""

    def __init__(self):
        """Initialize the repository with Asset Registry and Device Shadow services."""
        self.asset_service = AssetRegistryService()
        self.shadow_service = DeviceShadowService()
        logger.info("Initialized Asset Registry Water Heater Repository")

    async def get_water_heaters(
        self, manufacturer: Optional[str] = None
    ) -> List[WaterHeater]:
        """
        Get all water heaters from the Asset Registry and enrich with shadow data.

        Args:
            manufacturer: Optional filter by manufacturer name

        Returns:
            List of water heaters, optionally filtered by manufacturer
        """
        try:
            # Get all devices from the asset registry
            logger.info("Querying Asset Registry for water heaters")

            # Log all available device types for debugging
            try:
                all_devices = await self.asset_service.list_devices()
                device_types = set(
                    device.get("device_type", "unknown") for device in all_devices
                )
                logger.info(f"Available device types in Asset Registry: {device_types}")
                logger.info(f"Total devices in Asset Registry: {len(all_devices)}")

                # Log a sample of devices for debugging
                for i, device in enumerate(all_devices[:5]):
                    logger.info(f"Sample device {i+1}: {device}")
            except Exception as list_error:
                logger.error(f"Error listing all devices: {list_error}")

            # Get all devices tagged as water heaters
            try:
                devices = await self.asset_service.list_devices_by_device_type(
                    "water_heater"
                )
                logger.info(f"Found {len(devices)} water heaters in Asset Registry")
            except Exception as type_error:
                logger.error(
                    f"Error getting devices by type 'water_heater': {type_error}"
                )
                # Try alternate method as fallback
                all_devices = await self.asset_service.list_devices()
                devices = [
                    d for d in all_devices if d.get("device_type") == "water_heater"
                ]
                logger.info(
                    f"Fallback method found {len(devices)} water heaters in Asset Registry"
                )

            # Filter by manufacturer if specified
            if manufacturer:
                devices = [
                    device
                    for device in devices
                    if device.get("manufacturer", "").lower() == manufacturer.lower()
                ]
                logger.info(
                    f"Filtered to {len(devices)} water heaters by manufacturer: {manufacturer}"
                )

            # Convert devices to WaterHeater objects, enriched with shadow data
            water_heaters = []
            for device in devices:
                try:
                    water_heater = await self._device_to_water_heater(device)
                    water_heaters.append(water_heater)
                except Exception as e:
                    logger.error(f"Error converting device to water heater: {e}")

            return water_heaters
        except Exception as e:
            logger.error(f"Error getting water heaters from Asset Registry: {e}")
            return []

    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        """
        Get a specific water heater by ID from the Asset Registry and Shadow Service.

        Args:
            device_id: ID of the water heater

        Returns:
            WaterHeater object or None if not found
        """
        try:
            # Get device from Asset Registry
            device = await self.asset_service.get_device_info(device_id)
            if not device:
                logger.warning(f"Water heater {device_id} not found in Asset Registry")
                return None

            return await self._device_to_water_heater(device)
        except Exception as e:
            logger.error(
                f"Error getting water heater {device_id} from Asset Registry: {e}"
            )
            return None

    async def create_water_heater(self, water_heater: WaterHeater) -> WaterHeater:
        """
        Create a new water heater in the Asset Registry.

        Args:
            water_heater: WaterHeater object to create

        Returns:
            Created WaterHeater object
        """
        try:
            # Convert WaterHeater to asset registry device format
            device_data = {
                "device_id": water_heater.id,
                "name": water_heater.name,
                "manufacturer": water_heater.manufacturer,
                "model": water_heater.model,
                "device_type": "water_heater",  # Changed from 'type' to 'device_type'
                "status": water_heater.status.value
                if water_heater.status
                else "UNKNOWN",
                "location": water_heater.location,
                "installation_date": water_heater.installation_date.isoformat()
                if water_heater.installation_date
                else None,
            }

            # Create in Asset Registry
            await self.asset_service.register_device(device_data)

            # Create shadow document
            shadow_data = {
                "reported": {
                    "temperature": water_heater.current_temperature,
                    "target_temperature": water_heater.target_temperature,
                    "mode": water_heater.mode.value if water_heater.mode else "NORMAL",
                    "heater_status": water_heater.heater_status.value
                    if water_heater.heater_status
                    else "STANDBY",
                    "status": water_heater.status.value
                    if water_heater.status
                    else "ONLINE",
                    "last_updated": datetime.now().isoformat() + "Z",
                },
                "desired": {
                    "target_temperature": water_heater.target_temperature,
                    "mode": water_heater.mode.value if water_heater.mode else "NORMAL",
                },
            }

            # Check if shadow already exists
            try:
                existing_shadow = await self.shadow_service.get_device_shadow(
                    water_heater.id
                )
                if existing_shadow:
                    # Update existing shadow
                    await self.shadow_service.update_device_shadow(
                        water_heater.id, shadow_data["reported"]
                    )
                    await self.shadow_service.update_device_desired_state(
                        water_heater.id, shadow_data["desired"]
                    )
                else:
                    # Create new shadow
                    await self.shadow_service.create_device_shadow(
                        water_heater.id,
                        reported_state=shadow_data["reported"],
                        desired_state=shadow_data["desired"],
                    )
            except Exception:
                # Shadow doesn't exist, create it
                await self.shadow_service.create_device_shadow(
                    water_heater.id,
                    reported_state=shadow_data["reported"],
                    desired_state=shadow_data["desired"],
                )

            return water_heater
        except Exception as e:
            logger.error(f"Error creating water heater in Asset Registry: {e}")
            raise

    async def update_water_heater(
        self, device_id: str, updates: Dict[str, Any]
    ) -> Optional[WaterHeater]:
        """
        Update a water heater in the Asset Registry and Shadow Service.

        Args:
            device_id: ID of the water heater to update
            updates: Dictionary of fields to update and their new values

        Returns:
            Updated WaterHeater object or None if not found
        """
        try:
            # Get current water heater to ensure it exists
            water_heater = await self.get_water_heater(device_id)
            if not water_heater:
                logger.warning(f"Cannot update non-existent water heater: {device_id}")
                return None

            # Separate updates into shadow and device metadata
            shadow_updates = {}
            metadata_updates = {}

            for key, value in updates.items():
                if key in [
                    "current_temperature",
                    "target_temperature",
                    "mode",
                    "heater_status",
                    "status",
                ]:
                    # Shadow attributes
                    if key == "mode" and isinstance(value, WaterHeaterMode):
                        shadow_updates[key] = value.value
                    elif key == "heater_status" and isinstance(
                        value, WaterHeaterStatus
                    ):
                        shadow_updates[key] = value.value
                    elif key == "status" and isinstance(value, DeviceStatus):
                        shadow_updates[key] = value.value
                    else:
                        shadow_updates[key] = value
                else:
                    # Metadata attributes
                    metadata_updates[key] = value

            # Update shadow if needed
            if shadow_updates:
                try:
                    # Get current shadow
                    shadow = await self.shadow_service.get_device_shadow(device_id)

                    # Prepare updates
                    reported_updates = {}
                    desired_updates = {}

                    for key, value in shadow_updates.items():
                        if key == "current_temperature":
                            reported_updates["temperature"] = value
                        elif key == "target_temperature":
                            desired_updates["target_temperature"] = value
                            # Also update reported for immediate UI feedback
                            reported_updates["target_temperature"] = value
                        elif key == "mode":
                            desired_updates["mode"] = value
                            reported_updates["mode"] = value
                        else:
                            reported_updates[key] = value

                    # Add timestamp to reported updates
                    reported_updates["last_updated"] = datetime.now().isoformat() + "Z"

                    # Update shadow
                    if reported_updates:
                        await self.shadow_service.update_device_shadow(
                            device_id, reported_updates
                        )

                    if desired_updates:
                        await self.shadow_service.update_device_desired_state(
                            device_id, desired_updates
                        )

                except Exception as shadow_error:
                    logger.error(
                        f"Error updating shadow for {device_id}: {shadow_error}"
                    )

            # Update metadata if needed
            if metadata_updates:
                try:
                    # Convert to device metadata format
                    device_updates = {}
                    for key, value in metadata_updates.items():
                        device_updates[key] = value

                    # Update in Asset Registry
                    await self.asset_service.update_device_metadata(
                        device_id, device_updates
                    )
                except Exception as metadata_error:
                    logger.error(
                        f"Error updating metadata for {device_id}: {metadata_error}"
                    )

            # Return updated water heater
            return await self.get_water_heater(device_id)
        except Exception as e:
            logger.error(f"Error updating water heater in Asset Registry: {e}")
            return None

    async def add_reading(
        self, device_id: str, reading: WaterHeaterReading
    ) -> Optional[WaterHeater]:
        """
        Add a reading to water heater history.

        Args:
            device_id: ID of the water heater
            reading: Reading to add

        Returns:
            Updated WaterHeater object or None if not found
        """
        try:
            # Get current water heater to ensure it exists
            water_heater = await self.get_water_heater(device_id)
            if not water_heater:
                logger.warning(
                    f"Cannot add reading to non-existent water heater: {device_id}"
                )
                return None

            # Create shadow history entry
            history_data = {
                "temperature": reading.temperature,
                "timestamp": reading.timestamp.isoformat()
                if reading.timestamp
                else datetime.now().isoformat(),
            }

            # Add optional readings if available
            if reading.pressure is not None:
                history_data["pressure"] = reading.pressure
            if reading.energy_usage is not None:
                history_data["energy_usage"] = reading.energy_usage
            if reading.flow_rate is not None:
                history_data["flow_rate"] = reading.flow_rate

            # Update current state in shadow
            await self.shadow_service.update_device_shadow(device_id, history_data)

            # Add to history
            await self.shadow_service.add_shadow_history(device_id, history_data)

            # Return updated water heater
            return await self.get_water_heater(device_id)
        except Exception as e:
            logger.error(f"Error adding reading to water heater in Asset Registry: {e}")
            return None

    async def get_readings(
        self, device_id: str, limit: int = 24
    ) -> List[WaterHeaterReading]:
        """
        Get readings for a water heater from shadow history.

        Args:
            device_id: ID of the water heater
            limit: Maximum number of readings to return

        Returns:
            List of readings, most recent first
        """
        try:
            # Get history from shadow service
            history = await self.shadow_service.get_shadow_history(device_id, limit)

            # Convert to readings
            readings = []
            for entry in history:
                reading = WaterHeaterReading(
                    temperature=entry.get("temperature"),
                    timestamp=datetime.fromisoformat(
                        entry.get("timestamp").replace("Z", "+00:00")
                    )
                    if entry.get("timestamp")
                    else datetime.now(),
                    pressure=entry.get("pressure"),
                    energy_usage=entry.get("energy_usage"),
                    flow_rate=entry.get("flow_rate"),
                )
                readings.append(reading)

            return readings
        except Exception as e:
            logger.error(f"Error getting readings for water heater {device_id}: {e}")
            return []

    async def _device_to_water_heater(self, device: Dict[str, Any]) -> WaterHeater:
        """
        Convert a device from Asset Registry to a WaterHeater object, enriched with shadow data.

        Args:
            device: Device data from Asset Registry

        Returns:
            WaterHeater object
        """
        # Extract device_id safely, logging errors if not present
        device_id = device.get("device_id")
        if not device_id:
            logger.error(f"Device missing device_id: {device}")
            # Use a default or generated ID as fallback
            device_id = str(uuid.uuid4())

        # Get shadow data
        try:
            shadow = await self.shadow_service.get_device_shadow(device_id)
            if shadow:
                reported = shadow.get("reported", {})
                desired = shadow.get("desired", {})
            else:
                logger.warning(f"No shadow document found for device {device_id}")
                reported = {}
                desired = {}
        except Exception as e:
            logger.warning(f"Error getting shadow for device {device_id}: {e}")
            reported = {}
            desired = {}

        # Get readings from history
        try:
            history = await self.shadow_service.get_shadow_history(device_id, 24)
            readings = []
            if history:
                for entry in history:
                    try:
                        # Safely handle timestamp parsing
                        timestamp = None
                        if entry.get("timestamp"):
                            try:
                                # Try different formats to handle various timestamp formats
                                timestamp_str = entry.get("timestamp")
                                if "Z" in timestamp_str:
                                    timestamp_str = timestamp_str.replace("Z", "+00:00")
                                timestamp = datetime.fromisoformat(timestamp_str)
                            except ValueError:
                                timestamp = datetime.now()
                        else:
                            timestamp = datetime.now()

                        reading = WaterHeaterReading(
                            temperature=entry.get("temperature"),
                            timestamp=timestamp,
                            pressure=entry.get("pressure"),
                            energy_usage=entry.get("energy_usage"),
                            flow_rate=entry.get("flow_rate"),
                        )
                        readings.append(reading)
                    except Exception as reading_error:
                        logger.warning(
                            f"Error creating reading from history entry {entry}: {reading_error}"
                        )
            else:
                logger.info(f"No history found for device {device_id}")
        except Exception as e:
            logger.warning(f"Error getting history for device {device_id}: {e}")
            readings = []

        # Safely parse dates
        installation_date = None
        warranty_expiry = None
        last_maintenance = None

        if device.get("installation_date"):
            try:
                date_str = device.get("installation_date")
                if "Z" in date_str:
                    date_str = date_str.replace("Z", "+00:00")
                installation_date = datetime.fromisoformat(date_str)
            except ValueError:
                logger.warning(
                    f"Invalid installation_date format: {device.get('installation_date')}"
                )

        if device.get("warranty_expiry"):
            try:
                date_str = device.get("warranty_expiry")
                if "Z" in date_str:
                    date_str = date_str.replace("Z", "+00:00")
                warranty_expiry = datetime.fromisoformat(date_str)
            except ValueError:
                logger.warning(
                    f"Invalid warranty_expiry format: {device.get('warranty_expiry')}"
                )

        if device.get("last_maintenance"):
            try:
                date_str = device.get("last_maintenance")
                if "Z" in date_str:
                    date_str = date_str.replace("Z", "+00:00")
                last_maintenance = datetime.fromisoformat(date_str)
            except ValueError:
                logger.warning(
                    f"Invalid last_maintenance format: {device.get('last_maintenance')}"
                )

        # Safely parse last_updated
        last_seen = None
        if reported.get("last_updated"):
            try:
                date_str = reported.get("last_updated")
                if "Z" in date_str:
                    date_str = date_str.replace("Z", "+00:00")
                last_seen = datetime.fromisoformat(date_str)
            except ValueError:
                logger.warning(
                    f"Invalid last_updated format: {reported.get('last_updated')}"
                )

        # Safely handle enums
        try:
            mode = (
                WaterHeaterMode(reported.get("mode"))
                if reported.get("mode")
                else WaterHeaterMode.NORMAL
            )
        except ValueError:
            logger.warning(f"Invalid mode value: {reported.get('mode')}")
            mode = WaterHeaterMode.NORMAL

        try:
            heater_status = (
                WaterHeaterStatus(reported.get("heater_status"))
                if reported.get("heater_status")
                else WaterHeaterStatus.STANDBY
            )
        except ValueError:
            logger.warning(
                f"Invalid heater_status value: {reported.get('heater_status')}"
            )
            heater_status = WaterHeaterStatus.STANDBY

        try:
            status = (
                DeviceStatus(reported.get("status"))
                if reported.get("status")
                else DeviceStatus.ONLINE
            )
        except ValueError:
            logger.warning(f"Invalid status value: {reported.get('status')}")
            status = DeviceStatus.ONLINE

        try:
            water_heater_type = (
                WaterHeaterType(device.get("water_heater_type"))
                if device.get("water_heater_type")
                else WaterHeaterType.TANK
            )
        except ValueError:
            logger.warning(
                f"Invalid water_heater_type value: {device.get('water_heater_type')}"
            )
            water_heater_type = WaterHeaterType.TANK

        # Create WaterHeater object with all the safely parsed data
        water_heater = WaterHeater(
            id=device_id,
            name=device.get("name", f"Water Heater {device_id}"),
            manufacturer=device.get("manufacturer", "Unknown"),
            model=device.get("model", "Generic"),
            location=device.get("location", "Unknown"),
            installation_date=installation_date,
            warranty_expiry=warranty_expiry,
            last_maintenance=last_maintenance,
            # Shadow data
            current_temperature=reported.get(
                "temperature", 70.0
            ),  # Default temperature
            target_temperature=desired.get(
                "target_temperature", reported.get("target_temperature", 120.0)
            ),  # Default target
            mode=mode,
            heater_status=heater_status,
            status=status,
            last_seen=last_seen,
            readings=readings,
            # Additional attributes
            water_heater_type=water_heater_type,
            capacity=device.get("capacity"),
            energy_rating=device.get("energy_rating"),
            diagnostic_codes=[],
        )

        logger.info(f"Successfully converted device {device_id} to water heater")
        return water_heater
