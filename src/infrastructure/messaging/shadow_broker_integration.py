"""
Shadow Broker Integration Module

This module provides the integration between the Shadow service and the Message Broker.
It acts as a bridge between the domain layer (Shadow service) and the infrastructure layer
(Message Broker) following Clean Architecture principles.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from src.infrastructure.messaging.message_broker_adapter import (
    MessageBrokerAdapter,
    MessagePublishRequest,
    TopicPattern,
)
from src.services.shadow_change_stream_listener import ShadowChangeEvent

logger = logging.getLogger(__name__)


class ShadowTopicMapper:
    """
    Utility class for formatting shadow-related topics for the message broker.

    Provides standard topic formats to ensure consistency across the system.
    """

    def __init__(self, topic_prefix: str = "devices"):
        """
        Initialize the shadow topic mapper.

        Args:
            topic_prefix: The prefix for all topics
        """
        self.topic_prefix = topic_prefix

    def get_shadow_update_topic(self, device_id: str) -> str:
        """
        Get the topic for shadow updates.

        Args:
            device_id: The device ID

        Returns:
            The topic string
        """
        return f"{self.topic_prefix}.{device_id}.shadow.update"

    def get_shadow_created_topic(self, device_id: str) -> str:
        """
        Get the topic for shadow creation events.

        Args:
            device_id: The device ID

        Returns:
            The topic string
        """
        return f"{self.topic_prefix}.{device_id}.shadow.created"

    def get_shadow_deleted_topic(self, device_id: str) -> str:
        """
        Get the topic for shadow deletion events.

        Args:
            device_id: The device ID

        Returns:
            The topic string
        """
        return f"{self.topic_prefix}.{device_id}.shadow.deleted"

    def get_shadow_field_topic(self, device_id: str, field_path: str) -> str:
        """
        Get the topic for a specific shadow field.

        Args:
            device_id: The device ID
            field_path: The path to the field

        Returns:
            The topic string
        """
        return f"{self.topic_prefix}.{device_id}.shadow.{field_path.replace('.', '.')}"

    def get_shadow_desired_topic(self, device_id: str) -> str:
        """
        Get the topic for desired shadow properties.

        Args:
            device_id: The device ID

        Returns:
            The topic string
        """
        return f"{self.topic_prefix}.{device_id}.shadow.desired"

    def get_shadow_reported_topic(self, device_id: str) -> str:
        """
        Get the topic for reported shadow properties.

        Args:
            device_id: The device ID

        Returns:
            The topic string
        """
        return f"{self.topic_prefix}.{device_id}.shadow.reported"

    def parse_device_id_from_topic(self, topic: str) -> Optional[str]:
        """
        Extract the device ID from a topic.

        Args:
            topic: The topic string

        Returns:
            The device ID or None if not found
        """
        parts = topic.split(".")
        # Check for format: iotsphere.devices.device123.shadow.*
        expected_prefix = "iotsphere.devices"

        if len(parts) >= 4 and parts[0] == "iotsphere" and "shadow" in parts:
            shadow_index = parts.index("shadow")
            if shadow_index > 2:
                return parts[shadow_index - 1]  # Device ID is right before 'shadow'
        return None

    def get_all_devices_pattern(self) -> str:
        """
        Get a topic pattern that matches all device shadows.

        Returns:
            A topic pattern string
        """
        return f"{self.topic_prefix}.#"

    def get_specific_device_pattern(self, device_id: str) -> str:
        """
        Get a topic pattern that matches a specific device.

        Args:
            device_id: The device ID

        Returns:
            A topic pattern string
        """
        return f"{self.topic_prefix}.{device_id}.#"

    def get_specific_field_pattern(self, device_id: str, field_path: str) -> str:
        """
        Get a topic pattern that matches a specific field in a device shadow.

        Args:
            device_id: The device ID
            field_path: The path to the field

        Returns:
            A topic pattern string
        """
        return f"{self.topic_prefix}.{device_id}.shadow.field.{field_path}"


class ShadowBrokerIntegration:
    """
    Integration between the Shadow service and the Message Broker.

    Listens for shadow change events and publishes them to the message broker.
    """

    def __init__(
        self,
        change_stream_listener,
        message_broker: MessageBrokerAdapter,
        topic_prefix: str = "devices",
    ):
        """
        Initialize the Shadow Broker Integration.

        Args:
            change_stream_listener: The shadow change stream listener
            message_broker: The message broker adapter
            topic_prefix: The prefix for all topics
        """
        self.change_stream_listener = change_stream_listener
        self.message_broker = message_broker
        self.topic_mapper = ShadowTopicMapper(topic_prefix)
        self.initialized = False

        # Register to receive change events
        self.change_stream_listener.register_event_handler(
            self.handle_shadow_change_event
        )

    async def initialize(self) -> None:
        """
        Initialize the integration.

        Initializes the message broker connection if not already initialized.
        """
        if not self.message_broker.initialized:
            await self.message_broker.initialize()
        self.initialized = True
        logger.info("Shadow Broker Integration initialized")

    async def close(self) -> None:
        """
        Close the integration.

        Closes the message broker connection if opened by this integration.
        """
        if self.initialized:
            await self.message_broker.close()
            self.initialized = False
            logger.info("Shadow Broker Integration closed")

    async def handle_shadow_change_event(self, event: ShadowChangeEvent) -> None:
        """
        Handle a shadow change event from the change stream listener.

        Args:
            event: The shadow change event
        """
        if not self.initialized:
            logger.warning("ShadowBrokerIntegration not initialized, initializing now")
            await self.initialize()

        # Extract necessary data from the event
        device_id = event.device_id
        operation = event.operation_type

        # Create standardized message data
        message_data = {
            "device_id": device_id,
            "operation": operation,
            "timestamp": event.timestamp
            if isinstance(event.timestamp, str)
            else str(event.timestamp),
            "data": event.full_document if hasattr(event, "full_document") else {},
        }

        # Determine which topic to publish to based on the operation type
        if operation == "insert":
            topic = self.topic_mapper.get_shadow_created_topic(device_id)
        elif operation == "update":
            topic = self.topic_mapper.get_shadow_update_topic(device_id)
        elif operation == "delete":
            topic = self.topic_mapper.get_shadow_deleted_topic(device_id)
        else:
            # Unknown operation, use a generic topic
            topic = f"{self.topic_mapper.topic_prefix}.{device_id}.shadow.operation.{operation}"

        # Publish to the appropriate topic
        await self.message_broker.publish(
            MessagePublishRequest(
                topic=topic,
                message=message_data,
                headers={"content_source": "shadow_change_stream"},
            )
        )
        logger.debug(f"Published shadow change to {topic}")

        # If we have specific fields that changed, publish to field-specific topics
        if (
            hasattr(event, "full_document")
            and event.full_document
            and isinstance(event.full_document, dict)
        ):
            await self._publish_field_updates(device_id, event.full_document)

    async def _publish_field_updates(
        self, device_id: str, document: Dict[str, Any], parent_path: str = ""
    ) -> None:
        """
        Recursively publish updates to field-specific topics.

        Args:
            device_id: The device ID
            document: The document containing the fields to publish
            parent_path: The parent path in dot notation
        """
        for key, value in document.items():
            # Build the current path
            current_path = f"{parent_path}.{key}" if parent_path else key

            # Publish to the field-specific topic
            field_topic = self.topic_mapper.get_shadow_field_topic(
                device_id, current_path
            )
            await self.message_broker.publish(
                MessagePublishRequest(
                    topic=field_topic,
                    message=value,
                    headers={
                        "content_source": "shadow_change_stream",
                        "field_path": current_path,
                    },
                )
            )
            logger.debug(f"Published field update to {field_topic}")

            # If we have desired or reported state, publish to special topics
            if key == "desired" and not parent_path:
                desired_topic = self.topic_mapper.get_shadow_desired_topic(device_id)
                await self.message_broker.publish(
                    MessagePublishRequest(
                        topic=desired_topic,
                        message=value,
                        headers={"content_source": "shadow_change_stream"},
                    )
                )
                logger.debug(f"Published desired state to {desired_topic}")
            elif key == "reported" and not parent_path:
                reported_topic = self.topic_mapper.get_shadow_reported_topic(device_id)
                await self.message_broker.publish(
                    MessagePublishRequest(
                        topic=reported_topic,
                        message=value,
                        headers={"content_source": "shadow_change_stream"},
                    )
                )
                logger.debug(f"Published reported state to {reported_topic}")

            # Recursively publish nested fields
            if isinstance(value, dict):
                await self._publish_field_updates(device_id, value, current_path)
