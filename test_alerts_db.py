"""
Test script to debug the alerts data flow from database to API.
This will help track where the data is getting lost or transformed incorrectly.
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
    from src.monitoring.model_metrics_repository import ModelMetricsRepository
    from src.monitoring.model_monitoring_service import ModelMonitoringService
    
    logger.info("=== Starting Alerts DB Test ===")
    
    # Initialize database
    # Use the path to the production database so we're testing actual data
    db_path = "src/db/model_metrics.db"
    db = SQLiteDatabase(connection_string=db_path)
    logger.info(f"DB initialization complete: {db}")
    
    # Initialize repositories and services
    sql_repo = SQLiteModelMetricsRepository(db=db)
    metrics_repo = ModelMetricsRepository(sql_repo=sql_repo)
    service = ModelMonitoringService(metrics_repository=metrics_repo)
    
    # Test model data
    test_model_id = "water-heater-model-1"
    test_version = "1.0"
    
    # 1. First check if we can insert test alert rules and alerts
    logger.info("=== Creating test alert rules ===")
    try:
        # Create a test alert rule directly in the database
        rule_id = "test-rule-1"
        rule_query = """
        INSERT OR REPLACE INTO alert_rules 
            (id, model_id, model_version, rule_name, metric_name, threshold, operator, severity, created_at, is_active, description) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        db.execute(rule_query, (
            rule_id, 
            test_model_id, 
            test_version, 
            "Test Rule", 
            "accuracy", 
            0.85, 
            "BELOW", 
            "WARNING", 
            datetime.now().isoformat(),
            1,
            "Test rule description"
        ))
        logger.info("Alert rule created successfully")
        
        # Create a test alert event
        event_id = "test-alert-1"
        event_query = """
        INSERT OR REPLACE INTO alert_events 
            (id, rule_id, model_id, metric_name, metric_value, severity, created_at, resolved) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        db.execute(event_query, (
            event_id,
            rule_id,
            test_model_id,
            "accuracy",
            0.80,
            "WARNING",
            datetime.now().isoformat(),
            0
        ))
        logger.info("Alert event created successfully")
    except Exception as e:
        logger.error(f"Error creating test data: {str(e)}")
    
    # 2. Check database schema to debug issues
    logger.info("=== Checking database schema ===")
    try:
        # Check alert_rules table schema
        schema_query = "PRAGMA table_info(alert_rules)"
        rule_columns = db.fetch_all(schema_query)
        logger.info(f"Alert rules table columns: {[col['name'] for col in rule_columns]}")
        
        # Check alert_events table schema
        schema_query = "PRAGMA table_info(alert_events)"
        event_columns = db.fetch_all(schema_query)
        logger.info(f"Alert events table columns: {[col['name'] for col in event_columns]}")
    except Exception as e:
        logger.error(f"Error checking schema: {str(e)}")
    
    # 3. Test direct database access
    logger.info("=== Testing direct database access ===")
    try:
        # Query alert rules directly
        direct_rules_query = "SELECT * FROM alert_rules WHERE model_id = ? LIMIT 5"
        direct_rules = db.fetch_all(direct_rules_query, (test_model_id,))
        logger.info(f"Direct DB rules query returned {len(direct_rules)} rules")
        if direct_rules:
            logger.info(f"Sample rule: {direct_rules[0]}")
        
        # Query alert events directly
        direct_alerts_query = "SELECT * FROM alert_events WHERE model_id = ? LIMIT 5"
        direct_alerts = db.fetch_all(direct_alerts_query, (test_model_id,))
        logger.info(f"Direct DB alerts query returned {len(direct_alerts)} alerts")
        if direct_alerts:
            logger.info(f"Sample alert: {direct_alerts[0]}")
    except Exception as e:
        logger.error(f"Error with direct DB queries: {str(e)}")
    
    # 4. Test SQLiteModelMetricsRepository methods
    logger.info("=== Testing SQLiteModelMetricsRepository ===")
    try:
        # Get alert rules
        sql_rules = await sql_repo.get_alert_rules(test_model_id)
        logger.info(f"SQLiteModelMetricsRepository.get_alert_rules returned: {type(sql_rules)}")
        logger.info(f"Rules count: {len(sql_rules)}")
        if sql_rules:
            logger.info(f"Sample rule: {sql_rules[0]}")
        
        # Get alerts
        sql_alerts = await sql_repo.get_triggered_alerts(test_model_id, test_version)
        logger.info(f"SQLiteModelMetricsRepository.get_triggered_alerts returned: {type(sql_alerts)}")
        if isinstance(sql_alerts, tuple):
            logger.info(f"Alerts tuple length: {len(sql_alerts)}")
            logger.info(f"Alerts count: {len(sql_alerts[0])}")
            if sql_alerts[0]:
                logger.info(f"Sample alert: {sql_alerts[0][0]}")
        else:
            logger.info(f"Alerts count: {len(sql_alerts)}")
            if sql_alerts:
                logger.info(f"Sample alert: {sql_alerts[0]}")
    except Exception as e:
        logger.error(f"Error with SQLiteModelMetricsRepository methods: {str(e)}")
    
    # 5. Test ModelMetricsRepository methods
    logger.info("=== Testing ModelMetricsRepository ===")
    try:
        # Get alert rules
        repo_rules, is_mock_rules = await metrics_repo.get_alert_rules(test_model_id)
        logger.info(f"ModelMetricsRepository.get_alert_rules returned is_mock={is_mock_rules}")
        logger.info(f"Rules count: {len(repo_rules)}")
        if repo_rules:
            logger.info(f"Sample rule: {repo_rules[0]}")
        
        # Get alerts
        repo_alerts, is_mock_alerts = await metrics_repo.get_triggered_alerts(test_model_id, test_version)
        logger.info(f"ModelMetricsRepository.get_triggered_alerts returned is_mock={is_mock_alerts}")
        logger.info(f"Alerts count: {len(repo_alerts)}")
        if repo_alerts:
            logger.info(f"Sample alert: {repo_alerts[0]}")
    except Exception as e:
        logger.error(f"Error with ModelMetricsRepository methods: {str(e)}")
    
    # 6. Test ModelMonitoringService methods
    logger.info("=== Testing ModelMonitoringService ===")
    try:
        # Get alert rules
        service_rules, is_mock_rules = await service.get_alert_rules(test_model_id)
        logger.info(f"ModelMonitoringService.get_alert_rules returned is_mock={is_mock_rules}")
        logger.info(f"Rules count: {len(service_rules)}")
        if service_rules:
            logger.info(f"Sample rule: {service_rules[0]}")
        
        # Get alerts
        service_alerts, is_mock_alerts = await service.get_triggered_alerts(test_model_id, test_version)
        logger.info(f"ModelMonitoringService.get_triggered_alerts returned is_mock={is_mock_alerts}")
        logger.info(f"Alerts count: {len(service_alerts)}")
        if service_alerts:
            logger.info(f"Sample alert: {service_alerts[0]}")
    except Exception as e:
        logger.error(f"Error with ModelMonitoringService methods: {str(e)}")
    
    logger.info("=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
