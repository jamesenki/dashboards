"""
Unit tests for Message Broker Adapter.

This module contains tests for the Message Broker Adapter used for sending and receiving
events in our CDC architecture, following the TDD approach (red-green-refactor) and
Clean Architecture principles.
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# Create a simple domain event class for testing
class DomainEvent:
    """Base class for domain events."""

    def __init__(self, event_type, timestamp=None):
        self.event_type = event_type
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self):
        """Convert event to dictionary."""
        return {"event_type": self.event_type, "timestamp": self.timestamp}


class WaterHeaterTemperatureUpdated(DomainEvent):
    """Event raised when a water heater's temperature is updated."""

    def __init__(self, heater_id, old_temperature, new_temperature, timestamp=None):
        super().__init__("WaterHeaterTemperatureUpdated", timestamp)
        self.heater_id = heater_id
        self.old_temperature = old_temperature
        self.new_temperature = new_temperature

    def to_dict(self):
        """Convert event to dictionary."""
        event_dict = super().to_dict()
        event_dict.update(
            {
                "heater_id": self.heater_id,
                "old_temperature": self.old_temperature,
                "new_temperature": self.new_temperature,
            }
        )
        return event_dict


class DeviceShadowUpdated(DomainEvent):
    """Event raised when a device shadow is updated."""

    def __init__(self, device_id, update_type, data, timestamp=None):
        super().__init__("DeviceShadowUpdated", timestamp)
        self.device_id = device_id
        self.update_type = update_type  # "desired" or "reported"
        self.data = data

    def to_dict(self):
        """Convert event to dictionary."""
        event_dict = super().to_dict()
        event_dict.update(
            {
                "device_id": self.device_id,
                "update_type": self.update_type,
                "data": self.data,
            }
        )
        return event_dict


@pytest.mark.unit
class TestMessageBrokerAdapter:
    """Unit tests for Message Broker Adapter."""

    @pytest.fixture
    def mock_kafka_producer(self):
        """Create a mock Kafka producer."""
        with patch("confluent_kafka.Producer") as mock:
            mock_producer = MagicMock()
            mock.return_value = mock_producer
            yield mock_producer

    @pytest.fixture
    def mock_kafka_consumer(self):
        """Create a mock Kafka consumer."""
        with patch("confluent_kafka.Consumer") as mock:
            mock_consumer = MagicMock()
            mock.return_value = mock_consumer
            yield mock_consumer

    @pytest.fixture
    def adapter(self, mock_kafka_producer):
        """Create a message broker adapter instance with mocked dependencies."""
        with patch(
            "src.adapters.messaging.message_broker_adapter.MessageBrokerAdapter._init_producer",
            return_value=mock_kafka_producer,
        ):
            from src.adapters.messaging.message_broker_adapter import (
                MessageBrokerAdapter,
            )

            adapter = MessageBrokerAdapter(
                broker_config={
                    "bootstrap.servers": "localhost:9092",
                    "client.id": "test-client",
                }
            )
            return adapter

    @pytest.mark.red
    def test_init_producer(self, mock_kafka_producer):
        """Test initialization of Kafka producer.

        This test verifies that the adapter correctly initializes a Kafka producer
        with the provided configuration.
        """
        # Arrange
        with patch(
            "src.adapters.messaging.message_broker_adapter.MessageBrokerAdapter._init_producer",
            return_value=mock_kafka_producer,
        ):
            from src.adapters.messaging.message_broker_adapter import (
                MessageBrokerAdapter,
            )

            # Act
            adapter = MessageBrokerAdapter(
                broker_config={
                    "bootstrap.servers": "localhost:9092",
                    "client.id": "test-client",
                }
            )

            # Assert
            assert adapter.producer == mock_kafka_producer
            assert adapter.broker_config == {
                "bootstrap.servers": "localhost:9092",
                "client.id": "test-client",
            }

    @pytest.mark.red
    def test_publish_event(self, adapter, mock_kafka_producer):
        """Test publishing an event to Kafka.

        This test ensures the adapter correctly serializes a domain event
        and sends it to the Kafka topic.
        """
        # Arrange
        event = WaterHeaterTemperatureUpdated(
            heater_id="test-heater-001", old_temperature=50.0, new_temperature=55.0
        )
        topic = "water-heater-events"

        # Set up the callback handler
        callback = MagicMock()

        # Act
        adapter.publish_event(topic, event, callback=callback)

        # Assert
        mock_kafka_producer.produce.assert_called_once()
        # Check topic
        args, kwargs = mock_kafka_producer.produce.call_args
        assert args[0] == topic
        # Verify message content
        assert json.loads(args[1]) == event.to_dict()
        assert kwargs["callback"] == callback

    @pytest.mark.red
    def test_publish_event_with_key(self, adapter, mock_kafka_producer):
        """Test publishing an event with a specific key.

        This test ensures the adapter correctly serializes a domain event
        and sends it to the Kafka topic with the specified key.
        """
        # Arrange
        event = DeviceShadowUpdated(
            device_id="test-device-001",
            update_type="desired",
            data={"temperature": 60.0},
        )
        topic = "device-shadow-events"
        key = "test-device-001"

        # Act
        adapter.publish_event(topic, event, key=key)

        # Assert
        mock_kafka_producer.produce.assert_called_once()
        # Check topic and key
        args, kwargs = mock_kafka_producer.produce.call_args
        assert args[0] == topic
        assert kwargs["key"] == key

    @pytest.mark.red
    def test_flush_producer(self, adapter, mock_kafka_producer):
        """Test flushing the Kafka producer.

        This test verifies that the adapter correctly flushes the Kafka producer
        to ensure all messages are delivered.
        """
        # Arrange & Act
        adapter.flush()

        # Assert
        mock_kafka_producer.flush.assert_called_once()

    @pytest.mark.red
    def test_init_consumer(self, mock_kafka_consumer):
        """Test initialization of Kafka consumer.

        This test verifies that the adapter correctly initializes a Kafka consumer
        with the provided configuration and subscribes to the specified topic.
        """
        # Arrange
        topic = "water-heater-events"
        consumer_group = "test-group"

        with patch("confluent_kafka.Consumer", return_value=mock_kafka_consumer):
            from src.adapters.messaging.message_broker_adapter import (
                MessageBrokerAdapter,
            )

            # Act
            adapter = MessageBrokerAdapter(
                broker_config={
                    "bootstrap.servers": "localhost:9092",
                    "client.id": "test-client",
                }
            )
            consumer = adapter.create_consumer(topic, consumer_group)

            # Assert
            assert consumer == mock_kafka_consumer
            mock_kafka_consumer.subscribe.assert_called_once_with([topic])

    @pytest.mark.red
    def test_consume_messages(self, adapter, mock_kafka_consumer):
        """Test consuming messages from Kafka.

        This test ensures the adapter correctly consumes messages from Kafka
        and processes them with the provided callback.
        """
        # Arrange
        # Mock a Kafka message
        mock_message = MagicMock()
        mock_message.error.return_value = None
        mock_message.value.return_value = json.dumps(
            {
                "event_type": "WaterHeaterTemperatureUpdated",
                "timestamp": datetime.now().isoformat(),
                "heater_id": "test-heater-001",
                "old_temperature": 50.0,
                "new_temperature": 55.0,
            }
        )
        mock_message.key.return_value = "test-heater-001"

        # Set up the consumer to return our mock message
        with patch(
            "src.adapters.messaging.message_broker_adapter.MessageBrokerAdapter.create_consumer",
            return_value=mock_kafka_consumer,
        ):
            # Return None after one message to end the polling loop
            mock_kafka_consumer.poll.side_effect = [mock_message, None]

            # Create a mock callback
            mock_callback = MagicMock()

            # Act
            adapter.consume_messages(
                "water-heater-events", "test-group", mock_callback, poll_timeout=0.1
            )

            # Assert
            mock_kafka_consumer.poll.assert_called()
            mock_callback.assert_called_once()
            # Verify callback parameters
            args, _ = mock_callback.call_args
            assert args[0] == mock_message

    @pytest.mark.red
    def test_consumer_error_handling(self, adapter, mock_kafka_consumer):
        """Test handling of Kafka consumer errors.

        This test verifies that the adapter correctly handles errors that may occur
        during message consumption.
        """
        # Arrange
        # Mock a Kafka message with an error
        mock_message = MagicMock()
        mock_message.error.return_value = Exception("Kafka error")

        # Set up the consumer to return our error message
        with patch(
            "src.adapters.messaging.message_broker_adapter.MessageBrokerAdapter.create_consumer",
            return_value=mock_kafka_consumer,
        ):
            # Return None after one message to end the polling loop
            mock_kafka_consumer.poll.side_effect = [mock_message, None]

            # Create a mock callback
            mock_callback = MagicMock()

            # Act
            adapter.consume_messages(
                "water-heater-events", "test-group", mock_callback, poll_timeout=0.1
            )

            # Assert
            mock_kafka_consumer.poll.assert_called()
            # Callback should not be called due to error
            mock_callback.assert_not_called()

    @pytest.mark.red
    def test_close_consumer(self, adapter, mock_kafka_consumer):
        """Test closing the Kafka consumer.

        This test verifies that the adapter correctly closes the Kafka consumer
        when it's no longer needed.
        """
        # Arrange
        with patch(
            "src.adapters.messaging.message_broker_adapter.MessageBrokerAdapter.create_consumer",
            return_value=mock_kafka_consumer,
        ):
            # Act
            adapter.close_consumer(mock_kafka_consumer)

            # Assert
            mock_kafka_consumer.close.assert_called_once()
