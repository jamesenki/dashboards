#!/usr/bin/env python3
"""
Unit tests for the Asset Registry API endpoints.
Testing the API endpoints that provide device metadata.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the API module
from src.api.asset_registry_api import get_device_metadata, update_device_metadata


class TestAssetRegistryAPI:
    """Tests for the Asset Registry API endpoints."""
    
    @pytest.fixture
    def mock_asset_service(self):
        """Create a mock asset registry service."""
        service = MagicMock()
        return service
    
    @pytest.fixture
    def sample_metadata(self):
        """Return sample device metadata for testing."""
        return {
            "device_id": "wh-test-001",
            "device_type": "water_heater",
            "manufacturer": "AquaTech",
            "model": "HeatMaster 5000",
            "serial_number": "AT-HM5K-12345",
            "firmware_version": "1.2.3",
            "installation_date": datetime.utcnow().isoformat(),
            "location": {
                "building": "Main Campus",
                "floor": "3",
                "room": "304B"
            },
            "specifications": {
                "capacity": "80",
                "voltage": "240",
                "wattage": "4500"
            }
        }
    
    @pytest.mark.asyncio
    async def test_get_device_metadata(self, mock_asset_service, sample_metadata):
        """Test retrieving device metadata."""
        # Setup
        mock_asset_service.get_device_info.return_value = sample_metadata
        mock_request = MagicMock()
        mock_request.match_info = {"device_id": "wh-test-001"}
        
        # Execute with dependency injection
        with patch('src.api.asset_registry_api.get_asset_service', 
                  return_value=mock_asset_service):
            response = await get_device_metadata(mock_request)
        
        # Verify
        assert response.status == 200
        response_data = json.loads(response.body.decode())
        assert response_data["device_id"] == "wh-test-001"
        assert response_data["manufacturer"] == "AquaTech"
        assert "location" in response_data
        assert response_data["location"]["room"] == "304B"
        
        # Verify correct service method was called
        mock_asset_service.get_device_info.assert_called_once_with("wh-test-001")
    
    @pytest.mark.asyncio
    async def test_get_device_metadata_not_found(self, mock_asset_service):
        """Test retrieving metadata for non-existent device."""
        # Setup
        mock_asset_service.get_device_info.side_effect = ValueError("Device not found")
        mock_request = MagicMock()
        mock_request.match_info = {"device_id": "wh-nonexistent"}
        
        # Execute with dependency injection
        with patch('src.api.asset_registry_api.get_asset_service', 
                  return_value=mock_asset_service):
            response = await get_device_metadata(mock_request)
        
        # Verify
        assert response.status == 404
        response_data = json.loads(response.body.decode())
        assert "error" in response_data
        assert "not found" in response_data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_update_device_metadata(self, mock_asset_service, sample_metadata):
        """Test updating device metadata."""
        # Setup
        mock_asset_service.update_device_metadata.return_value = {
            **sample_metadata,
            "location": {
                "building": "Main Campus",
                "floor": "4",  # Updated floor
                "room": "401A"  # Updated room
            }
        }
        
        mock_request = MagicMock()
        mock_request.match_info = {"device_id": "wh-test-001"}
        mock_request.json.return_value = {
            "location": {
                "building": "Main Campus",
                "floor": "4",
                "room": "401A"
            }
        }
        
        # Execute with dependency injection
        with patch('src.api.asset_registry_api.get_asset_service', 
                  return_value=mock_asset_service):
            response = await update_device_metadata(mock_request)
        
        # Verify
        assert response.status == 200
        response_data = json.loads(response.body.decode())
        assert response_data["location"]["floor"] == "4"
        assert response_data["location"]["room"] == "401A"
        
        # Verify correct service method was called with right parameters
        mock_asset_service.update_device_metadata.assert_called_once()
        call_args = mock_asset_service.update_device_metadata.call_args[0]
        assert call_args[0] == "wh-test-001"  # device_id
        assert "location" in call_args[1]  # updates
        assert call_args[1]["location"]["room"] == "401A"
