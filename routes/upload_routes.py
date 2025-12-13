"""
Upload Routes - File upload and SNP processing endpoints
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user
import os
import sys
import json
import datetime
import time
import re
import subprocess
import shutil
from werkzeug.utils import secure_filename
from database.models import db, AnalysisHistory

# Create blueprint with no prefix for page routes
upload_bp = Blueprint('upload', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"csv", "ped"}


def allowed_file(filename):
    """Check if a file has allowed extension"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_analysis_to_database(patient_id, file_path, result_data, processing_time, user_id=None):
    """Save analysis results to the database
    
    Args:
        patient_id: The patient/sample identifier
        file_path: Path to the uploaded file
        result_data: Dictionary containing prediction results
        processing_time: Time taken for processing
        user_id: ID of the user who uploaded the file (None for anonymous)
    """
    try:
        # Extract gender prediction
        gender_prediction = None
        gender_confidence = None
        sex_pred = result_data.get("sex_prediction") or result_data.get("gender_prediction")
        if sex_pred:
            gender_prediction = sex_pred.get("predicted_sex")
            male_conf = sex_pred.get("male_confidence")
            female_conf = sex_pred.get("female_confidence")
            if male_conf is not None and female_conf is not None:
                gender_confidence = max(float(male_conf or 0), float(female_conf or 0)) * 100
            elif sex_pred.get("match_rate"):
                gender_confidence = float(sex_pred.get("match_rate", 0)) * 100 if sex_pred.get("match_rate", 0) <= 1 else float(sex_pred.get("match_rate", 0))

        # Extract ancestry prediction
        ancestry_prediction = None
        ancestry_code = None
        ancestry_confidence = None
        region_pred = result_data.get("region_prediction")
        if region_pred:
            pred_obj = region_pred.get("prediction", {})
            if isinstance(pred_obj, dict):
                ancestry_prediction = pred_obj.get("predicted_population")
                ancestry_code = ancestry_prediction  # Use same value for code
                match_rate = pred_obj.get("match_rate")
                if match_rate is not None:
                    ancestry_confidence = float(match_rate) * 100 if match_rate <= 1 else float(match_rate)

        # Create AnalysisHistory record with user association
        analysis = AnalysisHistory(
            user_id=user_id,  # Associate with the uploading user
            sample_id=patient_id,
            analysis_type='combined',
            gender_prediction=gender_prediction,
            gender_confidence=gender_confidence,
            ancestry_prediction=ancestry_prediction,
            ancestry_code=ancestry_code,
            ancestry_confidence=ancestry_confidence,
            file_name=os.path.basename(file_path),
            file_path=file_path,
            processing_time=processing_time,
            status='completed'
        )
        
        # Store full results as JSON
        analysis.set_full_results(result_data)
        
        db.session.add(analysis)
        db.session.commit()
        
        print(f"✅ Analysis saved to database: {patient_id}")
        return analysis
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving to database: {e}")
        raise


# ============================================================
# Page Routes
# ============================================================

@upload_bp.route("/upload", methods=["GET", "POST"])
def upload_file():
    """
    Upload SNP data file for genetic prediction
    ---
    tags:
      - Upload
    responses:
      200:
        description: Upload page or redirect to processing
    """
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part", "error")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file", "error")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
            
            # Ensure upload folder exists
            os.makedirs(upload_folder, exist_ok=True)
            
            # If it's a .ped file, rename to .csv
            if filename.lower().endswith('.ped'):
                filename = filename[:-4] + '.csv'
            
            file_path = os.path.join(upload_folder, filename)
            
            # Handle existing file - add timestamp if file exists and can't be removed
            if os.path.exists(file_path):
                try:
                    # Try to remove existing file first
                    os.remove(file_path)
                except (PermissionError, OSError):
                    # If we can't remove it, rename the new file with timestamp
                    name, ext = os.path.splitext(filename)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{name}_{timestamp}{ext}"
                    file_path = os.path.join(upload_folder, filename)
            
            try:
                file.save(file_path)
            except PermissionError as e:
                flash(f"Permission denied: Cannot save file. The file may be open in another program.", "error")
                return redirect(request.url)
            except Exception as e:
                flash(f"Error saving file: {str(e)}", "error")
                return redirect(request.url)
            
            patient_id = os.path.splitext(os.path.basename(file_path))[0]
            return redirect(url_for("upload.process_snp_data", file_path=file_path, patient_id=patient_id))

    return render_template("upload.html")


@upload_bp.route("/process_snp_data")
def process_snp_data():
    """
    Loading page that shows progress while processing SNP data
    ---
    tags:
      - Upload
    """
    file_path = request.args.get("file_path")
    patient_id = request.args.get("patient_id")

    if not file_path or not patient_id:
        flash("Missing file path or patient ID", "error")
        return redirect(url_for("index"))

    return render_template("processing.html", file_path=file_path, patient_id=patient_id)


# ============================================================
# API Routes
# ============================================================

@upload_bp.route("/api/upload_sample", methods=["POST"])
def api_upload_sample():
    """
    Upload a sample file via API and return JSON response
    ---
    tags:
      - Upload
    responses:
      200:
        description: Upload result
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part"})
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file"})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
        
        # Ensure upload folder exists
        os.makedirs(upload_folder, exist_ok=True)
        
        # If it's a .ped file, rename to .csv
        if filename.lower().endswith('.ped'):
            filename = filename[:-4] + '.csv'
        
        file_path = os.path.join(upload_folder, filename)
        
        # Handle existing file - add timestamp if file exists
        if os.path.exists(file_path):
            try:
                # Try to remove existing file first
                os.remove(file_path)
            except (PermissionError, OSError) as e:
                # If we can't remove it, rename the new file with timestamp
                from datetime import datetime
                name, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{name}_{timestamp}{ext}"
                file_path = os.path.join(upload_folder, filename)
        
        try:
            file.save(file_path)
        except PermissionError as e:
            return jsonify({
                "success": False,
                "error": f"Permission denied: Cannot save file. The file may be open in another program. Error: {str(e)}"
            }), 403
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error saving file: {str(e)}"
            }), 500
        
        return jsonify({
            "success": True,
            "filename": filename,
            "file_path": file_path
        })
    
    return jsonify({"success": False, "error": "Invalid file type. Only CSV and PED files are allowed."})


@upload_bp.route("/api/process_snp_file", methods=["POST"])
def process_snp_file():
    """
    Process SNP file and run genetic predictions
    ---
    tags:
      - Upload
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            file_path:
              type: string
              description: Path to the SNP CSV file
    responses:
      200:
        description: Processing result
    """
    try:
        data = request.json
        file_path = data.get("file_path")

        if not file_path or not os.path.exists(file_path):
            return jsonify({"success": False, "error": "File not found"})

        patient_id = os.path.splitext(os.path.basename(file_path))[0]
        start_time = time.time()

        # Use model packages from new_model directory (contains metadata.json and encoding_function.py)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sex_package_dir = os.path.join(project_root, "new_model", "gender_prediction_package")
        region_package_dir = os.path.join(project_root, "new_model", "region_prediction_package")

        script_path = os.path.join(project_root, "new_model", "predict_patient.py")
        if not os.path.exists(script_path):
            return jsonify({"success": False, "error": "predict_patient.py script not found"})

        abs_file_path = os.path.abspath(file_path)
        abs_sex_package_dir = os.path.abspath(sex_package_dir)
        abs_region_package_dir = os.path.abspath(region_package_dir)

        cmd = [
            sys.executable,
            script_path,
            "--gender-package-dir", abs_sex_package_dir,
            "--region-package-dir", abs_region_package_dir,
            "--sample", abs_file_path,
            "--prediction-type", "both",
        ]

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        try:
            process_result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=env, text=True, encoding='utf-8', errors='replace', check=False, timeout=300,
            )
            stdout = process_result.stdout if hasattr(process_result, "stdout") else ""
            # stderr available but not used currently
        except subprocess.TimeoutExpired:
            return jsonify({"success": False, "error": "Process timed out after 5 minutes"})
        except Exception as e:
            return jsonify({"success": False, "error": f"Error executing process: {str(e)}"})

        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
        result_folder = os.path.join(os.getcwd(), "result")
        
        # Check result folder first (primary location)
        result_file = os.path.join(result_folder, f"{patient_id}_combined_prediction_results.json")
        alt_result_file = os.path.join(os.path.dirname(file_path), f"{patient_id}_combined_prediction_results.json")
        upload_result_file = os.path.join(upload_folder, f"{patient_id}_combined_prediction_results.json")
        root_result_file = f"{patient_id}_combined_prediction_results.json"

        found_result_file = None
        for possible_file in [result_file, alt_result_file, upload_result_file, root_result_file]:
            if os.path.exists(possible_file):
                found_result_file = possible_file
                break

        if not found_result_file:
            extracted_results = {
                "patient_id": patient_id,
                "file_name": os.path.basename(file_path),
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_processing_time": time.time() - start_time,
                "gender_prediction": {"predicted_sex": "Unknown"},
                "region_prediction": {"prediction": {"predicted_population": "Unknown"}},
            }

            sex_match = re.search(r"Predicted Gender: ([A-Za-z]+)", stdout) if stdout else None
            if sex_match:
                extracted_results["gender_prediction"]["predicted_sex"] = sex_match.group(1)

            region_match = re.search(r"Predicted Population: ([A-Z]+)", stdout) if stdout else None
            if region_match:
                extracted_results["region_prediction"]["prediction"]["predicted_population"] = region_match.group(1)

            # Save to result folder with user-specific naming for logged-in users
            os.makedirs(result_folder, exist_ok=True)
            user_id = current_user.id if current_user.is_authenticated else None
            if user_id:
                result_filename = f"{patient_id}_user{user_id}_combined_prediction_results.json"
            else:
                result_filename = f"{patient_id}_combined_prediction_results.json"
            final_result_file = os.path.join(result_folder, result_filename)
            
            # Save extracted results to JSON file
            with open(final_result_file, 'w') as f:
                json.dump(extracted_results, f, indent=2)
            
            # Save to database with user association
            processing_time = time.time() - start_time
            try:
                save_analysis_to_database(patient_id, file_path, extracted_results, processing_time, user_id)
            except Exception as db_error:
                print(f"Warning: Could not save to database: {db_error}")
            
            return jsonify({
                "success": True,
                "patient_id": patient_id,
                "result_file": final_result_file,
                "processing_time": processing_time,
                "used_extracted_data": True,
            })

        try:
            with open(found_result_file, "r") as f:
                result_data = json.load(f)  # Validate JSON is readable and load data

            # Copy to result folder with user-specific naming for logged-in users
            os.makedirs(result_folder, exist_ok=True)
            user_id = current_user.id if current_user.is_authenticated else None
            if user_id:
                result_filename = f"{patient_id}_user{user_id}_combined_prediction_results.json"
            else:
                result_filename = f"{patient_id}_combined_prediction_results.json"
            final_result_file = os.path.join(result_folder, result_filename)
            if found_result_file != final_result_file:
                shutil.copy2(found_result_file, final_result_file)

            # Save to database with user association
            processing_time = time.time() - start_time
            try:
                save_analysis_to_database(patient_id, file_path, result_data, processing_time, user_id)
            except Exception as db_error:
                print(f"Warning: Could not save to database: {db_error}")

            return jsonify({
                "success": True,
                "patient_id": patient_id,
                "result_file": final_result_file,
                "processing_time": processing_time,
                "used_extracted_data": False,
            })

        except json.JSONDecodeError as e:
            return jsonify({"success": False, "error": f"Invalid JSON in results file: {str(e)}"})
        except Exception as e:
            return jsonify({"success": False, "error": f"Error processing results: {str(e)}"})

    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()})
