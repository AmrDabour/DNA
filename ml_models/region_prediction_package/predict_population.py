
#!/usr/bin/env python
"""
Population/Region Prediction from SNP Data
=========================================
This script uses a pre-trained model to predict population ancestry from genetic SNP data.
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

def predict_population(input_file, model_dir='.', output_file=None, verbose=True):
    """
    Predict population/ancestry from SNP data using the pre-trained model
    
    Args:
        input_file: Path to input CSV file containing SNP data
        model_dir: Directory containing model files
        output_file: Path to output CSV file (optional)
        verbose: Whether to print detailed output
    
    Returns:
        Dictionary with prediction results
    """
    if verbose:
        print(f"Population Prediction Pipeline\n=============================")
    
    # 1. Load model components
    if verbose:
        print("\nLoading model components...")
    
    # Load metadata
    try:
        with open(os.path.join(model_dir, 'metadata.json'), 'r') as f:
            metadata = json.load(f)
        if verbose:
            print(f"  Loaded metadata with {len(metadata.get('populations', []))} populations")
    except Exception as e:
        if verbose:
            print(f"  Warning: Could not load metadata: {str(e)}")
        metadata = {}
    
    # Import encoding function
    encoding_module = SourceFileLoader("encoding_module", 
                                     os.path.join(model_dir, 'encoding_function.py')).load_module()
    improved_encoding = encoding_module.improved_encoding
    
    # Load required components
    components = {}
    required_files = {
        'best_model': 'best_population_model.pkl',
        'pca': 'pca_model.pkl',
        'population_encoder': 'population_encoder.pkl',
        'selected_snps': 'selected_snps.csv'
    }
    
    for name, filename in required_files.items():
        try:
            filepath = os.path.join(model_dir, filename)
            if name == 'selected_snps':
                components[name] = pd.read_csv(filepath)
            else:
                components[name] = joblib.load(filepath)
            if verbose:
                print(f"  Loaded {name} from {filename}")
        except Exception as e:
            if verbose:
                print(f"  Error loading {filename}: {str(e)}")
            if name in ['best_model', 'pca', 'selected_snps']:
                raise RuntimeError(f"Required component {filename} could not be loaded")
    
    # Try to load scaler if it exists as separate file
    try:
        components['scaler'] = joblib.load(os.path.join(model_dir, 'scaler_model.pkl'))
        if verbose:
            print("  Loaded scaler from scaler_model.pkl")
    except:
        if verbose:
            print("  Scaler not found as separate file, will use pipeline scaler if available")
    
    # Check if scaler is part of the model pipeline
    if hasattr(components['best_model'], 'named_steps') and 'scaler' in components['best_model'].named_steps:
        if verbose:
            print("  Using scaler from model pipeline")
        has_pipeline_scaler = True
    else:
        has_pipeline_scaler = False
    
    # 2. Read input data
    if verbose:
        print(f"\nReading input file: {input_file}")
    
    try:
        sample_data = pd.read_csv(input_file)
        
        # Extract metadata
        if 'Population' in sample_data.columns:
            true_population = sample_data['Population'].iloc[0]
        else:
            true_population = "Unknown"
        
        if 'Patient_ID' in sample_data.columns:
            patient_id = sample_data['Patient_ID'].iloc[0]
        else:
            patient_id = os.path.basename(input_file).split('.')[0]
        
        if verbose:
            print(f"  Sample info - ID: {patient_id}, True Population: {true_population}")
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
        
        # Apply PCA transformation
        X_pca = components['pca'].transform(encoded_data)
        
        # Apply scaler if it exists and not part of pipeline
        if 'scaler' in components and not has_pipeline_scaler:
            X_features = components['scaler'].transform(X_pca)
            if verbose:
                print(f"  Applied external scaler to PCA features")
        else:
            X_features = X_pca
        
        # 5. Make prediction
        prediction_idx = components['best_model'].predict(X_features)[0]
        predicted_population = components['population_encoder'].inverse_transform([prediction_idx])[0]
        
        # Get confidence scores if available
        confidence_scores = {}
        if hasattr(components['best_model'], 'predict_proba'):
            probabilities = components['best_model'].predict_proba(X_features)[0]
            for pop_idx, prob in enumerate(probabilities):
                pop_name = components['population_encoder'].inverse_transform([pop_idx])[0]
                confidence_scores[pop_name] = prob
                
            if verbose:
                print(f"  Top 3 population predictions by confidence:")
                for pop, prob in sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
                    marker = " ← PREDICTED" if pop == predicted_population else ""
                    print(f"    {pop}: {prob:.4f}{marker}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # 6. Create result
        result = {
            'Sample_ID': patient_id,
            'True_Population': true_population,
            'Predicted_Population': predicted_population,
            'Matched_SNPs': matched_snps,
            'Match_Rate': match_rate / 100.0,
            'Processing_Time': processing_time
        }
        
        # Add confidence for each population
        for pop, conf in confidence_scores.items():
            result[f'Confidence_{pop}'] = conf
        
        # Add top 3 populations by confidence
        top_pops = sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        for i, (pop, conf) in enumerate(top_pops):
            result[f'Top{i+1}_Population'] = pop
            result[f'Top{i+1}_Confidence'] = conf
        
        # Check if prediction is correct
        result['Correct_Prediction'] = (predicted_population == true_population)
        
        # 7. Print and save results
        if verbose:
            print(f"  PREDICTION: {predicted_population}")
            if true_population != "Unknown":
                print(f"  Correct: {result['Correct_Prediction']}")
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
    Predict population for a batch of samples
    
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
        result = predict_population(file_path, model_dir=model_dir, verbose=False)
        if result:
            results.append(result)
        print(f"  {'✓' if result else '✗'} Completed\n")
    
    # Summarize and save results
    if results:
        results_df = pd.DataFrame(results)
        
        # Print summary
        print("\nPrediction Summary:")
        print(f"  Total samples processed: {len(results_df)}")
        
        # Summarize by predicted population
        pop_counts = results_df['Predicted_Population'].value_counts()
        for pop, count in pop_counts.items():
            print(f"  Predicted as {pop}: {count}")
        
        # Calculate accuracy if true population is available
        valid_predictions = results_df[results_df['True_Population'] != "Unknown"]
        if not valid_predictions.empty:
            accuracy = sum(valid_predictions['Correct_Prediction']) / len(valid_predictions)
            print(f"\nAccuracy: {accuracy:.2%} " + 
                  f"({sum(valid_predictions['Correct_Prediction'])}/{len(valid_predictions)})")
        
        # Save to CSV
        results_df.to_csv(output_file, index=False)
        print(f"\nBatch results saved to {output_file}")
        
        return results_df
    
    return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Predict population ancestry from SNP data')
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
        predict_population(args.input, model_dir=args.model_dir, 
                   output_file=args.output,
                   verbose=not args.quiet)

if __name__ == '__main__':
    main()
