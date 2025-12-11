import pandas as pd
import numpy as np
import os
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# Define population codes and descriptions
POPULATION_INFO = {
    'ASW': {'code': 'A', 'description': 'African ancestry in Southwest USA'},
    'CEU': {'code': 'C', 'description': 'Utah residents with Northern and Western European ancestry from the CEPH collection'},
    'CHB': {'code': 'H', 'description': 'Han Chinese in Beijing, China'},
    'CHD': {'code': 'D', 'description': 'Chinese in Metropolitan Denver, Colorado'},
    'GIH': {'code': 'G', 'description': 'Gujarati Indians in Houston, Texas'},
    'JPT': {'code': 'J', 'description': 'Japanese in Tokyo, Japan'},
    'LWK': {'code': 'L', 'description': 'Luhya in Webuye, Kenya'},
    'MEX': {'code': 'M', 'description': 'Mexican ancestry in Los Angeles, California'},
    'MKK': {'code': 'K', 'description': 'Maasai in Kinyawa, Kenya'},
    'TSI': {'code': 'T', 'description': 'Tuscan in Italy'},
    'YRI': {'code': 'Y', 'description': 'Yoruban in Ibadan, Nigeria (West Africa)'}
}

class AncestryPredictor:
    """
    Class for predicting ancestry using the trained model
    """
    def __init__(self, model_path, encoder_path, features_path, selected_snps_path=None):
        """
        Initialize the class with the required file paths
        """
        print("Loading the ancestry prediction model...")
        
        # Load the model and encoder
        self.model = joblib.load(model_path)
        self.encoder = joblib.load(encoder_path)
        
        # Load the features data used for training
        self.features_df = pd.read_csv(features_path)
        
        # Load the selected SNPs if available
        self.selected_snps = None
        if selected_snps_path and os.path.exists(selected_snps_path):
            self.selected_snps = pd.read_csv(selected_snps_path)
        
        # Number of principal components (from training data)
        self.n_components = len([col for col in self.features_df.columns if col.startswith('PC_')])
        
        # Known populations for the model
        self.known_populations = list(self.encoder.classes_)
        
        print(f"Model loaded successfully.")
        print(f"Number of principal components: {self.n_components}")
        print(f"Known populations: {self.known_populations}")
        
        # Display population information
        self.display_population_info()
    
    def display_population_info(self):
        """
        Display information about the population codes and descriptions
        """
        print("\n=== Population Information ===")
        for pop, info in POPULATION_INFO.items():
            print(f"{pop} ({info['code']}): {info['description']}")
        print()
    
    def predict_by_id(self, sample_id):
        """
        Predict ancestry using the sample ID present in the training data
        """
        if sample_id not in self.features_df['IID'].values:
            print(f"Error: Sample {sample_id} not found in the data.")
            return None, None
        
        # Extract data and make prediction
        sample_data = self.features_df[self.features_df['IID'] == sample_id]
        
        # Prepare features
        feature_cols = [col for col in sample_data.columns if col.startswith('PC_')]
        if 'SEX' in sample_data.columns:
            sample_data['SEX_numeric'] = sample_data['SEX'].fillna(0).astype(int)
            feature_cols.append('SEX_numeric')
        
        # Make prediction
        X = sample_data[feature_cols].values
        prediction = self.model.predict(X)[0]
        predicted_pop = self.encoder.inverse_transform([prediction])[0]
        
        # True population (if available)
        true_pop = None
        if 'Population' in sample_data.columns:
            true_pop = sample_data['Population'].values[0]
        
        return predicted_pop, true_pop
    
    def display_sample_prediction(self, sample_id):
        """
        Display prediction result for a specific sample
        """
        predicted_pop, true_pop = self.predict_by_id(sample_id)
        
        if predicted_pop is None:
            return
        
        print(f"\nSample: {sample_id}")
        
        # Get population code and description if available
        if predicted_pop in POPULATION_INFO:
            info = POPULATION_INFO[predicted_pop]
            print(f"Predicted ancestry: {predicted_pop} ({info['code']}): {info['description']}")
        else:
            print(f"Predicted ancestry: {predicted_pop}")
        
        if true_pop:
            if true_pop in POPULATION_INFO:
                info = POPULATION_INFO[true_pop]
                print(f"True ancestry: {true_pop} ({info['code']}): {info['description']}")
            else:
                print(f"True ancestry: {true_pop}")
            print(f"Prediction is {'Correct ✓' if predicted_pop == true_pop else 'Incorrect ✗'}")
    
    def get_available_samples(self, limit=10):
        """
        Display available sample IDs from the data
        """
        available_ids = self.features_df['IID'].unique().tolist()
        
        # Randomly select samples with diverse populations
        if len(available_ids) > limit and 'Population' in self.features_df.columns:
            # Group samples by population
            pop_samples = {}
            for sample_id in available_ids:
                pop = self.features_df[self.features_df['IID'] == sample_id]['Population'].values[0]
                if pop not in pop_samples:
                    pop_samples[pop] = []
                pop_samples[pop].append(sample_id)
            
            # Select samples from different populations
            selected_ids = []
            remaining_limit = limit
            
            # First, try to get at least one sample from each population
            for pop, samples in pop_samples.items():
                if remaining_limit > 0:
                    import random
                    selected_ids.append(random.choice(samples))
                    remaining_limit -= 1
            
            # If we still have room for more samples, fill randomly
            if remaining_limit > 0:
                remaining_samples = [s for s in available_ids if s not in selected_ids]
                import random
                selected_ids.extend(random.sample(remaining_samples, min(remaining_limit, len(remaining_samples))))
            
            # Make sure we don't exceed the limit
            selected_ids = selected_ids[:limit]
        else:
            # If we don't have population info or not enough samples, just take the first few
            import random
            selected_ids = random.sample(available_ids, min(limit, len(available_ids)))
        
        print(f"Number of available samples: {len(available_ids)}")
        print(f"Examples of available sample IDs:")
        
        for i, sample_id in enumerate(selected_ids):
            pop = "Unknown"
            if 'Population' in self.features_df.columns:
                pop = self.features_df[self.features_df['IID'] == sample_id]['Population'].values[0]
                if pop in POPULATION_INFO:
                    pop_code = POPULATION_INFO[pop]['code']
                    pop = f"{pop} ({pop_code})"
            print(f"{i+1}. {sample_id} ({pop})")
        
        return available_ids
    
    def predict_new_sample(self, sample_path):
        """
        Predict ancestry for a new sample not in the training data
        This functionality would need to be implemented based on your data format
        """
        print("This functionality is not implemented yet.")
        # TODO: Implement prediction for new samples based on your data format

# Function to check for required files
def check_required_files(model_dir):
    """
    Check for the required files in the specified directory
    """
    required_files = {
        'best_population_model.pkl': 'Population classification model',
        'population_encoder.pkl': 'Ancestry encoder',
        'genetic_features_pca.csv': 'Feature data'
    }
    
    optional_files = {
        'selected_snps.csv': 'Selected SNPs list'
    }
    
    # Check for required files
    for filename, description in required_files.items():
        filepath = os.path.join(model_dir, filename)
        if not os.path.exists(filepath):
            print(f"{description} is missing: {filepath}")
            return False
        else:
            print(f"{description} is present: {filepath}")
    
    # Check for optional files
    for filename, description in optional_files.items():
        filepath = os.path.join(model_dir, filename)
        if not os.path.exists(filepath):
            print(f"{description} is missing: {filepath}")
        else:
            print(f"{description} is present: {filepath}")
    
    return True

def main():
    """
    Main function for ancestry prediction
    """
    print("=== Ancestry Prediction System from Genetic Data ===\n")
    
    # Set the base directory (change this to your DNA directory path)
    base_dir = r"X:\DNA"  # Use the raw string (r prefix) for Windows paths
    
    # Set the model directory path
    model_dir = os.path.join(base_dir, 'hapmap_data', 'Model_region')
    
    if not os.path.exists(model_dir):
        print(f"Error: Model directory not found: {model_dir}")
        print("Please enter the correct path to your model directory:")
        user_model_dir = input()
        if os.path.exists(user_model_dir):
            model_dir = user_model_dir
        else:
            print(f"Error: The entered path does not exist: {user_model_dir}")
            return
    
    # Check for required files
    if not check_required_files(model_dir):
        print("Some required files are missing. Ensure that all model files are in the correct location.")
        return
    
    # Load the model
    try:
        # File paths
        model_path = os.path.join(model_dir, 'best_population_model.pkl')
        encoder_path = os.path.join(model_dir, 'population_encoder.pkl')
        features_path = os.path.join(model_dir, 'genetic_features_pca.csv')
        selected_snps_path = os.path.join(model_dir, 'selected_snps.csv')
        
        # Initialize the predictor class
        predictor = AncestryPredictor(
            model_path=model_path,
            encoder_path=encoder_path,
            features_path=features_path,
            selected_snps_path=selected_snps_path
        )
        
        # Display available samples
        available_ids = predictor.get_available_samples(limit=20)
        
        # Interactive menu
        while True:
            print("\n=== Ancestry Prediction Menu ===")
            print("1. Predict by sample ID")
            print("2. Show available sample IDs")
            print("3. Display population information")
            print("4. Exit")
            
            choice = input("\nSelect an option (1-4): ")
            
            if choice == '1':
                sample_id = input("Enter a sample ID to predict: ")
                predictor.display_sample_prediction(sample_id)
            elif choice == '2':
                limit = input("Enter the number of sample IDs to show (default 20): ")
                try:
                    limit = int(limit)
                except ValueError:
                    limit = 20
                predictor.get_available_samples(limit=limit)
            elif choice == '3':
                predictor.display_population_info()
            elif choice == '4':
                print("Exiting...")
                break
            else:
                print("Invalid option, please try again.")
        
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()