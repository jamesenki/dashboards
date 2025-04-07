/**
 * WebSocket Server Launcher for Integration Testing
 *
 * This script launches the Python WebSocket server for integration testing.
 * It's used to test the actual real-time monitoring implementation instead of mocks.
 */
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

class WebSocketServerLauncher {
  constructor() {
    this.serverProcess = null;
    this.isRunning = false;
    this.port = 8000; // Default WebSocket port
    this.serverReadyPromise = null;
    this.serverReadyResolver = null;
  }

  /**
   * Start the WebSocket server
   * @returns {Promise<boolean>} True if server started successfully
   */
  async start() {
    if (this.isRunning) {
      console.log("WebSocket server is already running");
      return true;
    }

    console.log("Starting WebSocket server for testing...");

    // Create a promise that will resolve when the server is ready
    this.serverReadyPromise = new Promise((resolve) => {
      this.serverReadyResolver = resolve;
    });

    // Path to the Python script for launching the standalone WebSocket server
    const scriptPath = path.resolve(__dirname, "../../src/services/test_websocket_server.py");

    // Check if the script exists and create it if it doesn't
    if (!fs.existsSync(scriptPath)) {
      await this.createTestServerScript(scriptPath);
    }

    // Launch the Python WebSocket server
    this.serverProcess = spawn("python", [scriptPath], {
      stdio: ["ignore", "pipe", "pipe"],
      env: { ...process.env, PYTHONUNBUFFERED: "1" },
    });

    // Handle server output
    this.serverProcess.stdout.on("data", (data) => {
      const output = data.toString().trim();
      console.log(`WebSocket Server: ${output}`);

      // Check if server is ready to accept connections
      if (
        output.includes("WebSocket server started") ||
        output.includes("Server started") ||
        output.includes("ready to accept connections")
      ) {
        this.isRunning = true;
        if (this.serverReadyResolver) {
          this.serverReadyResolver(true);
        }
      }
    });

    // Handle server errors
    this.serverProcess.stderr.on("data", (data) => {
      console.error(`WebSocket Server Error: ${data.toString().trim()}`);
    });

    // Handle server exit
    this.serverProcess.on("close", (code) => {
      console.log(`WebSocket server exited with code ${code}`);
      this.isRunning = false;
      this.serverProcess = null;
    });

    // Wait for server to be ready or timeout after 10 seconds
    const timeout = new Promise((resolve) => setTimeout(() => resolve(false), 10000));
    return Promise.race([this.serverReadyPromise, timeout]);
  }

  /**
   * Stop the WebSocket server
   */
  async stop() {
    if (!this.isRunning || !this.serverProcess) {
      console.log("WebSocket server is not running");
      return;
    }

    console.log("Stopping WebSocket server...");

    // Send SIGTERM to gracefully terminate the server
    this.serverProcess.kill("SIGTERM");

    // Wait for the process to exit
    await new Promise((resolve) => {
      this.serverProcess.on("close", () => {
        this.isRunning = false;
        this.serverProcess = null;
        resolve();
      });

      // Force kill after 5 seconds if not exited gracefully
      setTimeout(() => {
        if (this.serverProcess) {
          this.serverProcess.kill("SIGKILL");
          this.isRunning = false;
          this.serverProcess = null;
          resolve();
        }
      }, 5000);
    });

    console.log("WebSocket server stopped");
  }

  /**
   * Create a test WebSocket server script if it doesn't exist
   * @param {string} scriptPath - Path to create the script
   */
  async createTestServerScript(scriptPath) {
    const scriptContent = `
# Test WebSocket Server for integration testing
# This is a simplified version of the standalone_websocket_server.py
import asyncio
import json
import logging
import sys
from typing import Dict, List, Optional, Set, Any
import websockets

# Setup logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler()])
logger = logging.getLogger("test-websocket-server")

class TestWebSocketServer:
    def __init__(self):
        self.connections: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}
        self.host = "localhost"
        self.port = 8000
        self.server = None
        self.running = False

    async def start(self):
        """Start the WebSocket server."""
        if self.running:
            logger.warning("Server already running")
            return

        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port
        )
        self.running = True
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

        # Keep the server running
        await asyncio.Future()

    async def handler(self, websocket, path):
        """Handle incoming WebSocket connections."""
        # Extract device_id from path query params
        device_id = "unknown"
        if "?" in path:
            query = path.split("?")[1]
            params = query.split("&")
            for param in params:
                if param.startswith("deviceId="):
                    device_id = param.split("=")[1]
                    break

        logger.info(f"New connection for device: {device_id}")

        # Register the connection
        if device_id not in self.connections:
            self.connections[device_id] = set()
        self.connections[device_id].add(websocket)

        try:
            # Send initial connected message
            await websocket.send(json.dumps({
                "type": "connection_status",
                "status": "connected",
                "device_id": device_id
            }))

            # Wait for messages from the client
            async for message in websocket:
                logger.info(f"Received message from {device_id}: {message}")

                # Echo the message back for testing
                await websocket.send(message)

                # If this is a subscription message, send a fake shadow update
                try:
                    data = json.loads(message)
                    if data.get("action") == "subscribe" or data.get("type") == "subscribe":
                        # Send a simulated shadow update
                        await asyncio.sleep(0.5)  # Small delay
                        await websocket.send(json.dumps({
                            "type": "shadow_update",
                            "data": {
                                "state": {
                                    "reported": {
                                        "temperature": 140,
                                        "temperature_unit": "F",
                                        "status": "online",
                                        "heating_element": "active",
                                        "timestamp": "2025-04-07T15:00:00.000Z",
                                        "temperatureHistory": [
                                            {
                                              "timestamp": "2025-04-07T14:00:00.000Z",
                                              "value": 137
                                            },
                                            {
                                              "timestamp": "2025-04-07T14:30:00.000Z",
                                              "value": 139
                                            },
                                            {
                                              "timestamp": "2025-04-07T15:00:00.000Z",
                                              "value": 140
                                            }
                                        ]
                                    }
                                }
                            }
                        }))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed for device: {device_id}")
        finally:
            # Unregister the connection
            if device_id in self.connections:
                self.connections[device_id].discard(websocket)
                if not self.connections[device_id]:
                    del self.connections[device_id]

async def main():
    """Main function to start the server."""
    server = TestWebSocketServer()
    await server.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
`;

    // Write the script to the specified path
    fs.writeFileSync(scriptPath, scriptContent, "utf8");
    console.log(`Created test WebSocket server script at ${scriptPath}`);
  }
}

module.exports = new WebSocketServerLauncher();
