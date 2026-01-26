"""
Task Routes - API endpoints for Celery task management and monitoring
=====================================================================
Provides endpoints to:
- Submit async analysis tasks
- Check task status and results
- Cancel running tasks
- Get task statistics
"""
import logging
import os

from flask import Blueprint, jsonify, request

from celery_app import CELERY_AVAILABLE, CELERY_ENABLED, get_celery_status

# Import task modules
from tasks import (
    analyze_snp_file_task,
    batch_vep_annotation_task,
    predict_physical_traits_task,
    predict_disease_risk_task,
    generate_full_report_task,
)

logger = logging.getLogger(__name__)

# Create blueprint
tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


# ============================================================
# Task Status Endpoints
# ============================================================

@tasks_bp.route('/status', methods=['GET'])
def get_task_system_status():
    """
    Get Celery task system status
    ---
    tags:
      - Tasks
    responses:
      200:
        description: Task system status
    """
    status = get_celery_status()
    
    # Add worker stats if Celery is active
    if CELERY_ENABLED and CELERY_AVAILABLE:
        try:
            from celery_app import celery_app
            if celery_app:
                inspector = celery_app.control.inspect()
                
                # Get active workers
                active = inspector.active()
                status['workers'] = {
                    'connected': active is not None,
                    'count': len(active) if active else 0,
                    'active_tasks': sum(len(tasks) for tasks in active.values()) if active else 0
                }
                
                # Get queue stats
                reserved = inspector.reserved()
                status['queues'] = {
                    'reserved_tasks': sum(len(tasks) for tasks in reserved.values()) if reserved else 0
                }
        except Exception as e:
            logger.warning(f"Could not get Celery stats: {e}")
            status['workers'] = {'connected': False, 'error': str(e)}
    
    return jsonify(status)


@tasks_bp.route('/<task_id>', methods=['GET'])
def get_task_status(task_id: str):
    """
    Get status of a specific task
    ---
    tags:
      - Tasks
    parameters:
      - name: task_id
        in: path
        type: string
        required: true
        description: The task ID
    responses:
      200:
        description: Task status and result
    """
    if not CELERY_ENABLED or not CELERY_AVAILABLE:
        return jsonify({
            'task_id': task_id,
            'status': 'SYNC_MODE',
            'message': 'Celery is not enabled. Tasks run synchronously.'
        })
    
    try:
        from celery.result import AsyncResult
        from celery_app import celery_app
        
        result = AsyncResult(task_id, app=celery_app)
        
        response = {
            'task_id': task_id,
            'status': result.status,
            'ready': result.ready(),
            'successful': result.successful() if result.ready() else None,
        }
        
        # Include result if task is complete
        if result.ready():
            if result.successful():
                response['result'] = result.result
            else:
                response['error'] = str(result.result)
        
        # Include progress info if available
        if result.info and isinstance(result.info, dict):
            response['progress'] = result.info.get('progress')
            response['current_step'] = result.info.get('current_step')
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return jsonify({
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(e)
        }), 500


@tasks_bp.route('/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id: str):
    """
    Cancel a running task
    ---
    tags:
      - Tasks
    parameters:
      - name: task_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Task cancellation result
    """
    if not CELERY_ENABLED or not CELERY_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Celery is not enabled'
        })
    
    try:
        from celery.result import AsyncResult
        from celery_app import celery_app
        
        result = AsyncResult(task_id, app=celery_app)
        result.revoke(terminate=True)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Task cancellation requested'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# Async Analysis Endpoints
# ============================================================

@tasks_bp.route('/analyze/snp', methods=['POST'])
def submit_snp_analysis():
    """
    Submit SNP file for async analysis
    ---
    tags:
      - Tasks
    parameters:
      - name: body
        in: body
        schema:
          type: object
          properties:
            file_path:
              type: string
              description: Path to the SNP file
            patient_id:
              type: string
              description: Optional patient ID
            include_vep:
              type: boolean
              default: true
              description: Include VEP annotation
            vep_limit:
              type: integer
              description: Limit VEP annotations
    responses:
      200:
        description: Task submitted successfully
      400:
        description: Invalid request
    """
    data = request.json or {}
    file_path = data.get('file_path')
    
    if not file_path:
        return jsonify({'success': False, 'error': 'file_path is required'}), 400
    
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': f'File not found: {file_path}'}), 400
    
    patient_id = data.get('patient_id')
    include_vep = data.get('include_vep', True)
    vep_limit = data.get('vep_limit')
    
    # Submit task
    if CELERY_ENABLED:
        task = analyze_snp_file_task.delay(
            file_path=file_path,
            patient_id=patient_id,
            include_vep=include_vep,
            vep_limit=vep_limit
        )
        
        return jsonify({
            'success': True,
            'async': True,
            'task_id': task.id,
            'status': 'PENDING',
            'message': 'Task submitted for async processing',
            'status_url': f'/api/tasks/{task.id}'
        })
    else:
        # Run synchronously
        result = analyze_snp_file_task(
            file_path=file_path,
            patient_id=patient_id,
            include_vep=include_vep,
            vep_limit=vep_limit
        )
        
        return jsonify({
            'success': True,
            'async': False,
            'result': result,
            'message': 'Task completed synchronously (Celery disabled)'
        })


@tasks_bp.route('/analyze/vep-batch', methods=['POST'])
def submit_vep_batch():
    """
    Submit batch VEP annotation task
    ---
    tags:
      - Tasks
    """
    data = request.json or {}
    rs_ids = data.get('rs_ids', [])
    
    if not rs_ids or not isinstance(rs_ids, list):
        return jsonify({'success': False, 'error': 'rs_ids list is required'}), 400
    
    if CELERY_ENABLED:
        task = batch_vep_annotation_task.delay(rs_ids=rs_ids)
        
        return jsonify({
            'success': True,
            'async': True,
            'task_id': task.id,
            'snp_count': len(rs_ids),
            'status_url': f'/api/tasks/{task.id}'
        })
    else:
        result = batch_vep_annotation_task(rs_ids=rs_ids)
        return jsonify({
            'success': True,
            'async': False,
            'result': result
        })


@tasks_bp.route('/predict/traits', methods=['POST'])
def submit_traits_prediction():
    """
    Submit physical traits prediction task
    ---
    tags:
      - Tasks
    """
    data = request.json or {}
    file_path = data.get('file_path')
    patient_id = data.get('patient_id')
    
    if not file_path:
        return jsonify({'success': False, 'error': 'file_path is required'}), 400
    
    if CELERY_ENABLED:
        task = predict_physical_traits_task.delay(
            file_path=file_path,
            patient_id=patient_id
        )
        
        return jsonify({
            'success': True,
            'async': True,
            'task_id': task.id,
            'status_url': f'/api/tasks/{task.id}'
        })
    else:
        result = predict_physical_traits_task(
            file_path=file_path,
            patient_id=patient_id
        )
        return jsonify({
            'success': True,
            'async': False,
            'result': result
        })


@tasks_bp.route('/predict/disease-risk', methods=['POST'])
def submit_disease_risk_prediction():
    """
    Submit disease risk prediction task
    ---
    tags:
      - Tasks
    """
    data = request.json or {}
    file_path = data.get('file_path')
    patient_id = data.get('patient_id')
    
    if not file_path:
        return jsonify({'success': False, 'error': 'file_path is required'}), 400
    
    if CELERY_ENABLED:
        task = predict_disease_risk_task.delay(
            file_path=file_path,
            patient_id=patient_id
        )
        
        return jsonify({
            'success': True,
            'async': True,
            'task_id': task.id,
            'status_url': f'/api/tasks/{task.id}'
        })
    else:
        result = predict_disease_risk_task(
            file_path=file_path,
            patient_id=patient_id
        )
        return jsonify({
            'success': True,
            'async': False,
            'result': result
        })


@tasks_bp.route('/report/full', methods=['POST'])
def submit_full_report():
    """
    Submit full genetic report generation task
    ---
    tags:
      - Tasks
    """
    data = request.json or {}
    file_path = data.get('file_path')
    patient_id = data.get('patient_id')
    include_vep = data.get('include_vep', True)
    
    if not file_path:
        return jsonify({'success': False, 'error': 'file_path is required'}), 400
    
    if CELERY_ENABLED:
        task = generate_full_report_task.delay(
            file_path=file_path,
            patient_id=patient_id,
            include_vep=include_vep
        )
        
        return jsonify({
            'success': True,
            'async': True,
            'task_id': task.id,
            'status_url': f'/api/tasks/{task.id}',
            'message': 'Full report generation started'
        })
    else:
        result = generate_full_report_task(
            file_path=file_path,
            patient_id=patient_id,
            include_vep=include_vep
        )
        return jsonify({
            'success': True,
            'async': False,
            'result': result
        })


# ============================================================
# Bulk Task Operations
# ============================================================

@tasks_bp.route('/bulk/status', methods=['POST'])
def get_bulk_task_status():
    """
    Get status of multiple tasks
    ---
    tags:
      - Tasks
    """
    data = request.json or {}
    task_ids = data.get('task_ids', [])
    
    if not task_ids:
        return jsonify({'success': False, 'error': 'task_ids list is required'}), 400
    
    if not CELERY_ENABLED or not CELERY_AVAILABLE:
        return jsonify({
            'success': True,
            'message': 'Celery not enabled',
            'tasks': {tid: {'status': 'SYNC_MODE'} for tid in task_ids}
        })
    
    try:
        from celery.result import AsyncResult
        from celery_app import celery_app
        
        results = {}
        for task_id in task_ids:
            result = AsyncResult(task_id, app=celery_app)
            results[task_id] = {
                'status': result.status,
                'ready': result.ready(),
                'successful': result.successful() if result.ready() else None
            }
        
        return jsonify({
            'success': True,
            'tasks': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# Worker Management (Admin)
# ============================================================

@tasks_bp.route('/workers', methods=['GET'])
def get_workers():
    """
    Get active Celery workers info
    ---
    tags:
      - Tasks
    """
    if not CELERY_ENABLED or not CELERY_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Celery is not enabled'
        })
    
    try:
        from celery_app import celery_app
        
        inspector = celery_app.control.inspect()
        
        return jsonify({
            'success': True,
            'active': inspector.active() or {},
            'reserved': inspector.reserved() or {},
            'stats': inspector.stats() or {},
            'registered': inspector.registered() or {}
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/queues', methods=['GET'])
def get_queues():
    """
    Get Celery queue statistics
    ---
    tags:
      - Tasks
    """
    if not CELERY_ENABLED or not CELERY_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Celery is not enabled'
        })
    
    try:
        from celery_app import celery_app
        
        inspector = celery_app.control.inspect()
        
        return jsonify({
            'success': True,
            'active_queues': inspector.active_queues() or {},
            'scheduled': inspector.scheduled() or {}
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
