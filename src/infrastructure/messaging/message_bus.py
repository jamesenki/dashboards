#!/usr/bin/env python3
"""
Message Bus for IoTSphere

This module provides a message bus implementation for IoTSphere's event-driven architecture.
It supports both local in-memory messaging for testing and RabbitMQ for production use.
"""
import json
import logging
import os
import threading
import uuid
from datetime import datetime

import pika
from pika.exceptions import AMQPConnectionError

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# RabbitMQ connection parameters
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "iotsphere")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "iotsphere")
RABBITMQ_VHOST = os.environ.get("RABBITMQ_VHOST", "/")


class LocalMessageBus:
    """
    In-memory message bus implementation for testing or simple deployments.

    This implementation:
    - Stores subscribers in memory
    - Processes messages in the same thread (synchronous)
    - Does not require external infrastructure
    """

    def __init__(self):
        """Initialize local message bus"""
        self.subscribers = {}
        logger.info("Initialized local message bus")

    def publish(self, topic, message):
        """
        Publish message to topic

        Args:
            topic (str): Message topic
            message (dict): Message content

        Returns:
            bool: Success status
        """
        if topic not in self.subscribers:
            # No subscribers for this topic
            return True

        # Notify each subscriber
        for callback in self.subscribers[topic]:
            try:
                callback(topic, message)
            except Exception as e:
                logger.error(f"Error in subscriber callback: {e}")

        return True

    def subscribe(self, topic, callback):
        """
        Subscribe to topic

        Args:
            topic (str): Topic to subscribe to
            callback (callable): Function to call when message is received

        Returns:
            bool: Success status
        """
        if topic not in self.subscribers:
            self.subscribers[topic] = []

        self.subscribers[topic].append(callback)
        return True

    def unsubscribe(self, topic, callback):
        """
        Unsubscribe from topic

        Args:
            topic (str): Topic to unsubscribe from
            callback (callable): Callback function to remove

        Returns:
            bool: Success status
        """
        if topic not in self.subscribers:
            return False

        if callback in self.subscribers[topic]:
            self.subscribers[topic].remove(callback)
            return True

        return False

    def start(self):
        """Start the message bus (no-op for local bus)"""
        logger.info("Local message bus started")
        return True

    def stop(self):
        """Stop the message bus (no-op for local bus)"""
        logger.info("Local message bus stopped")
        return True


class RabbitMqMessageBus:
    """
    RabbitMQ implementation of message bus for production use.

    This implementation:
    - Uses RabbitMQ for reliable message delivery
    - Supports multiple consumers for horizontal scaling
    - Handles reconnection to RabbitMQ automatically
    """

    def __init__(self):
        """Initialize RabbitMQ message bus"""
        # RabbitMQ connection parameters
        self.credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        self.connection_params = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            virtual_host=RABBITMQ_VHOST,
            credentials=self.credentials,
        )

        # Connection and channel
        self.connection = None
        self.channel = None

        # Subscriber callbacks (topic -> list of callbacks)
        self.subscribers = {}

        # Consumer tags (topic -> consumer_tag)
        self.consumer_tags = {}

        # Connection state
        self.connected = False
        self.connection_thread = None
        self.running = False

        logger.info(
            f"Initialized RabbitMQ message bus ({RABBITMQ_HOST}:{RABBITMQ_PORT})"
        )

    def _connect(self):
        """
        Connect to RabbitMQ and set up channel

        Returns:
            bool: Success status
        """
        try:
            # Connect to RabbitMQ
            self.connection = pika.BlockingConnection(self.connection_params)
            self.channel = self.connection.channel()

            # Create exchange for topic-based routing
            self.channel.exchange_declare(
                exchange="iotsphere", exchange_type="topic", durable=True
            )

            self.connected = True
            logger.info("Connected to RabbitMQ")

            # Resubscribe to all topics
            for topic in self.subscribers:
                self._subscribe_topic(topic)

            return True

        except AMQPConnectionError as e:
            logger.error(f"RabbitMQ connection error: {e}")
            self.connected = False
            return False

        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {e}")
            self.connected = False
            return False

    def _subscribe_topic(self, topic):
        """
        Subscribe to a topic in RabbitMQ

        Args:
            topic (str): Topic to subscribe to

        Returns:
            bool: Success status
        """
        try:
            # Create queue for this consumer
            # Use exclusive queue to avoid duplicate message processing
            result = self.channel.queue_declare("", exclusive=True)
            queue_name = result.method.queue

            # Bind queue to exchange with topic routing key
            self.channel.queue_bind(
                exchange="iotsphere", queue=queue_name, routing_key=topic
            )

            # Set up consumer
            consumer_tag = self.channel.basic_consume(
                queue=queue_name, on_message_callback=self._on_message, auto_ack=True
            )

            # Store consumer tag for later cancellation
            self.consumer_tags[topic] = (consumer_tag, queue_name)

            logger.info(f"Subscribed to topic: {topic}")
            return True

        except Exception as e:
            logger.error(f"Error subscribing to topic {topic}: {e}")
            return False

    def _on_message(self, channel, method, properties, body):
        """
        Handle incoming RabbitMQ message

        Args:
            channel: RabbitMQ channel
            method: RabbitMQ method
            properties: RabbitMQ properties
            body: Message body
        """
        try:
            # Decode message
            message = json.loads(body)

            # Get topic from routing key
            topic = method.routing_key

            # Notify subscribers
            if topic in self.subscribers:
                for callback in self.subscribers[topic]:
                    try:
                        callback(topic, message)
                    except Exception as e:
                        logger.error(f"Error in subscriber callback: {e}")

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON message: {body}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _connection_monitor(self):
        """Monitor connection and reconnect if necessary"""
        while self.running:
            if not self.connected:
                logger.info("Attempting to reconnect to RabbitMQ...")
                self._connect()

            # Check connection every 5 seconds
            for _ in range(50):  # 5 seconds with 100ms checks
                if not self.running:
                    break
                time.sleep(0.1)

    def publish(self, topic, message):
        """
        Publish message to topic

        Args:
            topic (str): Message topic
            message (dict): Message content

        Returns:
            bool: Success status
        """
        try:
            if not self.connected:
                logger.warning("Not connected to RabbitMQ, attempting to reconnect...")
                if not self._connect():
                    return False

            # Convert message to JSON
            body = json.dumps(message)

            # Publish to exchange with topic routing key
            self.channel.basic_publish(
                exchange="iotsphere",
                routing_key=topic,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type="application/json",
                ),
            )

            return True

        except Exception as e:
            logger.error(f"Error publishing message to topic {topic}: {e}")
            self.connected = False
            return False

    def subscribe(self, topic, callback):
        """
        Subscribe to topic

        Args:
            topic (str): Topic to subscribe to
            callback (callable): Function to call when message is received

        Returns:
            bool: Success status
        """
        # Store callback
        if topic not in self.subscribers:
            self.subscribers[topic] = []

        self.subscribers[topic].append(callback)

        # Subscribe to topic in RabbitMQ if connected
        if self.connected and topic not in self.consumer_tags:
            self._subscribe_topic(topic)

        return True

    def unsubscribe(self, topic, callback):
        """
        Unsubscribe from topic

        Args:
            topic (str): Topic to unsubscribe from
            callback (callable): Callback function to remove

        Returns:
            bool: Success status
        """
        if topic not in self.subscribers:
            return False

        if callback in self.subscribers[topic]:
            self.subscribers[topic].remove(callback)

            # If no more subscribers, unsubscribe from RabbitMQ
            if not self.subscribers[topic] and topic in self.consumer_tags:
                try:
                    consumer_tag, queue_name = self.consumer_tags[topic]
                    self.channel.basic_cancel(consumer_tag)
                    self.channel.queue_delete(queue_name)
                    del self.consumer_tags[topic]
                except Exception as e:
                    logger.error(f"Error unsubscribing from topic {topic}: {e}")

            return True

        return False

    def start(self):
        """Start the message bus"""
        try:
            # Connect to RabbitMQ
            if not self.connected:
                self._connect()

            # Start connection monitor thread
            self.running = True
            self.connection_thread = threading.Thread(
                target=self._connection_monitor, daemon=True
            )
            self.connection_thread.start()

            logger.info("RabbitMQ message bus started")
            return True

        except Exception as e:
            logger.error(f"Error starting RabbitMQ message bus: {e}")
            return False

    def stop(self):
        """Stop the message bus"""
        try:
            # Stop connection monitor
            self.running = False

            if self.connection_thread:
                self.connection_thread.join(timeout=2.0)

            # Close connection
            if self.connection and self.connection.is_open:
                self.connection.close()

            self.connected = False
            logger.info("RabbitMQ message bus stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping RabbitMQ message bus: {e}")
            return False


# Factory function to create appropriate message bus
def create_message_bus(bus_type="rabbitmq"):
    """
    Create message bus instance

    Args:
        bus_type (str): Type of message bus ('local' or 'rabbitmq')

    Returns:
        MessageBus: Message bus instance
    """
    if bus_type.lower() == "local":
        return LocalMessageBus()
    else:
        return RabbitMqMessageBus()
