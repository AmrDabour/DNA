"""
History Routes - Analysis history management and retrieval
"""
import os
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import desc, or_

history_bp = Blueprint('history', __name__)


@history_bp.route('/history')
def history_page():
    """Display analysis history page"""
    return render_template('history.html')


@history_bp.route('/api/history')
def get_history():
    """API to get analysis history with filtering and pagination"""
    from database import db, AnalysisHistory
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Filter parameters
    search = request.args.get('search', '').strip()
    analysis_type = request.args.get('type', '')
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    starred_only = request.args.get('starred', 'false').lower() == 'true'
    
    # Build query
    query = AnalysisHistory.query
    
    # Filter by user if authenticated
    if current_user.is_authenticated:
        # Show user's analyses and public ones
        query = query.filter(
            or_(AnalysisHistory.user_id == current_user.id, AnalysisHistory.user_id == None)
        )
    
    # Search filter
    if search:
        query = query.filter(
            or_(
                AnalysisHistory.sample_id.ilike(f'%{search}%'),
                AnalysisHistory.file_name.ilike(f'%{search}%'),
                AnalysisHistory.ancestry_prediction.ilike(f'%{search}%'),
                AnalysisHistory.tags.ilike(f'%{search}%'),
                AnalysisHistory.notes.ilike(f'%{search}%')
            )
        )
    
    # Type filter
    if analysis_type:
        query = query.filter(AnalysisHistory.analysis_type == analysis_type)
    
    # Status filter
    if status:
        query = query.filter(AnalysisHistory.status == status)
    
    # Date filters
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(AnalysisHistory.created_at >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(AnalysisHistory.created_at < to_date)
        except ValueError:
            pass
    
    # Starred filter
    if starred_only:
        query = query.filter(AnalysisHistory.is_starred == True)
    
    # Order by most recent
    query = query.order_by(desc(AnalysisHistory.created_at))
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'analyses': [analysis.to_dict() for analysis in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@history_bp.route('/api/history/<int:analysis_id>')
def get_analysis(analysis_id):
    """Get a specific analysis by ID"""
    from database import AnalysisHistory
    
    analysis = AnalysisHistory.query.get_or_404(analysis_id)
    
    # Include full results
    result = analysis.to_dict()
    result['full_results'] = analysis.get_full_results()
    
    return jsonify({
        'success': True,
        'analysis': result
    })


@history_bp.route('/api/history/<int:analysis_id>/star', methods=['POST'])
def toggle_star(analysis_id):
    """Toggle star status of an analysis"""
    from database import db, AnalysisHistory
    
    analysis = AnalysisHistory.query.get_or_404(analysis_id)
    
    # Check permission
    if current_user.is_authenticated and analysis.user_id != current_user.id and analysis.user_id is not None:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    analysis.is_starred = not analysis.is_starred
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_starred': analysis.is_starred
    })


@history_bp.route('/api/history/<int:analysis_id>/tags', methods=['POST'])
def update_tags(analysis_id):
    """Update tags for an analysis"""
    from database import db, AnalysisHistory
    
    analysis = AnalysisHistory.query.get_or_404(analysis_id)
    
    # Check permission
    if current_user.is_authenticated and analysis.user_id != current_user.id and analysis.user_id is not None:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    data = request.get_json()
    tags = data.get('tags', [])
    
    analysis.tags = ','.join(tags) if tags else ''
    db.session.commit()
    
    return jsonify({
        'success': True,
        'tags': analysis.get_tags()
    })


@history_bp.route('/api/history/<int:analysis_id>/notes', methods=['POST'])
def update_notes(analysis_id):
    """Update notes for an analysis"""
    from database import db, AnalysisHistory
    
    analysis = AnalysisHistory.query.get_or_404(analysis_id)
    
    # Check permission
    if current_user.is_authenticated and analysis.user_id != current_user.id and analysis.user_id is not None:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    data = request.get_json()
    analysis.notes = data.get('notes', '')
    db.session.commit()
    
    return jsonify({
        'success': True,
        'notes': analysis.notes
    })


@history_bp.route('/api/history/<int:analysis_id>', methods=['DELETE'])
@login_required
def delete_analysis(analysis_id):
    """Delete an analysis"""
    from database import db, AnalysisHistory
    
    analysis = AnalysisHistory.query.get_or_404(analysis_id)
    
    # Check permission
    if analysis.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    db.session.delete(analysis)
    db.session.commit()
    
    return jsonify({'success': True})


@history_bp.route('/api/history/stats')
def get_history_stats():
    """Get statistics about analysis history"""
    from database import db, AnalysisHistory
    from sqlalchemy import func
    
    # Base query
    query = AnalysisHistory.query
    
    if current_user.is_authenticated:
        query = query.filter(
            or_(AnalysisHistory.user_id == current_user.id, AnalysisHistory.user_id == None)
        )
    
    # Total count
    total = query.count()
    
    # Count by type
    type_counts = db.session.query(
        AnalysisHistory.analysis_type,
        func.count(AnalysisHistory.id)
    ).group_by(AnalysisHistory.analysis_type).all()
    
    # Count by status
    status_counts = db.session.query(
        AnalysisHistory.status,
        func.count(AnalysisHistory.id)
    ).group_by(AnalysisHistory.status).all()
    
    # Recent analyses (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_count = query.filter(AnalysisHistory.created_at >= week_ago).count()
    
    # Starred count
    starred_count = query.filter(AnalysisHistory.is_starred == True).count()
    
    return jsonify({
        'success': True,
        'stats': {
            'total': total,
            'by_type': dict(type_counts),
            'by_status': dict(status_counts),
            'recent_week': recent_count,
            'starred': starred_count
        }
    })


@history_bp.route('/history/view/<int:analysis_id>')
def view_analysis(analysis_id):
    """View a specific analysis result"""
    from database import AnalysisHistory
    
    analysis = AnalysisHistory.query.get_or_404(analysis_id)
    full_results = analysis.get_full_results() or {}
    
    # Format results for the prediction_results template
    results = {
        'gender': None,
        'ancestry': None
    }
    
    if analysis.gender_prediction:
        results['gender'] = {
            'predicted': analysis.gender_prediction,
            'confidence': analysis.gender_confidence,
            'correct': analysis.gender_correct
        }
    
    if analysis.ancestry_prediction:
        results['ancestry'] = {
            'predicted': analysis.ancestry_prediction,
            'code': analysis.ancestry_code,
            'description': '',
            'confidence': analysis.ancestry_confidence,
            'correct': analysis.ancestry_correct
        }
    
    # Build gemini_prediction with physical characteristics if available
    gemini_prediction = None
    if analysis.physical_characteristics:
        gemini_prediction = {'success': True, 'characteristics': analysis.physical_characteristics}
    
    # Build disease_report if available
    disease_report = None
    if analysis.disease_risk_report:
        disease_report = {'success': True, 'report': analysis.disease_risk_report}
    
    # Get generated image from full_results if available
    generated_image = None
    if full_results.get('generated_image_path'):
        # Extract just the filename from the path (handles both / and \)
        raw_path = full_results.get('generated_image_path')
        image_filename = os.path.basename(raw_path)
        
        # Check if file exists in uploads folder
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        full_image_path = os.path.join(uploads_dir, image_filename)
        
        print(f"🔍 Image lookup: filename={image_filename}, exists={os.path.exists(full_image_path)}")
        
        if os.path.exists(full_image_path):
            generated_image = {
                'success': True,
                'image_filename': image_filename,  # Just the filename for URL building
                'image_path': raw_path,  # Original path for reference
                'description': full_results.get('generated_image_description', 'AI-generated portrait')
            }
        else:
            print(f"⚠️ Image file not found: {full_image_path}")
    
    # Get user info for PDF report
    user_info = None
    if current_user.is_authenticated:
        user_info = {
            'name': current_user.username,
            'email': getattr(current_user, 'email', None)
        }
    
    return render_template(
        'prediction_results.html',
        sample_id=analysis.sample_id,
        results=results,
        full_results=full_results,
        gemini_prediction=gemini_prediction,
        disease_report=disease_report,
        generated_image=generated_image,
        raw_snp_prediction=bool(full_results),
        from_history=True,
        analysis_id=analysis_id,
        user_info=user_info
    )


def save_analysis_to_history(sample_id, results, full_results=None, file_name=None, user_id=None):
    """Helper function to save an analysis to history"""
    from database import db, AnalysisHistory
    
    analysis = AnalysisHistory(
        user_id=user_id if user_id else (current_user.id if current_user.is_authenticated else None),
        sample_id=sample_id,
        analysis_type='combined',
        file_name=file_name
    )
    
    # Gender Prediction
    if results.get('gender'):
        analysis.gender_prediction = results['gender'].get('predicted')
        analysis.gender_confidence = results['gender'].get('confidence')
        analysis.gender_correct = results['gender'].get('correct')
    
    # Ancestry prediction
    if results.get('ancestry'):
        analysis.ancestry_prediction = results['ancestry'].get('predicted')
        analysis.ancestry_code = results['ancestry'].get('code')
        analysis.ancestry_confidence = results['ancestry'].get('confidence')
        analysis.ancestry_correct = results['ancestry'].get('correct')
    
    # Full results
    if full_results:
        analysis.set_full_results(full_results)
        if full_results.get('total_processing_time'):
            analysis.processing_time = full_results['total_processing_time']
    
    db.session.add(analysis)
    db.session.commit()
    
    return analysis


# ============================================================================
# PDF Report Generation Endpoints
# ============================================================================

@history_bp.route('/api/reports/<int:analysis_id>/pdf')
def generate_pdf_report(analysis_id):
    """
    Generate a professional PDF medical report for an analysis
    
    Args:
        analysis_id: The ID of the analysis to generate report for
        
    Returns:
        PDF file download or JSON error
    """
    from flask import send_file, make_response
    from database import db, AnalysisHistory
    from services.pdf_service import generate_medical_report, get_report_filename
    
    # Get the analysis
    analysis = AnalysisHistory.query.get_or_404(analysis_id)
    
    # Check access permissions
    if current_user.is_authenticated:
        # User can access their own analyses or public ones
        if analysis.user_id and analysis.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    # Prepare analysis data
    analysis_data = analysis.to_dict()
    analysis_data['full_results'] = analysis.get_full_results()
    
    # Prepare user info
    user_info = {}
    if current_user.is_authenticated:
        user_info = {
            'name': current_user.full_name or current_user.username,
            'email': current_user.email
        }
    elif analysis.user_id:
        # Try to get user info from the analysis owner
        from database import User
        user = User.query.get(analysis.user_id)
        if user:
            user_info = {
                'name': user.full_name or user.username,
                'email': user.email
            }
    
    # Generate PDF filename
    filename = get_report_filename(analysis.sample_id, analysis_id)
    
    # Define save path for caching
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    save_path = os.path.join(reports_dir, filename)
    
    # Check if cached report exists and is recent (less than 1 hour old)
    use_cached = False
    if os.path.exists(save_path):
        file_age = datetime.now().timestamp() - os.path.getmtime(save_path)
        if file_age < 3600:  # 1 hour cache
            use_cached = True
    
    try:
        if use_cached:
            # Return cached file
            return send_file(
                save_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        else:
            # Generate new PDF
            pdf_buffer, filepath = generate_medical_report(
                analysis_data=analysis_data,
                user_info=user_info,
                save_path=save_path
            )
            
            # Return the file
            return send_file(
                filepath,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': f'Failed to generate PDF report: {str(e)}'
        }), 500


@history_bp.route('/api/reports/<int:analysis_id>/pdf/preview')
def preview_pdf_report(analysis_id):
    """
    Generate and return PDF for inline preview (not download)
    """
    from flask import send_file
    from database import db, AnalysisHistory
    from services.pdf_service import generate_medical_report, get_report_filename
    
    analysis = AnalysisHistory.query.get_or_404(analysis_id)
    
    # Check access permissions
    if current_user.is_authenticated:
        if analysis.user_id and analysis.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    # Prepare data
    analysis_data = analysis.to_dict()
    analysis_data['full_results'] = analysis.get_full_results()
    
    user_info = {}
    if current_user.is_authenticated:
        user_info = {
            'name': current_user.full_name or current_user.username,
            'email': current_user.email
        }
    
    try:
        pdf_buffer, _ = generate_medical_report(
            analysis_data=analysis_data,
            user_info=user_info,
            save_path=None  # Don't save, just return buffer
        )
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=False,  # Inline display
            download_name=get_report_filename(analysis.sample_id, analysis_id)
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': f'Failed to generate PDF preview: {str(e)}'
        }), 500


@history_bp.route('/api/reports/sample/<sample_id>/pdf')
def generate_pdf_by_sample(sample_id):
    """
    Generate PDF report for the most recent analysis of a sample
    
    Args:
        sample_id: The sample ID to generate report for
        
    Returns:
        PDF file download or JSON error
    """
    from flask import send_file
    from database import db, AnalysisHistory
    from services.pdf_service import generate_medical_report, get_report_filename
    
    # Find the most recent analysis for this sample
    print(f"🔍 PDF Request: Looking for sample_id={sample_id}")
    query = AnalysisHistory.query.filter_by(sample_id=sample_id)
    
    if current_user.is_authenticated:
        query = query.filter(
            or_(AnalysisHistory.user_id == current_user.id, AnalysisHistory.user_id == None)
        )
    
    analysis = query.order_by(desc(AnalysisHistory.created_at)).first()
    
    # If not found, try partial match (sample_id might contain timestamp or extra info)
    if not analysis:
        print(f"⚠️ No exact match, trying partial match for: {sample_id}")
        # Try to find by basename (without extension or timestamp)
        base_sample_id = sample_id.split('_')[0] if '_' in sample_id else sample_id
        
        partial_query = AnalysisHistory.query.filter(
            AnalysisHistory.sample_id.ilike(f'%{base_sample_id}%')
        )
        if current_user.is_authenticated:
            partial_query = partial_query.filter(
                or_(AnalysisHistory.user_id == current_user.id, AnalysisHistory.user_id == None)
            )
        analysis = partial_query.order_by(desc(AnalysisHistory.created_at)).first()
        
        if analysis:
            print(f"✅ Found via partial match: {analysis.sample_id}")
        else:
            # List similar sample_ids for debugging
            similar = AnalysisHistory.query.filter(
                AnalysisHistory.sample_id.ilike(f'%{base_sample_id[:8]}%')
            ).limit(5).all()
            print(f"📋 Similar sample_ids found: {[a.sample_id for a in similar]}")
    
    if not analysis:
        print(f"❌ No analysis found for sample_id={sample_id}")
        return jsonify({'success': False, 'error': 'Analysis not found'}), 404
    
    # Prepare data
    analysis_data = analysis.to_dict()
    analysis_data['full_results'] = analysis.get_full_results()
    
    user_info = {}
    if current_user.is_authenticated:
        user_info = {
            'name': current_user.full_name or current_user.username,
            'email': current_user.email
        }
    
    filename = get_report_filename(sample_id, analysis.id)
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    save_path = os.path.join(reports_dir, filename)
    
    try:
        pdf_buffer, filepath = generate_medical_report(
            analysis_data=analysis_data,
            user_info=user_info,
            save_path=save_path
        )
        
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': f'Failed to generate PDF report: {str(e)}'
        }), 500
