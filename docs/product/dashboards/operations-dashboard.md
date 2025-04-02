# Operations Dashboard Documentation

## Overview

The Operations Dashboard for IoTSphere's Polar Delight vending machines provides two complementary views:

1. **Remote Operations Cockpit**: Real-time operational monitoring with status cards, gauges, and inventory tracking
2. **Operations Summary**: Historical analytics with sales data, usage patterns, and maintenance records

This dual approach provides both immediate operational status and long-term performance insights.

## Architecture

### Backend Components

#### Models

1. **Real-time Operations Models** (`src/models/vending_machine_realtime_operations.py`):
   - `VendingMachineOperationsData`: Main container for real-time operational data
   - `AssetHealthData`: Asset health gauge metrics
   - `FreezerTemperatureData`: Freezer temperature measurements
   - `DispensePressureData`: Dispense force/pressure metrics
   - `CycleTimeData`: Machine cycle time metrics
   - `RamLoadData`: RAM load status and thresholds
   - `FlavorInventory`: Inventory tracking for flavors

2. **Analytics Operations Models** (`src/models/vending_machine_operations.py`):
   - `OperationsSummary`: Container for all analytics data
   - `SalesData`: Sales performance metrics
   - `UsagePattern`: Usage analytics by time/day
   - `MaintenanceHistory`: Maintenance event records
   - `RefillHistory`: Product refill tracking
   - `TemperatureTrends`: Temperature monitoring over time

#### Services

1. **Real-time Operations Service** (`src/services/vending_machine_realtime_operations_service.py`):
   - `get_operations_data()`: Retrieves real-time operational metrics
   - Internal helper methods for gauge calculations and inventory generation

2. **Analytics Operations Service** (`src/services/vending_machine_operations_service.py`):
   - `get_operations_summary()`: Retrieves comprehensive analytics data
   - Specialized methods for individual analytics categories

#### API Endpoints

1. **Real-time Operations API** (`src/api/vending_machine_realtime_operations.py`):
   - `GET /api/vending-machines/{machine_id}/operations-realtime`: Real-time operational data

2. **Analytics Operations API** (`src/api/vending_machine_operations.py`):
   - `GET /api/vending-machines/{machine_id}/operations`: Full analytics summary
   - Additional endpoints for individual analytics categories

### Frontend Components

#### JavaScript API Client

The frontend API client (`frontend/static/js/api.js`) includes:
- `getVendingMachineRealtimeOperations(id)`: Fetches real-time operational data
- `getVendingMachineOperationsAnalytics(id)`: Fetches historical analytics data

#### Template & UI

The vending machine detail template (`frontend/templates/vending-machine/detail.html`) includes:
- Tab navigation for switching between operations views
- Dynamic data loading based on active tab
- Specialized rendering functions for each operations view

#### CSS & Styling

Operations-specific styling (`frontend/static/css/operations-dashboard.css`):
- Status indicator styles
- Gauge component styles
- Inventory bar visualizations
- Analytics charts and tables

#### Dashboard Interactivity

Dashboard JavaScript (`frontend/static/js/operations-dashboard.js`):
- Gauge initialization and animation
- Inventory bar visualization
- Status indicator enhancements
- Auto-refresh for real-time data

## Using the Operations Dashboard

### Access

The Operations Dashboard is accessible via the tabs in the vending machine detail view:
1. Navigate to a vending machine detail page
2. Select either "Remote Operations Cockpit" or "Operations Summary" tab

### Remote Operations Cockpit

The Remote Operations Cockpit provides real-time operational status including:

1. **Current Status Indicators**:
   - Machine Status (Online/Offline)
   - POD Code 
   - Cup Detection status
   - Door status (POD bin and customer)

2. **Performance Metric Gauges**:
   - Asset Health (overall health percentage)
   - Freezer Temperature (current temperature with thresholds)
   - Dispense Force (current mechanical force measurement)
   - Cycle Time (current operational cycle duration)

3. **RAM Load Panel**:
   - Current RAM load measurement with status indicator

4. **Inventory Tracking**:
   - Flavor-by-flavor inventory levels with visual bars

The dashboard automatically refreshes data every 30 seconds while the tab is active.

### Operations Summary

The Operations Summary provides long-term analytics and historical data:

1. **Sales Performance**:
   - Daily, weekly, and monthly sales figures
   - Revenue trends and product popularity

2. **Usage Patterns**:
   - Time-of-day usage distribution
   - Day-of-week popularity analysis

3. **Maintenance Records**:
   - Past maintenance events with details
   - Maintenance performance metrics

4. **Temperature Trends**:
   - Historical temperature measurements
   - Anomaly detection for temperature fluctuations

## Technical Implementation

### Data Flow

1. **Real-time Operations**:
   - Frontend requests data via API client
   - Backend service queries current machine state
   - Service generates real-time operational metrics
   - Data is returned to frontend for visualization
   - Dashboard initializes gauges and status indicators
   - Auto-refresh maintains data currency

2. **Analytics Operations**:
   - Frontend requests analytics data via API client
   - Backend service retrieves historical data
   - Service computes analytics and performance metrics
   - Data is returned to frontend for visualization
   - Charts and tables display historical trends

### Testing

1. **Unit Tests**:
   - Model tests verify data structures
   - Service tests confirm metric generation
   - API tests validate endpoint responses

2. **E2E Tests**:
   - Frontend tests verify proper tab switching
   - Tests confirm proper display of both operations views
   - Tests validate interactive dashboard elements

## Future Enhancements

Potential future enhancements for the Operations Dashboard include:

1. **Real-time Operations**:
   - Live video feed integration
   - Remote control capabilities for maintenance
   - Predictive maintenance alerts
   - Real-time data streaming via WebSockets

2. **Analytics Operations**:
   - Advanced ML-based trend analysis
   - Comparative performance across machine fleet
   - Exportable reports and visualizations
   - Customizable KPIs and metrics

## Troubleshooting

Common issues and resolutions:

1. **Data Not Loading**:
   - Check network connectivity
   - Verify API endpoint configuration
   - Confirm machine ID is valid

2. **Gauges Not Rendering**:
   - Check browser console for JavaScript errors
   - Verify operations-dashboard.js is loaded
   - Test with alternative browsers

3. **Auto-refresh Not Working**:
   - Verify machine is selected in dropdown
   - Check browser console for interval errors
   - Confirm tab is properly activated
