"""
Debug script to understand the import system and module resolution
for src.db.models vs src.db.models.py confusion
"""

import importlib
import inspect
import os
import sys


def debug_module(module_name):
    """Debug info about a module's location and contents"""
    print(f"\n=== Debugging module: {module_name} ===")

    try:
        # Try to import the module
        module = importlib.import_module(module_name)

        # Print module file location
        print(f"Module file: {getattr(module, '__file__', 'None')}")

        # Print module objects
        print(f"Module contents: {dir(module)}")

        # Print if the module is a package
        print(f"Is package: {getattr(module, '__package__', 'None')}")

        # For packages, print submodules
        if hasattr(module, "__path__"):
            print(f"Package path: {module.__path__}")
            if hasattr(module, "__all__"):
                print(f"Exported names (__all__): {module.__all__}")

        return module
    except Exception as e:
        print(f"Error importing {module_name}: {e}")
        return None


# Debug the modules involved in circular imports
print("\n=== Python Import System Debug ===")
print(f"Python version: {sys.version}")
print(f"sys.path: {sys.path}")

# Debug the main modules involved
db_module = debug_module("src.db")
models_module = debug_module("src.db.models")

# Try direct import of DeviceModel
print("\n=== Attempting direct imports ===")
try:
    from src.db.models import DeviceModel

    print("Successfully imported DeviceModel from src.db.models")
    print(f"DeviceModel class: {DeviceModel}")
    print(f"DeviceModel module: {DeviceModel.__module__}")
except ImportError as e:
    print(f"Failed to import DeviceModel: {e}")

# Try importing from models.py directly if possible
print("\n=== Trying alternative import paths ===")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "db"))
    import models as models_py

    print(f"Directly imported models.py: {models_py}")
    print(f"models.py contents: {dir(models_py)}")
    if hasattr(models_py, "DeviceModel"):
        print("DeviceModel found in models.py!")
except Exception as e:
    print(f"Failed alternative import: {e}")
