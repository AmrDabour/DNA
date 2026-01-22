"""
Prediction Service - ML Predictions Microservice
Handles: Gender prediction, Ancestry prediction, ML model inference
Port: 5003
"""
import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

# ============================================================
# Flask App Setup
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get("PREDICTION_SECRET_KEY", os.environ.get("FLASK_SECRET_KEY", "prediction_service_secret"))

# Enable CORS for microservices communication
CORS(app, resources={
    r"/api/*": {
        "origins": os.environ.get("ALLOWED_ORIGINS", "*").split(","),
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configuration
MODEL_PATH = os.environ.get("MODEL_PATH", "/app/models")
UPLOADS_PATH = os.environ.get("UPLOADS_PATH", "/app/uploads")


# ============================================================
# Load ML Models
# ============================================================

gender_predictor = None
ancestry_predictor = None

def load_models():
    """Load ML models on startup"""
    global gender_predictor, ancestry_predictor
    
    try:
        from models.predictors import SexPredictor, AncestryPredictor
        
        # Gender Model Paths - use actual file names
        gender_model_path = os.path.join(MODEL_PATH, "gender", "best_gender_model.pkl")
        gender_features_path = os.path.join(MODEL_PATH, "gender", "sex_features_pca.csv")
        gender_pca_path = os.path.join(MODEL_PATH, "gender", "pca_model.pkl")
        gender_selector_path = os.path.join(MODEL_PATH, "gender", "feature_selector.pkl")
        gender_snps_path = os.path.join(MODEL_PATH, "gender", "gender_selected_snps.csv")
        
        if os.path.exists(gender_model_path):
            gender_predictor = SexPredictor(
                model_path=gender_model_path,
                features_path=gender_features_path if os.path.exists(gender_features_path) else None,
                pca_path=gender_pca_path if os.path.exists(gender_pca_path) else None,
                selector_path=gender_selector_path if os.path.exists(gender_selector_path) else None,
                selected_snps_path=gender_snps_path if os.path.exists(gender_snps_path) else None
            )
            print("✅ Gender prediction model loaded")
        else:
            print(f"⚠️ Gender model not found at {gender_model_path}")
        
        # Ancestry Model Paths - use actual file names
        ancestry_model_path = os.path.join(MODEL_PATH, "region", "best_population_model.pkl")
        ancestry_encoder_path = os.path.join(MODEL_PATH, "region", "population_encoder.pkl")
        ancestry_features_path = os.path.join(MODEL_PATH, "region", "genetic_features_pca.csv")
        ancestry_snps_path = os.path.join(MODEL_PATH, "region", "selected_snps.csv")
        
        if os.path.exists(ancestry_model_path) and os.path.exists(ancestry_encoder_path):
            ancestry_predictor = AncestryPredictor(
                model_path=ancestry_model_path,
                encoder_path=ancestry_encoder_path,
                features_path=ancestry_features_path if os.path.exists(ancestry_features_path) else None,
                selected_snps_path=ancestry_snps_path if os.path.exists(ancestry_snps_path) else None
            )
            print("✅ Ancestry prediction model loaded")
        else:
            print(f"⚠️ Ancestry model not found at {ancestry_model_path} or encoder at {ancestry_encoder_path}")
            
    except Exception as e:
        import traceback
        print(f"❌ Error loading models: {e}")
        traceback.print_exc()


# ============================================================
# Health Check Endpoints
# ============================================================

@app.route('/health')
@app.route('/healthz')
def health_check():
    """Health check endpoint for Kubernetes"""
    models_status = {
        "gender_model": gender_predictor is not None,
        "ancestry_model": ancestry_predictor is not None
    }
    
    if any(models_status.values()):
        return jsonify({
            "status": "healthy",
            "service": "prediction-service",
            "models": models_status
        }), 200
    else:
        return jsonify({
            "status": "degraded",
            "service": "prediction-service",
            "models": models_status,
            "warning": "No models loaded"
        }), 200


@app.route('/ready')
def readiness_check():
    """Readiness check endpoint"""
    return jsonify({
        "status": "ready",
        "service": "prediction-service",
        "models_loaded": {
            "gender": gender_predictor is not None,
            "ancestry": ancestry_predictor is not None
        }
    }), 200


# ============================================================
# Import and Register Routes
# ============================================================

from routes.prediction_routes import prediction_bp
app.register_blueprint(prediction_bp)

# Load models at startup (for gunicorn)
with app.app_context():
    load_models()


# ============================================================
# Error Handlers
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PREDICTION_SERVICE_PORT', 5003))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    print(f"🧬 Prediction Service starting on port {port}")
    
    # Load ML models
    load_models()
    
    app.run(host='0.0.0.0', port=port, debug=debug)
