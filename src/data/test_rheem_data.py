"""
Test data for AquaTherm water heaters (implemented based on Rheem models)
"""
import random
import uuid
from datetime import datetime, timedelta

from src.models.device import DeviceStatus
from src.models.rheem_water_heater import (
    RheemEcoNetStatus,
    RheemProductSeries,
    RheemWaterHeater,
    RheemWaterHeaterMode,
    RheemWaterHeaterType,
)


def get_test_rheem_water_heaters():
    """
    Generate test AquaTherm water heater data for development and testing.
    This implements our Rheem-based features but uses a different brand name.

    Returns:
        list: List of RheemWaterHeater objects (using AquaTherm branding)
    """
    now = datetime.now()

    # Create a list to hold all water heaters
    water_heaters = []

    # --------- TANK WATER HEATERS ---------

    # Tank model #1
    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-tank-001",
            name="Master Bath HydroMax",
            status=DeviceStatus.ONLINE,
            location="Master Bathroom",
            last_seen=now,
            heater_type=RheemWaterHeaterType.TANK,
            series=RheemProductSeries.PROFESSIONAL,
            manufacturer="Rheem",
            target_temperature=49.0,  # 120°F
            current_temperature=48.5,
            mode=RheemWaterHeaterMode.ENERGY_SAVER,
            smart_enabled=True,
            capacity=50.0,
            uef_rating=0.93,
            energy_star_certified=True,
            installation_date=now - timedelta(days=90),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=75,
                last_connected=now - timedelta(minutes=5),
                firmware_version="2.3.5",
                update_available=False,
                remote_control_enabled=True,
            ),
        )
    )

    # Tank model #2
    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-tank-002",
            name="Basement HydroMax Plus",
            status=DeviceStatus.ONLINE,
            location="Basement",
            last_seen=now,
            heater_type=RheemWaterHeaterType.TANK,
            series=RheemProductSeries.PERFORMANCE_PLATINUM,
            target_temperature=48.0,  # 118°F
            current_temperature=48.0,
            mode=RheemWaterHeaterMode.ENERGY_SAVER,
            smart_enabled=True,
            capacity=75.0,
            uef_rating=0.95,
            energy_star_certified=True,
            installation_date=now - timedelta(days=180),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=92,
                last_connected=now - timedelta(minutes=15),
                firmware_version="2.3.7",
                update_available=True,
                remote_control_enabled=True,
            ),
        )
    )

    # Tank model #3 - offline for variety
    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-tank-003",
            name="Guest Bath HydroMax",
            status=DeviceStatus.OFFLINE,
            location="Guest Bathroom",
            last_seen=now - timedelta(hours=48),
            heater_type=RheemWaterHeaterType.TANK,
            series=RheemProductSeries.CLASSIC,
            target_temperature=46.0,  # 115°F
            current_temperature=20.0,  # Cooled down since offline
            mode=RheemWaterHeaterMode.ENERGY_SAVER,
            smart_enabled=True,
            capacity=40.0,
            uef_rating=0.88,
            energy_star_certified=False,
            installation_date=now - timedelta(days=365),
            econet_status=RheemEcoNetStatus(
                connected=False,
                wifi_signal_strength=0,
                last_connected=now - timedelta(hours=48),
                firmware_version="2.2.0",
                update_available=True,
                remote_control_enabled=True,
            ),
        )
    )

    # --------- HYBRID WATER HEATERS ---------

    # Hybrid model #1
    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-hybrid-001",
            name="Garage HydroMax EcoHybrid",
            status=DeviceStatus.ONLINE,
            location="Garage",
            last_seen=now,
            heater_type=RheemWaterHeaterType.HYBRID,
            series=RheemProductSeries.PROTERRA,
            manufacturer="Rheem",
            target_temperature=51.5,  # 125°F
            current_temperature=50.0,
            mode=RheemWaterHeaterMode.HEAT_PUMP,
            smart_enabled=True,
            capacity=65.0,
            uef_rating=4.0,
            energy_star_certified=True,
            installation_date=now - timedelta(days=45),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=82,
                last_connected=now - timedelta(minutes=2),
                firmware_version="3.1.0",
                update_available=True,
                remote_control_enabled=True,
            ),
        )
    )

    # Hybrid model #2
    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-hybrid-002",
            name="Utility Room EcoHybrid Pro",
            status=DeviceStatus.ONLINE,
            location="Utility Room",
            last_seen=now,
            heater_type=RheemWaterHeaterType.HYBRID,
            series=RheemProductSeries.PROFESSIONAL,
            target_temperature=52.0,  # 126°F
            current_temperature=51.0,
            mode=RheemWaterHeaterMode.HIGH_DEMAND,
            smart_enabled=True,
            capacity=80.0,
            uef_rating=3.8,
            energy_star_certified=True,
            installation_date=now - timedelta(days=30),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=95,
                last_connected=now - timedelta(minutes=1),
                firmware_version="3.1.1",
                update_available=False,
                remote_control_enabled=True,
            ),
        )
    )

    # --------- TANKLESS WATER HEATERS ---------

    # Tankless model #1
    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-tankless-001",
            name="Kitchen FlowMax Tankless",
            status=DeviceStatus.ONLINE,
            location="Kitchen",
            last_seen=now,
            heater_type=RheemWaterHeaterType.TANKLESS,
            series=RheemProductSeries.PERFORMANCE_PLATINUM,
            manufacturer="Rheem",
            target_temperature=54.0,  # 130°F
            current_temperature=54.0,
            mode=RheemWaterHeaterMode.HIGH_DEMAND,
            smart_enabled=True,
            uef_rating=0.95,
            energy_star_certified=True,
            installation_date=now - timedelta(days=120),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=90,
                last_connected=now - timedelta(minutes=1),
                firmware_version="2.5.0",
                update_available=False,
                remote_control_enabled=True,
            ),
        )
    )

    # Tankless model #2
    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-tankless-002",
            name="Master Suite FlowMax Elite",
            status=DeviceStatus.ONLINE,
            location="Master Suite",
            last_seen=now,
            heater_type=RheemWaterHeaterType.TANKLESS,
            series=RheemProductSeries.PRESTIGE,
            manufacturer="Rheem",
            target_temperature=52.0,  # 126°F
            current_temperature=52.0,
            mode=RheemWaterHeaterMode.ENERGY_SAVER,
            smart_enabled=True,
            uef_rating=0.97,
            energy_star_certified=True,
            installation_date=now - timedelta(days=60),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=88,
                last_connected=now - timedelta(minutes=3),
                firmware_version="2.5.2",
                update_available=False,
                remote_control_enabled=True,
            ),
        )
    )

    # Tankless model #3
    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-tankless-003",
            name="Apartment FlowMax Compact",
            status=DeviceStatus.ONLINE,
            location="Rental Apartment",
            last_seen=now,
            heater_type=RheemWaterHeaterType.TANKLESS,
            series=RheemProductSeries.CLASSIC,
            manufacturer="Rheem",
            target_temperature=50.0,  # 122°F
            current_temperature=49.5,
            mode=RheemWaterHeaterMode.ENERGY_SAVER,
            smart_enabled=True,
            uef_rating=0.93,
            energy_star_certified=True,
            installation_date=now - timedelta(days=240),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=78,
                last_connected=now - timedelta(minutes=10),
                firmware_version="2.4.1",
                update_available=True,
                remote_control_enabled=True,
            ),
        )
    )

    # Add 8 more water heaters to reach the required total of 16

    # Additional tank water heaters
    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-tank-004",
            name="Second Floor HydroMax",
            status=DeviceStatus.ONLINE,
            location="Upstairs Utility",
            last_seen=now,
            heater_type=RheemWaterHeaterType.TANK,
            series=RheemProductSeries.PROFESSIONAL,
            manufacturer="Rheem",
            target_temperature=48.0,  # 118°F
            current_temperature=48.0,
            mode=RheemWaterHeaterMode.ENERGY_SAVER,
            smart_enabled=True,
            capacity=50.0,
            uef_rating=0.93,
            energy_star_certified=True,
            installation_date=now - timedelta(days=180),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=88,
                last_connected=now - timedelta(minutes=7),
                firmware_version="2.3.5",
                update_available=True,
                remote_control_enabled=True,
            ),
        )
    )

    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-tank-005",
            name="Backyard Guest House HydroMax",
            status=DeviceStatus.ONLINE,
            location="Guest House",
            last_seen=now,
            heater_type=RheemWaterHeaterType.TANK,
            series=RheemProductSeries.PERFORMANCE_PLATINUM,
            manufacturer="Rheem",
            target_temperature=47.0,  # 117°F
            current_temperature=47.5,
            mode=RheemWaterHeaterMode.ENERGY_SAVER,
            smart_enabled=True,
            capacity=40.0,
            uef_rating=0.92,
            energy_star_certified=True,
            installation_date=now - timedelta(days=45),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=70,
                last_connected=now - timedelta(minutes=3),
                firmware_version="2.3.5",
                update_available=False,
                remote_control_enabled=True,
            ),
        )
    )

    # Additional hybrid water heaters
    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-hybrid-003",
            name="Workshop EcoHybrid",
            status=DeviceStatus.ONLINE,
            location="Workshop",
            last_seen=now,
            heater_type=RheemWaterHeaterType.HYBRID,
            series=RheemProductSeries.PROTERRA,
            manufacturer="Rheem",
            target_temperature=50.0,  # 122°F
            current_temperature=49.5,
            mode=RheemWaterHeaterMode.HEAT_PUMP,
            smart_enabled=True,
            capacity=65.0,
            uef_rating=3.9,
            energy_star_certified=True,
            installation_date=now - timedelta(days=60),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=85,
                last_connected=now - timedelta(minutes=1),
                firmware_version="3.1.0",
                update_available=False,
                remote_control_enabled=True,
            ),
        )
    )

    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-hybrid-004",
            name="Main Building EcoHybrid Pro",
            status=DeviceStatus.ONLINE,
            location="Main Building",
            last_seen=now,
            heater_type=RheemWaterHeaterType.HYBRID,
            series=RheemProductSeries.PROFESSIONAL,
            manufacturer="Rheem",
            target_temperature=51.0,  # 124°F
            current_temperature=51.0,
            mode=RheemWaterHeaterMode.ELECTRIC,
            smart_enabled=True,
            capacity=80.0,
            uef_rating=4.0,
            energy_star_certified=True,
            installation_date=now - timedelta(days=15),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=92,
                last_connected=now - timedelta(minutes=2),
                firmware_version="3.1.1",
                update_available=False,
                remote_control_enabled=True,
            ),
        )
    )

    # Additional tankless water heaters
    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-tankless-004",
            name="Laundry Room FlowMax",
            status=DeviceStatus.ONLINE,
            location="Laundry Room",
            last_seen=now,
            heater_type=RheemWaterHeaterType.TANKLESS,
            series=RheemProductSeries.PERFORMANCE_PLATINUM,
            manufacturer="Rheem",
            target_temperature=52.0,  # 126°F
            current_temperature=52.0,
            mode=RheemWaterHeaterMode.ENERGY_SAVER,
            smart_enabled=True,
            uef_rating=0.96,
            energy_star_certified=True,
            installation_date=now - timedelta(days=90),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=80,
                last_connected=now - timedelta(minutes=8),
                firmware_version="2.4.0",
                update_available=True,
                remote_control_enabled=True,
            ),
        )
    )

    # Additional water heaters with different series
    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-prestige-001",
            name="Pool House Prestige",
            status=DeviceStatus.ONLINE,
            location="Pool House",
            last_seen=now,
            heater_type=RheemWaterHeaterType.TANK,
            series=RheemProductSeries.PRESTIGE,
            manufacturer="Rheem",
            target_temperature=45.0,  # 113°F
            current_temperature=45.0,
            mode=RheemWaterHeaterMode.ENERGY_SAVER,
            smart_enabled=True,
            capacity=85.0,
            uef_rating=0.91,
            energy_star_certified=True,
            installation_date=now - timedelta(days=210),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=78,
                last_connected=now - timedelta(minutes=12),
                firmware_version="2.2.5",
                update_available=True,
                remote_control_enabled=True,
            ),
        )
    )

    water_heaters.append(
        RheemWaterHeater(
            id="aqua-wh-classicp-001",
            name="Fitness Center Classic Plus",
            status=DeviceStatus.ONLINE,
            location="Fitness Center",
            last_seen=now,
            heater_type=RheemWaterHeaterType.TANK,
            series=RheemProductSeries.CLASSIC_PLUS,
            manufacturer="Rheem",
            target_temperature=49.0,  # 120°F
            current_temperature=49.0,
            mode=RheemWaterHeaterMode.ENERGY_SAVER,
            smart_enabled=True,
            capacity=75.0,
            uef_rating=0.90,
            energy_star_certified=True,
            installation_date=now - timedelta(days=75),
            econet_status=RheemEcoNetStatus(
                connected=True,
                wifi_signal_strength=88,
                last_connected=now - timedelta(minutes=3),
                firmware_version="2.2.0",
                update_available=False,
                remote_control_enabled=True,
            ),
        )
    )

    return water_heaters
