"""
Device Update Handler for IoTSphere platform.

This service handles updates from devices, updates shadow documents,
and resolves pending state changes.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DeviceUpdateHandler:
    """
    Handle device state updates.

    This service is responsible for:
    1. Processing state updates from devices
    2. Updating shadow documents with reported state
    3. Resolving pending desired states when confirmed by the device
    """

    def __init__(self, shadow_service):
        """
        Initialize the device update handler.

        Args:
            shadow_service: Service for managing device shadows
        """
        self.shadow_service = shadow_service
        logger.info("Device Update Handler initialized")

    async def handle_device_update(
        self, device_id: str, update: Dict[str, Any]
    ) -> bool:
        """
        Handle a state update from a device.

        Args:
            device_id: Device identifier
            update: Device state update

        Returns:
            bool: True if update was processed successfully, False otherwise
        """
        logger.info(f"Processing update from device {device_id}")

        try:
            # Get current shadow document
            try:
                shadow = await self.shadow_service.get_device_shadow(device_id)
            except ValueError:
                logger.error(f"No shadow document found for device {device_id}")
                return False

            # Add timestamp to update
            update["last_updated"] = datetime.utcnow().isoformat() + "Z"

            # Check if this update resolves any pending desired states
            if "desired" in shadow and "_pending" in shadow["desired"]:
                pending_resolved = self._resolve_pending_states(shadow, update)
                if pending_resolved:
                    logger.info(
                        f"Resolved pending states for device {device_id}: {pending_resolved}"
                    )

            # Update the shadow with the new reported state
            await self.shadow_service.update_device_shadow(
                device_id=device_id, reported_state=update
            )

            logger.info(f"Updated shadow for device {device_id}")
            return True

        except Exception as e:
            logger.error(f"Error handling update from device {device_id}: {e}")
            return False

    def _resolve_pending_states(
        self, shadow: Dict[str, Any], update: Dict[str, Any]
    ) -> List[str]:
        """
        Resolve pending desired states that are confirmed by this update.

        Args:
            shadow: Current shadow document
            update: Device state update

        Returns:
            List: Resolved pending states
        """
        if not shadow.get("desired", {}).get("_pending"):
            return []

        pending = shadow["desired"].get("_pending", [])
        resolved = []

        # Check each pending state to see if it matches the update
        for state_name in pending[:]:  # Copy to allow modification during iteration
            if state_name in update:
                # If device reports the same value as the desired state, resolve it
                if update[state_name] == shadow["desired"].get(state_name):
                    resolved.append(state_name)
                    pending.remove(state_name)

        # Update the pending list
        if not pending:
            # If all pending states are resolved, remove the _pending field
            if "_pending" in shadow["desired"]:
                del shadow["desired"]["_pending"]
        else:
            # Otherwise update the pending list
            shadow["desired"]["_pending"] = pending

        return resolved
