#!/usr/bin/env python
"""
Archive Mock Data

This script archives all mock data files and removes mock data fallbacks
from the codebase, replacing them with proper error messages.
"""

import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path


def archive_mock_data():
    """Archive mock data files and create a backup."""

    # Define project root
    project_root = Path(__file__).parent.parent.parent

    # Create archive directory if it doesn't exist
    archive_dir = project_root / "archived_mock_data"
    os.makedirs(archive_dir, exist_ok=True)

    # Create timestamp for archive filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = archive_dir / f"mock_data_backup_{timestamp}.zip"

    # Files and directories to archive
    mock_data_paths = [
        # Utility mock data
        project_root / "src/utils/aquatherm_data.py",
        project_root / "src/utils/dummy_data.py",
        # Frontend mock data scripts
        project_root / "frontend/static/js/aquatherm-test-helper.js",
        project_root / "frontend/static/js/aquatherm-water-heater.js",
        project_root / "frontend/static/js/aquatherm-ui-debug.js",
        project_root / "frontend/static/js/tests/aquatherm-card-test.js",
        project_root / "frontend/static/js/aquatherm-fix.js",
        project_root / "frontend/static/js/aquatherm-card-fix.js",
        # Mock repositories
        project_root / "src/repositories/mock_water_heater_repository.py",
    ]

    # Create a zip archive
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for path in mock_data_paths:
            if path.exists():
                relative_path = path.relative_to(project_root)
                print(f"Archiving: {relative_path}")
                zipf.write(path, arcname=relative_path)
            else:
                print(f"Skipping (not found): {path}")

    print(f"\nMock data archived to: {zip_filename}")

    return zip_filename


if __name__ == "__main__":
    archive_path = archive_mock_data()
    print("\nArchiving complete. Mock data has been preserved in a zip file.")
    print("Next steps:")
    print("1. Replace mock data fallbacks with proper error messages")
    print("2. Update the UI to handle database connection errors gracefully")
    print("3. Run the UI validation script to confirm only real data is displayed")
