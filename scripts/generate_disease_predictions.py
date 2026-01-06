"""
Generate disease predictions for all farms using pathogen-specific models
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.farm import Farm
from app.models.disease import Disease, DiseasePrediction
from app.services.disease_intelligence import DiseaseModelEngine, ShortTermForecastEngine
from app.services.weather_service import WeatherDataIntegrator


def initialize_disease_catalog(db: Session):
    """
    Initialize disease catalog with research-backed models
    """
    diseases_data = [
        {
            'name': 'Late Blight',
            'scientific_name': 'Phytophthora infestans',
            'pathogen_type': 'fungal',
            'primary_crops': ['potato', 'tomato'],
            'optimal_temp_min': 10.0,
            'optimal_temp_max': 25.0,
            'optimal_humidity_min': 90.0,
            'required_leaf_wetness_hours': 11.0,
            'incubation_period_days': 5,
            'severity_potential': 'severe',
            'spread_rate': 'fast',
            'symptoms': 'Water-soaked lesions on leaves, white fungal growth on undersides, rapid tissue death',
            'management_practices': ['Use resistant varieties', 'Apply fungicides preventively', 'Improve air circulation', 'Remove infected plants'],
            'research_source': 'Cornell University',
            'model_type': 'mechanistic'
        },
        {
            'name': 'Septoria Leaf Spot',
            'scientific_name': 'Septoria lycopersici',
            'pathogen_type': 'fungal',
            'primary_crops': ['tomato'],
            'optimal_temp_min': 15.0,
            'optimal_temp_max': 27.0,
            'optimal_humidity_min': 80.0,
            'required_leaf_wetness_hours': 6.0,
            'incubation_period_days': 7,
            'severity_potential': 'high',
            'spread_rate': 'moderate',
            'symptoms': 'Small circular spots with gray centers and dark borders on lower leaves',
            'management_practices': ['Remove lower leaves', 'Apply fungicides', 'Avoid overhead irrigation', 'Mulch to prevent splash'],
            'research_source': 'Ohio State University',
            'model_type': 'statistical'
        },
        {
            'name': 'Powdery Mildew',
            'scientific_name': 'Erysiphales',
            'pathogen_type': 'fungal',
            'primary_crops': ['wheat', 'tomato', 'cucumber', 'squash'],
            'optimal_temp_min': 15.0,
            'optimal_temp_max': 22.0,
            'optimal_humidity_min': 50.0,
            'required_leaf_wetness_hours': 0.0,  # Doesn't require free water
            'incubation_period_days': 5,
            'severity_potential': 'moderate',
            'spread_rate': 'fast',
            'symptoms': 'White powdery coating on leaves, stems, and fruits',
            'management_practices': ['Improve air circulation', 'Apply sulfur fungicides', 'Use resistant varieties', 'Remove infected leaves'],
            'research_source': 'University Extension Programs',
            'model_type': 'mechanistic'
        },
        {
            'name': 'Bacterial Spot',
            'scientific_name': 'Xanthomonas spp.',
            'pathogen_type': 'bacterial',
            'primary_crops': ['tomato', 'pepper'],
            'optimal_temp_min': 24.0,
            'optimal_temp_max': 30.0,
            'optimal_humidity_min': 85.0,
            'required_leaf_wetness_hours': 3.0,
            'incubation_period_days': 7,
            'severity_potential': 'high',
            'spread_rate': 'fast',
            'symptoms': 'Small dark brown spots on leaves, stems, and fruit',
            'management_practices': ['Use disease-free seeds', 'Apply copper bactericides', 'Avoid overhead irrigation', 'Practice crop rotation'],
            'research_source': 'University of Florida',
            'model_type': 'mechanistic'
        },
        {
            'name': 'Fusarium Wilt',
            'scientific_name': 'Fusarium oxysporum',
            'pathogen_type': 'fungal',
            'primary_crops': ['tomato', 'banana', 'cotton'],
            'optimal_temp_min': 27.0,
            'optimal_temp_max': 32.0,
            'optimal_humidity_min': 60.0,
            'incubation_period_days': 14,
            'severity_potential': 'severe',
            'spread_rate': 'slow',
            'symptoms': 'Yellowing of lower leaves, wilting on one side of plant, vascular discoloration',
            'management_practices': ['Use resistant varieties', 'Soil solarization', 'Crop rotation', 'Maintain soil pH 6.5-7.0'],
            'research_source': 'Multiple University Sources',
            'model_type': 'mechanistic'
        }
    ]
    
    print("🔬 Initializing disease catalog...")
    
    for disease_data in diseases_data:
        existing = db.query(Disease).filter(Disease.name == disease_data['name']).first()
        
        if not existing:
            disease = Disease(**disease_data)
            db.add(disease)
            print(f"   ✓ Added: {disease_data['name']}")
        else:
            print(f"   - Already exists: {disease_data['name']}")
    
    db.commit()
    print("✅ Disease catalog initialized\n")


def generate_disease_predictions_for_farm(
    farm_id: int,
    db: Session,
    diseases: list = None
):
    """
    Generate disease predictions for a specific farm
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        print(f"❌ Farm {farm_id} not found")
        return
    
    print(f"\n🌾 Generating disease predictions for: {farm.name}")
    print(f"   Location: Lat {farm.latitude:.4f}, Lon {farm.longitude:.4f}")
    
    # Get weather data
    weather_integrator = WeatherDataIntegrator()
    weather_data = weather_integrator.integrate_multi_source_data(
        lat=farm.latitude,
        lon=farm.longitude,
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now()
    )
    
    # Calculate disease risk factors
    disease_risk_factors = weather_integrator.calculate_disease_risk_factors(weather_data)
    weather_data['disease_risk_factors'] = disease_risk_factors
    
    print(f"   Weather: {weather_data.get('temperature', 'N/A')}°C, {weather_data.get('humidity', 'N/A')}% humidity")
    
    # Get diseases to predict
    if diseases is None:
        diseases = db.query(Disease).all()
    
    disease_engine = DiseaseModelEngine()
    predictions_created = 0
    
    for disease in diseases:
        try:
            # Get disease-specific prediction
            disease_name_lower = disease.name.lower()
            
            if 'late blight' in disease_name_lower:
                disease_pred = disease_engine.predict_late_blight(weather_data)
            elif 'septoria' in disease_name_lower:
                disease_pred = disease_engine.predict_septoria_leaf_spot(weather_data)
            elif 'powdery mildew' in disease_name_lower:
                disease_pred = disease_engine.predict_powdery_mildew(weather_data)
            elif 'bacterial spot' in disease_name_lower:
                disease_pred = disease_engine.predict_bacterial_spot(weather_data)
            elif 'fusarium' in disease_name_lower:
                disease_pred = disease_engine.predict_fusarium_wilt(weather_data)
            else:
                continue
            
            # Store prediction
            prediction = DiseasePrediction(
                farm_id=farm.id,
                disease_id=disease.id,
                prediction_date=datetime.now().date(),
                forecast_horizon='current',
                risk_score=disease_pred['risk_score'],
                risk_level=disease_pred['risk_level'],
                infection_probability=disease_pred.get('infection_probability', 0.5),
                days_to_symptom_onset=disease_pred.get('days_to_symptoms'),
                weather_risk_score=disease_pred['risk_score'],
                risk_factors=disease_risk_factors,
                weather_conditions=weather_data,
                model_version='v1.0',
                confidence_score=85.0,
                action_threshold_reached=disease_pred['risk_score'] >= 60,
                recommended_actions=disease_pred.get('recommended_actions', []),
                treatment_window=disease_pred.get('action_threshold'),
                estimated_yield_loss_pct=min(disease_pred['risk_score'] / 2, 50)
            )
            
            db.add(prediction)
            predictions_created += 1
            
            # Print summary
            risk_icon = "🔴" if disease_pred['risk_level'] in ['high', 'severe'] else "🟡" if disease_pred['risk_level'] == 'moderate' else "🟢"
            print(f"   {risk_icon} {disease.name}: {disease_pred['risk_score']:.1f}/100 ({disease_pred['risk_level']})")
            
        except Exception as e:
            print(f"   ❌ Error predicting {disease.name}: {e}")
            continue
    
    db.commit()
    print(f"   ✅ Created {predictions_created} predictions\n")


def generate_predictions_for_all_farms(db: Session):
    """
    Generate disease predictions for all farms
    """
    farms = db.query(Farm).all()
    print(f"🔮 Generating disease predictions for {len(farms)} farms...\n")
    
    for farm in farms:
        try:
            generate_disease_predictions_for_farm(farm.id, db)
        except Exception as e:
            print(f"❌ Error for farm {farm.id}: {e}\n")
            continue
    
    print("✅ All predictions generated!")


def generate_weekly_forecasts(farm_id: int, db: Session):
    """
    Generate 7-day disease forecasts for a farm
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        print(f"❌ Farm {farm_id} not found")
        return
    
    print(f"\n📅 Generating 7-day forecasts for: {farm.name}")
    
    forecast_engine = ShortTermForecastEngine()
    diseases = db.query(Disease).all()
    
    for disease in diseases[:3]:  # Limit to top 3 diseases for demo
        try:
            weekly_summary = forecast_engine.generate_weekly_summary(
                farm,
                disease.name,
                db
            )
            
            print(f"\n{disease.name}:")
            print(f"  Weekly Risk: {weekly_summary['weekly_risk_level']}")
            print(f"  Average Score: {weekly_summary['average_risk_score']:.1f}/100")
            print(f"  Peak Risk Day: {weekly_summary['peak_risk_day']}")
            print(f"  Critical Days: {weekly_summary['critical_action_days']}")
            print(f"  Strategy: {weekly_summary['recommended_strategy']}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")


def print_prediction_summary(db: Session):
    """Print summary of disease predictions"""
    from sqlalchemy import func
    
    total_predictions = db.query(func.count(DiseasePrediction.id)).scalar()
    
    if total_predictions == 0:
        print("\n❌ No predictions found. Run with 'all' or 'farm' command first.")
        return
    
    # Risk level distribution
    risk_levels = db.query(
        DiseasePrediction.risk_level,
        func.count(DiseasePrediction.id)
    ).group_by(DiseasePrediction.risk_level).all()
    
    # High risk farms
    high_risk = db.query(DiseasePrediction).filter(
        DiseasePrediction.risk_level.in_(['high', 'severe'])
    ).count()
    
    print("\n📊 Disease Prediction Summary")
    print("=" * 50)
    print(f"Total predictions: {total_predictions}")
    print(f"\nRisk Distribution:")
    for level, count in risk_levels:
        print(f"  {level}: {count}")
    print(f"\n🚨 High/Severe risk alerts: {high_risk}")
    
    # Recent predictions
    recent = db.query(DiseasePrediction).order_by(
        DiseasePrediction.predicted_at.desc()
    ).limit(5).all()
    
    print(f"\nRecent Predictions:")
    for pred in recent:
        disease = db.query(Disease).filter(Disease.id == pred.disease_id).first()
        farm = db.query(Farm).filter(Farm.id == pred.farm_id).first()
        print(f"  {farm.name} - {disease.name}: {pred.risk_score:.1f}/100 ({pred.risk_level})")
    
    print("=" * 50)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate disease predictions")
    parser.add_argument(
        "command",
        choices=['init', 'all', 'farm', 'forecast', 'summary'],
        help="Command to execute"
    )
    parser.add_argument(
        "--farm-id",
        type=int,
        help="Farm ID for 'farm' or 'forecast' commands"
    )
    
    args = parser.parse_args()
    
    db = SessionLocal()
    
    try:
        if args.command == 'init':
            initialize_disease_catalog(db)
        elif args.command == 'all':
            generate_predictions_for_all_farms(db)
        elif args.command == 'farm':
            if not args.farm_id:
                print("❌ --farm-id required for 'farm' command")
            else:
                generate_disease_predictions_for_farm(args.farm_id, db)
        elif args.command == 'forecast':
            if not args.farm_id:
                print("❌ --farm-id required for 'forecast' command")
            else:
                generate_weekly_forecasts(args.farm_id, db)
        elif args.command == 'summary':
            print_prediction_summary(db)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n✅ Done!")
