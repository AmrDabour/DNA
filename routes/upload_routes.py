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
import pandas as pd
from werkzeug.utils import secure_filename
from database.models import db, AnalysisHistory
from routes.notifications_routes import notify_user

# Create blueprint with no prefix for page routes
upload_bp = Blueprint('upload', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"csv", "ped"}


def allowed_file(filename):
    """Check if a file has allowed extension"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_ped_to_csv(ped_file_path, map_file_path=None):
    """
    Convert PED file format to CSV format expected by the prediction models.
    
    PED format (PLINK):
    - Space/tab delimited
    - Columns: FamilyID, IndividualID, PaternalID, MaternalID, Sex(1=male,2=female), Phenotype, Genotypes...
    - Genotypes are pairs of alleles (A1 A2 for each SNP)
    
    MAP format (optional, provides SNP info):
    - Columns: Chromosome, SNP_ID, Genetic_Distance, Position
    
    Args:
        ped_file_path: Path to the .ped file
        map_file_path: Path to the .map file (optional, will look for it automatically)
    
    Returns:
        Path to the converted CSV file
    """
    print(f"Processing file: {ped_file_path}")
    
    # First, check if this is actually a CSV file with .ped extension
    try:
        # Try reading as CSV first
        test_df = pd.read_csv(ped_file_path, nrows=5)
        # If it has typical CSV columns like SNP, CHR, etc., it's actually a CSV
        csv_columns = {'SNP', 'CHR', 'POS', 'Allele1', 'Allele2', 'Patient_ID'}
        if csv_columns.intersection(set(test_df.columns)):
            print(f"File appears to be CSV format with .ped extension, copying as-is")
            # Just rename to .csv
            csv_file_path = ped_file_path.rsplit('.', 1)[0] + '.csv'
            if ped_file_path != csv_file_path:
                import shutil
                shutil.copy2(ped_file_path, csv_file_path)
            return csv_file_path
    except Exception as e:
        print(f"Not a CSV file, treating as PLINK PED format: {e}")
    
    print(f"Converting PLINK PED file: {ped_file_path}")
    
    # Try to find associated .map file if not provided
    if map_file_path is None:
        base_path = ped_file_path.rsplit('.', 1)[0]
        potential_map = base_path + '.map'
        if os.path.exists(potential_map):
            map_file_path = potential_map
            print(f"Found associated MAP file: {map_file_path}")
    
    # Read PED file - try different delimiters
    ped_data = None
    for delimiter in ['\t', ' ', ',']:
        try:
            ped_data = pd.read_csv(ped_file_path, delimiter=delimiter, header=None, dtype=str)
            if ped_data.shape[1] > 6:  # Valid PED should have at least 6 + genotype columns
                break
        except:
            continue
    
    if ped_data is None or ped_data.shape[1] <= 6:
        raise ValueError("Could not parse PED file. Please ensure it's in valid PLINK PED format.")
    
    print(f"PED file has {len(ped_data)} samples and {ped_data.shape[1]} columns")
    
    # Extract metadata from first 6 columns
    family_id = ped_data.iloc[0, 0]
    individual_id = ped_data.iloc[0, 1]
    sex_code = ped_data.iloc[0, 4]  # 1=male, 2=female, 0=unknown
    
    # Map sex code to our format (1=male, 2=female)
    sex_value = int(sex_code) if sex_code in ['1', '2'] else 0
    
    # Genotype columns start from index 6
    genotype_cols = ped_data.iloc[:, 6:]
    num_snps = genotype_cols.shape[1] // 2
    print(f"Found {num_snps} SNPs in PED file")
    
    # Read MAP file for SNP information if available
    snp_info = []
    if map_file_path and os.path.exists(map_file_path):
        try:
            map_data = pd.read_csv(map_file_path, delimiter='\t', header=None, dtype=str)
            if map_data.shape[1] < 4:
                # Try space delimiter
                map_data = pd.read_csv(map_file_path, delimiter=' ', header=None, dtype=str)
            
            for idx, row in map_data.iterrows():
                snp_info.append({
                    'CHR': row[0],
                    'SNP': row[1],
                    'GEN_DIST': row[2] if len(row) > 2 else '0',
                    'POS': row[3] if len(row) > 3 else '0'
                })
            print(f"Loaded {len(snp_info)} SNPs from MAP file")
        except Exception as e:
            print(f"Warning: Could not read MAP file: {e}")
            snp_info = []
    
    # Generate SNP info if MAP file not available
    if not snp_info:
        for i in range(num_snps):
            snp_info.append({
                'CHR': '0',
                'SNP': f'SNP_{i+1}',
                'GEN_DIST': '0',
                'POS': str(i+1)
            })
    
    # Build CSV data - one row per SNP (matching expected format)
    csv_rows = []
    for i in range(min(num_snps, len(snp_info))):
        allele1_idx = 6 + (i * 2)
        allele2_idx = 6 + (i * 2) + 1
        
        allele1 = ped_data.iloc[0, allele1_idx] if allele1_idx < ped_data.shape[1] else '0'
        allele2 = ped_data.iloc[0, allele2_idx] if allele2_idx < ped_data.shape[1] else '0'
        
        # Handle missing data (0, N, -, .)
        if allele1 in ['0', 'N', '-', '.', 'NA', '']:
            allele1 = '0'
        if allele2 in ['0', 'N', '-', '.', 'NA', '']:
            allele2 = '0'
        
        csv_rows.append({
            'CHR': snp_info[i]['CHR'],
            'SNP': snp_info[i]['SNP'],
            'GEN_DIST': snp_info[i]['GEN_DIST'],
            'POS': snp_info[i]['POS'],
            'Allele1': allele1,
            'Allele2': allele2,
            'Patient_ID': individual_id,
            'Population': family_id,  # Use family ID as population if not available
            'Sex': sex_value,
            'gender': sex_value  # Also include as 'gender' for compatibility
        })
    
    # Create DataFrame and save as CSV
    csv_df = pd.DataFrame(csv_rows)
    csv_file_path = ped_file_path.rsplit('.', 1)[0] + '.csv'
    csv_df.to_csv(csv_file_path, index=False)
    
    print(f"Converted PED to CSV: {csv_file_path}")
    print(f"CSV contains {len(csv_df)} SNPs for patient {individual_id}")
    
    return csv_file_path


def process_uploaded_file(file_path):
    """
    Process an uploaded file - convert PED to CSV if needed.
    
    Args:
        file_path: Path to the uploaded file
        
    Returns:
        Path to the CSV file (either original or converted)
    """
    if file_path.lower().endswith('.ped'):
        try:
            return convert_ped_to_csv(file_path)
        except Exception as e:
            print(f"Error converting PED file: {e}")
            # If conversion fails, try reading as-is (might be a CSV with .ped extension)
            return file_path
    return file_path


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
            
            # Keep original extension for proper processing
            is_ped_file = filename.lower().endswith('.ped')
            
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
            
            # Convert PED file to CSV format if needed
            if is_ped_file:
                try:
                    file_path = convert_ped_to_csv(file_path)
                    # flash("PED file converted to CSV format successfully", "success")
                    pass
                except Exception as e:
                    flash(f"Error converting PED file: {str(e)}. Trying to read as CSV format.", "warning")
            
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
        
        # Keep original extension for proper processing
        is_ped_file = filename.lower().endswith('.ped')
        
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
        
        # Convert PED file to CSV format if needed
        converted_path = file_path
        if is_ped_file:
            try:
                converted_path = convert_ped_to_csv(file_path)
            except Exception as e:
                print(f"Warning: Could not convert PED file: {e}")
                # Keep original path, will try to read as CSV
        
        return jsonify({
            "success": True,
            "filename": os.path.basename(converted_path),
            "file_path": converted_path,
            "original_format": "ped" if is_ped_file else "csv",
            "converted": is_ped_file and converted_path != file_path
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

        # Use model packages from ml_models directory (contains metadata.json and encoding_function.py)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sex_package_dir = os.path.join(project_root, "ml_models", "gender_prediction_package")
        region_package_dir = os.path.join(project_root, "ml_models", "region_prediction_package")

        script_path = os.path.join(project_root, "ml_models", "predict_patient.py")
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
            stderr = process_result.stderr if hasattr(process_result, "stderr") else ""
            
            # Check for critical errors in the output
            if "ERROR: Missing required columns" in stdout or "ERROR: Missing required columns" in stderr:
                error_msg = "Invalid file format. The CSV file must contain columns: SNP, Allele1, Allele2. Optional columns: Patient_ID, Population, gender/Sex"
                if current_user.is_authenticated:
                    notify_user(
                        user_id=current_user.id,
                        title="❌ Invalid File Format",
                        message=error_msg,
                        notification_type="error"
                    )
                return jsonify({"success": False, "error": error_msg})
            
            # Check for non-zero exit code
            if process_result.returncode != 0 and not stdout:
                error_msg = f"Processing failed: {stderr[:500] if stderr else 'Unknown error'}"
                return jsonify({"success": False, "error": error_msg, "stderr": stderr})
                
        except subprocess.TimeoutExpired:
            if current_user.is_authenticated:
                notify_user(
                    user_id=current_user.id,
                    title="⏱️ Analysis Timeout",
                    message="Analysis process timed out after 5 minutes. Please try with a smaller file.",
                    notification_type="error"
                )
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
            
            # Send notification to user if authenticated
            if user_id:
                gender = extracted_results.get("gender_prediction", {}).get("predicted_sex", "Unknown")
                ancestry = extracted_results.get("region_prediction", {}).get("prediction", {}).get("predicted_population", "Unknown")
                notify_user(
                    user_id=user_id,
                    title="🧬 Analysis Complete",
                    message=f"Sample {patient_id}: {gender}, {ancestry} ancestry. Processing took {processing_time:.1f}s",
                    notification_type="success",
                    data={"patient_id": patient_id, "result_file": final_result_file}
                )
            
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

            # Send notification to user if authenticated
            if user_id:
                gender = result_data.get("sex_prediction", result_data.get("gender_prediction", {}))
                if isinstance(gender, dict):
                    gender = gender.get("predicted_sex", "Unknown")
                ancestry = result_data.get("region_prediction", {}).get("prediction", {})
                if isinstance(ancestry, dict):
                    ancestry = ancestry.get("predicted_population", "Unknown")
                notify_user(
                    user_id=user_id,
                    title="🧬 Analysis Complete",
                    message=f"Sample {patient_id}: {gender}, {ancestry} ancestry. Processing took {processing_time:.1f}s",
                    notification_type="success",
                    data={"patient_id": patient_id, "result_file": final_result_file}
                )

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
        # Send error notification if user is authenticated
        if current_user.is_authenticated:
            notify_user(
                user_id=current_user.id,
                title="❌ Analysis Failed",
                message=f"Error processing file: {str(e)[:100]}",
                notification_type="error",
                data={"error": str(e)}
            )
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()})
