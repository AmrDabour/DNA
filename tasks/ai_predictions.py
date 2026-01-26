"""
AI Prediction Tasks
====================
Background tasks for Gemini AI-powered predictions.

These tasks handle:
- Physical characteristics prediction
- Disease risk assessment
- Full genetic report generation
"""
import logging
from typing import Dict, Any, Optional

from celery_app import async_task, CELERY_ENABLED

logger = logging.getLogger(__name__)


@async_task(name='tasks.ai_predictions.predict_physical_traits')
def predict_physical_traits_task(
    gender: str,
    population: str,
    patient_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate physical characteristics prediction using Gemini AI.
    
    Args:
        gender: Predicted gender (Male/Female)
        population: Population code (CEU, YRI, JPT, etc.)
        patient_id: Optional patient identifier
    
    Returns:
        Dict with physical trait predictions
    """
    logger.info(f"Predicting physical traits for: {gender}, {population}")
    
    try:
        from services import get_physical_characteristics
        
        # Create prediction input dicts
        gender_prediction = {"predicted": gender}
        ancestry_prediction = {"code": population}
        
        result = get_physical_characteristics(gender_prediction, ancestry_prediction)
        
        if result.get("success"):
            result["patient_id"] = patient_id
            logger.info(f"Physical traits prediction complete")
        else:
            logger.warning(f"Physical traits prediction failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Physical traits prediction error: {e}")
        return {"success": False, "error": str(e)}


@async_task(name='tasks.ai_predictions.predict_disease_risk')
def predict_disease_risk_task(
    gender: str,
    population: str,
    patient_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate disease risk assessment using Gemini AI.
    
    Args:
        gender: Predicted gender (Male/Female)
        population: Population code (CEU, YRI, JPT, etc.)
        patient_id: Optional patient identifier
    
    Returns:
        Dict with disease risk predictions
    """
    logger.info(f"Predicting disease risk for: {gender}, {population}")
    
    try:
        from services import get_genetic_disease_risk
        
        # Create prediction input dicts
        gender_prediction = {"predicted": gender}
        ancestry_prediction = {"code": population}
        
        result = get_genetic_disease_risk(gender_prediction, ancestry_prediction, patient_id)
        
        if result.get("success"):
            logger.info(f"Disease risk prediction complete: {len(result.get('diseases', []))} diseases")
        else:
            logger.warning(f"Disease risk prediction failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Disease risk prediction error: {e}")
        return {"success": False, "error": str(e)}


@async_task(name='tasks.ai_predictions.generate_full_report')
def generate_full_report_task(
    file_path: str,
    patient_id: Optional[str] = None,
    include_vep: bool = True
) -> Dict[str, Any]:
    """
    Generate a complete genetic analysis report.
    
    This task combines:
    1. ML-based gender prediction
    2. ML-based ancestry prediction
    3. AI physical characteristics prediction
    4. AI disease risk assessment
    5. Optional VEP functional annotation
    
    Args:
        file_path: Path to the SNP file
        patient_id: Optional patient identifier
        include_vep: Whether to include VEP annotation
    
    Returns:
        Dict with complete analysis report
    """
    logger.info(f"Generating full report for: {file_path}")
    
    try:
        import os
        import pandas as pd
        from ml_models import GeneticPredictor, find_model_directories
        
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        
        # Load the file
        df = pd.read_csv(file_path)
        
        # Initialize predictor
        predictor = GeneticPredictor()
        gender_model_dir, ancestry_model_dir = find_model_directories()
        
        report = {
            "success": True,
            "file_path": file_path,
            "patient_id": patient_id or df.get('Patient_ID', [None])[0] or "Unknown",
            "total_snps": len(df),
        }
        
        # Gender prediction
        if gender_model_dir and predictor.load_sex_predictor(gender_model_dir):
            gender_result = predictor.predict_sex(file_path)
            report["gender_prediction"] = gender_result
        else:
            report["gender_prediction"] = {"error": "Model not available"}
        
        # Ancestry prediction
        if ancestry_model_dir and predictor.load_ancestry_predictor(ancestry_model_dir):
            ancestry_result = predictor.predict_ancestry(file_path)
            report["ancestry_prediction"] = ancestry_result
        else:
            report["ancestry_prediction"] = {"error": "Model not available"}
        
        # Get gender and population for AI predictions
        gender = report.get("gender_prediction", {}).get("predicted", "Unknown")
        population = report.get("ancestry_prediction", {}).get("code", "Unknown")
        
        # Physical characteristics (AI)
        if gender != "Unknown" and population != "Unknown":
            physical_result = predict_physical_traits_task(gender, population, patient_id)
            report["physical_characteristics"] = physical_result
        
        # Disease risk (AI)
        if gender != "Unknown" and population != "Unknown":
            disease_result = predict_disease_risk_task(gender, population, patient_id)
            report["disease_risk"] = disease_result
        
        # VEP annotation
        if include_vep:
            from .snp_analysis import analyze_snp_file_task
            vep_result = analyze_snp_file_task(file_path, include_vep=True, vep_limit=100)
            report["vep_analysis"] = vep_result.get("vep_analysis", {})
        
        logger.info(f"Full report generated for: {report['patient_id']}")
        return report
        
    except Exception as e:
        logger.error(f"Full report generation error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# Helper functions for sync/async call pattern
# ============================================================

def predict_physical_traits(gender: str, population: str, **kwargs) -> Dict[str, Any]:
    """Predict physical traits - sync/async based on config"""
    if CELERY_ENABLED:
        return predict_physical_traits_task.delay(gender, population, **kwargs).get()
    else:
        return predict_physical_traits_task(gender, population, **kwargs)


def predict_disease_risk(gender: str, population: str, **kwargs) -> Dict[str, Any]:
    """Predict disease risk - sync/async based on config"""
    if CELERY_ENABLED:
        return predict_disease_risk_task.delay(gender, population, **kwargs).get()
    else:
        return predict_disease_risk_task(gender, population, **kwargs)


def generate_full_report(file_path: str, **kwargs) -> Dict[str, Any]:
    """Generate full report - sync/async based on config"""
    if CELERY_ENABLED:
        return generate_full_report_task.delay(file_path, **kwargs).get()
    else:
        return generate_full_report_task(file_path, **kwargs)

