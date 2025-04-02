#!/usr/bin/env python
"""
Creates a clean database with the correct schema for IoTSphere.

Following our TDD principles, this script creates a database that matches exactly
what our tests expect, rather than trying to adapt the tests to the database.
"""
import os
import sys
import logging
import sqlite3
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_clean_database(db_path, backup_existing=True):
    """Create a clean database with the correct schema."""
    
    # Make sure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Backup existing database if it exists
    if os.path.exists(db_path) and backup_existing:
        timestamp = int(time.time())
        backup_path = f"{db_path}.backup_{timestamp}"
        shutil.copy2(db_path, backup_path)
        logger.info(f"Backed up existing database to {backup_path}")
        
        # Delete the existing database
        os.remove(db_path)
        logger.info(f"Removed existing database at {db_path}")
    
    # Create a new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    try:
        # Create the schema version table
        cursor.execute("""
        CREATE TABLE schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("INSERT INTO schema_version (version) VALUES (7)")
        
        # Create the models table
        cursor.execute("""
        CREATE TABLE models (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            archived BOOLEAN NOT NULL DEFAULT 0
        )
        """)
        
        # Create the model_versions table
        cursor.execute("""
        CREATE TABLE model_versions (
            id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            version TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
            UNIQUE(model_id, version)
        )
        """)
        
        # Create the model_metrics table
        cursor.execute("""
        CREATE TABLE model_metrics (
            id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            model_version TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
        )
        """)
        
        # Create the alert_rules table
        cursor.execute("""
        CREATE TABLE alert_rules (
            id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            model_version TEXT,
            metric_name TEXT NOT NULL,
            threshold REAL NOT NULL,
            condition TEXT,
            operator TEXT NOT NULL,
            rule_name TEXT,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            severity TEXT DEFAULT 'WARNING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
        )
        """)
        
        # Create the alert_events table
        cursor.execute("""
        CREATE TABLE alert_events (
            id TEXT PRIMARY KEY,
            rule_id TEXT NOT NULL,
            model_id TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            severity TEXT NOT NULL DEFAULT 'WARNING',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN NOT NULL DEFAULT 0,
            resolved_at TIMESTAMP,
            FOREIGN KEY (rule_id) REFERENCES alert_rules(id) ON DELETE CASCADE,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
        )
        """)
        
        # Create the alert_rules_old table for backward compatibility
        cursor.execute("""
        CREATE TABLE alert_rules_old (
            id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            model_version TEXT,
            rule_name TEXT,
            metric_name TEXT NOT NULL,
            threshold REAL NOT NULL,
            operator TEXT NOT NULL,
            severity TEXT DEFAULT 'WARNING',
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create the model_tags table
        cursor.execute("""
        CREATE TABLE model_tags (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            color TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create the model_tag_assignments table
        cursor.execute("""
        CREATE TABLE model_tag_assignments (
            model_id TEXT NOT NULL,
            tag_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (model_id, tag_id),
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES model_tags(id) ON DELETE CASCADE
        )
        """)
        
        # Insert sample data
        
        # Insert models
        models = [
            ("water-heater-model-1", "Water Heater Predictive Model", "Model for predicting water heater issues"),
            ("anomaly-detection-1", "Anomaly Detection Model", "Detects anomalies in water heater operation"),
            ("energy-forecasting-1", "Energy Forecasting Model", "Forecasts energy consumption"),
            ("maintenance-predictor-1", "Maintenance Predictor", "Predicts maintenance needs")
        ]
        cursor.executemany(
            "INSERT INTO models (id, name, description) VALUES (?, ?, ?)",
            models
        )
        
        # Insert alert rules
        rules = [
            ("rule1", "water-heater-model-1", "1.0", "Accuracy Alert", "accuracy", 0.85, "<", "WARNING", "Alert when accuracy falls below threshold", 1),
            ("rule2", "water-heater-model-1", "1.0", "Precision Alert", "precision", 0.9, "<", "CRITICAL", "Alert when precision falls below threshold", 1),
            ("rule3", "anomaly-detection-1", "1.0", "Recall Monitoring", "recall", 0.75, "<", "WARNING", "Alert when recall falls below threshold", 1),
            ("rule4", "anomaly-detection-1", "1.0", "F1-Score Monitor", "f1", 0.8, "<", "INFO", "Alert when F1 score falls below threshold", 0),
            ("rule5", "energy-forecasting-1", "2.0", "Drift Monitor", "drift_score", 0.1, ">", "WARNING", "Alert when drift exceeds threshold", 1)
        ]
        cursor.executemany(
            """
            INSERT INTO alert_rules 
                (id, model_id, model_version, rule_name, metric_name, threshold, operator, severity, description, is_active) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rules
        )
        
        # Insert alert events
        now = datetime.now()
        events = [
            ("event1", "rule1", "water-heater-model-1", "accuracy", 0.82, "WARNING", 
             (now - timedelta(days=2)).isoformat(), False, None),
            ("event2", "rule3", "anomaly-detection-1", "recall", 0.72, "WARNING",
             (now - timedelta(days=5)).isoformat(), True, (now - timedelta(days=4)).isoformat())
        ]
        cursor.executemany(
            """
            INSERT INTO alert_events 
                (id, rule_id, model_id, metric_name, metric_value, severity, created_at, resolved, resolved_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            events
        )
        
        # Insert tags
        tags = [
            ("tag1", "production", "green"),
            ("tag2", "development", "blue"),
            ("tag3", "testing", "orange"),
            ("tag4", "deprecated", "red")
        ]
        cursor.executemany(
            "INSERT INTO model_tags (id, name, color) VALUES (?, ?, ?)",
            tags
        )
        
        # Assign tags to models
        tag_assignments = [
            ("water-heater-model-1", "tag1"),  # production
            ("water-heater-model-1", "tag3"),  # testing
            ("anomaly-detection-1", "tag2"),   # development
            ("anomaly-detection-1", "tag3"),   # testing
            ("energy-forecasting-1", "tag1"),  # production
            ("maintenance-predictor-1", "tag4") # deprecated
        ]
        cursor.executemany(
            "INSERT INTO model_tag_assignments (model_id, tag_id) VALUES (?, ?)",
            tag_assignments
        )
        
        # Commit changes
        conn.commit()
        logger.info(f"Created clean database at {db_path} with all required tables and sample data")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating clean database: {e}")
        return False
    
    finally:
        # Close connection
        conn.close()

if __name__ == "__main__":
    # Path to the main database
    data_dir = Path(__file__).parent / "data"
    db_path = str(data_dir / "iotsphere.db")
    
    logger.info(f"Creating clean database at {db_path}")
    success = create_clean_database(db_path)
    
    if success:
        logger.info("Database created successfully")
        sys.exit(0)
    else:
        logger.error("Failed to create database")
        sys.exit(1)
