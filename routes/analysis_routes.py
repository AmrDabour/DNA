"""
Analysis Routes - API endpoints for SNP analysis and visualization pages
"""
from flask import Blueprint, jsonify, request, render_template, redirect, url_for
import os
import pandas as pd
import numpy as np
from . import analysis_bp
from .samples_routes import POPULATION_INFO

# Create page blueprint (no prefix for page routes)
analysis_page_bp = Blueprint('analysis_pages', __name__)


@analysis_bp.route('/snp', methods=['POST'])
def query_snp():
    """
    Query a specific SNP from a sample file
    ---
    tags:
      - Analysis
    """
    data = request.json
    sample_file = data.get("sample_file")
    snp_id = data.get("snp_id")
    
    if not sample_file or not snp_id:
        return jsonify({"success": False, "error": "Missing sample_file or snp_id"})
    
    if not os.path.exists(sample_file):
        return jsonify({"success": False, "error": f"Sample file not found: {sample_file}"})
    
    try:
        df = pd.read_csv(sample_file)
        
        if 'SNP' not in df.columns:
            return jsonify({"success": False, "error": "Invalid file format: SNP column not found"})
        
        snp_data = df[df['SNP'] == snp_id]
        
        if snp_data.empty:
            return jsonify({"success": False, "error": f"SNP {snp_id} not found"})
        
        row = snp_data.iloc[0]
        
        result = {
            "success": True,
            "snp_id": snp_id,
            "chromosome": int(row['CHR']) if 'CHR' in row and row['CHR'] is not None and str(row['CHR']) != 'nan' else None,
            "position": int(row['POS']) if 'POS' in row and row['POS'] is not None and str(row['POS']) != 'nan' else None,
            "allele1": str(row['Allele1']) if 'Allele1' in row else None,
            "allele2": str(row['Allele2']) if 'Allele2' in row else None,
            "genotype": f"{row['Allele1']}/{row['Allele2']}" if 'Allele1' in row and 'Allele2' in row else None,
            "patient_id": str(row['Patient_ID']) if 'Patient_ID' in row else None,
            "population": str(row['Population']) if 'Population' in row else None
        }
        
        if result["population"] and result["population"] in POPULATION_INFO:
            result["population_description"] = POPULATION_INFO[result["population"]]["description"]
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@analysis_bp.route('/snp/multiple', methods=['POST'])
def query_multiple_snps():
    """
    Query multiple SNPs from a sample file
    ---
    tags:
      - Analysis
    """
    data = request.json
    sample_file = data.get("sample_file")
    snp_ids = data.get("snp_ids", [])
    
    if not sample_file or not snp_ids:
        return jsonify({"success": False, "error": "Missing sample_file or snp_ids"})
    
    if not os.path.exists(sample_file):
        return jsonify({"success": False, "error": f"Sample file not found: {sample_file}"})
    
    try:
        df = pd.read_csv(sample_file)
        
        if 'SNP' not in df.columns:
            return jsonify({"success": False, "error": "Invalid file format"})
        
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
                    "chromosome": int(row['CHR']) if 'CHR' in row and row['CHR'] is not None and str(row['CHR']) != 'nan' else None,
                    "position": int(row['POS']) if 'POS' in row and row['POS'] is not None and str(row['POS']) != 'nan' else None,
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
        return jsonify({"success": False, "error": str(e)})


@analysis_bp.route('/analyze', methods=['POST'])
def analyze_snp_file():
    """
    Perform complete genetic analysis on a sample file
    ---
    tags:
      - Analysis
    """
    data = request.json
    sample_file = data.get("sample_file")
    
    if not sample_file or not os.path.exists(sample_file):
        return jsonify({"success": False, "error": f"Sample file not found: {sample_file}"})
    
    try:
        df = pd.read_csv(sample_file)
        
        patient_id = df['Patient_ID'].iloc[0] if 'Patient_ID' in df.columns else os.path.basename(sample_file).split('_')[0]
        total_snps = len(df)
        
        result = {
            "success": True,
            "patient_id": str(patient_id),
            "file_analyzed": sample_file,
            "total_snps": total_snps,
            "analysis": {}
        }
        
        # Chromosomes
        if 'CHR' in df.columns:
            chromosomes = sorted([int(c) for c in df['CHR'].unique() if c is not None and str(c) != 'nan'])
            result["chromosomes_covered"] = chromosomes
        
        # Genotype analysis
        if 'Allele1' in df.columns and 'Allele2' in df.columns:
            df['is_hetero'] = df['Allele1'] != df['Allele2']
            heterozygosity = df['is_hetero'].mean()
            
            result["analysis"]["heterozygosity_rate"] = round(heterozygosity * 100, 2)
            result["analysis"]["homozygous_count"] = int((~df['is_hetero']).sum())
            result["analysis"]["heterozygous_count"] = int(df['is_hetero'].sum())
        
        # Gender
        if 'gender' in df.columns:
            sex_code = df['gender'].iloc[0]
            result["analysis"]["gender"] = {
                "predicted_sex": "Male" if sex_code == 1 else "Female" if sex_code == 2 else "Unknown",
                "confidence": "High (from original data)"
            }
        
        # Population
        if 'Population' in df.columns:
            population = df['Population'].iloc[0]
            result["analysis"]["ancestry"] = {
                "predicted_population": str(population),
                "confidence": "High (from original data)"
            }
            if population in POPULATION_INFO:
                result["analysis"]["ancestry"]["description"] = POPULATION_INFO[population]["description"]
        
        # Allele frequencies
        if 'Allele1' in df.columns:
            allele_counts = df['Allele1'].value_counts().to_dict()
            if 'Allele2' in df.columns:
                for allele, count in df['Allele2'].value_counts().items():
                    allele_counts[allele] = allele_counts.get(allele, 0) + count
            
            allele_counts = {k: v for k, v in allele_counts.items() if k != '0' and k != 0}
            total_alleles = sum(allele_counts.values())
            
            if total_alleles > 0:
                result["analysis"]["allele_frequencies"] = {
                    allele: round(count / total_alleles * 100, 2) 
                    for allele, count in sorted(allele_counts.items(), key=lambda x: -x[1])
                }
        
        # Summary
        sex_info = result["analysis"].get("gender", {})
        ancestry_info = result["analysis"].get("ancestry", {})
        
        result["summary"] = f"Sample {patient_id}: "
        if sex_info.get("predicted_sex"):
            result["summary"] += f"{sex_info['predicted_sex']}"
        if ancestry_info.get("predicted_population"):
            result["summary"] += f" from {ancestry_info['predicted_population']} population"
        result["summary"] += f". Analyzed {total_snps} SNPs."
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()})


@analysis_bp.route('/statistics', methods=['POST'])
def get_snp_statistics():
    """
    Get detailed SNP statistics for a sample file
    ---
    tags:
      - Analysis
    """
    data = request.json
    sample_file = data.get("sample_file")
    
    if not sample_file or not os.path.exists(sample_file):
        return jsonify({"success": False, "error": f"Sample file not found: {sample_file}"})
    
    try:
        df = pd.read_csv(sample_file)
        
        result = {
            "success": True,
            "total_snps": len(df),
            "statistics": {}
        }
        
        # Chromosome distribution
        if 'CHR' in df.columns:
            chr_counts = df['CHR'].value_counts().sort_index().to_dict()
            result["statistics"]["snps_per_chromosome"] = {
                f"chr{int(k)}": int(v) for k, v in chr_counts.items() if k is not None and str(k) != 'nan'
            }
        
        # Missing data
        if 'Allele1' in df.columns and 'Allele2' in df.columns:
            missing_allele1 = ((df['Allele1'] == '0') | (df['Allele1'] == 0) | df['Allele1'].isna()).sum()
            missing_allele2 = ((df['Allele2'] == '0') | (df['Allele2'] == 0) | df['Allele2'].isna()).sum()
            
            result["statistics"]["missing_data"] = {
                "missing_allele1": int(missing_allele1),
                "missing_allele2": int(missing_allele2),
                "complete_genotypes": int(len(df) - max(missing_allele1, missing_allele2)),
                "completeness_rate": round((1 - max(missing_allele1, missing_allele2) / len(df)) * 100, 2)
            }
            
            # Top genotypes
            df['genotype'] = df['Allele1'].astype(str) + '/' + df['Allele2'].astype(str)
            genotype_counts = df['genotype'].value_counts().head(10).to_dict()
            result["statistics"]["top_genotypes"] = genotype_counts
            
            # Heterozygosity
            valid_mask = (df['Allele1'] != '0') & (df['Allele2'] != '0')
            if valid_mask.sum() > 0:
                hetero_rate = (df.loc[valid_mask, 'Allele1'] != df.loc[valid_mask, 'Allele2']).mean()
                result["statistics"]["heterozygosity_rate"] = round(hetero_rate * 100, 2)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ============================================================
# Page Routes (no URL prefix)
# ============================================================

@analysis_page_bp.route("/visualizations")
def visualizations():
    """Enhanced visualization page"""
    try:
        from models import GeneticPredictor, find_model_directories
        
        predictor = GeneticPredictor()
        gender_model_dir, ancestry_model_dir = find_model_directories()
        
        gender_loaded = False
        ancestry_loaded = False
        
        if gender_model_dir:
            gender_loaded = predictor.load_sex_predictor(gender_model_dir)
        if ancestry_model_dir:
            ancestry_loaded = predictor.load_ancestry_predictor(ancestry_model_dir)
        
        gender_accuracy = None
        if gender_loaded:
            gender_accuracy = predictor.sex_predictor.analyze_prediction_accuracy()

        # Removed visualization generation - no longer needed without Model Performance tab
        gender_viz_data = None
        ancestry_viz_data = None
        ancestry_accuracy = None
        if ancestry_loaded:
            # Calculate ancestry accuracy if possible
            try:
                if predictor.ancestry_predictor.features_df is not None and 'Population' in predictor.ancestry_predictor.features_df.columns:
                    feature_cols = [col for col in predictor.ancestry_predictor.features_df.columns if col.startswith('PC_')]
                    if 'gender' in predictor.ancestry_predictor.features_df.columns:
                        predictor.ancestry_predictor.features_df['SEX_numeric'] = predictor.ancestry_predictor.features_df['gender'].fillna(0).astype(int)
                        feature_cols.append('SEX_numeric')
                    
                    X = predictor.ancestry_predictor.features_df[feature_cols].values
                    predictions = predictor.ancestry_predictor.model.predict(X)
                    predicted_pops = predictor.ancestry_predictor.encoder.inverse_transform(predictions)
                    true_pops = predictor.ancestry_predictor.features_df['Population'].values
                    ancestry_accuracy = float(np.mean(predicted_pops == true_pops))
            except Exception:
                ancestry_accuracy = None

        # Organize plot files by category
        plot_files = []
        plots_dir = os.path.join(os.getcwd(), "plots")
        if os.path.exists(plots_dir):
            plot_files = sorted([f for f in os.listdir(plots_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.svg'))])

        viz_files = []
        viz_dir = os.path.join(os.getcwd(), "visualizations")
        if os.path.exists(viz_dir):
            viz_files = sorted([f for f in os.listdir(viz_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.svg'))])

        # Categorize plots
        def categorize_plot(filename):
            filename_lower = filename.lower()
            if 'pca' in filename_lower or 'tsne' in filename_lower or 'mds' in filename_lower:
                return 'dimensionality'
            elif 'confusion' in filename_lower or 'roc' in filename_lower or 'accuracy' in filename_lower or 'error' in filename_lower:
                return 'performance'
            elif 'population' in filename_lower or 'fst' in filename_lower or 'distance' in filename_lower or 'admixture' in filename_lower:
                return 'population'
            elif 'manhattan' in filename_lower or 'qq' in filename_lower or 'snp' in filename_lower or 'allele' in filename_lower or 'chromosome' in filename_lower:
                return 'genetic_markers'
            elif 'haplotype' in filename_lower or 'ld' in filename_lower or 'heterozygosity' in filename_lower or 'genotype' in filename_lower:
                return 'genetic_structure'
            elif 'learning' in filename_lower or 'effect' in filename_lower or 'feature' in filename_lower:
                return 'model_analysis'
            elif 'clustering' in filename_lower or 'kmeans' in filename_lower:
                return 'clustering'
            elif 'distribution' in filename_lower or 'sex' in filename_lower or 'gender' in filename_lower:
                return 'distribution'
            elif 'dashboard' in filename_lower or 'coverage' in filename_lower:
                return 'overview'
            else:
                return 'other'

        # Organize visualization files
        viz_categories = {
            'performance': [],
            'distribution': [],
            'clustering': [],
            'dimensionality': [],
            'other': []
        }
        
        for viz_file in viz_files:
            category = categorize_plot(viz_file)
            if category in viz_categories:
                viz_categories[category].append(viz_file)
            else:
                viz_categories['other'].append(viz_file)

        # Organize plot files
        plot_categories = {
            'dimensionality': [],
            'population': [],
            'genetic_markers': [],
            'genetic_structure': [],
            'model_analysis': [],
            'overview': [],
            'other': []
        }
        
        for plot_file in plot_files:
            category = categorize_plot(plot_file)
            if category in plot_categories:
                plot_categories[category].append(plot_file)
            else:
                plot_categories['other'].append(plot_file)

        return render_template(
            "visualizations.html",
            gender_accuracy=gender_accuracy,
            gender_viz_data=gender_viz_data,
            ancestry_viz_data=ancestry_viz_data,
            ancestry_accuracy=ancestry_accuracy,
            gender_loaded=gender_loaded,
            ancestry_loaded=ancestry_loaded,
            plot_files=plot_files,
            viz_files=viz_files,
            plot_categories=plot_categories,
            viz_categories=viz_categories,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Initialize empty categories for error case
        viz_categories = {
            'performance': [],
            'distribution': [],
            'clustering': [],
            'dimensionality': [],
            'other': []
        }
        plot_categories = {
            'dimensionality': [],
            'population': [],
            'genetic_markers': [],
            'genetic_structure': [],
            'model_analysis': [],
            'overview': [],
            'other': []
        }
        
        return render_template(
            "visualizations.html",
            gender_accuracy=None,
            gender_viz_data=None,
            ancestry_viz_data=None,
            ancestry_accuracy=None,
            gender_loaded=False,
            ancestry_loaded=False,
            plot_files=[],
            viz_files=[],
            plot_categories=plot_categories,
            viz_categories=viz_categories,
            error=str(e)
        )


@analysis_page_bp.route("/analyze_accuracy")
def analyze_accuracy():
    """Redirect old route to new visualizations page"""
    return redirect(url_for("analysis_pages.visualizations"))


# @analysis_page_bp.route("/populations")
# def populations():
#     """Show known populations page"""
#     try:
#         from models import GeneticPredictor, POPULATION_INFO as POP_INFO, find_model_directories
#         
#         predictor = GeneticPredictor()
#         _, ancestry_model_dir = find_model_directories()
#         
#         ancestry_loaded = False
#         known_populations = []
#         
#         if ancestry_model_dir:
#             ancestry_loaded = predictor.load_ancestry_predictor(ancestry_model_dir)
#             
#             if ancestry_loaded:
#                 known_populations = [
#                     {
#                         "code": pop,
#                         "display_code": POP_INFO[pop]["code"] if pop in POP_INFO else "",
#                         "description": POP_INFO[pop]["description"] if pop in POP_INFO else "Unknown population",
#                     }
#                     for pop in predictor.ancestry_predictor.known_populations
#                 ]
# 
#         return render_template(
#             "populations.html",
#             populations=known_populations,
#             population_info=POP_INFO,
#             ancestry_loaded=ancestry_loaded,
#         )
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return render_template(
#             "populations.html",
#             populations=[],
#             population_info=POPULATION_INFO,
#             ancestry_loaded=False,
#             error=str(e)
#         )

