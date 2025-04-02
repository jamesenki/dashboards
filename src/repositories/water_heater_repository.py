"""
Repository interface and implementations for water heater data access.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import os
import logging
from datetime import datetime
import uuid
import sqlite3

from src.models.water_heater import (
    WaterHeater, 
    WaterHeaterMode,
    WaterHeaterStatus, 
    WaterHeaterReading,
    WaterHeaterType,
    WaterHeaterDiagnosticCode
)
from src.utils.dummy_data import dummy_data

# Setup logging
logger = logging.getLogger(__name__)

class WaterHeaterRepository(ABC):
    """Abstract base class for water heater repositories."""
    
    @abstractmethod
    async def get_water_heaters(self) -> List[WaterHeater]:
        """Get all water heaters."""
        pass
    
    @abstractmethod
    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        """Get a specific water heater by ID."""
        pass
    
    @abstractmethod
    async def create_water_heater(self, water_heater: WaterHeater) -> WaterHeater:
        """Create a new water heater."""
        pass
    
    @abstractmethod
    async def update_water_heater(self, device_id: str, updates: Dict[str, Any]) -> Optional[WaterHeater]:
        """Update a water heater with specified changes."""
        pass
    
    @abstractmethod
    async def add_reading(self, device_id: str, reading: WaterHeaterReading) -> Optional[WaterHeater]:
        """Add a new reading to a water heater."""
        pass
    
    @abstractmethod
    async def get_readings(self, device_id: str, limit: int = 24) -> List[WaterHeaterReading]:
        """Get recent readings for a water heater."""
        pass


class MockWaterHeaterRepository(WaterHeaterRepository):
    """Mock implementation of water heater repository using dummy data."""
    
    async def get_water_heaters(self) -> List[WaterHeater]:
        """Get all water heaters from mock data."""
        return dummy_data.get_water_heaters()
    
    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        """Get a specific water heater by ID from mock data."""
        return dummy_data.get_water_heater(device_id)
    
    async def create_water_heater(self, water_heater: WaterHeater) -> WaterHeater:
        """Create a new water heater in mock data."""
        # Generate ID if not provided
        if not water_heater.id:
            water_heater.id = f"wh-{str(uuid.uuid4())[:8]}"
        
        # Set creation timestamp
        if not water_heater.last_seen:
            water_heater.last_seen = datetime.now()
        
        # Initialize readings if not provided
        if not water_heater.readings:
            water_heater.readings = []
        
        return dummy_data.add_water_heater(water_heater)
    
    async def update_water_heater(self, device_id: str, updates: Dict[str, Any]) -> Optional[WaterHeater]:
        """Update a water heater in mock data."""
        return dummy_data.update_water_heater(device_id, updates)
    
    async def add_reading(self, device_id: str, reading: WaterHeaterReading) -> Optional[WaterHeater]:
        """Add a new reading to a water heater in mock data."""
        water_heater = await self.get_water_heater(device_id)
        if not water_heater:
            return None
        
        # Create a new list with the new reading at the beginning
        water_heater.readings = [reading] + (water_heater.readings or [])
        
        # Update last_seen timestamp
        water_heater.last_seen = datetime.now()
        
        # Update current temperature
        water_heater.current_temperature = reading.temperature
        
        return dummy_data.update_water_heater(device_id, {
            "readings": water_heater.readings,
            "last_seen": water_heater.last_seen,
            "current_temperature": water_heater.current_temperature
        })
    
    async def get_readings(self, device_id: str, limit: int = 24) -> List[WaterHeaterReading]:
        """Get recent readings for a water heater from mock data."""
        water_heater = await self.get_water_heater(device_id)
        if not water_heater or not water_heater.readings:
            return []
        
        return water_heater.readings[:limit]


class SQLiteWaterHeaterRepository(WaterHeaterRepository):
    """SQLite implementation of water heater repository."""
    
    def __init__(self, db_path: str = "data/iotsphere.db"):
        """Initialize with database path."""
        self.db_path = db_path
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure required tables exist in the database."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            self._create_tables(conn)
            conn.commit()
        except Exception as e:
            logger.error(f"Error ensuring water heater tables: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def _create_tables(self, conn):
        """Create necessary tables if they don't exist."""
        cursor = conn.cursor()
        
        # Create water_heaters table if not exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_heaters (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            brand TEXT,
            model TEXT,
            manufacturer TEXT,
            size TEXT,
            type TEXT,
            location TEXT,
            target_temperature REAL,
            current_temperature REAL,
            mode TEXT,
            status TEXT,
            installation_date TEXT,
            warranty_expiry TEXT,
            last_maintenance TEXT,
            efficiency_rating REAL,
            last_seen TEXT,
            health_status TEXT,
            metadata TEXT
        )
        """)
        
        # Create water_heater_readings table if not exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_heater_readings (
            id TEXT PRIMARY KEY,
            water_heater_id TEXT NOT NULL,
            temperature REAL NOT NULL,
            pressure REAL,
            energy_usage REAL,
            flow_rate REAL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (water_heater_id) REFERENCES water_heaters(id) ON DELETE CASCADE
        )
        """)
        
        # Create water_heater_diagnostic_codes table if not exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_heater_diagnostic_codes (
            id TEXT PRIMARY KEY,
            water_heater_id TEXT NOT NULL,
            code TEXT NOT NULL,
            description TEXT,
            severity TEXT,
            timestamp TEXT NOT NULL,
            resolved INTEGER DEFAULT 0,
            resolved_at TEXT,
            FOREIGN KEY (water_heater_id) REFERENCES water_heaters(id) ON DELETE CASCADE
        )
        """)
        
        # Create configuration tables for health status and alerts
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_heater_health_config (
            id TEXT PRIMARY KEY,
            metric TEXT NOT NULL,
            threshold REAL,
            status TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_heater_alert_rules (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            condition TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT,
            enabled INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
    
    async def get_water_heaters(self) -> List[WaterHeater]:
        """Get all water heaters from the database."""
        conn = None
        water_heaters = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all water heaters
            cursor.execute("SELECT * FROM water_heaters")
            rows = cursor.fetchall()
            
            for row in rows:
                water_heater = self._row_to_water_heater(conn, row)
                water_heaters.append(water_heater)
                
        except Exception as e:
            logger.error(f"Error getting water heaters: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
                
        return water_heaters
    
    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        """Get a specific water heater by ID from the database."""
        conn = None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the water heater
            cursor.execute("SELECT * FROM water_heaters WHERE id = ?", (device_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return self._row_to_water_heater(conn, row)
                
        except Exception as e:
            logger.error(f"Error getting water heater {device_id}: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def create_water_heater(self, water_heater: WaterHeater) -> WaterHeater:
        """Create a new water heater in the database."""
        conn = None
        
        # Generate ID if not provided
        if not water_heater.id:
            water_heater.id = f"wh-{str(uuid.uuid4())[:8]}"
        
        # Set creation timestamp
        if not water_heater.last_seen:
            water_heater.last_seen = datetime.now()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert water heater
            cursor.execute("""
            INSERT INTO water_heaters (
                id, name, model, manufacturer, target_temperature, current_temperature, 
                status, mode, installation_date, warranty_expiry, last_maintenance, 
                last_seen, health_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                water_heater.id,
                water_heater.name,
                water_heater.model,
                water_heater.manufacturer,
                water_heater.target_temperature,
                water_heater.current_temperature,
                water_heater.status.value if water_heater.status else None,
                water_heater.mode.value if water_heater.mode else None,
                water_heater.installation_date.isoformat() if water_heater.installation_date else None,
                water_heater.warranty_expiry.isoformat() if water_heater.warranty_expiry else None,
                water_heater.last_maintenance.isoformat() if water_heater.last_maintenance else None,
                water_heater.last_seen.isoformat() if water_heater.last_seen else None,
                water_heater.health_status
            ))
            
            # Add any readings
            if water_heater.readings:
                for reading in water_heater.readings:
                    self._add_reading_to_db(conn, water_heater.id, reading)
            
            # Add any diagnostic codes
            if water_heater.diagnostic_codes:
                for code in water_heater.diagnostic_codes:
                    self._add_diagnostic_code_to_db(conn, water_heater.id, code)
            
            conn.commit()
            
            # Return the created water heater
            return await self.get_water_heater(water_heater.id)
                
        except Exception as e:
            logger.error(f"Error creating water heater: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    async def update_water_heater(self, device_id: str, updates: Dict[str, Any]) -> Optional[WaterHeater]:
        """Update a water heater in the database."""
        conn = None
        
        # Verify water heater exists
        water_heater = await self.get_water_heater(device_id)
        if not water_heater:
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build update SQL
            fields = []
            values = []
            
            for key, value in updates.items():
                if key in ['readings', 'diagnostic_codes']:
                    # These are handled separately
                    continue
                    
                if key == 'mode' and isinstance(value, WaterHeaterMode):
                    value = value.value
                    
                if key == 'status' and isinstance(value, WaterHeaterStatus):
                    value = value.value
                    
                if isinstance(value, datetime):
                    value = value.isoformat()
                    
                fields.append(f"{key} = ?")
                values.append(value)
            
            if fields:
                sql = f"UPDATE water_heaters SET {', '.join(fields)} WHERE id = ?"
                values.append(device_id)
                cursor.execute(sql, values)
            
            conn.commit()
            
            # Return the updated water heater
            return await self.get_water_heater(device_id)
                
        except Exception as e:
            logger.error(f"Error updating water heater {device_id}: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    async def add_reading(self, device_id: str, reading: WaterHeaterReading) -> Optional[WaterHeater]:
        """Add a new reading to a water heater in the database."""
        conn = None
        
        # Verify water heater exists
        water_heater = await self.get_water_heater(device_id)
        if not water_heater:
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Add the reading
            self._add_reading_to_db(conn, device_id, reading)
            
            # Update current temperature and last_seen
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE water_heaters 
            SET current_temperature = ?, last_seen = ? 
            WHERE id = ?
            """, (reading.temperature, datetime.now().isoformat(), device_id))
            
            conn.commit()
            
            # Return the updated water heater
            return await self.get_water_heater(device_id)
                
        except Exception as e:
            logger.error(f"Error adding reading for water heater {device_id}: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    async def get_readings(self, device_id: str, limit: int = 24) -> List[WaterHeaterReading]:
        """Get recent readings for a water heater from the database."""
        conn = None
        readings = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get readings ordered by timestamp (newest first)
            cursor.execute("""
            SELECT id, temperature, pressure, energy_usage, flow_rate, timestamp 
            FROM water_heater_readings 
            WHERE water_heater_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (device_id, limit))
            
            rows = cursor.fetchall()
            
            for row in rows:
                reading = WaterHeaterReading(
                    id=row[0],
                    temperature=row[1],
                    pressure=row[2],
                    energy_usage=row[3],
                    flow_rate=row[4],
                    timestamp=datetime.fromisoformat(row[5])
                )
                readings.append(reading)
                
        except Exception as e:
            logger.error(f"Error getting readings for water heater {device_id}: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
                
        return readings
        
    async def get_health_configuration(self) -> Dict[str, Any]:
        """Get health configuration for water heaters."""
        conn = None
        config = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT metric, threshold, status, description 
            FROM water_heater_health_config
            """)
            
            rows = cursor.fetchall()
            
            for row in rows:
                metric, threshold, status, description = row
                config[metric] = {
                    "threshold": threshold,
                    "status": status,
                    "description": description
                }
                
        except Exception as e:
            logger.error(f"Error getting health configuration: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
                
        return config
    
    async def set_health_configuration(self, config: Dict[str, Dict[str, Any]]) -> None:
        """Set health configuration for water heaters."""
        conn = None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear existing configuration
            cursor.execute("DELETE FROM water_heater_health_config")
            
            # Insert new configuration
            now = datetime.now().isoformat()
            for metric, settings in config.items():
                cursor.execute("""
                INSERT INTO water_heater_health_config 
                (id, metric, threshold, status, description, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    metric,
                    settings.get("threshold"),
                    settings.get("status"),
                    settings.get("description", ""),
                    now,
                    now
                ))
            
            conn.commit()
                
        except Exception as e:
            logger.error(f"Error setting health configuration: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    async def get_alert_rules(self) -> List[Dict[str, Any]]:
        """Get alert rules for water heaters."""
        conn = None
        rules = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT id, name, condition, severity, message, enabled 
            FROM water_heater_alert_rules
            """)
            
            rows = cursor.fetchall()
            
            for row in rows:
                rule_id, name, condition, severity, message, enabled = row
                rules.append({
                    "id": rule_id,
                    "name": name,
                    "condition": condition,
                    "severity": severity,
                    "message": message,
                    "enabled": bool(enabled)
                })
                
        except Exception as e:
            logger.error(f"Error getting alert rules: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
                
        return rules
    
    async def add_alert_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new alert rule."""
        conn = None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            rule_id = rule.get("id") or str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            cursor.execute("""
            INSERT INTO water_heater_alert_rules 
            (id, name, condition, severity, message, enabled, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule_id,
                rule["name"],
                rule["condition"],
                rule["severity"],
                rule.get("message", ""),
                1 if rule.get("enabled", True) else 0,
                now,
                now
            ))
            
            conn.commit()
            
            # Return the rule with its ID
            return {**rule, "id": rule_id}
                
        except Exception as e:
            logger.error(f"Error adding alert rule: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    async def update_alert_rule(self, rule_id: str, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing alert rule."""
        conn = None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if rule exists
            cursor.execute("SELECT id FROM water_heater_alert_rules WHERE id = ?", (rule_id,))
            if not cursor.fetchone():
                raise ValueError(f"Alert rule with ID {rule_id} not found")
            
            now = datetime.now().isoformat()
            
            cursor.execute("""
            UPDATE water_heater_alert_rules 
            SET name = ?, condition = ?, severity = ?, message = ?, enabled = ?, updated_at = ? 
            WHERE id = ?
            """, (
                rule["name"],
                rule["condition"],
                rule["severity"],
                rule.get("message", ""),
                1 if rule.get("enabled", True) else 0,
                now,
                rule_id
            ))
            
            conn.commit()
            
            # Return the updated rule
            return {**rule, "id": rule_id}
                
        except Exception as e:
            logger.error(f"Error updating alert rule {rule_id}: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    async def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        conn = None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM water_heater_alert_rules WHERE id = ?", (rule_id,))
            deleted = cursor.rowcount > 0
            
            conn.commit()
            return deleted
                
        except Exception as e:
            logger.error(f"Error deleting alert rule {rule_id}: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def _row_to_water_heater(self, conn, row) -> WaterHeater:
        """Convert a database row to a WaterHeater object."""
        cursor = conn.cursor()
        
        # Extract fields from row
        (device_id, name, brand, model, manufacturer, size, device_type, location, 
         target_temp, current_temp, mode, status, installation_date, warranty_expiry, 
         last_maintenance, efficiency, last_seen, health_status, metadata) = row
        
        # Get readings for this water heater
        cursor.execute("""
        SELECT id, temperature, pressure, energy_usage, flow_rate, timestamp 
        FROM water_heater_readings 
        WHERE water_heater_id = ? 
        ORDER BY timestamp DESC
        """, (device_id,))
        
        readings = []
        for r_row in cursor.fetchall():
            reading = WaterHeaterReading(
                id=r_row[0],
                temperature=r_row[1],
                pressure=r_row[2],
                energy_usage=r_row[3],
                flow_rate=r_row[4],
                timestamp=datetime.fromisoformat(r_row[5])
            )
            readings.append(reading)
        
        # Get diagnostic codes for this water heater
        cursor.execute("""
        SELECT id, code, description, severity, timestamp, resolved, resolved_at 
        FROM water_heater_diagnostic_codes 
        WHERE water_heater_id = ? 
        ORDER BY timestamp DESC
        """, (device_id,))
        
        diagnostic_codes = []
        for d_row in cursor.fetchall():
            code = WaterHeaterDiagnosticCode(
                id=d_row[0],
                code=d_row[1],
                description=d_row[2],
                severity=d_row[3],
                timestamp=datetime.fromisoformat(d_row[4]),
                resolved=bool(d_row[5]),
                resolved_at=datetime.fromisoformat(d_row[6]) if d_row[6] else None
            )
            diagnostic_codes.append(code)
        
        # Create and return the water heater object
        return WaterHeater(
            id=device_id,
            name=name,
            model=model,
            manufacturer=manufacturer,
            target_temperature=target_temp,
            current_temperature=current_temp,
            status=WaterHeaterStatus(status) if status else None,
            mode=WaterHeaterMode(mode) if mode else None,
            installation_date=datetime.fromisoformat(installation_date) if installation_date else None,
            warranty_expiry=datetime.fromisoformat(warranty_expiry) if warranty_expiry else None,
            last_maintenance=datetime.fromisoformat(last_maintenance) if last_maintenance else None,
            last_seen=datetime.fromisoformat(last_seen) if last_seen else None,
            health_status=health_status,
            readings=readings,
            diagnostic_codes=diagnostic_codes
        )
    
    def _add_reading_to_db(self, conn, device_id: str, reading: WaterHeaterReading) -> None:
        """Add a reading to the database."""
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO water_heater_readings 
        (id, water_heater_id, temperature, pressure, energy_usage, flow_rate, timestamp) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            reading.id,
            device_id,
            reading.temperature,
            reading.pressure,
            reading.energy_usage,
            reading.flow_rate,
            reading.timestamp.isoformat()
        ))
    
    def _add_diagnostic_code_to_db(self, conn, device_id: str, code: WaterHeaterDiagnosticCode) -> None:
        """Add a diagnostic code to the database."""
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO water_heater_diagnostic_codes 
        (id, water_heater_id, code, description, severity, timestamp, resolved, resolved_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            code.id,
            device_id,
            code.code,
            code.description,
            code.severity,
            code.timestamp.isoformat(),
            1 if code.resolved else 0,
            code.resolved_at.isoformat() if code.resolved_at else None
        ))
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all water heaters
            cursor.execute("""
            SELECT * FROM water_heaters ORDER BY name
            """)
            
            rows = cursor.fetchall()
            
            for row in rows:
                water_heater = self._row_to_water_heater(dict(row))
                
                # Get recent readings
                cursor.execute("""
                SELECT * FROM water_heater_readings
                WHERE water_heater_id = ?
                ORDER BY timestamp DESC
                LIMIT 24
                """, (water_heater.id,))
                
                reading_rows = cursor.fetchall()
                readings = [self._row_to_reading(dict(r)) for r in reading_rows]
                water_heater.readings = readings
                
                # Get diagnostic codes
                cursor.execute("""
                SELECT * FROM water_heater_diagnostic_codes
                WHERE water_heater_id = ? AND resolved = 0
                ORDER BY timestamp DESC
                """, (water_heater.id,))
                
                diagnostic_rows = cursor.fetchall()
                diagnostic_codes = [self._row_to_diagnostic_code(dict(r)) for r in diagnostic_rows]
                water_heater.diagnostic_codes = diagnostic_codes
                
                water_heaters.append(water_heater)
            
            return water_heaters
            
        except Exception as e:
            logger.error(f"Error getting water heaters: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        """Get a specific water heater by ID from the database."""
        conn = None
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get the water heater
            cursor.execute("""
            SELECT * FROM water_heaters WHERE id = ?
            """, (device_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            water_heater = self._row_to_water_heater(dict(row))
            
            # Get recent readings
            cursor.execute("""
            SELECT * FROM water_heater_readings
            WHERE water_heater_id = ?
            ORDER BY timestamp DESC
            LIMIT 24
            """, (device_id,))
            
            reading_rows = cursor.fetchall()
            readings = [self._row_to_reading(dict(r)) for r in reading_rows]
            water_heater.readings = readings
            
            # Get diagnostic codes
            cursor.execute("""
            SELECT * FROM water_heater_diagnostic_codes
            WHERE water_heater_id = ? AND resolved = 0
            ORDER BY timestamp DESC
            """, (device_id,))
            
            diagnostic_rows = cursor.fetchall()
            diagnostic_codes = [self._row_to_diagnostic_code(dict(r)) for r in diagnostic_rows]
            water_heater.diagnostic_codes = diagnostic_codes
            
            return water_heater
            
        except Exception as e:
            logger.error(f"Error getting water heater {device_id}: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    async def create_water_heater(self, water_heater: WaterHeater) -> WaterHeater:
        """Create a new water heater in the database."""
        conn = None
        
        try:
            # Generate ID if not provided
            if not water_heater.id:
                water_heater.id = f"wh-{str(uuid.uuid4())[:8]}"
            
            # Set creation timestamp
            if not water_heater.last_seen:
                water_heater.last_seen = datetime.now()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert the water heater
            cursor.execute("""
            INSERT INTO water_heaters (
                id, name, brand, model, size, type, location, target_temperature,
                current_temperature, mode, status, installation_date, warranty_expiry,
                last_maintenance, efficiency_rating, last_seen, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                water_heater.id,
                water_heater.name,
                water_heater.brand,
                water_heater.model,
                water_heater.size,
                water_heater.type.value if water_heater.type else None,
                water_heater.location,
                water_heater.target_temperature,
                water_heater.current_temperature,
                water_heater.mode.value if water_heater.mode else None,
                water_heater.status.value if water_heater.status else None,
                water_heater.installation_date.isoformat() if water_heater.installation_date else None,
                water_heater.warranty_expiry.isoformat() if water_heater.warranty_expiry else None,
                water_heater.last_maintenance.isoformat() if water_heater.last_maintenance else None,
                water_heater.efficiency_rating,
                water_heater.last_seen.isoformat() if water_heater.last_seen else None,
                None  # metadata - could be JSON string
            ))
            
            # Save any readings
            if water_heater.readings:
                for reading in water_heater.readings:
                    if not reading.id:
                        reading.id = str(uuid.uuid4())
                    
                    cursor.execute("""
                    INSERT INTO water_heater_readings (
                        id, water_heater_id, temperature, pressure, energy_usage,
                        flow_rate, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        reading.id,
                        water_heater.id,
                        reading.temperature,
                        reading.pressure,
                        reading.energy_usage,
                        reading.flow_rate,
                        reading.timestamp.isoformat() if reading.timestamp else datetime.now().isoformat()
                    ))
            
            # Save any diagnostic codes
            if water_heater.diagnostic_codes:
                for code in water_heater.diagnostic_codes:
                    if not code.id:
                        code.id = str(uuid.uuid4())
                    
                    cursor.execute("""
                    INSERT INTO water_heater_diagnostic_codes (
                        id, water_heater_id, code, description, severity,
                        timestamp, resolved, resolved_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        code.id,
                        water_heater.id,
                        code.code,
                        code.description,
                        code.severity,
                        code.timestamp.isoformat() if code.timestamp else datetime.now().isoformat(),
                        1 if code.resolved else 0,
                        code.resolved_at.isoformat() if code.resolved_at else None
                    ))
            
            conn.commit()
            return water_heater
            
        except Exception as e:
            logger.error(f"Error creating water heater: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    async def update_water_heater(self, device_id: str, updates: Dict[str, Any]) -> Optional[WaterHeater]:
        """Update a water heater in the database with specified changes."""
        conn = None
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if water heater exists
            cursor.execute("SELECT id FROM water_heaters WHERE id = ?", (device_id,))
            if not cursor.fetchone():
                return None
            
            # Build the update query
            update_fields = []
            update_values = []
            
            field_mappings = {
                "name": "name",
                "brand": "brand",
                "model": "model",
                "size": "size",
                "type": "type",
                "location": "location",
                "target_temperature": "target_temperature",
                "current_temperature": "current_temperature",
                "mode": "mode",
                "status": "status",
                "installation_date": "installation_date",
                "warranty_expiry": "warranty_expiry",
                "last_maintenance": "last_maintenance",
                "efficiency_rating": "efficiency_rating",
                "last_seen": "last_seen"
            }
            
            for key, db_field in field_mappings.items():
                if key in updates:
                    value = updates[key]
                    
                    # Handle enum values
                    if key in ["mode", "status", "type"] and value is not None:
                        value = value.value if hasattr(value, "value") else value
                    
                    # Handle date values
                    if key in ["installation_date", "warranty_expiry", "last_maintenance", "last_seen"] and value is not None:
                        if isinstance(value, datetime):
                            value = value.isoformat()
                    
                    update_fields.append(f"{db_field} = ?")
                    update_values.append(value)
            
            if not update_fields:
                # Nothing to update
                return await self.get_water_heater(device_id)
            
            # Create update statement
            update_query = f"""
            UPDATE water_heaters
            SET {', '.join(update_fields)}
            WHERE id = ?
            """
            
            update_values.append(device_id)  # Add device_id for WHERE clause
            
            cursor.execute(update_query, update_values)
            
            # Handle special case: readings
            if "readings" in updates and updates["readings"] is not None:
                # This is a more complex update that might involve deleting old readings
                # and inserting new ones, but for simplicity, we'll just append the new ones
                for reading in updates["readings"]:
                    if not reading.id:
                        reading.id = str(uuid.uuid4())
                    
                    cursor.execute("""
                    INSERT INTO water_heater_readings (
                        id, water_heater_id, temperature, pressure, energy_usage,
                        flow_rate, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        reading.id,
                        device_id,
                        reading.temperature,
                        reading.pressure,
                        reading.energy_usage,
                        reading.flow_rate,
                        reading.timestamp.isoformat() if reading.timestamp else datetime.now().isoformat()
                    ))
            
            # Handle special case: diagnostic_codes
            if "diagnostic_codes" in updates and updates["diagnostic_codes"] is not None:
                for code in updates["diagnostic_codes"]:
                    if not code.id:
                        code.id = str(uuid.uuid4())
                    
                    # Check if the code already exists
                    cursor.execute("""
                    SELECT id FROM water_heater_diagnostic_codes
                    WHERE water_heater_id = ? AND code = ? AND resolved = 0
                    """, (device_id, code.code))
                    
                    existing_code = cursor.fetchone()
                    
                    if existing_code:
                        # Update the existing code
                        cursor.execute("""
                        UPDATE water_heater_diagnostic_codes
                        SET description = ?, severity = ?, resolved = ?, resolved_at = ?
                        WHERE id = ?
                        """, (
                            code.description,
                            code.severity,
                            1 if code.resolved else 0,
                            code.resolved_at.isoformat() if code.resolved_at else None,
                            existing_code[0]
                        ))
                    else:
                        # Insert a new code
                        cursor.execute("""
                        INSERT INTO water_heater_diagnostic_codes (
                            id, water_heater_id, code, description, severity,
                            timestamp, resolved, resolved_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            code.id,
                            device_id,
                            code.code,
                            code.description,
                            code.severity,
                            code.timestamp.isoformat() if code.timestamp else datetime.now().isoformat(),
                            1 if code.resolved else 0,
                            code.resolved_at.isoformat() if code.resolved_at else None
                        ))
            
            conn.commit()
            
            # Return the updated water heater
            return await self.get_water_heater(device_id)
            
        except Exception as e:
            logger.error(f"Error updating water heater {device_id}: {str(e)}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    async def add_reading(self, device_id: str, reading: WaterHeaterReading) -> Optional[WaterHeater]:
        """Add a new reading to a water heater in the database."""
        conn = None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if water heater exists
            cursor.execute("SELECT id FROM water_heaters WHERE id = ?", (device_id,))
            if not cursor.fetchone():
                return None
            
            # Generate ID if not provided
            if not reading.id:
                reading.id = str(uuid.uuid4())
            
            # Set timestamp if not provided
            if not reading.timestamp:
                reading.timestamp = datetime.now()
            
            # Insert the reading
            cursor.execute("""
            INSERT INTO water_heater_readings (
                id, water_heater_id, temperature, pressure, energy_usage,
                flow_rate, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                reading.id,
                device_id,
                reading.temperature,
                reading.pressure,
                reading.energy_usage,
                reading.flow_rate,
                reading.timestamp.isoformat()
            ))
            
            # Update the water heater's current temperature and last_seen
            cursor.execute("""
            UPDATE water_heaters
            SET current_temperature = ?, last_seen = ?
            WHERE id = ?
            """, (reading.temperature, reading.timestamp.isoformat(), device_id))
            
            conn.commit()
            
            # Return the updated water heater
            return await self.get_water_heater(device_id)
            
        except Exception as e:
            logger.error(f"Error adding reading to water heater {device_id}: {str(e)}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    async def get_readings(self, device_id: str, limit: int = 24) -> List[WaterHeaterReading]:
        """Get recent readings for a water heater from the database."""
        conn = None
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if water heater exists
            cursor.execute("SELECT id FROM water_heaters WHERE id = ?", (device_id,))
            if not cursor.fetchone():
                return []
            
            # Get recent readings
            cursor.execute("""
            SELECT * FROM water_heater_readings
            WHERE water_heater_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """, (device_id, limit))
            
            reading_rows = cursor.fetchall()
            readings = [self._row_to_reading(dict(r)) for r in reading_rows]
            
            return readings
            
        except Exception as e:
            logger.error(f"Error getting readings for water heater {device_id}: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def _row_to_water_heater(self, row: Dict[str, Any]) -> WaterHeater:
        """Convert a database row to a WaterHeater object."""
        # Parse dates
        installation_date = None
        if row.get("installation_date"):
            try:
                installation_date = datetime.fromisoformat(row["installation_date"])
            except ValueError:
                pass
        
        warranty_expiry = None
        if row.get("warranty_expiry"):
            try:
                warranty_expiry = datetime.fromisoformat(row["warranty_expiry"])
            except ValueError:
                pass
        
        last_maintenance = None
        if row.get("last_maintenance"):
            try:
                last_maintenance = datetime.fromisoformat(row["last_maintenance"])
            except ValueError:
                pass
        
        last_seen = None
        if row.get("last_seen"):
            try:
                last_seen = datetime.fromisoformat(row["last_seen"])
            except ValueError:
                pass
        
        # Parse enums
        water_heater_type = None
        if row.get("type"):
            try:
                water_heater_type = WaterHeaterType(row["type"])
            except ValueError:
                water_heater_type = WaterHeaterType.RESIDENTIAL
        
        mode = None
        if row.get("mode"):
            try:
                mode = WaterHeaterMode(row["mode"])
            except ValueError:
                mode = WaterHeaterMode.STANDARD
        
        status = None
        if row.get("status"):
            try:
                status = WaterHeaterStatus(row["status"])
            except ValueError:
                status = WaterHeaterStatus.ONLINE
        
        # Create and return the water heater object
        return WaterHeater(
            id=row.get("id"),
            name=row.get("name"),
            brand=row.get("brand"),
            model=row.get("model"),
            size=row.get("size"),
            type=water_heater_type,
            location=row.get("location"),
            target_temperature=row.get("target_temperature"),
            current_temperature=row.get("current_temperature"),
            mode=mode,
            status=status,
            installation_date=installation_date,
            warranty_expiry=warranty_expiry,
            last_maintenance=last_maintenance,
            efficiency_rating=row.get("efficiency_rating"),
            last_seen=last_seen,
            readings=[],  # To be populated separately
            diagnostic_codes=[]  # To be populated separately
        )
    
    def _row_to_reading(self, row: Dict[str, Any]) -> WaterHeaterReading:
        """Convert a database row to a WaterHeaterReading object."""
        timestamp = None
        if row.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(row["timestamp"])
            except ValueError:
                timestamp = datetime.now()
        
        return WaterHeaterReading(
            id=row.get("id"),
            temperature=row.get("temperature"),
            pressure=row.get("pressure"),
            energy_usage=row.get("energy_usage"),
            flow_rate=row.get("flow_rate"),
            timestamp=timestamp
        )
    
    def _row_to_diagnostic_code(self, row: Dict[str, Any]) -> WaterHeaterDiagnosticCode:
        """Convert a database row to a WaterHeaterDiagnosticCode object."""
        timestamp = None
        if row.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(row["timestamp"])
            except ValueError:
                timestamp = datetime.now()
        
        resolved_at = None
        if row.get("resolved_at"):
            try:
                resolved_at = datetime.fromisoformat(row["resolved_at"])
            except ValueError:
                pass
        
        return WaterHeaterDiagnosticCode(
            id=row.get("id"),
            code=row.get("code"),
            description=row.get("description"),
            severity=row.get("severity"),
            timestamp=timestamp,
            resolved=bool(row.get("resolved", 0)),
            resolved_at=resolved_at
        )
