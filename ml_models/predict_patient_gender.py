import os
import sys
import numpy as np
import pandas as pd
import joblib
import json
import time
from importlib.machinery import SourceFileLoader

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
        print("\n=== PREDICTION RESULTS ===")
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
        print(f"Error processing patient data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


# Example usage
if __name__ == "__main__":
    # Get command line arguments or use default paths
    if len(sys.argv) > 2:
        package_dir = sys.argv[1]
        patient_file = sys.argv[2]
    else:
        # Default paths - use organized models directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        package_dir = os.path.join(project_root, "models", "gender")
        patient_file = os.path.join(project_root, "patient_snp_data", "gender_samples", "NA19118_YRI_2.csv")
    
    # Run the prediction
    result = predict_patient_gender(package_dir, patient_file)
    
    # Optional: Save results to a file
    if result:
        output_file = os.path.join(os.path.dirname(patient_file), f"{result['patient_id']}_prediction.json")
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to: {output_file}")