"""
Authentication Routes - REST API for User Authentication
Auth Service Microservice
"""
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from functools import wraps

auth_bp = Blueprint('auth', __name__)


# ============================================================
# Helper Decorators
# ============================================================

def json_required(f):
    """Ensure request has JSON data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json and request.method in ['POST', 'PUT']:
            # Also accept form data for compatibility
            if not request.form:
                return jsonify({"error": "JSON or form data required"}), 400
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Require admin user"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# Authentication Endpoints
# ============================================================

@auth_bp.route('/api/auth/login', methods=['POST'])
@json_required
def login():
    """
    User login endpoint
    
    POST /api/auth/login
    Body: {"username": "...", "password": "...", "remember": true/false}
    
    Returns: {"success": true, "user": {...}} or {"error": "..."}
    """
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
    from database import db, User
    
    # Get data from JSON or form
    data = request.get_json() or {}
    username = data.get('username') or request.form.get('username', '').strip()
    password = data.get('password') or request.form.get('password', '')
    remember = data.get('remember', False) or request.form.get('remember', False)
    
    if not username or not password:
        return jsonify({
            "success": False,
            "error": "Username and password are required"
        }), 400
    
    # Find user by username or email
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user or not user.check_password(password):
        return jsonify({
            "success": False,
            "error": "Invalid username or password"
        }), 401
    
    if not user.is_active:
        return jsonify({
            "success": False,
            "error": "Account is deactivated. Please contact support."
        }), 403
    
    # Login user
    login_user(user, remember=remember)
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": f"Welcome back, {user.username}!",
        "user": user.to_dict()
    }), 200


@auth_bp.route('/api/auth/register', methods=['POST'])
@json_required
def register():
    """
    User registration endpoint
    
    POST /api/auth/register
    Body: {"username": "...", "email": "...", "password": "...", "confirm_password": "...", "full_name": "..."}
    
    Returns: {"success": true, "user": {...}} or {"error": "...", "errors": [...]}
    """
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
    from database import db, User
    
    # Get data from JSON or form
    data = request.get_json() or {}
    username = data.get('username') or request.form.get('username', '').strip()
    email = (data.get('email') or request.form.get('email', '')).strip().lower()
    password = data.get('password') or request.form.get('password', '')
    confirm_password = data.get('confirm_password') or request.form.get('confirm_password', '')
    full_name = data.get('full_name') or request.form.get('full_name', '').strip()
    
    errors = []
    
    # Validation
    if not username or len(username) < 3:
        errors.append('Username must be at least 3 characters long.')
    
    if not email or '@' not in email:
        errors.append('Please enter a valid email address.')
    
    if not password or len(password) < 6:
        errors.append('Password must be at least 6 characters long.')
    
    if password != confirm_password:
        errors.append('Passwords do not match.')
    
    # Check if username or email already exists
    if User.query.filter_by(username=username).first():
        errors.append('Username already taken.')
    
    if User.query.filter_by(email=email).first():
        errors.append('Email already registered.')
    
    if errors:
        return jsonify({
            "success": False,
            "error": "Validation failed",
            "errors": errors
        }), 400
    
    # Create new user (Note: full_name not in current DB schema)
    user = User(
        username=username,
        email=email
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Registration successful!",
        "user": user.to_dict()
    }), 201


@auth_bp.route('/api/auth/logout', methods=['POST', 'GET'])
@login_required
def logout():
    """
    User logout endpoint
    
    POST /api/auth/logout
    
    Returns: {"success": true, "message": "Logged out successfully"}
    """
    logout_user()
    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    }), 200


# ============================================================
# User Profile Endpoints
# ============================================================

@auth_bp.route('/api/auth/profile', methods=['GET'])
@login_required
def get_profile():
    """
    Get current user profile with statistics
    
    GET /api/auth/profile
    
    Returns: {"user": {...}, "stats": {...}}
    """
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
    from database import AnalysisHistory
    from sqlalchemy import or_
    
    # Get user's analyses statistics
    base_query = AnalysisHistory.query.filter(
        or_(AnalysisHistory.user_id == current_user.id, AnalysisHistory.user_id == None)
    )
    
    total_analyses = base_query.count()
    starred_analyses = base_query.filter(AnalysisHistory.is_starred == True).count()
    recent_analyses = base_query.order_by(AnalysisHistory.created_at.desc()).limit(5).all()
    
    return jsonify({
        "success": True,
        "user": current_user.to_dict(),
        "stats": {
            "total_analyses": total_analyses,
            "starred_analyses": starred_analyses,
            "recent_analyses": [a.to_dict() for a in recent_analyses]
        }
    }), 200


@auth_bp.route('/api/auth/profile', methods=['PUT', 'POST'])
@login_required
@json_required
def update_profile():
    """
    Update user profile
    
    PUT /api/auth/profile
    Body: {"email": "..."}
    
    Returns: {"success": true, "user": {...}}
    """
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
    from database import db, User
    
    data = request.get_json() or {}
    email = (data.get('email') or request.form.get('email', '')).strip().lower()
    
    # Update user info
    if email and email != current_user.email:
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({
                "success": False,
                "error": "Email already in use"
            }), 400
        current_user.email = email
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Profile updated successfully",
        "user": current_user.to_dict()
    }), 200


@auth_bp.route('/api/auth/change-password', methods=['POST'])
@login_required
@json_required
def change_password():
    """
    Change user password
    
    POST /api/auth/change-password
    Body: {"current_password": "...", "new_password": "...", "confirm_password": "..."}
    
    Returns: {"success": true, "message": "..."}
    """
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
    from database import db
    
    data = request.get_json() or {}
    current_password = data.get('current_password') or request.form.get('current_password', '')
    new_password = data.get('new_password') or request.form.get('new_password', '')
    confirm_password = data.get('confirm_password') or request.form.get('confirm_password', '')
    
    if not current_user.check_password(current_password):
        return jsonify({
            "success": False,
            "error": "Current password is incorrect"
        }), 400
    
    if len(new_password) < 6:
        return jsonify({
            "success": False,
            "error": "New password must be at least 6 characters long"
        }), 400
    
    if new_password != confirm_password:
        return jsonify({
            "success": False,
            "error": "New passwords do not match"
        }), 400
    
    current_user.set_password(new_password)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Password changed successfully"
    }), 200


# ============================================================
# Authentication Check Endpoints (for other services)
# ============================================================

@auth_bp.route('/api/auth/check', methods=['GET'])
def check_auth():
    """
    Check if user is authenticated
    Used by frontend and other services
    
    GET /api/auth/check
    
    Returns: {"authenticated": true/false, "user": {...}}
    """
    if current_user.is_authenticated:
        return jsonify({
            "authenticated": True,
            "user": current_user.to_dict()
        }), 200
    return jsonify({"authenticated": False}), 200


@auth_bp.route('/api/auth/user', methods=['GET'])
@login_required
def get_current_user_info():
    """
    Get current user info
    
    GET /api/auth/user
    
    Returns: {"success": true, "user": {...}}
    """
    return jsonify({
        "success": True,
        "user": current_user.to_dict()
    }), 200


@auth_bp.route('/api/auth/validate', methods=['POST'])
def validate_token():
    """
    Validate user session/token for inter-service communication
    Called by other microservices to verify authentication
    
    POST /api/auth/validate
    Headers: Authorization: Bearer <session_id>
    
    Returns: {"valid": true, "user_id": ..., "is_admin": ...}
    """
    if current_user.is_authenticated:
        return jsonify({
            "valid": True,
            "user_id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "is_admin": current_user.is_admin
        }), 200
    
    return jsonify({
        "valid": False,
        "error": "Not authenticated"
    }), 401


# ============================================================
# Admin Endpoints
# ============================================================

@auth_bp.route('/api/auth/users', methods=['GET'])
@admin_required
def list_users():
    """
    List all users (admin only)
    
    GET /api/auth/users
    
    Returns: {"success": true, "users": [...]}
    """
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
    from database import User
    
    users = User.query.all()
    return jsonify({
        "success": True,
        "users": [u.to_dict() for u in users],
        "total": len(users)
    }), 200


@auth_bp.route('/api/auth/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """
    Get user by ID
    
    GET /api/auth/users/<id>
    
    Returns: {"success": true, "user": {...}}
    """
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
    from database import User
    
    # Users can only view their own profile unless they're admin
    if user_id != current_user.id and not current_user.is_admin:
        return jsonify({
            "success": False,
            "error": "Access denied"
        }), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            "success": False,
            "error": "User not found"
        }), 404
    
    return jsonify({
        "success": True,
        "user": user.to_dict()
    }), 200


@auth_bp.route('/api/auth/users/<int:user_id>/activate', methods=['POST'])
@admin_required
def activate_user(user_id):
    """
    Activate/deactivate user (admin only)
    
    POST /api/auth/users/<id>/activate
    Body: {"active": true/false}
    
    Returns: {"success": true, "user": {...}}
    """
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
    from database import db, User
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            "success": False,
            "error": "User not found"
        }), 404
    
    data = request.get_json() or {}
    user.is_active = data.get('active', True)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": f"User {'activated' if user.is_active else 'deactivated'} successfully",
        "user": user.to_dict()
    }), 200


@auth_bp.route('/api/auth/users/<int:user_id>/admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    """
    Grant/revoke admin privileges (admin only)
    
    POST /api/auth/users/<id>/admin
    Body: {"is_admin": true/false}
    
    Returns: {"success": true, "user": {...}}
    """
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
    from database import db, User
    
    if user_id == current_user.id:
        return jsonify({
            "success": False,
            "error": "Cannot modify your own admin status"
        }), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            "success": False,
            "error": "User not found"
        }), 404
    
    data = request.get_json() or {}
    user.is_admin = data.get('is_admin', False)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": f"Admin privileges {'granted' if user.is_admin else 'revoked'} successfully",
        "user": user.to_dict()
    }), 200
