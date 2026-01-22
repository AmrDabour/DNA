"""
History Routes - REST API for Analysis History
Analysis Service Microservice
"""
from flask import Blueprint, request, jsonify
import os
import sys
from datetime import datetime
from sqlalchemy import or_, desc

history_bp = Blueprint('history', __name__)


@history_bp.route('/api/history', methods=['GET'])
def list_history():
    """
    List analysis history with pagination and filters
    
    GET /api/history?page=1&per_page=10&user_id=1&status=completed
    
    Returns: {"success": true, "analyses": [...], "pagination": {...}}
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from database import AnalysisHistory
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        per_page = min(per_page, 100)  # Max 100 per page
        
        # Filters
        user_id = request.args.get('user_id', type=int)
        status = request.args.get('status')
        analysis_type = request.args.get('type')
        starred = request.args.get('starred', type=bool)
        search = request.args.get('search', '').strip()
        
        # Build query
        query = AnalysisHistory.query
        
        if user_id:
            query = query.filter(or_(
                AnalysisHistory.user_id == user_id,
                AnalysisHistory.user_id == None
            ))
        
        if status:
            query = query.filter(AnalysisHistory.status == status)
        
        if analysis_type:
            query = query.filter(AnalysisHistory.analysis_type == analysis_type)
        
        if starred is not None:
            query = query.filter(AnalysisHistory.is_starred == starred)
        
        if search:
            query = query.filter(or_(
                AnalysisHistory.sample_id.ilike(f'%{search}%'),
                AnalysisHistory.file_name.ilike(f'%{search}%'),
                AnalysisHistory.tags.ilike(f'%{search}%')
            ))
        
        # Order by created_at descending
        query = query.order_by(desc(AnalysisHistory.created_at))
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "success": True,
            "analyses": [a.to_dict() for a in pagination.items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@history_bp.route('/api/history/recent', methods=['GET'])
def get_recent_analyses():
    """
    Get recent analyses
    
    GET /api/history/recent?limit=5&user_id=1
    
    Returns: {"success": true, "analyses": [...]}
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from database import AnalysisHistory
        
        limit = request.args.get('limit', 5, type=int)
        user_id = request.args.get('user_id', type=int)
        
        query = AnalysisHistory.query
        
        if user_id:
            query = query.filter(or_(
                AnalysisHistory.user_id == user_id,
                AnalysisHistory.user_id == None
            ))
        
        analyses = query.order_by(desc(AnalysisHistory.created_at)).limit(limit).all()
        
        return jsonify({
            "success": True,
            "analyses": [a.to_dict() for a in analyses]
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@history_bp.route('/api/history/starred', methods=['GET'])
def get_starred_analyses():
    """
    Get starred analyses
    
    GET /api/history/starred?user_id=1
    
    Returns: {"success": true, "analyses": [...]}
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from database import AnalysisHistory
        
        user_id = request.args.get('user_id', type=int)
        
        query = AnalysisHistory.query.filter(AnalysisHistory.is_starred == True)
        
        if user_id:
            query = query.filter(or_(
                AnalysisHistory.user_id == user_id,
                AnalysisHistory.user_id == None
            ))
        
        analyses = query.order_by(desc(AnalysisHistory.created_at)).all()
        
        return jsonify({
            "success": True,
            "analyses": [a.to_dict() for a in analyses],
            "total": len(analyses)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@history_bp.route('/api/history/stats', methods=['GET'])
def get_history_stats():
    """
    Get analysis statistics
    
    GET /api/history/stats?user_id=1
    
    Returns: {"success": true, "stats": {...}}
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from database import db, AnalysisHistory
        from sqlalchemy import func
        
        user_id = request.args.get('user_id', type=int)
        
        base_query = AnalysisHistory.query
        if user_id:
            base_query = base_query.filter(or_(
                AnalysisHistory.user_id == user_id,
                AnalysisHistory.user_id == None
            ))
        
        stats = {
            "total": base_query.count(),
            "completed": base_query.filter(AnalysisHistory.status == 'completed').count(),
            "pending": base_query.filter(AnalysisHistory.status == 'pending').count(),
            "failed": base_query.filter(AnalysisHistory.status == 'failed').count(),
            "starred": base_query.filter(AnalysisHistory.is_starred == True).count(),
        }
        
        # Analysis types count
        type_counts = db.session.query(
            AnalysisHistory.analysis_type,
            func.count(AnalysisHistory.id)
        ).group_by(AnalysisHistory.analysis_type).all()
        
        stats["by_type"] = {t: c for t, c in type_counts}
        
        # Gender prediction distribution
        gender_counts = db.session.query(
            AnalysisHistory.gender_prediction,
            func.count(AnalysisHistory.id)
        ).filter(AnalysisHistory.gender_prediction != None).group_by(AnalysisHistory.gender_prediction).all()
        
        stats["gender_distribution"] = {g: c for g, c in gender_counts}
        
        # Ancestry prediction distribution
        ancestry_counts = db.session.query(
            AnalysisHistory.ancestry_prediction,
            func.count(AnalysisHistory.id)
        ).filter(AnalysisHistory.ancestry_prediction != None).group_by(AnalysisHistory.ancestry_prediction).all()
        
        stats["ancestry_distribution"] = {a: c for a, c in ancestry_counts}
        
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@history_bp.route('/api/history/search', methods=['GET'])
def search_history():
    """
    Search analysis history
    
    GET /api/history/search?q=sample_name&user_id=1
    
    Returns: {"success": true, "results": [...]}
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from database import AnalysisHistory
        
        query_text = request.args.get('q', '').strip()
        user_id = request.args.get('user_id', type=int)
        limit = request.args.get('limit', 20, type=int)
        
        if not query_text:
            return jsonify({
                "success": False,
                "error": "Search query is required"
            }), 400
        
        query = AnalysisHistory.query.filter(or_(
            AnalysisHistory.sample_id.ilike(f'%{query_text}%'),
            AnalysisHistory.file_name.ilike(f'%{query_text}%'),
            AnalysisHistory.tags.ilike(f'%{query_text}%'),
            AnalysisHistory.gender_prediction.ilike(f'%{query_text}%'),
            AnalysisHistory.ancestry_prediction.ilike(f'%{query_text}%')
        ))
        
        if user_id:
            query = query.filter(or_(
                AnalysisHistory.user_id == user_id,
                AnalysisHistory.user_id == None
            ))
        
        results = query.order_by(desc(AnalysisHistory.created_at)).limit(limit).all()
        
        return jsonify({
            "success": True,
            "query": query_text,
            "results": [a.to_dict() for a in results],
            "count": len(results)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
