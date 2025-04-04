"""
Migration script to convert existing water heater data to Rheem specifications.

This script provides utilities to:
1. Update database schema with new Rheem water heater tables
2. Convert existing water heater records to use Rheem product specifications
3. Backfill Rheem-specific attributes for existing data
"""

import logging
import os

# Import Base directly from models.py module, not from models package
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Add parent directory to path to ensure correct imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.db.models import Base  # noqa
from src.db.models.rheem_water_heater import (
    RheemProductSeries,
    RheemWaterHeaterDevice,
    RheemWaterHeaterMode,
    RheemWaterHeaterModel,
    RheemWaterHeaterSeries,
    RheemWaterHeaterTelemetry,
    WaterHeaterType,
)
from src.db.models.water_heater import WaterHeaterModel, WaterHeaterTelemetry
from src.utils.rheem_dummy_data import (
    RHEEM_DIAGNOSTIC_CODES,
    RHEEM_HYBRID_MODELS,
    RHEEM_TANK_MODELS,
    RHEEM_TANKLESS_MODELS,
    SERIES_FEATURES,
)

logger = logging.getLogger(__name__)


class RheemMigrationTool:
    """Tool for migrating existing water heater data to Rheem specifications."""

    def __init__(self, db_url: Optional[str] = None):
        """Initialize the migration tool with database connection."""
        if not db_url:
            # Default to SQLite database in development
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data",
                "iotsphere.db",
            )
            db_url = f"sqlite:///{db_path}"

        self.engine = create_engine(db_url)
        self.logger = logging.getLogger(__name__)

    def create_rheem_schema(self):
        """Create the necessary database tables for Rheem water heaters."""
        self.logger.info("Creating Rheem water heater schema")
        # Create only the Rheem water heater tables
        Base.metadata.create_all(
            self.engine,
            tables=[
                RheemWaterHeaterSeries.__table__,
                RheemWaterHeaterModel.__table__,
                RheemWaterHeaterDevice.__table__,
                RheemWaterHeaterTelemetry.__table__,
            ],
        )
        self.logger.info("Rheem water heater schema created successfully")

    def populate_rheem_product_catalog(self):
        """Populate the database with Rheem product series and models."""
        self.logger.info("Populating Rheem product catalog")

        with Session(self.engine) as session:
            # Add product series
            for series_name in RheemProductSeries:
                # Skip if series already exists
                existing = session.execute(
                    select(RheemWaterHeaterSeries).where(
                        RheemWaterHeaterSeries.name == series_name
                    )
                ).first()

                if existing:
                    continue

                # Determine heater type based on series
                if series_name in [
                    RheemProductSeries.CLASSIC,
                    RheemProductSeries.CLASSIC_PLUS,
                    RheemProductSeries.PRESTIGE,
                    RheemProductSeries.PROFESSIONAL,
                ]:
                    heater_type = WaterHeaterType.TANK
                elif series_name in [
                    RheemProductSeries.PERFORMANCE,
                    RheemProductSeries.PERFORMANCE_PLATINUM,
                ]:
                    heater_type = WaterHeaterType.TANKLESS
                else:  # PROTERRA
                    heater_type = WaterHeaterType.HYBRID

                # Get the series features
                features = SERIES_FEATURES.get(series_name, {})

                # Create series record
                series = RheemWaterHeaterSeries(
                    manufacturer="Rheem",
                    name=series_name.value,
                    description=f"Rheem {series_name.value} Series",
                    type=heater_type,
                    tier=self._determine_tier(series_name),
                    features={
                        "uef_rating_range": self._get_uef_range(series_name),
                        "eco_net_enabled": features.get("eco_net_enabled", False),
                        "leak_guard": features.get("leak_guard", False),
                        "warranty_years": features.get("warranty_years", 6),
                        "energy_star_certified": features.get(
                            "energy_star_certified", False
                        ),
                        "operation_modes": self._get_operation_modes(heater_type),
                    },
                    eco_net_enabled=features.get("eco_net_enabled", False),
                    energy_star_certified=features.get("energy_star_certified", False),
                    leak_guard=features.get("leak_guard", False),
                    warranty_years=features.get("warranty_years", 6),
                )
                session.add(series)

            # Commit series to get IDs
            session.commit()

            # Add product models
            self._add_product_models(session)

            session.commit()
            self.logger.info("Rheem product catalog populated successfully")

    def _determine_tier(self, series_name):
        """Determine the tier level based on series name."""
        tier_mapping = {
            RheemProductSeries.CLASSIC: "entry",
            RheemProductSeries.CLASSIC_PLUS: "mid",
            RheemProductSeries.PRESTIGE: "premium",
            RheemProductSeries.PROFESSIONAL: "professional",
            RheemProductSeries.PERFORMANCE: "entry",
            RheemProductSeries.PERFORMANCE_PLATINUM: "premium",
            RheemProductSeries.PROTERRA: "premium",
        }
        return tier_mapping.get(series_name, "standard")

    def _get_uef_range(self, series_name):
        """Get the UEF rating range for a given series."""
        if series_name == RheemProductSeries.PROTERRA:
            return {"min": 3.5, "max": 4.0}
        elif series_name in [
            RheemProductSeries.PERFORMANCE_PLATINUM,
            RheemProductSeries.PROFESSIONAL,
        ]:
            return {"min": 0.93, "max": 0.96}
        elif series_name in [
            RheemProductSeries.PERFORMANCE,
            RheemProductSeries.PRESTIGE,
        ]:
            return {"min": 0.82, "max": 0.92}
        else:
            return {"min": 0.60, "max": 0.82}

    def _get_operation_modes(self, heater_type):
        """Get the supported operation modes based on heater type."""
        if heater_type == WaterHeaterType.HYBRID:
            return [
                RheemWaterHeaterMode.ENERGY_SAVER.value,
                RheemWaterHeaterMode.HEAT_PUMP.value,
                RheemWaterHeaterMode.ELECTRIC.value,
                RheemWaterHeaterMode.HIGH_DEMAND.value,
                RheemWaterHeaterMode.VACATION.value,
            ]
        else:
            return [
                RheemWaterHeaterMode.ENERGY_SAVER.value,
                RheemWaterHeaterMode.HIGH_DEMAND.value,
                RheemWaterHeaterMode.VACATION.value,
            ]

    def _add_product_models(self, session):
        """Add Rheem product models to the database."""
        # Process tank models
        self._add_models_for_type(session, RHEEM_TANK_MODELS, WaterHeaterType.TANK)

        # Process tankless models
        self._add_models_for_type(
            session, RHEEM_TANKLESS_MODELS, WaterHeaterType.TANKLESS
        )

        # Process hybrid models
        self._add_models_for_type(session, RHEEM_HYBRID_MODELS, WaterHeaterType.HYBRID)

    def _add_models_for_type(self, session, model_dict, heater_type):
        """Add models for a specific heater type."""
        for series_name, models in model_dict.items():
            # Get the series record
            series = session.execute(
                select(RheemWaterHeaterSeries).where(
                    RheemWaterHeaterSeries.name == series_name.value
                )
            ).scalar_one_or_none()

            if not series:
                self.logger.warning(
                    f"Series {series_name.value} not found, skipping models"
                )
                continue

            # Add each model
            for model_number in models:
                # Skip if model already exists
                existing = session.execute(
                    select(RheemWaterHeaterModel).where(
                        RheemWaterHeaterModel.model_number == model_number
                    )
                ).first()

                if existing:
                    continue

                # Create model with appropriate specifications
                name = f"Rheem {series_name.value} {model_number}"
                capacity = (
                    self._extract_capacity(model_number)
                    if heater_type != WaterHeaterType.TANKLESS
                    else None
                )

                # Set features based on series and model number
                features = SERIES_FEATURES.get(series_name, {})

                model = RheemWaterHeaterModel(
                    series_id=series.id,
                    model_number=model_number,
                    name=name,
                    capacity=capacity,
                    energy_star_certified=features.get("energy_star_certified", False),
                    smart_features=features.get("eco_net_enabled", False),
                    eco_net_compatible=features.get("eco_net_enabled", False),
                    wifi_module_included=features.get("eco_net_enabled", False),
                    leak_detection=features.get("leak_guard", False),
                    heating_elements=2
                    if heater_type != WaterHeaterType.TANKLESS
                    else None,
                    max_temperature=80.0
                    if heater_type != WaterHeaterType.TANKLESS
                    else 60.0,
                    first_hour_rating=self._calculate_first_hour_rating(capacity)
                    if capacity
                    else None,
                    recovery_rate=self._calculate_recovery_rate(model_number)
                    if heater_type != WaterHeaterType.TANKLESS
                    else None,
                    uef_rating=self._calculate_uef_rating(series_name, model_number),
                    warranty_info={
                        "tank": features.get("warranty_years", 6),
                        "parts": max(3, features.get("warranty_years", 6) - 5),
                        "labor": 1,
                    },
                    specifications=self._generate_model_specifications(
                        model_number, heater_type
                    ),
                )
                session.add(model)

    def _extract_capacity(self, model_number):
        """Extract the capacity from the model number if possible."""
        try:
            # Look for numeric parts that might be capacity
            parts = [p for p in model_number.split() if any(c.isdigit() for c in p)]
            for part in parts:
                digits = "".join([c for c in part if c.isdigit()])
                if digits and 30 <= int(digits) <= 100:
                    return int(digits)

            # Check if model number has embedded numbers
            digits = "".join([c for c in model_number if c.isdigit()])
            if len(digits) >= 2:
                # Get first 2 digits as capacity if they're in a reasonable range
                potential_capacity = int(digits[:2])
                if 30 <= potential_capacity <= 80:
                    return potential_capacity

            # Default capacities based on common sizes
            return 50  # Most common default size
        except:
            return 50  # Fallback

    def _calculate_first_hour_rating(self, capacity):
        """Calculate first hour rating based on capacity."""
        if not capacity:
            return None
        # First hour rating is typically higher than capacity
        return capacity * 1.2

    def _calculate_recovery_rate(self, model_number):
        """Calculate recovery rate based on model info."""
        # Recovery rate measures how many gallons per hour the unit can heat
        # Higher-end models typically have better recovery rates
        if "XE" in model_number:
            return 16.0
        elif "XG" in model_number:
            return 21.0
        elif "PROF" in model_number or "PROT" in model_number:
            return 25.0
        else:
            return 20.0

    def _calculate_uef_rating(self, series_name, model_number):
        """Calculate Uniform Energy Factor rating based on series and model."""
        # Different series and types have different UEF ranges
        base_ranges = {
            RheemProductSeries.CLASSIC: (0.58, 0.64),
            RheemProductSeries.CLASSIC_PLUS: (0.64, 0.75),
            RheemProductSeries.PRESTIGE: (0.75, 0.85),
            RheemProductSeries.PROFESSIONAL: (0.82, 0.92),
            RheemProductSeries.PERFORMANCE: (0.82, 0.87),
            RheemProductSeries.PERFORMANCE_PLATINUM: (0.92, 0.96),
            RheemProductSeries.PROTERRA: (3.75, 4.0),
        }

        range_min, range_max = base_ranges.get(series_name, (0.6, 0.8))

        # Adjust based on model number indicators
        if "PRO" in model_number:
            # Professional models are on the higher end
            return range_min + ((range_max - range_min) * 0.8)
        elif "PLAT" in model_number or "350" in model_number:
            # Platinum or high-end model indicators
            return range_max
        else:
            # Standard model
            return range_min + ((range_max - range_min) * 0.5)

    def _generate_model_specifications(self, model_number, heater_type):
        """Generate detailed specifications for a model."""
        if heater_type == WaterHeaterType.TANKLESS:
            return {
                "flow_rate_gpm": 5.5 if "95" in model_number else 8.4,
                "voltage": 240,
                "weight_lbs": 82,
                "dimensions": "27.5 x 18.5 x 10.0 inches",
                "btu_input": 199000,
                "min_activation_flow": 0.4,
            }
        elif heater_type == WaterHeaterType.HYBRID:
            return {
                "height_inches": 74.0,
                "diameter_inches": 24.5,
                "weight_lbs": 268,
                "voltage": 240,
                "wattage": 4500,
                "noise_level_db": 49,
                "compressor_type": "Scroll",
            }
        else:  # TANK
            capacity = self._extract_capacity(model_number)
            return {
                "height_inches": 46.0
                + (capacity / 50.0 * 10),  # Estimate height based on capacity
                "diameter_inches": 20.0
                + (capacity / 50.0 * 4),  # Estimate diameter based on capacity
                "weight_lbs": 120
                + (capacity * 1.5),  # Estimate weight based on capacity
                "voltage": 240,
                "wattage": 4500,
                "tank_material": "Glass-lined steel",
                "insulation": "Polyurethane foam",
            }

    def migrate_existing_water_heaters(self):
        """Migrate existing water heater data to the Rheem schema."""
        self.logger.info("Migrating existing water heater data to Rheem schema")

        with Session(self.engine) as session:
            # Get all existing water heater models
            existing_models = session.execute(select(WaterHeaterModel)).scalars().all()

            if not existing_models:
                self.logger.info("No existing water heater models found")
                return

            # Process each existing model
            for old_model in existing_models:
                # Map the old model to a Rheem series based on type
                rheem_series = self._map_to_rheem_series(old_model)

                # Get the Rheem series record
                series = session.execute(
                    select(RheemWaterHeaterSeries).where(
                        RheemWaterHeaterSeries.name == rheem_series.value
                    )
                ).scalar_one_or_none()

                if not series:
                    self.logger.warning(
                        f"Rheem series {rheem_series.value} not found, skipping migration for {old_model.model_number}"
                    )
                    continue

                # Get corresponding Rheem model or create a new one
                rheem_model = self._get_or_create_rheem_model(
                    session, old_model, series
                )

                # Process telemetry data
                self._migrate_telemetry_data(session, old_model, rheem_model)

            session.commit()
            self.logger.info("Migration of existing water heater data completed")

    def _map_to_rheem_series(self, old_model):
        """Map an existing water heater model to a Rheem series."""
        # Default mapping based on type
        if hasattr(old_model, "type"):
            if old_model.type == WaterHeaterType.TANKLESS:
                return RheemProductSeries.PERFORMANCE
            elif "hybrid" in (old_model.name or "").lower():
                return RheemProductSeries.PROTERRA

        # Default to Classic for most tank models
        return RheemProductSeries.CLASSIC

    def _get_or_create_rheem_model(self, session, old_model, series):
        """Get or create a Rheem model that corresponds to the old model."""
        # Check if we already have a mapping
        existing = session.execute(
            select(RheemWaterHeaterModel).where(
                RheemWaterHeaterModel.name.like(f"%{old_model.name}%")
            )
        ).scalar_one_or_none()

        if existing:
            return existing

        # Choose a Rheem model number based on series and type
        if series.type == WaterHeaterType.TANKLESS:
            model_number = RHEEM_TANKLESS_MODELS[RheemProductSeries.PERFORMANCE][0]
        elif series.type == WaterHeaterType.HYBRID:
            model_number = RHEEM_HYBRID_MODELS[RheemProductSeries.PROTERRA][0]
        else:  # TANK
            model_number = RHEEM_TANK_MODELS[RheemProductSeries.CLASSIC][0]

        # Create a new Rheem model based on the old one
        features = SERIES_FEATURES.get(RheemProductSeries(series.name), {})

        capacity = None
        if hasattr(old_model, "capacity"):
            capacity = old_model.capacity
        else:
            # Extract capacity from name if possible
            capacity = self._extract_capacity_from_text(old_model.name)

        rheem_model = RheemWaterHeaterModel(
            series_id=series.id,
            model_number=model_number,
            name=f"Rheem {series.name} {old_model.name}",
            capacity=capacity,
            energy_star_certified=features.get("energy_star_certified", False),
            smart_features=features.get("eco_net_enabled", False),
            eco_net_compatible=features.get("eco_net_enabled", False),
            wifi_module_included=features.get("eco_net_enabled", False),
            leak_detection=features.get("leak_guard", False),
            heating_elements=2 if series.type != WaterHeaterType.TANKLESS else None,
            max_temperature=80.0 if series.type != WaterHeaterType.TANKLESS else 60.0,
            first_hour_rating=self._calculate_first_hour_rating(capacity),
            uef_rating=self._calculate_uef_rating(
                RheemProductSeries(series.name), model_number
            ),
            warranty_info={
                "tank": features.get("warranty_years", 6),
                "parts": max(3, features.get("warranty_years", 6) - 5),
                "labor": 1,
            },
            specifications=self._generate_model_specifications(
                model_number, series.type
            ),
        )

        session.add(rheem_model)
        session.flush()

        return rheem_model

    def _extract_capacity_from_text(self, text):
        """Extract a capacity value from text."""
        try:
            # Look for patterns like "50 gallon" or "50G"
            import re

            matches = re.findall(r"(\d+)\s*(?:gal|g|gallons?)", text.lower())
            if matches:
                return int(matches[0])

            # If no pattern matched, just look for numbers between 30 and 100
            numbers = re.findall(r"\d+", text)
            for num in numbers:
                if 30 <= int(num) <= 100:
                    return int(num)

            # Default capacity
            return 50
        except:
            return 50

    def _migrate_model_telemetry_data(self, session, old_model, rheem_model):
        """Migrate telemetry data from old model to Rheem model."""
        # Get the old telemetry data
        old_telemetry = (
            session.execute(
                select(WaterHeaterTelemetry).where(
                    WaterHeaterTelemetry.model_id == old_model.id
                )
            )
            .scalars()
            .all()
        )

        if not old_telemetry:
            self.logger.info(f"No telemetry data found for model {old_model.name}")
            return

        # Process each telemetry record
        for record in old_telemetry:
            # Create new Rheem telemetry record with enhanced fields
            rheem_telemetry = RheemWaterHeaterTelemetry(
                device_id=record.device_id,
                model_id=rheem_model.id,
                timestamp=record.timestamp,
                temperature=record.temperature,
                set_point=record.set_point,
                heating_active=record.heating_active,
                flow_rate=record.flow_rate,
                inlet_temp=record.inlet_temp if hasattr(record, "inlet_temp") else None,
                outlet_temp=record.outlet_temp
                if hasattr(record, "outlet_temp")
                else None,
                power_consumption=record.power_consumption
                if hasattr(record, "power_consumption")
                else None,
                mode=record.mode if hasattr(record, "mode") else None,
                # New Rheem-specific fields
                ambient_temp=22.0,  # Default room temperature
                humidity=45.0,  # Default humidity
                compressor_active=False,
                heating_element_active=record.heating_active,
                wifi_signal_strength=None,
                eco_net_connected=False,
                error_codes=record.error_codes
                if hasattr(record, "error_codes")
                else None,
                power_source="ELECTRIC",
                energy_usage_day=None,
                total_energy_used=None,
                operating_cost=None,
                estimated_savings=None,
            )

            session.add(rheem_telemetry)

    def migrate_telemetry_data(self):
        """Migrate all telemetry data from existing water heaters to Rheem models.

        This method provides a public interface for telemetry migration that can be called
        independently from migrate_existing_water_heaters.
        """
        self.logger.info("Migrating water heater telemetry data to Rheem schema")

        with Session(self.engine) as session:
            # Get all existing water heater models
            existing_models = session.execute(select(WaterHeaterModel)).scalars().all()

            if not existing_models:
                self.logger.info("No existing water heater models found")
                return True

            # Get all Rheem models
            rheem_models = (
                session.execute(select(RheemWaterHeaterModel)).scalars().all()
            )

            if not rheem_models:
                self.logger.warning("No Rheem water heater models found")
                return False

            # Process each existing model
            for old_model in existing_models:
                # Find a matching Rheem model
                matching_model = None
                for rheem_model in rheem_models:
                    if old_model.name in rheem_model.name:
                        matching_model = rheem_model
                        break

                if not matching_model:
                    self.logger.warning(
                        f"No matching Rheem model found for {old_model.name}"
                    )
                    continue

                # Migrate telemetry data
                self._migrate_model_telemetry_data(session, old_model, matching_model)

            session.commit()
            self.logger.info("Telemetry data migration completed successfully")
            return True

    def run_full_migration(self):
        """Run the complete migration process.

        This is the main method to execute the full migration process that includes:
        1. Creating the Rheem database schema
        2. Populating the product catalog
        3. Migrating existing water heaters to Rheem models
        4. Migrating telemetry data

        Returns:
            bool: True if migration was successful, False otherwise
        """
        self.logger.info("Beginning Rheem water heater migration")

        try:
            # Create the schema
            self.create_rheem_schema()

            # Populate product catalog
            self.populate_rheem_product_catalog()

            # Migrate existing data
            self.migrate_existing_water_heaters()

            # Migrate telemetry data
            self.migrate_telemetry_data()

            self.logger.info("Rheem water heater migration completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Migration failed: {str(e)}")
            return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the migration
    migration_tool = RheemMigrationTool()
    success = migration_tool.run_full_migration()

    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed. Check logs for details.")
        exit(1)
