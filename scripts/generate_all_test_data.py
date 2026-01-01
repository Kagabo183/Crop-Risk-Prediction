"""
Generate complete test data for all tables: farms, predictions, alerts
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
import random
from app.db.database import SessionLocal
from app.models.farm import Farm
from app.models.prediction import Prediction
from app.models.alert import Alert
from app.models.user import User
from sqlalchemy import text

def generate_farms(count=20):
    """Generate test farms across Rwanda"""
    db = SessionLocal()
    farms = []
    
    districts = ["Musanze", "Huye", "Karongi", "Nyagatare", "Rulindo", "Kayonza", "Rusizi", "Bugesera"]
    crop_types = ["Coffee", "Tea", "Maize", "Rice", "Cassava", "Sweet Potato", "Beans", "Banana"]
    
    print(f"\n🌾 Generating {count} test farms...")
    
    for i in range(count):
        farm = Farm(
            name=f"Farm {chr(65 + i % 26)}{i+1} - {random.choice(districts)}",
            location=f"{random.choice(districts)}, Rwanda",
            area=round(random.uniform(0.5, 50.0), 2),  # hectares
            owner_id=None
        )
        farms.append(farm)
    
    db.add_all(farms)
    db.commit()
    
    print(f"✓ Created {count} farms")
    db.close()
    return farms

def generate_predictions(count=50):
    """Generate test predictions for farms"""
    db = SessionLocal()
    
    # Get all farms
    farms = db.query(Farm).all()
    if not farms:
        print("⚠️  No farms found. Generate farms first.")
        db.close()
        return []
    
    print(f"\n📊 Generating {count} predictions...")
    
    predictions = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(count):
        farm = random.choice(farms)
        pred_date = base_date + timedelta(days=random.randint(0, 30))
        
        # Generate correlated risk metrics
        risk_score = round(random.uniform(0, 100), 2)
        yield_loss = round(risk_score * random.uniform(0.3, 0.8), 2)  # Correlated with risk
        
        disease_levels = ["Low", "Medium", "High", "Critical"]
        disease_risk = disease_levels[min(3, int(risk_score / 30))]
        
        prediction = Prediction(
            farm_id=farm.id,
            predicted_at=pred_date,
            risk_score=risk_score,
            yield_loss=yield_loss,
            disease_risk=disease_risk
        )
        predictions.append(prediction)
    
    db.add_all(predictions)
    db.commit()
    
    print(f"✓ Created {count} predictions")
    db.close()
    return predictions

def generate_alerts(count=30):
    """Generate test alerts"""
    db = SessionLocal()
    
    # Get all farms
    farms = db.query(Farm).all()
    if not farms:
        print("⚠️  No farms found. Generate farms first.")
        db.close()
        return []
    
    print(f"\n🚨 Generating {count} alerts...")
    
    alerts = []
    alert_levels = ["info", "warning", "critical"]
    alert_messages = {
        "info": [
            "Satellite data updated for your farm",
            "Weather forecast available for next week",
            "NDVI analysis completed successfully"
        ],
        "warning": [
            "Moderate drought risk detected",
            "Pest activity reported in nearby area",
            "Soil moisture below optimal level"
        ],
        "critical": [
            "High disease risk detected - immediate action required",
            "Severe drought conditions expected",
            "Critical pest infestation warning"
        ]
    }
    
    base_date = datetime.now() - timedelta(days=14)
    
    for i in range(count):
        farm = random.choice(farms)
        alert_date = base_date + timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))
        level = random.choice(alert_levels)
        
        alert = Alert(
            farm_id=farm.id,
            level=level,
            message=random.choice(alert_messages[level]),
            created_at=alert_date
        )
        alerts.append(alert)
    
    db.add_all(alerts)
    db.commit()
    
    print(f"✓ Created {count} alerts")
    db.close()
    return alerts

def show_summary():
    """Display summary of generated data"""
    db = SessionLocal()
    
    farm_count = db.query(Farm).count()
    pred_count = db.query(Prediction).count()
    alert_count = db.query(Alert).count()
    
    # Get satellite image count
    result = db.execute(text("SELECT COUNT(*) FROM satellite_images"))
    sat_count = result.scalar()
    
    print("\n" + "="*50)
    print("📈 DATABASE SUMMARY")
    print("="*50)
    print(f"Farms:             {farm_count}")
    print(f"Predictions:       {pred_count}")
    print(f"Alerts:            {alert_count}")
    print(f"Satellite Images:  {sat_count}")
    print("="*50)
    
    # Show recent predictions
    recent_preds = db.query(Prediction).order_by(Prediction.predicted_at.desc()).limit(5).all()
    if recent_preds:
        print("\n📊 Recent Predictions:")
        for pred in recent_preds:
            print(f"  • Farm {pred.farm_id} | {pred.predicted_at.date()} | Risk: {pred.risk_score}% | Yield Loss: {pred.yield_loss}%")
    
    # Show recent alerts
    recent_alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(5).all()
    if recent_alerts:
        print("\n🚨 Recent Alerts:")
        for alert in recent_alerts:
            print(f"  • [{alert.level.upper()}] {alert.message}")
    
    db.close()

if __name__ == "__main__":
    print("🚀 Generating Complete Test Dataset")
    print("="*50)
    
    try:
        # Generate all test data
        generate_farms(20)
        generate_predictions(50)
        generate_alerts(30)
        
        # Show summary
        show_summary()
        
        print("\n✅ Test data generation complete!")
        print("\n💡 Next steps:")
        print("  1. Refresh your frontend dashboard")
        print("  2. Navigate to different pages (Farms, Predictions, Alerts)")
        print("  3. Explore the generated data")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
