"""
Auth Service - User Authentication Microservice
Handles: Login, Registration, JWT tokens, User management
Port: 5001
"""
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_login import LoginManager
from datetime import timedelta

# Import local database module
from database import db, User, init_db

# ============================================================
# Flask App Setup
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get("AUTH_SECRET_KEY", os.environ.get("FLASK_SECRET_KEY", "auth_service_secret_key"))

# Enable CORS for microservices communication
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
    os.environ.get("AUTH_DATABASE_URL", "postgresql://genovaai_user:genovaai_secure_password_2024@postgres:5432/genovaai")
)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': int(os.environ.get('DB_POOL_SIZE', 5)),
    'pool_recycle': 300,
    'pool_pre_ping': True,
}

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY", app.secret_key)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=int(os.environ.get("JWT_EXPIRY_HOURS", 24)))

# Initialize database
init_db(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


# ============================================================
# Health Check Endpoints
# ============================================================

@app.route('/health')
@app.route('/healthz')
def health_check():
    """Health check endpoint for Kubernetes"""
    try:
        # Check database connection
        User.query.first()
        return jsonify({
            "status": "healthy",
            "service": "auth-service",
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "auth-service",
            "error": str(e)
        }), 503


@app.route('/ready')
def readiness_check():
    """Readiness check endpoint"""
    return jsonify({"status": "ready", "service": "auth-service"}), 200


# ============================================================
# Import and Register Routes
# ============================================================

from routes.auth_routes import auth_bp
app.register_blueprint(auth_bp)


# ============================================================
# Additional API Endpoints for Microservices
# ============================================================

@app.route('/api/auth/verify', methods=['POST'])
def verify_token():
    """
    Verify JWT token - called by other services
    Used for inter-service authentication
    """
    from flask_login import current_user
    
    # For session-based auth
    if current_user.is_authenticated:
        return jsonify({
            "valid": True,
            "user_id": current_user.id,
            "username": current_user.username,
            "is_admin": current_user.is_admin
        }), 200
    
    # For JWT-based auth (future)
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        # TODO: Implement JWT verification
        # For now, return invalid
        return jsonify({"valid": False, "error": "JWT not implemented yet"}), 401
    
    return jsonify({"valid": False, "error": "Not authenticated"}), 401


@app.route('/api/auth/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """
    Get user info by ID - for other services
    """
    user = User.query.get(user_id)
    if user:
        return jsonify(user.to_dict()), 200
    return jsonify({"error": "User not found"}), 404


@app.route('/api/auth/users', methods=['GET'])
def list_users():
    """
    List all users - admin only
    """
    from flask_login import current_user
    
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403
    
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


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
    port = int(os.environ.get('AUTH_SERVICE_PORT', 5001))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    print(f"🔐 Auth Service starting on port {port}")
    print(f"📊 Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
    
    # Create tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables ready")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
