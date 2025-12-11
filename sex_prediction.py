import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder
import joblib
import warnings
warnings.filterwarnings('ignore')

class SexPredictor:
    """
    Class for predicting sex (male/female) using the trained model
    """
    def __init__(self, model_path, features_path=None, pca_path=None, selector_path=None, selected_snps_path=None):
        """
        Initialize the class with the required file paths
        """
        print("Loading the sex prediction model...")
        
        # Load the model
        self.model = joblib.load(model_path)
        
        # Load the features data used for training (if available)
        self.features_df = None
        if features_path and os.path.exists(features_path):
            self.features_df = pd.read_csv(features_path)
        
        # Load the PCA model (if available)
        self.pca = None
        if pca_path and os.path.exists(pca_path):
            self.pca = joblib.load(pca_path)
        
        # Load the feature selector (if available)
        self.selector = None
        if selector_path and os.path.exists(selector_path):
            self.selector = joblib.load(selector_path)
        
        # Load the selected SNPs (if available)
        self.selected_snps = None
        if selected_snps_path and os.path.exists(selected_snps_path):
            self.selected_snps = pd.read_csv(selected_snps_path)
        
        # Sex labels for display
        self.sex_labels = {1: 'Male', 2: 'Female'}
        
        # Number of principal components (from training data if available)
        self.n_components = 0
        if self.features_df is not None:
            pc_columns = [col for col in self.features_df.columns if col.startswith('PC_')]
            self.n_components = len(pc_columns)
        
        print(f"Model loaded successfully.")
        if self.features_df is not None:
            print(f"Number of samples in feature data: {len(self.features_df)}")
            print(f"Number of principal components: {self.n_components}")
        if self.selected_snps is not None:
            print(f"Number of selected SNPs: {len(self.selected_snps)}")
    
    def predict_by_id(self, sample_id):
        """
        Predict sex using the sample ID present in the training data
        """
        if self.features_df is None:
            print("Error: No feature data available for prediction by ID.")
            return None, None, None, None
            
        if sample_id not in self.features_df['IID'].values:
            print(f"Error: Sample {sample_id} not found in the data.")
            return None, None, None, None
        
        # Extract data and make prediction
        sample_data = self.features_df[self.features_df['IID'] == sample_id]
        
        # Prepare features
        feature_cols = [col for col in sample_data.columns if col.startswith('PC_')]
        if 'Population_encoded' in sample_data.columns:
            feature_cols.append('Population_encoded')
        
        # Make prediction
        X = sample_data[feature_cols].values
        try:
            prediction = self.model.predict(X)[0]
            predicted_sex_label = self.sex_labels.get(prediction, f"Unknown ({prediction})")
        except ValueError as e:
            if "has" in str(e) and "features" in str(e) and "expecting" in str(e):
                print(f"Error: Feature mismatch when predicting. {str(e)}")
                # Try using only PCA components (without Population_encoded)
                pc_only_cols = [col for col in sample_data.columns if col.startswith('PC_')]
                X = sample_data[pc_only_cols].values
                prediction = self.model.predict(X)[0]
                predicted_sex_label = self.sex_labels.get(prediction, f"Unknown ({prediction})")
            else:
                raise e
        
        # True sex (if available)
        true_sex = None
        true_sex_label = None
        if 'SEX' in sample_data.columns:
            true_sex = sample_data['SEX'].values[0]
            true_sex_label = self.sex_labels.get(true_sex, f"Unknown ({true_sex})")
        
        return prediction, predicted_sex_label, true_sex, true_sex_label
    
    def display_sample_prediction(self, sample_id):
        """
        Display prediction result for a specific sample
        """
        predicted_sex, predicted_label, true_sex, true_label = self.predict_by_id(sample_id)
        
        if predicted_sex is None:
            return
        
        print(f"\nSample: {sample_id}")
        print(f"Predicted sex: {predicted_label} (code: {predicted_sex})")
        
        if true_sex is not None:
            print(f"True sex: {true_label} (code: {true_sex})")
            is_correct = predicted_sex == true_sex
            print(f"Prediction is {'Correct ✓' if is_correct else 'Incorrect ✗'}")
    
    def get_available_samples(self, limit=10):
        """
        Display available sample IDs from the data
        """
        if self.features_df is None:
            print("No feature data available.")
            return []
            
        available_ids = self.features_df['IID'].unique().tolist()
        print(f"Number of available samples: {len(available_ids)}")
        print(f"Examples of available sample IDs:")
        
        for i, sample_id in enumerate(available_ids[:limit]):
            sex = "Unknown"
            pop = "Unknown"
            
            if 'SEX' in self.features_df.columns:
                sex_code = self.features_df[self.features_df['IID'] == sample_id]['SEX'].values[0]
                sex = self.sex_labels.get(sex_code, f"Unknown ({sex_code})")
                
            if 'Population' in self.features_df.columns:
                pop = self.features_df[self.features_df['IID'] == sample_id]['Population'].values[0]
                
            print(f"{i+1}. {sample_id} ({sex}, {pop})")
        
        return available_ids
    
    def analyze_prediction_accuracy(self):
        """
        Analyze and display prediction accuracy statistics
        """
        if self.features_df is None or 'SEX' not in self.features_df.columns:
            print("No feature data or sex labels available for accuracy analysis.")
            return
        
        print("\n=== Sex Prediction Accuracy Analysis ===")
        
        # Predict sex for all samples
        feature_cols = [col for col in self.features_df.columns if col.startswith('PC_')]
        if 'Population_encoded' in self.features_df.columns:
            feature_cols.append('Population_encoded')
        
        try:
            X = self.features_df[feature_cols].values
            predictions = self.model.predict(X)
        except ValueError as e:
            if "has" in str(e) and "features" in str(e) and "expecting" in str(e):
                print(f"Error in analyze_prediction_accuracy: {str(e)}")
                print("Using only PCA components for prediction...")
                
                # Use only PCA components
                pc_cols = [col for col in self.features_df.columns if col.startswith('PC_')]
                X = self.features_df[pc_cols].values
                predictions = self.model.predict(X)
            else:
                raise e
        
        # Calculate overall accuracy
        true_values = self.features_df['SEX'].values
        accuracy = np.mean(predictions == true_values)
        print(f"Overall accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        
        # Calculate accuracy by sex
        for sex_code, sex_label in self.sex_labels.items():
            mask = true_values == sex_code
            if np.sum(mask) > 0:
                sex_accuracy = np.mean(predictions[mask] == true_values[mask])
                print(f"{sex_label} accuracy: {sex_accuracy:.4f} ({sex_accuracy*100:.2f}%) - {np.sum(mask)} samples")
        
        # Calculate accuracy by population (if available)
        if 'Population' in self.features_df.columns:
            print("\nAccuracy by population:")
            populations = self.features_df['Population'].unique()
            
            # Sort populations by size (descending)
            pop_counts = self.features_df['Population'].value_counts()
            populations = pop_counts.index.tolist()
            
            for pop in populations:
                mask = self.features_df['Population'] == pop
                if np.sum(mask) >= 5:  # Only consider populations with at least 5 samples
                    pop_true = self.features_df.loc[mask, 'SEX'].values
                    pop_pred = predictions[mask]
                    pop_accuracy = np.mean(pop_pred == pop_true)
                    print(f"{pop}: {pop_accuracy:.4f} ({pop_accuracy*100:.2f}%) - {np.sum(mask)} samples")
    
    def visualize_predictions(self, output_dir=None):
        """
        Visualize predictions using PCA components
        """
        if self.features_df is None or 'SEX' not in self.features_df.columns:
            print("No feature data or sex labels available for visualization.")
            return
            
        # Create output directory if specified and doesn't exist
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Extract data
        pc_columns = [col for col in self.features_df.columns if col.startswith('PC_')]
        if len(pc_columns) < 2:
            print("Not enough principal components for visualization.")
            return
            
        # Make predictions
        try:
            feature_cols = pc_columns.copy()
            if 'Population_encoded' in self.features_df.columns:
                feature_cols.append('Population_encoded')
                
            X = self.features_df[feature_cols].values
            predictions = self.model.predict(X)
        except ValueError as e:
            if "has" in str(e) and "features" in str(e) and "expecting" in str(e):
                print(f"Error in visualize_predictions: {str(e)}")
                print("Using only PCA components for prediction...")
                
                # Use only PCA components
                X = self.features_df[pc_columns].values
                predictions = self.model.predict(X)
            else:
                raise e
        
        # Add predictions to the dataframe
        self.features_df['Predicted_SEX'] = predictions
        
        # Create a column to indicate correct/incorrect predictions
        self.features_df['Correct'] = self.features_df['SEX'] == self.features_df['Predicted_SEX']
        
        # Create PCA visualization (first two components)
        plt.figure(figsize=(12, 10))
        
        # Define colors and markers
        colors = {1: 'blue', 2: 'red'}
        markers = {True: 'o', False: 'x'}
        
        # Plot each sample
        for sex in [1, 2]:
            for correct in [True, False]:
                mask = (self.features_df['SEX'] == sex) & (self.features_df['Correct'] == correct)
                if np.sum(mask) > 0:
                    plt.scatter(
                        self.features_df.loc[mask, pc_columns[0]],
                        self.features_df.loc[mask, pc_columns[1]],
                        c=colors[sex],
                        marker=markers[correct],
                        alpha=0.7,
                        label=f"{self.sex_labels[sex]} ({'Correct' if correct else 'Incorrect'})"
                    )
        
        plt.xlabel(pc_columns[0])
        plt.ylabel(pc_columns[1])
        plt.title('Sex Classification Results in PCA Space')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if output_dir:
            plt.savefig(os.path.join(output_dir, 'sex_classification_results.png'), dpi=300)
            print(f"Visualization saved to: {os.path.join(output_dir, 'sex_classification_results.png')}")
        else:
            plt.show()


# Check for required files
def check_required_files(model_dir):
    """
    Check for the required files in the specified directory
    """
    required_files = {
        'best_sex_model.pkl': 'Sex classification model'
    }
    
    optional_files = {
        'ensemble_sex_model.pkl': 'Ensemble sex model',
        'sex_features_pca.csv': 'Feature data',
        'sex_predictions.csv': 'Prediction data',
        'sex_selected_snps.csv': 'Selected SNPs list',
        'pca_model.pkl': 'PCA model',
        'feature_selector.pkl': 'Feature selector'
    }
    
    # Check for required files
    for filename, description in required_files.items():
        filepath = os.path.join(model_dir, filename)
        if not os.path.exists(filepath):
            print(f"❌ {description} is missing: {filepath}")
            return False
        else:
            print(f"✓ {description} is present: {filepath}")
    
    # Check for optional files
    for filename, description in optional_files.items():
        filepath = os.path.join(model_dir, filename)
        if not os.path.exists(filepath):
            print(f"ℹ️ {description} is missing: {filepath}")
        else:
            print(f"✓ {description} is present: {filepath}")
    
    return True


# Main function
def main():
    """
    Main function for sex prediction
    """
    print("=== Sex Prediction System from Genetic Data ===\n")
    
    # Set the model directory path - CHANGE THIS TO YOUR LOCAL PATH
    model_dir = './hapmap_data/sex_prediction_data'
    
    if not os.path.exists(model_dir):
        alternative_dirs = [
            'hapmap_data/sex_prediction_data',
            './sex_prediction_data',
            './models'
        ]
        
        for alt_dir in alternative_dirs:
            if os.path.exists(alt_dir):
                model_dir = alt_dir
                print(f"Model directory path has been changed to: {model_dir}")
                break
        else:
            print(f"Error: Model directory not found. Tried multiple paths.")
            print("Please make sure the model directory exists and contains the required files.")
            return
    
    # Check for required files
    if not check_required_files(model_dir):
        print("Some required files are missing. Ensure that the model has been trained first.")
        return
    
    # Load the model and make predictions
    try:
        # File paths
        model_path = os.path.join(model_dir, 'best_sex_model.pkl')
        ensemble_model_path = os.path.join(model_dir, 'ensemble_sex_model.pkl')
        features_path = os.path.join(model_dir, 'sex_features_pca.csv')
        prediction_path = os.path.join(model_dir, 'sex_predictions.csv')
        selected_snps_path = os.path.join(model_dir, 'sex_selected_snps.csv')
        pca_path = os.path.join(model_dir, 'pca_model.pkl')
        selector_path = os.path.join(model_dir, 'feature_selector.pkl')
        
        # Choose the best model available
        chosen_model_path = ensemble_model_path if os.path.exists(ensemble_model_path) else model_path
        chosen_features_path = prediction_path if os.path.exists(prediction_path) else features_path
        
        # Initialize the predictor class
        predictor = SexPredictor(
            model_path=chosen_model_path,
            features_path=chosen_features_path,
            pca_path=pca_path if os.path.exists(pca_path) else None,
            selector_path=selector_path if os.path.exists(selector_path) else None,
            selected_snps_path=selected_snps_path if os.path.exists(selected_snps_path) else None
        )
        
        # Display available samples
        available_ids = predictor.get_available_samples(limit=10)
        
        # Analyze prediction accuracy
        predictor.analyze_prediction_accuracy()
        
        # Test prediction on a sample
        if available_ids:
            print("\n=== Test Prediction ===")
            sample_id = available_ids[0]  # Use the first sample for testing
            predictor.display_sample_prediction(sample_id)
            
            # Visualize predictions
            try:
                predictor.visualize_predictions(output_dir=model_dir)
            except Exception as e:
                print(f"Error during visualization: {str(e)}")
                print("Continuing with predictions...")
            
            # Allow user to input a sample ID for prediction
            while True:
                user_input = input("\nEnter a sample ID to predict (press q to quit): ")
                if user_input.lower() == 'q':
                    break
                predictor.display_sample_prediction(user_input)
        
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    main()