"""
Shadow API Adapter Module

This adapter bridges between the new Shadow Broker Integration implementation
and the existing API contracts, following the Adapter pattern from Clean Architecture.
"""
import logging
from typing import Any, Dict, List, Optional

from src.infrastructure.client.shadow_client_adapter import (
    ShadowClientAdapter,
    ShadowUpdateEvent,
)
from src.infrastructure.messaging.shadow_broker_integration import (
    ShadowBrokerIntegration,
)
from src.services.device_shadow import DeviceShadowService
from src.services.shadow_notification_service import ShadowNotificationService

logger = logging.getLogger(__name__)


class ShadowApiAdapter:
    """
    Adapter to bridge between the new Shadow Integration and existing API contracts.

    This adapter implements the same interface as the DeviceShadowService
    expected by the API layer, but delegates to the new Shadow Integration
    components internally.
    """

    def __init__(
        self,
        shadow_broker_integration: ShadowBrokerIntegration,
        shadow_notification_service: Optional[ShadowNotificationService] = None,
        client_adapter_factory=None,
        base_ws_url: str = "ws://localhost:8000/api/ws/shadows",
    ):
        """
        Initialize the shadow API adapter.

        Args:
            shadow_broker_integration: The shadow broker integration component
            shadow_notification_service: Optional notification service for WebSocket updates
            client_adapter_factory: Factory function for creating client adapters
            base_ws_url: Base URL for WebSocket connections
        """
        self.shadow_broker = shadow_broker_integration
        self.notification_service = shadow_notification_service
        self.client_adapter_factory = (
            client_adapter_factory or self._default_client_factory
        )
        self.base_ws_url = base_ws_url
        self.client_adapters = {}  # device_id -> ShadowClientAdapter
        self._initialized = False

    async def ensure_initialized(self) -> None:
        """
        Ensure the shadow service is initialized.

        This maintains API compatibility with the existing DeviceShadowService.
        """
        if not self._initialized:
            await self.shadow_broker.initialize()
            self._initialized = True

    async def get_device_shadow(self, device_id: str) -> Dict[str, Any]:
        """
        Get the current shadow state for a device.

        Args:
            device_id: The device ID

        Returns:
            The shadow document
        """
        await self.ensure_initialized()

        # Get the client adapter for this device
        client = self._get_client_adapter(device_id)

        # Request the shadow state
        await client.connect()
        try:
            await client.subscribe()
            shadow_state = await client.get_current_state()

            # Format the response to match the expected API contract
            return {
                "device_id": device_id,
                "reported": shadow_state.get("reported", {}),
                "desired": shadow_state.get("desired", {}),
                "version": shadow_state.get("version", 1),
                "timestamp": shadow_state.get("timestamp", ""),
                "metadata": shadow_state.get("metadata", {}),
            }
        finally:
            await client.disconnect()

    async def update_device_shadow(
        self, device_id: str, desired_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update the desired state for a device.

        Args:
            device_id: The device ID
            desired_state: The desired state to set

        Returns:
            The update result
        """
        await self.ensure_initialized()

        # Get the client adapter for this device
        client = self._get_client_adapter(device_id)

        # Update the desired state
        await client.connect()
        try:
            update_result = await client.update_desired_state(desired_state)

            # Format the response to match the expected API contract
            return {
                "success": True,
                "device_id": device_id,
                "version": update_result.get("version", 1),
                "pending": list(desired_state.keys()),
            }
        except Exception as e:
            logger.error(f"Error updating shadow desired state: {e}")
            return {"success": False, "device_id": device_id, "message": str(e)}
        finally:
            await client.disconnect()

    async def get_all_shadows(self) -> List[Dict[str, Any]]:
        """
        Get all shadow documents.

        Returns:
            List of shadow documents
        """
        await self.ensure_initialized()

        # Delegate to the shadow broker integration
        return await self.shadow_broker.get_all_shadows()

    async def get_shadow_history(
        self, device_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get shadow history for a device.

        Args:
            device_id: The device ID
            limit: Maximum number of history items to return

        Returns:
            List of shadow history items
        """
        await self.ensure_initialized()

        # Delegate to the shadow broker integration
        return await self.shadow_broker.get_shadow_history(device_id, limit)

    def _get_client_adapter(self, device_id: str) -> ShadowClientAdapter:
        """
        Get or create a client adapter for a device.

        Args:
            device_id: The device ID

        Returns:
            A ShadowClientAdapter instance
        """
        if device_id not in self.client_adapters:
            self.client_adapters[device_id] = self.client_adapter_factory(
                self.base_ws_url, device_id
            )
        return self.client_adapters[device_id]

    def _default_client_factory(
        self, base_url: str, device_id: str
    ) -> ShadowClientAdapter:
        """
        Default factory function for creating client adapters.

        Args:
            base_url: Base URL for WebSocket connections
            device_id: The device ID

        Returns:
            A new ShadowClientAdapter instance
        """
        return ShadowClientAdapter(
            base_url=base_url,
            device_id=device_id,
            notification_service=self.notification_service,
        )

    # Compatibility methods to match existing DeviceShadowService interface

    async def create_shadow(
        self, device_id: str, initial_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new shadow for a device.

        Args:
            device_id: The device ID
            initial_state: The initial state

        Returns:
            The created shadow document
        """
        await self.ensure_initialized()

        # Get the client adapter for this device
        client = self._get_client_adapter(device_id)

        # Create the shadow
        await client.connect()
        try:
            # Delegate to the client adapter
            create_result = await client.create_shadow(initial_state)
            return {
                "device_id": device_id,
                "success": True,
                "version": create_result.get("version", 1),
            }
        finally:
            await client.disconnect()
