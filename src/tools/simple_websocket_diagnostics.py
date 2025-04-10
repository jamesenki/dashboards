"""
Simple WebSocket Diagnostic Tool

This tool helps identify WebSocket initialization attempts in the IoTSphere application
by instrumenting key WebSocket classes without requiring system permissions.
"""

import inspect
import logging
import os
import socket

# DISABLED FOR PERFORMANCE
# All diagnostics have been disabled to reduce system load
import sys
import threading
import time
import traceback
from datetime import datetime

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_diagnostics")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter("[WebSocket Diagnostics] %(levelname)s: %(message)s")
)
logger.addHandler(handler)

# Global dictionary to track WebSocket instances and initializations
websocket_instances = {}
initialization_attempts = []
initialization_lock = threading.Lock()


def register_initialization(source, info=None):
    """Register a WebSocket initialization attempt with stack trace."""
    # Disabled for performance
    return


def register_instance(instance_id, instance_type, host=None, port=None):
    # Disabled for performance
    return


# End of function


def patch_websocket_classes():
    # Disabled for performance
    return
    """
    Patch WebSocket-related classes to track initialization.
    """
    try:
        # Import the WebSocketService class
        from src.infrastructure.websocket.websocket_manager import (
            WebSocketServiceManager,
        )
        from src.infrastructure.websocket.websocket_service import WebSocketService

        # Store original methods
        original_ws_init = WebSocketService.__init__
        original_ws_start = WebSocketService.start
        original_wsm_get_instance = WebSocketServiceManager.get_instance
        original_wsm_create_instance = WebSocketServiceManager._create_instance

        # Patch WebSocketService.__init__
        def patched_ws_init(self, *args, **kwargs):
            register_initialization(
                "WebSocketService.__init__", f"args={args}, kwargs={kwargs}"
            )
            result = original_ws_init(self, *args, **kwargs)
            register_instance(
                id(self),
                "WebSocketService",
                getattr(self, "host", None),
                getattr(self, "port", None),
            )
            return result

        # Patch WebSocketService.start
        def patched_ws_start(self, *args, **kwargs):
            register_initialization(
                "WebSocketService.start", f"host={self.host}, port={self.port}"
            )
            return original_ws_start(self, *args, **kwargs)

        # Patch WebSocketServiceManager.get_instance
        def patched_wsm_get_instance(cls, *args, **kwargs):
            register_initialization(
                "WebSocketServiceManager.get_instance", f"args={args}, kwargs={kwargs}"
            )
            return original_wsm_get_instance(cls, *args, **kwargs)

        # Patch WebSocketServiceManager._create_instance
        def patched_wsm_create_instance(cls, *args, **kwargs):
            register_initialization(
                "WebSocketServiceManager._create_instance",
                f"args={args}, kwargs={kwargs}",
            )
            return original_wsm_create_instance(cls, *args, **kwargs)

        # Apply patches
        WebSocketService.__init__ = patched_ws_init
        WebSocketService.start = patched_ws_start
        WebSocketServiceManager.get_instance = classmethod(patched_wsm_get_instance)
        WebSocketServiceManager._create_instance = classmethod(
            patched_wsm_create_instance
        )

        logger.info("Successfully patched WebSocket classes")

        # Try to patch standalone WebSocket server if it exists
        try:
            import src.services.standalone_websocket_server

            original_standalone_start = (
                src.services.standalone_websocket_server.start_standalone_websocket_server
            )

            def patched_standalone_start(*args, **kwargs):
                register_initialization(
                    "standalone_websocket_server.start_standalone_websocket_server",
                    f"args={args}, kwargs={kwargs}",
                )
                return original_standalone_start(*args, **kwargs)

            src.services.standalone_websocket_server.start_standalone_websocket_server = (
                patched_standalone_start
            )
            logger.info("Successfully patched standalone WebSocket server")
        except (ImportError, AttributeError):
            logger.info("No standalone WebSocket server found to patch")

        return True
    except Exception as e:
        logger.error(f"Error patching WebSocket classes: {e}")
        logger.error(traceback.format_exc())
        return False


def find_websocket_references():
    # Disabled for performance
    return []
    """Find all modules that might reference WebSocket classes."""
    ws_references = []

    for module_name, module in list(sys.modules.items()):
        if module_name.startswith("src."):
            try:
                module_source = inspect.getsource(module)
                if (
                    "WebSocketService" in module_source
                    or "websocket" in module_source.lower()
                ):
                    ws_references.append(
                        {"module": module_name, "references_websocket": True}
                    )
            except (TypeError, OSError, IOError):
                # Skip modules we can't inspect
                pass

    return ws_references


def is_port_in_use(host, port):
    # Disabled for performance
    return False
    """Check if a specific port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False  # Port is available
        except socket.error:
            return True  # Port is in use


def check_websocket_ports():
    # Disabled for performance
    return []
    """Check if the expected WebSocket ports are in use."""
    # Check default port
    default_port = int(os.environ.get("WS_PORT", 8912))

    # Check if the default port is already in use
    if is_port_in_use("0.0.0.0", default_port):
        logger.warning(f"WebSocket default port {default_port} is already in use!")
    else:
        logger.info(f"WebSocket default port {default_port} is available")

    # Check if active port from env var is in use
    active_port_str = os.environ.get("ACTIVE_WS_PORT")
    if active_port_str:
        try:
            active_port = int(active_port_str)
            if is_port_in_use("0.0.0.0", active_port):
                logger.warning(f"Active WebSocket port {active_port} is in use")
            else:
                logger.warning(
                    f"Active WebSocket port {active_port} is NOT in use (unexpected)"
                )
        except ValueError:
            logger.error(f"Invalid ACTIVE_WS_PORT value: {active_port_str}")


def find_duplicate_initializations():
    # Disabled for performance
    return []
    """Analyze initialization attempts to find potential duplicates."""
    # Count initializations by source
    source_counts = {}
    for attempt in initialization_attempts:
        source = attempt["source"]
        source_counts[source] = source_counts.get(source, 0) + 1

    # Report on frequency
    print("\nINITIALIZATION FREQUENCY BY SOURCE:")
    for source, count in source_counts.items():
        print(f"  - {source}: {count} times")
        if count > 1 and "WebSocketService.__init__" in source:
            print(f"    [WARNING] Multiple WebSocketService initializations detected!")

    # Look for multiple start calls
    start_calls = [a for a in initialization_attempts if "start" in a["source"]]
    if len(start_calls) > 1:
        print(
            f"\n[WARNING] Multiple WebSocket start attempts detected: {len(start_calls)}"
        )
        for call in start_calls:
            print(f"  - {call['timestamp']} from {call['source']}")
            if call.get("info"):
                print(f"    Info: {call['info']}")


def run_diagnostics():
    # Disabled for performance
    return
    """Run diagnostics and print a report."""
    print("\n" + "=" * 80)
    print("WEBSOCKET INITIALIZATION DIAGNOSTICS")
    print("=" * 80)

    # Patch WebSocket classes
    if not patch_websocket_classes():
        print("[ERROR] Failed to patch WebSocket classes for diagnostics")
        return

    print("\n1. CHECKING CURRENT PORT USAGE:")
    check_websocket_ports()

    print("\n2. COLLECTING WEBSOCKET MODULE REFERENCES...")
    ws_refs = find_websocket_references()
    print(f"Found {len(ws_refs)} modules referencing WebSockets:")
    for ref in ws_refs:
        print(f"  - {ref['module']}")

    print("\n3. ENVIRONMENT VARIABLES:")
    for env_var in [
        "WS_HOST",
        "WS_PORT",
        "DISABLE_WEBSOCKET",
        "WEBSOCKET_INITIALIZED",
        "WEBSOCKET_INIT_ATTEMPTED",
        "WEBSOCKET_PORT_UNAVAILABLE",
        "ACTIVE_WS_PORT",
    ]:
        value = os.environ.get(env_var, "[not set]")
        print(f"  - {env_var}: {value}")

    print("\n" + "=" * 80)
    print("\nREADY TO TRACE WEBSOCKET INITIALIZATION")
    print(
        "Now run the main application and check '/tmp/websocket_debug.log' for results"
    )
    print("=" * 80)


if __name__ == "__main__":
    run_diagnostics()

    # Configure file logging for when we're imported
    file_handler = logging.FileHandler("/tmp/websocket_debug.log", mode="w")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(file_handler)

    print("\nWebSocket diagnostics installed. Run your application normally.")
    print("Check /tmp/websocket_debug.log for detailed initialization traces.")
