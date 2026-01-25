"""
VEP Routes - API endpoints for Variant Effect Predictor integration
"""
from flask import Blueprint, jsonify, request, render_template
import os

# Create blueprints
vep_bp = Blueprint('vep', __name__, url_prefix='/api/vep')
vep_page_bp = Blueprint('vep_pages', __name__)


# ============================================================
# API Routes
# ============================================================

@vep_bp.route('/status', methods=['GET'])
def get_vep_status():
    """
    Check VEP service status and connectivity
    ---
    tags:
      - VEP
    responses:
      200:
        description: VEP service status
    """
    from services.vep_service import vep_service
    
    status = vep_service.get_service_status()
    return jsonify({"success": True, **status})


@vep_bp.route('/cache-stats', methods=['GET'])
def get_cache_stats():
    """
    Get VEP cache statistics
    ---
    tags:
      - VEP
    responses:
      200:
        description: Cache statistics
    """
    from services.vep_service import vep_service
    
    stats = vep_service.get_cache_stats()
    return jsonify({"success": True, **stats})


@vep_bp.route('/analyze-snp', methods=['POST'])
def analyze_single_snp():
    """
    Analyze a single SNP using Ensembl VEP
    ---
    tags:
      - VEP
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            rs_id:
              type: string
              description: SNP rsID (e.g., rs4040617)
    responses:
      200:
        description: VEP annotation result
    """
    from services.vep_service import vep_service
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400
    
    rs_id = data.get('rs_id')
    if not rs_id:
        return jsonify({"success": False, "error": "rs_id required"}), 400
    
    result = vep_service.get_single_variant(rs_id)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400 if "Invalid" in result.get("error", "") else 500


@vep_bp.route('/analyze-batch', methods=['POST'])
def analyze_batch_snps():
    """
    Analyze multiple SNPs using Ensembl VEP (max 200 per request)
    ---
    tags:
      - VEP
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            rs_ids:
              type: array
              items:
                type: string
              description: List of SNP rsIDs
    responses:
      200:
        description: VEP annotation results
    """
    from services.vep_service import vep_service
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400
    
    rs_ids = data.get('rs_ids', [])
    if not rs_ids:
        return jsonify({"success": False, "error": "rs_ids list required"}), 400
    
    if not isinstance(rs_ids, list):
        return jsonify({"success": False, "error": "rs_ids must be a list"}), 400
    
    result = vep_service.get_batch_variants(rs_ids)
    return jsonify(result)


@vep_bp.route('/analyze-file', methods=['POST'])
def analyze_patient_file():
    """
    Analyze variants from an uploaded patient CSV file
    ---
    tags:
      - VEP
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            file_path:
              type: string
              description: Path to the patient CSV file
            limit:
              type: integer
              description: Optional limit on SNPs to analyze (default 100)
    responses:
      200:
        description: VEP analysis results with statistics
    """
    from services.vep_service import vep_service
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400
    
    file_path = data.get('file_path')
    if not file_path:
        return jsonify({"success": False, "error": "file_path required"}), 400
    
    # Security: Ensure file is in uploads directory
    uploads_dir = os.path.abspath(os.environ.get('UPLOAD_DIR', './uploads'))
    requested_path = os.path.abspath(file_path)
    
    if not requested_path.startswith(uploads_dir):
        # Allow relative paths within uploads
        file_path = os.path.join(uploads_dir, os.path.basename(file_path))
    
    # If file doesn't exist, try with .csv extension (for converted PED files)
    if not os.path.exists(file_path):
        # Try .csv version if .ped was specified
        if file_path.endswith('.ped'):
            csv_path = file_path.rsplit('.', 1)[0] + '.csv'
            if os.path.exists(csv_path):
                file_path = csv_path
        # Also try adding .csv if no extension
        elif not file_path.endswith('.csv'):
            csv_path = file_path + '.csv'
            if os.path.exists(csv_path):
                file_path = csv_path
    
    limit = data.get('limit', 100)
    
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 100
    
    result = vep_service.analyze_patient_csv(file_path, limit=limit)
    return jsonify(result)


@vep_bp.route('/clear-cache', methods=['POST'])
def clear_expired_cache():
    """
    Clear expired VEP cache entries
    ---
    tags:
      - VEP
    responses:
      200:
        description: Cache clearing result
    """
    from services.vep_service import vep_service
    
    result = vep_service.clear_expired_cache()
    return jsonify({"success": True, **result})


# ============================================================
# Page Routes
# ============================================================

@vep_page_bp.route('/vep-analysis')
def vep_analysis_page():
    """VEP Analysis page"""
    from services.vep_service import vep_service
    
    # Get available sample files
    uploads_dir = os.environ.get('UPLOAD_DIR', './uploads')
    sample_files = []
    
    if os.path.exists(uploads_dir):
        for f in os.listdir(uploads_dir):
            if f.endswith('.csv'):
                sample_files.append(f)
    
    sample_files.sort()
    
    # Get VEP service status
    status = vep_service.get_service_status()
    cache_stats = vep_service.get_cache_stats()
    
    return render_template(
        'vep_analysis.html',
        sample_files=sample_files,
        vep_status=status,
        cache_stats=cache_stats
    )


@vep_page_bp.route('/vep-results/<sample_file>')
def vep_results_page(sample_file):
    """VEP Results page for a specific sample"""
    from services.vep_service import vep_service
    
    uploads_dir = os.environ.get('UPLOAD_DIR', './uploads')
    file_path = os.path.join(uploads_dir, sample_file)
    
    if not os.path.exists(file_path):
        return render_template('404.html', message=f"Sample file not found: {sample_file}"), 404
    
    # Get limit from query params
    limit = request.args.get('limit', 50, type=int)
    
    # Run VEP analysis
    result = vep_service.analyze_patient_csv(file_path, limit=limit)
    
    return render_template(
        'vep_analysis.html',
        sample_file=sample_file,
        analysis_result=result,
        limit=limit
    )

