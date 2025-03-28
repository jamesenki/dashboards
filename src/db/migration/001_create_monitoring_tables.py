"""
Migration script to create monitoring tables for model metrics and alerts.
"""
from src.db.migration import Migration


class CreateMonitoringTablesMigration(Migration):
    """
    Migration to create tables for model monitoring functionality.
    """
    
    def __init__(self):
        """Initialize the migration with version and description."""
        super().__init__(
            version="001",
            description="Create model monitoring and alerts tables"
        )
        
    def up(self, connection):
        """
        Apply the migration.
        
        Args:
            connection: Database connection
        """
        cursor = connection.cursor()
        
        # Read the SQL from the file
        with open('src/db/migration/001_create_monitoring_tables.sql', 'r') as sql_file:
            sql = sql_file.read()
            
        # Split the SQL script by statements and execute each one
        for statement in sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
                
        connection.commit()
        
    def down(self, connection):
        """
        Rollback the migration.
        
        Args:
            connection: Database connection
        """
        cursor = connection.cursor()
        
        # Drop tables in reverse order of dependencies
        tables = [
            "alert_events",
            "alert_rules",
            "model_metrics",
            "model_metadata"
        ]
        
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
        connection.commit()
