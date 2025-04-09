#!/usr/bin/env python3
"""
Manufacturer-Agnostic API Service for IoTSphere

This module provides a standardized API for working with devices from multiple manufacturers,
abstracting away manufacturer-specific details and providing a consistent interface.
"""
import json
import logging
import os
import uuid
from datetime import datetime

import psycopg2
import redis
from psycopg2.extras import RealDictCursor

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_PARAMS = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "user": os.environ.get("DB_USER", "iotsphere"),
    "password": os.environ.get("DB_PASSWORD", "iotsphere"),
    "dbname": os.environ.get("DB_NAME", "iotsphere"),
}

# Redis connection parameters
REDIS_PARAMS = {
    "host": os.environ.get("REDIS_HOST", "localhost"),
    "port": int(os.environ.get("REDIS_PORT", 6379)),
    "password": os.environ.get("REDIS_PASSWORD", None),
    "db": int(os.environ.get("REDIS_DB", 0)),
    "decode_responses": True,
}


class DeviceAPI:
    """
    Manufacturer-agnostic API for IoT devices

    This service:
    - Provides unified access to devices across manufacturers
    - Abstracts away manufacturer-specific details
    - Presents consistent data models for all device types
    - Enables cross-manufacturer analytics and operations
    """

    def __init__(self, db_connection=None, redis_client=None, message_bus=None):
        """
        Initialize device API service

        Args:
            db_connection: Database connection (optional)
            redis_client: Redis client for device state (optional)
            message_bus: Message bus for sending commands (optional)
        """
        # Set up database connection
        self.db_connection = db_connection
        if not self.db_connection:
            try:
                self.db_connection = psycopg2.connect(**DB_PARAMS)
                logger.info("Connected to database")
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                self.db_connection = None

        # Set up Redis client
        self.redis_client = redis_client
        if not self.redis_client:
            try:
                self.redis_client = redis.Redis(**REDIS_PARAMS)
                logger.info("Connected to Redis")
            except Exception as e:
                logger.error(f"Redis connection error: {e}")
                self.redis_client = None

        # Store message bus
        self.message_bus = message_bus

        logger.info("Initialized manufacturer-agnostic device API")

    def get_water_heaters(self, manufacturer=None, model=None, status=None):
        """
        Get list of water heaters with optional filtering

        Args:
            manufacturer (str, optional): Filter by manufacturer
            model (str, optional): Filter by model
            status (str, optional): Filter by connection status

        Returns:
            list: List of water heater devices
        """
        try:
            if not self.db_connection:
                logger.error("No database connection available")
                return []

            # Build query with filters
            query = """
                SELECT dr.device_id, dr.manufacturer, dr.model, dr.serial_number,
                       dr.firmware_version, dr.connection_status, dr.simulated
                FROM device_registry dr
                WHERE dr.device_type = 'water_heater'
            """
            params = []

            # Add filters if provided
            if manufacturer:
                query += " AND dr.manufacturer = %s"
                params.append(manufacturer)

            if model:
                query += " AND dr.model = %s"
                params.append(model)

            if status:
                query += " AND dr.connection_status = %s"
                params.append(status)

            # Execute query
            cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            water_heaters = cursor.fetchall()

            logger.info(f"Retrieved {len(water_heaters)} water heaters")
            return water_heaters

        except Exception as e:
            logger.error(f"Error retrieving water heaters: {e}")
            return []

    def get_water_heater_by_id(self, device_id):
        """
        Get detailed information about a specific water heater

        Args:
            device_id (str): Water heater device ID

        Returns:
            dict: Water heater details with current state
        """
        try:
            if not self.db_connection:
                logger.error("No database connection available")
                return None

            # Get device details from database
            query = """
                SELECT dr.device_id, dr.manufacturer, dr.model, dr.serial_number,
                       dr.firmware_version, dr.registration_date, dr.last_connection,
                       dr.connection_status, dr.simulated,
                       whm.capacity_gallons, whm.energy_source, whm.btu_rating,
                       whm.efficiency_rating, whm.temperature_min, whm.temperature_max,
                       whm.installation_date, whm.warranty_expiration, whm.tank_type
                FROM device_registry dr
                LEFT JOIN water_heater_metadata whm ON dr.device_id = whm.device_id
                WHERE dr.device_id = %s AND dr.device_type = 'water_heater'
            """

            cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, (device_id,))
            device = cursor.fetchone()

            if not device:
                logger.warning(f"Water heater not found: {device_id}")
                return None

            # Format the result
            result = {
                "device_id": device["device_id"],
                "manufacturer": device["manufacturer"],
                "model": device["model"],
                "serial_number": device["serial_number"],
                "firmware_version": device["firmware_version"],
                "registration_date": device["registration_date"].isoformat()
                if device["registration_date"]
                else None,
                "last_connection": device["last_connection"].isoformat()
                if device["last_connection"]
                else None,
                "connection_status": device["connection_status"],
                "simulated": device["simulated"],
                "metadata": {
                    "capacity_gallons": device["capacity_gallons"],
                    "energy_source": device["energy_source"],
                    "btu_rating": device["btu_rating"],
                    "efficiency_rating": device["efficiency_rating"],
                    "temperature_min": device["temperature_min"],
                    "temperature_max": device["temperature_max"],
                    "installation_date": device["installation_date"].isoformat()
                    if device["installation_date"]
                    else None,
                    "warranty_expiration": device["warranty_expiration"].isoformat()
                    if device["warranty_expiration"]
                    else None,
                    "tank_type": device["tank_type"],
                },
            }

            # Get current device state from Redis
            if self.redis_client:
                reported_state_key = f"device:{device_id}:reported"
                reported_state = self.redis_client.get(reported_state_key)

                if reported_state:
                    try:
                        result["state"] = json.loads(reported_state)
                    except json.JSONDecodeError:
                        logger.error(f"Error decoding device state for {device_id}")
                        result["state"] = {}
                else:
                    result["state"] = {}

            # Get recent telemetry
            recent_telemetry_query = """
                SELECT timestamp, temperature_current, temperature_setpoint,
                       heating_status, power_consumption_watts, water_flow_gpm,
                       error_code, mode
                FROM water_heater_telemetry
                WHERE device_id = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """

            cursor.execute(recent_telemetry_query, (device_id,))
            recent_telemetry = cursor.fetchone()

            if recent_telemetry:
                result["latest_telemetry"] = {
                    "timestamp": recent_telemetry["timestamp"].isoformat(),
                    "temperature_current": recent_telemetry["temperature_current"],
                    "temperature_setpoint": recent_telemetry["temperature_setpoint"],
                    "heating_status": recent_telemetry["heating_status"],
                    "power_consumption_watts": recent_telemetry[
                        "power_consumption_watts"
                    ],
                    "water_flow_gpm": recent_telemetry["water_flow_gpm"],
                    "error_code": recent_telemetry["error_code"],
                    "mode": recent_telemetry["mode"],
                }

            logger.info(f"Retrieved details for water heater: {device_id}")
            return result

        except Exception as e:
            logger.error(f"Error retrieving water heater details: {e}")
            return None

    def get_operational_summary(self, device_ids=None, include_maintenance=True):
        """
        Get operational summary for water heaters

        Args:
            device_ids (list, optional): List of device IDs to include
            include_maintenance (bool): Whether to include maintenance predictions

        Returns:
            list: Operational summaries for water heaters
        """
        try:
            if not self.db_connection:
                logger.error("No database connection available")
                return []

            # If no device IDs provided, get all water heaters
            if not device_ids:
                device_query = """
                    SELECT device_id FROM device_registry
                    WHERE device_type = 'water_heater'
                """
                cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute(device_query)
                devices = cursor.fetchall()
                device_ids = [d["device_id"] for d in devices]

            if not device_ids:
                return []

            # Build query for operational data
            device_list = ",".join([f"'{d}'" for d in device_ids])

            operational_query = f"""
                WITH daily_stats AS (
                    SELECT
                        device_id,
                        AVG(temperature_current) as avg_temperature,
                        COUNT(*) FILTER (WHERE heating_status = TRUE AND
                                      LAG(heating_status) OVER (PARTITION BY device_id ORDER BY timestamp) = FALSE)
                        as heating_cycles,
                        SUM(CASE WHEN heating_status = TRUE THEN 1 ELSE 0 END) as heating_minutes,
                        AVG(power_consumption_watts) as avg_power
                    FROM water_heater_telemetry
                    WHERE device_id IN ({device_list})
                    AND timestamp > NOW() - INTERVAL '24 hours'
                    GROUP BY device_id
                )
                SELECT
                    device_id,
                    avg_temperature,
                    heating_cycles as heating_cycles_24h,
                    heating_minutes as total_heating_time_24h,
                    (heating_minutes * avg_power / 60000.0) as energy_used_24h
                FROM daily_stats
            """

            cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(operational_query)
            operational_data = cursor.fetchall()

            # Create result with operational data
            result = []
            for device_data in operational_data:
                device_summary = {
                    "device_id": device_data["device_id"],
                    "operational": {
                        "avg_temperature": device_data["avg_temperature"],
                        "heating_cycles_24h": device_data["heating_cycles_24h"],
                        "total_heating_time_24h": device_data["total_heating_time_24h"],
                        "energy_used_24h": device_data["energy_used_24h"],
                    },
                }
                result.append(device_summary)

            # Add maintenance predictions if requested
            if include_maintenance:
                maintenance_query = f"""
                    SELECT device_id, health_score, estimated_remaining_life,
                           maintenance_due, next_maintenance_date, issues
                    FROM device_health_assessment
                    WHERE device_id IN ({device_list})
                    AND assessment_date > NOW() - INTERVAL '24 hours'
                    ORDER BY assessment_date DESC
                """

                cursor.execute(maintenance_query)
                maintenance_data = cursor.fetchall()

                # Add maintenance data to results
                maintenance_by_device = {m["device_id"]: m for m in maintenance_data}

                for device_summary in result:
                    device_id = device_summary["device_id"]
                    if device_id in maintenance_by_device:
                        maint = maintenance_by_device[device_id]

                        # Parse issues JSON if present
                        issues = []
                        if maint["issues"]:
                            try:
                                issues = json.loads(maint["issues"])
                            except json.JSONDecodeError:
                                logger.error(
                                    f"Error parsing maintenance issues for {device_id}"
                                )

                        device_summary["maintenance"] = {
                            "health_score": maint["health_score"],
                            "estimated_remaining_life": maint[
                                "estimated_remaining_life"
                            ],
                            "maintenance_due": maint["maintenance_due"],
                            "next_maintenance_date": maint[
                                "next_maintenance_date"
                            ].isoformat()
                            if maint["next_maintenance_date"]
                            else None,
                            "issues": issues,
                        }
                    else:
                        # No maintenance data available
                        device_summary["maintenance"] = {
                            "health_score": None,
                            "estimated_remaining_life": None,
                            "maintenance_due": None,
                            "next_maintenance_date": None,
                            "issues": [],
                        }

            logger.info(
                f"Retrieved operational summary for {len(result)} water heaters"
            )
            return result

        except Exception as e:
            logger.error(f"Error retrieving operational summary: {e}")
            return []

    def send_command(self, device_id, command):
        """
        Send command to device via message bus

        Args:
            device_id (str): Target device identifier
            command (dict): Command data with parameters

        Returns:
            dict: Command result with command ID
        """
        if not self.message_bus:
            logger.error("No message bus available for sending commands")
            return {"success": False, "error": "Message bus not available"}

        try:
            # Generate command ID
            command_id = str(uuid.uuid4())

            # Create command event
            command_event = {
                "event_id": str(uuid.uuid4()),
                "event_type": "device.command",
                "device_id": device_id,
                "command_id": command_id,
                "command": command.get("command"),
                "params": command.get("params", {}),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Publish to message bus
            self.message_bus.publish("device.command", command_event)

            logger.info(f"Sent command {command.get('command')} to device {device_id}")
            return {
                "success": True,
                "command_id": command_id,
                "timestamp": command_event["timestamp"],
            }

        except Exception as e:
            logger.error(f"Error sending command to device {device_id}: {e}")
            return {"success": False, "error": str(e)}

    def get_device_capabilities(self, device_id):
        """
        Get capabilities for a specific device

        Args:
            device_id (str): Device identifier

        Returns:
            list: Device capabilities
        """
        try:
            if not self.db_connection:
                logger.error("No database connection available")
                return []

            query = """
                SELECT capability_name, capability_type, description, parameters
                FROM device_capabilities
                WHERE device_id = %s
            """

            cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, (device_id,))
            capabilities = cursor.fetchall()

            # Format capabilities
            result = []
            for cap in capabilities:
                capability = {
                    "name": cap["capability_name"],
                    "type": cap["capability_type"],
                    "description": cap["description"],
                }

                # Parse parameters if present
                if cap["parameters"]:
                    try:
                        capability["parameters"] = cap["parameters"]
                    except Exception:
                        capability["parameters"] = {}

                result.append(capability)

            logger.info(f"Retrieved {len(result)} capabilities for device {device_id}")
            return result

        except Exception as e:
            logger.error(f"Error retrieving device capabilities: {e}")
            return []
