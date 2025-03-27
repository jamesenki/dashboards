"""
Usage pattern predictor for water heater operational data.

This module analyzes water usage patterns to predict component degradation
and optimize maintenance based on actual usage rather than fixed schedules.
"""
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from src.predictions.interfaces import PredictionResult, ActionSeverity, RecommendedAction


class UsagePatternPredictor:
    """
    Predicts component degradation and maintenance needs based on water heater usage patterns.
    
    This predictor analyzes usage data to identify:
    - Heavy usage patterns that accelerate wear
    - Usage scenario impacts on expected component lifespan
    - Efficiency changes based on usage patterns
    """
    
    def __init__(self):
        """Initialize the usage pattern predictor."""
        # Define usage classification thresholds
        self._usage_thresholds = {
            'light': {
                'daily_usage_liters': 100,
                'heating_cycles_per_day': 4
            },
            'normal': {
                'daily_usage_liters': 200,
                'heating_cycles_per_day': 8
            },
            'heavy': {
                'daily_usage_liters': 250,
                'heating_cycles_per_day': 10
            }
        }
        
        # Define component wear factors based on usage
        self._component_wear_factors = {
            'heating_element': {
                'light': 0.7,
                'normal': 1.0,
                'heavy': 1.3
            },
            'thermostat': {
                'light': 0.8,
                'normal': 1.0,
                'heavy': 1.2
            },
            'anode_rod': {
                'light': 0.85,
                'normal': 1.0,
                'heavy': 1.25
            },
            'tank_integrity': {
                'light': 0.9,
                'normal': 1.0, 
                'heavy': 1.15
            }
        }
        
        # Temperature impact multipliers
        self._temperature_multipliers = {
            # For temperature settings in degrees
            'low': (110, 0.8),     # Below 110°F
            'normal': (130, 1.0),  # 110-130°F 
            'high': (140, 1.2),    # 130-140°F
            'very_high': (150, 1.5) # Above 140°F
        }
    
    async def predict(self, device_id: str, features: Dict[str, Any]) -> PredictionResult:
        """
        Generate predictions based on water heater usage patterns.
        
        Args:
            device_id: Identifier for the water heater
            features: Dictionary containing usage data
            
        Returns:
            PredictionResult containing usage impact analysis and recommended actions
        """
        # Initialize prediction result
        result = PredictionResult(
            device_id=device_id,
            prediction_type="usage_patterns",  # Changed to match API endpoint
            predicted_value=0.0,  # Will be updated based on usage impact
            confidence=0.80,  # Initial confidence level
            features_used=[key for key in features.keys()],
            timestamp=datetime.now(),
            recommended_actions=[],  # Will be populated later
            raw_details={
                "usage_patterns": {},
                "impact_on_components": {},
                "efficiency_projections": {},
                "optimization_recommendations": []  # Added this key for optimization recommendations
            }
        )
        
        # Classify usage pattern
        usage_classification = self._classify_usage(features)
        result.raw_details["usage_classification"] = usage_classification
        
        # Analyze weekly and daily patterns
        if 'daily_usage_liters' in features:
            self._analyze_usage_patterns(features['daily_usage_liters'], result)
        
        # Determine impact on components
        self._calculate_component_impacts(usage_classification, features, result)
        
        # Project efficiency changes
        self._project_efficiency_changes(usage_classification, features, result)
        
        # Generate recommended actions
        self._generate_recommendations(result)
        
        # Calculate overall predicted value (0-1) - higher means more impact from usage
        impact_factors = [
            component_data.get('wear_acceleration_factor', 1.0)
            for component, component_data in result.raw_details["impact_on_components"].items()
        ]
        
        if impact_factors:
            # Average impact factor, normalized to 0-1 scale
            # 1.0 is normal wear, 2.0 would be maximum expected acceleration
            avg_impact = sum(impact_factors) / len(impact_factors)
            result.predicted_value = min(1.0, (avg_impact - 0.7) / 1.3)
        
        return result
    
    def _classify_usage(self, features: Dict[str, Any]) -> str:
        """
        Classify the usage pattern based on water usage and heating cycles.
        
        Args:
            features: Dictionary of water heater usage features
            
        Returns:
            Usage classification: 'light', 'normal', or 'heavy'
        """
        # Extract relevant features
        avg_daily_usage = self._get_average_daily_usage(features)
        avg_heating_cycles = self._get_average_heating_cycles(features)
        
        # Determine usage level based on thresholds
        usage_level = 'normal'  # Default
        
        # Check for heavy usage
        if (avg_daily_usage >= self._usage_thresholds['heavy']['daily_usage_liters'] or
            avg_heating_cycles >= self._usage_thresholds['heavy']['heating_cycles_per_day']):
            usage_level = 'heavy'
        # Check for light usage
        elif (avg_daily_usage <= self._usage_thresholds['light']['daily_usage_liters'] and
              avg_heating_cycles <= self._usage_thresholds['light']['heating_cycles_per_day']):
            usage_level = 'light'
            
        return usage_level
    
    def _get_average_daily_usage(self, features: Dict[str, Any]) -> float:
        """
        Calculate the average daily water usage from the features.
        
        Args:
            features: Dictionary containing usage data
            
        Returns:
            Average daily water usage in liters
        """
        if 'daily_usage_liters' not in features:
            return self._usage_thresholds['normal']['daily_usage_liters']  # Default if no data
            
        daily_usage = features['daily_usage_liters']
        if not daily_usage:
            return self._usage_thresholds['normal']['daily_usage_liters']
            
        # Focus on recent usage (last 10 entries if available)
        recent_usage = daily_usage[-10:] if len(daily_usage) > 10 else daily_usage
        return sum(entry['value'] for entry in recent_usage) / len(recent_usage)
    
    def _get_average_heating_cycles(self, features: Dict[str, Any]) -> float:
        """
        Calculate the average number of heating cycles per day.
        
        Args:
            features: Dictionary containing usage data
            
        Returns:
            Average heating cycles per day
        """
        if 'heating_cycles_per_day' in features and isinstance(features['heating_cycles_per_day'], (int, float)):
            return float(features['heating_cycles_per_day'])
            
        if 'heating_cycles_per_day' in features and isinstance(features['heating_cycles_per_day'], list):
            cycles = features['heating_cycles_per_day']
            if not cycles:
                return self._usage_thresholds['normal']['heating_cycles_per_day']
                
            # Focus on recent data
            recent_cycles = cycles[-10:] if len(cycles) > 10 else cycles
            return sum(entry['value'] for entry in recent_cycles) / len(recent_cycles)
            
        return self._usage_thresholds['normal']['heating_cycles_per_day']  # Default
    
    def _analyze_usage_patterns(self, daily_usage: List[Dict], result: PredictionResult) -> None:
        """
        Analyze daily usage data to identify patterns.
        
        Args:
            daily_usage: List of daily water usage records
            result: PredictionResult to update with findings
        """
        if not daily_usage or len(daily_usage) < 7:
            return
            
        # Sort data by date
        sorted_usage = sorted(daily_usage, key=lambda x: x['date'])
        
        # Extract weekday vs weekend patterns
        weekday_usage = []
        weekend_usage = []
        
        for entry in sorted_usage:
            # Extract weekday (0 = Monday, 6 = Sunday)
            weekday = entry['date'].weekday()
            
            if weekday < 5:  # Weekday (Monday-Friday)
                weekday_usage.append(entry['value'])
            else:  # Weekend (Saturday-Sunday)
                weekend_usage.append(entry['value'])
        
        if weekday_usage and weekend_usage:
            avg_weekday = sum(weekday_usage) / len(weekday_usage)
            avg_weekend = sum(weekend_usage) / len(weekend_usage)
            
            # Calculate weekly variation
            weekly_variation = (avg_weekend / avg_weekday) - 1 if avg_weekday > 0 else 0
            
            result.raw_details["usage_patterns"]["weekly"] = {
                "weekday_average_liters": avg_weekday,
                "weekend_average_liters": avg_weekend,
                "weekly_variation_percent": weekly_variation * 100
            }
        
        # Check for usage trend over time
        if len(sorted_usage) >= 14:
            first_half = sorted_usage[:len(sorted_usage)//2]
            second_half = sorted_usage[len(sorted_usage)//2:]
            
            avg_first = sum(entry['value'] for entry in first_half) / len(first_half)
            avg_second = sum(entry['value'] for entry in second_half) / len(second_half)
            
            # Calculate trend
            usage_trend = (avg_second / avg_first) - 1 if avg_first > 0 else 0
            
            result.raw_details["usage_patterns"]["trend"] = {
                "direction": "increasing" if usage_trend > 0.05 else 
                             "decreasing" if usage_trend < -0.05 else "stable",
                "percent_change": usage_trend * 100
            }
    
    def _calculate_component_impacts(self, usage_classification: str, 
                                   features: Dict[str, Any], 
                                   result: PredictionResult) -> None:
        """
        Calculate the impact of usage patterns on water heater components.
        
        Args:
            usage_classification: The classified usage pattern
            features: Dictionary of usage features
            result: PredictionResult to update with component impacts
        """
        components = ['heating_element', 'thermostat', 'anode_rod', 'tank_integrity']
        
        # Get temperature impact multiplier
        temp_setting = features.get('average_temperature_setting', 130)
        temp_multiplier = self._get_temperature_multiplier(temp_setting)
        
        # Calculate impact for each component
        for component in components:
            # Base wear factor from usage classification
            base_wear_factor = self._component_wear_factors[component].get(
                usage_classification, 
                self._component_wear_factors[component]['normal']
            )
            
            # Apply temperature multiplier
            adjusted_wear_factor = base_wear_factor * temp_multiplier
            
            # Calculate days until impact becomes significant
            days_until_impact = self._calculate_days_until_impact(
                component, adjusted_wear_factor, usage_classification
            )
            
            # Calculate efficiency impact
            efficiency_impact = self._calculate_efficiency_impact(
                component, adjusted_wear_factor
            )
            
            result.raw_details["impact_on_components"][component] = {
                "wear_acceleration_factor": adjusted_wear_factor,
                "days_until_significant_impact": days_until_impact,
                "efficiency_impact_percent": efficiency_impact,
                "contributing_factors": {
                    "usage_level": usage_classification,
                    "temperature_setting": temp_setting
                }
            }
    
    def _get_temperature_multiplier(self, temperature: float) -> float:
        """
        Get the temperature impact multiplier based on temperature setting.
        
        Args:
            temperature: The temperature setting in degrees
            
        Returns:
            Multiplier for component wear based on temperature
        """
        if temperature <= self._temperature_multipliers['low'][0]:
            return self._temperature_multipliers['low'][1]
        elif temperature <= self._temperature_multipliers['normal'][0]:
            return self._temperature_multipliers['normal'][1]
        elif temperature <= self._temperature_multipliers['high'][0]:
            return self._temperature_multipliers['high'][1]
        else:
            return self._temperature_multipliers['very_high'][1]
    
    def _calculate_days_until_impact(self, component: str, 
                                    wear_factor: float, 
                                    usage_classification: str) -> int:
        """
        Calculate days until usage impact becomes significant for a component.
        
        Args:
            component: The component name
            wear_factor: The calculated wear acceleration factor
            usage_classification: The usage classification
            
        Returns:
            Estimated days until significant impact
        """
        # Base days until impact by component
        base_days = {
            'heating_element': 180,
            'thermostat': 240,
            'anode_rod': 120,
            'tank_integrity': 365
        }
        
        # Calculate adjusted days
        adjusted_days = base_days.get(component, 180) / wear_factor
        
        # Apply usage-specific adjustments
        if usage_classification == 'heavy' and wear_factor > 1.2:
            adjusted_days *= 0.8  # Further reduce for very heavy usage
        elif usage_classification == 'light' and wear_factor < 0.9:
            adjusted_days *= 1.2  # Increase for very light usage
            
        return int(adjusted_days)
    
    def _calculate_efficiency_impact(self, component: str, wear_factor: float) -> float:
        """
        Calculate the efficiency impact percentage based on component and wear factor.
        
        Args:
            component: The component name
            wear_factor: The calculated wear acceleration factor
            
        Returns:
            Efficiency impact as a percentage
        """
        # Base efficiency impact by component
        base_impact = {
            'heating_element': 15,
            'thermostat': 10,
            'anode_rod': 5,
            'tank_integrity': 8
        }
        
        # Scale impact by how much wear factor exceeds normal (1.0)
        excess_wear = max(0, wear_factor - 1.0)
        efficiency_impact = base_impact.get(component, 10) * excess_wear
        
        return round(efficiency_impact, 1)
    
    def _project_efficiency_changes(self, usage_classification: str, 
                                  features: Dict[str, Any], 
                                  result: PredictionResult) -> None:
        """
        Project future efficiency changes based on usage patterns.
        
        Args:
            usage_classification: The classified usage pattern
            features: Dictionary of usage features
            result: PredictionResult to update with efficiency projections
        """
        # Extract age of water heater
        installation_date = features.get('installation_date')
        days_since_installation = 0
        
        if installation_date:
            days_since_installation = (datetime.now() - installation_date).days
        
        # Base efficiency decline rates (percent per year)
        base_decline_rates = {
            'light': 3,
            'normal': 5,
            'heavy': 8
        }
        
        # Adjust for age
        age_factor = 1.0
        if days_since_installation > 1095:  # > 3 years
            age_factor = 1.5
        elif days_since_installation > 730:  # > 2 years
            age_factor = 1.3
        elif days_since_installation > 365:  # > 1 year
            age_factor = 1.1
            
        # Calculate overall efficiency projection
        decline_rate = base_decline_rates.get(usage_classification, 5) * age_factor
        
        # Project for next 30, 60, 90 days
        result.raw_details["efficiency_projections"] = {
            "baseline_decline_rate_yearly": decline_rate,
            "30_day_projected_decline": round(decline_rate / 12, 1),
            "60_day_projected_decline": round(decline_rate / 6, 1),
            "90_day_projected_decline": round(decline_rate / 4, 1)
        }
    
    def _generate_recommendations(self, result: PredictionResult) -> None:
        """
        Generate recommended actions based on usage pattern analysis.
        
        Args:
            result: PredictionResult to update with recommendations
        """
        recommendations = []
        
        # Get usage classification
        usage_class = result.raw_details.get("usage_classification", "normal")
        
        # Generate component-specific recommendations
        for component, impact in result.raw_details["impact_on_components"].items():
            wear_factor = impact.get("wear_acceleration_factor", 1.0)
            days_until_impact = impact.get("days_until_significant_impact", 180)
            efficiency_impact = impact.get("efficiency_impact_percent", 0)
            
            # Only recommend for accelerated wear
            if wear_factor > 1.1:
                severity = ActionSeverity.LOW
                if days_until_impact < 60:
                    severity = ActionSeverity.HIGH
                elif days_until_impact < 120:
                    severity = ActionSeverity.MEDIUM
                
                component_name = component.replace("_", " ").title()
                wear_percent = int((wear_factor - 1.0) * 100)
                
                action = RecommendedAction(
                    action_id=f"usage_wear_{component}_{datetime.now().strftime('%Y%m%d')}",
                    description=f"Monitor {component_name} due to {usage_class} usage pattern",
                    impact=f"Current {usage_class} usage pattern accelerating {component_name} wear by "
                           f"{wear_percent}% above normal",
                    expected_benefit=f"Early detection of {component_name} degradation to prevent unexpected failures",
                    severity=severity,
                    due_date=datetime.now() + timedelta(days=min(days_until_impact // 2, 90)),
                    estimated_cost=None,  # Monitoring has no direct cost
                    estimated_duration="N/A - ongoing monitoring"
                )
                recommendations.append(action)
            
            # Add maintenance recommendations for high efficiency impact
            if efficiency_impact > 10:
                severity = ActionSeverity.MEDIUM
                due_days = 30
                if efficiency_impact > 20:
                    severity = ActionSeverity.HIGH
                    due_days = 14
                
                component_name = component.replace("_", " ").title()
                
                action = RecommendedAction(
                    action_id=f"efficiency_maint_{component}_{datetime.now().strftime('%Y%m%d')}",
                    description=f"Schedule {component_name} maintenance to address efficiency loss",
                    impact=f"Usage pattern causing projected {efficiency_impact:.1f}% efficiency decline over next 60 days",
                    expected_benefit=f"Restore {component_name} efficiency and reduce energy costs by up to {efficiency_impact:.1f}%",
                    severity=severity,
                    due_date=datetime.now() + timedelta(days=due_days),
                    estimated_cost=100 if component == "thermostat" else 
                                   200 if component == "heating_element" else 150,
                    estimated_duration="2-3 hours"
                )
                recommendations.append(action)
        
        # Add usage adjustment recommendation if heavy usage
        if usage_class == 'heavy':
            # Extract the most impacted component
            most_impacted = max(
                result.raw_details["impact_on_components"].items(),
                key=lambda x: x[1].get("wear_acceleration_factor", 0)
            )
            component_name = most_impacted[0].replace("_", " ").title()
            wear_factor = most_impacted[1].get("wear_acceleration_factor", 1.0)
            
            if wear_factor > 1.2:
                action = RecommendedAction(
                    action_id=f"usage_adjust_{datetime.now().strftime('%Y%m%d')}",
                    description="Consider adjusting usage pattern to extend water heater lifespan",
                    impact=f"Reducing current heavy usage by 15-20% could extend overall lifespan by up to 30%, "
                           f"particularly for the {component_name}",
                    expected_benefit="Significant lifespan extension and reduced maintenance costs over time",
                    severity=ActionSeverity.LOW,
                    due_date=None,  # Ongoing recommendation
                    estimated_cost=None,
                    estimated_duration=None
                )
                recommendations.append(action)
        
        # Add efficiency decline recommendation
        if "efficiency_projections" in result.raw_details:
            decline_90 = result.raw_details["efficiency_projections"].get("90_day_projected_decline", 0)
            
            if decline_90 > 5:
                action = RecommendedAction(
                    action_id=f"efficiency_service_{datetime.now().strftime('%Y%m%d')}",
                    description="Schedule efficiency maintenance service",
                    impact=f"Projected {decline_90}% efficiency decline over next 90 days based on current usage pattern",
                    expected_benefit=f"Restore optimal efficiency and save approximately ${decline_90 * 5:.0f}-${decline_90 * 10:.0f} in energy costs annually",
                    severity=ActionSeverity.MEDIUM,
                    due_date=datetime.now() + timedelta(days=45),
                    estimated_cost=200,
                    estimated_duration="3-4 hours"
                )
                recommendations.append(action)
        
        # Add recommendations to result
        result.recommended_actions.extend(recommendations)
        
        # Add a fallback recommendation if no recommendations were generated
        if not result.recommended_actions:
            # Get current date for the action ID
            current_date = datetime.now().strftime('%Y%m%d')
            
            # Add a recommendation based on usage classification
            usage_class = result.raw_details.get("usage_classification", "normal")
            device_id = result.device_id  # Get device_id from the result object
            
            if usage_class == "light":
                action = RecommendedAction(
                    action_id=f"light_usage_maint_{device_id}_{current_date}",
                    description="Maintain current optimal usage pattern",
                    severity=ActionSeverity.LOW,
                    impact="Your current light usage pattern extends component lifespan",
                    expected_benefit="Continued optimal efficiency and extended equipment life",
                    due_date=datetime.now() + timedelta(days=180),  # Semi-annual reminder
                    estimated_cost=0.0,
                    estimated_duration="N/A"
                )
            elif usage_class == "normal":
                action = RecommendedAction(
                    action_id=f"normal_usage_maint_{device_id}_{current_date}",
                    description="Schedule routine maintenance check",
                    severity=ActionSeverity.LOW,
                    impact="Maintain optimal performance with your normal usage pattern",
                    expected_benefit="Prevent efficiency loss and extend equipment lifespan",
                    due_date=datetime.now() + timedelta(days=120),  # Quarterly reminder
                    estimated_cost=50.0,
                    estimated_duration="1 hour"
                )
            else:  # heavy
                action = RecommendedAction(
                    action_id=f"heavy_usage_maint_{device_id}_{current_date}",
                    description="Consider usage adjustments to optimize efficiency",
                    severity=ActionSeverity.MEDIUM,
                    impact="Your heavy usage pattern may affect long-term efficiency",
                    expected_benefit="Extended equipment life and reduced operating costs",
                    due_date=datetime.now() + timedelta(days=30),
                    estimated_cost=0.0,
                    estimated_duration="N/A"
                )
            
            result.recommended_actions.append(action)
            
        # Generate optimization recommendations
        self._generate_optimization_recommendations(result)
    def _generate_optimization_recommendations(self, result: PredictionResult) -> None:
        """
        Generate optimization recommendations based on usage patterns.
        
        Args:
            result: PredictionResult to update with optimization recommendations
        """
        optimizations = []
        usage_class = result.raw_details.get('usage_classification', 'normal')
        usage_patterns = result.raw_details.get('usage_patterns', {})
        efficiency_projections = result.raw_details.get('efficiency_projections', {})
        
        # Default estimated annual cost increase if not available
        est_annual_cost_increase = 100
        if 'efficiency_projections' in result.raw_details:
            est_annual_cost_increase = result.raw_details['efficiency_projections'].get('estimated_annual_cost_increase', 100)
        
        # Generate optimization recommendations based on usage classification
        if usage_class == 'heavy':
            # Recommend temperature reduction if usage is heavy
            optimizations.append({
                'type': 'temperature',
                'description': 'Reduce water temperature by 3-5°C',
                'impact': 'Temperature reduction will decrease energy usage and reduce strain on heating elements',
                'benefit': 'Extended component lifespan and improved energy efficiency',
                'annual_savings_estimate': f'${round(est_annual_cost_increase * 0.4, 2)}'
            })
            
            # Recommend scheduled usage if we see peak usage times
            if usage_patterns.get('weekly_pattern') in ['peak_day', 'weekend_heavy']:
                optimizations.append({
                    'type': 'scheduling',
                    'description': 'Distribute water usage more evenly throughout the week',
                    'impact': 'Reducing peak loads extends component lifespan by preventing stress cycles',
                    'benefit': 'More consistent water temperature and reduced energy costs',
                    'annual_savings_estimate': f'${round(est_annual_cost_increase * 0.3, 2)}'
                })
                
            # Recommend usage monitoring system
            optimizations.append({
                'type': 'monitoring',
                'description': 'Install water usage monitoring system',
                'impact': 'Real-time monitoring allows for immediate detection of excessive usage',
                'benefit': 'Prevent water waste and optimize heating cycles',
                'annual_savings_estimate': f'${round(est_annual_cost_increase * 0.5, 2)}'
            })
            
        elif usage_class == 'normal':
            # For normal usage, optimize based on patterns
            if usage_patterns.get('daily_pattern') == 'morning_evening_peaks':
                optimizations.append({
                    'type': 'timing',
                    'description': 'Use timer to heat water just before peak usage periods',
                    'impact': 'Reduces standby losses by heating water only when needed',
                    'benefit': 'Lower energy consumption and reduced operating costs',
                    'annual_savings_estimate': '$75-$120'
                })
                
            # Recommend insulation improvement for all normal usage scenarios
            optimizations.append({
                'type': 'insulation',
                'description': 'Add supplemental insulation blanket to water heater',
                'impact': 'Reduces heat loss during standby periods',
                'benefit': 'Lower energy consumption and more consistent water temperature',
                'annual_savings_estimate': '$40-$60'
            })
            
        # For all usage classes, recommend regular maintenance
        optimizations.append({
            'type': 'maintenance',
            'description': 'Schedule regular maintenance every 6-12 months',
            'impact': 'Maintains efficiency and prevents sediment buildup',
            'benefit': 'Extended equipment life and consistent performance',
            'annual_savings_estimate': 'Prevents $200-$500 in potential repair costs'
        })
        
        # Add optimizations to raw details
        result.raw_details['optimization_recommendations'] = optimizations
