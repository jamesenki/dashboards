"""
Environment variable loader for IoTSphere.
Provides consistent access to environment variables across all scripts.
"""
import os
from pathlib import Path

from dotenv import load_dotenv


def load_env_vars():
    """
    Load environment variables from .env file.
    Returns True if successful, False otherwise.
    """
    # Try to locate .env file by searching up from current directory
    env_path = find_dotenv_file()

    if env_path:
        load_dotenv(env_path)
        return True
    else:
        # Fallback to load_dotenv default behavior (looking in current directory)
        return load_dotenv()


def find_dotenv_file():
    """
    Find .env file by searching up from current directory.
    Returns the path to the .env file if found, None otherwise.
    """
    current_dir = Path(os.path.abspath(os.path.dirname(__file__)))

    # Look for .env in current directory and parents
    while current_dir != current_dir.parent:
        env_file = current_dir / ".env"
        if env_file.exists():
            return str(env_file)
        current_dir = current_dir.parent

    # Look for .env in project root (additional check)
    project_root = Path(
        os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    )
    env_file = project_root / ".env"
    if env_file.exists():
        return str(env_file)

    return None


def get_db_credentials():
    """
    Get database credentials from environment variables.
    Returns a dictionary with the credentials.
    """
    load_env_vars()

    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "user": os.getenv("DB_USER", "iotsphere"),
        "password": os.getenv("DB_PASSWORD", "iotsphere"),
        "database": os.getenv("DB_NAME", "iotsphere"),
    }
