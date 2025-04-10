"""
Test suite for the Message Broker Adapter following TDD principles.

This test suite defines the expected behavior of the message broker adapter
before implementation, establishing a clear contract for how the component
should function. Each test focuses on one atomic behavior.
"""
import asyncio
import json
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import aio_pika
import pytest
from aio_pika import ExchangeType, Message

from src.infrastructure.messaging.message_broker_adapter import (
    MessageBrokerAdapter,
    MessagePublishRequest,
    MessageSubscriptionRequest,
    TopicPattern,
)


class TestMessageBrokerAdapter(unittest.TestCase):
    """Test suite for the Message Broker Adapter implementation."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock connection and channel
        self.mock_connection = AsyncMock()
        self.mock_channel = AsyncMock()
        self.mock_exchange = AsyncMock()
        self.mock_queue = AsyncMock()

        # Configure mocks
        self.mock_connection.channel.return_value = self.mock_channel
        self.mock_channel.declare_exchange.return_value = self.mock_exchange
        self.mock_channel.declare_queue.return_value = self.mock_queue

        # Configure the adapter
        self.adapter = MessageBrokerAdapter(
            broker_url="amqp://guest:guest@localhost:5672/",
            exchange_name="iotsphere.events",
        )
        self.adapter.connection = self.mock_connection
        self.adapter.channel = self.mock_channel
        self.adapter.exchange = self.mock_exchange

    def test_init_sets_properties(self):
        """Test that initialization sets the properties correctly."""
        # Arrange & Act
        adapter = MessageBrokerAdapter(
            broker_url="amqp://test:test@testhost:5672/",
            exchange_name="test.exchange",
            reconnect_interval=30,
        )

        # Assert
        self.assertEqual(adapter.broker_url, "amqp://test:test@testhost:5672/")
        self.assertEqual(adapter.exchange_name, "test.exchange")
        self.assertEqual(adapter.reconnect_interval, 30)
        self.assertFalse(adapter.initialized)
        self.assertEqual(adapter.subscribers, {})

    @pytest.mark.asyncio
    async def test_initialize_creates_connection(self):
        """Test that initialize creates a connection to the message broker."""
        # Reset adapter to test initialization
        self.adapter.connection = None
        self.adapter.channel = None
        self.adapter.exchange = None

        # Mock aio_pika.connect
        with patch("aio_pika.connect_robust", new=AsyncMock()) as mock_connect:
            mock_connect.return_value = self.mock_connection

            # Act
            await self.adapter.initialize()

            # Assert
            mock_connect.assert_called_once_with(
                self.adapter.broker_url,
                reconnect_interval=self.adapter.reconnect_interval,
            )

    @pytest.mark.asyncio
    async def test_initialize_creates_channel(self):
        """Test that initialize creates a channel from the connection."""
        # Reset adapter to test initialization
        self.adapter.connection = self.mock_connection
        self.adapter.channel = None
        self.adapter.exchange = None

        # Act
        await self.adapter.initialize()

        # Assert
        self.mock_connection.channel.assert_called_once()
        self.assertEqual(self.adapter.channel, self.mock_channel)

    @pytest.mark.asyncio
    async def test_initialize_declares_exchange(self):
        """Test that initialize declares the exchange."""
        # Reset adapter to test initialization
        self.adapter.connection = self.mock_connection
        self.adapter.channel = self.mock_channel
        self.adapter.exchange = None

        # Act
        await self.adapter.initialize()

        # Assert
        self.mock_channel.declare_exchange.assert_called_once_with(
            self.adapter.exchange_name, ExchangeType.TOPIC, durable=True
        )
        self.assertEqual(self.adapter.exchange, self.mock_exchange)

    @pytest.mark.asyncio
    async def test_initialize_sets_initialized_flag(self):
        """Test that initialize sets the initialized flag."""
        # Reset adapter to test initialization
        self.adapter.connection = self.mock_connection
        self.adapter.channel = self.mock_channel
        self.adapter.exchange = self.mock_exchange
        self.adapter.initialized = False

        # Act
        await self.adapter.initialize()

        # Assert
        self.assertTrue(self.adapter.initialized)

    @pytest.mark.asyncio
    async def test_close_closes_connection(self):
        """Test that close closes the connection."""
        # Act
        await self.adapter.close()

        # Assert
        self.mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_resets_initialized_flag(self):
        """Test that close resets the initialized flag."""
        # Arrange
        self.adapter.initialized = True

        # Act
        await self.adapter.close()

        # Assert
        self.assertFalse(self.adapter.initialized)

    @pytest.mark.asyncio
    async def test_create_message_sets_content_type(self):
        """Test that _create_message sets the content type correctly."""
        # Arrange
        data = {"test": "data"}
        content_type = "application/json"

        # Act
        message = self.adapter._create_message(data, content_type=content_type)

        # Assert
        self.assertEqual(message.content_type, content_type)

    @pytest.mark.asyncio
    async def test_create_message_encodes_json_data(self):
        """Test that _create_message correctly encodes JSON data."""
        # Arrange
        data = {"test": "data", "value": 42}

        # Act
        message = self.adapter._create_message(data, content_type="application/json")

        # Assert
        decoded_data = json.loads(message.body.decode())
        self.assertEqual(decoded_data, data)

    @pytest.mark.asyncio
    async def test_create_message_sets_message_id(self):
        """Test that _create_message sets the message ID if provided."""
        # Arrange
        data = {"test": "data"}
        message_id = "test_message_id"

        # Act
        message = self.adapter._create_message(data, message_id=message_id)

        # Assert
        self.assertEqual(message.message_id, message_id)

    @pytest.mark.asyncio
    async def test_create_message_sets_correlation_id(self):
        """Test that _create_message sets the correlation ID if provided."""
        # Arrange
        data = {"test": "data"}
        correlation_id = "test_correlation_id"

        # Act
        message = self.adapter._create_message(data, correlation_id=correlation_id)

        # Assert
        self.assertEqual(message.correlation_id, correlation_id)

    @pytest.mark.asyncio
    async def test_create_message_sets_headers(self):
        """Test that _create_message sets the headers if provided."""
        # Arrange
        data = {"test": "data"}
        headers = {"source": "test", "version": "1.0"}

        # Act
        message = self.adapter._create_message(data, headers=headers)

        # Assert
        self.assertEqual(message.headers, headers)

    @pytest.mark.asyncio
    async def test_create_message_sets_timestamp(self):
        """Test that _create_message sets the timestamp."""
        # Arrange
        data = {"test": "data"}

        # Act
        message = self.adapter._create_message(data)

        # Assert
        self.assertIsNotNone(message.timestamp)

    @pytest.mark.asyncio
    async def test_publish_creates_message_correctly(self):
        """Test that publish creates a message correctly."""
        # Arrange
        topic = "devices.device123.shadow.reported"
        message_data = {"device_id": "device123", "temperature": 75}

        request = MessagePublishRequest(
            topic=topic,
            message=message_data,
            message_id="test_message_1",
            correlation_id="test_correlation_1",
            content_type="application/json",
            headers={"source": "test"},
        )

        # Mock the _create_message method
        original_create_message = self.adapter._create_message
        mock_message = MagicMock(spec=Message)
        self.adapter._create_message = MagicMock(return_value=mock_message)

        # Act
        await self.adapter.publish(request)

        # Assert
        self.adapter._create_message.assert_called_once_with(
            message_data,
            content_type="application/json",
            message_id="test_message_1",
            correlation_id="test_correlation_1",
            headers={"source": "test"},
        )

        # Restore original method
        self.adapter._create_message = original_create_message

    @pytest.mark.asyncio
    async def test_publish_sends_to_correct_topic(self):
        """Test that publish sends to the correct topic."""
        # Arrange
        topic = "devices.device123.shadow.reported"
        message_data = {"device_id": "device123", "temperature": 75}

        request = MessagePublishRequest(topic=topic, message=message_data)

        # Act
        await self.adapter.publish(request)

        # Assert
        self.mock_exchange.publish.assert_called_once()
        routing_key = self.mock_exchange.publish.call_args[1]["routing_key"]
        self.assertEqual(routing_key, topic)

    @pytest.mark.asyncio
    async def test_publish_checks_initialized(self):
        """Test that publish checks if the adapter is initialized."""
        # Arrange
        self.adapter.initialized = False

        # Act & Assert
        with pytest.raises(RuntimeError):
            await self.adapter.publish(
                MessagePublishRequest(topic="test.topic", message={"test": "data"})
            )

    @pytest.mark.asyncio
    async def test_subscribe_declares_queue(self):
        """Test that subscribe declares a queue."""
        # Arrange
        topic_pattern = "devices.device123.shadow.*"
        queue_name = "test_queue"
        callback = AsyncMock()

        request = MessageSubscriptionRequest(
            topic_pattern=TopicPattern(pattern=topic_pattern),
            queue_name=queue_name,
            callback=callback,
            exclusive=True,
            auto_delete=True,
        )

        # Act
        await self.adapter.subscribe(request)

        # Assert
        self.mock_channel.declare_queue.assert_called_once_with(
            queue_name, exclusive=True, auto_delete=True
        )

    @pytest.mark.asyncio
    async def test_subscribe_binds_queue_to_exchange(self):
        """Test that subscribe binds the queue to the exchange with the correct routing key."""
        # Arrange
        topic_pattern = "devices.device123.shadow.*"
        queue_name = "test_queue"
        callback = AsyncMock()

        request = MessageSubscriptionRequest(
            topic_pattern=TopicPattern(pattern=topic_pattern),
            queue_name=queue_name,
            callback=callback,
        )

        # Act
        await self.adapter.subscribe(request)

        # Assert
        self.mock_queue.bind.assert_called_once_with(
            self.mock_exchange, routing_key=topic_pattern
        )

    @pytest.mark.asyncio
    async def test_subscribe_sets_up_consumer(self):
        """Test that subscribe sets up a consumer for the queue."""
        # Arrange
        topic_pattern = "devices.device123.shadow.*"
        queue_name = "test_queue"
        callback = AsyncMock()

        request = MessageSubscriptionRequest(
            topic_pattern=TopicPattern(pattern=topic_pattern),
            queue_name=queue_name,
            callback=callback,
        )

        consumer_tag = "test_consumer"
        self.mock_queue.consume.return_value = consumer_tag

        # Act
        result = await self.adapter.subscribe(request)

        # Assert
        self.mock_queue.consume.assert_called_once()
        self.assertEqual(result, consumer_tag)

    @pytest.mark.asyncio
    async def test_subscribe_registers_callback(self):
        """Test that subscribe registers the callback in the subscribers dictionary."""
        # Arrange
        topic_pattern = "devices.device123.shadow.*"
        queue_name = "test_queue"
        callback = AsyncMock()

        request = MessageSubscriptionRequest(
            topic_pattern=TopicPattern(pattern=topic_pattern),
            queue_name=queue_name,
            callback=callback,
        )

        consumer_tag = "test_consumer"
        self.mock_queue.consume.return_value = consumer_tag

        # Act
        await self.adapter.subscribe(request)

        # Assert
        self.assertIn(consumer_tag, self.adapter.subscribers)
        self.assertEqual(self.adapter.subscribers[consumer_tag].callback, callback)

    @pytest.mark.asyncio
    async def test_subscribe_checks_initialized(self):
        """Test that subscribe checks if the adapter is initialized."""
        # Arrange
        self.adapter.initialized = False

        # Act & Assert
        with pytest.raises(RuntimeError):
            await self.adapter.subscribe(
                MessageSubscriptionRequest(
                    topic_pattern=TopicPattern(pattern="test.*"),
                    queue_name="test_queue",
                    callback=AsyncMock(),
                )
            )

    @pytest.mark.asyncio
    async def test_unsubscribe_cancels_consumer(self):
        """Test that unsubscribe cancels the consumer with the correct tag."""
        # Arrange
        consumer_tag = "test_consumer"
        self.adapter.subscribers = {consumer_tag: MagicMock()}

        # Act
        await self.adapter.unsubscribe(consumer_tag)

        # Assert
        self.mock_channel.basic_cancel.assert_called_once_with(consumer_tag)

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_subscriber(self):
        """Test that unsubscribe removes the subscriber from the dictionary."""
        # Arrange
        consumer_tag = "test_consumer"
        self.adapter.subscribers = {consumer_tag: MagicMock()}

        # Act
        await self.adapter.unsubscribe(consumer_tag)

        # Assert
        self.assertNotIn(consumer_tag, self.adapter.subscribers)

    @pytest.mark.asyncio
    async def test_unsubscribe_handles_nonexistent_tag(self):
        """Test that unsubscribe handles a nonexistent consumer tag."""
        # Arrange
        self.adapter.subscribers = {}

        # Act - Should not raise an exception
        await self.adapter.unsubscribe("nonexistent_tag")

    @pytest.mark.asyncio
    async def test_unsubscribe_checks_initialized(self):
        """Test that unsubscribe checks if the adapter is initialized."""
        # Arrange
        self.adapter.initialized = False

        # Act & Assert
        with pytest.raises(RuntimeError):
            await self.adapter.unsubscribe("test_consumer")

    @pytest.mark.asyncio
    async def test_process_message_parses_message_body(self):
        """Test that _process_message correctly parses the message body."""
        # Arrange
        message_data = {"device_id": "device123", "temperature": 75}
        message_body = json.dumps(message_data).encode()

        # Create a mock message
        mock_message = MagicMock(spec=Message)
        mock_message.body = message_body
        mock_message.content_type = "application/json"

        # Create a mock subscriber
        consumer_tag = "test_consumer"
        mock_subscriber = MagicMock()
        mock_subscriber.callback = AsyncMock()

        self.adapter.subscribers = {consumer_tag: mock_subscriber}

        # Act
        await self.adapter._process_message(mock_message, consumer_tag)

        # Assert
        mock_subscriber.callback.assert_called_once()
        # Verify the parsed message was passed to the callback
        actual_data = mock_subscriber.callback.call_args[0][0]
        self.assertEqual(actual_data, message_data)

    @pytest.mark.asyncio
    async def test_process_message_handles_invalid_json(self):
        """Test that _process_message handles invalid JSON in the message body."""
        # Arrange
        message_body = b"invalid json"

        # Create a mock message
        mock_message = MagicMock(spec=Message)
        mock_message.body = message_body
        mock_message.content_type = "application/json"

        # Create a mock subscriber
        consumer_tag = "test_consumer"
        mock_subscriber = MagicMock()
        mock_subscriber.callback = AsyncMock()

        self.adapter.subscribers = {consumer_tag: mock_subscriber}

        # Act - Should not raise an exception
        await self.adapter._process_message(mock_message, consumer_tag)

        # Assert - Callback should not be called for invalid JSON
        mock_subscriber.callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_message_handles_missing_subscriber(self):
        """Test that _process_message handles a missing subscriber."""
        # Arrange
        message_data = {"device_id": "device123", "temperature": 75}
        message_body = json.dumps(message_data).encode()

        # Create a mock message
        mock_message = MagicMock(spec=Message)
        mock_message.body = message_body
        mock_message.content_type = "application/json"

        # No subscribers
        self.adapter.subscribers = {}

        # Act - Should not raise an exception
        await self.adapter._process_message(mock_message, "nonexistent_tag")

    @pytest.mark.asyncio
    async def test_process_message_handles_non_json_content_type(self):
        """Test that _process_message handles a non-JSON content type."""
        # Arrange
        message_body = b"plain text"

        # Create a mock message
        mock_message = MagicMock(spec=Message)
        mock_message.body = message_body
        mock_message.content_type = "text/plain"

        # Create a mock subscriber
        consumer_tag = "test_consumer"
        mock_subscriber = MagicMock()
        mock_subscriber.callback = AsyncMock()

        self.adapter.subscribers = {consumer_tag: mock_subscriber}

        # Act
        await self.adapter._process_message(mock_message, consumer_tag)

        # Assert
        mock_subscriber.callback.assert_called_once()
        # Verify the raw message body was passed to the callback
        actual_data = mock_subscriber.callback.call_args[0][0]
        self.assertEqual(actual_data, message_body.decode())


class TestTopicPattern(unittest.TestCase):
    """Test suite for the TopicPattern class."""

    def test_init_stores_pattern(self):
        """Test that initialization stores the pattern."""
        # Arrange & Act
        pattern = "devices.*.shadow.#"
        topic_pattern = TopicPattern(pattern=pattern)

        # Assert
        self.assertEqual(topic_pattern.pattern, pattern)

    def test_single_wildcard_pattern_replaces_star(self):
        """Test that single_wildcard_pattern replaces * with [^.]+."""
        # Arrange
        pattern = "devices.*.shadow.reported"
        topic_pattern = TopicPattern(pattern=pattern)

        # Act
        result = topic_pattern.single_wildcard_pattern()

        # Assert
        self.assertEqual(result, r"devices\.[^.]+\.shadow\.reported")

    def test_single_wildcard_pattern_escapes_dots(self):
        """Test that single_wildcard_pattern escapes dots in the pattern."""
        # Arrange
        pattern = "devices.device123.shadow.reported"
        topic_pattern = TopicPattern(pattern=pattern)

        # Act
        result = topic_pattern.single_wildcard_pattern()

        # Assert
        self.assertEqual(result, r"devices\.device123\.shadow\.reported")

    def test_multi_wildcard_pattern_replaces_hash(self):
        """Test that multi_wildcard_pattern replaces # with .*."""
        # Arrange
        pattern = "devices.device123.#"
        topic_pattern = TopicPattern(pattern=pattern)

        # Act
        result = topic_pattern.multi_wildcard_pattern()

        # Assert
        self.assertEqual(result, r"devices\.device123\..*")

    def test_multi_wildcard_pattern_escapes_dots(self):
        """Test that multi_wildcard_pattern escapes dots in the pattern."""
        # Arrange
        pattern = "devices.device123.shadow"
        topic_pattern = TopicPattern(pattern=pattern)

        # Act
        result = topic_pattern.multi_wildcard_pattern()

        # Assert
        self.assertEqual(result, r"devices\.device123\.shadow")

    def test_matches_topic_with_exact_match(self):
        """Test that matches_topic returns True for an exact match."""
        # Arrange
        pattern = "devices.device123.shadow.reported"
        topic = "devices.device123.shadow.reported"
        topic_pattern = TopicPattern(pattern=pattern)

        # Act & Assert
        self.assertTrue(topic_pattern.matches_topic(topic))

    def test_matches_topic_with_single_wildcard(self):
        """Test that matches_topic returns True for a match with a single wildcard."""
        # Arrange
        pattern = "devices.*.shadow.reported"
        topic = "devices.device123.shadow.reported"
        topic_pattern = TopicPattern(pattern=pattern)

        # Act & Assert
        self.assertTrue(topic_pattern.matches_topic(topic))

    def test_matches_topic_with_multi_wildcard(self):
        """Test that matches_topic returns True for a match with a multi-level wildcard."""
        # Arrange
        pattern = "devices.device123.#"
        topic = "devices.device123.shadow.reported.temperature"
        topic_pattern = TopicPattern(pattern=pattern)

        # Act & Assert
        self.assertTrue(topic_pattern.matches_topic(topic))

    def test_matches_topic_returns_false_for_mismatch(self):
        """Test that matches_topic returns False for a non-matching topic."""
        # Arrange
        pattern = "devices.device123.shadow.reported"
        topic = "devices.device456.shadow.reported"
        topic_pattern = TopicPattern(pattern=pattern)

        # Act & Assert
        self.assertFalse(topic_pattern.matches_topic(topic))

    def test_matches_topic_with_mixed_wildcards(self):
        """Test that matches_topic works with both single and multi-level wildcards."""
        # Arrange
        pattern = "devices.*.shadow.#"
        topic = "devices.device123.shadow.reported.temperature"
        topic_pattern = TopicPattern(pattern=pattern)

        # Act & Assert
        self.assertTrue(topic_pattern.matches_topic(topic))


class TestMessagePublishRequest(unittest.TestCase):
    """Test suite for the MessagePublishRequest class."""

    def test_init_with_required_parameters(self):
        """Test initialization with only required parameters."""
        # Arrange & Act
        topic = "devices.device123.shadow.reported"
        message = {"temperature": 75}
        request = MessagePublishRequest(topic=topic, message=message)

        # Assert
        self.assertEqual(request.topic, topic)
        self.assertEqual(request.message, message)
        self.assertIsNone(request.message_id)
        self.assertIsNone(request.correlation_id)
        self.assertEqual(request.content_type, "application/json")
        self.assertEqual(request.headers, {})

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        # Arrange & Act
        topic = "devices.device123.shadow.reported"
        message = {"temperature": 75}
        message_id = "test_message_1"
        correlation_id = "test_correlation_1"
        content_type = "application/custom"
        headers = {"source": "test"}

        request = MessagePublishRequest(
            topic=topic,
            message=message,
            message_id=message_id,
            correlation_id=correlation_id,
            content_type=content_type,
            headers=headers,
        )

        # Assert
        self.assertEqual(request.topic, topic)
        self.assertEqual(request.message, message)
        self.assertEqual(request.message_id, message_id)
        self.assertEqual(request.correlation_id, correlation_id)
        self.assertEqual(request.content_type, content_type)
        self.assertEqual(request.headers, headers)


class TestMessageSubscriptionRequest(unittest.TestCase):
    """Test suite for the MessageSubscriptionRequest class."""

    def test_init_with_required_parameters(self):
        """Test initialization with only required parameters."""
        # Arrange & Act
        topic_pattern = TopicPattern(pattern="devices.*.shadow.#")
        queue_name = "test_queue"
        callback = AsyncMock()

        request = MessageSubscriptionRequest(
            topic_pattern=topic_pattern, queue_name=queue_name, callback=callback
        )

        # Assert
        self.assertEqual(request.topic_pattern, topic_pattern)
        self.assertEqual(request.queue_name, queue_name)
        self.assertEqual(request.callback, callback)
        self.assertFalse(request.exclusive)
        self.assertFalse(request.auto_delete)

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        # Arrange & Act
        topic_pattern = TopicPattern(pattern="devices.*.shadow.#")
        queue_name = "test_queue"
        callback = AsyncMock()

        request = MessageSubscriptionRequest(
            topic_pattern=topic_pattern,
            queue_name=queue_name,
            callback=callback,
            exclusive=True,
            auto_delete=True,
        )

        # Assert
        self.assertEqual(request.topic_pattern, topic_pattern)
        self.assertEqual(request.queue_name, queue_name)
        self.assertEqual(request.callback, callback)
        self.assertTrue(request.exclusive)
        self.assertTrue(request.auto_delete)


if __name__ == "__main__":
    unittest.main()
