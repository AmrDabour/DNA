# Risk Calculator - Simplified Version

## What Changed

### ✅ Removed Manual Inputs:
- ❌ **Gender dropdown** - Now auto-extracted from SNP file
- ❌ **Population dropdown** - Now auto-extracted from SNP file  
- ❌ **Sample selection** - Only file upload

### ✅ Kept Only:
- ✅ **SNP File Upload** - Primary input (drag & drop or click)
- ✅ **Age Input** (Optional) - Used as accuracy multiplier
- ✅ **Disease Selection** - Choose which conditions to assess

## How It Works Now

### 1. Upload SNP File
User uploads CSV file containing:
- `SNP` column - RS IDs
- `Allele1`, `Allele2` - Genotypes
- `Sex` column - Auto-detected (1=Male, 2=Female)
- `Population` column - Auto-detected (CEU, GIH, etc.)

### 2. Automatic Extraction
Backend automatically extracts from file:
```python
gender = df['Sex'][0]  # 1=Male, 2=Female
population = df['Population'][0]  # CEU, GIH, CHB, etc.
snps = {rs_id: genotype}  # All patient SNPs
```

### 3. Age Multiplier (Optional)
If age is provided:
- **Age-related diseases** get increased risk
- Formula: `1.0 + ((age - 40) * 0.005)` for age > 40
- **Maximum:** +30% increase (age 100)
- **Example:** 60 years old = +10% risk for Alzheimer's

**Age-Related Diseases:**
- Alzheimer's Disease
- Cardiovascular Disease
- Osteoporosis
- Macular Degeneration
- Parkinson's Disease
- Prostate Cancer
- Breast Cancer

### 4. Risk Calculation
```python
Final Risk = Base Risk × Population Modifier × Gender Modifier × SNP Modifier × Age Modifier
```

**Example:**
- Base Risk: 10% (Alzheimer's)
- Population (GIH): ×1.1
- Gender (Male): ×0.9
- SNP (rs1801133): ×1.5 (matched, 2 risk alleles)
- Age (65): ×1.125 (25 years over 40)

**Result:** 10% × 1.1 × 0.9 × 1.5 × 1.125 = **16.7% risk**

## Frontend Changes

### Before:
```html
<select id="patient-gender">...</select>
<select id="patient-population">...</select>
<select id="sample-select">...</select>
```

### After:
```html
<input type="file" />
<input type="number" id="patient-age" placeholder="Age" />
```

### Auto-Display Patient Info:
After upload, shows extracted data:
```
👤 Male | 🌍 GIH | 🧬 50,000 SNPs
```

## Backend Changes

### New Function: `load_patient_data()`
Returns:
1. `patient_snps` - Dictionary of RS IDs → Genotypes
2. `gender` - Extracted from Sex column
3. `population` - Extracted from Population column

### Age Modifier Logic:
```python
if age > 40 and disease is age_related:
    age_modifier = 1.0 + ((age - 40) * 0.005)
    age_modifier = min(age_modifier, 1.3)  # Cap at 30%
    risk_score *= age_modifier
```

## API Changes

### Request (Simplified):
```json
{
  "sample_id": "NA20805_GIH_Male.csv",
  "age": 65,
  "diseases": ["cardiovascular", "alzheimers"]
}
```

### Response (Enhanced):
```json
{
  "success": true,
  "patient_info": {
    "gender": "Male",
    "population": "GIH",
    "age": 65,
    "snp_count": 50000
  },
  "results": {
    "diseases": [{
      "name": "Alzheimer's Disease",
      "risk_score": 16.7,
      "snps_analyzed": 1,
      "snp_impact": 50,
      "age_impact": 12.5,
      "gender": "Male",
      "population": "GIH"
    }]
  }
}
```

## User Experience

### Simple 3-Step Process:
1. **Upload** SNP file (drag & drop)
2. **Enter** age (optional)
3. **Calculate** risk

### Auto-Detected Info Shown:
- Gender icon and label
- Population code and name
- Total SNP count in file

### Results Show:
- Only diseases with matched SNPs
- SNP impact percentage
- Age impact percentage (if age provided)
- Patient metadata (gender, population)

## Benefits

✅ **Simpler** - No manual data entry  
✅ **Faster** - One file, one click  
✅ **Accurate** - No user input errors  
✅ **Transparent** - Shows what was extracted  
✅ **Flexible** - Age is optional but useful  

## Age Impact Examples

| Age | Years Over 40 | Age Modifier | Risk Increase |
|-----|---------------|--------------|---------------|
| 35  | 0             | 1.000        | 0%            |
| 40  | 0             | 1.000        | 0%            |
| 50  | 10            | 1.050        | +5%           |
| 60  | 20            | 1.100        | +10%          |
| 70  | 30            | 1.150        | +15%          |
| 80  | 40            | 1.200        | +20%          |
| 100 | 60            | 1.300        | +30% (max)    |

**Note:** Age modifier only applies to age-related conditions, not all diseases.

## Testing

Upload files with different parameters:
- **NA20805_GIH_Male.csv** - South Asian Male
- **NA12753_CEU_Female.csv** - European Female
- **NA18524_CHB_Male.csv** - East Asian Male

Try with/without age to see the difference in risk scores!




