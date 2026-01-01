from fastapi import APIRouter
from app.api.v1.endpoints import users, predictions, farms, alerts, auth, features, satellite, predict, satellite_images

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(farms.router, prefix="/farms", tags=["farms"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(features.router, prefix="/features", tags=["features"])
api_router.include_router(satellite.router, prefix="/satellite", tags=["satellite"])
api_router.include_router(satellite_images.router, prefix="/satellite-images", tags=["satellite-images"])
api_router.include_router(predict.router, prefix="/predict", tags=["predict"])
