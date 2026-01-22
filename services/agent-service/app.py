"""
Agent Service - LangGraph DNA Analysis Agent Microservice
Handles: AI Agent interactions, DNA analysis conversations
Port: 5005
"""
import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

# ============================================================
# Flask App Setup
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get("AGENT_SECRET_KEY", os.environ.get("FLASK_SECRET_KEY", "agent_service_secret"))

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": os.environ.get("ALLOWED_ORIGINS", "*").split(","),
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Service URLs for inter-service communication
PREDICTION_SERVICE_URL = os.environ.get("PREDICTION_SERVICE_URL", "http://prediction-service:5003")
ANALYSIS_SERVICE_URL = os.environ.get("ANALYSIS_SERVICE_URL", "http://analysis-service:5002")
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://ai-service:5004")

# Gemini Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY")
GEMINI_MODEL = os.environ.get("AGENT_MODEL", "gemini-2.5-flash")


# ============================================================
# Health Check Endpoints
# ============================================================

@app.route('/health')
@app.route('/healthz')
def health_check():
    """Health check endpoint for Kubernetes"""
    return jsonify({
        "status": "healthy" if GEMINI_API_KEY else "degraded",
        "service": "agent-service",
        "gemini_configured": GEMINI_API_KEY is not None,
        "model": GEMINI_MODEL
    }), 200 if GEMINI_API_KEY else 503


@app.route('/ready')
def readiness_check():
    """Readiness check endpoint"""
    return jsonify({
        "status": "ready",
        "service": "agent-service"
    }), 200


# ============================================================
# Import and Register Routes
# ============================================================

from routes.agent_routes import agent_bp
app.register_blueprint(agent_bp)


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
    port = int(os.environ.get('AGENT_SERVICE_PORT', 5005))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    print(f"🤖 Agent Service starting on port {port}")
    print(f"🔑 Gemini API: {'Configured' if GEMINI_API_KEY else 'NOT CONFIGURED'}")
    print(f"📡 Services: Prediction={PREDICTION_SERVICE_URL}, Analysis={ANALYSIS_SERVICE_URL}, AI={AI_SERVICE_URL}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
