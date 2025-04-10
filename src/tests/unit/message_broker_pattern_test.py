"""
Test suite for Message Broker Pattern implementation
Following TDD principles to ensure proper design is enforced
"""
import asyncio
import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import components to test
from src.services.message_service import MessageService
from src.storage.mongodb_shadow_storage import MongoDBShadowStorage
from src.messaging.mqtt_publisher import MQTTPublisher
from src.messaging.websocket_server import WebSocketServer

# Test categories aligned with Clean Architecture
@pytest.mark.unit
class TestMessageBrokerPattern:
    """Unit tests for message broker pattern components"""

    @pytest.fixture
    async def mock_mqtt_client(self):
        """Mock MQTT client for testing"""
        client = AsyncMock()
        client.connect = AsyncMock()
        client.publish = AsyncMock()
        client.subscribe = AsyncMock()
        client.disconnect = AsyncMock()
        return client

    @pytest.fixture
    async def mock_mongo_client(self):
        """Mock MongoDB client for testing"""
        client = AsyncMock()
        db = AsyncMock()
        collection = AsyncMock()
        client.__getitem__.return_value = db
        db.__getitem__.return_value = collection
        collection.find_one = AsyncMock()
        collection.update_one = AsyncMock()
        collection.insert_one = AsyncMock()
        return client

    @pytest.fixture
    async def message_service(self, mock_mqtt_client, mock_mongo_client):
        """Create MessageService with mocked dependencies"""
        with patch('src.storage.mongodb_shadow_storage.MongoClient', return_value=mock_mongo_client):
            storage = MongoDBShadowStorage()
            publisher = MQTTPublisher(client=mock_mqtt_client)
            service = MessageService(storage=storage, publisher=publisher)
            yield service

    # Test External Message Processing
    async def test_external_message_processing(self, message_service, mock_mqtt_client):
        """Test that external messages are processed and stored in MongoDB"""
        # Arrange
        device_id = "wh-12345"
        message = {
            "device_id": device_id,
            "temperature": 124.6,
            "target_temperature": 120.0,
            "status": "ONLINE",
            "mode": "ECO",
            "timestamp": "2025-04-10T15:30:00Z"
        }
        message_service.storage.update_shadow = AsyncMock()
        
        # Act
        await message_service.process_device_message(json.dumps(message))
        
        # Assert
        message_service.storage.update_shadow.assert_called_once()
        call_args = message_service.storage.update_shadow.call_args[0]
        assert call_args[0] == device_id
        assert "temperature" in call_args[1]
        assert call_args[1]["temperature"] == 124.6

    # Test MongoDB to MQTT Publishing
    async def test_mongodb_to_mqtt_publishing(self, message_service, mock_mqtt_client):
        """Test that MongoDB shadow updates are published to internal MQTT broker"""
        # Arrange
        device_id = "wh-12345"
        shadow_update = {
            "temperature": 125.0,
            "target_temperature": 120.0,
            "status": "ONLINE",
            "mode": "ECO",
            "timestamp": "2025-04-10T15:31:00Z"
        }
        message_service.publisher.publish = AsyncMock()
        
        # Act
        await message_service.storage.on_shadow_updated(device_id, shadow_update)
        
        # Assert
        message_service.publisher.publish.assert_called_once()
        call_args = message_service.publisher.publish.call_args
        assert call_args[0][0] == f"shadows/{device_id}"  # Topic
        published_message = json.loads(call_args[0][1])  # Message payload
        assert published_message["device_id"] == device_id
        assert published_message["temperature"] == 125.0

    # Test WebSocket Server Integration
    @patch('src.messaging.websocket_server.WebSocketServer._setup_mqtt_client')
    async def test_websocket_mqtt_subscription(self, mock_setup, mock_mqtt_client):
        """Test that WebSocket server subscribes to MQTT topics and forwards to clients"""
        # Arrange
        websocket_server = WebSocketServer()
        websocket_server.mqtt_client = mock_mqtt_client
        mock_client_socket = MagicMock()
        websocket_server.connected_clients = {"client1": {"socket": mock_client_socket, "subscriptions": ["shadows/#"]}}
        
        # Define the MQTT message
        mqtt_message = MagicMock()
        mqtt_message.topic = b"shadows/wh-12345"
        mqtt_message.payload = json.dumps({
            "device_id": "wh-12345",
            "temperature": 125.0,
            "timestamp": "2025-04-10T15:32:00Z"
        }).encode()
        
        # Act
        await websocket_server._on_mqtt_message(None, None, mqtt_message)
        
        # Assert
        mock_client_socket.send.assert_called_once()
        sent_message = mock_client_socket.send.call_args[0][0]
        assert "wh-12345" in sent_message
        assert "125.0" in sent_message

    # Test Frontend Updates from WebSocket
    @pytest.mark.frontend
    def test_frontend_websocket_handling(self):
        """Test that frontend properly handles WebSocket messages"""
        # This would be tested using a JavaScript test framework
        # Using pytest-playwright or Cypress
        # Testing here in comments for clarity:
        """
        describe('WebSocket Integration', () => {
            it('should update UI components when receiving websocket messages', () => {
                // Arrange - mock websocket
                const mockWebSocket = new MockWebSocket();
                window.shadowWebSocket = mockWebSocket;
                
                // Setup spy on UI update function
                const uiUpdateSpy = cy.spy(window.WaterHeaterList.prototype, 'updateHeaterData');
                
                // Act - simulate receiving a websocket message
                mockWebSocket.triggerMessage(JSON.stringify({
                    device_id: 'wh-12345',
                    temperature: 125.0,
                    target_temperature: 120.0,
                    status: 'ONLINE',
                    mode: 'ECO'
                }));
                
                // Assert
                expect(uiUpdateSpy).to.be.calledWith(sinon.match({
                    device_id: 'wh-12345',
                    temperature: 125.0
                }));
                
                // Verify UI shows updated values
                cy.get('[data-testid="temperature-gauge"]').should('contain', '125.0');
                cy.get('[data-testid="status-indicator"]').should('contain', 'ONLINE');
                cy.get('[data-testid="mode-indicator"]').should('contain', 'ECO');
            });
        });
        """
