import pydantic
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

class BaseSchema(BaseModel):
    """Base schema for all API models."""
    class Config:
        from_attributes = True
        extra = "ignore"

class CKDStage(str, Enum):
    """CKD stages enumeration."""
    STAGE_1 = "1"
    STAGE_2 = "2"
    STAGE_3a = "3a"
    STAGE_3b = "3b"
    STAGE_4 = "4"
    STAGE_5 = "5"

class RiskCategory(str, Enum):
    """CKD risk enumeration."""
    RISK_LOW = "LOW"
    RISK_MEDIUM = "MEDIUM"
    RISK_HIGH = "HIGH"

class Sex(str, Enum):
    MALE = "M"
    FEMALE = "F"

# --- Common Response Schemas ---

class APIResponse(BaseSchema):
    """Generic API response schema."""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseSchema):
    """Error response schema."""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# --- Prediction Schemas ---

class PredictionInput(BaseSchema):
    """Schema for prediction input data."""
    age: float = Field(..., ge=1, le=120, description="Âge du patient (ans)")
    sexe: Sex = Field(..., description="Sexe (M/F)")
    poids: float = Field(..., ge=10, le=250, description="Poids (kg)")
    taille: float = Field(..., ge=0.5, le=2.5, description="Taille (m)")
    creatinine: float = Field(..., ge=1, le=250, description="Créatinine (mg/L)")
    uree: float = Field(..., ge=0.05, le=5.0, description="Urée (g/L)")
    hb: float = Field(..., ge=3, le=22, description="Hémoglobine (g/dL)")
    k: float = Field(..., ge=1, le=10, description="Potassium (meq/L)")

class PredictionOutputData(BaseSchema):
    """Schema for the actual prediction result data."""
    predicted_stage: str
    risk_category: RiskCategory
    risk_score: float = Field(..., ge=0, le=100)
    calculated_indicators: Dict[str, float]

class PredictionResponse(APIResponse):
    """Schema for the prediction response."""
    data: PredictionOutputData

# --- Health Check Schema ---

class HealthCheck(BaseSchema):
    """Health check response schema."""
    status: str
    version: str
    database_connected: bool
    model_loaded: bool
    timestamp: datetime = Field(default_factory=datetime.now)