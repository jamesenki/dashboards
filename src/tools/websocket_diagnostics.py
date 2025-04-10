"""
WebSocket Diagnostic Tool

This tool helps identify all WebSocket initialization attempts and connections in the IoTSphere application.
It logs detailed information about each WebSocket-related activity to help debug duplication issues.
"""

# DISABLED FOR PERFORMANCE
# This module is disabled to improve application performance
# All functions will return immediately without performing diagnostics
import asyncio
import inspect
import logging
import os
import socket
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Thread

import psutil

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_diagnostics")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter("[WebSocket Diagnostics] %(levelname)s: %(message)s")
)
logger.addHandler(handler)


# Global registry for tracking WebSocket services - DISABLED FOR PERFORMANCE
class WebSocketRegistry:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WebSocketRegistry, cls).__new__(cls)
                cls._instance.services = []
                cls._instance.connection_attempts = []
                cls._instance.active_ports = set()
                cls._instance.initialization_stack_traces = []
            return cls._instance

    # All methods are no-ops for performance
    def register_service(self, *args, **kwargs):
        return

    def register_connection_attempt(self, *args, **kwargs):
        return

    def register_port(self, *args, **kwargs):
        return

    def get_services(self, *args, **kwargs):
        return []

    def get_connection_attempts(self, *args, **kwargs):
        return []

    def register_service(self, service_info):
        """Register a WebSocket service instance."""
        with self._lock:
            self.services.append(service_info)
            logger.info(f"Registered WebSocket service: {service_info}")

    def register_connection_attempt(self, connection_info):
        """Register a WebSocket connection attempt."""
        with self._lock:
            self.connection_attempts.append(connection_info)
            logger.info(f"WebSocket connection attempt: {connection_info}")

    def register_active_port(self, port, service_name):
        """Register a port being used by a WebSocket service."""
        with self._lock:
            if port in self.active_ports:
                logger.warning(f"PORT CONFLICT: Port {port} is already in use!")
            self.active_ports.add(port)
            logger.info(f"Registered active WebSocket port {port} for {service_name}")

    def register_initialization(self, stack_trace, source):
        """Register a WebSocket initialization with stack trace."""
        with self._lock:
            self.initialization_stack_traces.append(
                {"source": source, "stack_trace": stack_trace}
            )
            logger.info(f"WebSocket initialization from: {source}")


# Create registry instance
registry = WebSocketRegistry()


def get_active_listener_ports():
    # Disabled for performance
    return []
    """Get all ports that are being actively listened to on the system."""
    active_ports = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.status == "LISTEN":
            active_ports.append(conn.laddr.port)
    return active_ports


def check_for_websocket_service_instances():
    # Disabled for performance
    return []
    """Look for all WebSocket service instances in the application."""
    from src.infrastructure.websocket.websocket_service import WebSocketService

    # Introspect at runtime to find any instances
    instances = []
    for module_name, module in sys.modules.items():
        if module_name.startswith("src."):
            for name, obj in inspect.getmembers(module):
                # Check for WebSocketService instances
                if isinstance(obj, WebSocketService):
                    instances.append(
                        {
                            "module": module_name,
                            "instance": obj,
                            "port": getattr(obj, "port", None),
                            "host": getattr(obj, "host", None),
                            "is_running": hasattr(obj, "_is_running")
                            and obj._is_running,
                        }
                    )

    return instances


def find_all_websocket_imports():
    # Disabled for performance
    return []
    """Find all modules that import WebSocket-related modules."""
    websocket_imports = []

    for module_name, module in sys.modules.items():
        if module_name.startswith("src."):
            # Check if the module imports any WebSocket modules
            for name, obj in inspect.getmembers(module):
                if inspect.ismodule(obj) and "websocket" in obj.__name__.lower():
                    websocket_imports.append(
                        {"module": module_name, "imports": obj.__name__}
                    )

    return websocket_imports


def check_for_duplicate_ports():
    # Disabled for performance
    return []
    """Check if there are duplicate ports among WebSocket services."""
    instances = check_for_websocket_service_instances()

    # Check for duplicates in collected instances
    ports = {}
    for instance in instances:
        port = instance.get("port")
        if port:
            if port in ports:
                # Found a duplicate
                logger.error(f"DUPLICATE PORT DETECTED: Port {port} is used by:")
                logger.error(f"  1. {ports[port]['module']}")
                logger.error(f"  2. {instance['module']}")
                return True
            ports[port] = instance

    return False


def monitor_socket_activity(duration=10):
    # Disabled for performance
    return []
    """Monitor socket activity for a specified duration."""
    logger.info(f"Starting socket activity monitor for {duration} seconds...")

    # Get initial state
    initial_ports = set(get_active_listener_ports())
    logger.info(f"Initial active listener ports: {initial_ports}")

    # Monitor for changes
    end_time = asyncio.get_event_loop().time() + duration
    try:
        while asyncio.get_event_loop().time() < end_time:
            current_ports = set(get_active_listener_ports())

            # Check for new ports
            new_ports = current_ports - initial_ports
            if new_ports:
                logger.info(f"New ports detected: {new_ports}")
                initial_ports = current_ports

            # Sleep briefly
            asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"Error monitoring socket activity: {e}")

    logger.info("Socket activity monitoring completed")


def patch_websocket_classes():
    # Disabled for performance
    return
    """
    Patch WebSocket classes to track initialization and connections.
    This adds diagnostic hooks to key WebSocket methods.
    """
    try:
        # Import the WebSocketService class
        from src.infrastructure.websocket.websocket_service import WebSocketService

        # Store the original methods
        original_init = WebSocketService.__init__
        original_start = WebSocketService.start

        # Patch the initialization method
        def patched_init(self, *args, **kwargs):
            # Call the original method
            original_init(self, *args, **kwargs)

            # Register this instance
            stack = traceback.format_stack()
            registry.register_service(
                {
                    "type": "WebSocketService",
                    "host": getattr(self, "host", None),
                    "port": getattr(self, "port", None),
                    "id": id(self),
                }
            )
            registry.register_initialization(stack, "WebSocketService.__init__")

        # Patch the start method
        def patched_start(self, *args, **kwargs):
            # Register before start
            logger.info(
                f"WebSocketService.start called for service on port {self.port}"
            )
            stack = traceback.format_stack()
            registry.register_initialization(stack, "WebSocketService.start")

            # Call the original method
            result = original_start(self, *args, **kwargs)

            # Register after start
            if result:
                registry.register_active_port(self.port, "WebSocketService")

            return result

        # Apply the patches
        WebSocketService.__init__ = patched_init
        WebSocketService.start = patched_start

        logger.info("Successfully patched WebSocketService class for diagnostics")

        # Also patch the WebSocketServiceManager
        from src.infrastructure.websocket.websocket_manager import (
            WebSocketServiceManager,
        )

        original_get_instance = WebSocketServiceManager.get_instance

        def patched_get_instance(cls, *args, **kwargs):
            # Register the call
            stack = traceback.format_stack()
            registry.register_initialization(
                stack, "WebSocketServiceManager.get_instance"
            )

            # Call the original method
            result = original_get_instance(cls, *args, **kwargs)
            return result

        WebSocketServiceManager.get_instance = classmethod(patched_get_instance)
        logger.info(
            "Successfully patched WebSocketServiceManager class for diagnostics"
        )

        # Find and patch any standalone server implementations
        try:
            from src.services.standalone_websocket_server import (
                start_standalone_websocket_server,
            )

            original_standalone_start = start_standalone_websocket_server

            def patched_standalone_start(*args, **kwargs):
                # Register the call
                stack = traceback.format_stack()
                registry.register_initialization(stack, "standalone_websocket_server")

                # Call the original
                return original_standalone_start(*args, **kwargs)

            # Apply patch
            import src.services.standalone_websocket_server

            src.services.standalone_websocket_server.start_standalone_websocket_server = (
                patched_standalone_start
            )
            logger.info(
                "Successfully patched standalone WebSocket server for diagnostics"
            )
        except ImportError:
            logger.info("No standalone WebSocket server found to patch")

        return True
    except Exception as e:
        logger.error(f"Error patching WebSocket classes: {e}")
        logger.error(traceback.format_exc())
        return False


def run_diagnostic_checks():
    # Disabled for performance
    return {"disabled": "All diagnostics disabled for performance"}
    """Run all diagnostic checks and return a report."""
    logger.info("Starting WebSocket diagnostics...")

    # Patch WebSocket classes for monitoring
    if not patch_websocket_classes():
        logger.warning(
            "Failed to patch WebSocket classes. Diagnostics may be incomplete."
        )

    # Gather information
    results = {
        "active_ports": get_active_listener_ports(),
        "websocket_instances": check_for_websocket_service_instances(),
        "websocket_imports": find_all_websocket_imports(),
        "has_duplicate_ports": check_for_duplicate_ports(),
    }

    # Log the findings
    logger.info(f"Active listener ports: {results['active_ports']}")
    logger.info(f"Found {len(results['websocket_instances'])} WebSocket instances")
    logger.info(
        f"Found {len(results['websocket_imports'])} modules importing WebSocket modules"
    )

    if results["has_duplicate_ports"]:
        logger.error("Duplicate ports detected in WebSocket services!")
    else:
        logger.info("No duplicate WebSocket ports detected in service instances.")

    return results


def print_diagnostic_report():
    # Disabled for performance
    return
    """Run diagnostics and print a formatted report."""
    results = run_diagnostic_checks()

    print("\n" + "=" * 80)
    print("WEBSOCKET DIAGNOSTIC REPORT")
    print("=" * 80)

    print("\nACTIVE LISTENER PORTS:")
    for port in sorted(results["active_ports"]):
        print(f"  - Port {port}")

    print("\nWEBSOCKET SERVICE INSTANCES:")
    for instance in results["websocket_instances"]:
        state = "RUNNING" if instance.get("is_running") else "NOT RUNNING"
        print(
            f"  - {instance.get('module')} on {instance.get('host')}:{instance.get('port')} ({state})"
        )

    print("\nWEBSOCKET IMPORTS BY MODULE:")
    for imp in results["websocket_imports"]:
        print(f"  - {imp['module']} imports {imp['imports']}")

    print("\nDUPLICATION CHECK:")
    if results["has_duplicate_ports"]:
        print("  [WARNING] Duplicate WebSocket ports detected!")
    else:
        print("  [OK] No duplicate ports detected in service instances")

    print("\n" + "=" * 80)
    registry_instance = WebSocketRegistry()
    print(
        f"INITIALIZATION STACK TRACES ({len(registry_instance.initialization_stack_traces)}):"
    )
    for i, trace in enumerate(registry_instance.initialization_stack_traces):
        print(f"\n{i+1}. From: {trace['source']}")
        print(
            "   " + "\n   ".join(trace["stack_trace"][-5:])
        )  # Show last 5 lines of each trace

    print("\n" + "=" * 80)


if __name__ == "__main__":
    print_diagnostic_report()
