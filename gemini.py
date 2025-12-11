import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import warnings
import json
import requests
from sklearn.preprocessing import LabelEncoder
import traceback

# Suppress warnings
warnings.filterwarnings('ignore')

# Function to find model directories and files
def find_model_files():
    """
    Find the model directories and files in the current structure
    """
    print("Searching for model files...")
    
    # Define base directories to search
    base_dirs = [
        '.', 
        './hapmap_data', 
        './sex_prediction_package',
        'X:/DNA',                     # From your file structure
        'X:/DNA/hapmap_data'          # From your file structure
    ]
    
    # Sex prediction files
    sex_files = {
        'model_file': 'best_sex_model.pkl',
        'ensemble_model_file': 'ensemble_sex_model.pkl',
        'features_file': 'sex_features_pca.csv',
        'pca_file': 'pca_model.pkl',
        'selector_file': 'feature_selector.pkl',
        'snps_file': 'sex_selected_snps.csv'
    }
    
    # Ancestry prediction files
    ancestry_files = {
        'model_file': 'best_population_model.pkl',
        'encoder_file': 'population_encoder.pkl',
        'features_file': 'genetic_features_pca.csv',
        'snps_file': 'selected_snps.csv'
    }
    
    # Paths for sex prediction
    sex_dirs = {
        'model_dir': None,
        'data_dir': None
    }
    
    # Paths for ancestry prediction
    ancestry_dirs = {
        'model_dir': None,
        'data_dir': None
    }
    
    # Search for sex prediction files
    for base_dir in base_dirs:
        # Check common subdirectories
        sub_dirs = [
            'sex_prediction_data',
            'models',
            'hapmap_data/sex_prediction_data'
        ]
        
        for sub_dir in sub_dirs:
            dir_path = os.path.join(base_dir, sub_dir)
            if os.path.exists(dir_path) and os.path.exists(os.path.join(dir_path, sex_files['model_file'])):
                sex_dirs['model_dir'] = dir_path
                sex_dirs['data_dir'] = dir_path  # Default to same dir
                print(f"Found sex prediction model dir: {dir_path}")
                break
        
        if sex_dirs['model_dir']:
            break
    
    # Search for ancestry prediction files
    for base_dir in base_dirs:
        # Check common subdirectories
        sub_dirs = [
            'Model_region',
            'models/ancestry',
            'hapmap_data/Model_region'
        ]
        
        for sub_dir in sub_dirs:
            dir_path = os.path.join(base_dir, sub_dir)
            if os.path.exists(dir_path) and os.path.exists(os.path.join(dir_path, ancestry_files['model_file'])):
                ancestry_dirs['model_dir'] = dir_path
                ancestry_dirs['data_dir'] = dir_path  # Default to same dir
                print(f"Found ancestry prediction model dir: {dir_path}")
                break
        
        if ancestry_dirs['model_dir']:
            break
    
    # Verify all required files exist in their directories
    sex_paths = {}
    if sex_dirs['model_dir']:
        for file_key, filename in sex_files.items():
            file_path = os.path.join(sex_dirs['model_dir'], filename)
            if os.path.exists(file_path):
                sex_paths[file_key] = file_path
                print(f"Found {file_key}: {file_path}")
            else:
                print(f"Warning: {file_key} not found at {file_path}")
    
    ancestry_paths = {}
    if ancestry_dirs['model_dir']:
        for file_key, filename in ancestry_files.items():
            file_path = os.path.join(ancestry_dirs['model_dir'], filename)
            if os.path.exists(file_path):
                ancestry_paths[file_key] = file_path
                print(f"Found {file_key}: {file_path}")
            else:
                print(f"Warning: {file_key} not found at {file_path}")
    
    return sex_dirs, sex_paths, ancestry_dirs, ancestry_paths

# Import the SexPredictor and AncestryPredictor classes from existing scripts
try:
    from sex_prediction import SexPredictor
    from region_prediction import AncestryPredictor, POPULATION_INFO
    print("Successfully imported prediction modules")
except ImportError as e:
    print(f"Error importing prediction modules: {str(e)}")
    print("Attempting to load modules from current directory...")
    
    # Define the path to the scripts
    sys.path.append('.')
    
    # Try loading again
    try:
        # Try to load from current directory
        from sex_prediction import SexPredictor
        from region_prediction import AncestryPredictor, POPULATION_INFO
        print("Successfully imported prediction modules from current directory")
    except ImportError as e:
        print(f"Failed to import modules: {str(e)}")
        print("Please ensure sex_prediction.py and region_prediction.py are in the current directory")
        raise

class DNAAnalyzer:
    """
    Class that combines sex and ancestry prediction and sends results to Gemini
    """
    def __init__(self, sex_paths, ancestry_paths, gemini_api_key):
        """
        Initialize the DNA analyzer with paths to model files
        """
        print("=== DNA Analysis System ===")
        print("Initializing models...")
        
        self.sex_paths = sex_paths
        self.ancestry_paths = ancestry_paths
        self.gemini_api_key = gemini_api_key
        
        # Initialize sex predictor
        self.sex_predictor = self._initialize_sex_predictor()
        
        # Initialize ancestry predictor
        self.ancestry_predictor = self._initialize_ancestry_predictor()
        
        # Sample information
        self.available_samples = self._get_common_samples()
        
        print("\nDNA Analysis System initialized successfully.")
        print(f"Number of samples available in both models: {len(self.available_samples)}")
    
    def _initialize_sex_predictor(self):
        """
        Initialize the sex predictor with specific file paths
        """
        try:
            print("\nInitializing Sex Predictor...")
            
            # Use specific files as found by the file search
            model_path = self.sex_paths.get('model_file')
            ensemble_path = self.sex_paths.get('ensemble_model_file')
            features_path = self.sex_paths.get('features_file')
            pca_path = self.sex_paths.get('pca_file')
            selector_path = self.sex_paths.get('selector_file')
            snps_path = self.sex_paths.get('snps_file')
            
            # Choose the best model available
            chosen_model_path = ensemble_path if ensemble_path and os.path.exists(ensemble_path) else model_path
            
            if not chosen_model_path:
                print("Error: No sex prediction model file found")
                return None
                
            if not features_path:
                print("Warning: No sex features file found")
            
            # Create the sex predictor
            predictor = SexPredictor(
                model_path=chosen_model_path,
                features_path=features_path if features_path and os.path.exists(features_path) else None,
                pca_path=pca_path if pca_path and os.path.exists(pca_path) else None,
                selector_path=selector_path if selector_path and os.path.exists(selector_path) else None,
                selected_snps_path=snps_path if snps_path and os.path.exists(snps_path) else None
            )
            
            return predictor
            
        except Exception as e:
            print(f"Error initializing sex predictor: {str(e)}")
            traceback.print_exc()
            return None
    
    def _initialize_ancestry_predictor(self):
        """
        Initialize the ancestry predictor with specific file paths
        """
        try:
            print("\nInitializing Ancestry Predictor...")
            
            # Use specific files as found by the file search
            model_path = self.ancestry_paths.get('model_file')
            encoder_path = self.ancestry_paths.get('encoder_file')
            features_path = self.ancestry_paths.get('features_file')
            snps_path = self.ancestry_paths.get('snps_file')
            
            if not model_path or not encoder_path or not features_path:
                print("Error: Required ancestry prediction files not found")
                return None
            
            # Create the ancestry predictor
            predictor = AncestryPredictor(
                model_path=model_path,
                encoder_path=encoder_path,
                features_path=features_path,
                selected_snps_path=snps_path if snps_path and os.path.exists(snps_path) else None
            )
            
            return predictor
            
        except Exception as e:
            print(f"Error initializing ancestry predictor: {str(e)}")
            traceback.print_exc()
            return None
    
    def _get_common_samples(self):
        """
        Get samples that are available in both sex and ancestry datasets
        """
        if not self.sex_predictor or not self.ancestry_predictor:
            return []
            
        sex_samples = set(self.sex_predictor.features_df['IID'].unique())
        ancestry_samples = set(self.ancestry_predictor.features_df['IID'].unique())
        
        common_samples = sex_samples.intersection(ancestry_samples)
        return list(common_samples)
    
    def analyze_sample(self, sample_id):
        """
        Analyze a sample ID and return sex and ancestry predictions
        """
        if not self.sex_predictor or not self.ancestry_predictor:
            return None
            
        if sample_id not in self.available_samples:
            print(f"Sample {sample_id} not available in both models.")
            return None
        
        # Get sex prediction
        sex_prediction, sex_label, true_sex, true_sex_label = self.sex_predictor.predict_by_id(sample_id)
        
        # Get ancestry prediction
        ancestry_prediction, true_ancestry = self.ancestry_predictor.predict_by_id(sample_id)
        
        # Get ancestry details
        ancestry_details = POPULATION_INFO.get(ancestry_prediction, {})
        ancestry_description = ancestry_details.get('description', 'Unknown ancestry')
        
        # Compile results
        results = {
            'sample_id': sample_id,
            'sex': {
                'predicted': sex_label,
                'code': sex_prediction,
                'true': true_sex_label,
                'true_code': true_sex
            },
            'ancestry': {
                'predicted': ancestry_prediction,
                'description': ancestry_description,
                'true': true_ancestry
            }
        }
        
        return results
    
    def display_analysis(self, analysis_results):
        """
        Display the analysis results
        """
        if not analysis_results:
            return
            
        print("\n=== DNA Analysis Results ===")
        print(f"Sample ID: {analysis_results['sample_id']}")
        
        # Sex prediction
        print("\nSex Prediction:")
        print(f"Predicted: {analysis_results['sex']['predicted']} (code: {analysis_results['sex']['code']})")
        if analysis_results['sex']['true']:
            print(f"True: {analysis_results['sex']['true']} (code: {analysis_results['sex']['true_code']})")
            is_correct = analysis_results['sex']['code'] == analysis_results['sex']['true_code']
            print(f"Prediction is {'Correct ✓' if is_correct else 'Incorrect ✗'}")
        
        # Ancestry prediction
        print("\nAncestry Prediction:")
        print(f"Predicted: {analysis_results['ancestry']['predicted']} - {analysis_results['ancestry']['description']}")
        if analysis_results['ancestry']['true']:
            print(f"True: {analysis_results['ancestry']['true']}")
            is_correct = analysis_results['ancestry']['predicted'] == analysis_results['ancestry']['true']
            print(f"Prediction is {'Correct ✓' if is_correct else 'Incorrect ✗'}")
    
    def get_available_sample_list(self, limit=10):
        """
        Get a list of available samples with information
        """
        if not self.sex_predictor or not self.ancestry_predictor or not self.available_samples:
            return []
            
        # Select a subset of samples
        import random
        sample_subset = random.sample(self.available_samples, min(limit, len(self.available_samples)))
        
        # Get information for each sample
        sample_info = []
        for sample_id in sample_subset:
            sex_info = "Unknown"
            if 'SEX' in self.sex_predictor.features_df.columns:
                mask = self.sex_predictor.features_df['IID'] == sample_id
                if mask.any():
                    sex_code = self.sex_predictor.features_df.loc[mask, 'SEX'].values[0]
                    sex_info = self.sex_predictor.sex_labels.get(sex_code, f"Unknown ({sex_code})")
            
            ancestry_info = "Unknown"
            if 'Population' in self.ancestry_predictor.features_df.columns:
                mask = self.ancestry_predictor.features_df['IID'] == sample_id
                if mask.any():
                    ancestry_code = self.ancestry_predictor.features_df.loc[mask, 'Population'].values[0]
                    if ancestry_code in POPULATION_INFO:
                        ancestry_info = f"{ancestry_code} - {POPULATION_INFO[ancestry_code]['description']}"
                    else:
                        ancestry_info = ancestry_code
            
            sample_info.append({
                'sample_id': sample_id,
                'sex': sex_info,
                'ancestry': ancestry_info
            })
        
        return sample_info
    
    def display_available_samples(self, limit=10):
        """
        Display available samples
        """
        sample_info = self.get_available_sample_list(limit)
        
        print(f"\nAvailable Samples (showing {len(sample_info)} of {len(self.available_samples)}):")
        for i, info in enumerate(sample_info):
            print(f"{i+1}. {info['sample_id']} - Sex: {info['sex']}, Ancestry: {info['ancestry']}")
        
        return sample_info
    
    def send_to_gemini(self, analysis_results):
        """
        Send the analysis results to Gemini API for further insights
        """
        if not analysis_results:
            print("No analysis results to send to Gemini.")
            return None
            
        print("\nSending analysis results to Gemini API for additional insights...")
        
        # Format the prompt for Gemini
        prompt = self._create_gemini_prompt(analysis_results)
        
        # Call Gemini API
        response = self._call_gemini_api(prompt)
        
        return response
    
    def _create_gemini_prompt(self, analysis_results):
        """
        Create the prompt for Gemini API
        """
        prompt = f"""
Based on DNA analysis results, provide possible genetic features, characteristics, and ancestry insights for this individual.

Sample details:
- Sample ID: {analysis_results['sample_id']}
- Predicted Sex: {analysis_results['sex']['predicted']}
- Predicted Ancestry: {analysis_results['ancestry']['predicted']} - {analysis_results['ancestry']['description']}

As a genetic analysis AI, please provide:
1. Physical characteristics that might be common in this ancestry group
2. Health predispositions or genetic conditions common in this population (if any)
3. Historical and geographical insights related to this ancestry
4. Interesting genetic facts about this population
5. Recommendations for further genetic testing based on ancestry-specific insights

Please format your response as a structured report with clear sections and remember these are statistical probabilities, not certainties.
"""
        return prompt
    
    def _call_gemini_api(self, prompt):
        """
        Call the Gemini API with the given prompt
        """
        try:
            api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
            headers = {"Content-Type": "application/json"}
            
            # Add the API key as a query parameter
            api_url = f"{api_url}?key={self.gemini_api_key}"
            
            # Prepare the request
            request_data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048
                }
            }
            
            # Make the request
            response = requests.post(api_url, headers=headers, data=json.dumps(request_data))
            
            # Check if the request was successful
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract the generated text
                if 'candidates' in response_data and len(response_data['candidates']) > 0:
                    if 'content' in response_data['candidates'][0]:
                        content = response_data['candidates'][0]['content']
                        if 'parts' in content and len(content['parts']) > 0:
                            generated_text = content['parts'][0].get('text', '')
                            return generated_text
            
            # If we reached here, something went wrong
            print(f"Error calling Gemini API: {response.status_code}")
            print(response.text)
            return f"Error: Unable to get insights from Gemini API. Status code: {response.status_code}"
            
        except Exception as e:
            print(f"Exception when calling Gemini API: {str(e)}")
            traceback.print_exc()
            return f"Error: {str(e)}"

# Find model directories and files
sex_dirs, sex_paths, ancestry_dirs, ancestry_paths = find_model_files()

# Print found model files
print("\nFound model files:")
print("Sex prediction files:")
for key, path in sex_paths.items():
    print(f"- {key}: {path}")

print("\nAncestry prediction files:")
for key, path in ancestry_paths.items():
    print(f"- {key}: {path}")

# Gemini API key
gemini_api_key = "AIzaSyBtAZU9tpTTi6XBVKE28N16LQhyQkDkmDY"  # Your Gemini API key

# Initialize the analyzer
analyzer = DNAAnalyzer(
    sex_paths=sex_paths,
    ancestry_paths=ancestry_paths,
    gemini_api_key=gemini_api_key
)

# Show some available samples
sample_info = analyzer.display_available_samples(limit=10)

# Example: Analyze a specific sample
if sample_info:
    # You can choose any sample from the list
    sample_id = sample_info[0]['sample_id']  # Default to first sample
    
    # Or you can specify a sample ID directly if you know it
    # sample_id = "NA18969"  # Example sample ID
    
    print(f"\nAnalyzing sample: {sample_id}")
    results = analyzer.analyze_sample(sample_id)
    
    if results:
        analyzer.display_analysis(results)
        
        # Get Gemini insights
        print("\nGetting insights from Gemini API...")
        gemini_response = analyzer.send_to_gemini(results)
        
        if gemini_response:
            print("\n=== Gemini AI Insights ===")
            print(gemini_response)
            
            # Save insights to file
            output_filename = f"gemini_insights_{results['sample_id']}.txt"
            with open(output_filename, 'w') as f:
                f.write(f"=== DNA Analysis Results ===\n")
                f.write(f"Sample ID: {results['sample_id']}\n")
                f.write(f"Sex: {results['sex']['predicted']}\n")
                f.write(f"Ancestry: {results['ancestry']['predicted']} - {results['ancestry']['description']}\n\n")
                f.write("=== Gemini AI Insights ===\n")
                f.write(gemini_response)
            print(f"\nInsights saved to {output_filename}")
else:
    print("No samples available for analysis. Please check model files and data.")