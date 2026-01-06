"""
Enhanced Weather Data Fetcher - Multi-source integration
Fetches weather data from ERA5, NOAA, IBM EIS, and local stations
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.farm import Farm
from app.models.data import WeatherRecord
from app.services.weather_service import WeatherDataIntegrator, store_weather_data


def fetch_weather_for_all_farms(days_back: int = 7):
    """
    Fetch weather data for all farms in the system
    Integrates data from multiple sources
    """
    db: Session = SessionLocal()
    weather_integrator = WeatherDataIntegrator()
    
    try:
        # Get all farms
        farms = db.query(Farm).all()
        print(f"📡 Fetching weather data for {len(farms)} farms...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        total_records = 0
        
        for farm in farms:
            print(f"\n🌾 Processing Farm: {farm.name} (ID: {farm.id})")
            print(f"   Location: Lat {farm.latitude:.4f}, Lon {farm.longitude:.4f}")
            
            try:
                # Fetch integrated weather data
                weather_data = weather_integrator.integrate_multi_source_data(
                    lat=farm.latitude,
                    lon=farm.longitude,
                    start_date=start_date,
                    end_date=end_date,
                    station_id=None  # Add station ID if available in farm metadata
                )
                
                # Calculate disease risk factors
                risk_factors = weather_integrator.calculate_disease_risk_factors(weather_data)
                weather_data['disease_risk_factors'] = risk_factors
                
                # Store in database
                record = store_weather_data(
                    db=db,
                    weather_data=weather_data,
                    lat=farm.latitude,
                    lon=farm.longitude,
                    date=end_date
                )
                
                print(f"   ✓ Weather data stored (ID: {record.id})")
                print(f"     Temperature: {weather_data.get('temperature', 'N/A')}°C")
                print(f"     Humidity: {weather_data.get('humidity', 'N/A')}%")
                print(f"     Rainfall: {weather_data.get('rainfall', 'N/A')}mm")
                print(f"     Fungal Risk: {risk_factors.get('fungal_risk', 'N/A')}/100")
                
                total_records += 1
                
            except Exception as e:
                print(f"   ❌ Error fetching weather for farm {farm.id}: {e}")
                continue
        
        print(f"\n✅ Successfully fetched weather data for {total_records}/{len(farms)} farms")
        
    except Exception as e:
        print(f"❌ Fatal error in weather fetch: {e}")
    finally:
        db.close()


def fetch_weather_for_specific_farm(farm_id: int, days_back: int = 30):
    """
    Fetch historical weather data for a specific farm
    Useful for backfilling data
    """
    db: Session = SessionLocal()
    weather_integrator = WeatherDataIntegrator()
    
    try:
        farm = db.query(Farm).filter(Farm.id == farm_id).first()
        if not farm:
            print(f"❌ Farm {farm_id} not found")
            return
        
        print(f"📡 Fetching {days_back} days of weather data for {farm.name}...")
        
        end_date = datetime.now()
        
        # Fetch daily data
        for day in range(days_back):
            fetch_date = end_date - timedelta(days=day)
            
            try:
                weather_data = weather_integrator.integrate_multi_source_data(
                    lat=farm.latitude,
                    lon=farm.longitude,
                    start_date=fetch_date,
                    end_date=fetch_date
                )
                
                risk_factors = weather_integrator.calculate_disease_risk_factors(weather_data)
                weather_data['disease_risk_factors'] = risk_factors
                
                record = store_weather_data(
                    db=db,
                    weather_data=weather_data,
                    lat=farm.latitude,
                    lon=farm.longitude,
                    date=fetch_date
                )
                
                if day % 7 == 0:  # Progress update every 7 days
                    print(f"   ✓ Day -{day}: {fetch_date.strftime('%Y-%m-%d')} complete")
                
            except Exception as e:
                print(f"   ❌ Error on day -{day}: {e}")
                continue
        
        print(f"✅ Weather data fetch complete for {farm.name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


def fetch_weather_forecasts(forecast_days: int = 7):
    """
    Fetch weather forecasts for all farms
    Uses NOAA/ERA5/IBM forecast APIs
    """
    db: Session = SessionLocal()
    weather_integrator = WeatherDataIntegrator()
    
    try:
        from app.models.disease import WeatherForecast
        
        farms = db.query(Farm).all()
        print(f"🔮 Fetching {forecast_days}-day weather forecasts for {len(farms)} farms...")
        
        total_forecasts = 0
        
        for farm in farms:
            print(f"\n🌾 Farm: {farm.name}")
            
            for day_offset in range(1, forecast_days + 1):
                forecast_date = datetime.now().date()
                valid_date = forecast_date + timedelta(days=day_offset)
                
                try:
                    # In production, use actual forecast APIs
                    # For now, use integrated weather data as proxy
                    weather_data = weather_integrator.integrate_multi_source_data(
                        lat=farm.latitude,
                        lon=farm.longitude,
                        start_date=datetime.now(),
                        end_date=datetime.now() + timedelta(days=day_offset)
                    )
                    
                    # Calculate leaf wetness hours
                    humidity = weather_data.get('humidity', 70)
                    temp = weather_data.get('temperature', 20)
                    dewpoint = weather_data.get('dewpoint', temp - 5)
                    
                    if humidity > 90 or (temp - dewpoint) < 2:
                        leaf_wetness_hours = min(humidity / 100.0 * 24, 24)
                    else:
                        leaf_wetness_hours = max(0, (humidity - 80) / 20.0 * 12)
                    
                    # Store forecast
                    forecast = WeatherForecast(
                        location=f"Lat:{farm.latitude:.2f},Lon:{farm.longitude:.2f}",
                        forecast_date=forecast_date,
                        valid_date=valid_date,
                        forecast_horizon_hours=day_offset * 24,
                        temperature_min=weather_data.get('temperature', 20) - 3,
                        temperature_max=weather_data.get('temperature', 20) + 3,
                        temperature_mean=weather_data.get('temperature', 20),
                        humidity_min=max(40, weather_data.get('humidity', 70) - 10),
                        humidity_max=min(100, weather_data.get('humidity', 70) + 10),
                        humidity_mean=weather_data.get('humidity', 70),
                        rainfall_total=weather_data.get('rainfall', 0),
                        rainfall_probability=0.3 if weather_data.get('rainfall', 0) > 0 else 0.1,
                        wind_speed=weather_data.get('wind_speed', 3),
                        dewpoint=dewpoint,
                        leaf_wetness_hours=leaf_wetness_hours,
                        source='INTEGRATED',
                        confidence=max(0.5, 1.0 - (day_offset * 0.05))  # Confidence decreases with time
                    )
                    
                    db.add(forecast)
                    total_forecasts += 1
                    
                except Exception as e:
                    print(f"   ❌ Error for day +{day_offset}: {e}")
                    continue
            
            db.commit()
            print(f"   ✓ {forecast_days} forecasts stored")
        
        print(f"\n✅ Total forecasts created: {total_forecasts}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


def print_weather_summary():
    """Print summary of available weather data"""
    db: Session = SessionLocal()
    
    try:
        from sqlalchemy import func
        
        # Weather records
        record_count = db.query(func.count(WeatherRecord.id)).scalar()
        latest_record = db.query(WeatherRecord).order_by(WeatherRecord.date.desc()).first()
        
        print("\n📊 Weather Data Summary")
        print("=" * 50)
        print(f"Total weather records: {record_count}")
        
        if latest_record:
            print(f"Latest record date: {latest_record.date}")
            print(f"Latest temperature: {latest_record.temperature}°C")
            print(f"Latest rainfall: {latest_record.rainfall}mm")
        
        # Forecasts (if available)
        try:
            from app.models.disease import WeatherForecast
            forecast_count = db.query(func.count(WeatherForecast.id)).scalar()
            latest_forecast = db.query(WeatherForecast).order_by(WeatherForecast.created_at.desc()).first()
            
            print(f"\nTotal weather forecasts: {forecast_count}")
            if latest_forecast:
                print(f"Latest forecast valid date: {latest_forecast.valid_date}")
        except:
            print("\nNo forecast data available")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch weather data from multiple sources")
    parser.add_argument(
        "command",
        choices=['all', 'farm', 'forecasts', 'summary'],
        help="Command to execute"
    )
    parser.add_argument(
        "--farm-id",
        type=int,
        help="Farm ID for 'farm' command"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days (back for historical, forward for forecasts)"
    )
    
    args = parser.parse_args()
    
    if args.command == 'all':
        fetch_weather_for_all_farms(days_back=args.days)
    elif args.command == 'farm':
        if not args.farm_id:
            print("❌ --farm-id required for 'farm' command")
        else:
            fetch_weather_for_specific_farm(args.farm_id, days_back=args.days)
    elif args.command == 'forecasts':
        fetch_weather_forecasts(forecast_days=args.days)
    elif args.command == 'summary':
        print_weather_summary()
    
    print("\n✅ Done!")
