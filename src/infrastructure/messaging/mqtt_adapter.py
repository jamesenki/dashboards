#!/usr/bin/env python3
"""
MQTT Adapter for IoTSphere

This module provides an adapter between MQTT protocol and the internal message bus,
bridging IoT devices using MQTT protocol with the event-driven architecture of IoTSphere.
"""
import os
import json
import logging
import uuid
import paho.mqtt.client as mqtt
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default MQTT configuration
DEFAULT_MQTT_BROKER = os.environ.get('MQTT_BROKER', 'localhost')
DEFAULT_MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
DEFAULT_MQTT_USERNAME = os.environ.get('MQTT_USERNAME', None)
DEFAULT_MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD', None)
DEFAULT_MQTT_CLIENT_ID = f"iotsphere-mqtt-adapter-{uuid.uuid4().hex[:8]}"

class MqttAdapter:
    """
    Adapter between MQTT protocol and internal message bus
    
    This adapter:
    - Subscribes to device topics on MQTT broker
    - Translates MQTT messages to internal event format
    - Publishes events to the internal message bus
    - Sends commands to devices via MQTT
    """
    
    def __init__(self, mqtt_client=None, message_bus=None):
        """
        Initialize MQTT adapter
        
        Args:
            mqtt_client: Optional pre-configured MQTT client
            message_bus: Internal message bus client
        """
        # Set up MQTT client
        self.mqtt_client = mqtt_client or mqtt.Client(DEFAULT_MQTT_CLIENT_ID)
        if DEFAULT_MQTT_USERNAME and DEFAULT_MQTT_PASSWORD:
            self.mqtt_client.username_pw_set(DEFAULT_MQTT_USERNAME, DEFAULT_MQTT_PASSWORD)
        
        # Set message callback
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_connect = self.on_connect
        
        # Store message bus
        self.message_bus = message_bus
        
        # Topic patterns
        self.device_telemetry_topic = "iotsphere/devices/+/telemetry"
        self.device_event_topic = "iotsphere/devices/+/events"
        self.device_command_topic = "iotsphere/devices/+/commands"
        self.device_command_response_topic = "iotsphere/devices/+/command_response"
        
        logger.info("Initialized MQTT adapter")
    
    def start(self):
        """Connect to MQTT broker and start processing messages"""
        try:
            logger.info(f"Connecting to MQTT broker at {DEFAULT_MQTT_BROKER}:{DEFAULT_MQTT_PORT}")
            self.mqtt_client.connect(DEFAULT_MQTT_BROKER, DEFAULT_MQTT_PORT)
            
            # Subscribe to device topics
            self.mqtt_client.subscribe(self.device_telemetry_topic)
            self.mqtt_client.subscribe(self.device_event_topic)
            self.mqtt_client.subscribe(self.device_command_response_topic)
            
            # Start MQTT loop in the background
            self.mqtt_client.loop_start()
            
            logger.info("MQTT adapter started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MQTT adapter: {e}")
            return False
    
    def stop(self):
        """Disconnect from MQTT broker and stop processing messages"""
        try:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT adapter stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping MQTT adapter: {e}")
            return False
    
    def on_connect(self, client, userdata, flags, rc):
        """Handle connection to MQTT broker"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            
            # Re-subscribe to topics
            self.mqtt_client.subscribe(self.device_telemetry_topic)
            self.mqtt_client.subscribe(self.device_event_topic)
            self.mqtt_client.subscribe(self.device_command_response_topic)
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def on_message(self, client, userdata, message):
        """
        Handle incoming MQTT messages
        
        Args:
            client: MQTT client instance
            userdata: User data (not used)
            message: MQTT message object
        """
        try:
            # Decode message payload
            payload = message.payload.decode('utf-8')
            data = json.loads(payload)
            topic = message.topic
            
            # Extract device ID from topic
            # Topic format: iotsphere/devices/{device_id}/{message_type}
            topic_parts = topic.split('/')
            if len(topic_parts) >= 4:
                device_id = topic_parts[2]
                message_type = topic_parts[3]
                
                # Forward message to appropriate handler
                if message_type == "telemetry":
                    self._handle_telemetry(device_id, data)
                elif message_type == "events":
                    self._handle_event(device_id, data)
                elif message_type == "command_response":
                    self._handle_command_response(device_id, data)
                
            else:
                logger.warning(f"Received message with invalid topic format: {topic}")
                
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON message: {message.payload}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _handle_telemetry(self, device_id, data):
        """
        Process telemetry data from device
        
        Args:
            device_id (str): Device identifier
            data (dict): Telemetry data
        """
        if not self.message_bus:
            logger.warning("No message bus available for telemetry forwarding")
            return
        
        # Ensure device_id is consistent
        if "device_id" in data and data["device_id"] != device_id:
            logger.warning(f"Device ID mismatch: {device_id} vs {data['device_id']}")
        
        # Create event for internal message bus
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "device.telemetry",
            "device_id": device_id,
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
            "data": {k: v for k, v in data.items() if k not in ["device_id", "timestamp"]},
            "simulated": data.get("simulated", False)
        }
        
        # Publish to message bus
        self.message_bus.publish("device.telemetry", event)
        logger.debug(f"Forwarded telemetry from device {device_id}")
    
    def _handle_event(self, device_id, data):
        """
        Process event from device
        
        Args:
            device_id (str): Device identifier
            data (dict): Event data
        """
        if not self.message_bus:
            logger.warning("No message bus available for event forwarding")
            return
        
        # Ensure device_id is consistent
        if "device_id" in data and data["device_id"] != device_id:
            logger.warning(f"Device ID mismatch in event: {device_id} vs {data['device_id']}")
        
        # Create event for internal message bus
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": data.get("event_type", "unknown"),
            "device_id": device_id,
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
            "severity": data.get("severity", "info"),
            "message": data.get("message", ""),
            "details": data.get("details", {}),
            "simulated": data.get("simulated", False)
        }
        
        # Publish to message bus
        self.message_bus.publish("device.event", event)
        logger.info(f"Forwarded event from device {device_id}: {event['event_type']} - {event['message']}")
    
    def _handle_command_response(self, device_id, data):
        """
        Process command response from device
        
        Args:
            device_id (str): Device identifier
            data (dict): Command response data
        """
        if not self.message_bus:
            logger.warning("No message bus available for command response forwarding")
            return
        
        # Ensure device_id is consistent
        if "device_id" in data and data["device_id"] != device_id:
            logger.warning(f"Device ID mismatch in command response: {device_id} vs {data['device_id']}")
        
        # Create event for internal message bus
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "device.command_response",
            "device_id": device_id,
            "command_id": data.get("command_id"),
            "command": data.get("command"),
            "status": data.get("status"),
            "message": data.get("message", ""),
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
            "simulated": data.get("simulated", False)
        }
        
        # Publish to message bus
        self.message_bus.publish("device.command_response", event)
        logger.info(f"Forwarded command response from device {device_id}: {event['status']}")
    
    def publish_command(self, device_id, command):
        """
        Send command to device via MQTT
        
        Args:
            device_id (str): Target device identifier
            command (dict): Command data
            
        Returns:
            str: Command ID
        """
        try:
            # Generate command ID if not provided
            if "command_id" not in command:
                command["command_id"] = str(uuid.uuid4())
            
            # Add timestamp if not present
            if "timestamp" not in command:
                command["timestamp"] = datetime.utcnow().isoformat()
            
            # Publish to device command topic
            topic = f"iotsphere/devices/{device_id}/commands"
            payload = json.dumps(command)
            self.mqtt_client.publish(topic, payload)
            
            logger.info(f"Sent command to device {device_id}: {command.get('command')}")
            return command["command_id"]
            
        except Exception as e:
            logger.error(f"Error sending command to device {device_id}: {e}")
            return None
