#!/usr/bin/env python3
"""
WebSocket Service Manager for IoTSphere

This module provides a singleton manager for WebSocket services to ensure
that only one WebSocket server is created throughout the application lifecycle.
"""
import logging
import os
import random
import socket
import threading

# Setup logging
logger = logging.getLogger(__name__)

# Global lock to ensure thread safety
_init_lock = threading.Lock()

# Global initialization flag - this is more reliable than environment variables for in-process checks
_INITIALIZED = False
_INITIALIZATION_COMPLETED = False
_INSTANCE = None

# Standardized environment variables to avoid conflicts
ENV_WS_HOST = "WS_HOST"
ENV_WS_PORT = "WS_PORT"
ENV_WS_DISABLED = "DISABLE_WEBSOCKET"
ENV_WS_INIT_ATTEMPTED = "WEBSOCKET_INIT_ATTEMPTED"
ENV_WS_INITIALIZED = "WEBSOCKET_INITIALIZED"
ENV_WS_PORT_UNAVAILABLE = "WEBSOCKET_PORT_UNAVAILABLE"
ENV_ACTIVE_WS_PORT = "ACTIVE_WS_PORT"

# Set early in import process to prevent multiple initialization
os.environ[ENV_WS_INIT_ATTEMPTED] = "true"


class WebSocketServiceManager:
    """Singleton manager for WebSocket services.

    This manager ensures that only one WebSocket service is created throughout
    the application lifecycle, preventing port conflicts and duplicate servers.
    """

    _instance = None
    _initialized = False

    @classmethod
    def get_instance(cls, message_bus=None):
        """Get the WebSocket service instance, creating it if it doesn't exist.

        Args:
            message_bus: Message bus to use for the WebSocket service

        Returns:
            WebSocketService instance or None if creation failed
        """
        global _INITIALIZED, _INITIALIZATION_COMPLETED, _INSTANCE

        # First quick check without acquiring lock
        if _INITIALIZATION_COMPLETED and _INSTANCE:
            logger.debug(
                "WebSocketServiceManager: Returning existing WebSocket service instance"
            )
            return _INSTANCE

        # Thread-safe initialization with lock
        with _init_lock:
            # Check again after acquiring lock
            if _INITIALIZATION_COMPLETED:
                logger.debug(
                    "WebSocketServiceManager: Initialization already completed"
                )
                return _INSTANCE

            # Check if disabled by configuration
            if os.environ.get(ENV_WS_DISABLED, "false").lower() == "true":
                logger.warning(
                    "WebSocketServiceManager: Service disabled by configuration"
                )
                _INITIALIZATION_COMPLETED = True
                return None

            # Prevent multiple initialization attempts
            if _INITIALIZED:
                logger.warning(
                    "WebSocketServiceManager: Another initialization attempt already in progress"
                )
                return None

            # Mark as initialized to prevent concurrent attempts
            _INITIALIZED = True
            logger.info(
                "WebSocketServiceManager: Starting initialization process (thread-safe)"
            )

            try:
                logger.info(
                    "WebSocketServiceManager: Creating new WebSocket service instance"
                )
                instance = cls._create_instance(message_bus)

                # Store in both class variable and global variable for extra safety
                cls._instance = instance
                _INSTANCE = instance

                if instance:
                    logger.info(
                        "WebSocketServiceManager: Successfully created WebSocket service"
                    )
                    # Set environment variables for other processes
                    os.environ[ENV_WS_INITIALIZED] = "true"
                else:
                    logger.warning(
                        "WebSocketServiceManager: Failed to create WebSocket service"
                    )
            except Exception as e:
                logger.error(
                    f"WebSocketServiceManager: Error creating WebSocket service: {e}"
                )
            finally:
                # Always mark initialization as completed to prevent further attempts
                _INITIALIZATION_COMPLETED = True

            return _INSTANCE

    @classmethod
    def _create_instance(cls, message_bus):
        """Create and start a WebSocket service instance with non-blocking behavior.

        Args:
            message_bus: Message bus to use for the WebSocket service

        Returns:
            WebSocketService instance or None if creation failed
        """
        # Import WebSocketService with specific error handling
        try:
            # Import WebSocketService here to avoid circular imports
            from src.infrastructure.websocket.websocket_service import WebSocketService
        except ImportError as e:
            logger.warning(
                f"WebSocketServiceManager: WebSocket modules not available: {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"WebSocketServiceManager: Unexpected error importing WebSocketService: {e}"
            )
            return None

        # Get configuration with error handling
        try:
            # Get WebSocket configuration with standardized environment variables
            ws_host = os.environ.get(ENV_WS_HOST, "0.0.0.0")
            ws_port = int(os.environ.get(ENV_WS_PORT, 8912))

            # Log the initial configuration
            logger.info(
                f"WebSocketServiceManager: Initial configuration - host: {ws_host}, port: {ws_port}"
            )
        except ValueError as e:
            logger.error(f"WebSocketServiceManager: Invalid port configuration: {e}")
            return None
        except Exception as e:
            logger.error(f"WebSocketServiceManager: Error getting configuration: {e}")
            return None

        # Find an available port with error handling
        try:
            port_found = False
            original_port = ws_port

            # Try up to 10 ports starting from the default
            for attempt in range(10):
                logger.info(
                    f"WebSocketServiceManager: Port attempt {attempt+1}/10 - Trying port {ws_port}"
                )
                try:
                    if cls._is_port_available(ws_host, ws_port):
                        port_found = True
                        logger.info(
                            f"WebSocketServiceManager: Port {ws_port} is available"
                        )
                        break
                    logger.warning(
                        f"WebSocketServiceManager: Port {ws_port} unavailable, trying another port"
                    )
                except Exception as port_error:
                    logger.error(
                        f"WebSocketServiceManager: Error checking port {ws_port}: {port_error}"
                    )
                # Try ports in a different range to avoid conflicts
                ws_port = random.randint(8920, 8980)

            if not port_found:
                logger.error(
                    "WebSocketServiceManager: Could not find an available port"
                )
                os.environ[ENV_WS_PORT_UNAVAILABLE] = "true"
                return None

            if ws_port != original_port:
                logger.info(
                    f"WebSocketServiceManager: Using alternate port {ws_port} instead of {original_port}"
                )

            # Store the selected port in environment for other components
            os.environ[ENV_ACTIVE_WS_PORT] = str(ws_port)
            logger.info(f"WebSocketServiceManager: Set {ENV_ACTIVE_WS_PORT}={ws_port}")
        except Exception as e:
            logger.error(f"WebSocketServiceManager: Error finding available port: {e}")
            return None

        # Create and start the WebSocket service with timeout protection
        try:
            # Create service instance
            logger.info(
                f"WebSocketServiceManager: Creating WebSocket service on {ws_host}:{ws_port}"
            )
            service = WebSocketService(
                message_bus=message_bus, host=ws_host, port=ws_port
            )

            # Use non-blocking approach with timeout
            import asyncio
            import concurrent.futures

            # Start the service with a timeout to prevent blocking the main thread
            logger.info(
                "WebSocketServiceManager: Starting WebSocket service with timeout protection"
            )

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(service.start)
                try:
                    # Wait for up to 3 seconds for the service to start
                    success = future.result(timeout=3.0)

                    if success:
                        logger.info(
                            f"WebSocketServiceManager: Successfully started WebSocket on {ws_host}:{ws_port}"
                        )
                        return service
                    else:
                        logger.error(
                            "WebSocketServiceManager: Service start() returned False"
                        )
                        return None
                except concurrent.futures.TimeoutError:
                    logger.warning(
                        "WebSocketServiceManager: WebSocket start timed out after 3 seconds"
                    )
                    # Proceed anyway - it might be running in background thread
                    # This ensures we don't block app startup
                    logger.info(
                        "WebSocketServiceManager: Returning service instance despite timeout"
                    )
                    return service
                except Exception as start_error:
                    logger.error(
                        f"WebSocketServiceManager: Error starting service: {start_error}"
                    )
                    return None
        except Exception as e:
            logger.error(
                f"WebSocketServiceManager: Error in service creation/startup: {e}"
            )
            return None

    @staticmethod
    def _is_port_available(host, port):
        """Check if a port is available for binding.

        Args:
            host: Host address to check
            port: Port number to check

        Returns:
            bool: True if port is available, False otherwise
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(0.5)
            sock.bind((host, port))
            return True
        except socket.error:
            return False
        finally:
            sock.close()


# Create a global instance for early access during import
_manager = WebSocketServiceManager()


def get_websocket_service(message_bus=None):
    """Global function to get the WebSocket service instance.

    This function provides a convenient way to access the WebSocket service
    from anywhere in the application.

    Args:
        message_bus: Message bus to use for the WebSocket service

    Returns:
        WebSocketService instance or None if not available
    """
    return WebSocketServiceManager.get_instance(message_bus)
