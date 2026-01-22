"""
Upload Routes - REST API for File Uploads
Analysis Service Microservice
"""
from flask import Blueprint, request, jsonify, current_app
import os
import sys
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename

upload_bp = Blueprint('upload', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'txt', 'ped', 'vcf', 'gz'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_ped_to_csv(ped_filepath, output_filepath=None):
    """
    Convert PED format file to CSV format
    
    PED format: Family_ID Individual_ID Paternal_ID Maternal_ID Sex Phenotype Genotypes...
    """
    try:
        # Read PED file (space/tab delimited)
        df = pd.read_csv(ped_filepath, sep=r'\s+', header=None)
        
        # Standard PED columns
        columns = ['FID', 'IID', 'PAT', 'MAT', 'SEX', 'PHENOTYPE']
        
        # If there are more columns, they are genotype data
        if len(df.columns) > 6:
            # Generate SNP column names
            snp_cols = [f'SNP_{i}' for i in range(len(df.columns) - 6)]
            columns.extend(snp_cols)
        
        df.columns = columns[:len(df.columns)]
        
        # Determine output path
        if output_filepath is None:
            output_filepath = ped_filepath.rsplit('.', 1)[0] + '.csv'
        
        # Save as CSV
        df.to_csv(output_filepath, index=False)
        
        return output_filepath, len(df)
        
    except Exception as e:
        raise Exception(f"PED conversion error: {str(e)}")


@upload_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Upload genetic data file
    
    POST /api/upload
    Form: file=<file>, user_id=<int>
    
    Returns: {"success": true, "file_path": "...", "sample_id": "..."}
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file provided"
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400
        
        # Get user_id if provided
        user_id = request.form.get('user_id', type=int)
        
        # Secure filename and add timestamp
        original_filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{original_filename}"
        
        # Create upload directory if needed
        upload_folder = current_app.config.get('UPLOAD_FOLDER', '/app/uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        
        # Convert PED to CSV if needed
        converted_path = None
        if file_ext == 'ped':
            try:
                converted_path, row_count = convert_ped_to_csv(file_path)
            except Exception as e:
                # Delete uploaded file on conversion error
                os.remove(file_path)
                return jsonify({
                    "success": False,
                    "error": f"Failed to convert PED file: {str(e)}"
                }), 400
        
        # Generate sample ID from filename
        sample_id = original_filename.rsplit('.', 1)[0]
        
        return jsonify({
            "success": True,
            "message": "File uploaded successfully",
            "file_path": converted_path or file_path,
            "original_filename": original_filename,
            "sample_id": sample_id,
            "file_size": file_size,
            "file_type": file_ext,
            "converted": converted_path is not None
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@upload_bp.route('/api/upload/validate', methods=['POST'])
def validate_file():
    """
    Validate uploaded file format
    
    POST /api/upload/validate
    Body: {"file_path": "..."}
    
    Returns: {"success": true, "valid": true, "info": {...}}
    """
    try:
        data = request.get_json() or {}
        file_path = data.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                "success": False,
                "error": "File not found"
            }), 404
        
        # Try to read the file
        try:
            df = pd.read_csv(file_path)
            
            info = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns)[:20],  # First 20 columns
                "has_id": 'IID' in df.columns or 'ID' in df.columns,
                "has_gender": 'SEX' in df.columns or 'gender' in df.columns,
                "has_population": 'Population' in df.columns
            }
            
            # Count SNP columns (columns starting with rs or PC_)
            snp_cols = [c for c in df.columns if c.startswith('rs') or c.startswith('PC_')]
            info["snp_columns"] = len(snp_cols)
            
            return jsonify({
                "success": True,
                "valid": True,
                "info": info
            }), 200
            
        except Exception as e:
            return jsonify({
                "success": True,
                "valid": False,
                "error": f"Could not parse file: {str(e)}"
            }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@upload_bp.route('/api/upload/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    """
    Delete uploaded file
    
    DELETE /api/upload/<filename>
    
    Returns: {"success": true}
    """
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', '/app/uploads')
        file_path = os.path.join(upload_folder, secure_filename(filename))
        
        if not os.path.exists(file_path):
            return jsonify({
                "success": False,
                "error": "File not found"
            }), 404
        
        os.remove(file_path)
        
        return jsonify({
            "success": True,
            "message": "File deleted"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@upload_bp.route('/api/upload/list', methods=['GET'])
def list_uploaded_files():
    """
    List uploaded files
    
    GET /api/upload/list
    
    Returns: {"success": true, "files": [...]}
    """
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', '/app/uploads')
        
        if not os.path.exists(upload_folder):
            return jsonify({
                "success": True,
                "files": []
            }), 200
        
        files = []
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # Sort by modified date (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            "success": True,
            "files": files,
            "total": len(files)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
