"""
Step definitions for Device Management BDD tests.
Following RED phase of TDD - define expected behavior before implementation.

This file implements the RED phase of Test-Driven Development by:
1. Defining the expected behavior through BDD steps
2. Ensuring tests will initially fail (as features are not yet implemented)
3. Setting up proper test isolation with mocks and fixtures
"""
import json
import logging
import os
import sys
from unittest.mock import MagicMock, patch

from behave import given, then, when
from fastapi.testclient import TestClient

# Add project root to Python path to make 'src' module importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import our application
from src.main import app

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a test client for the API
test_client = TestClient(app)

# Mock device data for testing
MOCK_DEVICES = {
    "Test Water Heater": {
        "id": "dev-wh-001",
        "name": "Test Water Heater",
        "manufacturer": "AquaTech",
        "model": "AT-5000",
        "serial_number": "AT5K-12345",
        "location": "Building A, Basement",
        "device_type": "water_heater",
        "status": "PENDING_ACTIVATION",
        "created_at": "2025-04-09T10:00:00Z",
        "updated_at": "2025-04-09T10:00:00Z",
    }
}


# Step implementations
@when("I navigate to the device management page")
def step_navigate_to_device_management(context):
    """
    RED PHASE: Simulate navigation to device management page.
    """
    logger.info("Navigating to device management page")

    try:
        # Make a request to the device management API
        response = context.client.get("/api/devices")
        logger.info(f"Device management API response status: {response.status_code}")

        # Store the response for verification in later steps
        context.response = response
        if response.status_code == 200:
            context.device_list = response.json()
        else:
            context.device_list = None
    except Exception as e:
        logger.error(f"Error navigating to device management: {str(e)}")
        context.exception = e
        context.response = None
        context.device_list = None

    # For UI testing, simulate that we're on the device management page
    context.current_page = "device_management"


@when('I select "Add New Device"')
def step_select_add_new_device(context):
    """
    RED PHASE: Simulate selecting Add New Device option.
    """
    logger.info("Selecting 'Add New Device' option")

    # Simulate navigation to device creation form
    context.current_page = "device_creation_form"
    context.new_device_data = {}


@when("I enter the following device information")
def step_enter_device_information(context):
    """
    RED PHASE: Process device information from table.
    """
    logger.info("Entering device information")

    # Initialize new device data if not exists
    if not hasattr(context, "new_device_data"):
        context.new_device_data = {}

    # Process the table data
    if context.table:
        for row in context.table:
            field = row["field"]
            value = row["value"]
            context.new_device_data[field] = value

    logger.info(f"Device information entered: {context.new_device_data}")


@when("I submit the device registration form")
def step_submit_device_registration(context):
    """
    RED PHASE: Simulate form submission for device registration.
    """
    logger.info("Submitting device registration form")

    # Ensure we have device data
    assert hasattr(context, "new_device_data"), "No device data to submit"

    try:
        # Make a request to create the device
        response = context.client.post("/api/devices", json=context.new_device_data)
        logger.info(f"Device creation API response status: {response.status_code}")

        # Store the response for verification in later steps
        context.response = response
        if response.status_code in [200, 201]:
            context.created_device = response.json()
            logger.info(f"Device created: {context.created_device}")
        else:
            context.created_device = None
            logger.warning(
                f"Device creation failed with status: {response.status_code}"
            )
    except Exception as e:
        logger.error(f"Error creating device: {str(e)}")
        context.exception = e
        context.response = None
        context.created_device = None


@then("the device should be successfully registered in the system")
def step_verify_device_registered(context):
    """
    RED PHASE: Verify device registration success.
    """
    logger.info("Verifying device registration")

    # Check response status
    assert hasattr(context, "response"), "No API response received"
    assert context.response.status_code in [
        200,
        201,
    ], f"Device registration failed with status: {context.response.status_code}"

    # Verify created device data
    assert hasattr(context, "created_device"), "No created device data available"
    assert "id" in context.created_device, "Created device missing ID"

    # Store device ID for later use
    context.device_id = context.created_device["id"]
    logger.info(f"Device registered with ID: {context.device_id}")


@then("I should see the new device in the device list")
def step_verify_device_in_list(context):
    """
    RED PHASE: Verify device appears in device list.
    """
    logger.info("Verifying device appears in list")

    try:
        # Make a request to get the updated device list
        response = context.client.get("/api/devices")
        context.response = response
        if response.status_code == 200:
            context.updated_device_list = response.json()
            logger.info(f"Retrieved updated device list")
        else:
            context.updated_device_list = None
            logger.warning(f"Failed to get device list: {response.status_code}")
    except Exception as e:
        logger.error(f"Error getting device list: {str(e)}")
        context.exception = e
        context.response = None
        context.updated_device_list = None

    # Verify the new device is in the list
    assert hasattr(context, "updated_device_list"), "No updated device list available"
    assert (
        "devices" in context.updated_device_list
    ), "Device list response missing 'devices' array"

    # Check if the device ID is in the list
    device_found = False
    for device in context.updated_device_list["devices"]:
        if device["id"] == context.device_id:
            device_found = True
            break

    assert device_found, f"Device with ID {context.device_id} not found in device list"


@then('the device should have status "{status}"')
def step_verify_device_status(context, status):
    """
    RED PHASE: Verify device has the correct status.
    """
    logger.info(f"Verifying device has status: {status}")

    # Check if we have a device ID
    assert hasattr(context, "device_id"), "No device ID available"

    try:
        # Make a request to get the device details
        response = context.client.get(f"/api/devices/{context.device_id}")
        context.response = response
        if response.status_code == 200:
            context.device_details = response.json()
            logger.info(f"Retrieved device details")
        else:
            context.device_details = None
            logger.warning(f"Failed to get device details: {response.status_code}")
    except Exception as e:
        logger.error(f"Error getting device details: {str(e)}")
        context.exception = e
        context.response = None
        context.device_details = None

    # Verify the device status
    assert hasattr(context, "device_details"), "No device details available"
    assert "status" in context.device_details, "Device details missing 'status' field"
    assert (
        context.device_details["status"] == status
    ), f"Device status is {context.device_details['status']}, expected {status}"


@given('a device with name "{name}" exists with status "{status}"')
def step_device_exists_with_status(context, name, status):
    """
    RED PHASE: Setup a device with the given name and status.
    """
    logger.info(f"Setting up device '{name}' with status '{status}'")

    # Initialize test client if not already available
    if not hasattr(context, "client"):
        context.client = test_client
        logger.info("Test client initialized")

    # Check if device exists in mock data
    if name in MOCK_DEVICES:
        # Use existing mock device
        device_data = MOCK_DEVICES[name].copy()
        device_data["status"] = status
        logger.info(f"Using mock device: {name}")
    else:
        # Create new mock device
        device_data = {
            "id": f"dev-{len(MOCK_DEVICES) + 1:03d}",
            "name": name,
            "status": status,
            "device_type": "water_heater",
        }
        logger.info(f"Created new mock device: {name}")

    # Store device data in context
    context.device_data = device_data
    context.device_id = device_data["id"]
    context.device_name = name

    # Verify the device exists in the system (or mock it for RED phase)
    try:
        # Try to get the device via API
        response = context.client.get(f"/api/devices?name={name}")
        if response.status_code == 200 and response.json().get("devices"):
            # Device exists, use real data
            for device in response.json()["devices"]:
                if device["name"] == name:
                    context.device_id = device["id"]
                    logger.info(f"Found existing device with ID: {context.device_id}")

                    # Update status if needed
                    if device["status"] != status:
                        update_response = context.client.patch(
                            f"/api/devices/{context.device_id}", json={"status": status}
                        )
                        if update_response.status_code == 200:
                            logger.info(f"Updated device status to {status}")
                        else:
                            logger.warning(
                                f"Failed to update device status: {update_response.status_code}"
                            )
                    break
            else:
                # Device not found, create it for RED phase
                logger.info(f"Device '{name}' not found, will be mocked for RED phase")
        else:
            # API call failed, proceed with mock
            logger.info(f"Device lookup failed, will use mock for RED phase")
    except Exception as e:
        logger.error(f"Error checking device existence: {str(e)}")
        logger.info(f"Will use mock device for RED phase")


@when('I select the device with name "{name}"')
def step_select_device_by_name(context, name):
    """
    RED PHASE: Simulate selecting a device from the list.
    """
    logger.info(f"Selecting device: {name}")

    # Verify we have device data
    assert hasattr(context, "device_name"), "No device_name in context"
    assert (
        context.device_name == name
    ), f"Expected device {name}, but context has {context.device_name}"

    # Simulate device selection
    context.selected_device = context.device_data
    context.current_page = "device_details"
    logger.info(f"Selected device: {context.selected_device}")


@when('I select "{action}"')
def step_select_device_action(context, action):
    """
    RED PHASE: Simulate selecting an action for a device.
    """
    logger.info(f"Selecting action: {action}")

    # Verify we have a selected device
    assert hasattr(context, "selected_device"), "No device selected"

    # Store the selected action
    context.selected_action = action

    # Update current page based on action
    action_page_map = {
        "Activate Device": "device_activation_form",
        "Edit Device": "device_edit_form",
        "Deactivate Device": "device_deactivation_confirmation",
        "Remove Device": "device_removal_confirmation",
    }

    if action in action_page_map:
        context.current_page = action_page_map[action]
        logger.info(f"Navigated to: {context.current_page}")
    else:
        logger.warning(f"Unknown action: {action}")


@when("I enter the following activation information")
def step_enter_activation_info(context):
    """
    RED PHASE: Process activation information from table.
    """
    logger.info("Entering activation information")

    # Initialize activation data
    context.activation_data = {}

    # Process the table data
    if context.table:
        for row in context.table:
            field = row["field"]
            value = row["value"]
            context.activation_data[field] = value

    logger.info(f"Activation information entered: {context.activation_data}")


@when("I submit the activation form")
def step_submit_activation_form(context):
    """
    RED PHASE: Simulate form submission for device activation.
    """
    logger.info("Submitting activation form")

    # Ensure we have activation data and device ID
    assert hasattr(context, "activation_data"), "No activation data to submit"
    assert hasattr(context, "device_id"), "No device ID available"

    try:
        # Make a request to activate the device
        response = context.client.post(
            f"/api/devices/{context.device_id}/activate", json=context.activation_data
        )
        logger.info(f"Device activation API response status: {response.status_code}")

        # Store the response for verification in later steps
        context.response = response
        if response.status_code == 200:
            context.activation_result = response.json()
            logger.info(f"Device activated successfully")
        else:
            context.activation_result = None
            logger.warning(
                f"Device activation failed with status: {response.status_code}"
            )
    except Exception as e:
        logger.error(f"Error activating device: {str(e)}")
        context.exception = e
        context.response = None
        context.activation_result = None


@then("the system should generate device credentials")
def step_verify_device_credentials(context):
    """
    RED PHASE: Verify device credentials are generated.
    """
    logger.info("Verifying device credentials generation")

    # Check activation result
    assert hasattr(context, "activation_result"), "No activation result available"

    # Verify credentials in result
    assert (
        "credentials" in context.activation_result
    ), "Activation result missing 'credentials'"
    credentials = context.activation_result["credentials"]

    # Check for required credential fields
    required_fields = ["client_id", "client_secret"]
    for field in required_fields:
        assert field in credentials, f"Credentials missing '{field}'"
        assert credentials[field], f"Empty value for credential field '{field}'"


@then("I should see the device connection information")
def step_verify_connection_info(context):
    """
    RED PHASE: Verify connection information is displayed.
    """
    logger.info("Verifying connection information display")

    # Check activation result
    assert hasattr(context, "activation_result"), "No activation result available"

    # Verify connection info in result
    assert (
        "connection_info" in context.activation_result
    ), "Activation result missing 'connection_info'"
    connection_info = context.activation_result["connection_info"]

    # Check for required connection fields
    required_fields = ["endpoint", "port", "protocol"]
    for field in required_fields:
        assert field in connection_info, f"Connection info missing '{field}'"
