"""
Message Broker Adapter Implementation.

This module contains the implementation of the Message Broker Adapter,
which provides a clean interface for publishing and consuming events
through a message broker (like Kafka or similar systems).
"""
import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from confluent_kafka import Consumer, KafkaError, KafkaException, Producer

from src.domain.events.event import Event
from src.gateways.message_broker import MessageBroker

logger = logging.getLogger(__name__)


class MessageBrokerAdapter(MessageBroker):
    """Message Broker Adapter implementation.

    This adapter provides a clean interface for interacting with message brokers,
    implementing the MessageBroker interface from the gateway layer. It abstracts
    the details of the specific message broker used (e.g., Kafka).
    """

    def __init__(
        self,
        bootstrap_servers: str,
        client_id: str,
        group_id: Optional[str] = None,
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = True,
    ):
        """Initialize the Message Broker Adapter.

        Args:
            bootstrap_servers: Comma-separated list of broker addresses
            client_id: Client identifier for this producer/consumer
            group_id: Consumer group ID (only needed for consuming)
            auto_offset_reset: Where to start consuming if no offset is stored
            enable_auto_commit: Whether to automatically commit offsets
        """
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.group_id = group_id
        self.auto_offset_reset = auto_offset_reset
        self.enable_auto_commit = enable_auto_commit

        self.producer: Optional[Producer] = None
        self.consumer: Optional[Consumer] = None
        self.topic_handlers: Dict[str, Callable] = {}
        self.is_consuming = False
        self.consumer_task = None

    def init_producer(self) -> None:
        """Initialize the Kafka producer.

        This method initializes the Kafka producer with the appropriate configuration.
        It should be called before publishing any events.
        """
        if self.producer is not None:
            return

        conf = {
            "bootstrap.servers": self.bootstrap_servers,
            "client.id": f"{self.client_id}-producer",
        }

        self.producer = Producer(conf)
        logger.info(
            f"Initialized Kafka producer with bootstrap servers: {self.bootstrap_servers}"
        )

    def init_consumer(self, topics: List[str]) -> None:
        """Initialize the Kafka consumer.

        This method initializes the Kafka consumer with the appropriate configuration
        and subscribes to the specified topics.

        Args:
            topics: List of topics to subscribe to
        """
        if self.consumer is not None:
            return

        if not self.group_id:
            raise ValueError("group_id is required for consumer initialization")

        conf = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "client.id": f"{self.client_id}-consumer",
            "auto.offset.reset": self.auto_offset_reset,
            "enable.auto.commit": self.enable_auto_commit,
        }

        self.consumer = Consumer(conf)
        self.consumer.subscribe(topics)
        logger.info(f"Initialized Kafka consumer for topics: {topics}")

    def publish_event(
        self, topic: str, event: Event, key: Optional[str] = None
    ) -> None:
        """Publish an event to the specified topic.

        This method publishes an event to the specified topic in the message broker.
        If the producer is not initialized, it will be initialized before publishing.

        Args:
            topic: Topic to publish the event to
            event: Event object to publish
            key: Optional key for the message (e.g., device ID)
        """
        if self.producer is None:
            self.init_producer()

        # Convert event to JSON string
        event_data = event.to_dict()
        event_data["event_type"] = event.__class__.__name__
        event_json = json.dumps(event_data)

        # Publish the event
        try:
            self.producer.produce(
                topic=topic,
                value=event_json.encode("utf-8"),
                key=key.encode("utf-8") if key else None,
                callback=self._delivery_callback,
            )
            # Trigger any queued messages to be sent
            self.producer.poll(0)
            logger.debug(f"Published event to topic {topic}: {event_data}")
        except KafkaException as e:
            logger.error(f"Failed to publish event to topic {topic}: {e}")
            raise

    def _delivery_callback(self, err, msg) -> None:
        """Delivery callback for producer.

        Args:
            err: Error object if delivery failed
            msg: Message object
        """
        if err:
            logger.error(f"Failed to deliver message: {err}")
        else:
            logger.debug(
                f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
            )

    def register_handler(self, topic: str, handler: Callable) -> None:
        """Register a handler for a specific topic.

        This method registers a callback function to handle messages from a specific topic.
        The handler should take a message value (dictionary) as its only argument.

        Args:
            topic: Topic to register the handler for
            handler: Callback function to handle messages from the topic
        """
        self.topic_handlers[topic] = handler
        logger.info(f"Registered handler for topic: {topic}")

    async def start_consuming(self) -> None:
        """Start consuming messages from subscribed topics.

        This method starts an asynchronous task to consume messages from the
        subscribed topics and pass them to the registered handlers.
        """
        if self.consumer is None:
            raise RuntimeError("Consumer not initialized. Call init_consumer first.")

        if self.is_consuming:
            return

        self.is_consuming = True
        self.consumer_task = asyncio.create_task(self._consume_loop())
        logger.info("Started consuming messages")

    async def stop_consuming(self) -> None:
        """Stop consuming messages.

        This method stops the message consumption loop and closes the consumer.
        """
        if not self.is_consuming or self.consumer_task is None:
            return

        self.is_consuming = False
        if self.consumer_task:
            self.consumer_task.cancel()
            try:
                await self.consumer_task
            except asyncio.CancelledError:
                pass

        if self.consumer:
            self.consumer.close()
            self.consumer = None

        logger.info("Stopped consuming messages")

    async def _consume_loop(self) -> None:
        """Consumer loop for processing messages from the message broker.

        This method continually polls the message broker for new messages and
        passes them to the appropriate handlers.
        """
        try:
            while self.is_consuming:
                msg = self.consumer.poll(1.0)

                if msg is None:
                    await asyncio.sleep(0.01)  # Yield to other tasks
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        logger.debug(
                            f"Reached end of partition {msg.topic()} [{msg.partition()}]"
                        )
                    else:
                        # Error
                        logger.error(f"Error while consuming message: {msg.error()}")
                else:
                    # Process message
                    topic = msg.topic()
                    value = json.loads(msg.value().decode("utf-8"))

                    if topic in self.topic_handlers:
                        try:
                            await self._process_message(topic, value)
                        except Exception as e:
                            logger.error(
                                f"Error processing message from topic {topic}: {e}"
                            )
                    else:
                        logger.warning(f"No handler registered for topic: {topic}")
        except asyncio.CancelledError:
            # Task was cancelled, just exit
            pass
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")
            self.is_consuming = False

    async def _process_message(self, topic: str, message: Dict[str, Any]) -> None:
        """Process a message from the message broker.

        This method calls the appropriate handler for a message from a specific topic.

        Args:
            topic: Topic the message was received from
            message: Message value as a dictionary
        """
        handler = self.topic_handlers.get(topic)
        if handler:
            # Handle the message
            if asyncio.iscoroutinefunction(handler):
                await handler(message)
            else:
                handler(message)
            logger.debug(
                f"Processed message from topic {topic}: {message.get('event_type', 'Unknown')}"
            )
        else:
            logger.warning(f"No handler found for topic: {topic}")

    def close(self) -> None:
        """Close the producer and consumer connections.

        This method should be called when the adapter is no longer needed to
        clean up resources.
        """
        if self.producer:
            self.producer.flush()
            logger.info("Flushed and closed Kafka producer")

        # Consumer is closed in stop_consuming
