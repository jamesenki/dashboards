#!/usr/bin/env python3
"""
Test runner for the SecureModelLoader tests.

This script sets up the correct environment and runs the tests
for the secure model loading functionality.
"""
import os
import sys
import subprocess
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.append(str(src_dir.absolute()))

def run_tests():
    """Run the SecureModelLoader tests."""
    print("Running SecureModelLoader tests...")
    
    # Path to the test file
    test_file = src_dir / "tests" / "unit" / "security" / "test_secure_model_loader.py"
    
    # Ensure the test file exists
    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        return False
    
    # Run pytest with verbose output
    cmd = [
        sys.executable, "-m", "pytest", 
        str(test_file), "-v"
    ]
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        
        # Print the test output
        print(result.stdout)
        
        if result.stderr:
            print("Error output:")
            print(result.stderr)
        
        # Return True if all tests passed
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    # Ensure we're running from the project root
    os.chdir(Path(__file__).parent)
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed successfully!")
    else:
        print("\n❌ Tests failed. Please check the output above for details.")
        sys.exit(1)
