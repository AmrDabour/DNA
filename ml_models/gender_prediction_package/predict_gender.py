
#!/usr/bin/env python
"""
Gender Prediction from SNP Data
============================
This script uses a pre-trained model to predict Biological Gender from genetic SNP data.
"""

import os
import sys
import json
import joblib
import argparse
import numpy as np
import pandas as pd
import time
from importlib.machinery import SourceFileLoader

def predict_gender(input_file, model_dir='.', output_file=None, verbose=True):
    """
    Predict gender from SNP data using the pre-trained model
    
    Args:
        input_file: Path to input CSV file containing SNP data
        model_dir: Directory containing model files
        output_file: Path to output CSV file (optional)
        verbose: Whether to print detailed output
    
    Returns:
        Dictionary with prediction results
    """
    if verbose:
        print(f"Gender Prediction Pipeline\n======================")
    
    # 1. Load model components
    if verbose:
        print("\nLoading model components...")
    
    # Load metadata
    with open(os.path.join(model_dir, 'metadata.json'), 'r') as f:
        metadata = json.load(f)
    
    # Import encoding function
    encoding_module = SourceFileLoader("encoding_module", 
                                     os.path.join(model_dir, 'encoding_function.py')).load_module()
    improved_encoding = encoding_module.improved_encoding
    
    # Load required components
    components = {}
    components['pca'] = joblib.load(os.path.join(model_dir, 'pca_model.pkl'))
    components['best_model'] = joblib.load(os.path.join(model_dir, 'best_gender_model.pkl'))
    components['selected_snps'] = pd.read_csv(os.path.join(model_dir, 'gender_selected_snps.csv'))
    
    # Try to load selected indices
    try:
        components['selected_indices'] = joblib.load(os.path.join(model_dir, 'selected_indices.pkl'))
    except:
        if verbose:
            print("  Selected indices file not found, will use all SNPs")
    
    # Try to load population encoder
    try:
        components['pop_encoder'] = joblib.load(os.path.join(model_dir, 'population_encoder.pkl'))
    except:
        if verbose:
            print("  Population encoder not found, will use default value")
    
    # Optional: load ensemble model
    try:
        components['ensemble_model'] = joblib.load(os.path.join(model_dir, 'ensemble_gender_model.pkl'))
    except:
        if verbose:
            print("  Ensemble model not found, using primary model only")
    
    # 2. Read input data
    if verbose:
        print(f"\nReading input file: {input_file}")
    
    try:
        sample_data = pd.read_csv(input_file)
        
        # Extract metadata
        if 'gender' in sample_data.columns:
            true_sex = sample_data['gender'].iloc[0]
            true_sex_label = "Male" if true_sex == 1 else "Female" if true_sex == 2 else "Unknown"
        else:
            true_sex = None
            true_sex_label = "Unknown"
        
        if 'Patient_ID' in sample_data.columns:
            patient_id = sample_data['Patient_ID'].iloc[0]
        else:
            patient_id = os.path.basename(input_file).split('.')[0]
        
        if 'Population' in sample_data.columns:
            population = sample_data['Population'].iloc[0]
        else:
            population = "Unknown"
        
        if verbose:
            print(f"  Sample info - ID: {patient_id}, True Gender: {true_sex_label}, Population: {population}")
            print(f"  Sample contains {len(sample_data)} SNPs")
        
        # 3. Match SNPs with selected ones and prepare allele data
        matched_snps = 0
        genotype_data = []
        
        # Create a lookup for the sample data
        sample_snp_lookup = {row['SNP']: (row['Allele1'], row['Allele2']) 
                           for _, row in sample_data.iterrows() 
                           if 'SNP' in row and 'Allele1' in row and 'Allele2' in row}
        
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
        if verbose:
            print(f"  Matched {matched_snps} SNPs with the model reference panel ({match_rate:.1f}%)")
        
        # 4. Process genetic data
        start_time = time.time()
        
        # Encode genotype data
        genotype_array = np.array(genotype_data).reshape(1, -1)
        encoded_data = improved_encoding(genotype_array, verbose=False)
        
        # Apply feature selection if needed (using the indices directly)
        if 'selected_indices' in components:
            X_selected = encoded_data[:, components['selected_indices']]
        else:
            X_selected = encoded_data
        
        # Apply PCA transformation
        X_pca = components['pca'].transform(X_selected)
        
        # Add population encoded feature if needed
        if 'expected_features' in metadata and metadata['expected_features'] > X_pca.shape[1]:
            # Get the population index if we have the encoder
            if 'pop_encoder' in components and population in components['pop_encoder'].classes_:
                pop_idx = components['pop_encoder'].transform([population])[0]
            else:
                pop_idx = 0  # Default value
            
            # Add as an extra feature
            pop_feature = np.array([pop_idx]).reshape(1, 1)
            X_features = np.hstack([X_pca, pop_feature])
        else:
            X_features = X_pca
        
        # 5. Make prediction
        gender_prediction = components['best_model'].predict(X_features)[0]
        pred_sex_label = "Male" if gender_prediction == 1 else "Female"
        
        # Get ensemble prediction if available
        ensemble_prediction = None
        ensemble_sex_label = None
        if 'ensemble_model' in components:
            try:
                ensemble_prediction = components['ensemble_model'].predict(X_features)[0]
                ensemble_sex_label = "Male" if ensemble_prediction == 1 else "Female"
            except Exception as e:
                if verbose:
                    print(f"  Warning: Error with ensemble prediction: {str(e)}")
        
        # Get confidence scores if available
        confidence_scores = {}
        if hasattr(components['best_model'], 'predict_proba'):
            try:
                probabilities = components['best_model'].predict_proba(X_features)[0]
                if len(probabilities) >= 2:
                    confidence_scores = {
                        1: probabilities[0],  # Male
                        2: probabilities[1]   # Female
                    }
                    
                    if verbose:
                        print(f"  Confidence scores:")
                        for sex_value, prob in confidence_scores.items():
                            sex_label = "Male" if sex_value == 1 else "Female"
                            marker = " ← PREDICTED" if sex_value == gender_prediction else ""
                            print(f"    {sex_label}: {prob:.4f}{marker}")
            except Exception as e:
                if verbose:
                    print(f"  Warning: Error getting confidence scores: {str(e)}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # 6. Create result
        result = {
            'Sample_ID': patient_id,
            'Population': population,
            'True_Sex': true_sex,
            'True_Sex_Label': true_sex_label,
            'Predicted_Sex': gender_prediction,
            'Predicted_Sex_Label': pred_sex_label,
            'Male_Confidence': confidence_scores.get(1, None),
            'Female_Confidence': confidence_scores.get(2, None),
            'Matched_SNPs': matched_snps,
            'Match_Rate': match_rate / 100.0,
            'Processing_Time': processing_time
        }
        
        # Add ensemble prediction if available
        if ensemble_prediction is not None:
            result['Ensemble_Predicted_Sex'] = ensemble_prediction
            result['Ensemble_Predicted_Sex_Label'] = ensemble_sex_label
        
        # 7. Print and save results
        if verbose:
            print(f"  PREDICTION: {pred_sex_label}")
            if true_sex in [1, 2]:
                correct = gender_prediction == true_sex
                result['Correct_Prediction'] = correct
                print(f"  Correct: {correct}")
            print(f"  Processing time: {processing_time:.2f} seconds")
        
        if output_file:
            # Save as CSV
            pd.DataFrame([result]).to_csv(output_file, index=False)
            if verbose:
                print(f"\nResults saved to {output_file}")
        
        return result
    
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def predict_batch(input_dir, model_dir='.', output_file='batch_results.csv', pattern='*.csv'):
    """
    Predict gender for a batch of samples
    
    Args:
        input_dir: Directory containing input CSV files
        model_dir: Directory containing model files
        output_file: Path to output CSV file
        pattern: File pattern for input files
    
    Returns:
        DataFrame with prediction results
    """
    import glob
    
    print(f"Batch Processing: {input_dir}\n=========================")
    
    # Find all input files
    input_files = glob.glob(os.path.join(input_dir, pattern))
    
    if not input_files:
        print(f"No files matching {pattern} found in {input_dir}")
        return None
    
    print(f"Found {len(input_files)} files to process\n")
    
    # Process each file
    results = []
    for i, file_path in enumerate(input_files):
        print(f"Processing file {i+1}/{len(input_files)}: {os.path.basename(file_path)}")
        result = predict_gender(file_path, model_dir=model_dir, verbose=False)
        if result:
            results.append(result)
        print(f"  {'✓' if result else '✗'} Completed\n")
    
    # Summarize and save results
    if results:
        results_df = pd.DataFrame(results)
        
        # Print summary
        print("\nPrediction Summary:")
        print(f"  Total samples processed: {len(results_df)}")
        
        # Summarize by Predicted Gender
        sex_counts = results_df['Predicted_Sex_Label'].value_counts()
        for sex_label, count in sex_counts.items():
            print(f"  Predicted as {sex_label}: {count}")
        
        # Calculate accuracy if True Gender is available
        if 'Correct_Prediction' in results_df.columns:
            valid_results = results_df[results_df['True_Sex'].isin([1, 2])]
            if len(valid_results) > 0:
                accuracy = sum(valid_results['Correct_Prediction']) / len(valid_results)
                print(f"\nAccuracy: {accuracy:.2%} ({sum(valid_results['Correct_Prediction'])}/{len(valid_results)})")
        
        # Save to CSV
        results_df.to_csv(output_file, index=False)
        print(f"\nBatch results saved to {output_file}")
        
        return results_df
    
    return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Predict Biological Gender from SNP data')
    parser.add_argument('--input', required=True, help='Input CSV file or directory')
    parser.add_argument('--output', default=None, help='Output CSV file')
    parser.add_argument('--model-dir', default='.', help='Directory containing model files')
    parser.add_argument('--batch', action='store_true', help='Process all CSV files in input directory')
    parser.add_argument('--pattern', default='*.csv', help='File pattern for batch processing')
    parser.add_argument('--quiet', action='store_true', help='Suppress detailed output')
    
    args = parser.parse_args()
    
    if args.batch:
        # Batch processing
        predict_batch(args.input, model_dir=args.model_dir, 
                     output_file=args.output or 'batch_results.csv',
                     pattern=args.pattern)
    else:
        # Single file processing
        predict_gender(args.input, model_dir=args.model_dir, 
                   output_file=args.output,
                   verbose=not args.quiet)

if __name__ == '__main__':
    main()
