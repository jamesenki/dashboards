"""
Tests for the complete alert workflow - following TDD principles.
This tests creation, storage, and retrieval of alerts.
"""
import asyncio
import os
import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient

from src.main import app
from src.db.real_database import SQLiteDatabase
from src.db.adapters.sqlite_model_metrics import SQLiteModelMetricsRepository

# Set environment variables to use real database for tests
os.environ["USE_MOCK_DATA"] = "False"

# Test client for API requests
client = TestClient(app)

# Global variables to store test data
test_rule_id = None
test_alert_id = None

@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for the test module."""
    loop = asyncio.get_event_loop()
    yield loop

@pytest.fixture(scope="module")
async def db_connection():
    """Initialize the database connection."""
    db = SQLiteDatabase(connection_string="data/iotsphere.db")
    yield db
    await db.close()

@pytest.fixture(scope="module")
async def sql_repo(db_connection):
    """Initialize the SQLite repository."""
    repo = SQLiteModelMetricsRepository(db=db_connection)
    yield repo

@pytest.mark.asyncio
async def test_create_alert_rule(sql_repo):
    """Test creating an alert rule."""
    global test_rule_id
    
    # Create a unique rule
    rule_id = str(uuid.uuid4())
    model_id = "test-model"
    metric_name = f"test_metric_{datetime.now().timestamp()}"
    threshold = 0.75
    condition = ">"
    severity = "WARNING"
    
    # Insert the rule into the database
    try:
        # First check schema to determine correct columns
        cursor = await sql_repo.db.execute("PRAGMA table_info(alert_rules)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Base columns
        base_columns = ['id', 'model_id', 'metric_name', 'threshold', 'severity']
        values = [rule_id, model_id, metric_name, threshold, severity]
        
        # Add operator/condition column if it exists
        if 'operator' in column_names:
            base_columns.append('operator')
            values.append(condition)
        if 'condition' in column_names:
            base_columns.append('condition')
            values.append(condition)
            
        # Add active column if it exists
        if 'active' in column_names:
            base_columns.append('active')
            values.append(1)
        elif 'is_active' in column_names:
            base_columns.append('is_active')
            values.append(1)
            
        # Create rule
        placeholders = ','.join(['?'] * len(values))
        cols = ','.join(base_columns)
        
        query = f"INSERT INTO alert_rules ({cols}) VALUES ({placeholders})"
        await sql_repo.db.execute(query, tuple(values))
        
        # Store rule_id for later tests
        test_rule_id = rule_id
        
        # Verify rule was created
        result_cursor = await sql_repo.db.execute("SELECT * FROM alert_rules WHERE id = ?", (rule_id,))
        rule = await result_cursor.fetchone()
        
        assert rule is not None
        assert rule['id'] == rule_id
        assert rule['metric_name'] == metric_name
        
        print(f"Successfully created test rule: {rule_id}")
        
    except Exception as e:
        pytest.fail(f"Failed to create alert rule: {str(e)}")

@pytest.mark.asyncio
async def test_create_alert_event(sql_repo):
    """Test creating an alert event."""
    global test_rule_id, test_alert_id
    
    assert test_rule_id is not None, "Must run test_create_alert_rule first"
    
    # Create alert event
    event_id = str(uuid.uuid4())
    model_id = "test-model"
    metric_name = f"test_metric_{datetime.now().timestamp()}"
    metric_value = 0.85  # Above threshold
    severity = "WARNING"
    timestamp = datetime.now().isoformat()
    
    try:
        # Insert alert event
        query = """
        INSERT INTO alert_events 
            (id, rule_id, model_id, metric_name, metric_value, severity, created_at, resolved) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (event_id, test_rule_id, model_id, metric_name, metric_value, severity, timestamp, 0)
        await sql_repo.db.execute(query, params)
        
        # Store event_id for later tests
        test_alert_id = event_id
        
        # Verify alert was created
        result_cursor = await sql_repo.db.execute("SELECT * FROM alert_events WHERE id = ?", (event_id,))
        alert = await result_cursor.fetchone()
        
        assert alert is not None
        assert alert['id'] == event_id
        assert alert['rule_id'] == test_rule_id
        assert alert['metric_name'] == metric_name
        
        print(f"Successfully created test alert event: {event_id}")
        
    except Exception as e:
        pytest.fail(f"Failed to create alert event: {str(e)}")

def test_api_get_alerts():
    """Test retrieving alerts via the API endpoint."""
    global test_alert_id
    
    assert test_alert_id is not None, "Must run test_create_alert_event first"
    
    # Call the API endpoint
    response = client.get("/api/monitoring/alerts")
    
    # Check response
    assert response.status_code == 200
    
    # Parse the response
    alerts = response.json()
    
    # Verify the response is a list
    assert isinstance(alerts, list), f"Expected list, got {type(alerts)}"
    
    # Try to find our test alert in the response
    found_test_alert = False
    for alert in alerts:
        if 'id' in alert and alert['id'] == test_alert_id:
            found_test_alert = True
            break
    
    # Assert our test alert was found
    assert found_test_alert, f"Test alert {test_alert_id} not found in response. Alerts count: {len(alerts)}"
    
    print(f"Successfully retrieved alerts from API. Found {len(alerts)} alerts including our test alert.")

if __name__ == "__main__":
    # Run tests manually
    pytest.main(["-xvs", __file__])
