import os
import sys
import numpy as np
import pandas as pd
import joblib
import json
import time
import datetime
from importlib.machinery import SourceFileLoader
import traceback
import argparse

def predict_patient_gender(package_dir, patient_file):
    """
    Predict gender from a patient's SNP data using the pre-trained models
    
    Args:
        package_dir: Path to the directory containing the model files
        patient_file: Path to the CSV file containing patient SNP data
    
    Returns:
        Dictionary with prediction results
    """
    print(f"Loading Gender Prediction models from: {package_dir}")
    print(f"Patient SNP file: {patient_file}")
    
    # 1. Load model components
    start_time = time.time()
    
    # Load metadata
    with open(os.path.join(package_dir, 'metadata.json'), 'r') as f:
        metadata = json.load(f)
    print(f"Loaded metadata for {metadata.get('target', 'gender')} prediction")
    
    # Load encoding function
    encoding_module = SourceFileLoader("encoding_module", 
                                     os.path.join(package_dir, 'encoding_function.py')).load_module()
    improved_encoding = encoding_module.improved_encoding
    print("Loaded encoding function")
    
    # Load all required model components
    components = {
        'pca': joblib.load(os.path.join(package_dir, 'pca_model.pkl')),
        'best_model': joblib.load(os.path.join(package_dir, 'best_gender_model.pkl')),
        'selected_snps': pd.read_csv(os.path.join(package_dir, 'gender_selected_snps.csv')),
    }
    
    # Try to load population encoder if it exists
    try:
        components['pop_encoder'] = joblib.load(os.path.join(package_dir, 'population_encoder.pkl'))
        print(f"Loaded population encoder with {len(components['pop_encoder'].classes_)} populations")
    except Exception as e:
        print(f"Population encoder not found or could not be loaded: {str(e)}")
    
    # Try to load ensemble model
    try:
        components['ensemble_model'] = joblib.load(os.path.join(package_dir, 'ensemble_gender_model.pkl'))
        print("Loaded ensemble model for comparison")
    except Exception as e:
        print(f"Ensemble model not found or could not be loaded: {str(e)}")
    
    print(f"Loaded {len(components['selected_snps'])} selected SNPs information")
    
    # 2. Read and process patient data
    try:
        print(f"\nReading patient SNP data from: {patient_file}")
        patient_data = pd.read_csv(patient_file)
        
        # Extract patient metadata
        patient_id = patient_data['Patient_ID'].iloc[0] if 'Patient_ID' in patient_data.columns else os.path.basename(patient_file).split('.')[0]
        population = patient_data['Population'].iloc[0] if 'Population' in patient_data.columns else "Unknown"
        true_sex = patient_data['gender'].iloc[0] if 'gender' in patient_data.columns else 0
        
        sex_label = "Male" if true_sex == 1 else "Female" if true_sex == 2 else "Unknown"
        print(f"Patient info - ID: {patient_id}, True Gender: {sex_label} ({true_sex}), Population: {population}")
        print(f"Patient data contains {len(patient_data)} SNPs")
        
        # 3. Match SNPs with the selected ones
        matched_snps = 0
        genotype_data = []
        
        # Create a lookup for the patient data
        patient_snp_lookup = {row['SNP']: (row['Allele1'], row['Allele2']) 
                           for _, row in patient_data.iterrows() 
                           if 'SNP' in row and 'Allele1' in row and 'Allele2' in row}
        
        # Extract only the selected SNPs in the right order
        for _, row in components['selected_snps'].iterrows():
            snp_id = row['SNP']
            
            if snp_id in patient_snp_lookup:
                matched_snps += 1
                allele1, allele2 = patient_snp_lookup[snp_id]
                genotype_data.extend([allele1, allele2])
            else:
                # Missing SNP - use placeholders
                genotype_data.extend(['0', '0'])
        
        match_rate = matched_snps/len(components['selected_snps']) * 100
        print(f"Matched {matched_snps} SNPs with the reference panel ({match_rate:.1f}%)")
        
        # 4. Process the data through the prediction pipeline
        # Encode genotype data
        genotype_array = np.array(genotype_data).reshape(1, -1)
        encoded_data = improved_encoding(genotype_array, verbose=False)
        print(f"Encoded data shape: {encoded_data.shape}")
        
        # Apply PCA transformation directly to encoded data
        X_pca = components['pca'].transform(encoded_data)
        print(f"PCA features shape: {X_pca.shape}")
        
        # ALWAYS add population encoded feature - we know we need 51 features total and PCA gives 50
        # Get the population index if we have the encoder
        if 'pop_encoder' in components and population in components['pop_encoder'].classes_:
            pop_idx = components['pop_encoder'].transform([population])[0]
        else:
            # Default value if population unknown or not found in encoder
            pop_idx = 0
        
        # Add as an extra feature - this gives us the 51st feature that StandardScaler expects
        pop_feature = np.array([pop_idx]).reshape(1, 1)
        X_features = np.hstack([X_pca, pop_feature])
        print(f"Added population feature, new shape: {X_features.shape}")
        
        # 5. Make prediction using the best model
        gender_prediction = components['best_model'].predict(X_features)[0]
        pred_sex_label = "Male" if gender_prediction == 1 else "Female"
        
        # Get ensemble prediction if available
        ensemble_prediction = None
        ensemble_label = None
        if 'ensemble_model' in components:
            try:
                ensemble_prediction = components['ensemble_model'].predict(X_features)[0]
                ensemble_label = "Male" if ensemble_prediction == 1 else "Female"
            except Exception as e:
                print(f"Error with ensemble prediction: {str(e)}")
        
        # Get confidence scores if possible
        confidence_scores = {}
        if hasattr(components['best_model'], 'predict_proba'):
            try:
                probabilities = components['best_model'].predict_proba(X_features)[0]
                if len(probabilities) >= 2:  # We should have 2 classes (male/female)
                    confidence_scores = {
                        "Male": float(probabilities[0]),
                        "Female": float(probabilities[1])
                    }
            except Exception as e:
                print(f"Error getting confidence scores: {str(e)}")
                
        processing_time = time.time() - start_time
                
        # 6. Prepare and return results
        result = {
            "patient_id": patient_id,
            "population": population,
            "true_sex": sex_label if true_sex in [1, 2] else "Unknown",
            "predicted_sex": pred_sex_label,
            "male_confidence": confidence_scores.get("Male", None),
            "female_confidence": confidence_scores.get("Female", None),
            "match_rate": float(match_rate),  # Convert numpy.float64 to Python float
            "processing_time": float(processing_time),  # Convert numpy.float64 to Python float
            "correct": bool(gender_prediction == true_sex) if true_sex in [1, 2] else None  # Convert numpy.bool_ to Python bool
        }
        
        if ensemble_prediction is not None:
            result["ensemble_prediction"] = ensemble_label
        
        # Print results
        print("\n=== Gender Prediction RESULTS ===")
        print(f"Patient ID: {patient_id}")
        print(f"Predicted Gender: {pred_sex_label}")
        
        if confidence_scores:
            print(f"Confidence Scores:")
            for gender, conf in confidence_scores.items():
                print(f"  {gender}: {conf:.4f}")
        
        if true_sex in [1, 2]:
            correct = bool(gender_prediction == true_sex)  # Convert numpy.bool_ to Python bool
            print(f"True Gender: {sex_label}")
            print(f"Prediction Correct: {correct}")
        
        if ensemble_prediction is not None:
            print(f"Ensemble Model Prediction: {ensemble_label}")
        
        print(f"Processing Time: {processing_time:.2f} seconds")
        
        return result
        
    except Exception as e:
        print(f"Error processing patient data for Gender Prediction: {str(e)}")
        traceback.print_exc()
        return None


def predict_patient_region(
    package_dir="region_prediction_package", 
    patient_file="sample_data/patient_sample.csv",
    save_metadata=True
):
    """
    Predict ancestral region/population for a patient sample file
    
    Args:
        package_dir: Directory containing the region prediction model package
        patient_file: Path to the patient's SNP data file
        save_metadata: Whether to save model metadata in the results
        
    Returns:
        Dictionary with prediction results
    """
    print(f"Loading region prediction models from: {package_dir}")
    print(f"Patient file: {patient_file}")
    
    # 1. Load all required model components
    start_time = time.time()
    
    # Load metadata
    with open(os.path.join(package_dir, 'metadata.json'), 'r') as f:
        model_metadata = json.load(f)
    print(f"Loaded metadata for {model_metadata.get('target', 'region/population')} prediction")
    
    # Load encoding function
    encoding_module = SourceFileLoader("encoding_module", 
                                     os.path.join(package_dir, 'encoding_function.py')).load_module()
    improved_encoding = encoding_module.improved_encoding
    print("Loaded encoding function")
    
    # Load all components
    components = {
        'pca': joblib.load(os.path.join(package_dir, 'pca_model.pkl')),
        'best_model': joblib.load(os.path.join(package_dir, 'best_population_model.pkl')),
        'selected_snps': pd.read_csv(os.path.join(package_dir, 'selected_snps.csv')),
        'encoder': joblib.load(os.path.join(package_dir, 'population_encoder.pkl'))
    }
    
    # Try to load scaler - it might be part of the pipeline or a separate file
    has_separate_scaler = False
    try:
        components['scaler'] = joblib.load(os.path.join(package_dir, 'scaler_model.pkl'))
        has_separate_scaler = True
        print("Loaded separate scaler model")
    except:
        print("Scaler not found as separate file, may be part of the model pipeline")
    
    # Try to load selected indices if they exist
    has_feature_selection = False
    try:
        components['selected_indices'] = joblib.load(os.path.join(package_dir, 'selected_indices.pkl'))
        has_feature_selection = True
        print(f"Loaded feature selection indices: {len(components['selected_indices'])} features")
    except:
        print("Selected indices file not found, will use all SNPs")
    
    print(f"Loaded all model components")
    
    # 2. Read and process the patient sample
    try:
        print(f"\nReading patient data file: {patient_file}")
        sample_data = pd.read_csv(patient_file)
        
        # Extract metadata
        true_population = sample_data['Population'].iloc[0] if 'Population' in sample_data.columns else "Unknown"
        patient_id = sample_data['Patient_ID'].iloc[0] if 'Patient_ID' in sample_data.columns else os.path.basename(patient_file).split('.')[0]
        gender = sample_data['gender'].iloc[0] if 'gender' in sample_data.columns else None
        
        print(f"Patient info - ID: {patient_id}, True Population: {true_population}")
        print(f"Sample contains {len(sample_data)} SNPs")
        
        # 3. Match SNPs with the reference panel
        matched_snps = 0
        genotype_data = []
        
        # Create a fast lookup dictionary
        sample_snp_lookup = {row['SNP']: (row['Allele1'], row['Allele2']) 
                           for _, row in sample_data.iterrows() 
                           if 'SNP' in row and 'Allele1' in row and 'Allele2' in row}
        
        # Extract only SNPs from the reference panel
        for _, row in components['selected_snps'].iterrows():
            snp_id = row['SNP']
            
            if snp_id in sample_snp_lookup:
                matched_snps += 1
                allele1, allele2 = sample_snp_lookup[snp_id]
                genotype_data.extend([allele1, allele2])
            else:
                # Missing SNP - use placeholders
                genotype_data.extend(['0', '0'])
        
        match_rate = matched_snps/len(components['selected_snps']) * 100
        print(f"Matched {matched_snps} SNPs with the reference panel ({match_rate:.1f}%)")
        
        # 4. Encode genetic data
        genotype_array = np.array(genotype_data).reshape(1, -1)
        encoded_data = improved_encoding(genotype_array, verbose=True)
        print(f"Encoded data shape: {encoded_data.shape}")
        
        # 5. Apply feature selection if needed
        if has_feature_selection:
            X_selected = encoded_data[:, components['selected_indices']]
            print(f"Applied feature selection: {encoded_data.shape} → {X_selected.shape}")
        else:
            X_selected = encoded_data
        
        # 6. Apply PCA transformation
        X_pca = components['pca'].transform(X_selected)
        print(f"PCA features shape: {X_pca.shape}")
        
        # 7. Make prediction
        # If model is a pipeline with a scaler, we can pass X_pca directly
        # Otherwise, we need to apply the scaler first if it exists
        has_pipeline_scaler = hasattr(components['best_model'], 'named_steps') and 'scaler' in components['best_model'].named_steps
        
        if has_pipeline_scaler:
            X_features = X_pca
            print("Using pipeline with built-in scaler")
        elif has_separate_scaler:
            X_features = components['scaler'].transform(X_pca)
            print("Applied separate scaling to features")
        else:
            X_features = X_pca
            print("No scaling applied to features")
        
        # Print some feature values for debugging
        print(f"First few feature values: {X_features[0, :5]}")
        
        # Get prediction
        prediction_idx = components['best_model'].predict(X_features)[0]
        predicted_population = components['encoder'].inverse_transform([prediction_idx])[0]
        
        # 8. Get confidence scores
        confidence_scores = {}
        population_list = components['encoder'].classes_
        
        if hasattr(components['best_model'], 'predict_proba'):
            probabilities = components['best_model'].predict_proba(X_features)[0]
            for i, pop in enumerate(population_list):
                confidence_scores[pop] = float(probabilities[i])
        
        processing_time = time.time() - start_time
        
        # 9. Print and return results
        print("\n=== REGION PREDICTION RESULTS ===")
        print(f"Patient ID: {patient_id}")
        print(f"Predicted Population: {predicted_population}")
        
        if confidence_scores:
            print(f"Top 3 confidence scores:")
            for pop, conf in sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"  {pop}: {conf:.4f}" + (" ← PREDICTED" if pop == predicted_population else ""))
        
        if true_population != "Unknown":
            print(f"True Population: {true_population}")
            correct = predicted_population == true_population
            print(f"Prediction Correct: {correct}")
        
        print(f"Processing Time: {processing_time:.2f} seconds")
        
        # 10. Create comprehensive results dictionary with metadata
        result = {
            # Patient information
            "patient_info": {
                "patient_id": patient_id,
                "true_population": true_population,
                "gender": gender,
                "file_name": os.path.basename(patient_file),
                "snp_count": len(sample_data)
            },
            
            # Prediction results
            "prediction": {
                "predicted_population": predicted_population,
                "correct": predicted_population == true_population if true_population != "Unknown" else None,
                "matched_snps": matched_snps,
                "match_rate": match_rate/100.0,
                "processing_time": processing_time
            },
            
            # Confidence scores
            "confidence_scores": confidence_scores,
            
            # Timestamp
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add top 3 populations
        result["top_populations"] = []
        for i, (pop, conf) in enumerate(sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)[:3]):
            result["top_populations"].append({
                "rank": i+1,
                "population": pop,
                "confidence": conf
            })
        
        # Add model metadata if requested
        if save_metadata:
            result["model_metadata"] = {
                "target": model_metadata.get("target", "region/population"),
                "populations": model_metadata.get("populations", []),
                "max_snps": model_metadata.get("max_snps", 50000),
                "n_pca_components": model_metadata.get("n_pca_components", 50),
                "preprocessing": {
                    "feature_selection_used": has_feature_selection,
                    "pca_shape": X_pca.shape[1] if X_pca is not None else None,
                    "scaler_used": has_separate_scaler or has_pipeline_scaler,
                    "pipeline_scaler": has_pipeline_scaler,
                    "model_type": type(components["best_model"]).__name__
                },
                "package_creation_date": model_metadata.get("package_creation_date", "Unknown")
            }
        
        # Fix numpy types for JSON serialization
        def fix_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: fix_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [fix_numpy_types(item) for item in obj]
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            else:
                return obj
        
        result = fix_numpy_types(result)
        
        # Save results to a file
        result_file = os.path.join(os.path.dirname(patient_file), f"{patient_id}_region_prediction_results.json")
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\nResults saved to: {result_file}")
        
        return result
    
    except Exception as e:
        print(f"Error processing patient data for region prediction: {str(e)}")
        traceback.print_exc()
        return None


def predict_patient_sex_and_region(
    sex_package_dir, 
    region_package_dir,
    patient_file,
    save_metadata=True
):
    """
    Predict both gender and ancestral region/population for a patient sample file
    
    Args:
        sex_package_dir: Directory containing the Gender Prediction model package
        region_package_dir: Directory containing the region prediction model package
        patient_file: Path to the patient's SNP data file
        save_metadata: Whether to save model metadata in the results
        
    Returns:
        Dictionary with combined prediction results
    """
    print(f"\n{'='*80}")
    print(f"COMBINED GENDER AND REGION PREDICTION")
    print(f"{'='*80}")
    print(f"Patient file: {patient_file}")
    print(f"Gender Model directory: {sex_package_dir}")
    print(f"Region model directory: {region_package_dir}")
    
    start_time = time.time()
    
    # Run both predictions
    print(f"\n{'='*40}")
    print(f"RUNNING Gender Prediction")
    print(f"{'='*40}")
    sex_result = predict_patient_gender(sex_package_dir, patient_file)
    
    print(f"\n{'='*40}")
    print(f"RUNNING REGION PREDICTION")
    print(f"{'='*40}")
    region_result = predict_patient_region(region_package_dir, patient_file, save_metadata)
    
    total_processing_time = time.time() - start_time
    
    # Combine results
    patient_id = None
    if sex_result and "patient_id" in sex_result:
        patient_id = sex_result["patient_id"]
    elif region_result and "patient_info" in region_result and "patient_id" in region_result["patient_info"]:
        patient_id = region_result["patient_info"]["patient_id"]
    else:
        patient_id = os.path.basename(patient_file).split('.')[0]
    
    # Create combined results
    combined_result = {
        "patient_id": patient_id,
        "file_name": os.path.basename(patient_file),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_processing_time": total_processing_time,
        "gender_prediction": sex_result,
        "region_prediction": region_result
    }
    
    # Print combined summary
    print(f"\n{'='*60}")
    print(f"COMBINED PREDICTION RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"Patient ID: {patient_id}")
    
    if sex_result:
        print(f"Predicted Gender: {sex_result['predicted_sex']}")
        if "true_sex" in sex_result and sex_result["true_sex"] != "Unknown":
            print(f"True Gender: {sex_result['true_sex']}")
            print(f"Gender Prediction Correct: {sex_result['correct']}")
    else:
        print("Gender Prediction failed")
    
    if region_result and "prediction" in region_result:
        print(f"Predicted Population: {region_result['prediction']['predicted_population']}")
        if "true_population" in region_result["patient_info"] and region_result["patient_info"]["true_population"] != "Unknown":
            print(f"True Population: {region_result['patient_info']['true_population']}")
            print(f"Region Prediction Correct: {region_result['prediction']['correct']}")
    else:
        print("Region prediction failed")
    
    print(f"Total Processing Time: {total_processing_time:.2f} seconds")
    
    # Save combined results to result folder
    result_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "result")
    os.makedirs(result_folder, exist_ok=True)
    
    combined_file = os.path.join(result_folder, f"{patient_id}_combined_prediction_results.json")
    with open(combined_file, 'w') as f:
        json.dump(combined_result, f, indent=2)
    
    print(f"\nCombined results saved to: {combined_file}")
    
    return combined_result


def run_batch_prediction(sex_package_dir, region_package_dir, samples_dir, pattern="*.csv"):
    """
    Run combined gender and region predictions on multiple patient samples
    
    Args:
        sex_package_dir: Directory containing the Gender Prediction model package
        region_package_dir: Directory containing the region prediction model package
        samples_dir: Directory containing the sample files
        pattern: File pattern for finding samples
    """
    import glob
    
    # Find all sample files
    sample_files = glob.glob(os.path.join(samples_dir, pattern))
    
    if not sample_files:
        print(f"No sample files found in {samples_dir} matching pattern {pattern}")
        return
    
    print(f"Found {len(sample_files)} sample files for prediction")
    
    # Process each file
    results = []
    for i, file_path in enumerate(sample_files):
        print(f"\n{'='*80}")
        print(f"PROCESSING SAMPLE {i+1}/{len(sample_files)}: {os.path.basename(file_path)}")
        print(f"{'='*80}")
        
        result = predict_patient_sex_and_region(sex_package_dir, region_package_dir, file_path)
        
        if result:
            # Extract key results for summary
            gender_correct = None
            region_correct = None
            
            if "gender_prediction" in result and result["gender_prediction"] and "correct" in result["gender_prediction"]:
                gender_correct = result["gender_prediction"]["correct"]
                
            if "region_prediction" in result and result["region_prediction"] and "prediction" in result["region_prediction"]:
                region_correct = result["region_prediction"]["prediction"].get("correct")
            
            results.append({
                'file': os.path.basename(file_path),
                'patient_id': result["patient_id"],
                'gender_correct': gender_correct,
                'region_correct': region_correct
            })
    
    # Summarize results
    if results:
        sex_correct_count = sum(1 for r in results if r['gender_correct'] == True)
        region_correct_count = sum(1 for r in results if r['region_correct'] == True)
        
        sex_total_with_truth = sum(1 for r in results if r['gender_correct'] is not None)
        region_total_with_truth = sum(1 for r in results if r['region_correct'] is not None)
        
        print("\n===== BATCH PREDICTION SUMMARY =====")
        print(f"Total samples processed: {len(results)}")
        
        if sex_total_with_truth > 0:
            gender_accuracy = sex_correct_count / sex_total_with_truth
            print(f"Gender Prediction accuracy: {gender_accuracy:.2%} ({sex_correct_count}/{sex_total_with_truth})")
        
        if region_total_with_truth > 0:
            region_accuracy = region_correct_count / region_total_with_truth
            print(f"Region prediction accuracy: {region_accuracy:.2%} ({region_correct_count}/{region_total_with_truth})")
        
        # Save summary to file
        summary_file = "combined_batch_prediction_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'samples_processed': len(results),
                'gender_accuracy': sex_correct_count / sex_total_with_truth if sex_total_with_truth > 0 else None,
                'region_accuracy': region_correct_count / region_total_with_truth if region_total_with_truth > 0 else None,
                'results': results
            }, f, indent=2)
        
        print(f"Summary saved to: {summary_file}")


# Main execution logic
if __name__ == "__main__":
    # Default paths - use organized models directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    default_sex_package_dir = os.path.join(project_root, "models", "gender")
    default_region_package_dir = os.path.join(project_root, "models", "region")
    
    parser = argparse.ArgumentParser(description='Predict gender and/or region/population for genetic samples')
    parser.add_argument('--gender-package-dir', type=str, default=default_sex_package_dir, 
                        help='Directory containing the Gender Prediction model package')
    parser.add_argument('--region-package-dir', type=str, default=default_region_package_dir, 
                        help='Directory containing the region prediction model package')
    parser.add_argument('--sample', type=str, default=None,
                        help='Path to a single sample file')
    parser.add_argument('--samples-dir', type=str, default=None,
                        help='Directory containing multiple sample files')
    parser.add_argument('--pattern', type=str, default='*.csv',
                        help='File pattern for batch processing')
    parser.add_argument('--prediction-type', type=str, choices=['gender', 'region', 'both'], default='both',
                        help='Type of prediction to run: gender, region, or both')
    
    args = parser.parse_args()
    
    if args.sample:
        # Process a single sample
        if args.prediction_type == 'gender':
            predict_patient_gender(args.gender_package_dir, args.sample)
        elif args.prediction_type == 'region':
            predict_patient_region(args.region_package_dir, args.sample)
        else:  # 'both'
            predict_patient_sex_and_region(args.gender_package_dir, args.region_package_dir, args.sample)
    elif args.samples_dir:
        # Process batch of samples
        if args.prediction_type == 'gender':
            print("Batch Gender Prediction not implemented separately. Running combined prediction instead.")
            run_batch_prediction(args.gender_package_dir, args.region_package_dir, args.samples_dir, args.pattern)
        elif args.prediction_type == 'region':
            from predict_patient_region import run_batch_prediction as run_region_batch
            run_region_batch(args.region_package_dir, args.samples_dir, args.pattern)
        else:  # 'both'
            run_batch_prediction(args.gender_package_dir, args.region_package_dir, args.samples_dir, args.pattern)
    else:
        print("Error: Either --sample or --samples-dir must be specified")
        parser.print_help()