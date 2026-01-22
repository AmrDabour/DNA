"""
Prediction Routes - REST API for ML Predictions
Prediction Service Microservice
"""
from flask import Blueprint, request, jsonify
from functools import wraps
import os
import sys
import pandas as pd
import numpy as np
import json
from datetime import datetime

prediction_bp = Blueprint('prediction', __name__)


# ============================================================
# Utility Functions
# ============================================================

def convert_to_serializable(obj):
    """Convert numpy types to JSON serializable types"""
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    return obj


def load_predictor(predictor_type):
    """Load predictor from app context"""
    from flask import current_app
    
    if predictor_type == 'gender':
        return getattr(current_app, 'gender_predictor', None)
    elif predictor_type == 'ancestry':
        return getattr(current_app, 'ancestry_predictor', None)
    return None


# Population Information
POPULATION_INFO = {
    "ASW": {"code": "A", "description": "African ancestry in Southwest USA"},
    "CEU": {"code": "C", "description": "Utah residents with Northern and Western European ancestry"},
    "CHB": {"code": "H", "description": "Han Chinese in Beijing, China"},
    "CHD": {"code": "D", "description": "Chinese in Metropolitan Denver, Colorado"},
    "GIH": {"code": "G", "description": "Gujarati Indians in Houston, Texas"},
    "JPT": {"code": "J", "description": "Japanese in Tokyo, Japan"},
    "LWK": {"code": "L", "description": "Luhya in Webuye, Kenya"},
    "MEX": {"code": "M", "description": "Mexican ancestry in Los Angeles, California"},
    "MKK": {"code": "K", "description": "Maasai in Kinyawa, Kenya"},
    "TSI": {"code": "T", "description": "Tuscan in Italy"},
    "YRI": {"code": "Y", "description": "Yoruban in Ibadan, Nigeria"},
}


# ============================================================
# Gender Prediction Endpoints
# ============================================================

@prediction_bp.route('/api/predictions/gender', methods=['POST'])
def predict_gender():
    """
    Predict gender from genetic data
    
    POST /api/predictions/gender
    Body: {"sample_id": "...", "data": {...}} or file upload
    
    Returns: {"success": true, "prediction": {...}}
    """
    try:
        # Get predictor
        from app import gender_predictor
        
        if gender_predictor is None:
            return jsonify({
                "success": False,
                "error": "Gender prediction model not loaded"
            }), 503
        
        data = request.get_json() or {}
        sample_id = data.get('sample_id')
        
        if sample_id:
            # Predict by sample ID (from training data)
            prediction, pred_label, true_sex, true_label = gender_predictor.predict_by_id(sample_id)
            
            if prediction is None:
                return jsonify({
                    "success": False,
                    "error": f"Sample ID '{sample_id}' not found"
                }), 404
            
            result = {
                "success": True,
                "prediction": {
                    "sample_id": sample_id,
                    "predicted_gender": pred_label,
                    "predicted_code": int(prediction),
                    "true_gender": true_label,
                    "true_code": int(true_sex) if true_sex else None,
                    "correct": prediction == true_sex if true_sex else None
                }
            }
            
            return jsonify(convert_to_serializable(result)), 200
        
        # For raw data prediction (future feature)
        return jsonify({
            "success": False,
            "error": "Please provide sample_id or upload genetic data"
        }), 400
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@prediction_bp.route('/api/predictions/gender/accuracy', methods=['GET'])
def get_gender_accuracy():
    """
    Get gender prediction model accuracy statistics
    
    GET /api/predictions/gender/accuracy
    
    Returns: {"success": true, "accuracy": {...}}
    """
    try:
        from app import gender_predictor
        
        if gender_predictor is None:
            return jsonify({
                "success": False,
                "error": "Gender prediction model not loaded"
            }), 503
        
        accuracy_stats = gender_predictor.analyze_prediction_accuracy()
        
        if accuracy_stats is None:
            return jsonify({
                "success": False,
                "error": "Could not calculate accuracy statistics"
            }), 500
        
        return jsonify({
            "success": True,
            "accuracy": convert_to_serializable(accuracy_stats)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@prediction_bp.route('/api/predictions/gender/visualization', methods=['GET'])
def get_gender_visualization():
    """
    Get gender prediction visualization (base64 encoded image)
    
    GET /api/predictions/gender/visualization
    
    Returns: {"success": true, "image": "base64..."}
    """
    try:
        from app import gender_predictor
        
        if gender_predictor is None:
            return jsonify({
                "success": False,
                "error": "Gender prediction model not loaded"
            }), 503
        
        # Generate visualization
        image_data = gender_predictor.generate_visualization(save_to_plots=False)
        
        if image_data is None:
            return jsonify({
                "success": False,
                "error": "Could not generate visualization"
            }), 500
        
        return jsonify({
            "success": True,
            "image": image_data,
            "format": "png",
            "encoding": "base64"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# Ancestry Prediction Endpoints
# ============================================================

@prediction_bp.route('/api/predictions/ancestry', methods=['POST'])
def predict_ancestry():
    """
    Predict ancestry/population from genetic data
    
    POST /api/predictions/ancestry
    Body: {"sample_id": "..."} or file upload
    
    Returns: {"success": true, "prediction": {...}}
    """
    try:
        from app import ancestry_predictor
        
        if ancestry_predictor is None:
            return jsonify({
                "success": False,
                "error": "Ancestry prediction model not loaded"
            }), 503
        
        data = request.get_json() or {}
        sample_id = data.get('sample_id')
        
        if sample_id:
            # Predict by sample ID
            prediction, pred_label, true_ancestry, true_label = ancestry_predictor.predict_by_id(sample_id)
            
            if prediction is None:
                return jsonify({
                    "success": False,
                    "error": f"Sample ID '{sample_id}' not found"
                }), 404
            
            # Get population info
            pop_info = POPULATION_INFO.get(pred_label, {})
            
            result = {
                "success": True,
                "prediction": {
                    "sample_id": sample_id,
                    "predicted_ancestry": pred_label,
                    "predicted_description": pop_info.get("description", "Unknown"),
                    "true_ancestry": true_label,
                    "correct": pred_label == true_label if true_label else None
                }
            }
            
            return jsonify(convert_to_serializable(result)), 200
        
        return jsonify({
            "success": False,
            "error": "Please provide sample_id"
        }), 400
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@prediction_bp.route('/api/predictions/ancestry/accuracy', methods=['GET'])
def get_ancestry_accuracy():
    """
    Get ancestry prediction model accuracy statistics
    
    GET /api/predictions/ancestry/accuracy
    
    Returns: {"success": true, "accuracy": {...}}
    """
    try:
        from app import ancestry_predictor
        
        if ancestry_predictor is None:
            return jsonify({
                "success": False,
                "error": "Ancestry prediction model not loaded"
            }), 503
        
        accuracy_stats = ancestry_predictor.analyze_prediction_accuracy()
        
        if accuracy_stats is None:
            return jsonify({
                "success": False,
                "error": "Could not calculate accuracy statistics"
            }), 500
        
        return jsonify({
            "success": True,
            "accuracy": convert_to_serializable(accuracy_stats)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# Combined Prediction Endpoint
# ============================================================

@prediction_bp.route('/api/predictions/combined', methods=['POST'])
def predict_combined():
    """
    Run both gender and ancestry predictions
    
    POST /api/predictions/combined
    Body: {"sample_id": "..."}
    
    Returns: {"success": true, "predictions": {...}}
    """
    try:
        from app import gender_predictor, ancestry_predictor
        
        data = request.get_json() or {}
        sample_id = data.get('sample_id')
        
        if not sample_id:
            return jsonify({
                "success": False,
                "error": "sample_id is required"
            }), 400
        
        result = {
            "success": True,
            "sample_id": sample_id,
            "timestamp": datetime.utcnow().isoformat(),
            "predictions": {}
        }
        
        # Gender prediction
        if gender_predictor:
            prediction, pred_label, true_sex, true_label = gender_predictor.predict_by_id(sample_id)
            if prediction is not None:
                result["predictions"]["gender"] = {
                    "predicted": pred_label,
                    "predicted_code": int(prediction),
                    "true": true_label,
                    "true_code": int(true_sex) if true_sex else None,
                    "correct": prediction == true_sex if true_sex else None
                }
        
        # Ancestry prediction
        if ancestry_predictor:
            # AncestryPredictor returns (predicted_pop, true_pop) - only 2 values
            ancestry_result = ancestry_predictor.predict_by_id(sample_id)
            if ancestry_result and ancestry_result[0] is not None:
                pred_label = ancestry_result[0]
                true_label = ancestry_result[1] if len(ancestry_result) > 1 else None
                pop_info = POPULATION_INFO.get(pred_label, {})
                result["predictions"]["ancestry"] = {
                    "predicted": pred_label,
                    "description": pop_info.get("description", "Unknown"),
                    "true": true_label,
                    "correct": pred_label == true_label if true_label else None
                }
        
        if not result["predictions"]:
            return jsonify({
                "success": False,
                "error": f"Sample ID '{sample_id}' not found in any model"
            }), 404
        
        return jsonify(convert_to_serializable(result)), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# Sample Management Endpoints
# ============================================================

@prediction_bp.route('/api/predictions/samples', methods=['GET'])
def list_available_samples():
    """
    List available sample IDs for prediction
    
    GET /api/predictions/samples?limit=10
    
    Returns: {"success": true, "samples": [...]}
    """
    try:
        from app import gender_predictor, ancestry_predictor
        
        limit = request.args.get('limit', 10, type=int)
        
        samples = {
            "gender_samples": [],
            "ancestry_samples": []
        }
        
        if gender_predictor:
            samples["gender_samples"] = gender_predictor.get_available_samples(limit=limit, print_samples=False)
        
        if ancestry_predictor:
            samples["ancestry_samples"] = ancestry_predictor.get_available_samples(limit=limit, print_samples=False)
        
        # Combine and deduplicate
        all_samples = list(set(samples["gender_samples"] + samples["ancestry_samples"]))
        
        return jsonify({
            "success": True,
            "samples": all_samples[:limit],
            "total_gender": len(samples["gender_samples"]),
            "total_ancestry": len(samples["ancestry_samples"])
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# File Processing Endpoint
# ============================================================

@prediction_bp.route('/api/predictions/process_file', methods=['POST'])
def process_snp_file():
    """
    Process an uploaded SNP file and run predictions
    
    POST /api/predictions/process_file
    Body: {"file_path": "...", "patient_id": "..."}
    
    Returns: {"success": true, "predictions": {...}}
    """
    import time
    
    try:
        data = request.get_json() or {}
        file_path = data.get('file_path')
        patient_id = data.get('patient_id')
        
        if not file_path:
            return jsonify({
                "success": False,
                "error": "file_path is required"
            }), 400
        
        start_time = time.time()
        
        # Try to use the prediction models directly
        from app import gender_predictor, ancestry_predictor
        
        # Read the SNP file if accessible
        possible_paths = [
            file_path,
            f"/app/uploads/{os.path.basename(file_path)}"
        ]
        
        file_data = None
        actual_path = None
        sample_id = None
        population = None
        sex = None
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    file_data = pd.read_csv(path)
                    actual_path = path
                    # Extract sample info from file
                    if 'Patient_ID' in file_data.columns:
                        sample_id = file_data['Patient_ID'].iloc[0]
                    if 'Population' in file_data.columns:
                        population = file_data['Population'].iloc[0]
                    if 'Sex' in file_data.columns:
                        sex = int(file_data['Sex'].iloc[0])
                    break
                except Exception as e:
                    print(f"Error reading {path}: {e}")
                    continue
        
        if not patient_id:
            patient_id = sample_id or os.path.splitext(os.path.basename(file_path))[0]
        
        result = {
            "success": True,
            "patient_id": patient_id,
            "sample_id": sample_id,
            "file_name": os.path.basename(file_path),
            "timestamp": datetime.utcnow().isoformat(),
            "predictions": {},
            "file_found": file_data is not None
        }
        
        # If we found a sample_id in the file, try to run predictions
        if sample_id and gender_predictor is not None:
            try:
                pred_result = gender_predictor.predict_by_id(sample_id)
                if pred_result and pred_result[0] is not None:
                    prediction, pred_label, true_sex, true_label = pred_result
                    result["predictions"]["gender"] = {
                        "predicted": pred_label,
                        "predicted_code": int(prediction),
                        "true": true_label,
                        "true_code": int(true_sex) if true_sex is not None else None,
                        "correct": prediction == true_sex if true_sex is not None else None,
                        "model_loaded": True
                    }
                else:
                    # Sample not in training data, use file data if available
                    if sex is not None:
                        sex_labels = {1: "Male", 2: "Female"}
                        result["predictions"]["gender"] = {
                            "predicted": sex_labels.get(sex, "Unknown"),
                            "from_file": True,
                            "model_loaded": True
                        }
                    else:
                        result["predictions"]["gender"] = {
                            "predicted": "Unknown",
                            "error": f"Sample {sample_id} not found in model training data",
                            "model_loaded": True
                        }
            except Exception as e:
                result["predictions"]["gender"] = {
                    "predicted": "Unknown",
                    "error": str(e),
                    "model_loaded": True
                }
        elif gender_predictor is None:
            result["predictions"]["gender"] = {
                "predicted": "Unknown",
                "error": "Model not loaded",
                "model_loaded": False
            }
        
        # Ancestry prediction
        if sample_id and ancestry_predictor is not None:
            try:
                pred_result = ancestry_predictor.predict_by_id(sample_id)
                if pred_result and pred_result[0] is not None:
                    pred_label = pred_result[0]
                    true_label = pred_result[1] if len(pred_result) > 1 else None
                    pop_info = POPULATION_INFO.get(pred_label, {})
                    result["predictions"]["ancestry"] = {
                        "predicted": pred_label,
                        "description": pop_info.get("description", "Unknown"),
                        "true": true_label,
                        "correct": pred_label == true_label if true_label else None,
                        "model_loaded": True
                    }
                else:
                    # Sample not in training data, use file data if available
                    if population:
                        pop_info = POPULATION_INFO.get(population, {})
                        result["predictions"]["ancestry"] = {
                            "predicted": population,
                            "description": pop_info.get("description", "Unknown"),
                            "from_file": True,
                            "model_loaded": True
                        }
                    else:
                        result["predictions"]["ancestry"] = {
                            "predicted": "Unknown",
                            "error": f"Sample {sample_id} not found in model training data",
                            "model_loaded": True
                        }
            except Exception as e:
                result["predictions"]["ancestry"] = {
                    "predicted": "Unknown",
                    "error": str(e),
                    "model_loaded": True
                }
        elif ancestry_predictor is None:
            result["predictions"]["ancestry"] = {
                "predicted": "Unknown",
                "error": "Model not loaded",
                "model_loaded": False
            }
        
        result["processing_time"] = time.time() - start_time
        
        return jsonify(convert_to_serializable(result)), 200
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============================================================
# Population Info Endpoint
# ============================================================

@prediction_bp.route('/api/predictions/populations', methods=['GET'])
def get_populations():
    """
    Get all population codes and descriptions
    
    GET /api/predictions/populations
    
    Returns: {"success": true, "populations": {...}}
    """
    return jsonify({
        "success": True,
        "populations": POPULATION_INFO
    }), 200


# ============================================================
# Model Info Endpoint
# ============================================================

@prediction_bp.route('/api/predictions/models', methods=['GET'])
def get_model_info():
    """
    Get information about loaded models
    
    GET /api/predictions/models
    
    Returns: {"success": true, "models": {...}}
    """
    try:
        from app import gender_predictor, ancestry_predictor
        
        models_info = {
            "gender_model": {
                "loaded": gender_predictor is not None,
                "type": type(gender_predictor).__name__ if gender_predictor else None,
                "n_samples": len(gender_predictor.features_df) if gender_predictor and gender_predictor.features_df is not None else 0
            },
            "ancestry_model": {
                "loaded": ancestry_predictor is not None,
                "type": type(ancestry_predictor).__name__ if ancestry_predictor else None,
                "n_samples": len(ancestry_predictor.features_df) if ancestry_predictor and ancestry_predictor.features_df is not None else 0
            }
        }
        
        return jsonify({
            "success": True,
            "models": models_info
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
