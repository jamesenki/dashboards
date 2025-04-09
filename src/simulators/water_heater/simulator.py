#!/usr/bin/env python3
"""
Water Heater Simulator for IoTSphere

This module provides a realistic simulation of water heater devices,
generating telemetry and responding to commands using MQTT protocol.
The simulator implements the same interface as a real water heater
would, making it suitable for testing and demonstration purposes.
"""
import json
import logging
import os
import random
import threading
import time
from datetime import datetime

import paho.mqtt.client as mqtt

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default MQTT configuration
DEFAULT_MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
DEFAULT_MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
DEFAULT_MQTT_USERNAME = os.environ.get("MQTT_USERNAME", None)
DEFAULT_MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", None)


class WaterHeaterSimulator:
    """
    Simulates a water heater device with realistic behavior.

    This simulator:
    - Connects to MQTT broker to send telemetry and receive commands
    - Simulates realistic water heater behavior (heating cycles, temperature changes)
    - Responds to commands similar to a real device
    - Includes clear indication of simulated status
    """

    def __init__(
        self, device_id, model, manufacturer, initial_state=None, mqtt_client=None
    ):
        """
        Initialize water heater simulator

        Args:
            device_id (str): Unique identifier for this device
            model (str): Water heater model name
            manufacturer (str): Manufacturer name
            initial_state (dict, optional): Initial state values
            mqtt_client: Optional pre-configured MQTT client
        """
        self.device_id = device_id
        self.model = model
        self.manufacturer = manufacturer
        self.simulated = True  # Always true for simulators

        # Set default initial state if not provided
        if initial_state is None:
            initial_state = {
                "temperature_current": 120.0,  # Current water temperature (F)
                "temperature_setpoint": 125.0,  # Target temperature (F)
                "heating_status": False,  # Whether heating element is active
                "power_consumption_watts": 0.0,  # Current power draw
                "water_flow_gpm": 0.0,  # Water flow in gallons per minute
                "mode": "standby",  # Operating mode (standby, heating, eco)
                "error_code": None,  # Error code if present
            }

        # Initialize state with these values
        self.state = initial_state.copy()

        # Add metadata
        self.metadata = {
            "model": model,
            "manufacturer": manufacturer,
            "device_id": device_id,
            "firmware_version": "1.0.0",
            "simulated": True,
        }

        # Set up simulation parameters
        self.max_power_watts = 4500.0  # Maximum power when heating
        self.standby_power_watts = 10.0  # Power when not actively heating
        self.heating_rate = 0.2  # Temperature increase per second when heating
        self.cooling_rate = 0.05  # Temperature decrease per second when not heating

        # Set up MQTT client
        self.mqtt_client = mqtt_client or mqtt.Client()
        if DEFAULT_MQTT_USERNAME and DEFAULT_MQTT_PASSWORD:
            self.mqtt_client.username_pw_set(
                DEFAULT_MQTT_USERNAME, DEFAULT_MQTT_PASSWORD
            )

        # Simulation control
        self.running = False
        self.simulation_thread = None
        self.simulation_interval = 1.0  # Update interval in seconds

        logger.info(
            f"Initialized water heater simulator: {device_id} ({manufacturer} {model})"
        )

    def connect(self):
        """Connect to MQTT broker and subscribe to command topic"""
        try:
            logger.info(
                f"Connecting to MQTT broker at {DEFAULT_MQTT_BROKER}:{DEFAULT_MQTT_PORT}"
            )
            self.mqtt_client.connect(DEFAULT_MQTT_BROKER, DEFAULT_MQTT_PORT)

            # Subscribe to command topic
            command_topic = f"iotsphere/devices/{self.device_id}/commands"
            self.mqtt_client.subscribe(command_topic)
            self.mqtt_client.on_message = self.on_message

            # Start MQTT loop in the background
            self.mqtt_client.loop_start()

            logger.info(f"Connected to MQTT broker and subscribed to: {command_topic}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def disconnect(self):
        """Disconnect from MQTT broker"""
        try:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info(f"Disconnected from MQTT broker: {self.device_id}")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {e}")
            return False

    def publish_telemetry(self):
        """Publish current device state as telemetry"""
        try:
            # Create telemetry payload
            telemetry = self.state.copy()

            # Add important metadata
            telemetry["device_id"] = self.device_id
            telemetry["timestamp"] = datetime.utcnow().isoformat()
            telemetry["simulated"] = True

            # Publish to telemetry topic
            topic = f"iotsphere/devices/{self.device_id}/telemetry"
            payload = json.dumps(telemetry)
            self.mqtt_client.publish(topic, payload)

            logger.debug(f"Published telemetry for device {self.device_id}")
            return True

        except Exception as e:
            logger.error(f"Error publishing telemetry: {e}")
            return False

    def publish_event(self, event_type, severity, message, details=None):
        """Publish a device event"""
        try:
            # Create event payload
            event = {
                "device_id": self.device_id,
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "severity": severity,
                "message": message,
                "details": details or {},
                "simulated": True,
            }

            # Publish to events topic
            topic = f"iotsphere/devices/{self.device_id}/events"
            payload = json.dumps(event)
            self.mqtt_client.publish(topic, payload)

            logger.info(
                f"Published event for device {self.device_id}: {event_type} - {message}"
            )
            return True

        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            return False

    def on_message(self, client, userdata, message):
        """
        Handle incoming MQTT messages (commands)

        Args:
            client: MQTT client instance
            userdata: User data (not used)
            message: MQTT message object
        """
        try:
            # Decode message payload
            payload = message.payload.decode("utf-8")
            command = json.loads(payload)

            logger.info(
                f"Received command for device {self.device_id}: {command.get('command')}"
            )

            # Process command
            result = self.handle_command(command)

            # Publish command response
            response_topic = f"iotsphere/devices/{self.device_id}/command_response"
            response = {
                "device_id": self.device_id,
                "timestamp": datetime.utcnow().isoformat(),
                "command_id": command.get("command_id"),
                "command": command.get("command"),
                "status": "success" if result else "error",
                "message": "Command processed successfully"
                if result
                else "Failed to process command",
                "simulated": True,
            }

            self.mqtt_client.publish(response_topic, json.dumps(response))

        except Exception as e:
            logger.error(f"Error processing command: {e}")

            # Publish error response
            error_topic = f"iotsphere/devices/{self.device_id}/command_response"
            error_response = {
                "device_id": self.device_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "message": f"Error processing command: {str(e)}",
                "simulated": True,
            }
            self.mqtt_client.publish(error_topic, json.dumps(error_response))

    def handle_command(self, command):
        """
        Process device command

        Args:
            command (dict): Command payload

        Returns:
            bool: True if command was processed successfully, False otherwise
        """
        cmd = command.get("command", "").lower()

        if cmd == "set_temperature":
            # Set temperature setpoint
            setpoint = command.get("setpoint")
            if setpoint is not None:
                self.state["temperature_setpoint"] = float(setpoint)
                self.publish_event(
                    "temperature_setpoint_changed",
                    "info",
                    f"Temperature setpoint changed to {setpoint}°F",
                )
                return True

        elif cmd == "set_mode":
            # Set operating mode
            mode = command.get("mode", "").lower()
            valid_modes = ["standby", "heating", "eco", "vacation"]

            if mode in valid_modes:
                self.state["mode"] = mode

                # Update heating status based on mode
                if mode == "standby":
                    self.state["heating_status"] = False
                    self.state["power_consumption_watts"] = self.standby_power_watts

                self.publish_event(
                    "mode_changed", "info", f"Operating mode changed to {mode}"
                )
                return True
            else:
                return False

        elif cmd == "power_toggle":
            # Toggle power state
            current_mode = self.state["mode"]

            if current_mode != "standby":
                # Turn off
                self.state["mode"] = "standby"
                self.state["heating_status"] = False
                self.state["power_consumption_watts"] = self.standby_power_watts
                self.publish_event("power_changed", "info", "Device powered off")
            else:
                # Turn on
                self.state["mode"] = "heating"
                self.publish_event("power_changed", "info", "Device powered on")

            return True

        elif cmd == "inject_error":
            # Simulate an error condition (for testing)
            error_code = command.get("error_code", "E01")
            self.state["error_code"] = error_code
            self.publish_event(
                "error_occurred",
                "error",
                f"Error condition: {error_code}",
                {"error_code": error_code},
            )
            return True

        elif cmd == "clear_error":
            # Clear error condition
            self.state["error_code"] = None
            self.publish_event("error_cleared", "info", "Error condition cleared")
            return True

        else:
            logger.warning(f"Unknown command: {cmd}")
            return False

    def update_simulation(self):
        """Update simulated state based on current conditions"""
        current_temp = self.state["temperature_current"]
        setpoint = self.state["temperature_setpoint"]
        mode = self.state["mode"]

        # Determine if we should be heating
        if mode == "standby" or current_temp >= setpoint:
            self.state["heating_status"] = False
        elif mode == "heating" and current_temp < setpoint:
            self.state["heating_status"] = True

        # Update temperature based on heating status
        if self.state["heating_status"]:
            # Heating up
            new_temp = current_temp + (self.heating_rate * self.simulation_interval)
            # Don't exceed setpoint by too much
            new_temp = min(new_temp, setpoint + 1.0)
            self.state["temperature_current"] = new_temp

            # Set power consumption during heating
            self.state["power_consumption_watts"] = self.max_power_watts

            # Simulate slight water flow variations during heating
            self.state["water_flow_gpm"] = round(random.uniform(0.1, 0.5), 2)

        else:
            # Cooling down
            new_temp = current_temp - (self.cooling_rate * self.simulation_interval)
            self.state["temperature_current"] = new_temp

            # Set standby power consumption
            self.state["power_consumption_watts"] = self.standby_power_watts

            # No water flow when not heating
            self.state["water_flow_gpm"] = 0.0

        # Round temperature to 1 decimal place for readability
        self.state["temperature_current"] = round(self.state["temperature_current"], 1)

        # Randomly simulate error condition (very rarely)
        if (
            random.random() < 0.0001 and not self.state["error_code"]
        ):  # 0.01% chance per update
            error_code = random.choice(["E01", "E02", "E03", "E04"])
            self.state["error_code"] = error_code
            self.publish_event(
                "error_occurred",
                "error",
                f"Error condition: {error_code}",
                {"error_code": error_code},
            )

    def run_simulation(self):
        """Main simulation loop - runs in a separate thread"""
        logger.info(f"Starting simulation loop for device {self.device_id}")

        # Initial connection
        if not hasattr(self, "connected") or not self.connected:
            self.connect()
            self.connected = True

        last_telemetry_time = 0
        telemetry_interval = 5  # Send telemetry every 5 seconds

        while self.running:
            # Update simulation state
            self.update_simulation()

            # Publish telemetry at the defined interval
            current_time = time.time()
            if current_time - last_telemetry_time >= telemetry_interval:
                self.publish_telemetry()
                last_telemetry_time = current_time

            # Sleep until next update
            time.sleep(self.simulation_interval)

        logger.info(f"Simulation loop stopped for device {self.device_id}")

    def start(self):
        """Start the simulation"""
        if not self.running:
            self.running = True

            # Create and start simulation thread
            self.simulation_thread = threading.Thread(
                target=self.run_simulation,
                daemon=True,  # Thread will exit when main program exits
            )
            self.simulation_thread.start()

            logger.info(f"Started water heater simulation for device {self.device_id}")
            return True

        logger.warning(f"Simulation already running for device {self.device_id}")
        return False

    def stop(self):
        """Stop the simulation"""
        if self.running:
            self.running = False

            # Wait for simulation thread to end
            if self.simulation_thread and self.simulation_thread.is_alive():
                self.simulation_thread.join(timeout=2.0)

            # Disconnect from MQTT
            self.disconnect()

            logger.info(f"Stopped water heater simulation for device {self.device_id}")
            return True

        logger.warning(f"Simulation already stopped for device {self.device_id}")
        return False


class WaterHeaterSimulationManager:
    """
    Manages multiple water heater simulator instances.
    Allows coordinated control of multiple simulated devices.
    """

    def __init__(self):
        """Initialize the simulation manager"""
        self.simulators = {}
        logger.info("Initialized Water Heater Simulation Manager")

    def create_simulator(self, device_id, model, manufacturer, initial_state=None):
        """
        Create a new water heater simulator

        Args:
            device_id (str): Unique device identifier
            model (str): Device model
            manufacturer (str): Device manufacturer
            initial_state (dict, optional): Initial state for the simulator

        Returns:
            WaterHeaterSimulator: The created simulator instance
        """
        # Create simulator
        simulator = WaterHeaterSimulator(
            device_id=device_id,
            model=model,
            manufacturer=manufacturer,
            initial_state=initial_state,
        )

        # Store in simulators dictionary
        self.simulators[device_id] = simulator

        logger.info(f"Created simulator: {device_id} ({manufacturer} {model})")
        return simulator

    def start_simulator(self, device_id):
        """Start a specific simulator by device ID"""
        if device_id in self.simulators:
            return self.simulators[device_id].start()

        logger.error(f"Simulator not found: {device_id}")
        return False

    def stop_simulator(self, device_id):
        """Stop a specific simulator by device ID"""
        if device_id in self.simulators:
            return self.simulators[device_id].stop()

        logger.error(f"Simulator not found: {device_id}")
        return False

    def start_all(self):
        """Start all simulators"""
        for device_id, simulator in self.simulators.items():
            simulator.start()

        return len(self.simulators) > 0

    def stop_all(self):
        """Stop all simulators"""
        for device_id, simulator in self.simulators.items():
            simulator.stop()

        return True

    def create_fleet(self, count, manufacturer=None, model=None):
        """
        Create a fleet of simulated water heaters

        Args:
            count (int): Number of simulators to create
            manufacturer (str, optional): Manufacturer name
            model (str, optional): Model name

        Returns:
            list: List of created device IDs
        """
        created_devices = []

        # Define manufacturer options if not specified
        manufacturers = (
            [manufacturer]
            if manufacturer
            else ["Rheem", "AO Smith", "Bradford White", "State", "Navien"]
        )

        # Define model options if not specified
        models = {
            "Rheem": ["Performance", "Gladiator", "ProTerra", "EcoNet", "Marathon"],
            "AO Smith": ["Vertex", "Signature", "ProLine", "Voltex", "NextGen"],
            "Bradford White": [
                "eF Series",
                "AeroTherm",
                "TTW",
                "Defender",
                "ElectriFLEX",
            ],
            "State": ["Premier", "ProLine", "GeoThermal", "SolarLine", "ElectricFlex"],
            "Navien": ["NPE-A", "NPN", "NCB", "NFC", "NFB"],
        }

        # Create simulators
        for i in range(count):
            # Select manufacturer and model
            selected_manufacturer = manufacturer or random.choice(manufacturers)
            selected_model = model

            if not selected_model:
                if selected_manufacturer in models:
                    selected_model = random.choice(models[selected_manufacturer])
                else:
                    selected_model = f"Model {chr(65 + random.randint(0, 25))}{random.randint(1, 999)}"

            # Create unique device ID
            device_id = f"sim-water-heater-{selected_manufacturer.lower()}-{i+1:03d}"

            # Randomize initial state
            initial_state = {
                "temperature_current": round(random.uniform(110.0, 140.0), 1),
                "temperature_setpoint": random.choice([120.0, 125.0, 130.0, 135.0]),
                "heating_status": random.choice([True, False]),
                "power_consumption_watts": 0.0,  # Will be updated in simulation
                "water_flow_gpm": 0.0,  # Will be updated in simulation
                "mode": random.choice(["standby", "heating", "eco"]),
                "error_code": None,
            }

            # Create simulator and add to dictionary
            simulator = self.create_simulator(
                device_id=device_id,
                model=selected_model,
                manufacturer=selected_manufacturer,
                initial_state=initial_state,
            )

            created_devices.append(device_id)

        logger.info(f"Created fleet of {count} water heater simulators")
        return created_devices


# Example usage
if __name__ == "__main__":
    # Create a simulation manager
    manager = WaterHeaterSimulationManager()

    # Create a fleet of 5 water heaters
    device_ids = manager.create_fleet(5)

    # Start all simulators
    manager.start_all()

    try:
        # Run for a while
        print("Simulators running. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Stop all simulators on exit
        manager.stop_all()
        print("Simulators stopped.")
