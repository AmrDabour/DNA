import os
import joblib
import json
import numpy as np
import pandas as pd
import time
import datetime
from importlib.machinery import SourceFileLoader

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
        print("\n=== PREDICTION RESULTS ===")
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
        
        # Save a backup copy directly to the working directory
        with open(f"{patient_id}_region_prediction_results.json", 'w') as f:
            json.dump(result, f, indent=2)
            
        print(f"Backup copy saved to current directory: {patient_id}_region_prediction_results.json")
        
        return result
    
    except Exception as e:
        print(f"Error processing patient data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def run_batch_prediction(package_dir, samples_dir, pattern="*.csv"):
    """
    Run predictions on multiple patient samples
    
    Args:
        package_dir: Directory containing the prediction model package
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
        print(f"\n===== Processing sample {i+1}/{len(sample_files)} =====")
        result = predict_patient_region(package_dir, file_path)
        
        if result:
            results.append({
                'file': os.path.basename(file_path),
                'predicted': result['prediction']['predicted_population'],
                'true': result['patient_info']['true_population'],
                'correct': result['prediction']['correct']
            })
    
    # Summarize results
    if results:
        correct_count = sum(1 for r in results if r['correct'] == True)
        total_with_truth = sum(1 for r in results if r['correct'] is not None)
        
        print("\n===== BATCH PREDICTION SUMMARY =====")
        print(f"Total samples processed: {len(results)}")
        
        if total_with_truth > 0:
            accuracy = correct_count / total_with_truth
            print(f"Overall accuracy: {accuracy:.2%} ({correct_count}/{total_with_truth})")
        
        # Save summary to file
        summary_file = "batch_prediction_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'samples_processed': len(results),
                'accuracy': correct_count / total_with_truth if total_with_truth > 0 else None,
                'results': results
            }, f, indent=2)
        
        print(f"Summary saved to: {summary_file}")

# Execute the function if this script is run directly
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Predict population/region for genetic samples')
    parser.add_argument('--package-dir', type=str, default='region_prediction_package', 
                        help='Directory containing the model package')
    parser.add_argument('--sample', type=str, default=None,
                        help='Path to a single sample file')
    parser.add_argument('--samples-dir', type=str, default=None,
                        help='Directory containing multiple sample files')
    parser.add_argument('--pattern', type=str, default='*.csv',
                        help='File pattern for batch processing')
    
    args = parser.parse_args()
    
    if args.sample:
        # Process a single sample
        predict_patient_region(args.package_dir, args.sample)
    elif args.samples_dir:
        # Process batch of samples
        run_batch_prediction(args.package_dir, args.samples_dir, args.pattern)
    else:
        print("Error: Either --sample or --samples-dir must be specified")
        parser.print_help()