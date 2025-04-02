"""
Script to set model health status for all models in the database.
This will ensure that all models have a proper health status.
"""
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
import random
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "data/iotsphere.db"

def main():
    """Set health status for all models."""
    logger.info("Starting health status configuration for all models")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if the model_health table exists
        cursor.execute("""
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' AND name='model_health'
        """)
        
        if not cursor.fetchone():
            logger.info("Creating model_health table")
            cursor.execute("""
            CREATE TABLE model_health (
                id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                model_version TEXT NOT NULL,
                health_status TEXT NOT NULL,
                metrics_summary TEXT,
                drift_status TEXT,
                last_updated TEXT,
                recommendations TEXT,
                FOREIGN KEY (model_id) REFERENCES models (id)
            )
            """)
        
        # Get all models and their versions
        logger.info("Getting all model versions")
        cursor.execute("""
        SELECT mv.model_id, mv.version, m.name
        FROM model_versions mv
        JOIN models m ON mv.model_id = m.id
        """)
        model_versions = cursor.fetchall()
        
        logger.info(f"Found {len(model_versions)} model versions")
        
        # Health statuses to choose from
        health_statuses = ["healthy", "drifting", "degraded"]
        health_weights = [0.6, 0.3, 0.1]  # Weights for random selection (60% healthy, 30% drifting, 10% degraded)
        
        # For each model version, set health status
        for model_version in model_versions:
            model_id = model_version['model_id']
            version = model_version['version']
            model_name = model_version['name']
            
            # Check if health record exists
            cursor.execute("""
            SELECT id FROM model_health
            WHERE model_id = ? AND model_version = ?
            """, (model_id, version))
            
            existing_record = cursor.fetchone()
            
            # Randomly select a health status based on weights
            health_status = random.choices(health_statuses, health_weights)[0]
            
            # Create recommendations based on health status
            recommendations = []
            if health_status == "drifting":
                recommendations.append("Data drift detected. Consider retraining the model.")
            elif health_status == "degraded":
                recommendations.append("Model accuracy has degraded. Investigate and consider retraining.")
            
            # Generate sample metrics
            metrics_summary = {
                "accuracy": round(random.uniform(0.85 if health_status == "healthy" else 0.70, 0.98), 4),
                "precision": round(random.uniform(0.85 if health_status == "healthy" else 0.70, 0.98), 4),
                "recall": round(random.uniform(0.85 if health_status == "healthy" else 0.70, 0.98), 4),
                "f1_score": round(random.uniform(0.85 if health_status == "healthy" else 0.70, 0.98), 4)
            }
            
            # Drift metrics
            drift_status = "normal" if health_status != "drifting" else "significant"
            drift_metrics = {
                "drift_score": round(random.uniform(0.02 if drift_status == "normal" else 0.15, 
                                                0.08 if drift_status == "normal" else 0.35), 4),
                "data_quality_score": round(random.uniform(0.85 if drift_status == "normal" else 0.60, 0.95), 4)
            }
            
            # Record data
            record_data = {
                "id": str(uuid.uuid4()) if not existing_record else existing_record['id'],
                "model_id": model_id,
                "model_version": version,
                "health_status": health_status,
                "metrics_summary": json.dumps(metrics_summary),
                "drift_status": drift_status,
                "last_updated": datetime.now().isoformat(),
                "recommendations": json.dumps(recommendations)
            }
            
            if existing_record:
                logger.info(f"Updating health status for {model_name} ({model_id}) version {version} to {health_status}")
                cursor.execute("""
                UPDATE model_health
                SET health_status = ?, metrics_summary = ?, drift_status = ?, 
                    last_updated = ?, recommendations = ?
                WHERE id = ?
                """, (
                    record_data["health_status"],
                    record_data["metrics_summary"],
                    record_data["drift_status"],
                    record_data["last_updated"],
                    record_data["recommendations"],
                    record_data["id"]
                ))
            else:
                logger.info(f"Creating health status for {model_name} ({model_id}) version {version} as {health_status}")
                cursor.execute("""
                INSERT INTO model_health
                    (id, model_id, model_version, health_status, metrics_summary, 
                     drift_status, last_updated, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record_data["id"],
                    record_data["model_id"],
                    record_data["model_version"],
                    record_data["health_status"],
                    record_data["metrics_summary"],
                    record_data["drift_status"],
                    record_data["last_updated"],
                    record_data["recommendations"]
                ))
        
        # We'll check the models table schema instead of trying to update a non-existent column
        logger.info("Checking model table schema")
        cursor.execute("PRAGMA table_info(models)")
        columns = cursor.fetchall()
        column_names = [col['name'] for col in columns]
        logger.info(f"Models table has columns: {column_names}")
        
        # Instead of updating metadata, we'll create a separate lookup table for model health reference
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_health_reference (
            model_id TEXT PRIMARY KEY,
            latest_version TEXT,
            health_status TEXT,
            last_updated TEXT,
            FOREIGN KEY (model_id) REFERENCES models (id)
        )
        """)
        
        # Update the health reference table with latest health status for each model
        cursor.execute("""
        SELECT id FROM models
        """)
        all_models = cursor.fetchall()
        
        for model in all_models:
            model_id = model['id']
            
            # Get latest version for this model
            cursor.execute("""
            SELECT version FROM model_versions
            WHERE model_id = ?
            ORDER BY version DESC
            LIMIT 1
            """, (model_id,))
            
            version_row = cursor.fetchone()
            if version_row:
                latest_version = version_row['version']
                
                # Get health status for this version
                cursor.execute("""
                SELECT health_status FROM model_health
                WHERE model_id = ? AND model_version = ?
                """, (model_id, latest_version))
                
                health_row = cursor.fetchone()
                if health_row:
                    health_status = health_row['health_status']
                    
                    # Update model health reference
                    cursor.execute("""
                    INSERT OR REPLACE INTO model_health_reference
                    (model_id, latest_version, health_status, last_updated)
                    VALUES (?, ?, ?, ?)
                    """, (model_id, latest_version, health_status, datetime.now().isoformat()))
                    
                    logger.info(f"Updated health reference for model {model_id} to {health_status}")
        
        # Create a view for easy querying of model health
        logger.info("Creating model_health_view")
        cursor.execute("""
        DROP VIEW IF EXISTS model_health_view
        """)
        
        cursor.execute("""
        CREATE VIEW model_health_view AS
        SELECT 
            m.id AS model_id,
            m.name AS model_name,
            mv.version AS model_version,
            COALESCE(mh.health_status, 'unknown') AS health_status,
            mh.drift_status,
            mh.last_updated,
            mh.metrics_summary,
            mh.recommendations
        FROM 
            models m
        LEFT JOIN 
            model_versions mv ON m.id = mv.model_id
        LEFT JOIN 
            model_health mh ON m.id = mh.model_id AND mv.version = mh.model_version
        """)
        
        # Update the model display view to include health status
        logger.info("Creating model_display_view with health status")
        cursor.execute("""
        DROP VIEW IF EXISTS model_display_view
        """)
        
        cursor.execute("""
        CREATE VIEW model_display_view AS
        SELECT 
            m.id AS model_id,
            m.name AS model_name,
            mv.version AS current_version,
            COALESCE(mh.health_status, 'unknown') AS health_status,
            CASE
                WHEN mh.health_status = 'healthy' THEN 'Good'
                WHEN mh.health_status = 'drifting' THEN 'Warning'
                WHEN mh.health_status = 'degraded' THEN 'Critical'
                ELSE 'Unknown'
            END AS health_display,
            json_extract(mh.metrics_summary, '$.accuracy') AS accuracy,
            m.archived
        FROM 
            models m
        LEFT JOIN 
            model_versions mv ON m.id = mv.model_id
        LEFT JOIN 
            model_health mh ON m.id = mh.model_id AND mv.version = mh.model_version
        WHERE 
            mv.version = (
                SELECT MAX(version) 
                FROM model_versions 
                WHERE model_id = m.id
            )
        """)
        
        # Commit changes
        conn.commit()
        logger.info("Successfully configured health status for all models")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error configuring health status: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
