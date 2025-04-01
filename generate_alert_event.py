"""
Script to generate a test alert event for an existing rule.
This will make the alert appear in Recent Alerts.
"""
import asyncio
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Make sure we're using real data, not mock
os.environ["USE_MOCK_DATA"] = "False"

async def main():
    # Import here to ensure environment vars are set first
    from src.db.real_database import SQLiteDatabase
    from src.db.adapters.sqlite_model_metrics import SQLiteModelMetricsRepository
    
    logger.info("=== Generating Alert Event ===")
    
    # Initialize database
    db_path = "data/iotsphere.db"
    db = SQLiteDatabase(connection_string=db_path)
    logger.info(f"DB initialization complete: {db}")
    
    # Create repository
    repo = SQLiteModelMetricsRepository(db=db)
    
    try:
        # First, let's find the energy consumption rule - adapting to actual schema
        cursor = await db.execute("SELECT * FROM alert_rules WHERE metric_name LIKE '%energy%' OR metric_name LIKE '%consumption%'")
        rules = await cursor.fetchall()
        
        if not rules:
            logger.warning("No energy consumption rule found. Creating one now.")
            # Create a test rule for energy consumption
            try:
                # First check table structure
                schema_cursor = await db.execute("PRAGMA table_info(alert_rules)")
                columns = await schema_cursor.fetchall()
                column_names = [col[1] for col in columns]  # Column name is at index 1
                
                # Determine necessary fields based on schema
                has_operator = 'operator' in column_names
                has_condition = 'condition' in column_names
                operator_column = 'condition' if has_condition else 'operator'
                
                # Prepare query based on available columns
                base_columns = ['id', 'model_id', 'metric_name', 'threshold', 'severity']
                values_placeholders = ['?'] * len(base_columns)
                
                # Add operator/condition
                if operator_column:
                    base_columns.append(operator_column)
                    values_placeholders.append('?')
                    
                # Add active column if it exists
                if 'active' in column_names:
                    base_columns.append('active')
                    values_placeholders.append('?')
                    
                # Create rule ID and set up values
                rule_id = 'energy-consumption-rule'
                model_id = 'anomaly-detection-1'  # Use an existing model
                metric_name = 'energy_consumption'
                threshold = 0.85
                condition = 'ABOVE'
                severity = 'WARNING'
                
                # Prepare parameters
                params = [rule_id, model_id, metric_name, threshold, severity]
                if operator_column:
                    params.append(condition)
                if 'active' in column_names:
                    params.append(1)  # Set active to true
                    
                # Create the rule
                query = f"INSERT INTO alert_rules ({', '.join(base_columns)}) VALUES ({', '.join(values_placeholders)})"
                await db.execute(query, tuple(params))
                logger.info(f"Created new rule: {rule_id} for {metric_name}")
                
            except Exception as e:
                logger.error(f"Error creating rule: {str(e)}")
                return
            
        # Get the first matching rule
        rule = rules[0]
        
        # Use dictionary-style access for SQLite row objects if they support it
        try:
            rule_id = rule['id']
            model_id = rule['model_id']
            metric_name = rule['metric_name']
            threshold = rule['threshold']
            
            # Adapt to schema differences - check which column name is used
            if 'condition' in rule:
                condition = rule['condition']
            elif 'operator' in rule:
                condition = rule['operator']
            else:
                condition = 'ABOVE'  # Default
                
            severity = rule.get('severity', 'WARNING')
        except (TypeError, KeyError):
            # Handle tuple-style results if dictionary access fails
            # Get column names from cursor description
            columns = [col[0] for col in cursor.description]
            rule_tuple = rule
            
            # Map tuple values to named fields
            rule_id = rule_tuple[columns.index('id')]
            model_id = rule_tuple[columns.index('model_id')]
            metric_name = rule_tuple[columns.index('metric_name')]
            threshold = rule_tuple[columns.index('threshold')]
            
            # Get condition/operator
            if 'condition' in columns:
                condition = rule_tuple[columns.index('condition')]
            elif 'operator' in columns:
                condition = rule_tuple[columns.index('operator')]
            else:
                condition = 'ABOVE'  # Default
                
            severity = rule_tuple[columns.index('severity')] if 'severity' in columns else 'WARNING'
        
        logger.info(f"Found rule: {rule_id} for {metric_name}")
        
        # Generate a metric value that would trigger the alert
        metric_value = 0.0
        if condition == 'ABOVE' or condition == '>':
            metric_value = threshold + 0.1  # Slightly above threshold
        else:
            metric_value = threshold - 0.1  # Slightly below threshold
            
        # Create an alert event
        try:
            alert = await repo.record_alert_event(
                rule_id=rule_id,
                model_id=model_id,
                metric_name=metric_name,
                metric_value=metric_value,
                severity=rule['severity']
            )
            
            logger.info(f"Successfully created alert event: {alert}")
            
            # Verify the alert was created
            cursor = await db.execute("SELECT * FROM alert_events WHERE rule_id = ? ORDER BY created_at DESC LIMIT 1", (rule_id,))
            result = await cursor.fetchone()
            if result:
                logger.info(f"Verified alert in database: {result}")
            else:
                logger.warning("Alert created but not found in database verification")
                
        except Exception as e:
            logger.error(f"Error creating alert event: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error finding energy consumption rule: {str(e)}")
    finally:
        if db is not None:
            try:
                await db.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
