"""
Advanced ML Intelligence Module
Provides risk driver explanation, confidence scoring, and decision support
"""
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class RiskIntelligence:
    """Advanced risk analysis and explainability"""
    
    @staticmethod
    def calculate_feature_importance(features: Dict[str, float], prediction: float) -> Dict[str, float]:
        """
        Calculate feature contributions to risk score
        Approximates SHAP values using model sensitivity analysis
        """
        # Feature weights based on XGBoost model training (approximate)
        # In production, use actual SHAP values from trained model
        feature_weights = {
            'ndvi_trend': 0.35,      # Trend has highest impact
            'ndvi_anomaly': 0.30,    # Current anomaly is critical
            'rainfall_deficit': 0.20, # Rainfall stress
            'heat_stress_days': 0.15  # Heat damage
        }
        
        # Normalize feature values to contribution percentages
        contributions = {}
        total_contribution = 0
        
        for feature, value in features.items():
            if feature in feature_weights:
                # Absolute impact = |value| * weight * prediction
                impact = abs(value) * feature_weights[feature] * (prediction / 100)
                contributions[feature] = impact
                total_contribution += impact
        
        # Normalize to percentages
        if total_contribution > 0:
            contributions = {k: (v / total_contribution) * 100 
                           for k, v in contributions.items()}
        
        return contributions
    
    @staticmethod
    def get_top_risk_drivers(contributions: Dict[str, float], n: int = 3) -> List[Tuple[str, float]]:
        """Get top N risk drivers sorted by contribution"""
        sorted_drivers = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
        return sorted_drivers[:n]
    
    @staticmethod
    def explain_risk_drivers(top_drivers: List[Tuple[str, float]], risk_score: float) -> str:
        """Generate human-readable risk explanation"""
        driver_names = {
            'ndvi_trend': 'vegetation decline',
            'ndvi_anomaly': 'abnormal vegetation health',
            'rainfall_deficit': 'rainfall deficit',
            'heat_stress_days': 'heat stress'
        }
        
        if not top_drivers:
            return "Risk assessment based on multiple factors"
        
        explanations = []
        for feature, contribution in top_drivers:
            driver_name = driver_names.get(feature, feature)
            explanations.append(f"{driver_name} ({contribution:.0f}%)")
        
        return f"Risk driven mainly by {' and '.join(explanations)}"
    
    @staticmethod
    def calculate_time_to_impact(risk_score: float, ndvi_trend: float) -> str:
        """
        Estimate time window for expected impact
        Based on vegetation decline rate and current stress level
        """
        # Rapid decline + high risk = immediate impact
        if ndvi_trend < -0.1 and risk_score > 70:
            return "< 7 days"
        
        # Significant decline or high risk
        if ndvi_trend < -0.05 or risk_score > 70:
            return "7-14 days"
        
        # Moderate decline or medium risk
        if ndvi_trend < -0.02 or risk_score > 40:
            return "14-30 days"
        
        # Stable or improving
        return "> 30 days (Stable)"
    
    @staticmethod
    def calculate_prediction_confidence(features: Dict[str, float], 
                                       data_points: int = 30,
                                       cloud_coverage: float = 0.0) -> Tuple[str, float]:
        """
        Assess prediction confidence based on data quality
        Returns: (confidence_level, confidence_score)
        """
        confidence_score = 100.0
        
        # Penalize for insufficient data
        if data_points < 10:
            confidence_score -= 30
        elif data_points < 20:
            confidence_score -= 15
        
        # Penalize for high cloud coverage
        if cloud_coverage > 0.5:
            confidence_score -= 25
        elif cloud_coverage > 0.3:
            confidence_score -= 15
        
        # Penalize for extreme/unusual feature values
        if abs(features.get('ndvi_anomaly', 0)) > 0.4:
            confidence_score -= 10
        
        if abs(features.get('ndvi_trend', 0)) > 0.2:
            confidence_score -= 10
        
        # Confidence level
        if confidence_score >= 80:
            return {'level': 'High', 'score': confidence_score}
        elif confidence_score >= 60:
            return {'level': 'Medium', 'score': confidence_score}
        else:
            return {'level': 'Low', 'score': confidence_score}
    
    @staticmethod
    def simulate_scenario(base_risk: float, base_yield_loss: float, 
                         scenario: str) -> Dict[str, float]:
        """
        Simulate impact of intervention scenarios
        """
        scenarios = {
            'rainfall_increase': {
                'risk_reduction': 0.25,  # 25% risk reduction
                'yield_improvement': 0.30,
                'description': 'Rainfall +20%'
            },
            'temperature_decrease': {
                'risk_reduction': 0.15,  # 15% risk reduction
                'yield_improvement': 0.20,
                'description': 'Temperature -2°C'
            },
            'irrigation': {
                'risk_reduction': 0.35,  # 35% risk reduction
                'yield_improvement': 0.40,
                'description': 'Irrigation support'
            },
            'combined': {
                'risk_reduction': 0.50,  # 50% risk reduction
                'yield_improvement': 0.55,
                'description': 'Combined interventions'
            }
        }
        
        if scenario not in scenarios:
            return {
                'new_risk': base_risk,
                'new_yield_loss': base_yield_loss,
                'description': 'No scenario'
            }
        
        config = scenarios[scenario]
        new_risk = base_risk * (1 - config['risk_reduction'])
        new_yield_loss = base_yield_loss * (1 - config['yield_improvement'])
        
        return {
            'new_risk': round(new_risk, 2),
            'new_yield_loss': round(new_yield_loss, 2),
            'risk_reduction': round((base_risk - new_risk), 2),
            'yield_improvement': round((base_yield_loss - new_yield_loss), 2),
            'description': config['description']
        }
    
    @staticmethod
    def generate_recommendations(risk_score: float, top_drivers: List[Tuple[str, float]], 
                                time_to_impact: str) -> List[Dict[str, str]]:
        """
        Generate actionable recommendations based on risk profile
        """
        recommendations = []
        
        # Immediate interventions (high risk + short timeframe)
        if risk_score >= 70 and time_to_impact in ["< 7 days", "7-14 days"]:
            recommendations.append({
                'urgency': 'Immediate',
                'action': 'Deploy field officers for assessment',
                'timeframe': '0-3 days',
                'priority': 'Critical'
            })
            recommendations.append({
                'urgency': 'Immediate',
                'action': 'Activate emergency irrigation if available',
                'timeframe': '0-7 days',
                'priority': 'Critical'
            })
        
        # Short-term interventions (medium-high risk)
        if risk_score >= 40:
            # Check dominant driver
            if top_drivers and 'rainfall' in top_drivers[0][0]:
                recommendations.append({
                    'urgency': 'Short-term',
                    'action': 'Provide drought-resistant seed varieties',
                    'timeframe': '7-14 days',
                    'priority': 'High'
                })
            elif top_drivers and 'ndvi' in top_drivers[0][0]:
                recommendations.append({
                    'urgency': 'Short-term',
                    'action': 'Conduct pest/disease inspection',
                    'timeframe': '3-7 days',
                    'priority': 'High'
                })
        
        # Advisory (medium risk)
        if 30 <= risk_score < 70:
            recommendations.append({
                'urgency': 'Advisory',
                'action': 'Issue preventive farming advisories',
                'timeframe': '7-21 days',
                'priority': 'Medium'
            })
        
        # Monitoring (low risk or stable)
        if risk_score < 30 or time_to_impact == "> 30 days (Stable)":
            recommendations.append({
                'urgency': 'Monitor',
                'action': 'Continue regular satellite monitoring',
                'timeframe': 'Ongoing',
                'priority': 'Low'
            })
        
        return recommendations
    
    @staticmethod
    def calculate_impact_metrics(risk_score: float, yield_loss: float,
                                farm_area: float = 5.0,
                                avg_yield_per_ha: float = 2.5) -> Dict[str, float]:
        """
        Translate risk into policy-relevant metrics
        Assumptions: Average Rwanda farm, maize/bean cultivation
        """
        # Expected yield without stress
        expected_yield_tons = farm_area * avg_yield_per_ha
        
        # Yield loss in tons
        yield_loss_tons = expected_yield_tons * (yield_loss / 100)
        
        # Economic loss (USD) - approximate $400/ton for staple crops
        price_per_ton = 400
        economic_loss_usd = yield_loss_tons * price_per_ton
        
        # Food security impact - meals lost (assuming 0.5kg/meal)
        meals_lost = (yield_loss_tons * 1000) / 0.5
        
        return {
            'expected_yield_tons': round(expected_yield_tons, 2),
            'yield_loss_tons': round(yield_loss_tons, 2),
            'economic_loss_usd': round(economic_loss_usd, 2),
            'meals_lost': int(meals_lost),
            'farmers_affected': 1  # Per farm basis
        }

class SpatialAnalyzer:
    """Spatial hotspot detection and clustering"""
    
    @staticmethod
    def detect_hotspots(predictions: List[Dict], threshold: float = 60.0) -> Dict[str, List[Dict]]:
        """
        Detect geographic clusters of high-risk farms
        Group by region/district
        """
        hotspots = {}
        
        for pred in predictions:
            if pred['risk_score'] >= threshold:
                region = pred.get('region', 'Unknown')
                
                if region not in hotspots:
                    hotspots[region] = []
                
                hotspots[region].append({
                    'farm_id': pred['farm_id'],
                    'risk_score': pred['risk_score'],
                    'primary_driver': pred.get('primary_driver', 'Unknown')
                })
        
        return hotspots
    
    @staticmethod
    def categorize_hotspot_type(farms: List[Dict]) -> str:
        """Determine if hotspot is drought, disease, or heat-driven"""
        driver_counts = {}
        
        for farm in farms:
            driver = farm.get('primary_driver', 'Unknown')
            driver_counts[driver] = driver_counts.get(driver, 0) + 1
        
        if not driver_counts:
            return 'Unknown'
        
        dominant = max(driver_counts.items(), key=lambda x: x[1])
        return dominant[0]
