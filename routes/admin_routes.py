"""
Admin Routes - Admin dashboard and management endpoints
Requires admin privileges to access
"""
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
import os
import psutil

from database.models import db, User, AnalysisHistory

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# Admin Dashboard
# ============================================================

@admin_bp.route('/', strict_slashes=False)
@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    """Main admin dashboard"""
    stats = get_admin_stats()
    return render_template('admin/dashboard.html', stats=stats)


def get_admin_stats():
    """Get comprehensive admin statistics"""
    stats = {
        'system': get_system_health(),
        'cache': get_cache_stats(),
        'users': get_user_stats(),
        'analyses': get_analysis_stats(),
        'storage': get_storage_stats(),
    }
    return stats


def get_system_health():
    """Get system health status"""
    health = {
        'status': 'healthy',
        'services': {}
    }
    
    # PostgreSQL
    try:
        db.session.execute(db.text("SELECT 1"))
        health['services']['postgresql'] = {
            'status': 'healthy',
            'icon': 'check-circle',
            'color': 'green'
        }
    except Exception as e:
        health['services']['postgresql'] = {
            'status': 'unhealthy',
            'error': str(e),
            'icon': 'x-circle',
            'color': 'red'
        }
        health['status'] = 'degraded'
    
    # MongoDB
    try:
        from config.mongodb import is_mongodb_available, get_snp_collection
        if is_mongodb_available():
            collection = get_snp_collection()
            count = collection.count_documents({})
            health['services']['mongodb'] = {
                'status': 'healthy',
                'snp_count': count,
                'icon': 'check-circle',
                'color': 'green'
            }
        else:
            health['services']['mongodb'] = {
                'status': 'unavailable',
                'icon': 'minus-circle',
                'color': 'yellow'
            }
    except Exception as e:
        health['services']['mongodb'] = {
            'status': 'error',
            'error': str(e),
            'icon': 'x-circle',
            'color': 'red'
        }
    
    # Redis
    try:
        from config.redis import redis_health_check, is_redis_available
        if is_redis_available():
            redis_status = redis_health_check()
            health['services']['redis'] = {
                'status': redis_status.get('status', 'unknown'),
                'version': redis_status.get('version', 'unknown'),
                'uptime': redis_status.get('uptime_seconds', 0),
                'clients': redis_status.get('connected_clients', 0),
                'icon': 'check-circle' if redis_status.get('status') == 'healthy' else 'minus-circle',
                'color': 'green' if redis_status.get('status') == 'healthy' else 'yellow'
            }
        else:
            health['services']['redis'] = {
                'status': 'unavailable',
                'icon': 'minus-circle',
                'color': 'yellow'
            }
    except Exception as e:
        health['services']['redis'] = {
            'status': 'error',
            'error': str(e),
            'icon': 'x-circle',
            'color': 'red'
        }
    
    # Gemini API
    gemini_key = os.environ.get('GEMINI_API_KEY')
    health['services']['gemini'] = {
        'status': 'configured' if gemini_key else 'not_configured',
        'icon': 'check-circle' if gemini_key else 'minus-circle',
        'color': 'green' if gemini_key else 'yellow'
    }
    
    # VEP Service
    try:
        from services.vep_service import vep_service
        vep_status = vep_service.get_service_status()
        health['services']['vep'] = {
            'status': 'healthy' if vep_status.get('api_available') else 'degraded',
            'enabled': vep_status.get('enabled'),
            'response_time': vep_status.get('response_time_ms'),
            'icon': 'check-circle' if vep_status.get('api_available') else 'minus-circle',
            'color': 'green' if vep_status.get('api_available') else 'yellow'
        }
    except Exception as e:
        health['services']['vep'] = {
            'status': 'error',
            'error': str(e),
            'icon': 'x-circle',
            'color': 'red'
        }
    
    # System resources
    try:
        health['system_resources'] = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_gb': round(psutil.virtual_memory().used / (1024**3), 2),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'disk_percent': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
        }
    except:
        health['system_resources'] = {}
    
    return health


def get_cache_stats():
    """Get Redis cache statistics"""
    cache_stats = {
        'available': False,
        'vep': {},
        'memory': {},
        'sessions': {},
        'server': {}
    }
    
    try:
        from config.redis import is_redis_available, get_redis_client
        
        if is_redis_available():
            cache_stats['available'] = True
            client = get_redis_client()
            
            # Count cache entries
            vep_keys = client.keys('genovaai:vep:*')
            memory_keys = client.keys('genovaai:memory:*')
            session_keys = client.keys('genovaai:session:*')
            
            cache_stats['vep'] = {
                'entries': len(vep_keys) if vep_keys else 0,
                'ttl_days': int(os.environ.get('VEP_CACHE_TTL', 7))
            }
            
            cache_stats['memory'] = {
                'entries': len(memory_keys) if memory_keys else 0,
                'ttl_hours': 24
            }
            
            cache_stats['sessions'] = {
                'entries': len(session_keys) if session_keys else 0,
                'ttl_days': 7
            }
            
            # Server stats
            info = client.info('stats')
            memory_info = client.info('memory')
            
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total = hits + misses
            
            cache_stats['server'] = {
                'hits': hits,
                'misses': misses,
                'hit_rate': round((hits / total * 100), 1) if total > 0 else 0,
                'total_commands': info.get('total_commands_processed', 0),
                'memory_used_mb': round(memory_info.get('used_memory', 0) / (1024**2), 2),
                'memory_peak_mb': round(memory_info.get('used_memory_peak', 0) / (1024**2), 2),
            }
    except Exception as e:
        cache_stats['error'] = str(e)
    
    return cache_stats


def get_user_stats():
    """Get user statistics"""
    total_users = User.query.count()
    admin_users = User.query.filter_by(is_admin=True).count()
    active_users = User.query.filter_by(is_active=True).count()
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Users with most analyses
    top_users = db.session.query(
        User.username,
        User.email,
        db.func.count(AnalysisHistory.id).label('analysis_count')
    ).outerjoin(AnalysisHistory).group_by(User.id).order_by(
        db.func.count(AnalysisHistory.id).desc()
    ).limit(5).all()
    
    return {
        'total': total_users,
        'admins': admin_users,
        'active': active_users,
        'recent': [u.to_dict() for u in recent_users],
        'top_users': [{'username': u[0], 'email': u[1], 'analyses': u[2]} for u in top_users]
    }


def get_analysis_stats():
    """Get analysis statistics"""
    total = AnalysisHistory.query.count()
    
    # By type
    by_type = db.session.query(
        AnalysisHistory.analysis_type,
        db.func.count(AnalysisHistory.id)
    ).group_by(AnalysisHistory.analysis_type).all()
    
    # By status
    completed = AnalysisHistory.query.filter_by(status='completed').count()
    failed = AnalysisHistory.query.filter_by(status='failed').count()
    pending = AnalysisHistory.query.filter_by(status='pending').count()
    
    # Today's analyses
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_count = AnalysisHistory.query.filter(
        AnalysisHistory.created_at >= today_start
    ).count()
    
    # This week
    week_start = today_start - timedelta(days=today.weekday())
    week_count = AnalysisHistory.query.filter(
        AnalysisHistory.created_at >= week_start
    ).count()
    
    return {
        'total': total,
        'by_type': {t: c for t, c in by_type},
        'completed': completed,
        'failed': failed,
        'pending': pending,
        'success_rate': round((completed / total * 100), 1) if total > 0 else 0,
        'today': today_count,
        'this_week': week_count
    }


def get_storage_stats():
    """Get storage statistics"""
    uploads_dir = 'uploads'
    results_dir = 'result'
    
    def get_dir_size(path):
        total = 0
        if os.path.exists(path):
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total += os.path.getsize(fp)
        return total
    
    uploads_size = get_dir_size(uploads_dir)
    results_size = get_dir_size(results_dir)
    
    uploads_count = len(os.listdir(uploads_dir)) if os.path.exists(uploads_dir) else 0
    results_count = len(os.listdir(results_dir)) if os.path.exists(results_dir) else 0
    
    return {
        'uploads': {
            'count': uploads_count,
            'size_mb': round(uploads_size / (1024**2), 2)
        },
        'results': {
            'count': results_count,
            'size_mb': round(results_size / (1024**2), 2)
        },
        'total_mb': round((uploads_size + results_size) / (1024**2), 2)
    }


# ============================================================
# Cache Management API
# ============================================================

@admin_bp.route('/api/cache/stats')
@admin_required
def api_cache_stats():
    """Get cache statistics"""
    return jsonify(get_cache_stats())


@admin_bp.route('/api/cache/clear/vep', methods=['POST'])
@admin_required
def clear_vep_cache():
    """Clear VEP cache"""
    try:
        from config.redis import get_redis_client, is_redis_available
        
        if not is_redis_available():
            return jsonify({'success': False, 'error': 'Redis not available'})
        
        client = get_redis_client()
        keys = client.keys('genovaai:vep:*')
        deleted = 0
        if keys:
            deleted = client.delete(*keys)
        
        # Also clear VEP service memory cache
        from services.vep_service import vep_service
        vep_service._memory_cache.clear()
        
        return jsonify({
            'success': True,
            'deleted': deleted,
            'message': f'Cleared {deleted} VEP cache entries'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/api/cache/clear/memory', methods=['POST'])
@admin_required
def clear_memory_cache():
    """Clear chat memory cache"""
    try:
        from config.redis import get_redis_client, is_redis_available
        
        if not is_redis_available():
            return jsonify({'success': False, 'error': 'Redis not available'})
        
        client = get_redis_client()
        keys = client.keys('genovaai:memory:*')
        deleted = 0
        if keys:
            deleted = client.delete(*keys)
        
        # Also clear in-memory store
        from agent.memory import _memory_store
        _memory_store.clear()
        
        return jsonify({
            'success': True,
            'deleted': deleted,
            'message': f'Cleared {deleted} memory cache entries'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/api/cache/clear/sessions', methods=['POST'])
@admin_required
def clear_session_cache():
    """Clear session cache"""
    try:
        from config.redis import get_redis_client, is_redis_available
        
        if not is_redis_available():
            return jsonify({'success': False, 'error': 'Redis not available'})
        
        client = get_redis_client()
        keys = client.keys('genovaai:session:*')
        deleted = 0
        if keys:
            deleted = client.delete(*keys)
        
        return jsonify({
            'success': True,
            'deleted': deleted,
            'message': f'Cleared {deleted} session entries'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/api/cache/clear/all', methods=['POST'])
@admin_required
def clear_all_cache():
    """Clear all caches"""
    try:
        from config.redis import get_redis_client, is_redis_available
        
        if not is_redis_available():
            return jsonify({'success': False, 'error': 'Redis not available'})
        
        client = get_redis_client()
        keys = client.keys('genovaai:*')
        deleted = 0
        if keys:
            deleted = client.delete(*keys)
        
        return jsonify({
            'success': True,
            'deleted': deleted,
            'message': f'Cleared {deleted} total cache entries'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============================================================
# User Management API
# ============================================================

@admin_bp.route('/users')
@admin_required
def users_page():
    """User management page"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/api/users')
@admin_required
def api_users():
    """Get all users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users])


@admin_bp.route('/api/users/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    """Toggle admin status for a user"""
    if current_user.id == user_id:
        return jsonify({'success': False, 'error': 'Cannot modify your own admin status'})
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_admin': user.is_admin,
        'message': f'{"Granted" if user.is_admin else "Revoked"} admin privileges for {user.username}'
    })


@admin_bp.route('/api/users/<int:user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_active(user_id):
    """Toggle active status for a user"""
    if current_user.id == user_id:
        return jsonify({'success': False, 'error': 'Cannot deactivate your own account'})
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_active': user.is_active,
        'message': f'{"Activated" if user.is_active else "Deactivated"} user {user.username}'
    })


@admin_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user"""
    if current_user.id == user_id:
        return jsonify({'success': False, 'error': 'Cannot delete your own account'})
    
    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Deleted user {username}'
    })


# ============================================================
# System Health API
# ============================================================

@admin_bp.route('/api/health')
@admin_required
def api_health():
    """Get system health"""
    return jsonify(get_system_health())


@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """Get all admin stats"""
    return jsonify(get_admin_stats())

