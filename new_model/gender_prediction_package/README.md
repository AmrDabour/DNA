# Gender Prediction from SNP Data

This package contains a pre-trained model for predicting Biological Gender from genetic SNP data.

## Contents

- `best_gender_model.pkl`: The primary trained model
- `ensemble_gender_model.pkl`: Ensemble model for comparison
- `pca_model.pkl`: PCA model for feature transformation
- `selected_indices.pkl`: Indices of selected features
- `gender_selected_snps.csv`: Information about the SNPs used
- `population_encoder.pkl`: Label encoder for population data
- `encoding_function.py`: Function for encoding genetic data
- `metadata.json`: Information about the model and processing
- `predict_gender.py`: Script for making predictions

## Requirements

- Python 3.6+
- pandas
- numpy
- scikit-learn
- joblib

You can install the required packages with:

```bash
pip install pandas numpy scikit-learn joblib
```

## Usage

### Predicting Gender for a Single Sample

```bash
python predict_gender.py --input sample_data.csv --output results.csv
```

### Batch Processing Multiple Samples

```bash
python predict_gender.py --input samples_directory --batch --output batch_results.csv
```

### Input File Format

The input CSV file should contain the following columns:
- `SNP`: SNP identifier
- `Allele1`: First allele
- `Allele2`: Second allele

Optional columns:
- `Patient_ID`: Sample identifier
- `Population`: Population identifier
- `gender`: Known gender (1 for male, 2 for female) used for validation

