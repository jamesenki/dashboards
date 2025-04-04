# Rheem Water Heater Knowledge Base Framework

> **LLM Agent Implementation Note**: This framework is designed for consumption by LLM agents in an Agentic/Multi-agent/RAG implementation. Each section includes structured data with clear categorization for efficient information retrieval and reasoning.

## 1. Introduction
- About Rheem as a company
  - Source: https://www.rheem.com/about/
  - Founded: 1925
  - Parent company: Paloma Industries
  - Manufacturing locations: Montgomery, AL; Fort Smith, AR; Oxnard, CA
- How to use this knowledge base
  - Data schema for LLM agent queries
  - Metadata structure for RAG implementation
- Glossary of water heater terminology
  - Source: https://www.rheem.com/water-heaters-101/
  - API endpoint format: `/glossary/{term}`

## 1.1 Key Capabilities

This knowledge base supports four key capability areas:

* **Predictive Maintenance**: Early detection of potential failures, optimizing maintenance schedules, and forecasting component failures before they occur.
* **Warranty Determination**: Automating claim validation, handling complex conditional coverage situations, and proactively alerting customers before warranty issues arise.
* **Service Technician Instructions**: Generating precise repair procedures tailored to specific models and situations, creating appropriate documentation, and enforcing safety protocols.
* **Reactive Issue Response**: Managing emergency situations, generating clear customer communications, and optimizing technician dispatch based on skills and issue complexity.

## 2. Water Heater Types
### 2.1 Tank Water Heaters
- Residential models
  - Standard models
  - High-efficiency models
  - Marathon series
- Commercial models
  - Standard commercial
  - High-efficiency commercial
  - Heavy-duty models

### 2.2 Tankless Water Heaters
- Residential models
  - Indoor models
  - Outdoor models
  - Condensing vs. non-condensing
- Commercial models
  - Point-of-use
  - Whole building solutions

### 2.3 Heat Pump Water Heaters
- Hybrid Electric models
- Commercial heat pump solutions

### 2.4 Solar Water Heating Systems
- Active systems
- Passive systems
- Solar with backup

## 3. Organization by Fuel Source
### 3.1 Electric Water Heaters
- Standard electric models
- High-efficiency electric models
- Common components and parts
- Wiring diagrams

### 3.2 Gas Water Heaters
- Natural gas models
- Propane-compatible models
- Common components and parts
- Gas control valve types
- Venting requirements

### 3.3 Heat Pump Technology
- How Rheem heat pumps work
- Energy efficiency ratings
- Components specific to heat pumps

### 3.4 Solar-Powered Systems
- Solar collectors
- Storage tanks
- Controllers and pumps
- Backup heating systems

## 4. Installation Guidelines
### 4.1 General Installation Requirements
- Code compliance
- Clearance requirements
- Ventilation requirements
- Plumbing connections
- Electrical requirements

### 4.2 Tank Installation
- Location considerations
- Water connections
- T&P valve installation
- Expansion tanks
- Seismic strapping

### 4.3 Tankless Installation
- Gas line sizing
- Venting options
- Condensate disposal (for condensing models)
- Water filtration requirements
- Recirculation systems

### 4.4 Heat Pump Installation
- Airflow requirements
- Condensate management
- Noise considerations
- Operating temperature ranges

### 4.5 Solar System Installation
- Collector positioning
- Pipe insulation
- Controller setup
- Freeze protection

## 5. Maintenance Procedures
### 5.1 Regular Maintenance Tasks
- Flushing procedures
- Anode rod inspection and replacement
- Element testing and replacement (electric)
- Burner cleaning (gas)
- Temperature and pressure relief valve testing

### 5.2 Model-Specific Maintenance
- Tankless heat exchanger flushing
- Heat pump coil cleaning
- Solar collector maintenance
- Commercial unit maintenance

### 5.3 Seasonal Maintenance
- Winter preparation
- Summer optimization
- Vacation mode settings

### 5.4 Professional vs. DIY Maintenance
- Tasks homeowners can safely perform
- When to call a professional
- Tools needed for common maintenance

## 6. Troubleshooting Guides
### 6.1 No Hot Water Issues
- Electric heater troubleshooting
  - Source: https://www.rheem.com/support/faqs/water-heaters/no-hot-water-electric/
  - Decision tree format for agent reasoning
  - Structured data:
    ```json
    {
      "symptom": "no_hot_water",
      "model_type": "electric",
      "possible_causes": [
        {"cause": "tripped_breaker", "probability": 0.35, "check_procedure": "...", "fix_complexity": "low"},
        {"cause": "failed_element", "probability": 0.28, "check_procedure": "...", "fix_complexity": "medium"},
        {"cause": "thermostat_failure", "probability": 0.22, "check_procedure": "...", "fix_complexity": "medium"}
      ]
    }
    ```
- Gas heater troubleshooting
  - Source: https://www.rheem.com/support/faqs/water-heaters/no-hot-water-gas/
  - Decision tree with safety warnings
  - Image recognition patterns for pilot light issues
- Tankless flow issues
  - Source: https://cdn.globalimageserver.com/FetchDocument.aspx?ID=8a1652fc-d7e9-4724-a14a-abb300fd65b6
  - Flow rate validation algorithm
  - Case-based reasoning patterns for similar symptoms
- Heat pump troubleshooting
  - Source: https://cdn.globalimageserver.com/FetchDocument.aspx?ID=8c9f5ead-fd4d-48ff-85a6-adf4015c0750
  - Environmental condition correlation data
  - Time-series analysis for performance degradation

### 6.2 Water Temperature Problems
- Inconsistent temperature
- Water too hot
- Water not hot enough
- Sudden temperature changes

### 6.3 Leaking Issues
- Finding the source of leaks
- Common leak points
- Emergency shutdown procedures
- When tank replacement is necessary

### 6.4 Noise and Operation Issues
- Popping or rumbling sounds
- Whistling noises
- Abnormal cycling
- Pilot light issues (gas models)

### 6.5 Error Codes and Indicators
- LED/display code reference tables
- Resetting after error codes
- Diagnostic procedures

## 7. Comprehensive Error Code Reference
### 7.1 Tankless Error Codes
- Complete list of error codes by model
- Troubleshooting steps for each code
- Required parts for common repairs

### 7.2 Heat Pump Error Codes
- Complete list of error codes by model
- Troubleshooting steps for each code
- Required parts for common repairs

### 7.3 Smart/Connected Model Error Codes
- EcoNet® error codes
- App-based diagnostics
- Remote troubleshooting capabilities

## 8. Parts and Replacements
### 8.1 Common Replacement Parts
- Heating elements
- Thermostats
- Gas valves
- Ignition systems
- Anode rods
- Pressure relief valves

### 8.2 Model-Specific Parts
- Cross-reference guides
- Part number lookup tables
- Compatible alternative parts

### 8.3 Where to Purchase Parts
- Authorized dealers
- Online resources
- OEM vs. aftermarket options

## 9. Efficiency and Optimization
### 9.1 Improving Water Heater Efficiency
- Insulation options
- Temperature settings
- Recirculation system optimization
- Heat traps and pipe insulation

### 9.2 Energy Usage Monitoring
- Understanding energy consumption
- Smart monitoring tools
- Seasonal efficiency adjustments

### 9.3 Upgrade Considerations
- When to replace vs. repair
- Efficiency upgrade options
- ROI calculations for upgrades

## 10. Special Topics
### 10.1 Commercial Applications
- Large-scale installation considerations
- Commercial maintenance schedules
- High-demand applications

### 10.2 Warranty Information
- Warranty terms by model
- Registration requirements
- How to make warranty claims
- Documentation required for claims

### 10.3 Smart/Connected Features
- EcoNet® setup and troubleshooting
- App connectivity
- Remote management features
- Integration with home automation

### 10.4 Water Quality Considerations
- Hard water impacts
- Sediment buildup prevention
- Water softeners and filtration
- Water quality testing

## 11. Technical Diagrams and Specifications
### 11.1 Wiring Diagrams
- Electric models
- Gas models with electronic controls
- Heat pump models
- Control board schematics

### 11.2 Plumbing Diagrams
- Standard installations
- Multiple heater installations
- Recirculation setups
- Expansion tank configurations

### 11.3 Technical Specifications
- BTU ratings
- Recovery rates
- First hour ratings
- Energy factor/UEF ratings
- Dimensions and clearances

## 12. Resources and References
### 12.1 Official Rheem Resources
- Manuals repository: https://www.rheem.com/resources/product-literature/
- Technical service bulletins: https://www.rheempro.com/tsb (requires contractor login)
- Training videos: https://www.youtube.com/user/RheemUsa/videos
- Customer support: 1-800-432-8373
- Contractor support: https://www.rheempro.com/
- EcoNet® support: https://www.rheem.com/EcoNet/

### 12.2 Code Requirements
- National code references
- Common local code variations
- Inspection requirements

### 12.3 Professional Resources
- Certification requirements
- Training opportunities
- Professional forums and communities

### 12.4 Safety Information
- Carbon monoxide awareness
- Scalding prevention
- Electrical safety
- Gas safety
- Emergency procedures

## 13. LLM Agent Implementation Guidelines
### 13.1 Vector Database Structure
- Chunk size recommendations: 512-1024 tokens
- Embedding model: text-embedding-3-large or equivalent
- Metadata schema:
  ```json
  {
    "section": "troubleshooting",
    "model_type": ["tankless", "gas"],
    "severity": "critical",
    "resolution_complexity": "medium",
    "requires_professional": true
  }
  ```

### 13.2 Query Processing
- Intent classification taxonomy
- Entity extraction patterns for water heater model numbers
- Example queries with annotated entities
- Question-answering pairs for fine-tuning

### 13.3 Multi-agent Coordination
- Agent roles:
  - Diagnostician: Analyzes symptoms and error codes
  - Parts Specialist: Identifies necessary replacement parts
  - Procedure Expert: Provides step-by-step repair instructions
  - Safety Monitor: Validates safety of recommended procedures
- Coordination protocols for complex troubleshooting

### 13.4 API Integration Points
- Parts inventory system integration
- Warranty validation endpoints
- Service scheduling system API
- Image recognition for error code/component identification

## 14. Resources and References

## 15. Predictive Maintenance System
### 15.1 Failure Prediction Models
- Component failure rate data
  - Source: Aggregated warranty claim statistics
  - MTBF (Mean Time Between Failures) by component
  - Environmental factor coefficients (water hardness, usage patterns)
- Early warning indicators
  - Pre-failure symptom patterns
  - Sequential symptom progression timelines
  - Statistical correlation between symptoms and failures
- Sensor data interpretation
  - For EcoNet® connected models
  - Temperature deviation patterns
  - Flow rate anomaly detection
  - Pressure fluctuation analysis

### 15.2 Maintenance Scheduling Algorithms
- Risk-based prioritization
  - Age-weighted component risk scores
  - Critical failure consequence metrics
  - Usage intensity factors
- Optimal maintenance intervals
  - Model-specific maintenance schedules
  - Usage-adjusted interval calculations
  - Water quality impact factors
- Cost-benefit analysis
  - Repair vs. replace decision matrices
  - Efficiency degradation cost models
  - Downtime impact calculations

### 15.3 Predictive Analytics for Parts Inventory
- Demand forecasting models
  - Regional failure rate variations
  - Seasonal component failure patterns
  - Installation date cohort analysis
- Stocking level recommendations
  - Critical component identification
  - Lead time considerations
  - Technician inventory optimization

## 16. Service Technician Instruction Generation
### 16.1 Procedure Template Library
- Step-by-step repair procedures
  - Model-specific variations
  - Required certification level indicators
  - Safety protocol integration
  - Estimated time requirements
- Diagnostic flowcharts
  - Decision trees for symptom-based diagnosis
  - Test procedure sequences
  - Measurement validation thresholds
- Installation templates
  - Code-compliant installation patterns
  - Regional requirement variations
  - Upgrade path procedures

### 16.2 Visual Instruction Generation
- Component location diagrams
  - Interactive 3D model references
  - Cross-sectional views
  - Exploded parts diagrams
- Tool usage illustrations
  - Proper tool positioning
  - Torque specifications
  - Special procedure animations
- Before/after validation imagery
  - Visual inspection guidelines
  - Comparison references for worn parts
  - Completed installation verification

### 16.3 Field Service Documentation
- Service report templates
  - Required data fields for warranty validation
  - Customer communication scripts
  - Follow-up recommendations
- Work verification procedures
  - Testing protocols after repair
  - Performance validation methods
  - Safety certification requirements
- Return visit reduction strategies
  - Common follow-up issue prevention
  - Comprehensive inspection checklists
  - Related component assessment guidelines

## 17. Warranty Determination System
### 17.1 Warranty Coverage Database
- Model-specific warranty terms
  - Source: https://www.rheem.com/warranty/
  - Standard coverage periods by component
  - Extended warranty details
  - Commercial vs. residential terms
- Registration verification
  - API endpoint for registration status
  - Required documentation
  - Transfer policies
- Exclusion conditions
  - Documented improper installation factors
  - Maintenance requirement violations
  - Water quality threshold violations
  - Unauthorized modification implications

### 17.2 Claim Validation Procedures
- Required evidence documentation
  - Photo/video requirements
  - Serial number validation patterns
  - Installation date verification methods
  - Maintenance record requirements
- Failure cause analysis
  - Normal wear vs. defect determination decision trees
  - Environmental factor assessment
  - Usage pattern evaluation
  - Component failure pattern library
- Approval/denial logic
  - Coverage verification workflow
  - Proration calculation formulas
  - Precedent-based determination support
  - Appeal process guidelines

### 17.3 Automated Warranty Decisions
- Confidence scoring model
  - Feature weighting for warranty factors
  - Certainty threshold requirements
  - Human review trigger conditions
- Decision explanation generation
  - Customer-friendly explanation templates
  - Technical justification documentation
  - Regulatory compliance verifications
- Historical case comparison
  - Similar claim outcome references
  - Policy interpretation consistency
  - Special circumstance handling

## 18. Reaction System for Issues
### 18.1 Emergency Response Protocols
- Critical failure detection
  - Safety hazard identification criteria
  - Immediate action requirements by hazard type
  - Customer notification templates
  - Emergency service dispatch triggers
- Containment procedures
  - Water damage minimization instructions
  - Gas leak response protocols
  - Electrical hazard isolation procedures
  - Temperature-related hazard management
- Severity classification
  - Issue urgency assessment criteria
  - Response time requirements by severity
  - Escalation thresholds and procedures
  - Public safety notification criteria

### 18.2 Customer Communication Engine
- Issue notification templates
  - Problem description generation
  - Severity-appropriate language
  - Next steps guidance
  - DIY vs. professional guidance
- Self-service options
  - Simple fix instruction generation
  - Video tutorial recommendations
  - Parts ordering assistance
  - Temporary workaround suggestions
- Scheduled maintenance reminders
  - Seasonal maintenance recommendations
  - Usage-based interval calculations
  - Preventive vs. reactive messaging

### 18.3 Service Network Integration
- Technician dispatch prioritization
  - Skill matching for issue complexity
  - Geolocation-based assignment
  - Parts availability confirmation
  - Response time optimization
- Real-time issue tracking
  - Resolution status updates
  - Escalation path automation
  - SLA compliance monitoring
  - Customer satisfaction measurement
- Fleet management coordination
  - Emergency response resource allocation
  - Preventive maintenance route optimization
  - Inventory distribution optimization
  - Multi-location service coordination

## 19. System Use Cases

This knowledge base supports four key capability areas:

* **Predictive Maintenance**: Early detection of potential failures, optimizing maintenance schedules, and forecasting component failures before they occur.
* **Warranty Determination**: Automating claim validation, handling complex conditional coverage situations, and proactively alerting customers before warranty issues arise.
* **Service Technician Instructions**: Generating precise repair procedures tailored to specific models and situations, creating appropriate documentation, and enforcing safety protocols.
* **Reactive Issue Response**: Managing emergency situations, generating clear customer communications, and optimizing technician dispatch based on skills and issue complexity.

### 19.1 Predictive Maintenance Use Cases
- **Early Failure Detection**
  - *Scenario:* Detect increasing exhaust temperature trend in tankless unit
  - *Actions:* Alert customer to schedule descaling before complete failure
  - *Benefits:* Avoid emergency service call, extend unit lifespan, prevent warranty dispute
  - *Data Inputs:* EcoNet® sensor readings, usage patterns, water hardness data
  - *Outputs:* Maintenance recommendation with urgency level, cost/benefit analysis

- **Maintenance Schedule Optimization**
  - *Scenario:* Determine optimal maintenance intervals based on usage and environment
  - *Actions:* Generate personalized maintenance schedule for maximum efficiency and lifespan
  - *Benefits:* Reduce unnecessary service calls, prevent premature failures
  - *Data Inputs:* Installation environment, water quality, usage intensity, model reliability data
  - *Outputs:* Custom maintenance timeline with specific tasks and priorities

- **Component Failure Forecasting**
  - *Scenario:* Calculate probability and timeframe of specific component failures
  - *Actions:* Recommend proactive replacement of high-risk components
  - *Benefits:* Minimize downtime, consolidate service visits, optimize parts inventory
  - *Data Inputs:* Component age, usage cycles, environmental factors, failure rate statistics
  - *Outputs:* Component risk assessment with replacement recommendations

### 19.2 Warranty Determination Use Cases
- **Automatic Claim Validation**
  - *Scenario:* Evaluate warranty coverage for heat exchanger failure on 3-year-old unit
  - *Actions:* Verify installation date, registration status, maintenance history, and coverage terms
  - *Benefits:* Reduce manual review time, ensure consistent policy application
  - *Data Inputs:* Purchase documentation, maintenance records, model warranty terms
  - *Outputs:* Coverage determination with justification and next steps

- **Conditional Coverage Assessment**
  - *Scenario:* Determine coverage when maintenance requirements partially met
  - *Actions:* Evaluate maintenance history against failure cause, assess policy exemptions
  - *Benefits:* Balance customer satisfaction with policy enforcement, identify reasonable exceptions
  - *Data Inputs:* Maintenance record timeline, water quality tests, actual vs. required maintenance
  - *Outputs:* Coverage recommendation with confidence score and required documentation

- **Proactive Warranty Alerts**
  - *Scenario:* Identify units at risk of warranty invalidation
  - *Actions:* Alert customers before maintenance deadline or warranty expiration
  - *Benefits:* Increase compliance, improve customer satisfaction, reduce disputes
  - *Data Inputs:* Installation records, maintenance history, warranty requirements
  - *Outputs:* Personalized notifications with deadline and recommended actions

### 19.3 Service Technician Instruction Use Cases
- **Precise Repair Procedure Generation**
  - *Scenario:* Generate model-specific instructions for error code C7 31 (scale buildup)
  - *Actions:* Create step-by-step procedure with correct tool requirements and safety precautions
  - *Benefits:* Reduce repair time, ensure proper procedure, prevent technician errors
  - *Data Inputs:* Model specifications, error diagnostics, technician skill level
  - *Outputs:* Custom repair procedure with visual aids and testing protocols

- **Dynamic Field Service Documentation**
  - *Scenario:* Generate required documentation templates for warranty repair
  - *Actions:* Create checklists and forms specific to the repair type and warranty requirements
  - *Benefits:* Ensure complete documentation, streamline claim processing
  - *Data Inputs:* Repair type, warranty terms, required evidence standards
  - *Outputs:* Custom documentation forms with required fields and photo requirements

- **Critical Safety Procedure Enforcement**
  - *Scenario:* Ensure safety protocols for gas-related repairs
  - *Actions:* Generate safety-focused procedures with verification steps
  - *Benefits:* Prevent safety incidents, ensure compliance with regulations
  - *Data Inputs:* Local codes, safety requirements, incident history
  - *Outputs:* Safety-enhanced repair procedures with verification requirements

### 19.4 Reactive Issue Response Use Cases
- **Emergency Situation Handling**
  - *Scenario:* Customer reports gas smell and error code indicating valve failure
  - *Actions:* Provide immediate safety instructions, dispatch emergency technician
  - *Benefits:* Ensure customer safety, prevent property damage
  - *Data Inputs:* Error code severity, safety risk assessment, location information
  - *Outputs:* Emergency response protocol with customer safety instructions

- **Issue-Specific Communication Generation**
  - *Scenario:* Generate customer notification for intermittent water temperature fluctuation
  - *Actions:* Create explanation with severity assessment and temporary workarounds
  - *Benefits:* Set appropriate expectations, reduce follow-up calls, improve customer experience
  - *Data Inputs:* Issue diagnosis, customer proficiency level, availability of workarounds
  - *Outputs:* Customized communication with clear explanation and recommended actions

- **Technician Dispatch Optimization**
  - *Scenario:* Assign appropriate technician for complex heat pump water heater issue
  - *Actions:* Match issue complexity with technician skills and part availability
  - *Benefits:* First-time fix rate improvement, reduced repeat visits
  - *Data Inputs:* Issue diagnosis, required skills, technician certifications, inventory data
  - *Outputs:* Optimized service assignment with skill matching and parts preparation

## Appendices
### Appendix A: Model Number Decoder
- How to read Rheem model numbers
  - Source: https://www.rheem.com/resources/residential/water-heaters/model-decoder/
  - JSON schema for programmatic decoding
  - Example: {"XG40T09HE36U0": {"type": "gas", "capacity": "40 gallons", "series": "Performance"}}
- Manufacturing date codes
  - Format: YYWW (Year-Week)
  - Decoder API endpoint: `/decoder/manufacturing-date/{code}`
- Series identification
  - Model prefix mappings in JSON format for agent consumption

### Appendix B: Tool Requirements
- Basic maintenance tools
  - Structured list with tool name, purpose, and alternative options
  - Links to compatible testing equipment
- Advanced repair tools
  - Specialized tools by repair type
  - Object schema: {"repair_type": "element_replacement", "tools": ["element wrench", "multimeter"]}
- Diagnostic equipment
  - Digital vs. analog options
  - Source: https://www.rheempro.com/tools (requires contractor login)

### Appendix C: Conversion Tables
- Temperature conversions
  - F to C formula: (F - 32) * 5/9
  - Conversion API endpoint: `/convert/temperature/{value}/{from}/{to}`
- Pressure measurements
  - PSI to kPa conversion: PSI * 6.89476
  - Common water heater pressure ranges in structured format
- Volume calculations
  - Gallons to cubic feet: gallons * 0.133681
  - Tank size reference table in CSV format
- BTU calculations
  - Formula: BTU/h needed = (GPH × ΔT × 8.33) ÷ efficiency
  - Calculator API endpoint: `/calculate/btu/{params}`

### Appendix D: Document Revision History
- Knowledge base updates
  - Timestamp format: ISO 8601
  - Change tracking schema for version control
- New model additions
  - JSON feed for model information updates
  - Last update timestamp metadata
- Technical bulletin references
  - Bulletin ID mapping to affected models
  - Vector embeddings for semantic search implementation
