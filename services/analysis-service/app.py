"""
Analysis Service - SNP Analysis Microservice
Handles: SNP analysis, file processing, DNA analysis, history management
Port: 5002
"""
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

# Import local database module
from database import db, AnalysisHistory, SNPInfo, init_db

# ============================================================
# Flask App Setup
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get("ANALYSIS_SECRET_KEY", os.environ.get("FLASK_SECRET_KEY", "analysis_service_secret"))

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": os.environ.get("ALLOWED_ORIGINS", "*").split(","),
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Database Configuration
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    os.environ.get("ANALYSIS_DATABASE_URL", "postgresql://genovaai_user:genovaai_secure_password_2024@postgres:5432/genovaai")
)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': int(os.environ.get('DB_POOL_SIZE', 5)),
    'pool_recycle': 300,
    'pool_pre_ping': True,
}

# File Upload Configuration
UPLOADS_PATH = os.environ.get("UPLOADS_PATH", "/app/uploads")
app.config['UPLOAD_FOLDER'] = UPLOADS_PATH
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_UPLOAD_SIZE', 100 * 1024 * 1024))  # 100MB

# Initialize database
init_db(app)


# ============================================================
# Health Check Endpoints
# ============================================================

@app.route('/health')
@app.route('/healthz')
def health_check():
    """Health check endpoint for Kubernetes"""
    try:
        # Check database connection
        AnalysisHistory.query.first()
        return jsonify({
            "status": "healthy",
            "service": "analysis-service",
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "analysis-service",
            "error": str(e)
        }), 503


@app.route('/ready')
def readiness_check():
    """Readiness check endpoint"""
    return jsonify({"status": "ready", "service": "analysis-service"}), 200


# ============================================================
# Import and Register Routes
# ============================================================

from routes.analysis_routes import analysis_bp
from routes.history_routes import history_bp
from routes.upload_routes import upload_bp
from routes.snp_routes import snp_bp

app.register_blueprint(analysis_bp)
app.register_blueprint(history_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(snp_bp)


# ============================================================
# Error Handlers
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({"error": "File too large"}), 413


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('ANALYSIS_SERVICE_PORT', 5002))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    print(f"🔬 Analysis Service starting on port {port}")
    print(f"📊 Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
    print(f"📁 Uploads: {UPLOADS_PATH}")
    
    # Create tables and uploads directory
    with app.app_context():
        db.create_all()
        os.makedirs(UPLOADS_PATH, exist_ok=True)
        print("✅ Database tables ready")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
