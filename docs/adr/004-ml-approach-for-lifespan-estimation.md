# ADR 004: Machine Learning Approach for Water Heater Lifespan Estimation

## Status
Accepted

## Context
A critical feature of the IoTSphere water heater monitoring system is predicting the remaining useful life of water heaters. This prediction helps facility managers plan maintenance, budget for replacements, and minimize disruptions. We needed to determine the most appropriate machine learning approach for implementing lifespan estimation that balances accuracy, interpretability, and development complexity.

Options considered:
1. Simple rule-based system with fixed degradation rates
2. Statistical approach with weighted factor analysis
3. Regression-based machine learning models
4. Deep learning neural networks
5. Time-series forecasting models
6. Hybrid approach combining domain knowledge with machine learning

## Decision
We will implement a hybrid approach for lifespan estimation that combines domain expertise with statistical machine learning techniques. This model follows the "modification factor" methodology, where a base lifespan is adjusted by various factors derived from device characteristics and operational data.

The implementation will:
1. Start with a base lifespan estimate derived from manufacturer specifications
2. Apply modification factors based on key variables (temperature settings, water hardness, usage intensity, etc.)
3. Incorporate robust error handling for various input formats
4. Follow Test-Driven Development practices throughout implementation

## Rationale

### Hybrid Approach Benefits
- Leverages domain expertise about water heater degradation factors
- Produces explainable results that can be traced to specific factors
- Requires less training data than pure machine learning approaches
- Allows for easy adjustment of individual factors as more data becomes available
- Gracefully handles missing or incomplete data
- Can be incrementally improved without complete model replacement

### Test-Driven Development Integration
- Aligns with our project's TDD principles
- Enables clear definition of expected model behaviors
- Facilitates iterative improvement of the prediction model
- Ensures robust error handling for edge cases

### Implementation Considerations
- Focus on real-time operational monitoring rather than historical analytics
- Prioritization of robustness over complex modeling techniques
- Graceful degradation when ideal data is unavailable
- Emphasis on maintainability and explainability

## Implementation Details
- Factor-based mathematical model that combines multiple influence variables
- Explicit handling of different data formats (floats, lists, strings)
- Clear logging for data quality issues
- PostgreSQL storage of prediction results
- Well-documented code with clear variable names representing real-world factors

## Consequences

### Positive Consequences
- Transparent prediction model that facility managers can understand
- Ability to explain the factors influencing a specific water heater's lifespan
- Easier troubleshooting and refinement compared to black-box ML models
- Lower computational requirements than deep learning approaches
- Graceful handling of various input data formats and edge cases

### Negative Consequences
- May not capture complex, non-linear interactions between factors
- Requires domain expertise to properly set and adjust factor weights
- Less powerful than deep learning for very large, complex datasets
- May require manual recalibration as water heater technology evolves

## References
- [ASHRAE Equipment Life Expectancy chart](https://www.ashrae.org/technical-resources/research)
- [Water Heater Degradation Research](https://www.energy.gov/energysaver/water-heating)
- IoTSphere Project [predictionsplan.md](/docs/predictionsplan.md)
- TDD Principles from Project Memory
