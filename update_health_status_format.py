"""
Script to update health status formats in the database.
This will update health status values to match the expected frontend values.
"""
import os
import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "data/iotsphere.db"

def main():
    """Update health status formats in the database."""
    logger.info("Starting health status format update")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Map the current health status values to the expected frontend values
        status_mapping = {
            'healthy': 'GREEN',
            'drifting': 'YELLOW',
            'degraded': 'RED',
            'unknown': 'GREY'
        }
        
        # Update the model_health table
        for old_status, new_status in status_mapping.items():
            cursor.execute("""
            UPDATE model_health
            SET health_status = ?
            WHERE health_status = ?
            """, (new_status, old_status))
            
            logger.info(f"Updated {cursor.rowcount} records in model_health from {old_status} to {new_status}")
            
        # Update the model_health_reference table
        for old_status, new_status in status_mapping.items():
            cursor.execute("""
            UPDATE model_health_reference
            SET health_status = ?
            WHERE health_status = ?
            """, (new_status, old_status))
            
            logger.info(f"Updated {cursor.rowcount} records in model_health_reference from {old_status} to {new_status}")
        
        # Commit changes
        conn.commit()
        logger.info("Successfully updated health status formats")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating health status formats: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
