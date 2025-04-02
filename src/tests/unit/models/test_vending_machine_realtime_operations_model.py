"""
Unit tests for the vending machine real-time operations models
"""
import unittest

from src.models.vending_machine_realtime_operations import (
    AssetHealthData,
    CycleTimeData,
    DispensePressureData,
    FlavorInventory,
    FreezerTemperatureData,
    GaugeData,
    RamLoadData,
    VendingMachineOperationsData,
)


class TestVendingMachineRealtimeOperationsModel(unittest.TestCase):
    """Test cases for vending machine real-time operations models"""

    def test_gauge_data_creation(self):
        """Test creating gauge data object"""
        gauge = GaugeData(min=0, max=100, needleValue=75.5)
        self.assertEqual(gauge.min, 0)
        self.assertEqual(gauge.max, 100)
        self.assertEqual(gauge.needleValue, 75.5)

        # Test dictionary conversion
        gauge_dict = gauge.model_dump()
        self.assertIsInstance(gauge_dict, dict)
        self.assertEqual(gauge_dict["min"], 0)
        self.assertEqual(gauge_dict["max"], 100)
        self.assertEqual(gauge_dict["needleValue"], 75.5)

    def test_flavor_inventory_creation(self):
        """Test creating flavor inventory object"""
        item = FlavorInventory(name="Vanilla", value=5)
        self.assertEqual(item.name, "Vanilla")
        self.assertEqual(item.value, 5)

        # Test dictionary conversion
        item_dict = item.model_dump()
        self.assertIsInstance(item_dict, dict)
        self.assertEqual(item_dict["name"], "Vanilla")
        self.assertEqual(item_dict["value"], 5)

    def test_ram_load_data_creation(self):
        """Test creating RAM load data object"""
        ram_data = RamLoadData(ramLoad=12.5, min=0, max=20, status="OK")
        self.assertEqual(ram_data.ramLoad, 12.5)
        self.assertEqual(ram_data.min, 0)
        self.assertEqual(ram_data.max, 20)
        self.assertEqual(ram_data.status, "OK")

        # Test dictionary conversion
        ram_dict = ram_data.model_dump()
        self.assertIsInstance(ram_dict, dict)
        self.assertEqual(ram_dict["ramLoad"], 12.5)
        self.assertEqual(ram_dict["min"], 0)
        self.assertEqual(ram_dict["max"], 20)
        self.assertEqual(ram_dict["status"], "OK")

    def test_operations_data_creation(self):
        """Test creating full operations data object"""
        # Create sub-components
        asset_health = AssetHealthData(assetHealth="75%", needleValue=75.0)

        freezer_temp = FreezerTemperatureData(
            freezerTemperature=-5.0, min=-25.0, max=0.0, needleValue=80.0
        )

        dispense_pressure = DispensePressureData(
            dispensePressure=5.8, min=2.0, max=8.0, needleValue=44.0
        )

        cycle_time = CycleTimeData(cycleTime=12.3, min=8.0, max=30.0, needleValue=70.0)

        ram_load = RamLoadData(ramLoad=12.2, min=0.0, max=20.0, status="OK")

        inventory = [
            FlavorInventory(name="Vanilla", value=2),
            FlavorInventory(name="Chocolate", value=7),
        ]

        # Create full operations data
        ops_data = VendingMachineOperationsData(
            assetId="test-123",
            assetLocation="Test Location",
            machineStatus="Online",
            podCode="PD_54",
            cupDetect="Yes",
            podBinDoor="Closed",
            customerDoor="Closed",
            assetHealthData=asset_health,
            freezerTemperatureData=freezer_temp,
            dispensePressureData=dispense_pressure,
            cycleTimeData=cycle_time,
            maxRamLoadData=ram_load,
            freezerInventory=inventory,
        )

        # Test basic properties
        self.assertEqual(ops_data.assetId, "test-123")
        self.assertEqual(ops_data.assetLocation, "Test Location")
        self.assertEqual(ops_data.machineStatus, "Online")
        self.assertEqual(ops_data.podCode, "PD_54")
        self.assertEqual(ops_data.cupDetect, "Yes")
        self.assertEqual(ops_data.podBinDoor, "Closed")
        self.assertEqual(ops_data.customerDoor, "Closed")

        # Test gauge components
        self.assertEqual(ops_data.assetHealthData.assetHealth, "75%")
        self.assertEqual(ops_data.assetHealthData.needleValue, 75.0)
        self.assertEqual(ops_data.freezerTemperatureData.freezerTemperature, -5.0)
        self.assertEqual(ops_data.dispensePressureData.dispensePressure, 5.8)
        self.assertEqual(ops_data.cycleTimeData.cycleTime, 12.3)

        # Test RAM load
        self.assertEqual(ops_data.maxRamLoadData.ramLoad, 12.2)
        self.assertEqual(ops_data.maxRamLoadData.status, "OK")

        # Test inventory
        self.assertEqual(len(ops_data.freezerInventory), 2)
        self.assertEqual(ops_data.freezerInventory[0].name, "Vanilla")
        self.assertEqual(ops_data.freezerInventory[0].value, 2)
        self.assertEqual(ops_data.freezerInventory[1].name, "Chocolate")
        self.assertEqual(ops_data.freezerInventory[1].value, 7)

        # Test dictionary conversion
        ops_dict = ops_data.model_dump()
        self.assertIsInstance(ops_dict, dict)
        self.assertEqual(ops_dict["assetId"], "test-123")
        self.assertEqual(ops_dict["assetLocation"], "Test Location")
        self.assertEqual(ops_dict["machineStatus"], "Online")
        self.assertEqual(len(ops_dict["freezerInventory"]), 2)
        self.assertEqual(ops_dict["freezerInventory"][0]["name"], "Vanilla")
        self.assertEqual(ops_dict["freezerInventory"][0]["value"], 2)


if __name__ == "__main__":
    unittest.main()
