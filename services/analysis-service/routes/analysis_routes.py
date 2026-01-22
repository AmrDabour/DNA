"""
Analysis Routes - REST API for SNP Analysis
Analysis Service Microservice
"""
from flask import Blueprint, request, jsonify
import os
import sys
import pandas as pd
import json
from datetime import datetime

analysis_bp = Blueprint('analysis', __name__)


# ============================================================
# Analysis Endpoints
# ============================================================

@analysis_bp.route('/api/analysis/start', methods=['POST'])
def start_analysis():
    """
    Start a new DNA analysis
    
    POST /api/analysis/start
    Body: {"file_path": "...", "sample_id": "...", "user_id": ...}
    
    Returns: {"success": true, "analysis_id": ...}
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from database import db, AnalysisHistory
        
        data = request.get_json() or {}
        file_path = data.get('file_path')
        sample_id = data.get('sample_id', f"SAMPLE_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
        user_id = data.get('user_id')
        analysis_type = data.get('analysis_type', 'combined')
        
        if not file_path:
            return jsonify({
                "success": False,
                "error": "file_path is required"
            }), 400
        
        # Create analysis record
        analysis = AnalysisHistory(
            user_id=user_id,
            sample_id=sample_id,
            analysis_type=analysis_type,
            file_path=file_path,
            file_name=os.path.basename(file_path),
            status='pending',
            created_at=datetime.utcnow()
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Analysis started",
            "analysis_id": analysis.id,
            "sample_id": sample_id,
            "status": "pending"
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analysis_bp.route('/api/analysis/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """
    Get analysis by ID
    
    GET /api/analysis/<id>
    
    Returns: {"success": true, "analysis": {...}}
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from database import AnalysisHistory
        
        analysis = AnalysisHistory.query.get(analysis_id)
        
        if not analysis:
            return jsonify({
                "success": False,
                "error": "Analysis not found"
            }), 404
        
        return jsonify({
            "success": True,
            "analysis": analysis.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analysis_bp.route('/api/analysis/<int:analysis_id>/status', methods=['GET'])
def get_analysis_status(analysis_id):
    """
    Get analysis status
    
    GET /api/analysis/<id>/status
    
    Returns: {"success": true, "status": "...", "progress": ...}
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from database import AnalysisHistory
        
        analysis = AnalysisHistory.query.get(analysis_id)
        
        if not analysis:
            return jsonify({
                "success": False,
                "error": "Analysis not found"
            }), 404
        
        return jsonify({
            "success": True,
            "analysis_id": analysis_id,
            "status": analysis.status,
            "sample_id": analysis.sample_id,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analysis_bp.route('/api/analysis/<int:analysis_id>/results', methods=['PUT'])
def update_analysis_results(analysis_id):
    """
    Update analysis with results (called by prediction service)
    
    PUT /api/analysis/<id>/results
    Body: {"gender": {...}, "ancestry": {...}, "status": "completed"}
    
    Returns: {"success": true}
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from database import db, AnalysisHistory
        
        analysis = AnalysisHistory.query.get(analysis_id)
        
        if not analysis:
            return jsonify({
                "success": False,
                "error": "Analysis not found"
            }), 404
        
        data = request.get_json() or {}
        
        # Update gender results
        if 'gender' in data:
            gender_data = data['gender']
            analysis.gender_prediction = gender_data.get('predicted')
            analysis.gender_confidence = gender_data.get('confidence')
            analysis.gender_correct = gender_data.get('correct')
        
        # Update ancestry results
        if 'ancestry' in data:
            ancestry_data = data['ancestry']
            analysis.ancestry_prediction = ancestry_data.get('predicted')
            analysis.ancestry_code = ancestry_data.get('code')
            analysis.ancestry_confidence = ancestry_data.get('confidence')
            analysis.ancestry_correct = ancestry_data.get('correct')
        
        # Update full results
        if 'full_results' in data:
            analysis.set_full_results(data['full_results'])
        
        # Update physical characteristics
        if 'physical_characteristics' in data:
            analysis.physical_characteristics = data['physical_characteristics']
        
        # Update disease risk
        if 'disease_risk_report' in data:
            analysis.disease_risk_report = data['disease_risk_report']
        
        # Update status
        analysis.status = data.get('status', 'completed')
        analysis.processing_time = data.get('processing_time')
        analysis.snp_count = data.get('snp_count')
        analysis.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Analysis results updated",
            "analysis_id": analysis_id
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analysis_bp.route('/api/analysis/<int:analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    """
    Delete analysis
    
    DELETE /api/analysis/<id>
    
    Returns: {"success": true}
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from database import db, AnalysisHistory
        
        analysis = AnalysisHistory.query.get(analysis_id)
        
        if not analysis:
            return jsonify({
                "success": False,
                "error": "Analysis not found"
            }), 404
        
        # Delete associated file if exists
        if analysis.file_path and os.path.exists(analysis.file_path):
            try:
                os.remove(analysis.file_path)
            except:
                pass
        
        db.session.delete(analysis)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Analysis deleted"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# Tags and Notes
# ============================================================

@analysis_bp.route('/api/analysis/<int:analysis_id>/star', methods=['POST'])
def toggle_star(analysis_id):
    """
    Toggle star status for analysis
    
    POST /api/analysis/<id>/star
    Body: {"starred": true/false}
    
    Returns: {"success": true, "is_starred": true/false}
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from database import db, AnalysisHistory
        
        analysis = AnalysisHistory.query.get(analysis_id)
        
        if not analysis:
            return jsonify({
                "success": False,
                "error": "Analysis not found"
            }), 404
        
        data = request.get_json() or {}
        analysis.is_starred = data.get('starred', not analysis.is_starred)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "is_starred": analysis.is_starred
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analysis_bp.route('/api/analysis/<int:analysis_id>/tags', methods=['PUT'])
def update_tags(analysis_id):
    """
    Update tags for analysis
    
    PUT /api/analysis/<id>/tags
    Body: {"tags": ["tag1", "tag2"]}
    
    Returns: {"success": true, "tags": [...]}
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from database import db, AnalysisHistory
        
        analysis = AnalysisHistory.query.get(analysis_id)
        
        if not analysis:
            return jsonify({
                "success": False,
                "error": "Analysis not found"
            }), 404
        
        data = request.get_json() or {}
        tags = data.get('tags', [])
        analysis.tags = ','.join(tags)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "tags": analysis.get_tags()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analysis_bp.route('/api/analysis/<int:analysis_id>/notes', methods=['PUT'])
def update_notes(analysis_id):
    """
    Update notes for analysis
    
    PUT /api/analysis/<id>/notes
    Body: {"notes": "..."}
    
    Returns: {"success": true}
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from database import db, AnalysisHistory
        
        analysis = AnalysisHistory.query.get(analysis_id)
        
        if not analysis:
            return jsonify({
                "success": False,
                "error": "Analysis not found"
            }), 404
        
        data = request.get_json() or {}
        analysis.notes = data.get('notes', '')
        db.session.commit()
        
        return jsonify({
            "success": True,
            "notes": analysis.notes
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
