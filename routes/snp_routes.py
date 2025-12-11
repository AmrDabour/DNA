"""
SNP Routes - API endpoints for SNP queries and dataset building
"""
from flask import jsonify, request, send_file, current_app
import os
import datetime
import pandas as pd
from . import samples_bp
from .samples_routes import POPULATION_INFO


# ============================================================
# SNP Query Feature - Query specific SNP values from sample files
# ============================================================

@samples_bp.route('/snps/query', methods=['POST'])
def query_snp():
    """
    Query a specific SNP value from a sample file
    ---
    tags:
      - SNP Query
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - sample_file
            - snp_id
          properties:
            sample_file:
              type: string
              description: Path to the sample CSV file
              example: "patient_snp_data/NA12753_CEU_Female.csv"
            snp_id:
              type: string
              description: The SNP identifier to query
              example: "rs123456"
    responses:
      200:
        description: SNP query result
        schema:
          type: object
          properties:
            success:
              type: boolean
            snp_id:
              type: string
            chromosome:
              type: integer
            position:
              type: integer
            allele1:
              type: string
            allele2:
              type: string
            genotype:
              type: string
      400:
        description: SNP not found or invalid file
    """
    try:
        data = request.json
        sample_file = data.get("sample_file")
        snp_id = data.get("snp_id")
        
        if not sample_file or not snp_id:
            return jsonify({
                "success": False,
                "error": "Missing sample file or SNP ID"
            })
        
        # Check if file exists
        if not os.path.exists(sample_file):
            return jsonify({
                "success": False,
                "error": f"Sample file not found: {sample_file}"
            })
        
        # Load the sample data
        df = pd.read_csv(sample_file)
        
        # Check if SNP column exists
        if 'SNP' not in df.columns:
            return jsonify({
                "success": False,
                "error": "Invalid file format: SNP column not found"
            })
        
        # Find the SNP
        snp_data = df[df['SNP'] == snp_id]
        
        if snp_data.empty:
            return jsonify({
                "success": False,
                "error": f"SNP {snp_id} not found in this sample"
            })
        
        # Get the first match
        row = snp_data.iloc[0]
        
        # Build result
        result = {
            "success": True,
            "snp_id": snp_id,
            "chromosome": int(row['CHR']) if 'CHR' in row else None,
            "position": int(row['POS']) if 'POS' in row else None,
            "allele1": str(row['Allele1']) if 'Allele1' in row else None,
            "allele2": str(row['Allele2']) if 'Allele2' in row else None,
            "genotype": f"{row['Allele1']}/{row['Allele2']}" if 'Allele1' in row and 'Allele2' in row else None,
            "patient_id": str(row['Patient_ID']) if 'Patient_ID' in row else None,
            "population": str(row['Population']) if 'Population' in row else None,
            "gender": "Female" if row.get('gender') == 2 else "Male" if row.get('gender') == 1 else None
        }
        
        # Add population description if available
        if result["population"] and result["population"] in POPULATION_INFO:
            result["population_description"] = POPULATION_INFO[result["population"]]["description"]
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        })


@samples_bp.route('/snps/list', methods=['POST'])
def get_sample_snps():
    """
    Get list of available SNPs in a sample file
    ---
    tags:
      - SNP Query
    """
    try:
        data = request.json
        sample_file = data.get("sample_file")
        
        if not sample_file:
            return jsonify({
                "success": False,
                "error": "Missing sample file"
            })
        
        if not os.path.exists(sample_file):
            return jsonify({
                "success": False,
                "error": f"Sample file not found: {sample_file}"
            })
        
        # Load the sample data
        df = pd.read_csv(sample_file)
        
        if 'SNP' not in df.columns:
            return jsonify({
                "success": False,
                "error": "Invalid file format: SNP column not found"
            })
        
        # Get sample info
        patient_id = df['Patient_ID'].iloc[0] if 'Patient_ID' in df.columns else "Unknown"
        population = df['Population'].iloc[0] if 'Population' in df.columns else "Unknown"
        sex_code = df['gender'].iloc[0] if 'gender' in df.columns else None
        gender = "Female" if sex_code == 2 else "Male" if sex_code == 1 else "Unknown"
        
        # Get SNP list
        snps = df['SNP'].tolist()
        
        return jsonify({
            "success": True,
            "patient_id": patient_id,
            "population": population,
            "gender": gender,
            "total_snps": len(snps),
            "snps": snps[:500]  # Return first 500 SNPs for autocomplete
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@samples_bp.route('/snps/query-multiple', methods=['POST'])
def query_multiple_snps():
    """
    Query multiple SNP values from a sample file
    ---
    tags:
      - SNP Query
    """
    try:
        data = request.json
        sample_file = data.get("sample_file")
        snp_ids = data.get("snp_ids", [])
        
        if not sample_file or not snp_ids:
            return jsonify({
                "success": False,
                "error": "Missing sample file or SNP IDs"
            })
        
        if not os.path.exists(sample_file):
            return jsonify({
                "success": False,
                "error": f"Sample file not found: {sample_file}"
            })
        
        # Load the sample data
        df = pd.read_csv(sample_file)
        
        if 'SNP' not in df.columns:
            return jsonify({
                "success": False,
                "error": "Invalid file format: SNP column not found"
            })
        
        # Query all SNPs
        results = []
        not_found = []
        
        for snp_id in snp_ids:
            snp_data = df[df['SNP'] == snp_id]
            
            if snp_data.empty:
                not_found.append(snp_id)
            else:
                row = snp_data.iloc[0]
                results.append({
                    "snp_id": snp_id,
                    "chromosome": int(row['CHR']) if 'CHR' in row else None,
                    "position": int(row['POS']) if 'POS' in row else None,
                    "allele1": str(row['Allele1']) if 'Allele1' in row else None,
                    "allele2": str(row['Allele2']) if 'Allele2' in row else None,
                    "genotype": f"{row['Allele1']}/{row['Allele2']}" if 'Allele1' in row and 'Allele2' in row else None
                })
        
        return jsonify({
            "success": True,
            "results": results,
            "not_found": not_found,
            "found_count": len(results),
            "not_found_count": len(not_found)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


# ============================================================
# Dataset Builder - Create CSV with SNPs from multiple samples
# ============================================================

@samples_bp.route('/common-snps', methods=['POST'])
def get_common_snps():
    """
    Get common SNPs across multiple sample files
    ---
    tags:
      - Dataset
    """
    try:
        data = request.json
        sample_files = data.get("sample_files", [])
        
        if not sample_files:
            return jsonify({
                "success": False,
                "error": "No sample files provided"
            })
        
        # Get SNPs from first file
        first_df = pd.read_csv(sample_files[0])
        common_snps = set(first_df['SNP'].tolist())
        
        # Find intersection with other files
        for file_path in sample_files[1:]:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                file_snps = set(df['SNP'].tolist())
                common_snps = common_snps.intersection(file_snps)
        
        common_snps_list = sorted(list(common_snps))
        
        return jsonify({
            "success": True,
            "common_snps": common_snps_list[:1000],  # Limit to 1000 for performance
            "total_common": len(common_snps_list)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@samples_bp.route('/build-dataset', methods=['POST'])
def build_dataset():
    """
    Build a CSV dataset from multiple samples with selected SNPs
    ---
    tags:
      - Dataset
    """
    try:
        data = request.json
        sample_files = data.get("sample_files", [])
        snp_ids = data.get("snp_ids", [])
        target_column = data.get("target_column", "population")  # population, gender, or both
        encoding = data.get("encoding", "genotype")  # genotype (A/T), numeric (0,1,2), or alleles
        
        if not sample_files or not snp_ids:
            return jsonify({
                "success": False,
                "error": "Missing sample files or SNP IDs"
            })
        
        # Build dataset
        dataset_rows = []
        
        for file_path in sample_files:
            if not os.path.exists(file_path):
                continue
            
            df = pd.read_csv(file_path)
            
            # Get sample info
            patient_id = df['Patient_ID'].iloc[0] if 'Patient_ID' in df.columns else os.path.basename(file_path).replace('.csv', '')
            population = df['Population'].iloc[0] if 'Population' in df.columns else "Unknown"
            sex_code = df['gender'].iloc[0] if 'gender' in df.columns else None
            gender = "Female" if sex_code == 2 else "Male" if sex_code == 1 else "Unknown"
            
            # Create row
            row = {
                'Sample_ID': patient_id,
            }
            
            # Add target columns based on selection
            if target_column in ['population', 'both']:
                row['Population'] = population
            if target_column in ['gender', 'both']:
                row['gender'] = gender
            
            # Get SNP values
            for snp_id in snp_ids:
                snp_data = df[df['SNP'] == snp_id]
                
                if snp_data.empty:
                    if encoding == 'numeric':
                        row[snp_id] = -1  # Missing value
                    else:
                        row[snp_id] = "NA"
                else:
                    snp_row = snp_data.iloc[0]
                    allele1 = str(snp_row['Allele1']) if 'Allele1' in snp_row else '?'
                    allele2 = str(snp_row['Allele2']) if 'Allele2' in snp_row else '?'
                    
                    if encoding == 'genotype':
                        row[snp_id] = f"{allele1}/{allele2}"
                    elif encoding == 'alleles':
                        row[f"{snp_id}_A1"] = allele1
                        row[f"{snp_id}_A2"] = allele2
                    elif encoding == 'numeric':
                        # Encode as count of minor allele (simplified - using A as reference)
                        ref_allele = 'A'  # Simplified
                        alt_count = sum([1 for a in [allele1, allele2] if a != ref_allele and a != '0'])
                        row[snp_id] = alt_count
            
            dataset_rows.append(row)
        
        # Create DataFrame
        result_df = pd.DataFrame(dataset_rows)
        
        # Generate filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snp_dataset_{len(sample_files)}samples_{len(snp_ids)}snps_{timestamp}.csv"
        
        # Get upload folder from app config
        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
        filepath = os.path.join(upload_folder, filename)
        
        # Save CSV
        result_df.to_csv(filepath, index=False)
        
        return jsonify({
            "success": True,
            "filename": filename,
            "filepath": filepath,
            "samples_count": len(dataset_rows),
            "snps_count": len(snp_ids),
            "columns": list(result_df.columns),
            "preview": result_df.head(5).to_dict(orient='records')
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        })


@samples_bp.route('/download/<filename>')
def download_dataset(filename):
    """
    Download a generated dataset
    ---
    tags:
      - Dataset
    parameters:
      - in: path
        name: filename
        type: string
        required: true
        description: Name of the dataset file to download
    responses:
      200:
        description: CSV file download
        content:
          text/csv:
            schema:
              type: string
              format: binary
      404:
        description: File not found
    """
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
    filepath = os.path.join(upload_folder, filename)
    
    if not os.path.exists(filepath):
        return jsonify({"success": False, "error": "File not found"}), 404
    
    return send_file(
        filepath,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )
