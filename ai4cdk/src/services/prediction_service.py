import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any
from ..models.schemas import PredictionInput, PredictionOutputData, RiskCategory
from sqlalchemy.orm import Session

class PredictionService:
    def __init__(self, db: Session = None):
        self.db = db
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.model_path = os.path.join(self.base_dir, "assets", "renal_stacking_pipeline_v3.joblib")
        self.encoder_path = os.path.join(self.base_dir, "assets", "label_encoder_v3.joblib")
        
        # Load artifacts
        try:
            self.pipeline = joblib.load(self.model_path)
            self.label_encoder = joblib.load(self.encoder_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load model artifacts: {e}")

        self.feature_names = [
            'eDFG_CKD_EPI', 'Clairance_Cockcroft', 'Gap_Formules', 'Score_Echo_Total', 
            'Ratio_K_Hb', 'Ratio_Uree_Creat', 'Score_Surcharge_Bio',
            'Syndrome_Anemique', 'Pression_Pulsee', 'IMC', 'Age',
            'Interaction_eDFG_Hb', 'eDFG_Norm_Age', 'Creat_Norm_Age', 
            'Score_Anemie_Renale', 'Interaction_IMC_eDFG'
        ]

    def _calculate_edfg(self, creat, age, is_male):
        creat_mg_dl = creat / 10.0
        if is_male:
            kappa, alpha = 0.9, -0.302
            gender_mult = 1.0
        else:
            kappa, alpha = 0.7, -0.241
            gender_mult = 1.012
        return 142 * min(creat_mg_dl / kappa, 1)**alpha * \
               max(creat_mg_dl / kappa, 1)**-1.200 * \
               0.9938**age * gender_mult

    def _calculate_risk_score(self, stage_label, age, edfg, creatinine):
        """
        Custom risk score calculation (0-100) based on medical factors.
        """
        # Base score from stage
        stage_base = {
            "1": 10, "2": 25, "3a": 45, "3b": 60, "4": 80, "5": 95
        }
        score = stage_base.get(stage_label, 50)
        
        # Adjust based on Age (higher age + low eDFG = higher risk)
        if age > 65 and edfg < 45:
            score += 5
            
        # Adjust based on Creatinine levels
        if creatinine > 50:
            score += 5
            
        return min(max(score, 0), 100)

    def predict_stage(self, input_data: PredictionInput) -> PredictionOutputData:
        # 1. Feature Engineering
        creat_mg_dl = input_data.creatinine / 10.0
        is_male = input_data.sexe == "M"
        
        edfg = self._calculate_edfg(input_data.creatinine, input_data.age, is_male)
        cockcroft = ((140 - input_data.age) * input_data.poids) / (72 * creat_mg_dl) * (1.0 if is_male else 0.85)
        imc = input_data.poids / (input_data.taille**2)
        
        features = {
            'eDFG_CKD_EPI': edfg,
            'Clairance_Cockcroft': cockcroft,
            'Gap_Formules': abs(edfg - cockcroft),
            'Score_Echo_Total': 2.0,
            'Ratio_K_Hb': input_data.k / (input_data.hb + 0.1),
            'Ratio_Uree_Creat': input_data.uree / (creat_mg_dl + 0.1),
            'Score_Surcharge_Bio': (input_data.k > 5.0) + (input_data.uree > 0.5),
            'Syndrome_Anemique': 1 if input_data.hb < 12 else 0,
            'Pression_Pulsee': 45.0,
            'IMC': imc,
            'Age': input_data.age,
            'Interaction_eDFG_Hb': edfg * (input_data.hb + 0.1),
            'eDFG_Norm_Age': edfg / (input_data.age + 1),
            'Creat_Norm_Age': creat_mg_dl * (input_data.age + 1) / 100.0,
            'Score_Anemie_Renale': (input_data.hb + 0.1) * edfg / 100.0,
            'Interaction_IMC_eDFG': imc * edfg / 100.0
        }
        
        df_features = pd.DataFrame([features])[self.feature_names]
        
        # 2. Prediction
        pred_idx = self.pipeline.predict(df_features)[0]
        stage_label = self.label_encoder.inverse_transform([pred_idx])[0]
        
        # 3. Risk Calculation
        risk_score = self._calculate_risk_score(stage_label, input_data.age, edfg, input_data.creatinine)
        
        if risk_score < 40:
            category = RiskCategory.RISK_LOW
        elif risk_score < 70:
            category = RiskCategory.RISK_MEDIUM
        else:
            category = RiskCategory.RISK_HIGH
            
        return PredictionOutputData(
            predicted_stage=stage_label,
            risk_category=category,
            risk_score=float(risk_score),
            calculated_indicators={
                "eDFG": round(float(edfg), 2),
                "Cockcroft": round(float(cockcroft), 2),
                "IMC": round(float(imc), 2)
            }
        )

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_loaded": True,
            "features_count": len(self.feature_names),
            "target_classes": list(self.label_encoder.classes_)
        }
