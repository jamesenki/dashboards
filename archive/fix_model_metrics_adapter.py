#!/usr/bin/env python
"""
Script to fix the SQLiteModelMetricsRepository to handle both 'active' and 'is_active' column names.

This script follows the TDD principle of adapting code to pass tests rather than changing tests.
"""
import os
import sys
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_adapter_file():
    """Fix the SQLiteModelMetricsRepository adapter file to handle both column name formats."""
    file_path = os.path.join("src", "db", "adapters", "sqlite_model_metrics.py")
    
    if not os.path.exists(file_path):
        logger.error(f"Adapter file not found at {file_path}")
        return False
    
    logger.info(f"Fixing adapter file at {file_path}")
    
    # Read the file content
    with open(file_path, "r") as f:
        content = f.read()
    
    # Make a backup
    import time
    backup_path = f"{file_path}.bak.{int(time.time())}"
    with open(backup_path, "w") as f:
        f.write(content)
    logger.info(f"Created backup at {backup_path}")
    
    # Update the get_alert_rules method to handle both column name formats
    updated_content = content
    
    # Add is_active column detection
    active_column_check = """            # Check if is_active column exists, if not we'll use active as fallback
            has_is_active = 'is_active' in column_names
            activity_column = 'is_active' if has_is_active else 'active'
            
            # Need to include activity column in our select if it exists
            if has_is_active:
                column_list.append('is_active')"""
    
    # Pattern to find the location for active column check just before query building
    pattern = r"((\s+)# Build the query)"
    
    # Add the active column check
    updated_content = re.sub(pattern, f"{active_column_check}\\1", updated_content)
    
    # Update queries to use dynamic column name
    updated_content = updated_content.replace(
        "WHERE model_id = ? AND active = 1",
        "WHERE model_id = ? AND " + activity_column + " = 1"
    )
    
    updated_content = updated_content.replace(
        "WHERE active = 1",
        "WHERE " + activity_column + " = 1"
    )
    
    # Write the updated content
    with open(file_path, "w") as f:
        f.write(updated_content)
    
    logger.info(f"Successfully updated {file_path}")
    
    # Create a simpler direct replacement
    simple_fix_path = os.path.join("src", "db", "adapters", "fix_column_names.py")
    with open(simple_fix_path, "w") as f:
        f.write('''"""
Fix script to update column name references in SQLiteModelMetricsRepository.
"""
import re
import logging
import os

logger = logging.getLogger(__name__)

def fix_column_names():
    """Update active to is_active in SQLiteModelMetricsRepository."""
    file_path = os.path.join("src", "db", "adapters", "sqlite_model_metrics.py")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    # Read the file
    with open(file_path, "r") as f:
        content = f.read()
    
    # Simple string replacements
    updated_content = content.replace(
        "model_id = ? AND active = 1",
        "model_id = ? AND is_active = 1"
    )
    
    updated_content = updated_content.replace(
        "WHERE active = 1",
        "WHERE is_active = 1"
    )
    
    # Write the updated content
    with open(file_path, "w") as f:
        f.write(updated_content)
    
    logger.info(f"Updated column references in {file_path}")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fix_column_names()
''')
    
    logger.info(f"Created simple fix script at {simple_fix_path}")
    return True

if __name__ == "__main__":
    success = fix_adapter_file()
    if success:
        logger.info("Model metrics adapter updated successfully")
        sys.exit(0)
    else:
        logger.error("Failed to update model metrics adapter")
        sys.exit(1)
