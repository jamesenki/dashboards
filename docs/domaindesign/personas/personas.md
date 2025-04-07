# IoTSphere Personas

This document defines the key personas that interact with the IoTSphere platform. These personas inform our domain model and help prioritize features and behaviors.

## Primary Personas

### Facility Manager / Property Owner
- **Identifier:** `FACILITY_MANAGER`
- **Description:** Responsible for overall management of properties with installed IoT devices.
- **Goals:**
  - Maximize operational efficiency of managed devices
  - Minimize downtime and service interruptions
  - Optimize total cost of ownership
  - Effectively schedule and prioritize maintenance
- **Pain Points:**
  - Unexpected device failures
  - Inefficient maintenance scheduling
  - Lack of visibility into device performance
  - High energy/operational costs
- **Key Activities:**
  - Monitoring device health dashboards
  - Reviewing maintenance schedules
  - Analyzing performance trends
  - Making resource allocation decisions
- **Key Decisions:**
  - When to schedule maintenance
  - When to replace vs. repair equipment
  - How to optimize operational settings
  - How to allocate maintenance resources

### Service Technician
- **Identifier:** `SERVICE_TECHNICIAN`
- **Description:** Professional who installs, maintains, and repairs IoT devices.
- **Goals:**
  - Efficiently diagnose and resolve issues
  - Complete maintenance tasks effectively
  - Maintain device performance and longevity
  - Minimize repeat service calls
- **Pain Points:**
  - Insufficient diagnostic information
  - Incomplete maintenance history
  - Difficulty accessing technical specifications
  - Challenges in remote troubleshooting
- **Key Activities:**
  - Performing installation and maintenance
  - Troubleshooting reported issues
  - Replacing components and parts
  - Updating device firmware/settings
- **Key Decisions:**
  - Which components to repair or replace
  - Priority of service calls
  - When to escalate issues
  - Which tools and parts to bring to service calls

### End User / Resident
- **Identifier:** `END_USER`
- **Description:** Person who directly uses the services provided by IoT devices.
- **Goals:**
  - Reliable service (e.g., hot water, climate control)
  - Easy control of device settings
  - Energy and cost efficiency
  - Minimal interaction with technical aspects
- **Pain Points:**
  - Service disruptions
  - Complicated interfaces
  - Unexpected changes in performance
  - High utility bills
- **Key Activities:**
  - Adjusting comfort settings (temperature, etc.)
  - Reporting issues when service is disrupted
  - Monitoring basic device status
  - Scheduling operations (when applicable)
- **Key Decisions:**
  - Temperature and comfort settings
  - Operation modes (eco, standard, etc.)
  - When to report issues to property management

### System Administrator
- **Identifier:** `SYSTEM_ADMIN`
- **Description:** Technical personnel responsible for managing the IoTSphere platform.
- **Goals:**
  - Maintain system availability and performance
  - Ensure data security and integrity
  - Support user access needs
  - Facilitate integrations with other systems
- **Pain Points:**
  - System downtime
  - Security vulnerabilities
  - Complex integration requirements
  - Data management challenges
- **Key Activities:**
  - Configuring system settings
  - Managing user accounts and permissions
  - Monitoring system performance
  - Troubleshooting platform issues
- **Key Decisions:**
  - Access control policies
  - System configuration settings
  - Integration approaches
  - Data retention policies

## Secondary Personas

### Energy Manager
- **Identifier:** `ENERGY_MANAGER`
- **Description:** Professional focused on energy efficiency across facilities.
- **Goals:**
  - Reduce energy consumption
  - Identify optimization opportunities
  - Ensure compliance with efficiency standards
  - Document energy savings
- **Key Activities:**
  - Analyzing consumption patterns
  - Implementing energy-saving measures
  - Reporting on efficiency metrics

### Equipment Manufacturer
- **Identifier:** `MANUFACTURER`
- **Description:** Company that produces IoT devices and wants insights on field performance.
- **Goals:**
  - Monitor product performance
  - Manage warranty claims
  - Identify design improvements
  - Support customer satisfaction
- **Key Activities:**
  - Analyzing performance metrics
  - Tracking failure patterns
  - Managing product lifecycle

### Building Management System Integrator
- **Identifier:** `BMS_INTEGRATOR`
- **Description:** Professional who integrates IoTSphere with broader building systems.
- **Goals:**
  - Seamless integration between systems
  - Unified monitoring and control
  - Reliable data exchange
  - Simplified management interfaces
- **Key Activities:**
  - Configuring API integrations
  - Setting up data flows
  - Creating unified dashboards
  - Testing system interoperability
