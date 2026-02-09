"""
Authentication Routes - User login, registration, and session management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    # Import here to avoid circular imports
    from database import db, User
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('auth/login.html')
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Track successful login
            try:
                from utils.metrics import metrics_collector
                metrics_collector.track_login(success=True)
            except ImportError:
                pass
            
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            
            # Redirect to next page or index
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            # Track failed login
            try:
                from utils.metrics import metrics_collector
                metrics_collector.track_login(success=False)
            except ImportError:
                pass
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    from database import db, User
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        
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
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Track successful registration
        try:
            from utils.metrics import metrics_collector
            metrics_collector.track_registration(success=True)
        except ImportError:
            pass
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    from database import AnalysisHistory
    from sqlalchemy import or_
    
    # Get user's analyses statistics (include user's own + public/unassigned analyses)
    base_query = AnalysisHistory.query.filter(
        or_(AnalysisHistory.user_id == current_user.id, AnalysisHistory.user_id == None)
    )
    
    total_analyses = base_query.count()
    starred_analyses = base_query.filter(AnalysisHistory.is_starred == True).count()
    recent_analyses = base_query.order_by(AnalysisHistory.created_at.desc()).limit(5).all()
    
    stats = {
        'total_analyses': total_analyses,
        'starred_analyses': starred_analyses,
        'recent_analyses': recent_analyses
    }
    
    return render_template('auth/profile.html', stats=stats)


@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    from database import db
    
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    
    # Update user info
    if full_name:
        current_user.full_name = full_name
    
    if email and email != current_user.email:
        # Check if email already exists
        from database import User
        if User.query.filter_by(email=email).first():
            flash('Email already in use.', 'error')
            return redirect(url_for('auth.profile'))
        current_user.email = email
    
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('auth.profile'))


@auth_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    from database import db
    
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('auth.profile'))
    
    if len(new_password) < 6:
        flash('New password must be at least 6 characters long.', 'error')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('auth.profile'))
    
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Password changed successfully!', 'success')
    return redirect(url_for('auth.profile'))


# API endpoints for AJAX requests
@auth_bp.route('/api/auth/check')
def check_auth():
    """Check if user is authenticated"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        })
    return jsonify({'authenticated': False})


@auth_bp.route('/api/auth/user')
@login_required
def get_current_user():
    """Get current user info"""
    return jsonify(current_user.to_dict())
