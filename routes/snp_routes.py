"""
SNP Routes - API endpoints for SNP queries and dataset building
"""
from flask import jsonify, request, send_file, current_app
import os
import datetime
import pandas as pd
from . import samples_bp
from .samples_routes import POPULATION_INFO


def get_snp_column_name(df):
    """Detect the SNP column name in the dataframe"""
    possible_names = ['SNP', 'snp', 'SNP_ID', 'snp_id', 'rsid', 'RS_ID', 'rs_id', 'RSID', 'ID', 'id']
    for col_name in possible_names:
        if col_name in df.columns:
            return col_name
    return None


def get_allele_columns(df):
    """Detect allele column names in the dataframe"""
    allele1_col = None
    allele2_col = None
    
    # Try different possible column names
    possible_allele1 = ['Allele1', 'allele1', 'ALLELE1', 'A1', 'a1', 'REF', 'ref', 'Reference']
    possible_allele2 = ['Allele2', 'allele2', 'ALLELE2', 'A2', 'a2', 'ALT', 'alt', 'Alternative']
    
    for col in possible_allele1:
        if col in df.columns:
            allele1_col = col
            break
    
    for col in possible_allele2:
        if col in df.columns:
            allele2_col = col
            break
    
    return allele1_col, allele2_col


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
        
        # Detect SNP column name
        snp_col = get_snp_column_name(df)
        if not snp_col:
            return jsonify({
                "success": False,
                "error": "Invalid file format: SNP column not found. Expected columns: SNP, snp, SNP_ID, rsid, RS_ID, etc."
            })
        
        # Find the SNP
        snp_data = df[df[snp_col] == snp_id]
        
        if snp_data.empty:
            return jsonify({
                "success": False,
                "error": f"SNP {snp_id} not found in this sample"
            })
        
        # Get the first match
        row = snp_data.iloc[0]
        
        # Get allele column names
        allele1_col, allele2_col = get_allele_columns(df)
        
        # Get patient info from first row of dataframe (gender/population are usually the same across all rows)
        first_row = df.iloc[0]
        patient_id = str(first_row['Patient_ID']) if 'Patient_ID' in first_row and pd.notna(first_row['Patient_ID']) else None
        population = str(first_row['Population']) if 'Population' in first_row and pd.notna(first_row['Population']) else None
        
        # Get gender from first row (check multiple possible column names and handle different formats)
        gender = None
        sex_code = None
        
        # Try different column names
        if 'gender' in first_row and pd.notna(first_row['gender']):
            sex_code = first_row['gender']
        elif 'Sex' in first_row and pd.notna(first_row['Sex']):
            sex_code = first_row['Sex']
        elif 'sex' in first_row and pd.notna(first_row['sex']):
            sex_code = first_row['sex']
        elif 'SEX' in first_row and pd.notna(first_row['SEX']):
            sex_code = first_row['SEX']
        
        # Convert to gender string (handle both numeric and string values)
        if sex_code is not None:
            try:
                # Try to convert to int if it's a string
                if isinstance(sex_code, str):
                    sex_code = int(sex_code)
                # Check for numeric codes
                if sex_code == 2 or sex_code == '2' or str(sex_code).upper() == 'F' or str(sex_code).upper() == 'FEMALE':
                    gender = "Female"
                elif sex_code == 1 or sex_code == '1' or str(sex_code).upper() == 'M' or str(sex_code).upper() == 'MALE':
                    gender = "Male"
            except (ValueError, TypeError):
                # If conversion fails, check string values directly
                sex_str = str(sex_code).upper()
                if sex_str in ['F', 'FEMALE', '2']:
                    gender = "Female"
                elif sex_str in ['M', 'MALE', '1']:
                    gender = "Male"
        
        # Get chromosome and position (try different column names)
        chr_col = None
        pos_col = None
        for col in ['CHR', 'Chr', 'chr', 'Chromosome', 'chromosome', 'CHROMOSOME']:
            if col in row:
                chr_col = col
                break
        for col in ['POS', 'Pos', 'pos', 'Position', 'position', 'POSITION']:
            if col in row:
                pos_col = col
                break
        
        # Build result
        result = {
            "success": True,
            "snp_id": snp_id,
            "chromosome": int(row[chr_col]) if chr_col and pd.notna(row[chr_col]) else None,
            "position": int(row[pos_col]) if pos_col and pd.notna(row[pos_col]) else None,
            "allele1": str(row[allele1_col]) if allele1_col and pd.notna(row[allele1_col]) else None,
            "allele2": str(row[allele2_col]) if allele2_col and pd.notna(row[allele2_col]) else None,
            "genotype": f"{row[allele1_col]}/{row[allele2_col]}" if allele1_col and allele2_col and pd.notna(row[allele1_col]) and pd.notna(row[allele2_col]) else None,
            "patient_id": patient_id,
            "population": population,
            "gender": gender
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
        
        # Detect SNP column name
        snp_col = get_snp_column_name(df)
        if not snp_col:
            return jsonify({
                "success": False,
                "error": "Invalid file format: SNP column not found. Expected columns: SNP, snp, SNP_ID, rsid, RS_ID, etc."
            })
        
        # Get sample info
        patient_id = df['Patient_ID'].iloc[0] if 'Patient_ID' in df.columns else "Unknown"
        population = df['Population'].iloc[0] if 'Population' in df.columns else "Unknown"
        sex_code = df['gender'].iloc[0] if 'gender' in df.columns else None
        gender = "Female" if sex_code == 2 else "Male" if sex_code == 1 else "Unknown"
        
        # Get SNP list
        snps = df[snp_col].tolist()
        
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
        
        # Detect SNP column name
        snp_col = get_snp_column_name(df)
        if not snp_col:
            return jsonify({
                "success": False,
                "error": "Invalid file format: SNP column not found. Expected columns: SNP, snp, SNP_ID, rsid, RS_ID, etc."
            })
        
        # Get allele column names
        allele1_col, allele2_col = get_allele_columns(df)
        
        # Get chromosome and position column names
        chr_col = None
        pos_col = None
        for col in ['CHR', 'Chr', 'chr', 'Chromosome', 'chromosome', 'CHROMOSOME']:
            if col in df.columns:
                chr_col = col
                break
        for col in ['POS', 'Pos', 'pos', 'Position', 'position', 'POSITION']:
            if col in df.columns:
                pos_col = col
                break
        
        # Query all SNPs
        results = []
        not_found = []
        
        for snp_id in snp_ids:
            snp_data = df[df[snp_col] == snp_id]
            
            if snp_data.empty:
                not_found.append(snp_id)
            else:
                row = snp_data.iloc[0]
                allele1 = str(row[allele1_col]) if allele1_col and allele1_col in row and pd.notna(row[allele1_col]) else None
                allele2 = str(row[allele2_col]) if allele2_col and allele2_col in row and pd.notna(row[allele2_col]) else None
                results.append({
                    "snp_id": snp_id,
                    "chromosome": int(row[chr_col]) if chr_col and chr_col in row and pd.notna(row[chr_col]) else None,
                    "position": int(row[pos_col]) if pos_col and pos_col in row and pd.notna(row[pos_col]) else None,
                    "allele1": allele1,
                    "allele2": allele2,
                    "genotype": f"{allele1}/{allele2}" if allele1 and allele2 else None
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
        first_snp_col = get_snp_column_name(first_df)
        if not first_snp_col:
            return jsonify({
                "success": False,
                "error": "Invalid file format: SNP column not found in first file"
            })
        common_snps = set(first_df[first_snp_col].tolist())
        
        # Find intersection with other files
        for file_path in sample_files[1:]:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                snp_col = get_snp_column_name(df)
                if snp_col:
                    file_snps = set(df[snp_col].tolist())
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
            
            # Detect column names
            snp_col = get_snp_column_name(df)
            if not snp_col:
                continue  # Skip files without SNP column
            
            allele1_col, allele2_col = get_allele_columns(df)
            
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
                snp_data = df[df[snp_col] == snp_id]
                
                if snp_data.empty:
                    if encoding == 'numeric':
                        row[snp_id] = -1  # Missing value
                    else:
                        row[snp_id] = "NA"
                else:
                    snp_row = snp_data.iloc[0]
                    allele1 = str(snp_row[allele1_col]) if allele1_col and allele1_col in snp_row and pd.notna(snp_row[allele1_col]) else '?'
                    allele2 = str(snp_row[allele2_col]) if allele2_col and allele2_col in snp_row and pd.notna(snp_row[allele2_col]) else '?'
                    
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
