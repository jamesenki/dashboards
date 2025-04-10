"""
Test WebSocketServiceManager

This test suite ensures that the WebSocketServiceManager properly manages WebSocket initialization
and prevents duplicate instances from being created.
"""
import os
import socket
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

# Import the WebSocketServiceManager
from src.infrastructure.websocket.websocket_manager import (
    ENV_ACTIVE_WS_PORT,
    ENV_DISABLE_WEBSOCKET,
    ENV_WS_HOST,
    ENV_WS_INIT_ATTEMPTED,
    ENV_WS_INITIALIZED,
    ENV_WS_PORT,
    ENV_WS_PORT_UNAVAILABLE,
    WebSocketServiceManager,
)


class TestWebSocketServiceManager:
    """Tests for the WebSocketServiceManager class to ensure proper WebSocket management."""

    def setup_method(self):
        """Setup test environment before each test."""
        # Reset environment variables
        for env_var in [
            ENV_WS_HOST,
            ENV_WS_PORT,
            ENV_DISABLE_WEBSOCKET,
            ENV_WS_INITIALIZED,
            ENV_WS_INIT_ATTEMPTED,
            ENV_WS_PORT_UNAVAILABLE,
            ENV_ACTIVE_WS_PORT,
        ]:
            if env_var in os.environ:
                del os.environ[env_var]

        # Reset the WebSocketServiceManager state
        WebSocketServiceManager._instance = None

        # Initialize mock message bus
        self.mock_message_bus = MagicMock()

    def test_singleton_pattern(self):
        """Test that WebSocketServiceManager follows the singleton pattern."""
        # Get two instances
        instance1 = WebSocketServiceManager.get_instance(self.mock_message_bus)
        instance2 = WebSocketServiceManager.get_instance(self.mock_message_bus)

        # Verify they are the same instance
        assert instance1 is instance2
        assert WebSocketServiceManager._instance is instance1

    def test_only_initializes_once(self):
        """Test that WebSocketServiceManager only initializes the WebSocket service once."""
        # Mock the _create_instance method to track calls
        with patch.object(WebSocketServiceManager, "_create_instance") as mock_create:
            # Configure mock to return a valid service
            mock_service = MagicMock()
            mock_create.return_value = mock_service

            # Get multiple instances
            for _ in range(5):
                WebSocketServiceManager.get_instance(self.mock_message_bus)

            # Verify _create_instance was only called once
            assert mock_create.call_count == 1

    def test_thread_safety(self):
        """Test that initialization is thread-safe."""
        # Reset for this test
        WebSocketServiceManager._instance = None

        # Mock _create_instance to track calls and add delay to simulate concurrency
        with patch.object(WebSocketServiceManager, "_create_instance") as mock_create:

            def delayed_create(*args, **kwargs):
                time.sleep(0.1)  # Simulate work
                mock_service = MagicMock()
                return mock_service

            mock_create.side_effect = delayed_create

            # Launch multiple threads to get instances concurrently
            threads = []
            for _ in range(10):
                thread = threading.Thread(
                    target=WebSocketServiceManager.get_instance,
                    args=(self.mock_message_bus,),
                )
                threads.append(thread)

            # Start all threads
            for thread in threads:
                thread.start()

            # Wait for all to complete
            for thread in threads:
                thread.join()

            # Verify _create_instance was called exactly once despite concurrent access
            assert mock_create.call_count == 1

    def test_environment_variables_set(self):
        """Test that environment variables are properly set during initialization."""
        # Mock _create_instance to return a valid service
        with patch.object(WebSocketServiceManager, "_create_instance") as mock_create:
            mock_service = MagicMock()
            mock_create.return_value = mock_service

            # Get an instance
            WebSocketServiceManager.get_instance(self.mock_message_bus)

            # Verify environment variables were set
            assert os.environ.get(ENV_WS_INITIALIZED) == "true"
            assert ENV_WS_INIT_ATTEMPTED in os.environ

    def test_respects_disable_flag(self):
        """Test that WebSocketServiceManager respects the disable flag."""
        # Set the disable flag
        os.environ[ENV_DISABLE_WEBSOCKET] = "true"

        # Mock _create_instance to track if it's called
        with patch.object(WebSocketServiceManager, "_create_instance") as mock_create:
            # Get an instance
            instance = WebSocketServiceManager.get_instance(self.mock_message_bus)

            # Verify _create_instance was not called
            assert mock_create.call_count == 0
            # Verify we got None back
            assert instance is None

    def test_port_allocation(self):
        """Test that WebSocketServiceManager finds an available port."""
        # Import here to avoid circular imports in test
        from src.infrastructure.websocket.websocket_service import WebSocketService

        # Create a socket to occupy the default port
        default_port = int(os.environ.get(ENV_WS_PORT, 8912))
        blocking_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            blocking_socket.bind(("0.0.0.0", default_port))
            blocking_socket.listen(1)

            # Now the default port is taken, let's see if WebSocketServiceManager finds another
            with patch.object(WebSocketService, "start", return_value=True):
                instance = WebSocketServiceManager.get_instance(self.mock_message_bus)

                # Verify an alternate port was chosen
                assert os.environ.get(ENV_ACTIVE_WS_PORT) is not None
                assert int(os.environ.get(ENV_ACTIVE_WS_PORT)) != default_port
        finally:
            blocking_socket.close()

    def test_handles_initialization_failure(self):
        """Test that WebSocketServiceManager handles initialization failures gracefully."""
        # Import here to avoid circular imports in test
        from src.infrastructure.websocket.websocket_service import WebSocketService

        # Mock WebSocketService.start to simulate failure
        with patch.object(WebSocketService, "start", return_value=False):
            # Get an instance
            instance = WebSocketServiceManager.get_instance(self.mock_message_bus)

            # Verify we still got an instance
            assert instance is None

            # Verify the environment variable indicates initialization failed
            assert ENV_WS_INITIALIZED not in os.environ

    def test_prevents_duplicate_servers(self):
        """Test that the system prevents duplicate WebSocket servers."""
        # Import here to avoid circular imports in test
        from src.infrastructure.websocket.websocket_service import WebSocketService

        # Create a mock WebSocketService that returns success
        with patch.object(WebSocketService, "start", return_value=True):
            # Get an instance through the manager
            manager_instance = WebSocketServiceManager.get_instance(
                self.mock_message_bus
            )

            # Attempt to create a second instance directly
            direct_instance = WebSocketService(self.mock_message_bus)

            # Now try to start it
            with patch.object(
                WebSocketService, "_is_port_available", return_value=True
            ):
                # This should return False as the initialization should be skipped due to
                # the environment variables set by the WebSocketServiceManager
                assert not direct_instance.start()

    def test_integration_with_standalone_server(self):
        """Test that the standalone server respects the WebSocketServiceManager."""
        # Import standalone server
        from src.services.standalone_websocket_server import (
            start_standalone_websocket_server,
        )

        # First, simulate WebSocketServiceManager initializing a server
        with patch.object(WebSocketServiceManager, "_create_instance") as mock_create:
            mock_service = MagicMock()
            mock_create.return_value = mock_service

            # Set up the environment as if WebSocketServiceManager initialized successfully
            os.environ[ENV_WS_INITIALIZED] = "true"
            os.environ[ENV_ACTIVE_WS_PORT] = "8950"

            # Now try to start the standalone server
            result = start_standalone_websocket_server()

            # It should not start because the manager already has a server
            assert not result

    def test_blocking_behavior_prevented(self):
        """Test that the WebSocketServiceManager doesn't block app startup."""
        # Import here to avoid circular imports in test
        from src.infrastructure.websocket.websocket_service import WebSocketService

        # Create a mock start method that takes a long time (simulating potential blocking)
        def slow_start(*args, **kwargs):
            time.sleep(5)  # Simulate a slow startup
            return True

        # Run with the patched slow start method
        with patch.object(WebSocketService, "start", side_effect=slow_start):
            # Time how long it takes to get an instance
            start_time = time.time()
            instance = WebSocketServiceManager.get_instance(self.mock_message_bus)
            end_time = time.time()

            # Verify we got back quickly (less than the 5 seconds the mock would take)
            # This is possible because of our timeout logic
            assert (end_time - start_time) < 5

            # We should still get a service instance
            assert instance is not None


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
