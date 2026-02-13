from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models.schemas import PredictionInput, PredictionResponse, ErrorResponse
from ..services.prediction_service import PredictionService
from ..core.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["prediction"])

@router.post("/stage", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
async def predict_stage(
    input_data: PredictionInput,
    db: Session = Depends(get_db)
):
    """
    Predict CKD stage, risk category and risk score for a patient.
    
    This endpoint takes clinical parameters (Age, Creatinine, Hb, etc.)
    and returns:
    - predicted_stage (1-5)
    - risk_category (LOW, MEDIUM, HIGH)
    - risk_score (0-100)
    - calculated indicators (eDFG, Cockcroft, IMC)
    """
    try:
        service = PredictionService(db)
        result = service.predict_stage(input_data)
        
        return PredictionResponse(
            success=True,
            message="Prediction successful",
            data=result
        )
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during prediction: {str(e)}"
        )
