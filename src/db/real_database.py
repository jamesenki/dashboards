"""
Real database connection module for IoTSphere.

This module provides a SQLite database implementation for development and testing.
"""
import os
import sqlite3
import logging
from typing import List, Tuple, Any, Optional, Union, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class SQLiteDatabase:
    """
    SQLite database connection manager.
    
    Provides a real database implementation that can be used for development and testing.
    """
    
    def __init__(self, connection_string: str = None):
        """
        Initialize SQLite database connection.
        
        Args:
            connection_string: Database file path or :memory: for in-memory database
        """
        # Default to in-memory database for testing if not specified
        self.connection_string = connection_string or ":memory:"
        self.connection = None
        self.connect()
        logger.info(f"SQLite database initialized at {self.connection_string}")
        
    def connect(self):
        """Establish database connection."""
        if self.connection_string == ":memory:":
            # In-memory database - create a new connection
            self.connection = sqlite3.connect(self.connection_string)
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Configure connection to return dictionaries
            self.connection.row_factory = sqlite3.Row
            # Create schema for in-memory database
            self._create_schema()
        else:
            # File-based database - create directory if needed
            os.makedirs(os.path.dirname(self.connection_string), exist_ok=True)
            db_exists = os.path.exists(self.connection_string)
            
            # Connect to the database file
            self.connection = sqlite3.connect(self.connection_string)
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Configure connection to return dictionaries
            self.connection.row_factory = sqlite3.Row
            
            # Create schema if this is a new database
            if not db_exists:
                self._create_schema()
    
    def _create_schema(self):
        """Create database schema for models, metrics, and alerts."""
        cursor = self.connection.cursor()
        
        # Create models table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            archived BOOLEAN NOT NULL DEFAULT 0
        )
        """)
        
        # Create model_versions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_versions (
            id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            version TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
            UNIQUE(model_id, version)
        )
        """)
        
        # Create model_metrics table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_metrics (
            id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            model_version TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
        )
        """)
        
        # Create alert_rules table with all fields expected by tests and repository code
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_rules (
            id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            model_version TEXT,
            rule_name TEXT,
            metric_name TEXT NOT NULL,
            threshold REAL NOT NULL,
            operator TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'WARNING',
            description TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
        )
        """)
        
        # Create alert_events table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_events (
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
        
        # Create model_tags table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_tags (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            color TEXT NOT NULL DEFAULT 'blue',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create model_tag_assignments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_tag_assignments (
            model_id TEXT NOT NULL,
            tag_id TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (model_id, tag_id),
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES model_tags(id) ON DELETE CASCADE
        )
        """)
        
        self.connection.commit()
    
    def execute(self, query: str, params: Optional[Union[Tuple, List]] = None) -> List[Tuple]:
        """
        Execute a database query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Query results as a list of tuples
        """
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            # For non-SELECT queries, just return affected row count
            if not query.strip().upper().startswith("SELECT"):
                self.connection.commit()
                return [(cursor.rowcount,)]
            
            # For SELECT queries, fetch all results
            results = cursor.fetchall()
            return [tuple(row) for row in results]
        except Exception as e:
            logger.error(f"Database error executing query: {str(e)}")
            self.connection.rollback()
            raise
    
    def execute_batch(self, query: str, params_list: List[Tuple]) -> bool:
        """
        Execute a batch of queries with different parameters.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
            
        Returns:
            Success flag
        """
        cursor = self.connection.cursor()
        try:
            cursor.executemany(query, params_list)
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Database error executing batch query: {str(e)}")
            self.connection.rollback()
            raise
    
    def begin_transaction(self):
        """Begin a database transaction."""
        logger.debug("Beginning transaction")
        # SQLite automatically begins a transaction on first query
        pass
    
    def commit(self):
        """Commit the current transaction."""
        logger.debug("Committing transaction")
        self.connection.commit()
    
    def rollback(self):
        """Roll back the current transaction."""
        logger.debug("Rolling back transaction")
        self.connection.rollback()
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            logger.debug("Closing database connection")
            self.connection.close()
            self.connection = None

    def fetch_all(self, query: str, params: Optional[Union[Tuple, List]] = None) -> List[dict]:
        """
        Execute a query and fetch all results as a list of dictionaries.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Query results as a list of dictionaries
        """
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            # Fetch all rows
            rows = cursor.fetchall()
            
            # Convert sqlite3.Row objects to dictionaries
            results = []
            for row in rows:
                item = {}
                for key in row.keys():
                    item[key] = row[key]
                results.append(item)
                
            return results
        except Exception as e:
            logger.error(f"Database error in fetch_all: {str(e)}")
            raise

    def fetch_one(self, query: str, params: Optional[Union[Tuple, List]] = None) -> Optional[dict]:
        """
        Execute a query and fetch a single result as a dictionary.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Single row as dictionary or None if no results
        """
        results = self.fetch_all(query, params)
        if results:
            return results[0]
        return None

    def get_models(self):
        """
        Get a list of all active models with their latest metrics.
        
        Returns:
            List of model information
        """
        # Forward to SQLiteModelMetricsRepository
        try:
            # Get all active model info
            models_query = """
            SELECT 
                id, name, archived
            FROM 
                models
            WHERE
                archived = 0
            ORDER BY
                name
            """
            models_data = self.fetch_all(models_query)
            
            # Prepare result list
            result = []
            
            for model in models_data:
                model_id = model['id']
                
                # Get versions for this model
                versions_query = """
                SELECT DISTINCT model_version 
                FROM model_metrics 
                WHERE model_id = ?
                ORDER BY model_version
                """
                versions_data = self.fetch_all(versions_query, (model_id,))
                versions = [v['model_version'] for v in versions_data]
                
                # Get latest metrics for this model
                latest_metrics_query = """
                SELECT 
                    m1.metric_name, m1.metric_value
                FROM 
                    model_metrics m1
                INNER JOIN (
                    SELECT 
                        model_id, MAX(timestamp) as max_timestamp
                    FROM 
                        model_metrics
                    WHERE 
                        model_id = ?
                    GROUP BY 
                        model_id
                ) m2 ON m1.model_id = m2.model_id AND m1.timestamp = m2.max_timestamp
                WHERE 
                    m1.model_id = ?
                """
                latest_metrics_data = self.fetch_all(latest_metrics_query, (model_id, model_id))
                
                # Convert list of metrics to a dictionary
                metrics = {}
                for metric in latest_metrics_data:
                    metrics[metric['metric_name']] = metric['metric_value']
                
                # Get alert count for this model
                alert_count_query = """
                SELECT 
                    COUNT(*) as count
                FROM 
                    alert_events
                WHERE 
                    model_id = ?
                """
                alert_count_data = self.fetch_one(alert_count_query, (model_id,))
                alert_count = alert_count_data['count'] if alert_count_data else 0
                
                # Get tags for this model
                tags_query = """
                SELECT 
                    tag
                FROM 
                    model_tags
                WHERE 
                    model_id = ?
                ORDER BY 
                    tag
                """
                tags_data = self.fetch_all(tags_query, (model_id,))
                tags = [t['tag'] for t in tags_data]
                
                # Build model info
                model_info = {
                    'id': model_id,
                    'name': model['name'],
                    'versions': versions,
                    'metrics': metrics,
                    'alert_count': alert_count,
                    'tags': tags,
                    'archived': False,
                    'data_source': 'database'  # Explicitly mark as from database
                }
                
                result.append(model_info)
                
            return result
        except Exception as e:
            logger.error(f"Error in SQLiteDatabase.get_models: {str(e)}")
            raise
    
    def get_archived_models(self):
        """
        Get a list of all archived models with their latest metrics.
        
        Returns:
            List of archived model information
        """
        try:
            # Get all archived model info
            models_query = """
            SELECT 
                id, name, archived
            FROM 
                models
            WHERE
                archived = 1
            ORDER BY
                name
            """
            models_data = self.fetch_all(models_query)
            
            # Prepare result list
            result = []
            
            for model in models_data:
                model_id = model['id']
                
                # Get versions for this model
                versions_query = """
                SELECT DISTINCT model_version 
                FROM model_metrics 
                WHERE model_id = ?
                ORDER BY model_version
                """
                versions_data = self.fetch_all(versions_query, (model_id,))
                versions = [v['model_version'] for v in versions_data]
                
                # Get latest metrics for this model (same logic as get_models)
                latest_metrics_query = """
                SELECT 
                    m1.metric_name, m1.metric_value
                FROM 
                    model_metrics m1
                INNER JOIN (
                    SELECT 
                        model_id, MAX(timestamp) as max_timestamp
                    FROM 
                        model_metrics
                    WHERE 
                        model_id = ?
                    GROUP BY 
                        model_id
                ) m2 ON m1.model_id = m2.model_id AND m1.timestamp = m2.max_timestamp
                WHERE 
                    m1.model_id = ?
                """
                latest_metrics_data = self.fetch_all(latest_metrics_query, (model_id, model_id))
                
                # Convert list of metrics to a dictionary
                metrics = {}
                for metric in latest_metrics_data:
                    metrics[metric['metric_name']] = metric['metric_value']
                
                # Get alert count for this model
                alert_count_query = """
                SELECT 
                    COUNT(*) as count
                FROM 
                    alert_events
                WHERE 
                    model_id = ?
                """
                alert_count_data = self.fetch_one(alert_count_query, (model_id,))
                alert_count = alert_count_data['count'] if alert_count_data else 0
                
                # Get tags for this model
                tags_query = """
                SELECT 
                    tag
                FROM 
                    model_tags
                WHERE 
                    model_id = ?
                ORDER BY 
                    tag
                """
                tags_data = self.fetch_all(tags_query, (model_id,))
                tags = [t['tag'] for t in tags_data]
                
                # Build model info
                model_info = {
                    'id': model_id,
                    'name': model['name'],
                    'versions': versions,
                    'metrics': metrics,
                    'alert_count': alert_count,
                    'tags': tags,
                    'archived': True,
                    'data_source': 'database'  # Explicitly mark as from database
                }
                
                result.append(model_info)
                
            return result
        except Exception as e:
            logger.error(f"Error in SQLiteDatabase.get_archived_models: {str(e)}")
            raise
    
    def populate_test_data(self):
        """
        Populate the database with test data for development and testing.
        """
        logger.info("Populating database with test data")
        
        # Generate test data
        
        # Add test models
        models = [
            ("water-heater-model-1", "Water Heater Prediction Model", "Predictive model for water heater efficiency", False),
            ("anomaly-detection-1", "Anomaly Detection Model", "Detects anomalies in sensor data", False),
            ("energy-forecasting-1", "Energy Consumption Forecaster", "Forecasts energy usage patterns", False),
            ("maintenance-predictor-1", "Maintenance Need Predictor", "Predicts when equipment needs maintenance", True)
        ]
        
        self.execute_batch(
            "INSERT OR REPLACE INTO models (id, name, description, archived) VALUES (?, ?, ?, ?)",
            models
        )
        
        # Add model versions
        versions = [
            ("water-heater-v1", "water-heater-model-1", "1.0", "/models/water-heater/v1.pkl"),
            ("water-heater-v2", "water-heater-model-1", "1.1", "/models/water-heater/v2.pkl"),
            ("water-heater-v3", "water-heater-model-1", "1.2", "/models/water-heater/v3.pkl"),
            ("anomaly-v1", "anomaly-detection-1", "0.9", "/models/anomaly/v0.9.pkl"),
            ("anomaly-v2", "anomaly-detection-1", "1.0", "/models/anomaly/v1.0.pkl"),
            ("energy-v1", "energy-forecasting-1", "1.0", "/models/energy/v1.0.pkl"),
            ("maintenance-v1", "maintenance-predictor-1", "1.0", "/models/maintenance/v1.0.pkl")
        ]
        
        self.execute_batch(
            "INSERT OR REPLACE INTO model_versions (id, model_id, version, file_path) VALUES (?, ?, ?, ?)",
            versions
        )
        
        # Add model metrics
        import uuid
        import random
        from datetime import datetime, timedelta
        
        metrics = []
        
        # Generate last 30 days of metrics for each model version
        for model_id, versions in {
            "water-heater-model-1": ["1.0", "1.1", "1.2"],
            "anomaly-detection-1": ["0.9", "1.0"],
            "energy-forecasting-1": ["1.0"],
            "maintenance-predictor-1": ["1.0"]
        }.items():
            for version in versions:
                # Last 30 days of daily metrics
                for days_ago in range(30, 0, -1):
                    date = datetime.now() - timedelta(days=days_ago)
                    
                    # Accuracy (fluctuating between 0.85 and 0.95)
                    metrics.append((
                        str(uuid.uuid4()),
                        model_id,
                        version,
                        "accuracy",
                        0.90 + random.uniform(-0.05, 0.05),
                        date.isoformat()
                    ))
                    
                    # Precision (fluctuating between 0.82 and 0.92)
                    metrics.append((
                        str(uuid.uuid4()),
                        model_id,
                        version,
                        "precision",
                        0.87 + random.uniform(-0.05, 0.05),
                        date.isoformat()
                    ))
                    
                    # Recall (fluctuating between 0.80 and 0.90)
                    metrics.append((
                        str(uuid.uuid4()),
                        model_id,
                        version,
                        "recall",
                        0.85 + random.uniform(-0.05, 0.05),
                        date.isoformat()
                    ))
                    
                    # F1 score (fluctuating between 0.81 and 0.91)
                    metrics.append((
                        str(uuid.uuid4()),
                        model_id,
                        version,
                        "f1_score",
                        0.86 + random.uniform(-0.05, 0.05),
                        date.isoformat()
                    ))
                    
                    # Drift score (gradually increasing in some models)
                    drift_base = 0.03 if model_id != "anomaly-detection-1" else 0.07
                    drift_trend = days_ago / 1000 if model_id == "water-heater-model-1" else 0
                    metrics.append((
                        str(uuid.uuid4()),
                        model_id,
                        version,
                        "drift_score",
                        drift_base + drift_trend + random.uniform(-0.01, 0.01),
                        date.isoformat()
                    ))
        
        self.execute_batch(
            """
            INSERT OR REPLACE INTO model_metrics 
                (id, model_id, model_version, metric_name, metric_value, timestamp) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            metrics
        )
        
        # Add alert rules - now with our full schema
        rules = [
            # id, model_id, model_version, rule_name, metric_name, threshold, operator, severity, description, created_at, is_active
            ("rule1", "water-heater-model-1", "1.0", "Accuracy Alert", "accuracy", 0.85, "BELOW", "WARNING", "Alert when accuracy falls below threshold", datetime.now().isoformat(), 1),
            ("rule2", "water-heater-model-1", "1.0", "Drift Alert", "drift_score", 0.10, "ABOVE", "CRITICAL", "Alert when drift exceeds threshold", datetime.now().isoformat(), 1),
            ("rule3", "anomaly-detection-1", "0.9", "Precision Alert", "precision", 0.82, "BELOW", "WARNING", "Alert when precision falls below threshold", datetime.now().isoformat(), 1),
            ("rule4", "energy-forecasting-1", "1.0", "Accuracy Alert", "accuracy", 0.87, "BELOW", "WARNING", "Alert when accuracy falls below threshold", datetime.now().isoformat(), 1)
        ]
        
        self.execute_batch(
            """
            INSERT OR REPLACE INTO alert_rules 
                (id, model_id, model_version, rule_name, metric_name, threshold, operator, severity, description, created_at, is_active) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rules
        )
        
        # Add a few alert events
        events = [
            ("event1", "rule2", "anomaly-detection-1", "drift_score", 0.12, "CRITICAL", 
             (datetime.now() - timedelta(days=2)).isoformat(), False, None),
            ("event2", "rule3", "anomaly-detection-1", "precision", 0.81, "WARNING", 
             (datetime.now() - timedelta(days=5)).isoformat(), True, 
             (datetime.now() - timedelta(days=4)).isoformat())
        ]
        
        self.execute_batch(
            """
            INSERT OR REPLACE INTO alert_events 
                (id, rule_id, model_id, metric_name, metric_value, severity, created_at, resolved, resolved_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            events
        )
        
        # Add tags
        tags = [
            ("tag1", "production", "green"),
            ("tag2", "development", "blue"),
            ("tag3", "testing", "orange"),
            ("tag4", "deprecated", "red")
        ]
        
        self.execute_batch(
            "INSERT OR REPLACE INTO model_tags (id, name, color) VALUES (?, ?, ?)",
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
        
        self.execute_batch(
            "INSERT OR REPLACE INTO model_tag_assignments (model_id, tag_id) VALUES (?, ?)",
            tag_assignments
        )
        
        self.commit()
        logger.info("Test data population complete")
    
    # Add database adapter methods required by SQLiteModelMetricsRepository
    def get_models(self):
        """
        Get a list of all models with their latest metrics.
        
        Returns:
            List of model information
        """
        # Get all model info
        models_query = """
        SELECT 
            id, name, archived
        FROM 
            models
        ORDER BY
            name
        """
        models_data = self.fetch_all(models_query)
        
        # Prepare result list
        result = []
        
        for model in models_data:
            model_id = model['id']
            
            # Get versions for this model
            versions_query = """
            SELECT DISTINCT model_version 
            FROM model_metrics 
            WHERE model_id = ?
            ORDER BY model_version
            """
            versions_data = self.fetch_all(versions_query, (model_id,))
            versions = [v['model_version'] for v in versions_data]
            
            # Get latest metrics for this model
            latest_metrics_query = """
            SELECT 
                m1.metric_name, m1.metric_value
            FROM 
                model_metrics m1
            INNER JOIN (
                SELECT 
                    model_id, MAX(timestamp) as max_timestamp
                FROM 
                    model_metrics
                WHERE 
                    model_id = ?
                GROUP BY 
                    model_id
            ) m2 ON m1.model_id = m2.model_id AND m1.timestamp = m2.max_timestamp
            WHERE 
                m1.model_id = ?
            """
            metrics_data = self.fetch_all(latest_metrics_query, (model_id, model_id))
            
            metrics = {}
            for metric in metrics_data:
                metrics[metric['metric_name']] = metric['metric_value']
            
            # Count active alerts
            alerts_query = """
            SELECT COUNT(*) as alert_count
            FROM alert_events
            WHERE model_id = ? AND resolved = 0
            """
            alert_data = self.fetch_one(alerts_query, (model_id,))
            alert_count = alert_data['alert_count'] if alert_data else 0
            
            # Get tags for this model
            tags_query = """
            SELECT t.name
            FROM model_tags t
            JOIN model_tag_assignments a ON t.id = a.tag_id
            WHERE a.model_id = ?
            """
            tags_data = self.fetch_all(tags_query, (model_id,))
            tags = [t['name'] for t in tags_data]
            
            # Assemble model info with data_source = 'database' explicitly set
            model_info = {
                'id': model_id,
                'name': model['name'],
                'versions': versions,
                'archived': bool(model['archived']),
                'metrics': metrics,
                'alert_count': alert_count,
                'tags': tags,
                'data_source': 'database'  # Explicitly mark as database source
            }
            
            result.append(model_info)
            
        return result
        
    def get_latest_metrics(self, model_id, model_version):
        """
        Get the most recent metrics for a model.
        
        Args:
            model_id: ID of the model
            model_version: Version of the model
            
        Returns:
            Dictionary of the latest metrics by name
        """
        query = """
        SELECT 
            m1.metric_name, m1.metric_value, m1.timestamp
        FROM 
            model_metrics m1
        INNER JOIN (
            SELECT 
                metric_name, MAX(timestamp) as max_timestamp
            FROM 
                model_metrics
            WHERE 
                model_id = ? AND model_version = ?
            GROUP BY 
                metric_name
        ) m2 ON m1.metric_name = m2.metric_name AND m1.timestamp = m2.max_timestamp
        WHERE 
            m1.model_id = ? AND m1.model_version = ?
        """
        
        params = (model_id, model_version, model_id, model_version)
        results = self.fetch_all(query, params)
        
        # Format results
        metrics = {}
        for record in results:
            metrics[record['metric_name']] = record['metric_value']
            
        return metrics
    
    def get_alert_rules(self, model_id=None):
        """
        Get alert rules for a model or all models.
        
        Args:
            model_id: Optional model ID to filter by
            
        Returns:
            List of alert rules
        """
        if model_id:
            query = """
            SELECT 
                id, rule_name, metric_name, threshold, operator, severity, description, is_active,
                created_at, updated_at
            FROM 
                alert_rules
            WHERE 
                model_id = ? OR model_id IS NULL
            ORDER BY
                created_at DESC
            """
            params = (model_id,)
        else:
            query = """
            SELECT 
                id, rule_name, metric_name, threshold, operator, severity, description, is_active,
                created_at, updated_at
            FROM 
                alert_rules
            ORDER BY
                created_at DESC
            """
            params = ()
            
        # Execute query
        results = self.fetch_all(query, params)
        
        # Format results
        rules = []
        for record in results:
            rule = dict(record)
            rule['is_active'] = bool(rule['is_active'])
            rules.append(rule)
            
        return rules
