#!/usr/bin/env python
"""
Script to move unused files to the archive directory.
"""
import os
import shutil
from pathlib import Path

# Define base directory and archive directory
BASE_DIR = Path(__file__).parent
ARCHIVE_DIR = BASE_DIR / "archive"

# List of files to archive
FILES_TO_ARCHIVE = [
    # Temporary Test Scripts
    "test_model_monitoring.py",
    # Debug and Fix Scripts
    "data_source_fix.py",
    "test_alerts_db.py",
    "debug_alerts_query.py",
    "debug_db_access.py",
    "diagnose_alerts.py",
    "fix_alerts_api.py",
    "fix_alerts_frontend.py",
    "fix_model_metrics_adapter.py",
    "fix_models_dropdown.py",
    # Redundant Test Files
    "test_data_access_integration.py",
    "test_data_source.py",
    "test_database_to_ui_flow.py",
    "test_frontend_alerts.py",
    "test_repositories.py",
    "test_water_heater_config.py",
    # One-time Data Manipulation Scripts
    "generate_alert_event.py",
    "insert_alert_event.py",
    "populate_metrics_for_models.py",
    "set_model_health.py",
    "update_health_status_format.py",
]


def main():
    """Move files to archive directory."""
    # Ensure archive directory exists
    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    # Track successful and failed moves
    moved = []
    not_found = []

    # Move files to archive
    for filename in FILES_TO_ARCHIVE:
        src_path = BASE_DIR / filename
        dst_path = ARCHIVE_DIR / filename

        if src_path.exists():
            try:
                shutil.move(str(src_path), str(dst_path))
                moved.append(filename)
                print(f"✅ Moved: {filename}")
            except Exception as e:
                print(f"❌ Error moving {filename}: {e}")
        else:
            not_found.append(filename)
            print(f"⚠️ Not found: {filename}")

    # Print summary
    print("\n==== Summary ====")
    print(f"✅ Successfully moved: {len(moved)} files")
    print(f"⚠️ Not found: {len(not_found)} files")

    if moved:
        print("\nSuccessfully moved files:")
        for file in moved:
            print(f"  - {file}")

    if not_found:
        print("\nFiles not found:")
        for file in not_found:
            print(f"  - {file}")


if __name__ == "__main__":
    main()
