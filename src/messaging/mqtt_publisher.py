"""
MQTT Publisher - Component responsible for publishing messages to MQTT brokers
Part of the Message Broker Pattern for IoTSphere
"""
import asyncio
import json
import logging
from typing import Any, Dict, Optional, Union, Callable

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

class MQTTPublisher:
    """
    MQTT Publisher responsible for publishing messages to an MQTT broker
    
    Following Clean Architecture principles:
    - This class is part of the interface adapter layer
    - It abstracts the details of MQTT communication from the business logic
    - Implements retry logic and connection management
    """
    
    def __init__(self, client: Optional[Any] = None, 
                 host: str = "localhost", 
                 port: int = 1883,
                 client_id: str = "iotsphere-publisher",
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 use_tls: bool = False,
                 ca_cert: Optional[str] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Initialize the MQTT publisher
        
        Args:
            client: Optional pre-configured MQTT client (for testing)
            host: MQTT broker hostname
            port: MQTT broker port
            client_id: Client ID for MQTT connection
            username: Optional username for authentication
            password: Optional password for authentication
            use_tls: Whether to use TLS/SSL
            ca_cert: CA certificate file path (for TLS)
            max_retries: Maximum number of connection/publish retries
            retry_delay: Delay between retries in seconds
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.ca_cert = ca_cert
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Connection status
        self._connected = False
        self._connecting = False
        self._connection_lock = asyncio.Lock()
        
        # Use provided client or create a new one
        self._mqtt_client = client if client else self._create_mqtt_client()
        
        logger.info(f"MQTT Publisher initialized for {host}:{port}")
        
    def _create_mqtt_client(self) -> mqtt.Client:
        """
        Create and configure MQTT client
        
        Returns:
            Configured MQTT client
        """
        # Create client
        client = mqtt.Client(client_id=self.client_id)
        
        # Configure authentication if provided
        if self.username and self.password:
            client.username_pw_set(self.username, self.password)
            
        # Configure TLS if enabled
        if self.use_tls:
            client.tls_set(ca_certs=self.ca_cert)
            
        # Configure callbacks
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        
        return client
        
    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback for when the client connects to the broker
        
        Args:
            client: MQTT client instance
            userdata: User data
            flags: Connection flags
            rc: Result code
        """
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self._connected = True
        else:
            logger.error(f"Failed to connect to MQTT broker, rc={rc}")
            self._connected = False
            
    def _on_disconnect(self, client, userdata, rc):
        """
        Callback for when the client disconnects from the broker
        
        Args:
            client: MQTT client instance
            userdata: User data
            rc: Result code
        """
        logger.info("Disconnected from MQTT broker")
        self._connected = False
        
    async def connect(self) -> bool:
        """
        Connect to the MQTT broker with retry logic
        
        Returns:
            True if connected successfully, False otherwise
        """
        async with self._connection_lock:
            if self._connected:
                return True
                
            if self._connecting:
                return False
                
            self._connecting = True
            
            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.info(f"Connecting to MQTT broker (attempt {attempt}/{self.max_retries})")
                    
                    # Connect to broker (using thread executor since this is blocking)
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, 
                        lambda: self._mqtt_client.connect(self.host, self.port, keepalive=60)
                    )
                    
                    # Start the loop to process callbacks
                    self._mqtt_client.loop_start()
                    
                    # Wait for connection to be established
                    for _ in range(10):  # Wait up to 1 second
                        if self._connected:
                            break
                        await asyncio.sleep(0.1)
                        
                    if self._connected:
                        self._connecting = False
                        return True
                        
                except Exception as e:
                    logger.error(f"Error connecting to MQTT broker: {str(e)}")
                    
                # Wait before retrying
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                    
            self._connecting = False
            return False
            
    async def disconnect(self) -> None:
        """
        Disconnect from the MQTT broker
        """
        if not self._connected:
            return
            
        try:
            # Disconnect (using thread executor since this is blocking)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._mqtt_client.disconnect)
            self._mqtt_client.loop_stop()
            self._connected = False
            logger.info("Disconnected from MQTT broker")
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {str(e)}")
            
    async def publish(self, topic: str, payload: Union[str, Dict[str, Any]], 
                     qos: int = 1, retain: bool = False) -> bool:
        """
        Publish a message to the MQTT broker with retry logic
        
        Args:
            topic: MQTT topic
            payload: Message payload (string or dict that will be JSON-encoded)
            qos: Quality of Service (0, 1, or 2)
            retain: Whether to retain the message
            
        Returns:
            True if published successfully, False otherwise
        """
        # Ensure we have a string payload
        if isinstance(payload, dict):
            payload = json.dumps(payload)
            
        # Ensure we're connected
        if not self._connected:
            if not await self.connect():
                logger.error("Failed to connect to MQTT broker for publishing")
                return False
                
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Publishing to {topic} (attempt {attempt}/{self.max_retries})")
                
                # Publish message (using thread executor since this is blocking)
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self._mqtt_client.publish(topic, payload, qos=qos, retain=retain)
                )
                
                # Check result
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.debug(f"Successfully published to {topic}")
                    return True
                else:
                    logger.warning(f"Failed to publish to {topic}, rc={result.rc}")
                    
            except Exception as e:
                logger.error(f"Error publishing to {topic}: {str(e)}")
                
            # Wait before retrying
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay)
                
        return False
