"""
Frontend Request Handler for IoTSphere platform.

This service handles requests from the frontend for device state changes,
updating shadow documents with pending desired states until confirmed by the device.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FrontendRequestHandler:
    """
    Handle state change requests from the frontend.

    This service is responsible for:
    1. Processing state change requests from the frontend
    2. Updating shadow documents with desired state
    3. Marking desired states as pending until confirmed by the device
    """

    def __init__(self, shadow_service):
        """
        Initialize the frontend request handler.

        Args:
            shadow_service: Service for managing device shadows
        """
        self.shadow_service = shadow_service
        logger.info("Frontend Request Handler initialized")

    async def handle_state_change_request(
        self, device_id: str, request: Dict[str, Any]
    ) -> bool:
        """
        Handle a state change request from the frontend.

        Args:
            device_id: Device identifier
            request: Desired state change request

        Returns:
            bool: True if the request was processed successfully, False otherwise
        """
        logger.info(f"Processing state change request for device {device_id}")

        try:
            # Get current shadow document
            try:
                shadow = await self.shadow_service.get_device_shadow(device_id)
            except ValueError:
                logger.error(f"No shadow document found for device {device_id}")
                return False

            # Add timestamp to request
            request["request_time"] = datetime.utcnow().isoformat() + "Z"

            # Track pending state changes
            pending_states = self._get_pending_states(shadow, request)
            if pending_states:
                request["_pending"] = pending_states
                logger.info(
                    f"Marking states as pending for device {device_id}: {pending_states}"
                )

            # Update the shadow with the new desired state
            await self.shadow_service.update_device_shadow(
                device_id=device_id, desired_state=request
            )

            logger.info(f"Updated desired state for device {device_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error handling state change request for device {device_id}: {e}"
            )
            return False

    def _get_pending_states(
        self, shadow: Dict[str, Any], request: Dict[str, Any]
    ) -> List[str]:
        """
        Determine which states should be marked as pending.

        Args:
            shadow: Current shadow document
            request: Desired state change request

        Returns:
            List: States to mark as pending
        """
        # Get existing pending states, if any
        existing_pending = shadow.get("desired", {}).get("_pending", [])

        # Identify states that have changed from the current desired state
        pending = []
        for key, value in request.items():
            # Skip metadata fields
            if key.startswith("_") or key == "request_time":
                continue

            # Check if this is a change from current reported state
            current_value = shadow.get("reported", {}).get(key)
            if current_value != value:
                pending.append(key)

        # Combine with existing pending states
        combined_pending = list(set(existing_pending + pending))
        # Sort for consistent ordering in tests and to ensure deterministic behavior
        combined_pending.sort()
        return combined_pending
