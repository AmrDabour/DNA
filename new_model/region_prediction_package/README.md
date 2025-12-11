# Population/Region Prediction from SNP Data

This package contains a pre-trained model for predicting population ancestry from genetic SNP data.

## Contents

- `best_population_model.pkl`: The trained RandomForest classifier
- `pca_model.pkl`: PCA model for feature transformation
- `population_encoder.pkl`: Label encoder for population data
- `selected_snps.csv`: Information about the 50,000 SNPs used
- `scaler_model.pkl`: StandardScaler for normalizing features (may be part of model pipeline)
- `encoding_function.py`: Function for encoding genetic data
- `metadata.json`: Information about the model and processing
- `predict_population.py`: Script for making predictions

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

### Predicting Population for a Single Sample

```bash
python predict_population.py --input sample_data.csv --output results.csv
```

### Batch Processing Multiple Samples

```bash
python predict_population.py --input samples_directory --batch --output batch_results.csv
```

### Input File Format

The input CSV file should contain the following columns:
- `SNP`: SNP identifier
- `Allele1`: First allele
- `Allele2`: Second allele

Optional columns:
- `Patient_ID`: Sample identifier
- `Population`: Known population (used for validation)

## Population Groups

The model can predict the following population groups:
- ASW: African ancestry in Southwest USA
- CEU: Utah residents with Northern and Western European ancestry
- CHB: Han Chinese in Beijing, China
- CHD: Chinese in Metropolitan Denver, Colorado
- GIH: Gujarati Indians in Houston, Texas
- JPT: Japanese in Tokyo, Japan
- LWK: Luhya in Webuye, Kenya
- MEX: Mexican ancestry in Los Angeles, California
- MKK: Maasai in Kinyawa, Kenya
- TSI: Toscani in Italia
- YRI: Yoruba in Ibadan, Nigeria

