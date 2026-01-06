"""
Example integration of disease prediction system into main.py
"""

# Add this to your main.py file to enable disease prediction endpoints

from fastapi import FastAPI
from app.api.v1 import api_router
from app.core.config import Settings

settings = Settings()
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Include the disease prediction API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Example startup event to initialize disease catalog
@app.on_event("startup")
async def startup_event():
    """Initialize disease catalog on startup if not exists"""
    from app.db.database import SessionLocal
    from app.models.disease import Disease
    
    db = SessionLocal()
    try:
        # Check if diseases are already initialized
        disease_count = db.query(Disease).count()
        if disease_count == 0:
            print("🔬 Initializing disease catalog...")
            # Run initialization script
            import subprocess
            subprocess.run([
                "python", 
                "scripts/generate_disease_predictions.py", 
                "init"
            ])
            print("✅ Disease catalog initialized")
        else:
            print(f"✅ Disease catalog loaded: {disease_count} diseases")
    finally:
        db.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "features": {
            "disease_prediction": True,
            "weather_integration": True,
            "forecasting": True
        }
    }

# API documentation will be available at:
# http://localhost:8000/docs
# http://localhost:8000/redoc
