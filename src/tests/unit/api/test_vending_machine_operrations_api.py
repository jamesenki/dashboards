# Test endpoints for fetching operations data
# Verify payload structure matches expected format
# Test error handling (machine not found, etc.)
class TestVendingMachineOperationsAPI:

    def test_get_vending_machine_operations(self, test_client, sample_vm):
        """Test GET /api/vending-machines/{vm_id}/operations endpoint."""
        # Setup mock
        test_client.app.dependency_overrides[get_service] = lambda: VendingMachineService(mock_db)

        # Make request
        response = test_client.get(f"/api/vending-machines/{sample_vm.id}/operations")

        # Check response
        assert response.status_code == 200
        operations = response.json()
        assert isinstance(operations, list)
        assert len(operations) > 0
        for operation in operations:
            assert "id" in operation
            assert "name" in operation
            assert "type" in operation
            assert "state" in operation
            assert "start_time" in operation
            assert "end_time" in operation

    def test_get_vending_machine_operations_vm_not_found(self, test_client, sample_vm):
        """Test GET /api/vending-machines/{vm_id}/operations endpoint with non-existent VM."""
        # Setup mock
        test_client.app.dependency_overrides[get_service] = lambda: VendingMachineService(mock_db)

        # Make request
        response = test_client.get("/api/vending-machines/non-existent-vm/operations")

        # Check response
        assert response.status_code == 404

