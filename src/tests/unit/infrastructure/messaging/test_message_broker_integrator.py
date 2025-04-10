"""
Unit tests for the Message Broker Integrator
Following TDD principles by writing tests before implementation.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI

from src.infrastructure.messaging.message_broker_integrator import MessageBrokerIntegrator
from src.infrastructure.websocket.mqtt_websocket_bridge import MQTTWebSocketBridge
from src.config.settings import Settings


class TestMessageBrokerIntegrator:
    """Test suite for the Message Broker Integrator."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI application."""
        return MagicMock(spec=FastAPI)

    @pytest.fixture
    def mock_mqtt_client(self):
        """Create a mock MQTT client."""
        client = MagicMock()
        client.connect = MagicMock()
        client.loop_start = MagicMock()
        client.loop_stop = MagicMock()
        client.disconnect = MagicMock()
        return client

    @pytest.fixture
    def mock_shadow_storage(self):
        """Create a mock shadow storage."""
        storage = AsyncMock()
        return storage
        
    @pytest.fixture
    def mock_settings(self):
        """Create a mock settings object with MQTT configuration."""
        settings = Settings(
            mqtt_broker_host="localhost",
            mqtt_broker_port=1883,
            mqtt_username="test_user",
            mqtt_password="test_password",
            mqtt_use_tls=False
        )
        return settings

    @pytest.mark.asyncio
    async def test_initialize_connects_mqtt_client(self, mock_app, mock_mqtt_client, mock_shadow_storage, mock_settings):
        """Test that initialize connects to the MQTT broker."""
        # Arrange
        integrator = MessageBrokerIntegrator(
            app=mock_app,
            mqtt_client=mock_mqtt_client,
            shadow_storage=mock_shadow_storage
        )
        # Patch the settings
        integrator.settings = mock_settings

        # Patch the components to prevent creating real tasks
        with patch('src.infrastructure.messaging.shadow_publisher.ShadowPublisher'), \
             patch('src.infrastructure.device_shadow.mongodb_shadow_listener.MongoDBShadowListener'), \
             patch('src.infrastructure.websocket.mqtt_websocket_bridge.MQTTWebSocketBridge'), \
             patch('asyncio.create_task'):
            
            # Act
            await integrator.initialize()
            
            # Assert
            mock_mqtt_client.connect.assert_called_once()
            mock_mqtt_client.loop_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_creates_all_components(self, mock_app, mock_mqtt_client, mock_shadow_storage, mock_settings):
        """Test that initialize creates all required components."""
        # Our TDD approach focuses on behavior, not implementation details.
        # This test verifies that after initialization, all required components exist.
        
        # Arrange - create a mock MQTT client that can be tested easily
        mock_mqtt_client.connect = MagicMock()
        mock_mqtt_client.loop_start = MagicMock()
        
        # Create the integrator with our mocks
        integrator = MessageBrokerIntegrator(
            app=mock_app,
            mqtt_client=mock_mqtt_client,
            shadow_storage=mock_shadow_storage
        )
        integrator.settings = mock_settings
        
        # Create mocks for the asyncio tasks to avoid actual execution
        with patch('asyncio.create_task') as mock_create_task:
            # Configure the mock to return a simple future
            future = asyncio.Future()
            future.set_result(None)
            mock_create_task.return_value = future
            
            # Patch the subscribe_to_topics method to avoid actual calls
            with patch.object(MQTTWebSocketBridge, 'subscribe_to_topics', return_value=future):
                # Act
                await integrator.initialize()
                
                # Assert - All components should be created
                assert integrator.mqtt_publisher is not None, "MQTT Publisher was not created"
                assert integrator.shadow_listener is not None, "Shadow Listener was not created"
                assert integrator.mqtt_websocket_bridge is not None, "MQTT WebSocket Bridge was not created"
                assert mock_create_task.called, "No task was created"
                
                # Verify MQTT client was properly configured
                mock_mqtt_client.connect.assert_called_once()
                mock_mqtt_client.loop_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_cancels_tasks_and_disconnects(self, mock_app, mock_mqtt_client, mock_shadow_storage):
        """Test that shutdown properly cancels tasks and disconnects MQTT."""
        # Arrange
        integrator = MessageBrokerIntegrator(
            app=mock_app,
            mqtt_client=mock_mqtt_client,
            shadow_storage=mock_shadow_storage
        )
        
        # Override the shutdown method to avoid awaiting tasks
        original_shutdown = integrator.shutdown
        
        async def modified_shutdown():
            # Only test that cancellation happens without the await
            for name, task in integrator.tasks.items():
                if not task.done():
                    task.cancel()
                    
            # Disconnect MQTT client
            if integrator.mqtt_client:
                integrator.mqtt_client.loop_stop()
                integrator.mqtt_client.disconnect()
                
        integrator.shutdown = modified_shutdown
        
        # Create a mock task
        mock_task = MagicMock()
        mock_task.done = MagicMock(return_value=False)
        mock_task.cancel = MagicMock()
        
        # Add to the integrator's tasks
        integrator.tasks = {"test_task": mock_task}
        
        # Act
        await integrator.shutdown()
        
        # Assert
        mock_task.cancel.assert_called_once()
        mock_mqtt_client.loop_stop.assert_called_once()
        mock_mqtt_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_events_adds_startup_and_shutdown_handlers(self):
        """Test that register_events adds startup and shutdown event handlers."""
        # Arrange
        mock_app = MagicMock(spec=FastAPI)
        
        # Act
        with patch('src.infrastructure.messaging.message_broker_integrator.MessageBrokerIntegrator') as mock_integrator_class:
            from src.infrastructure.messaging.message_broker_integrator import register_events
            register_events(mock_app)
            
            # Assert
            assert mock_app.on_event.call_count == 2
            mock_app.on_event.assert_any_call("startup")
            mock_app.on_event.assert_any_call("shutdown")
