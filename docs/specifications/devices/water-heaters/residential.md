# Residential Water Heater Specifications

## Overview

Residential water heaters are designed for home use, providing efficient hot water delivery for household needs such as bathing, washing, and cooking. These units are optimized for lower capacity needs while maintaining energy efficiency, quiet operation, and ease of installation in residential settings.

## Models

| Model Name | Capacity (Liters) | Power (kW) | Recovery Rate (L/hr) | Recommended Applications |
|------------|------------------|------------|---------------------|--------------------------|
| SmartTemp Home-50 | 50 | 3 | 40 | Small Apartments, Single Bathrooms |
| EcoHeat Family-80 | 80 | 4.5 | 60 | Small Homes, 1-2 Bathrooms |
| AquaWarm Comfort-100 | 100 | 6 | 80 | Medium Homes, 2-3 Bathrooms |
| ThermoGuard Premium-150 | 150 | 7.5 | 100 | Large Homes, 3+ Bathrooms |

## Bill of Materials (BOM)

### Core Components

| Component | Description | Supplier | Part Number | Notes |
|-----------|-------------|----------|------------|-------|
| Tank | Glass-Lined Steel Tank | Johnson Thermal | JT-GL-TANK-R | Corrosion resistant |
| Heating Element | Residential Electric Element | HeatCorp | HC-EL-6KW | Energy efficient |
| Control Board | Smart Home Control System | TechControl | TC-WH-RES-01 | WiFi-enabled |
| Temperature Sensor | Digital Temperature Sensor | SensorTech | ST-DTS-100 | ±0.5°C accuracy |
| Pressure Sensor | Analog Pressure Sensor | FlowMaster | FM-APS-200 | 0-6 bar range |
| Flow Switch | Paddle Flow Switch | FlowMaster | FM-PFS-R15 | Simple, reliable design |
| Relay | Residential Power Relay | PowerSwitch | PS-RPR-30A | Standard capacity |
| Safety Valve | TP Relief Valve | SafeFlow | SF-TPR-RES | Residential rated |
| Display Module | 2.4" LCD Display | DisplayTech | DT-24-LCD | Energy efficient |
| WiFi Module | Home Wireless Module | ConnectPro | CP-HWM-2G | Standard range |
| Anode Rod | Magnesium Anode Rod | CorrosionStop | CS-MAG-RES-M | Standard protection |

### Case and Fittings

| Component | Description | Supplier | Part Number | Notes |
|-----------|-------------|----------|------------|-------|
| Outer Casing | Painted Steel | MetalWorks | MW-PS-CASE-R | Residential finish |
| Insulation | Polyurethane Foam | ThermoGuard | TG-PUF-R35 | Energy efficient |
| Water Inlet | 3/4" NPT Brass Fitting | PlumbParts | PP-NPT-0.75-BR | Standard residential |
| Water Outlet | 3/4" NPT Brass Fitting | PlumbParts | PP-NPT-0.75-BR | Standard residential |
| Drain Valve | 1/2" Brass Valve | ValveTech | VT-STD-0.5-BR | Basic maintenance |
| Mounting Brackets | Wall Mounting Kit | SupportSys | SS-WMK-R | Residential use |

## Software BOM

| Component | Version | License | Purpose | Source |
|-----------|---------|---------|---------|--------|
| Control Firmware | 2.8.4 | Proprietary | Core functionality | Internal |
| Diagnostic Suite | 1.5.0 | Proprietary | Error detection | Internal |
| IoTSphere Client | 1.8.3 | MIT | Cloud connectivity | IoTSphere |
| HomeTemp | 3.1.0 | Proprietary | Temperature management | ThermoTech Inc |
| EcoMode | 2.4.2 | Proprietary | Energy saving features | EcoSystems |
| HomeConnect | 3.5.0 | Proprietary | Smart home integration | ConnectPro |
| SecurityLite | 2.0.3 | Proprietary | Basic security | SecureTech |
| OTAManager | 1.4.0 | MIT | Remote updates | IoTSphere |
| ErrorReport | 1.3.1 | Proprietary | Basic diagnostics | Internal |
| SimpleLogger | 2.1.0 | Apache 2.0 | Basic monitoring | OpenDataSys |

## Technical Specifications

| Specification | Value |
|---------------|-------|
| Voltage | 220V-240V, Single-Phase |
| Operating Pressure | 1-6 bar |
| Maximum Temperature | 75°C |
| Typical Efficiency | 85-93% |
| Recovery Rate | 40-100 L/hr |
| Connectivity | WiFi, Bluetooth |
| Data Protocol | MQTT, HTTP/REST |
| Data Encryption | TLS 1.2 |
| Data Reporting Frequency | Configurable (30s to 60min) |
| Update Method | OTA (Over-the-Air) |
| Operating Environment | 5°C to 40°C, up to 80% RH |
| Certification | UL, CE, Energy Star |
| Warranty | 2 years (parts), 1 year (labor) |

## Diagnostic Codes

| Code | Description | Severity | Recommended Action | Real-time Alert |
|------|-------------|----------|-------------------|----------------|
| R001 | High temperature warning | Warning | Check temperature setting | Yes |
| R002 | Critical high temperature | Critical | Shutdown recommended | Yes |
| R003 | Low pressure warning | Warning | Check water supply | No |
| R004 | High pressure warning | Warning | Check expansion tank | Yes |
| R005 | Critical high pressure | Critical | Call service technician | Yes |
| R006 | Control system error | Warning | Restart system | No |
| R007 | Temperature sensor error | Critical | Service required | Yes |
| R008 | Pressure sensor error | Warning | Service recommended | No |
| R009 | Water leak detected | Critical | Shut off water supply | Yes |
| R010 | Heating element failure | Critical | Service required | Yes |
| R011 | WiFi connection lost | Info | Check router | No |
| R012 | Scale buildup detected | Maintenance | Descale recommended | No |
| R013 | Anode rod depletion | Maintenance | Replacement needed | No |
| R014 | Efficiency reduced | Warning | Check for scale buildup | No |
| R015 | Unusual usage pattern | Info | Check for leaks | No |
| R016 | Vacation mode active | Info | Normal operation | No |
| R017 | Power outage recovery | Info | Normal operation | No |
| R018 | Multiple heating cycles | Warning | Check for water draw issues | No |
| R019 | Long recovery time | Warning | Check element functionality | No |
| R020 | Energy usage high | Warning | Check insulation and settings | No |

## Troubleshooting Instructions

### Temperature Issues (R001, R002)
1. Check temperature setting on control panel
2. Verify hot water usage patterns
3. Check for proper insulation
4. Reset system if temperature remains high
5. Call service if problem persists

### Pressure Issues (R003, R004, R005)
1. Check home water pressure
2. Inspect expansion tank
3. Verify pressure relief valve operation
4. Check for closed valves or blockages
5. Call service for pressure relief valve replacement if needed

### Sensor Problems (R007, R008)
1. Try resetting the system
2. Check for loose connections
3. Test water temperature manually to compare
4. Check for error code details
5. Contact service for sensor replacement

### Heating Element Issues (R010)
1. Reset the circuit breaker
2. Check for error codes on display
3. Verify power is reaching the unit
4. Check water supply
5. Contact service for element replacement

### Water Leaks (R009)
1. Shut off water immediately
2. Check connections and fittings
3. Look for corrosion or cracks
4. Dry the area and monitor
5. Contact service if leak continues

### Efficiency Issues (R012, R014, R020)
1. Check for scale buildup
2. Inspect insulation quality
3. Verify temperature settings aren't too high
4. Consider a system flush
5. Schedule regular maintenance

### Connectivity Issues (R011)
1. Check router operation
2. Verify WiFi password hasn't changed
3. Restart router and water heater
4. Check for interference
5. Re-pair device with app if necessary

## Maintenance Schedule

| Maintenance Task | Frequency | Skill Level | Average Time |
|------------------|-----------|-------------|--------------|
| Temperature setting check | Monthly | Homeowner | 5 minutes |
| Pressure relief valve test | Quarterly | Homeowner | 10 minutes |
| Anode rod inspection | Annually | DIY/Technician | 30 minutes |
| Sediment flushing | Annually | DIY/Technician | 30 minutes |
| Element inspection | Annually | Technician | 30 minutes |
| Full system inspection | Biennially | Technician | 1 hour |
| Tank replacement | 8-12 years | Technician | 2-3 hours |

## Real-time Monitoring Parameters

| Parameter | Normal Range | Sampling Rate | Alert Threshold |
|-----------|--------------|--------------|----------------|
| Water Temperature | 50-75°C | 30 seconds | ±5°C from setpoint |
| System Pressure | 1-6 bar | 60 seconds | <1 bar, >6 bar |
| Energy Usage | Model dependent | 5 minutes | >20% above average |
| Heating Cycles | 3-8 daily | Event based | >12 cycles in 24h |
| Hot Water Availability | 80-100% | Calculated hourly | <50% of capacity |
| Leak Detection | No leak | Continuous | Any detected moisture |
| WiFi Signal Strength | >-70dBm | 5 minutes | <-80dBm |

## API Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/devices/{id}/temperature` | GET | Current temperature | N/A |
| `/api/devices/{id}/status` | GET | Operational status | N/A |
| `/api/devices/{id}/energy` | GET | Energy consumption | period=[day,week,month] |
| `/api/devices/{id}/diagnostics` | GET | Active diagnostic codes | N/A |
| `/api/devices/{id}/settings` | GET/PUT | Device settings | temperature, mode |
| `/api/devices/{id}/maintenance` | GET | Maintenance status | N/A |
| `/api/devices/{id}/usage-pattern` | GET | Hot water usage pattern | period=[day,week] |
| `/api/devices/{id}/schedule` | GET/PUT | Heating schedule | N/A |
