# Immediate Tasks for Water Heater Demo

This document outlines the immediate tasks required to deliver a compelling water heater demo that demonstrates real business value while aligning with our TDD principles and BDD test requirements.

## Phase 1: Infrastructure Foundation (1-2 weeks)

### 1. Database Setup
- **Set up TimescaleDB** for telemetry storage
  ```bash
  # Example task
  docker-compose up -d timescale-db
  python src/infrastructure/db_migration/create_telemetry_tables.py
  ```
- **Configure Redis** for device shadow/twin
  ```bash
  # Example task
  docker-compose up -d redis
  python src/infrastructure/device_shadow/init_shadow_store.py
  ```
- **Implement asset schema** in PostgreSQL
  ```bash
  # Example task
  python src/infrastructure/db_migration/create_asset_tables.py
  ```

### 2. Water Heater Simulator
- **Develop water heater simulator** implementing realistic behavior
  ```python
  # Example class structure
  class WaterHeaterSimulator:
      def __init__(self, device_id, model, initial_state):
          self.device_id = device_id
          self.model = model
          self.state = initial_state

      def start(self):
          # Begin simulation thread

      def generate_telemetry(self):
          # Create realistic telemetry data

      def handle_command(self, command):
          # Respond to commands like a real device
  ```
- **Create simulation manager** to coordinate multiple simulated devices
- **Implement MQTT connectivity** for simulator-to-platform communication

### 3. Basic Event Pipeline
- **Set up message broker** (RabbitMQ for quicker setup than Kafka)
  ```bash
  docker-compose up -d rabbitmq
  ```
- **Create core event producers/consumers** for device events
- **Implement WebSocket service** for real-time UI updates

## Phase 2: Water Heater Core Features (2-3 weeks)

### 1. Manufacturer-Agnostic API Enhancement
- **Refine existing API** to work with simulated devices
- **Implement telemetry storage** via TimescaleDB
- **Create device shadow service** with MongoDB Change Streams
  - Implement Change Data Capture (CDC) pattern for real-time updates
  - Enable WebSocket notification system for UI updates

### 2. Real-time Operational Dashboard
- **Implement real-time status cards** showing:
  - Current temperature
  - Operating mode
  - Energy usage
  - Heating cycle status
- **Create gauge visualizations** for key metrics
- **Build real-time event display** for operational events

### 3. Basic Analytics Implementation
- **Implement water heater efficiency calculator**
- **Create basic maintenance prediction** for component health
- **Build simple ROI calculator** for maintenance actions

## Phase 3: Demo Preparation (1 week)

### 1. Demo Scenario Development
- **Create demonstration script** highlighting key features
- **Configure realistic device scenarios** showing value
- **Set up demonstration environment** with sample data

### 2. Quality Assurance
- **Verify BDD test compliance** for @current tests
- **Ensure simulation indicators** are clear and functional
- **Test all dashboard components** with simulated data

### 3. Documentation Update
- **Create quick-start guide** for demo setup
- **Document architecture implementation** progress
- **Update BDD test status** with passing scenarios

## Prioritized BDD Tests to Target

Focus on the following @current BDD scenarios for the initial demo:

1. **Manufacturer-Agnostic Water Heater API**
   - "Get water heaters across multiple manufacturers"
   - "Get individual water heater details by ID"
   - "Get operational summary including maintenance predictions"

2. **Predictive Maintenance**
   - "Generate health assessment for a water heater"
   - "View maintenance recommendations for a water heater"

3. **Business Intelligence (start with basics)**
   - "View operational efficiency analytics for water heaters"

## Implementation Approach

To align with TDD principles and deliver a compelling demo:

1. **Start with failing tests** for each priority scenario
2. **Implement minimal infrastructure** to support those tests
3. **Create simulators** that generate realistic data
4. **Build visual components** that demonstrate value
5. **Focus on real-time aspects** for demo impact

This approach will provide:
- A compelling demonstration of water heater monitoring
- A foundation for the broader device-agnostic architecture
- Satisfaction of key @current BDD tests without mocks
- Visible business value through operational insights and maintenance predictions
