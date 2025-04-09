"""
Device Manifest Processor for IoTSphere platform.

This service processes device manifests during device registration,
creating the appropriate asset entries and shadow documents.
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ManifestProcessor:
    """
    Process device manifests during registration.

    This service is responsible for:
    1. Validating the device manifest
    2. Creating asset entries based on manifest data
    3. Initializing shadow documents with appropriate structure
    """

    def __init__(self, registration_service, asset_registry, shadow_service):
        """
        Initialize the manifest processor.

        Args:
            registration_service: Service for accessing device registration information
            asset_registry: Service for managing asset metadata
            shadow_service: Service for managing device shadows
        """
        self.registration_service = registration_service
        self.asset_registry = asset_registry
        self.shadow_service = shadow_service
        logger.info("Manifest Processor initialized")

    async def process_device_manifest(
        self, device_id: str, manifest: Dict[str, Any]
    ) -> bool:
        """
        Process a device manifest.

        Args:
            device_id: Device identifier
            manifest: Device manifest containing metadata and capabilities

        Returns:
            bool: True if processing succeeded, False otherwise
        """
        logger.info(f"Processing manifest for device {device_id}")

        try:
            # Validate the manifest (basic validation)
            if not self._validate_manifest(manifest):
                logger.error(f"Invalid manifest for device {device_id}")
                return False

            # Verify device is registered
            registration = await self.registration_service.get_device(device_id)
            if not registration:
                logger.error(f"Device {device_id} not found in registration database")
                return False

            # Create asset entry from manifest
            asset_data = self._extract_asset_data(manifest)
            await self.asset_registry.create_asset(device_id, asset_data)
            logger.info(f"Created asset entry for device {device_id}")

            # Check if shadow document already exists
            try:
                existing_shadow = await self.shadow_service.get_device_shadow(device_id)

                # If shadow already exists, check for differences
                if existing_shadow:
                    logger.info(
                        f"Shadow document already exists for device {device_id}, checking for updates"
                    )

                    # Extract expected states from manifest
                    reported_state, desired_state = self._extract_shadow_states(
                        manifest
                    )

                    # Update the shadow if there are differences
                    if self._shadow_needs_update(
                        existing_shadow, reported_state, desired_state
                    ):
                        logger.info(f"Updating shadow document for device {device_id}")

                        # Update reported and desired states separately to preserve other fields
                        if reported_state:
                            await self.shadow_service.update_device_shadow(
                                device_id=device_id, reported_state=reported_state
                            )

                        if desired_state:
                            await self.shadow_service.update_device_shadow(
                                device_id=device_id, desired_state=desired_state
                            )
                    else:
                        logger.info(
                            f"No updates needed for shadow document of device {device_id}"
                        )
                else:
                    # Create shadow document if it doesn't exist
                    reported_state, desired_state = self._extract_shadow_states(
                        manifest
                    )
                    await self.shadow_service.create_device_shadow(
                        device_id=device_id,
                        reported_state=reported_state,
                        desired_state=desired_state,
                    )
                    logger.info(f"Created shadow document for device {device_id}")
            except Exception as e:
                # If there was an error getting the shadow, try to create it
                logger.warning(
                    f"Error checking shadow document for device {device_id}: {e}"
                )
                reported_state, desired_state = self._extract_shadow_states(manifest)
                await self.shadow_service.create_device_shadow(
                    device_id=device_id,
                    reported_state=reported_state,
                    desired_state=desired_state,
                )
                logger.info(
                    f"Created shadow document for device {device_id} after error"
                )

            return True

        except Exception as e:
            logger.error(f"Error processing manifest for device {device_id}: {e}")
            return False

    def _validate_manifest(self, manifest: Dict[str, Any]) -> bool:
        """
        Validate the device manifest.

        Args:
            manifest: Device manifest

        Returns:
            bool: True if valid, False otherwise
        """
        # Basic validation - check required fields
        required_fields = ["device_id", "manufacturer", "model", "capabilities"]
        for field in required_fields:
            if field not in manifest:
                logger.error(f"Missing required field '{field}' in manifest")
                return False

        # Validate capabilities section
        if not isinstance(manifest["capabilities"], dict):
            logger.error("Capabilities must be a dictionary")
            return False

        return True

    def _extract_asset_data(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract asset data from manifest.

        Args:
            manifest: Device manifest

        Returns:
            Dict: Asset data for asset registry
        """
        # Copy relevant fields to asset data
        asset_data = {
            "manufacturer": manifest["manufacturer"],
            "model": manifest["model"],
            "firmware_version": manifest.get("firmware_version", "unknown"),
            "device_type": self._determine_device_type(manifest),
            "metadata": manifest.get("metadata", {}),
        }

        return asset_data

    def _determine_device_type(self, manifest: Dict[str, Any]) -> str:
        """
        Determine device type from manifest.

        Args:
            manifest: Device manifest

        Returns:
            str: Device type
        """
        # This could be more sophisticated based on capabilities
        # For now, use device_id prefix or model info
        device_id = manifest["device_id"]

        if device_id.startswith("wh-"):
            return "water_heater"
        elif device_id.startswith("therm-"):
            return "thermostat"
        else:
            # Try to infer from model or other fields
            model = manifest["model"].lower()
            if "thermostat" in model:
                return "thermostat"
            elif "heater" in model:
                return "water_heater"
            else:
                return "generic"

    def _shadow_needs_update(
        self,
        existing_shadow: Dict[str, Any],
        reported_state: Dict[str, Any],
        desired_state: Dict[str, Any],
    ) -> bool:
        """
        Check if a shadow document needs to be updated based on differences between
        the existing shadow and the new states derived from the manifest.

        Args:
            existing_shadow: The existing shadow document
            reported_state: New reported state derived from manifest
            desired_state: New desired state derived from manifest

        Returns:
            bool: True if updates are needed, False otherwise
        """
        # Check reported state differences
        if "reported" not in existing_shadow and reported_state:
            return True

        if "reported" in existing_shadow and reported_state:
            for key, value in reported_state.items():
                # Skip last_updated since it will always be different
                if key == "last_updated":
                    continue

                # If key is missing or value is different, update is needed
                if (
                    key not in existing_shadow["reported"]
                    or existing_shadow["reported"][key] != value
                ):
                    return True

        # Check desired state differences
        if "desired" not in existing_shadow and desired_state:
            return True

        if "desired" in existing_shadow and desired_state:
            for key, value in desired_state.items():
                # Skip special fields like _pending
                if key.startswith("_"):
                    continue

                # If key is missing or value is different, update is needed
                if (
                    key not in existing_shadow["desired"]
                    or existing_shadow["desired"][key] != value
                ):
                    return True

        # No significant differences found
        return False

    def _extract_shadow_states(self, manifest: Dict[str, Any]) -> tuple:
        """
        Extract initial reported and desired states from manifest.

        Args:
            manifest: Device manifest

        Returns:
            tuple: (reported_state, desired_state)
        """
        capabilities = manifest["capabilities"]

        # Initialize with empty states
        reported_state = {"status": "OFFLINE"}  # Default to offline
        desired_state = {}

        # Add sensors to reported state (with null values initially)
        if "sensors" in capabilities:
            for sensor in capabilities["sensors"]:
                reported_state[sensor] = None

        # Add settings to both reported and desired
        if "settings" in capabilities:
            for setting in capabilities["settings"]:
                reported_state[setting] = None  # Current setting value (null initially)
                desired_state[setting] = None  # Desired setting value (null initially)

        # Add actuators to reported state
        if "actuators" in capabilities:
            for actuator in capabilities["actuators"]:
                reported_state[actuator + "_status"] = "inactive"

        return reported_state, desired_state
