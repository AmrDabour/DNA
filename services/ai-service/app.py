"""
AI Service - Gemini AI Integration Microservice
Handles: Physical characteristics, Disease risk analysis, Health insights
Port: 5004
"""
import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
import google.generativeai as genai

# ============================================================
# Flask App Setup
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get("AI_SECRET_KEY", os.environ.get("FLASK_SECRET_KEY", "ai_service_secret"))

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": os.environ.get("ALLOWED_ORIGINS", "*").split(","),
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Gemini Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print(f"✅ Gemini API configured with model: {GEMINI_MODEL}")
else:
    print("⚠️ WARNING: GEMINI_API_KEY not set!")


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
# Health Check Endpoints
# ============================================================

@app.route('/health')
@app.route('/healthz')
def health_check():
    """Health check endpoint for Kubernetes"""
    return jsonify({
        "status": "healthy" if GEMINI_API_KEY else "degraded",
        "service": "ai-service",
        "gemini_configured": GEMINI_API_KEY is not None,
        "model": GEMINI_MODEL
    }), 200 if GEMINI_API_KEY else 503


@app.route('/ready')
def readiness_check():
    """Readiness check endpoint"""
    return jsonify({
        "status": "ready",
        "service": "ai-service"
    }), 200


# ============================================================
# Import and Register Routes
# ============================================================

from routes.ai_routes import ai_bp
app.register_blueprint(ai_bp)


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
    port = int(os.environ.get('AI_SERVICE_PORT', 5004))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    print(f"🤖 AI Service starting on port {port}")
    print(f"🔑 Gemini API: {'Configured' if GEMINI_API_KEY else 'NOT CONFIGURED'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
