"""
WebSocket Initialization Tracer

This module traces all WebSocket initialization points in the application.
It uses monkeypatching to instrument key methods and print detailed diagnostics.
"""

import inspect
import logging
import os
import sys
import threading
import traceback
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_tracer")
file_handler = logging.FileHandler("websocket_tracer.log", mode="w")
file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter("[WEBSOCKET TRACE] %(message)s"))
logger.addHandler(stream_handler)

# Store initialization traces
initialization_points = []
trace_lock = threading.Lock()


def trace_method(cls, method_name):
    """Monkeypatch a method to trace its execution."""
    original_method = getattr(cls, method_name)

    @wraps(original_method)
    def traced_method(*args, **kwargs):
        # Extract caller information
        frame = inspect.currentframe().f_back
        caller_info = inspect.getframeinfo(frame)

        # Get full stack trace for debugging
        stack = traceback.extract_stack()
        # Remove the last two entries which are this function and its caller
        relevant_stack = stack[:-2]

        # Format the stack trace for better readability
        formatted_stack = []
        for frame in relevant_stack:
            if "/site-packages/" not in frame.filename and frame.filename != "<string>":
                formatted_stack.append(
                    f"{os.path.basename(frame.filename)}:{frame.lineno}"
                )

        # Format arguments for better readability
        arg_str = ""
        if len(args) > 1:  # Skip 'self' for instance methods
            arg_str = f"args={args[1:]}"
        if kwargs:
            if arg_str:
                arg_str += ", "
            arg_str += f"kwargs={kwargs}"

        # Record the initialization point
        with trace_lock:
            call_point = {
                "class": cls.__name__,
                "method": method_name,
                "file": caller_info.filename,
                "line": caller_info.lineno,
                "stack": formatted_stack,
                "args": arg_str,
            }
            initialization_points.append(call_point)

        # Log the tracing information
        logger.info(
            f"TRACE: {cls.__name__}.{method_name} called from {caller_info.filename}:{caller_info.lineno}"
        )
        logger.info(f"STACK: {' -> '.join(formatted_stack)}")
        if arg_str:
            logger.info(f"ARGS: {arg_str}")

        # Call the original method
        return original_method(*args, **kwargs)

    # Replace the original method with our traced version
    setattr(cls, method_name, traced_method)


def patch_socket_classes():
    """Patch low-level socket classes to catch all socket binding operations."""
    original_socket_bind = socket.socket.bind

    @wraps(original_socket_bind)
    def traced_socket_bind(self, address):
        # Extract caller information from the stack
        stack = traceback.extract_stack()

        # Format the trace
        formatted_stack = []
        for frame in stack[:-1]:  # Exclude this function
            if "/site-packages/" not in frame.filename and frame.filename != "<string>":
                formatted_stack.append(
                    f"{os.path.basename(frame.filename)}:{frame.lineno}"
                )

        if isinstance(address, tuple) and len(address) >= 2:
            host, port = address[0], address[1]
            logger.info(
                f"SOCKET BIND: {host}:{port} from {' -> '.join(formatted_stack)}"
            )

        # Call the original method
        return original_socket_bind(self, address)

    # Apply the patch
    socket.socket.bind = traced_socket_bind


def trace_websocket_initializations():
    """
    Trace all WebSocket initialization points in the application.
    """
    logger.info("Starting WebSocket initialization tracing...")

    try:
        # Import and patch the WebSocketService class
        from src.infrastructure.websocket.websocket_service import WebSocketService

        trace_method(WebSocketService, "__init__")
        trace_method(WebSocketService, "start")

        # Import and patch the WebSocketServiceManager
        from src.infrastructure.websocket.websocket_manager import (
            WebSocketServiceManager,
        )

        trace_method(WebSocketServiceManager, "get_instance")
        trace_method(WebSocketServiceManager, "_create_instance")

        # Check if standalone WebSocket server exists
        try:
            import src.services.standalone_websocket_server

            # Monkeypatch
            original_start_standalone = (
                src.services.standalone_websocket_server.start_standalone_websocket_server
            )

            @wraps(original_start_standalone)
            def traced_start_standalone(*args, **kwargs):
                stack = traceback.extract_stack()
                formatted_stack = []
                for frame in stack[:-1]:
                    if (
                        "/site-packages/" not in frame.filename
                        and frame.filename != "<string>"
                    ):
                        formatted_stack.append(
                            f"{os.path.basename(frame.filename)}:{frame.lineno}"
                        )

                logger.info(
                    f"STANDALONE WEBSOCKET START from {' -> '.join(formatted_stack)}"
                )
                return original_start_standalone(*args, **kwargs)

            # Apply the patch
            src.services.standalone_websocket_server.start_standalone_websocket_server = (
                traced_start_standalone
            )
            logger.info("Successfully patched standalone WebSocket server")
        except ImportError:
            logger.info("No standalone WebSocket server found")

        # Patch socket.socket.bind to catch all socket binding operations
        import socket

        patch_socket_classes()

        logger.info("WebSocket tracing initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize WebSocket tracing: {e}")
        logger.error(traceback.format_exc())
        return False


def print_diagnostic_report():
    """Print a diagnostic report of all WebSocket initializations."""
    print("\n" + "=" * 80)
    print(" WEBSOCKET INITIALIZATION DIAGNOSTIC REPORT")
    print("=" * 80)

    with trace_lock:
        if not initialization_points:
            print("\nNo WebSocket initializations detected yet.")
            return

        print(
            f"\nDetected {len(initialization_points)} WebSocket initialization points:"
        )

        for i, point in enumerate(initialization_points):
            print(
                f"\n{i+1}. {point['class']}.{point['method']} called from {os.path.basename(point['file'])}:{point['line']}"
            )
            print(f"   Stack: {' -> '.join(point['stack'])}")
            if point.get("args"):
                print(f"   Args: {point['args']}")

    print("\n" + "=" * 80)
    print(" Check websocket_tracer.log for more detailed information")
    print("=" * 80 + "\n")


# Initialize tracing when this module is imported
trace_websocket_initializations()

if __name__ == "__main__":
    print(
        "WebSocket Tracer initialized. Run your application and check the log for results."
    )
    print("To view a diagnostic report, call print_diagnostic_report()")
