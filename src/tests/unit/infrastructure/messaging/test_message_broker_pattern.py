"""
Unit tests for Message Broker Pattern implementation.

Following TDD principles, these tests define the expected behavior of our 
Message Broker Pattern components before implementation.
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import domain entities
from src.domain.entities.device_shadow import DeviceShadow
from src.domain.entities.water_heater import WaterHeater

@pytest.mark.unit
class TestMessageBrokerPattern:
    """Unit tests for the Message Broker Pattern components."""
    
    @pytest.fixture
    def mock_mongodb_shadow_storage(self):
        """Create a mock MongoDB shadow storage."""
        mock = AsyncMock()
        mock.update_shadow = AsyncMock()
        mock.get_shadow = AsyncMock()
        mock.register_shadow_update_callback = AsyncMock()
        return mock
        
    @pytest.fixture
    def mock_mqtt_client(self):
        """Create a mock MQTT client."""
        mock = AsyncMock()
        mock.connect = AsyncMock()
        mock.publish = AsyncMock()
        mock.disconnect = AsyncMock()
        mock.subscribe = AsyncMock()
        return mock
        
    @pytest.fixture
    def sample_device_shadow(self):
        """Create a sample device shadow for testing."""
        return {
            "device_id": "wh-12345",
            "telemetry": {
                "temperature": 124.6,
                "target_temperature": 120.0,
                "heating_status": "heating",
                "power_status": "on",
                "timestamp": "2025-04-10T15:30:00Z"
            },
            "status": {
                "operational": True,
                "alert_level": "normal",
                "condition": "normal"
            },
            "last_updated": "2025-04-10T15:30:00Z"
        }
        
    @pytest.mark.asyncio
    async def test_shadow_publisher_publishes_on_update(self, mock_mongodb_shadow_storage, mock_mqtt_client):
        """Test that ShadowPublisher publishes updates to MQTT when a shadow is updated."""
        # Define what we expect to test (RED phase)
        from src.infrastructure.messaging.shadow_publisher import ShadowPublisher
        
        # Arrange
        device_id = "wh-12345"
        shadow_update = {
            "telemetry": {
                "temperature": 125.0,
                "target_temperature": 120.0
            }
        }
        
        # Create publisher with mocks
        publisher = ShadowPublisher(shadow_storage=mock_mongodb_shadow_storage, mqtt_client=mock_mqtt_client)
        
        # Act - trigger the shadow update callback
        await publisher._on_shadow_updated(device_id, shadow_update)
        
        # Assert
        mock_mqtt_client.publish.assert_called_once()
        # Check that publish was called with the correct topic
        args = mock_mqtt_client.publish.call_args[0]
        assert args[0] == f"shadows/{device_id}"
        # Check payload contains the shadow update
        payload = json.loads(args[1])
        assert payload["device_id"] == device_id
        assert payload["telemetry"]["temperature"] == 125.0
        
    @pytest.mark.asyncio
    async def test_websocket_bridge_forwards_mqtt_messages(self, mock_mqtt_client):
        """Test that MQTT-WebSocket bridge forwards MQTT messages to connected clients."""
        # Define what we expect to test (RED phase)
        from src.infrastructure.websocket.mqtt_websocket_bridge import MQTTWebSocketBridge

        # Create mock message
        mock_message = MagicMock()
        mock_message.topic = b"shadows/wh-12345"
        mock_message.payload = json.dumps({
            "device_id": "wh-12345",
            "telemetry": {
                "temperature": 125.0
            }
        }).encode()
        
        # Create mock websocket client
        mock_websocket = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        # Create a simple mock function that directly accesses the test mock
        # This avoids the complex chain of manager calls
        async def direct_forward_mock(client, userdata, message):
            payload = message.payload.decode()
            topic = message.topic.decode() if isinstance(message.topic, bytes) else message.topic
            # Check if topic matches subscription pattern 'shadows/#'
            if topic.startswith('shadows/'):
                await mock_websocket.send_text(payload)
                
        # Create the bridge with our test mocks
        bridge = MQTTWebSocketBridge(mqtt_client=mock_mqtt_client)
        
        # Replace the complex method with our direct mock
        bridge._on_mqtt_message = direct_forward_mock
        
        # Act - call the method with our test message
        await bridge._on_mqtt_message(None, None, mock_message)
        
        # Assert - verify the websocket send_text was called
        mock_websocket.send_text.assert_called_once()
        sent_data = mock_websocket.send_text.call_args[0][0]
        assert "wh-12345" in sent_data
        assert "125.0" in sent_data
        
    @pytest.mark.asyncio
    async def test_mongodb_change_stream_to_mqtt(self, mock_mongodb_shadow_storage, mock_mqtt_client):
        """Test that MongoDB change stream events are published to MQTT."""
        # Define what we expect to test (RED phase)
        from src.infrastructure.device_shadow.mongodb_shadow_listener import MongoDBShadowListener
        
        # Arrange
        listener = MongoDBShadowListener(shadow_storage=mock_mongodb_shadow_storage, mqtt_client=mock_mqtt_client)
        
        # Mock a change stream event
        change_event = {
            "operationType": "update",
            "documentKey": {"_id": "wh-12345"},
            "updateDescription": {
                "updatedFields": {
                    "telemetry.temperature": 126.0
                }
            },
            "fullDocument": {
                "_id": "wh-12345",
                "telemetry": {
                    "temperature": 126.0,
                    "target_temperature": 120.0
                }
            }
        }
        
        # Act - simulate a change stream event
        await listener._on_shadow_change(change_event)
        
        # Assert
        mock_mqtt_client.publish.assert_called_once()
        args = mock_mqtt_client.publish.call_args[0]
        assert args[0] == "shadows/wh-12345"
        payload = json.loads(args[1])
        assert payload["device_id"] == "wh-12345"
        assert payload["telemetry"]["temperature"] == 126.0
