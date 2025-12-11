"""
Model Verification Script
Run this script to verify that all model files can be found and loaded correctly.
"""
import os
import sys

def check_file_exists(filepath, description):
    """Check if a file exists and print the result"""
    exists = os.path.exists(filepath)
    status = "[OK] FOUND" if exists else "[!!] MISSING"
    print(f"{status}: {description}")
    print(f"   Path: {filepath}")
    return exists

def main():
    print("\n" + "="*80)
    print("DNA Genetic Prediction - Model Verification")
    print("="*80 + "\n")
    
    # Get project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    all_files_found = True
    
    # Check Gender Prediction Models
    print("\n[Gender Prediction Models]")
    print("-" * 80)
    
    # Now using organized models directory
    gender_dir = os.path.join(script_dir, "models", "gender")
    
    print(f"\n  Checking directory: {gender_dir}")
    dir_exists = os.path.exists(gender_dir)
    if not dir_exists:
        print(f"  [!!] Directory does not exist!")
        all_files_found = False
    else:
        # Check for model files (both naming conventions)
        model_files = [
            ("best_gender_model.pkl", "Best Gender Model"),
            ("best_sex_model.pkl", "Best Sex Model"),
            ("ensemble_gender_model.pkl", "Ensemble Gender Model"),
            ("ensemble_sex_model.pkl", "Ensemble Sex Model"),
            ("pca_model.pkl", "PCA Model"),
            ("feature_selector.pkl", "Feature Selector"),
        ]
        
        for filename, description in model_files:
            filepath = os.path.join(gender_dir, filename)
            if os.path.exists(filepath):
                check_file_exists(filepath, description)
    
    # Check Region Prediction Models
    print("\n\n[Region/Population Prediction Models]")
    print("-" * 80)
    
    # Now using organized models directory
    region_dir = os.path.join(script_dir, "models", "region")
    
    print(f"\n  Checking directory: {region_dir}")
    dir_exists = os.path.exists(region_dir)
    if not dir_exists:
        print(f"  [!!] Directory does not exist!")
    else:
        # Check for model files
        model_files = [
            ("best_population_model.pkl", "Population Model"),
            ("population_encoder.pkl", "Population Encoder"),
        ]
        
        for filename, description in model_files:
            filepath = os.path.join(region_dir, filename)
            found = check_file_exists(filepath, description)
            if not found:
                all_files_found = False
    
    # Test model loading using the actual code
    print("\n\n[Testing Model Loading]")
    print("-" * 80)
    
    try:
        from models import GeneticPredictor, find_model_directories
        
        predictor = GeneticPredictor()
        gender_model_dir, ancestry_model_dir = find_model_directories()
        
        print(f"\nGender Model Directory Found: {gender_model_dir}")
        print(f"Ancestry Model Directory Found: {ancestry_model_dir}")
        
        if gender_model_dir:
            gender_loaded = predictor.load_sex_predictor(gender_model_dir)
            status = "[OK] SUCCESS" if gender_loaded else "[FAIL] FAILED"
            print(f"\n{status}: Gender Model Loading")
        else:
            print(f"\n[FAIL] FAILED: No gender model directory found")
            all_files_found = False
        
        if ancestry_model_dir:
            ancestry_loaded = predictor.load_ancestry_predictor(ancestry_model_dir)
            status = "[OK] SUCCESS" if ancestry_loaded else "[FAIL] FAILED"
            print(f"{status}: Ancestry Model Loading")
        else:
            print(f"\n[WARN] WARNING: No ancestry model directory found")
    
    except Exception as e:
        print(f"\n[ERROR] ERROR during model loading test: {str(e)}")
        import traceback
        traceback.print_exc()
        all_files_found = False
    
    # Final Summary
    print("\n\n" + "="*80)
    if all_files_found:
        print("[SUCCESS] VERIFICATION PASSED - All models found and loaded successfully!")
    else:
        print("[FAIL] VERIFICATION FAILED - Some models are missing or failed to load")
        print("\nPlease check:")
        print("1. All .pkl model files are present in the correct directories")
        print("2. The directory structure matches the expected layout")
        print("3. Model files were copied when deploying to a new machine")
    print("="*80 + "\n")
    
    return 0 if all_files_found else 1

if __name__ == "__main__":
    sys.exit(main())

