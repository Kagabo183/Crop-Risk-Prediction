"""
API v1 router initialization
Includes disease prediction endpoints
"""
from fastapi import APIRouter
from app.api.v1 import diseases

api_router = APIRouter()

# Include disease prediction routes
api_router.include_router(diseases.router)

# Add other routers here as needed
# api_router.include_router(farms.router)
# api_router.include_router(predictions.router)
# api_router.include_router(alerts.router)
