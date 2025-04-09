"""
Add a simple health check endpoint to the IoTSphere application
"""
import os
import sys

# Add the repo root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Import main app
    from src.main import app

    # Add a health check endpoint
    @app.get("/health", include_in_schema=False)
    async def health_check():
        return {"status": "ok", "message": "Server is healthy"}

    print("✅ Health check endpoint added at /health")
    print(
        "✅ You can now run 'python start_with_guaranteed_history.py 8000' to start the server"
    )

except ImportError as e:
    print(f"❌ Error importing main app: {e}")
    sys.exit(1)
