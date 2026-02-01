"""
Samples Routes - API endpoints for sample management
"""
from flask import jsonify, request
import pandas as pd
import os
from . import samples_bp

# Population information
POPULATION_INFO = {
    "ASW": {"code": "A", "description": "African ancestry in Southwest USA"},
    "CEU": {"code": "C", "description": "Utah residents with Northern and Western European ancestry from the CEPH collection"},
    "CHB": {"code": "H", "description": "Han Chinese in Beijing, China"},
    "CHD": {"code": "D", "description": "Chinese in Metropolitan Denver, Colorado"},
    "GIH": {"code": "G", "description": "Gujarati Indians in Houston, Texas"},
    "JPT": {"code": "J", "description": "Japanese in Tokyo, Japan"},
    "LWK": {"code": "L", "description": "Luhya in Webuye, Kenya"},
    "MEX": {"code": "M", "description": "Mexican ancestry in Los Angeles, California"},
    "MKK": {"code": "K", "description": "Maasai in Kinyawa, Kenya"},
    "TSI": {"code": "T", "description": "Tuscan in Italy"},
    "YRI": {"code": "Y", "description": "Yoruban in Ibadan, Nigeria (West Africa)"},
}

# Build reverse lookup: short code -> full population code
SHORT_CODE_TO_POPULATION = {info["code"]: pop_code for pop_code, info in POPULATION_INFO.items()}


def resolve_population_code(population):
    """
    Resolve a population code to its full form.
    Handles both full codes (CEU, YRI) and short codes (C, Y, H).
    
    Args:
        population: Population code (can be full like 'CEU' or short like 'C')
    
    Returns:
        tuple: (full_code, description)
    """
    if not population:
        return "Unknown", "Unknown Population"
    
    pop_upper = str(population).upper().strip()
    
    # First check if it's already a full code
    if pop_upper in POPULATION_INFO:
        return pop_upper, POPULATION_INFO[pop_upper]["description"]
    
    # Check if it's a short code
    if pop_upper in SHORT_CODE_TO_POPULATION:
        full_code = SHORT_CODE_TO_POPULATION[pop_upper]
        return full_code, POPULATION_INFO[full_code]["description"]
    
    # Unknown population - return as is
    return pop_upper, f"Population: {pop_upper}"


@samples_bp.route('/list', methods=['GET'])
def list_samples():
    """
    List all available genetic sample files
    ---
    tags:
      - Samples
    responses:
      200:
        description: List of samples
    """
    sample_files = []
    
    # Check patient_snp_data directory
    patient_data_dir = "patient_snp_data"
    if os.path.exists(patient_data_dir):
        for root, dirs, files in os.walk(patient_data_dir):
            for file in files:
                if file.endswith('.csv') and not file.startswith('all_patients'):
                    file_path = os.path.join(root, file)
                    try:
                        df = pd.read_csv(file_path, nrows=1)
                        patient_id = df['Patient_ID'].iloc[0] if 'Patient_ID' in df.columns else file.replace('.csv', '')
                        population = df['Population'].iloc[0] if 'Population' in df.columns else "Unknown"
                        sex_code = df['gender'].iloc[0] if 'gender' in df.columns else None
                        gender = "Female" if sex_code == 2 else "Male" if sex_code == 1 else "Unknown"
                    except:
                        patient_id = file.replace('.csv', '')
                        population = "Unknown"
                        gender = "Unknown"
                    
                    sample_files.append({
                        'filename': file,
                        'path': file_path,
                        'patient_id': str(patient_id),
                        'population': str(population),
                        'gender': gender
                    })
    
    # Check uploads folder
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            if file.endswith('.csv'):
                file_path = os.path.join(uploads_dir, file)
                try:
                    df = pd.read_csv(file_path, nrows=1)
                    patient_id = df['Patient_ID'].iloc[0] if 'Patient_ID' in df.columns else file.replace('.csv', '')
                    population = df['Population'].iloc[0] if 'Population' in df.columns else "Unknown"
                    sex_code = df['gender'].iloc[0] if 'gender' in df.columns else None
                    gender = "Female" if sex_code == 2 else "Male" if sex_code == 1 else "Unknown"
                except:
                    patient_id = file.replace('.csv', '')
                    population = "Unknown"
                    gender = "Unknown"
                
                sample_files.append({
                    'filename': file,
                    'path': file_path,
                    'patient_id': str(patient_id),
                    'population': str(population),
                    'gender': gender
                })
    
    return jsonify({
        "success": True,
        "samples": sample_files,
        "total": len(sample_files)
    })


@samples_bp.route('/info', methods=['POST'])
def get_sample_info():
    """
    Get detailed information about a sample file
    ---
    tags:
      - Samples
    """
    data = request.json
    sample_file = data.get("sample_file")
    
    if not sample_file or not os.path.exists(sample_file):
        return jsonify({"success": False, "error": f"Sample file not found: {sample_file}"})
    
    try:
        df = pd.read_csv(sample_file)
        
        if 'SNP' not in df.columns:
            return jsonify({"success": False, "error": "Invalid file format: SNP column not found"})
        
        patient_id = df['Patient_ID'].iloc[0] if 'Patient_ID' in df.columns else "Unknown"
        population = df['Population'].iloc[0] if 'Population' in df.columns else "Unknown"
        sex_code = df['gender'].iloc[0] if 'gender' in df.columns else None
        gender = "Female" if sex_code == 2 else "Male" if sex_code == 1 else "Unknown"
        
        total_snps = len(df)
        chromosomes = df['CHR'].unique().tolist() if 'CHR' in df.columns else []
        
        result = {
            "success": True,
            "patient_id": str(patient_id),
            "population": str(population),
            "gender": gender,
            "total_snps": total_snps,
            "chromosomes_covered": sorted([int(c) for c in chromosomes if pd.notna(c)]),
            "file_path": sample_file
        }
        
        if population in POPULATION_INFO:
            result["population_description"] = POPULATION_INFO[population]["description"]
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@samples_bp.route('/populations', methods=['GET'])
def list_populations():
    """
    List all known populations
    ---
    tags:
      - Samples
    """
    populations = []
    for code, info in POPULATION_INFO.items():
        populations.append({
            "code": code,
            "short_code": info["code"],
            "description": info["description"]
        })
    
    return jsonify({
        "success": True,
        "populations": populations,
        "total": len(populations)
    })


@samples_bp.route('/population/<population_code>', methods=['GET'])
def get_population_info(population_code):
    """
    Get info about a specific population
    ---
    tags:
      - Samples
    """
    population_code = population_code.upper()
    
    if population_code in POPULATION_INFO:
        info = POPULATION_INFO[population_code]
        return jsonify({
            "success": True,
            "code": population_code,
            "short_code": info["code"],
            "description": info["description"]
        })
    else:
        return jsonify({
            "success": False,
            "error": f"Unknown population code: {population_code}",
            "available_populations": list(POPULATION_INFO.keys())
        })


@samples_bp.route('/compare', methods=['POST'])
def compare_samples():
    """
    Compare two sample files
    ---
    tags:
      - Samples
    """
    data = request.json
    sample_file_1 = data.get("sample_file_1")
    sample_file_2 = data.get("sample_file_2")
    
    if not os.path.exists(sample_file_1):
        return jsonify({"success": False, "error": f"First sample file not found: {sample_file_1}"})
    if not os.path.exists(sample_file_2):
        return jsonify({"success": False, "error": f"Second sample file not found: {sample_file_2}"})
    
    try:
        df1 = pd.read_csv(sample_file_1)
        df2 = pd.read_csv(sample_file_2)
        
        info1 = {
            "patient_id": str(df1['Patient_ID'].iloc[0]) if 'Patient_ID' in df1.columns else "Unknown",
            "population": str(df1['Population'].iloc[0]) if 'Population' in df1.columns else "Unknown",
            "total_snps": len(df1)
        }
        info2 = {
            "patient_id": str(df2['Patient_ID'].iloc[0]) if 'Patient_ID' in df2.columns else "Unknown",
            "population": str(df2['Population'].iloc[0]) if 'Population' in df2.columns else "Unknown",
            "total_snps": len(df2)
        }
        
        snps1 = set(df1['SNP'].tolist())
        snps2 = set(df2['SNP'].tolist())
        common_snps = snps1.intersection(snps2)
        
        matching_genotypes = 0
        different_genotypes = 0
        
        df1_indexed = df1.set_index('SNP')
        df2_indexed = df2.set_index('SNP')
        
        for snp in list(common_snps)[:1000]:
            if 'Allele1' in df1.columns and 'Allele2' in df1.columns:
                geno1 = f"{df1_indexed.loc[snp, 'Allele1']}/{df1_indexed.loc[snp, 'Allele2']}"
                geno2 = f"{df2_indexed.loc[snp, 'Allele1']}/{df2_indexed.loc[snp, 'Allele2']}"
                
                if geno1 == geno2:
                    matching_genotypes += 1
                else:
                    different_genotypes += 1
        
        similarity_rate = matching_genotypes / (matching_genotypes + different_genotypes) if (matching_genotypes + different_genotypes) > 0 else 0
        
        return jsonify({
            "success": True,
            "sample1": info1,
            "sample2": info2,
            "common_snps_count": len(common_snps),
            "unique_to_sample1": len(snps1 - snps2),
            "unique_to_sample2": len(snps2 - snps1),
            "matching_genotypes": matching_genotypes,
            "different_genotypes": different_genotypes,
            "similarity_rate": round(similarity_rate * 100, 2)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

