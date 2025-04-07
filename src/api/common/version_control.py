"""
API version control utilities.

This module provides utilities for tracking and comparing API versions
to ensure compatibility between the database and mock implementations.
"""
import datetime
import json
import os
from pathlib import Path
from typing import Dict, Optional

# Current API version - increment this when making breaking changes
CURRENT_API_VERSION = "1.0.0"

# File to store API version history
VERSION_HISTORY_FILE = (
    Path(__file__).parent.parent.parent / "data" / "api_version_history.json"
)


def get_current_version() -> str:
    """Get the current API version."""
    return CURRENT_API_VERSION


def load_version_history() -> Dict:
    """Load the API version history from the file."""
    if not VERSION_HISTORY_FILE.exists():
        # Create directory if it doesn't exist
        VERSION_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Create a default history file
        default_history = {
            "database_api": {
                "version": CURRENT_API_VERSION,
                "last_updated": datetime.datetime.now().isoformat(),
                "endpoints": [
                    "/api/db/water-heaters",
                    "/api/db/water-heaters/{device_id}",
                    "/api/db/water-heaters/data-source",
                    "/api/db/water-heaters/health",
                ],
            },
            "mock_api": {
                "version": CURRENT_API_VERSION,
                "last_updated": datetime.datetime.now().isoformat(),
                "endpoints": [
                    "/api/mock/water-heaters",
                    "/api/mock/water-heaters/{device_id}",
                    "/api/mock/water-heaters/data-source",
                    "/api/mock/water-heaters/simulate/failure",
                    "/api/mock/water-heaters/simulation/status",
                ],
            },
        }
        with open(VERSION_HISTORY_FILE, "w") as f:
            json.dump(default_history, f, indent=2)
        return default_history

    with open(VERSION_HISTORY_FILE, "r") as f:
        return json.load(f)


def update_api_version(
    api_type: str, new_version: str, endpoints: Optional[list] = None
) -> None:
    """
    Update the API version history.

    Args:
        api_type: Either 'database_api' or 'mock_api'
        new_version: The new version string (e.g., '1.0.1')
        endpoints: Optional list of endpoints for this API version
    """
    history = load_version_history()

    if api_type not in history:
        history[api_type] = {}

    history[api_type]["version"] = new_version
    history[api_type]["last_updated"] = datetime.datetime.now().isoformat()

    if endpoints:
        history[api_type]["endpoints"] = endpoints

    with open(VERSION_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def check_version_compatibility() -> Dict:
    """
    Check if the database and mock API versions are compatible.

    Returns:
        Dict with compatibility status and details
    """
    history = load_version_history()

    db_version = history.get("database_api", {}).get("version", "0.0.0")
    mock_version = history.get("mock_api", {}).get("version", "0.0.0")

    # Simple version comparison - in a real app, we'd use semantic versioning
    compatible = db_version == mock_version

    return {
        "compatible": compatible,
        "database_api_version": db_version,
        "mock_api_version": mock_version,
        "current_version": CURRENT_API_VERSION,
        "timestamp": datetime.datetime.now().isoformat(),
        "details": "API versions are compatible"
        if compatible
        else "API versions may be incompatible",
    }
