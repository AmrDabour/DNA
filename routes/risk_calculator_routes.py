"""
Genetic Risk Calculator Routes - Disease risk assessment and health recommendations
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import current_user, login_required
import os
import pandas as pd
from routes.snp_database_routes import SNP_DATABASE

risk_calculator_bp = Blueprint('risk_calculator', __name__)


# Disease risk factors based on population and gender
DISEASE_RISK_FACTORS = {
    'cardiovascular': {
        'name': 'Cardiovascular Disease',
        'icon': 'heart',
        'color': '#ef4444',
        'base_risk': 15,
        'description': 'Risk of heart disease, stroke, and related conditions',
        'population_modifiers': {
            'CEU': 1.0, 'CHB': 0.85, 'CHD': 0.85, 'GIH': 1.2,
            'JPT': 0.8, 'LWK': 1.1, 'MEX': 1.15, 'MKK': 0.9,
            'TSI': 1.0, 'YRI': 1.0, 'ASW': 1.15
        },
        'gender_modifiers': {'Male': 1.2, 'Female': 0.9},
        'snp_associations': ['rs429358', 'rs7412', 'rs1801133'],
        'recommendations': [
            'Regular cardiovascular exercise (150 min/week)',
            'Mediterranean diet rich in omega-3',
            'Regular blood pressure monitoring',
            'Maintain healthy cholesterol levels',
            'Avoid smoking and excessive alcohol'
        ]
    },
    'type2_diabetes': {
        'name': 'Type 2 Diabetes',
        'icon': 'droplet',
        'color': '#f59e0b',
        'base_risk': 12,
        'description': 'Risk of developing type 2 diabetes mellitus',
        'population_modifiers': {
            'CEU': 1.0, 'CHB': 1.3, 'CHD': 1.25, 'GIH': 1.5,
            'JPT': 1.2, 'LWK': 1.1, 'MEX': 1.4, 'MKK': 0.9,
            'TSI': 1.05, 'YRI': 1.0, 'ASW': 1.3
        },
        'gender_modifiers': {'Male': 1.1, 'Female': 1.0},
        'snp_associations': [],
        'recommendations': [
            'Maintain healthy weight (BMI 18.5-24.9)',
            'Regular blood glucose monitoring',
            'Low glycemic index diet',
            'Regular physical activity',
            'Limit processed foods and sugars'
        ]
    },
    'breast_cancer': {
        'name': 'Breast Cancer',
        'icon': 'ribbon',
        'color': '#ec4899',
        'base_risk': 12.5,
        'description': 'Lifetime risk of developing breast cancer',
        'population_modifiers': {
            'CEU': 1.1, 'CHB': 0.7, 'CHD': 0.7, 'GIH': 0.8,
            'JPT': 0.65, 'LWK': 0.9, 'MEX': 0.85, 'MKK': 0.85,
            'TSI': 1.05, 'YRI': 0.95, 'ASW': 1.0
        },
        'gender_modifiers': {'Male': 0.01, 'Female': 1.0},
        'snp_associations': ['rs6983267'],
        'recommendations': [
            'Regular mammogram screening (age 40+)',
            'Breast self-examination monthly',
            'Maintain healthy weight',
            'Limit alcohol consumption',
            'Consider genetic counseling if family history'
        ]
    },
    'colorectal_cancer': {
        'name': 'Colorectal Cancer',
        'icon': 'circle-radiation',
        'color': '#8b5cf6',
        'base_risk': 4.5,
        'description': 'Lifetime risk of developing colorectal cancer',
        'population_modifiers': {
            'CEU': 1.1, 'CHB': 0.9, 'CHD': 0.9, 'GIH': 0.7,
            'JPT': 1.0, 'LWK': 0.8, 'MEX': 0.85, 'MKK': 0.75,
            'TSI': 1.0, 'YRI': 0.85, 'ASW': 1.05
        },
        'gender_modifiers': {'Male': 1.15, 'Female': 1.0},
        'snp_associations': ['rs6983267'],
        'recommendations': [
            'Colonoscopy screening (age 45+)',
            'High-fiber diet',
            'Limit red and processed meat',
            'Regular physical activity',
            'Maintain healthy weight'
        ]
    },
    'alzheimers': {
        'name': "Alzheimer's Disease",
        'icon': 'brain',
        'color': '#6366f1',
        'base_risk': 10,
        'description': 'Risk of developing late-onset Alzheimer\'s disease',
        'population_modifiers': {
            'CEU': 1.0, 'CHB': 0.8, 'CHD': 0.8, 'GIH': 0.85,
            'JPT': 0.75, 'LWK': 0.9, 'MEX': 0.95, 'MKK': 0.85,
            'TSI': 1.0, 'YRI': 1.1, 'ASW': 1.2
        },
        'gender_modifiers': {'Male': 0.9, 'Female': 1.1},
        'snp_associations': ['rs429358', 'rs7412'],
        'recommendations': [
            'Cognitive stimulation and brain exercises',
            'Regular physical exercise',
            'Mediterranean or MIND diet',
            'Quality sleep (7-8 hours)',
            'Social engagement and activities'
        ]
    },
    'melanoma': {
        'name': 'Melanoma',
        'icon': 'sun',
        'color': '#f97316',
        'base_risk': 2.5,
        'description': 'Risk of developing melanoma skin cancer',
        'population_modifiers': {
            'CEU': 1.5, 'CHB': 0.2, 'CHD': 0.3, 'GIH': 0.3,
            'JPT': 0.2, 'LWK': 0.15, 'MEX': 0.5, 'MKK': 0.15,
            'TSI': 1.2, 'YRI': 0.1, 'ASW': 0.4
        },
        'gender_modifiers': {'Male': 1.1, 'Female': 1.0},
        'snp_associations': ['rs1805007', 'rs1426654', 'rs16891982'],
        'recommendations': [
            'Use SPF 30+ sunscreen daily',
            'Avoid peak sun hours (10am-4pm)',
            'Regular skin self-examination',
            'Annual dermatologist screening',
            'Wear protective clothing and hats'
        ]
    },
    'osteoporosis': {
        'name': 'Osteoporosis',
        'icon': 'bone',
        'color': '#94a3b8',
        'base_risk': 8,
        'description': 'Risk of developing bone density loss',
        'population_modifiers': {
            'CEU': 1.1, 'CHB': 1.0, 'CHD': 1.0, 'GIH': 0.95,
            'JPT': 1.05, 'LWK': 0.7, 'MEX': 0.85, 'MKK': 0.7,
            'TSI': 1.0, 'YRI': 0.65, 'ASW': 0.8
        },
        'gender_modifiers': {'Male': 0.5, 'Female': 1.3},
        'snp_associations': [],
        'recommendations': [
            'Adequate calcium intake (1000-1200mg/day)',
            'Vitamin D supplementation',
            'Weight-bearing exercises',
            'Avoid smoking',
            'DEXA scan screening (age 65+)'
        ]
    },
    'hypertension': {
        'name': 'Hypertension',
        'icon': 'gauge-high',
        'color': '#dc2626',
        'base_risk': 30,
        'description': 'Risk of developing high blood pressure',
        'population_modifiers': {
            'CEU': 1.0, 'CHB': 1.1, 'CHD': 1.1, 'GIH': 1.15,
            'JPT': 1.05, 'LWK': 1.3, 'MEX': 1.1, 'MKK': 1.25,
            'TSI': 1.0, 'YRI': 1.35, 'ASW': 1.4
        },
        'gender_modifiers': {'Male': 1.1, 'Female': 0.95},
        'snp_associations': [],
        'recommendations': [
            'DASH diet (low sodium)',
            'Limit sodium to 2300mg/day',
            'Regular blood pressure monitoring',
            'Maintain healthy weight',
            'Regular aerobic exercise'
        ]
    }
}


@risk_calculator_bp.route('/risk-calculator')
def risk_calculator_page():
    """Genetic Risk Calculator page"""
    return render_template('risk_calculator.html')


def load_patient_data(sample_id):
    """Load SNPs and extract patient info from uploaded file"""
    try:
        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
        file_path = os.path.join(upload_folder, sample_id)
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return {}, None, None
        
        print(f"Reading SNP file: {file_path}")
        df = pd.read_csv(file_path)
        print(f"CSV columns: {df.columns.tolist()}")
        
        # Extract patient metadata (first row)
        gender = None
        population = None
        
        if 'Sex' in df.columns:
            sex_value = df.iloc[0]['Sex']
            # Convert: 1=Male, 2=Female, or string values
            if sex_value == 1 or str(sex_value).lower() in ['male', 'm', '1']:
                gender = 'Male'
            elif sex_value == 2 or str(sex_value).lower() in ['female', 'f', '2']:
                gender = 'Female'
        
        if 'Population' in df.columns:
            population = str(df.iloc[0]['Population']).strip().upper()
        
        print(f"Extracted metadata: Gender={gender}, Population={population}")
        
        # Create dictionary of rs_id -> genotype
        patient_snps = {}
        
        # Format 1: rsid, genotype columns
        if 'rsid' in df.columns and 'genotype' in df.columns:
            for _, row in df.iterrows():
                rs_id = str(row['rsid']).strip()
                genotype = str(row['genotype']).strip()
                patient_snps[rs_id] = genotype
        # Format 2: RS_ID, GENOTYPE columns
        elif 'RS_ID' in df.columns and 'GENOTYPE' in df.columns:
            for _, row in df.iterrows():
                rs_id = str(row['RS_ID']).strip()
                genotype = str(row['GENOTYPE']).strip()
                patient_snps[rs_id] = genotype
        # Format 3: SNP, Allele1, Allele2 columns (HapMap format)
        elif 'SNP' in df.columns and 'Allele1' in df.columns and 'Allele2' in df.columns:
            for _, row in df.iterrows():
                rs_id = str(row['SNP']).strip()
                allele1 = str(row['Allele1']).strip()
                allele2 = str(row['Allele2']).strip()
                genotype = allele1 + allele2
                patient_snps[rs_id] = genotype
        else:
            print(f"Unsupported CSV format. Available columns: {df.columns.tolist()}")
        
        print(f"Loaded {len(patient_snps)} SNPs from patient file")
        if len(patient_snps) > 0:
            sample_snps = list(patient_snps.items())[:3]
            print(f"Sample SNPs: {sample_snps}")
        
        return patient_snps, gender, population
    except Exception as e:
        print(f"Error loading patient data: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}, None, None


def calculate_snp_risk_score(patient_snps, disease_name):
    """Calculate risk score based on actual SNP genotypes"""
    matched_snps = []
    risk_score_modifier = 1.0
    
    # Normalize disease name for matching (handle different naming conventions)
    disease_name_lower = disease_name.lower()
    
    for rs_id, snp_info in SNP_DATABASE.items():
        if rs_id in patient_snps:
            disease_assoc = snp_info.get('disease_associations', [])
            
            # Check if this SNP is associated with the disease (case-insensitive)
            # Support partial matching (e.g., "cardiovascular" in "Cardiovascular Disease")
            if any(disease_name_lower in assoc.lower() or assoc.lower() in disease_name_lower for assoc in disease_assoc):
                patient_genotype = patient_snps[rs_id]
                risk_allele = snp_info.get('risk_allele', '')
                odds_ratio = snp_info.get('odds_ratio', 1.0)
                
                if odds_ratio:
                    # Count risk alleles in genotype
                    risk_allele_count = patient_genotype.count(risk_allele) if risk_allele else 0
                    
                    # Apply odds ratio based on number of risk alleles
                    if risk_allele_count == 2:  # Homozygous risk
                        risk_score_modifier *= odds_ratio
                    elif risk_allele_count == 1:  # Heterozygous
                        risk_score_modifier *= (1 + (odds_ratio - 1) * 0.5)
                    
                    matched_snps.append({
                        'rs_id': rs_id,
                        'gene': snp_info.get('gene_symbol', 'Unknown'),
                        'genotype': patient_genotype,
                        'risk_allele': risk_allele,
                        'odds_ratio': odds_ratio,
                        'risk_allele_count': risk_allele_count
                    })
    
    return matched_snps, risk_score_modifier


@risk_calculator_bp.route('/api/risk/calculate', methods=['POST'])
def calculate_risk():
    """Calculate genetic risk scores based on actual SNP data"""
    data = request.get_json()
    
    print(f"=== Risk Calculation Request ===")
    print(f"Received data: {data}")
    
    sample_id = data.get('sample_id', '')
    age = data.get('age')
    selected_diseases = data.get('diseases', [])
    
    if not sample_id:
        return jsonify({
            'success': False,
            'error': 'SNP file is required'
        }), 400
    
    # Load patient SNPs and extract metadata from file
    patient_snps, gender, population_code = load_patient_data(sample_id)
    
    if not patient_snps:
        return jsonify({
            'success': False,
            'error': 'Could not load SNP data from file'
        }), 400
    
    print(f"Auto-detected: Gender={gender}, Population={population_code}, Age={age}")
    print(f"Selected diseases: {selected_diseases}")
    
    results = {
        'overall_score': 0,
        'diseases': [],  # Changed from 'risks' to 'diseases' to match frontend
        'protective_factors': [],
        'high_risks': [],
        'moderate_risks': [],
        'low_risks': []
    }
    
    total_risk = 0
    risk_count = 0
    
    # Always process all diseases (auto-selected in background)
    print(f"Processing all {len(DISEASE_RISK_FACTORS)} diseases")
    diseases_to_process = list(DISEASE_RISK_FACTORS.items())
    
    for disease_id, disease in diseases_to_process:
        # Calculate base risk
        base_risk = disease['base_risk']
        
        # Apply population modifier
        pop_modifier = disease['population_modifiers'].get(population_code, 1.0)
        
        # Apply gender modifier
        gender_modifier = disease['gender_modifiers'].get(gender, 1.0)
        
        # Calculate population-based risk
        risk_score = base_risk * pop_modifier * gender_modifier
        
        # Apply SNP-based risk modification if patient data available
        matched_snps = []
        snp_modifier = 1.0
        if patient_snps:
            matched_snps, snp_modifier = calculate_snp_risk_score(patient_snps, disease['name'])
            if len(matched_snps) > 0:
                print(f"{disease['name']}: {len(matched_snps)} SNPs matched, modifier = {snp_modifier:.3f}")
                risk_score *= snp_modifier
            else:
                print(f"{disease['name']}: No SNPs matched in database")
        
        # Apply age multiplier (slight increase for age-related conditions)
        age_modifier = 1.0
        if age:
            # Age-related diseases get higher multiplier
            age_related_diseases = ['alzheimers', 'cardiovascular', 'osteoporosis', 'macular_degeneration', 
                                   'parkinsons', 'prostate_cancer', 'breast_cancer']
            
            if disease_id in age_related_diseases:
                # Increase risk by 0.5% per year after age 40
                if age > 40:
                    age_modifier = 1.0 + ((age - 40) * 0.005)
                    age_modifier = min(age_modifier, 1.3)  # Cap at 30% increase
                    risk_score *= age_modifier
                    print(f"  Age modifier ({age} years): {age_modifier:.3f}")
        
        # Cap at reasonable limits
        risk_score = min(risk_score, 95)
        risk_score = max(risk_score, 0.1)
        risk_score = round(risk_score, 1)
        
        # Determine risk level
        if risk_score >= 20:
            risk_level = 'high'
            results['high_risks'].append(disease['name'])
        elif risk_score >= 10:
            risk_level = 'moderate'
            results['moderate_risks'].append(disease['name'])
        else:
            risk_level = 'low'
            results['low_risks'].append(disease['name'])
        
        risk_data = {
            'id': disease_id,
            'name': disease['name'],
            'icon': disease['icon'],
            'color': disease['color'],
            'risk_score': risk_score,
            'risk_level': risk_level,
            'description': disease['description'],
            'recommendations': disease['recommendations'],
            'population': population_code or 'Unknown',
            'gender': gender or 'Unknown',
            'age': age,
            'population_effect': 'increased' if pop_modifier > 1 else 'decreased' if pop_modifier < 1 else 'average',
            'population_modifier': round((pop_modifier - 1) * 100, 1),
            'snps_analyzed': len(matched_snps),
            'matched_snps': matched_snps[:5] if matched_snps else [],  # Top 5 SNPs
            'snp_impact': round((snp_modifier - 1) * 100, 1) if snp_modifier != 1.0 else 0,
            'age_impact': round((age_modifier - 1) * 100, 1) if age_modifier != 1.0 else 0
        }
        
        results['diseases'].append(risk_data)
        total_risk += risk_score
        risk_count += 1
    
    # Calculate overall score (inverted - lower risk = higher health score)
    avg_risk = total_risk / risk_count if risk_count > 0 else 0
    results['overall_score'] = round(100 - avg_risk, 1)
    results['average_risk'] = round(avg_risk, 1)
    
    # Sort risks by score
    results['diseases'].sort(key=lambda x: x['risk_score'], reverse=True)
    
    # Add recommendations array for frontend
    results['recommendations'] = []
    if len(results['high_risks']) > 0:
        results['recommendations'].append({
            'type': 'screening',
            'title': 'Regular Health Screening',
            'description': f'Consider regular screening for high-risk conditions: {", ".join(results["high_risks"][:3])}'
        })
    
    # Generate protective factors based on low risks
    if len(results['low_risks']) > 0:
        results['protective_factors'] = [
            f'Lower than average risk for {len(results["low_risks"])} conditions',
            f'Population ancestry provides some protective factors'
        ]
    
    return jsonify({
        'success': True,
        'results': results,
        'patient_info': {
            'gender': gender,
            'population': population_code,
            'age': age,
            'snp_count': len(patient_snps)
        }
    })


@risk_calculator_bp.route('/api/risk/recommendations', methods=['POST'])
def get_recommendations():
    """Get personalized health recommendations"""
    data = request.get_json()
    
    gender = data.get('gender', 'Unknown')
    population_code = data.get('population_code', '')
    age = data.get('age', 30)
    
    recommendations = {
        'screenings': [],
        'lifestyle': [],
        'diet': [],
        'monitoring': []
    }
    
    # Age-based screening recommendations
    if age >= 40:
        recommendations['screenings'].append({
            'name': 'Blood Pressure Check',
            'frequency': 'Annually',
            'icon': 'heart-pulse'
        })
        recommendations['screenings'].append({
            'name': 'Cholesterol Panel',
            'frequency': 'Every 4-6 years',
            'icon': 'droplet'
        })
    
    if age >= 45:
        recommendations['screenings'].append({
            'name': 'Colorectal Cancer Screening',
            'frequency': 'Every 10 years (colonoscopy)',
            'icon': 'stethoscope'
        })
    
    if gender == 'Female':
        if age >= 21:
            recommendations['screenings'].append({
                'name': 'Pap Smear',
                'frequency': 'Every 3 years',
                'icon': 'user-nurse'
            })
        if age >= 40:
            recommendations['screenings'].append({
                'name': 'Mammogram',
                'frequency': 'Annually',
                'icon': 'x-ray'
            })
    
    if gender == 'Male' and age >= 50:
        recommendations['screenings'].append({
            'name': 'Prostate Screening',
            'frequency': 'Discuss with doctor',
            'icon': 'user-doctor'
        })
    
    # Population-specific recommendations
    pop_recommendations = {
        'GIH': 'Consider diabetes screening earlier due to elevated population risk',
        'YRI': 'Regular blood pressure monitoring recommended',
        'ASW': 'Cardiovascular health monitoring recommended',
        'CEU': 'Sun protection for skin cancer prevention',
        'JPT': 'Stomach cancer screening if family history',
        'CHB': 'Hepatitis B screening recommended',
        'MEX': 'Diabetes and cardiovascular screening important'
    }
    
    if population_code in pop_recommendations:
        recommendations['monitoring'].append({
            'name': pop_recommendations[population_code],
            'icon': 'notes-medical'
        })
    
    # General lifestyle recommendations
    recommendations['lifestyle'] = [
        {'name': '150+ minutes of moderate exercise weekly', 'icon': 'person-running'},
        {'name': '7-8 hours of quality sleep', 'icon': 'bed'},
        {'name': 'Stress management and relaxation', 'icon': 'spa'},
        {'name': 'Regular social engagement', 'icon': 'users'}
    ]
    
    # Diet recommendations
    recommendations['diet'] = [
        {'name': 'Mediterranean or plant-based diet', 'icon': 'leaf'},
        {'name': 'Limit processed foods and sugars', 'icon': 'ban'},
        {'name': 'Adequate hydration (8 glasses/day)', 'icon': 'glass-water'},
        {'name': 'Moderate alcohol if any', 'icon': 'wine-glass'}
    ]
    
    return jsonify({
        'success': True,
        'recommendations': recommendations
    })


@risk_calculator_bp.route('/api/risk/diseases')
def get_disease_list():
    """Get list of all diseases in the risk calculator"""
    diseases = []
    for disease_id, disease in DISEASE_RISK_FACTORS.items():
        diseases.append({
            'id': disease_id,
            'name': disease['name'],
            'icon': disease['icon'],
            'color': disease['color'],
            'description': disease['description']
        })
    
    return jsonify({
        'success': True,
        'diseases': diseases
    })
