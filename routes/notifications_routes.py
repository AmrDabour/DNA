"""
Notifications Routes - User notifications and real-time progress tracking
Uses in-memory storage for simplicity (use Redis in production)
"""
from flask import Blueprint, request, jsonify
from flask_login import current_user
from datetime import datetime
import uuid

notifications_bp = Blueprint('notifications', __name__)

# In-memory storage for notifications and progress tracking
# In production, use Redis or a database
NOTIFICATIONS_STORE = {}  # user_id -> list of notifications
PROGRESS_STORE = {}  # task_id -> progress data


def get_user_notifications(user_id):
    """Get notifications for a user"""
    if user_id not in NOTIFICATIONS_STORE:
        NOTIFICATIONS_STORE[user_id] = []
    return NOTIFICATIONS_STORE[user_id]


def add_notification(user_id, title, message, notification_type='info', data=None):
    """Add a notification for a user"""
    if user_id not in NOTIFICATIONS_STORE:
        NOTIFICATIONS_STORE[user_id] = []
    
    notification = {
        'id': str(uuid.uuid4()),
        'title': title,
        'message': message,
        'type': notification_type,
        'data': data or {},
        'read': False,
        'created_at': datetime.utcnow().isoformat()
    }
    
    NOTIFICATIONS_STORE[user_id].insert(0, notification)
    
    # Keep only last 100 notifications per user
    NOTIFICATIONS_STORE[user_id] = NOTIFICATIONS_STORE[user_id][:100]
    
    return notification


@notifications_bp.route('/api/notifications')
def get_notifications():
    """Get user notifications"""
    # Allow unauthenticated users to get empty notifications
    if not current_user.is_authenticated:
        return jsonify({
            'success': True,
            'notifications': [],
            'unread_count': 0
        })
    
    user_id = current_user.id
    notifications = get_user_notifications(user_id)
    
    unread_only = request.args.get('unread', 'false').lower() == 'true'
    
    if unread_only:
        notifications = [n for n in notifications if not n.get('read')]
    
    unread_count = len([n for n in get_user_notifications(user_id) if not n.get('read')])
    
    return jsonify({
        'success': True,
        'notifications': notifications[:20],
        'unread_count': unread_count
    })


@notifications_bp.route('/api/notifications/count')
def get_unread_count():
    """Get count of unread notifications"""
    if not current_user.is_authenticated:
        return jsonify({'success': True, 'count': 0})
    
    notifications = get_user_notifications(current_user.id)
    count = len([n for n in notifications if not n.get('read')])
    
    return jsonify({'success': True, 'count': count})


@notifications_bp.route('/api/notifications/<notification_id>/read', methods=['POST'])
def mark_as_read(notification_id):
    """Mark a notification as read"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    notifications = get_user_notifications(current_user.id)
    
    for notification in notifications:
        if notification['id'] == notification_id:
            notification['read'] = True
            notification['read_at'] = datetime.utcnow().isoformat()
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Notification not found'}), 404


@notifications_bp.route('/api/notifications/mark-all-read', methods=['POST'])
def mark_all_read():
    """Mark all notifications as read"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    notifications = get_user_notifications(current_user.id)
    now = datetime.utcnow().isoformat()
    
    for notification in notifications:
        if not notification.get('read'):
            notification['read'] = True
            notification['read_at'] = now
    
    return jsonify({'success': True})


@notifications_bp.route('/api/notifications/<notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Delete a notification"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    user_id = current_user.id
    notifications = get_user_notifications(user_id)
    
    NOTIFICATIONS_STORE[user_id] = [n for n in notifications if n['id'] != notification_id]
    
    return jsonify({'success': True})


# ============================================================
# Progress Tracking Endpoints
# ============================================================

@notifications_bp.route('/api/progress/<task_id>')
def get_progress(task_id):
    """Get progress of a task"""
    progress = PROGRESS_STORE.get(task_id, {
        'status': 'not_found',
        'progress': 0,
        'message': 'Task not found'
    })
    
    return jsonify({'success': True, 'progress': progress})


@notifications_bp.route('/api/progress/<task_id>/update', methods=['POST'])
def update_progress(task_id):
    """Update progress of a task"""
    data = request.get_json() or {}
    
    if task_id not in PROGRESS_STORE:
        PROGRESS_STORE[task_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '',
            'started_at': datetime.utcnow().isoformat()
        }
    
    PROGRESS_STORE[task_id].update({
        'status': data.get('status', PROGRESS_STORE[task_id].get('status', 'processing')),
        'progress': min(data.get('progress', PROGRESS_STORE[task_id].get('progress', 0)), 100),
        'message': data.get('message', PROGRESS_STORE[task_id].get('message', '')),
        'stage': data.get('stage', PROGRESS_STORE[task_id].get('stage', '')),
        'updated_at': datetime.utcnow().isoformat()
    })
    
    return jsonify({'success': True})


@notifications_bp.route('/api/progress/<task_id>/complete', methods=['POST'])
def complete_progress(task_id):
    """Mark a task as complete"""
    data = request.get_json() or {}
    
    PROGRESS_STORE[task_id] = {
        'status': 'completed',
        'progress': 100,
        'message': data.get('message', 'Analysis complete!'),
        'result': data.get('result', {}),
        'completed_at': datetime.utcnow().isoformat()
    }
    
    # Create notification if user is authenticated
    if current_user.is_authenticated:
        add_notification(
            current_user.id,
            title=data.get('title', 'Analysis Complete'),
            message=data.get('message', 'Your genetic analysis has been completed.'),
            notification_type='success',
            data={'task_id': task_id, 'result': data.get('result')}
        )
    
    return jsonify({'success': True})


@notifications_bp.route('/api/progress/<task_id>/error', methods=['POST'])
def error_progress(task_id):
    """Mark a task as failed"""
    data = request.get_json() or {}
    
    PROGRESS_STORE[task_id] = {
        'status': 'error',
        'progress': PROGRESS_STORE.get(task_id, {}).get('progress', 0),
        'message': data.get('message', 'An error occurred'),
        'error': data.get('error', 'Unknown error'),
        'failed_at': datetime.utcnow().isoformat()
    }
    
    # Create notification if user is authenticated
    if current_user.is_authenticated:
        add_notification(
            current_user.id,
            title='Analysis Error',
            message=data.get('message', 'An error occurred during analysis.'),
            notification_type='error',
            data={'task_id': task_id, 'error': data.get('error')}
        )
    
    return jsonify({'success': True})


# ============================================================
# Helper Functions for use in other modules
# ============================================================

def init_progress(task_id, message='Starting analysis...'):
    """Initialize progress tracking for a task"""
    PROGRESS_STORE[task_id] = {
        'status': 'processing',
        'progress': 0,
        'message': message,
        'stage': 'initializing',
        'started_at': datetime.utcnow().isoformat()
    }
    return task_id


def update_task_progress(task_id, progress, message='', stage=''):
    """Update progress for a task"""
    if task_id in PROGRESS_STORE:
        PROGRESS_STORE[task_id].update({
            'progress': min(progress, 100),
            'message': message or PROGRESS_STORE[task_id].get('message', ''),
            'stage': stage or PROGRESS_STORE[task_id].get('stage', ''),
            'updated_at': datetime.utcnow().isoformat()
        })


def notify_user(user_id, title, message, notification_type='info', data=None):
    """Create a notification for a user (can be called from other modules)"""
    return add_notification(user_id, title, message, notification_type, data)
