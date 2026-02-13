"""
Health Check Routes
API endpoints for system health monitoring
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.database import get_db, engine
from ..core.config import settings
from ..services.prediction_service import PredictionService
from ..models.schemas import HealthCheck, APIResponse

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/", response_model=HealthCheck)
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check for the AI4CKD API.
    
    Returns system status including:
    - Overall status
    - API version
    - Database connectivity
    - Model loading status
    - Current timestamp
    """
    health_status = HealthCheck(
        status="healthy",
        version=settings.app_version,
        database_connected=False,
        model_loaded=False,
        timestamp=datetime.now()
    )
    
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_status.database_connected = True
    except Exception as e:
        health_status.status = "unhealthy"
        health_status.database_connected = False
    
    # Check model loading
    try:
        prediction_service = PredictionService(db)
        model_info = prediction_service.get_model_info()
        health_status.model_loaded = model_info.get("model_loaded", False)
        
        if not health_status.model_loaded:
            health_status.status = "degraded"
            
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Health check model loading error: {str(e)}")
        health_status.status = "unhealthy"
        health_status.model_loaded = False
    
    return health_status

@router.get("/database", response_model=APIResponse)
async def database_health_check(db: Session = Depends(get_db)):
    """
    Check database connectivity and basic operations.
    """
    try:
        # Test basic query
        result = db.execute(text("SELECT COUNT(*) as count")).fetchone()
        record_count = result[0] if result else 0
        
        # Test table existence
        tables_check = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = 'main' 
            AND table_name IN ('patients', 'predictions')
        """)).fetchone()
        
        table_count = tables_check[0] if tables_check else 0
        
        return APIResponse(
            success=True,
            message="Database is healthy",
            data={
                "record_count": record_count,
                "required_tables": table_count,
                "connection_status": "connected"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}"
        )

@router.get("/model", response_model=APIResponse)
async def model_health_check(db: Session = Depends(get_db)):
    """
    Check ML model status and performance.
    """
    try:
        prediction_service = PredictionService(db)
        model_info = prediction_service.get_model_info()
        
        # Test prediction with sample data
        from ..models.schemas import PredictionInput, Sex
        test_request = PredictionInput(
            age=50,
            sexe=Sex.MALE,
            poids=70,
            taille=1.75,
            creatinine=12,
            uree=0.3,
            hb=14,
            k=4.2
        )
        
        test_prediction = prediction_service.predict_stage(test_request)
        
        return APIResponse(
            success=True,
            message="Model is healthy",
            data={
                "model_info": model_info,
                "test_prediction": {
                    "predicted_stage": test_prediction.predicted_stage,
                    "risk_score": test_prediction.risk_score
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model health check failed: {str(e)}"
        )

@router.get("/system", response_model=APIResponse)
async def system_health_check():
    """
    Check system resources and configuration.
    """
    try:
        import psutil
        import os
        
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Configuration check
        config_checks = {
            "app_name": settings.app_name,
            "debug_mode": settings.debug
        }
        
        system_info = {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "configuration": config_checks
        }
        
        return APIResponse(
            success=True,
            message="System is healthy",
            data=system_info
        )
        
    except ImportError:
        # psutil not available
        return APIResponse(
            success=True,
            message="System check limited (psutil not available)",
            data={"configuration": {
                "app_name": settings.app_name,
                "debug_mode": settings.debug
            }}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"System health check failed: {str(e)}"
        )

@router.get("/ready", response_model=APIResponse)
async def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes-style readiness probe.
    Checks if the application is ready to serve traffic.
    """
    try:
        # Check database
        db.execute(text("SELECT 1"))
        
        # Check model
        prediction_service = PredictionService(db)
        model_info = prediction_service.get_model_info()
        
        if not model_info.get("model_loaded", False):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model not loaded"
            )
        
        return APIResponse(
            success=True,
            message="Application is ready"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Application not ready: {str(e)}"
        )

@router.get("/live", response_model=APIResponse)
async def liveness_check():
    """
    Kubernetes-style liveness probe.
    Checks if the application is running.
    """
    try:
        # Simple check - if we can respond, we're alive
        return APIResponse(
            success=True,
            message="Application is alive",
            data={"timestamp": datetime.now().isoformat()}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Liveness check failed: {str(e)}"
        )