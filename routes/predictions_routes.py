"""
Predictions Routes - API endpoints for AI predictions and prediction result pages
"""
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, current_app
from flask_login import current_user
import pandas as pd
import os
import json
import google.generativeai as genai
from . import predictions_bp
from .samples_routes import POPULATION_INFO, resolve_population_code
from database.models import db, AnalysisHistory
from sqlalchemy import or_

# Import utilities
try:
    from utils import convert_to_serializable
    from services import get_physical_characteristics, get_genetic_disease_risk, get_ai_health_guidance
except ImportError:
    # Fallback if not available
    def convert_to_serializable(obj):
        import numpy as np
        if isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    get_physical_characteristics = None
    get_genetic_disease_risk = None
    get_ai_health_guidance = None

# Create page blueprint (no prefix for page routes)
predictions_page_bp = Blueprint('predictions_pages', __name__)


def get_api_config():
    """Get Gemini API configuration"""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY")
    model_name = os.environ.get("AGENT_MODEL", "gemini-2.5-flash")
    return api_key, model_name


@predictions_bp.route('/physical', methods=['POST'])
def predict_physical_characteristics():
    """
    Predict physical characteristics based on gender and population
    ---
    tags:
      - Predictions
    """
    data = request.json
    gender = data.get("gender")
    population = data.get("population")
    
    if not gender or not population:
        return jsonify({"success": False, "error": "Missing gender or population"})
    
    api_key, model_name = get_api_config()
    if not api_key:
        return jsonify({"success": False, "error": "Gemini API key not configured"})
    
    try:
        pop_description = POPULATION_INFO.get(population.upper(), {}).get("description", population)
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        
        prompt = f"""Describe physical characteristics for: {gender}, {population} population ({pop_description}).

Provide in this exact markdown format:

## 🧬 Physical Characteristics Prediction

**Profile:** {gender} | {population} ({pop_description})

---

### 💇 Hair
- **Color:** Common colors for this population
- **Texture:** Typical textures

### 👁️ Eyes
- **Color:** Common eye colors
- **Shape:** Typical eye shapes

### 🎨 Skin
- **Tone:** Common skin tones

### 👤 Facial Features
- **Nose:** Typical characteristics
- **Lips:** Typical characteristics
- **Face Shape:** Common shapes
- **Cheekbones:** Typical characteristics

### 🏃 Body Structure
- **Height:** Typical range
- **Build:** Common body types
- **Frame:** Typical frame

### ✨ Other Distinctive Traits
- List any other notable characteristics

---

⚠️ **Note:** These are statistical predictions based on population genetics. Individual variation is significant.

Be scientifically accurate and avoid stereotypes."""

        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "formatted_result": response.text,
            "gender": gender,
            "population": population
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@predictions_bp.route('/disease-risk', methods=['POST'])
def assess_disease_risk():
    """
    Assess genetic disease risk based on gender and population
    ---
    tags:
      - Predictions
    """
    data = request.json
    gender = data.get("gender")
    population = data.get("population")
    patient_id = data.get("patient_id", "Unknown")
    
    if not gender or not population:
        return jsonify({"success": False, "error": "Missing gender or population"})
    
    api_key, model_name = get_api_config()
    if not api_key:
        return jsonify({"success": False, "error": "Gemini API key not configured"})
    
    try:
        pop_description = POPULATION_INFO.get(population.upper(), {}).get("description", population)
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        
        prompt = f"""List 5 genetic disease risks for: {gender}, {population} population ({pop_description}).

Provide a detailed assessment in this exact markdown format:

## 🏥 Genetic Disease Risk Assessment

**Patient:** {patient_id}
**Profile:** {gender} | {population} ({pop_description})

---

### 1. [Disease Name] 🔴/🟡/🟢
**Risk Level:** High/Moderate/Low
**Affected Genes:** GENE1, GENE2
**Description:** Brief description of the disease
**Prevalence:** X% in this population
**Recommendations:**
- Recommendation 1
- Recommendation 2

### 2. [Next Disease]
... (continue for 5 diseases)

---

⚠️ **Medical Disclaimer:** This is for informational purposes only. Consult a healthcare provider for personalized advice.

Use real diseases with actual genetic links to the {population} population. Be scientifically accurate."""

        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "formatted_result": response.text,
            "gender": gender,
            "population": population,
            "patient_id": patient_id
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@predictions_bp.route('/physical/from-sample', methods=['POST'])
def predict_physical_from_sample():
    """
    Predict physical characteristics from a sample file
    ---
    tags:
      - Predictions
    """
    data = request.json
    sample_file = data.get("sample_file")
    
    if not sample_file or not os.path.exists(sample_file):
        return jsonify({"success": False, "error": f"Sample file not found: {sample_file}"})
    
    try:
        df = pd.read_csv(sample_file, nrows=1)
        
        patient_id = df['Patient_ID'].iloc[0] if 'Patient_ID' in df.columns else "Unknown"
        
        # Check for gender/sex column (different CSV formats use different names)
        gender = "Unknown"
        sex_code = None
        if 'gender' in df.columns:
            sex_code = df['gender'].iloc[0]
        elif 'Sex' in df.columns:
            sex_code = df['Sex'].iloc[0]
        elif 'sex' in df.columns:
            sex_code = df['sex'].iloc[0]
        if sex_code is not None:
            gender = "Male" if sex_code == 1 else "Female" if sex_code == 2 else "Unknown"
        
        population = "Unknown"
        if 'Population' in df.columns:
            population = str(df['Population'].iloc[0])
        elif 'population' in df.columns:
            population = str(df['population'].iloc[0])
        
        if gender == "Unknown" or population == "Unknown":
            return jsonify({"success": False, "error": f"Could not determine gender ({gender}) or population ({population})"})
        
        # Call the main prediction endpoint logic
        api_key, model_name = get_api_config()
        if not api_key:
            return jsonify({"success": False, "error": "Gemini API key not configured"})
        
        pop_description = POPULATION_INFO.get(population.upper(), {}).get("description", population)
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        
        prompt = f"""Describe physical characteristics for: {gender}, {population} population ({pop_description}).

## 🧬 Physical Characteristics Prediction

**Patient:** {patient_id}
**Profile:** {gender} | {population} ({pop_description})

---

### 💇 Hair
- **Color:** Common colors
- **Texture:** Typical textures

### 👁️ Eyes
- **Color:** Common colors
- **Shape:** Typical shapes

### 🎨 Skin
- **Tone:** Common tones

### 👤 Facial Features
- Key features

### 🏃 Body Structure
- **Height:** Range
- **Build:** Type
- **Frame:** Size

---

⚠️ **Note:** Statistical predictions based on population genetics.

Be brief and scientifically accurate."""

        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "formatted_result": response.text,
            "sample_info": {
                "patient_id": str(patient_id),
                "gender": gender,
                "population": population,
                "file": sample_file
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@predictions_bp.route('/generate-person-image', methods=['POST'])
def generate_person_image():
    """
    Generate an AI image of a person based on Predicted Gender and ancestry
    Uses Google Gemini Image Generation API (gemini-2.5-flash-image model)
    ---
    tags:
      - Predictions
    """
    import base64
    from google import genai as genai_new
    
    data = request.json
    gender = data.get("gender")
    population = data.get("population")
    patient_id = data.get("patient_id", "Unknown")
    
    if not gender or not population:
        return jsonify({"success": False, "error": "Missing gender or population"})
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY")
    if not api_key:
        return jsonify({"success": False, "error": "Gemini API key not configured"})
    
    try:
        pop_description = POPULATION_INFO.get(population.upper(), {}).get("description", population)
        
        # Determine gender description
        gender = "man" if gender.lower() == "male" else "woman" if gender.lower() == "female" else "person"
        
        # Build detailed prompt based on ancestry and gender
        prompt = f"""Generate a realistic portrait photograph of an adult {gender} with typical {pop_description} ancestry features.

Physical characteristics to include:
- Natural skin tone typical of {pop_description} population
- Appropriate facial features for this ethnic background
- Age: adult (25-40 years old)
- Expression: neutral, natural, friendly
- Lighting: soft, professional studio lighting
- Background: simple, light colored background
- Style: professional headshot portrait photograph
- High quality, photorealistic image

The person should look natural and authentic, representing typical physical characteristics of someone from the {pop_description} ethnic background."""

        # Initialize client with new genai library
        client = genai_new.Client(api_key=api_key)
        
        # Generate image using gemini-2.5-flash-image model (same as test file)
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
        )
        
        # Process response to extract image
        image_data = None
        response_text = None
        
        for part in response.parts:
            if part.text is not None:
                response_text = part.text
            elif part.inline_data is not None:
                # Use as_image() method like in the working test file
                image = part.as_image()
                
                # Save image to uploads folder
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"{patient_id}_generated_portrait_{timestamp}.png"
                image_path = os.path.join("uploads", image_filename)
                
                # Save the image using PIL
                image.save(image_path)
                
                # Read the saved file and convert to base64 for frontend
                with open(image_path, "rb") as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        if image_data:
            base64_uri = f"data:image/png;base64,{image_data}"
            
            # Save image path to database (filter by user for proper ownership)
            if patient_id and patient_id != "Unknown":
                try:
                    print(f"🔍 Looking for analysis with sample_id={patient_id}")
                    # Build query with user filter for proper ownership
                    query = AnalysisHistory.query.filter_by(sample_id=patient_id)
                    if current_user.is_authenticated:
                        print(f"🔍 User is authenticated: user_id={current_user.id}")
                        # For logged-in users, only update their own analyses or unassigned ones
                        query = query.filter(
                            or_(AnalysisHistory.user_id == current_user.id, AnalysisHistory.user_id == None)
                        )
                    else:
                        print(f"🔍 User is NOT authenticated")
                    analysis = query.order_by(AnalysisHistory.created_at.desc()).first()
                    if analysis:
                        # Store image path in full_results
                        full_results = analysis.get_full_results() or {}
                        full_results['generated_image_path'] = image_path
                        full_results['generated_image_description'] = response_text or f"Generated portrait for {gender} with {pop_description} ancestry"
                        analysis.set_full_results(full_results)
                        db.session.commit()
                        print(f"✅ Generated image path saved for {patient_id} (analysis_id={analysis.id})")
                        print(f"   📁 Path stored: {image_path}")
                        print(f"   📁 File exists: {os.path.exists(image_path)}")
                    else:
                        print(f"⚠️ No analysis found for sample_id={patient_id}")
                        # Try to find any analysis with similar sample_id
                        all_analyses = AnalysisHistory.query.filter(
                            AnalysisHistory.sample_id.like(f"%{patient_id}%")
                        ).limit(5).all()
                        if all_analyses:
                            print(f"📋 Similar sample_ids found: {[a.sample_id for a in all_analyses]}")
                except Exception as db_err:
                    print(f"❌ Error saving image path: {db_err}")
                    import traceback
                    traceback.print_exc()
            
            return jsonify({
                "success": True,
                "image_data": base64_uri,
                "image_path": image_path,
                "description": response_text or f"Generated portrait for {gender} with {pop_description} ancestry",
                "patient_id": patient_id,
                "gender": gender,
                "population": population,
                "formatted_result": f"🖼️ **Generated Portrait**\n\n![Generated Portrait]({base64_uri})\n\n**Patient:** {patient_id}\n**Gender:** {gender}\n**Ancestry:** {pop_description}"
            })
        else:
            return jsonify({
                "success": False, 
                "error": "No image was generated. The model may have returned text only.",
                "response_text": response_text
            })
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc()
        })


@predictions_bp.route('/disease-risk/from-sample', methods=['POST'])
def assess_disease_risk_from_sample():
    """
    Assess disease risk from a sample file
    ---
    tags:
      - Predictions
    """
    data = request.json
    sample_file = data.get("sample_file")
    
    if not sample_file or not os.path.exists(sample_file):
        return jsonify({"success": False, "error": f"Sample file not found: {sample_file}"})
    
    try:
        df = pd.read_csv(sample_file, nrows=1)
        
        patient_id = df['Patient_ID'].iloc[0] if 'Patient_ID' in df.columns else "Unknown"
        
        # Check for gender/sex column (different CSV formats use different names)
        gender = "Unknown"
        sex_code = None
        if 'gender' in df.columns:
            sex_code = df['gender'].iloc[0]
        elif 'Sex' in df.columns:
            sex_code = df['Sex'].iloc[0]
        elif 'sex' in df.columns:
            sex_code = df['sex'].iloc[0]
        if sex_code is not None:
            gender = "Male" if sex_code == 1 else "Female" if sex_code == 2 else "Unknown"
        
        population = "Unknown"
        if 'Population' in df.columns:
            population = str(df['Population'].iloc[0])
        elif 'population' in df.columns:
            population = str(df['population'].iloc[0])
        
        if gender == "Unknown" or population == "Unknown":
            return jsonify({"success": False, "error": f"Could not determine gender ({gender}) or population ({population})"})
        
        api_key, model_name = get_api_config()
        if not api_key:
            return jsonify({"success": False, "error": "Gemini API key not configured"})
        
        pop_description = POPULATION_INFO.get(population.upper(), {}).get("description", population)
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        
        prompt = f"""List 5 genetic disease risks for: {gender}, {population} population ({pop_description}).

## 🏥 Genetic Disease Risk Assessment

**Patient:** {patient_id}
**Profile:** {gender} | {population} ({pop_description})

---

### 1. [Disease Name] 🔴/🟡/🟢
**Risk Level:** High/Moderate/Low
**Affected Genes:** GENE1, GENE2
**Description:** Brief description
**Prevalence:** X% in population
**Recommendations:**
- Recommendation 1
- Recommendation 2

(Continue for 5 diseases)

---

⚠️ **Medical Disclaimer:** Consult a healthcare provider.

Use real diseases with genetic links. Be accurate."""

        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "formatted_result": response.text,
            "sample_info": {
                "patient_id": str(patient_id),
                "gender": gender,
                "population": population,
                "file": sample_file
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@predictions_bp.route('/full-report', methods=['POST'])
def full_genetic_report():
    """
    Generate a complete genetic report from a sample file
    ---
    tags:
      - Predictions
    """
    data = request.json
    sample_file = data.get("sample_file")
    
    if not sample_file or not os.path.exists(sample_file):
        return jsonify({"success": False, "error": f"Sample file not found: {sample_file}"})
    
    api_key, model_name = get_api_config()
    
    try:
        df = pd.read_csv(sample_file)
        
        patient_id = df['Patient_ID'].iloc[0] if 'Patient_ID' in df.columns else "Unknown"
        total_snps = len(df)
        
        # Check for gender/sex column (different CSV formats use different names)
        gender = "Unknown"
        sex_code = None
        if 'gender' in df.columns:
            sex_code = df['gender'].iloc[0]
        elif 'Sex' in df.columns:
            sex_code = df['Sex'].iloc[0]
        elif 'sex' in df.columns:
            sex_code = df['sex'].iloc[0]
        if sex_code is not None:
            gender = "Male" if sex_code == 1 else "Female" if sex_code == 2 else "Unknown"
        
        population = "Unknown"
        if 'Population' in df.columns:
            population = str(df['Population'].iloc[0])
        elif 'population' in df.columns:
            population = str(df['population'].iloc[0])
        
        pop_description = POPULATION_INFO.get(population.upper(), {}).get("description", population)
        
        # Calculate statistics
        heterozygosity_rate = 0
        homozygous_count = 0
        heterozygous_count = 0
        allele_freqs = {}
        
        if 'Allele1' in df.columns and 'Allele2' in df.columns:
            df['is_hetero'] = df['Allele1'] != df['Allele2']
            heterozygosity_rate = round(df['is_hetero'].mean() * 100, 2)
            homozygous_count = int((~df['is_hetero']).sum())
            heterozygous_count = int(df['is_hetero'].sum())
            
            allele_counts = df['Allele1'].value_counts().to_dict()
            for allele, count in df['Allele2'].value_counts().items():
                allele_counts[allele] = allele_counts.get(allele, 0) + count
            allele_counts = {k: v for k, v in allele_counts.items() if k != '0' and k != 0}
            total_alleles = sum(allele_counts.values())
            if total_alleles > 0:
                allele_freqs = {k: round(v/total_alleles*100, 2) for k, v in sorted(allele_counts.items(), key=lambda x: -x[1])}
        
        # Build report
        report = f"""## 🧬 Complete Genetic Report for {patient_id}

### 📋 Sample Information
- **Patient ID:** {patient_id}
- **File:** {sample_file}
- **Total SNPs:** {total_snps:,}
- **Gender:** {gender} {'♂️' if gender == 'Male' else '♀️' if gender == 'Female' else ''}
- **Population:** {population}
- **Population Description:** {pop_description}

### 📊 Genetic Statistics
- **Heterozygosity Rate:** {heterozygosity_rate}%
- **Homozygous SNPs:** {homozygous_count:,}
- **Heterozygous SNPs:** {heterozygous_count:,}

### 🔬 Allele Frequencies
"""
        for allele, freq in list(allele_freqs.items())[:6]:
            report += f"- **{allele}:** {freq}%\n"
        
        # Add AI predictions if available
        if gender != "Unknown" and population != "Unknown" and api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name=model_name)
                
                phys_prompt = f"""For a {gender} from {population} ({pop_description}), list typical physical characteristics briefly:
- Hair: color, texture
- Eyes: color, shape
- Skin: tone
- Facial Features: key traits
- Body: height, build"""

                phys_response = model.generate_content(phys_prompt)
                report += f"\n---\n\n## 🎨 Physical Characteristics\n\n{phys_response.text}\n"
                
                disease_prompt = f"""List 4 genetic disease risks for {gender}, {population} population briefly:
For each: Disease Name (🔴/🟡/🟢), Risk Level, Genes, Prevalence, Recommendation"""

                disease_response = model.generate_content(disease_prompt)
                report += f"\n---\n\n## 🏥 Disease Risk Assessment\n\n{disease_response.text}\n"
                
            except Exception as e:
                report += f"\n---\n\n⚠️ Could not generate AI predictions: {str(e)}\n"
        
        report += """
---

⚠️ **Disclaimer:** This report is for informational purposes only. Consult a healthcare provider for medical advice.
"""
        
        return jsonify({
            "success": True,
            "formatted_result": report,
            "patient_id": str(patient_id),
            "gender": gender,
            "population": population
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ============================================================
# New Fun & Educational Endpoints
# ============================================================

@predictions_bp.route('/generate-image-from-sample', methods=['POST'])
def generate_image_from_sample():
    """
    Generate AI portrait from a sample file
    ---
    tags:
      - Predictions
    """
    import base64
    from google import genai as genai_new
    
    data = request.json
    sample_file = data.get("sample_file")
    
    if not sample_file or not os.path.exists(sample_file):
        return jsonify({"success": False, "error": f"Sample file not found: {sample_file}"})
    
    try:
        df = pd.read_csv(sample_file, nrows=1)
        
        patient_id = df['Patient_ID'].iloc[0] if 'Patient_ID' in df.columns else "Unknown"
        
        # Check for gender/sex column (different CSV formats use different names)
        gender = "Unknown"
        sex_code = None
        if 'gender' in df.columns:
            sex_code = df['gender'].iloc[0]
        elif 'Sex' in df.columns:
            sex_code = df['Sex'].iloc[0]
        elif 'sex' in df.columns:
            sex_code = df['sex'].iloc[0]
        
        if sex_code is not None:
            gender = "Male" if sex_code == 1 else "Female" if sex_code == 2 else "Unknown"
        
        population = "Unknown"
        if 'Population' in df.columns:
            population = str(df['Population'].iloc[0])
        elif 'population' in df.columns:
            population = str(df['population'].iloc[0])
        
        if gender == "Unknown" or population == "Unknown":
            return jsonify({"success": False, "error": f"Could not determine gender ({gender}) or population ({population}). Available columns: {list(df.columns)}"})
        
        # Get API key
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY")
        if not api_key:
            return jsonify({"success": False, "error": "Gemini API key not configured"})
        
        pop_description = POPULATION_INFO.get(population.upper(), {}).get("description", population)
        gender_word = "man" if gender.lower() == "male" else "woman" if gender.lower() == "female" else "person"
        
        prompt = f"""Generate a realistic portrait photograph of an adult {gender_word} with typical {pop_description} ancestry features.
Physical characteristics to include:
- Natural skin tone typical of {pop_description} population
- Appropriate facial features for this ethnic background
- Age: adult (25-40 years old)
- Expression: neutral, natural, friendly
- Lighting: soft, professional studio lighting
- Background: simple, light colored background
- Style: professional headshot portrait photograph
- High quality, photorealistic image"""

        client = genai_new.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
        )
        
        image_data = None
        response_text = None
        
        for part in response.parts:
            if part.text is not None:
                response_text = part.text
            elif part.inline_data is not None:
                image = part.as_image()
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"{patient_id}_generated_portrait_{timestamp}.png"
                image_path = os.path.join("uploads", image_filename)
                image.save(image_path)
                with open(image_path, "rb") as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        if image_data:
            base64_uri = f"data:image/png;base64,{image_data}"
            return jsonify({
                "success": True,
                "image_data": base64_uri,
                "image_path": image_path,
                "description": response_text or f"Generated portrait for {gender} with {pop_description} ancestry",
                "patient_id": str(patient_id),
                "gender": gender,
                "population": population,
                "formatted_result": f"🖼️ **Generated Portrait**\n\n![Generated Portrait]({base64_uri})\n\n**Patient:** {patient_id}\n**Gender:** {gender}\n**Ancestry:** {pop_description}"
            })
        else:
            return jsonify({"success": False, "error": "No image was generated"})
        
    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()})


@predictions_bp.route('/fun-facts', methods=['POST'])
def get_fun_facts():
    """
    Get fun genetic facts
    ---
    tags:
      - Predictions
    """
    data = request.json
    topic = data.get("topic", "general")
    
    api_key, model_name = get_api_config()
    if not api_key:
        return jsonify({"success": False, "error": "Gemini API key not configured"})
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        
        topic_prompts = {
            "general": "5 amazing and surprising facts about human genetics and DNA",
            "ancestry": "5 fascinating facts about genetic ancestry and human migration",
            "health": "5 interesting facts about how genetics affects health and disease",
            "traits": "5 surprising facts about genetic traits like eye color, height, and taste",
            "evolution": "5 mind-blowing facts about human genetic evolution"
        }
        
        prompt = f"""Provide {topic_prompts.get(topic, topic_prompts['general'])}.

Format in markdown:

## 🧬 Fun Genetic Facts: {topic.title()}

### 1. [Catchy Title] 🔬
[Interesting fact with explanation]

### 2. [Catchy Title] 🧪
[Interesting fact with explanation]

(Continue for 5 facts)

---
💡 **Did you know?** Add a bonus fun fact!

Make it engaging, accurate, and easy to understand. Use emojis!"""

        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "topic": topic,
            "formatted_result": response.text
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@predictions_bp.route('/explain-snp', methods=['POST'])
def explain_snp():
    """
    Explain the significance of a specific SNP
    ---
    tags:
      - Predictions
    """
    data = request.json
    snp_id = data.get("snp_id", "")
    
    if not snp_id:
        return jsonify({"success": False, "error": "SNP ID is required"})
    
    api_key, model_name = get_api_config()
    if not api_key:
        return jsonify({"success": False, "error": "Gemini API key not configured"})
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        
        prompt = f"""Explain the SNP {snp_id} in detail. If this is a well-known SNP, provide accurate information. If unknown, provide general information about SNP naming.

Format in markdown:

## 🔬 SNP Analysis: {snp_id}

### 📍 Basic Information
- **SNP ID:** {snp_id}
- **Gene:** [Gene name if known]
- **Chromosome:** [Location if known]
- **Type:** [Type of variation]

### 🧬 What Does This SNP Affect?
[Explain known associations - traits, health conditions, etc.]

### 📊 Population Frequencies
[If known, mention how common different variants are in various populations]

### 🔍 Research & Significance
[Mention relevant research or clinical significance]

### ⚠️ Important Notes
- [Disclaimers about genetic testing interpretation]

---
📚 **Learn More:** Suggest reliable resources for genetic information.

Be scientifically accurate. If the SNP is not well-documented, say so and provide general SNP education."""

        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "snp_id": snp_id,
            "formatted_result": response.text
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@predictions_bp.route('/ancestry-deep-dive', methods=['POST'])
def ancestry_deep_dive():
    """
    Deep dive into ancestry and population genetics
    ---
    tags:
      - Predictions
    """
    data = request.json
    gender = data.get("gender")
    population = data.get("population")
    
    if not gender or not population:
        return jsonify({"success": False, "error": "Missing gender or population"})
    
    api_key, model_name = get_api_config()
    if not api_key:
        return jsonify({"success": False, "error": "Gemini API key not configured"})
    
    try:
        pop_description = POPULATION_INFO.get(population.upper(), {}).get("description", population)
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        
        prompt = f"""Provide a deep dive into the ancestry and genetic history of the {population} population ({pop_description}).

Format in markdown:

## 🌍 Ancestry Deep Dive: {population}

### 📜 Historical Origins
[Explain the historical origins and migration patterns]

### 🗺️ Geographic Distribution
[Where this population is found today and historically]

### 🧬 Genetic Characteristics
[Unique genetic markers and characteristics of this population]

### 👥 Related Populations
[Genetically related populations and their connections]

### 🏛️ Cultural Heritage
[Brief cultural context without stereotypes]

### 🔬 Notable Genetic Studies
[Mention significant research involving this population]

### 📊 Genetic Diversity
[Information about genetic diversity within this population]

---
🌐 **Population Code:** {population}
📍 **Description:** {pop_description}

Be scientifically accurate, respectful, and educational."""

        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "gender": gender,
            "population": population,
            "formatted_result": response.text
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@predictions_bp.route('/genetic-relatedness', methods=['POST'])
def genetic_relatedness():
    """
    Calculate genetic relatedness between two samples
    ---
    tags:
      - Predictions
    """
    data = request.json
    sample_file_1 = data.get("sample_file_1")
    sample_file_2 = data.get("sample_file_2")
    
    if not sample_file_1 or not sample_file_2:
        return jsonify({"success": False, "error": "Two sample files required"})
    
    if not os.path.exists(sample_file_1) or not os.path.exists(sample_file_2):
        return jsonify({"success": False, "error": "One or both sample files not found"})
    
    try:
        # Read both samples
        df1 = pd.read_csv(sample_file_1)
        df2 = pd.read_csv(sample_file_2)
        
        patient1 = df1['Patient_ID'].iloc[0] if 'Patient_ID' in df1.columns else "Sample 1"
        patient2 = df2['Patient_ID'].iloc[0] if 'Patient_ID' in df2.columns else "Sample 2"
        
        pop1 = df1['Population'].iloc[0] if 'Population' in df1.columns else "Unknown"
        pop2 = df2['Population'].iloc[0] if 'Population' in df2.columns else "Unknown"
        
        # Find common SNPs and calculate similarity
        if 'SNP' in df1.columns and 'SNP' in df2.columns:
            common_snps = set(df1['SNP']).intersection(set(df2['SNP']))
            
            if len(common_snps) > 0:
                df1_common = df1[df1['SNP'].isin(common_snps)].set_index('SNP')
                df2_common = df2[df2['SNP'].isin(common_snps)].set_index('SNP')
                
                # Calculate allele matching
                matches = 0
                total = 0
                for snp in list(common_snps)[:10000]:  # Sample up to 10k SNPs
                    if snp in df1_common.index and snp in df2_common.index:
                        a1_1 = df1_common.loc[snp, 'Allele1'] if 'Allele1' in df1_common.columns else None
                        a1_2 = df1_common.loc[snp, 'Allele2'] if 'Allele2' in df1_common.columns else None
                        a2_1 = df2_common.loc[snp, 'Allele1'] if 'Allele1' in df2_common.columns else None
                        a2_2 = df2_common.loc[snp, 'Allele2'] if 'Allele2' in df2_common.columns else None
                        
                        if all([a1_1, a1_2, a2_1, a2_2]):
                            alleles1 = {a1_1, a1_2}
                            alleles2 = {a2_1, a2_2}
                            matches += len(alleles1.intersection(alleles2))
                            total += 2
                
                similarity = (matches / total * 100) if total > 0 else 0
            else:
                similarity = 0
                common_snps = set()
        else:
            similarity = 0
            common_snps = set()
        
        # Determine relationship estimate based on similarity
        if similarity >= 99:
            relationship = "Identical twins / Same person"
        elif similarity >= 75:
            relationship = "First-degree relatives (parent-child, siblings)"
        elif similarity >= 50:
            relationship = "Second-degree relatives (half-siblings, grandparent-grandchild)"
        elif similarity >= 25:
            relationship = "Third-degree relatives (first cousins)"
        else:
            relationship = "Distantly related or unrelated"
        
        # Check if same population
        same_pop = pop1 == pop2
        
        report = f"""## 🧬 Genetic Relatedness Analysis

### 👥 Samples Compared
| Sample | Patient ID | Population |
|--------|------------|------------|
| Sample 1 | {patient1} | {pop1} |
| Sample 2 | {patient2} | {pop2} |

### 📊 Similarity Metrics
- **Common SNPs Analyzed:** {len(common_snps):,}
- **Genetic Similarity Score:** {similarity:.1f}%
- **Same Population:** {'✅ Yes' if same_pop else '❌ No'}

### 🔍 Estimated Relationship
**{relationship}**

### 📈 Similarity Scale
```
0%  ████████████████████████████████████████ 100%
    {'█' * int(similarity/5)}{'░' * (20 - int(similarity/5))} {similarity:.1f}%
```

---
⚠️ **Note:** This is a simplified genetic similarity calculation for educational purposes. 
Professional genetic testing uses more sophisticated methods for relationship determination.
"""
        
        return jsonify({
            "success": True,
            "similarity_score": similarity,
            "common_snps": len(common_snps),
            "estimated_relationship": relationship,
            "same_population": same_pop,
            "formatted_result": report
        })
        
    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()})


@predictions_bp.route('/traits-guide', methods=['GET'])
def traits_guide():
    """
    Get a guide about predictable genetic traits
    ---
    tags:
      - Predictions
    """
    guide = """## 🧬 Genetic Traits Prediction Guide

### 🎯 What Can Genetics Predict?

#### 🟢 High Confidence Traits (Well-Established)
| Trait | Genes | Accuracy |
|-------|-------|----------|
| Eye Color | OCA2, HERC2 | 90%+ for blue/brown |
| Blood Type | ABO gene | 99%+ |
| Earwax Type | ABCC11 | 95%+ |
| Bitter Taste (PTC) | TAS2R38 | 85%+ |
| Lactose Tolerance | LCT | 90%+ |

#### 🟡 Moderate Confidence Traits
| Trait | Complexity | Accuracy |
|-------|------------|----------|
| Hair Color | Multi-gene | 70-85% |
| Hair Texture | FGFR2, EDAR | 70-80% |
| Freckling | MC1R, IRF4 | 75%+ |
| Cleft Chin | Various | 70%+ |
| Attached Earlobes | EDAR | 70%+ |

#### 🔴 Complex Traits (Lower Predictability)
| Trait | Why Complex |
|-------|-------------|
| Height | 1000+ genes + environment |
| Weight/BMI | Genetics + lifestyle |
| Intelligence | Highly polygenic |
| Athletic Ability | Multi-factorial |
| Disease Risk | Gene-environment interaction |

### 📊 Understanding Genetic Predictions

#### What Affects Accuracy?
1. **Number of genes involved** - Single gene = more predictable
2. **Environmental factors** - Diet, lifestyle, exposure
3. **Gene-gene interactions** - Epistasis
4. **Population studied** - Different accuracy across populations

#### 🔬 Types of Genetic Variation
- **SNPs** - Single nucleotide changes (most common)
- **Insertions/Deletions** - Adding or removing bases
- **CNVs** - Copy number variations
- **Structural variants** - Large chromosomal changes

### ⚠️ Important Disclaimers
- Genetic predictions are **probabilistic**, not deterministic
- **Environment** plays a significant role in most traits
- **Population-specific** studies may not apply universally
- Always consult healthcare professionals for medical decisions

---
🧪 **Fun Fact:** You share 99.9% of your DNA with every other human!
"""
    
    return jsonify({
        "success": True,
        "formatted_result": guide
    })


@predictions_bp.route('/summary-card', methods=['POST'])
def summary_card():
    """
    Generate a genetic summary card from a sample
    ---
    tags:
      - Predictions
    """
    data = request.json
    sample_file = data.get("sample_file")
    
    if not sample_file or not os.path.exists(sample_file):
        return jsonify({"success": False, "error": f"Sample file not found: {sample_file}"})
    
    try:
        df = pd.read_csv(sample_file)
        
        patient_id = df['Patient_ID'].iloc[0] if 'Patient_ID' in df.columns else "Unknown"
        
        # Check for gender/sex column (different CSV formats use different names)
        gender = "Unknown"
        gender_emoji = "👤"
        sex_code = None
        if 'gender' in df.columns:
            sex_code = df['gender'].iloc[0]
        elif 'Sex' in df.columns:
            sex_code = df['Sex'].iloc[0]
        elif 'sex' in df.columns:
            sex_code = df['sex'].iloc[0]
        
        if sex_code is not None:
            gender = "Male" if sex_code == 1 else "Female" if sex_code == 2 else "Unknown"
            gender_emoji = "♂️" if gender == "Male" else "♀️" if gender == "Female" else "👤"
        
        population = "Unknown"
        if 'Population' in df.columns:
            population = str(df['Population'].iloc[0])
        
        pop_description = POPULATION_INFO.get(population.upper(), {}).get("description", population)
        
        total_snps = len(df)
        
        # Calculate heterozygosity
        hetero_rate = 0
        if 'Allele1' in df.columns and 'Allele2' in df.columns:
            df['is_hetero'] = df['Allele1'] != df['Allele2']
            hetero_rate = df['is_hetero'].mean() * 100
        
        # Chromosome distribution (for potential future use)
        top_chromosomes = ""
        if 'Chromosome' in df.columns:
            chr_counts = df['Chromosome'].value_counts().head(3).to_dict()
            top_chromosomes = ", ".join([f"Chr{k}: {v:,}" for k, v in chr_counts.items()])
        
        card = f"""
╔══════════════════════════════════════════════════════════════╗
║                    🧬 GENETIC PROFILE CARD                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  👤 Patient ID:     {patient_id:<40} ║
║  {gender_emoji} Gender:          {gender:<40} ║
║  🌍 Ancestry:        {population:<40} ║
║  📍 Origin:          {pop_description[:38]:<38} ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                       📊 GENETIC METRICS                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🔬 Total SNPs:        {total_snps:>10,}                        ║
║  🧪 Heterozygosity:       {hetero_rate:>6.1f}%                        ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                     🏆 UNIQUE IDENTIFIER                      ║
║                                                              ║
║     Your DNA is 99.9% similar to all humans,                 ║
║     but that 0.1% makes you uniquely YOU! 🌟                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

### 📈 Quick Stats
- **Total Variants Analyzed:** {total_snps:,}
- **Heterozygosity Rate:** {hetero_rate:.2f}%
- **Population Group:** {population} ({pop_description})
- **Top Chromosomes:** {top_chromosomes if top_chromosomes else "N/A"}

### 🧬 What This Means
Your genetic profile shows typical characteristics for someone with {pop_description} ancestry.
The heterozygosity rate of {hetero_rate:.1f}% indicates {'good' if hetero_rate > 30 else 'typical'} genetic diversity.

---
📅 Generated by DNA Analysis Assistant
"""
        
        return jsonify({
            "success": True,
            "patient_id": str(patient_id),
            "gender": gender,
            "population": population,
            "total_snps": total_snps,
            "heterozygosity_rate": hetero_rate,
            "formatted_result": card
        })
        
    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()})


# ============================================================
# Page Routes (no URL prefix)
# ============================================================

@predictions_page_bp.route("/predict", methods=["POST"])
def predict():
    """Handle sample prediction requests from the samples page"""
    try:
        # Import predictors lazily to avoid circular imports
        from ml_models import GeneticPredictor, POPULATION_INFO as POP_INFO, find_model_directories
        
        sample_id = request.form.get("sample_id")
        if not sample_id:
            flash("Please provide a sample ID", "error")
            return redirect(url_for("samples"))

        # Initialize predictor
        predictor = GeneticPredictor()
        gender_model_dir, ancestry_model_dir = find_model_directories()
        
        gender_loaded = False
        ancestry_loaded = False
        
        if gender_model_dir:
            gender_loaded = predictor.load_sex_predictor(gender_model_dir)
        if ancestry_model_dir:
            ancestry_loaded = predictor.load_ancestry_predictor(ancestry_model_dir)

        prediction_results = {"sample_id": sample_id, "gender": None, "ancestry": None}

        if gender_loaded and predictor.sex_predictor:
            sex_code, sex_label, true_sex, true_sex_label = predictor.sex_predictor.predict_by_id(sample_id)
            if sex_code is not None:
                prediction_results["gender"] = {
                    "predicted": sex_label,
                    "code": sex_code,
                    "true": true_sex_label,
                    "true_code": true_sex,
                    "correct": sex_code == true_sex if true_sex is not None else None,
                }

        if ancestry_loaded and predictor.ancestry_predictor:
            ancestry, true_ancestry = predictor.ancestry_predictor.predict_by_id(sample_id)
            if ancestry is not None:
                pop_info = POP_INFO.get(ancestry, {})
                prediction_results["ancestry"] = {
                    "predicted": ancestry,
                    "code": pop_info.get("code", ""),
                    "description": pop_info.get("description", ""),
                    "true": true_ancestry,
                    "correct": ancestry == true_ancestry if true_ancestry is not None else None,
                }
                if true_ancestry in POP_INFO:
                    true_pop_info = POP_INFO.get(true_ancestry, {})
                    prediction_results["ancestry"]["true_code"] = true_pop_info.get("code", "")
                    prediction_results["ancestry"]["true_description"] = true_pop_info.get("description", "")

        prediction_results = convert_to_serializable(prediction_results)

        # Get Gemini prediction if available
        gemini_prediction = None
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if prediction_results.get("gender") and prediction_results.get("ancestry") and gemini_api_key:
            if get_physical_characteristics:
                gemini_prediction = get_physical_characteristics(
                    prediction_results["gender"], prediction_results["ancestry"]
                )

        # Get user info for PDF report
        user_info = None
        if current_user.is_authenticated:
            user_info = {
                'name': current_user.username,
                'email': getattr(current_user, 'email', None)
            }

        return render_template(
            "prediction_results.html",
            results=prediction_results,
            sample_id=sample_id,
            gender_loaded=gender_loaded,
            ancestry_loaded=ancestry_loaded,
            gemini_prediction=gemini_prediction,
            user_info=user_info,
        )

    except Exception as e:
        import traceback
        print(f"Error in predict route: {str(e)}")
        traceback.print_exc()
        flash(f"Error during prediction: {str(e)}", "error")
        return redirect(url_for("samples"))


@predictions_page_bp.route("/prediction_results/<patient_id>")
def show_prediction_results(patient_id):
    """Display the prediction results for a processed SNP file"""
    base_name = patient_id.split("_")[0] if "_" in patient_id else patient_id
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
    result_folder = os.path.join(os.getcwd(), "result")

    possible_files = []
    
    # For logged-in users, check user-specific result files first
    if current_user.is_authenticated:
        user_id = current_user.id
        possible_files.extend([
            os.path.join(result_folder, f"{base_name}_user{user_id}_combined_prediction_results.json"),
            os.path.join(result_folder, f"{patient_id}_user{user_id}_combined_prediction_results.json"),
        ])
    
    # Then check non-user-specific files (for backwards compatibility and anonymous users)
    possible_files.extend([
        # Check result folder first (primary location)
        os.path.join(result_folder, f"{base_name}_combined_prediction_results.json"),
        os.path.join(result_folder, f"{patient_id}_combined_prediction_results.json"),
        # Then check other locations for backwards compatibility
        f"{base_name}_combined_prediction_results.json",
        f"{patient_id}_combined_prediction_results.json",
        f"{patient_id}_simplified_results.json",
        os.path.join(upload_folder, f"{base_name}_combined_prediction_results.json"),
        os.path.join(upload_folder, f"{patient_id}_combined_prediction_results.json"),
        f"backup_{patient_id}_results.json",
    ])

    found_path = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            found_path = file_path
            break

    if not found_path:
        flash("Results file not found", "error")
        return redirect(url_for("index"))

    try:
        with open(found_path, "r") as f:
            prediction_results = json.load(f)

        display_results = {
            "sample_id": prediction_results.get("patient_id", patient_id),
            "file_name": prediction_results.get("file_name", f"{patient_id}.csv"),
            "processing_time": prediction_results.get("total_processing_time", "N/A"),
        }

        # Process Gender Prediction (check both sex_prediction and gender_prediction keys)
        display_results["gender"] = {"predicted": "Unknown", "confidence": 0.0}
        sex_pred = prediction_results.get("sex_prediction") or prediction_results.get("gender_prediction")
        if sex_pred:
            predicted_sex = sex_pred.get("predicted_sex", "Unknown")
            male_confidence = float(sex_pred.get("male_confidence", 0.0) or 0.0)
            female_confidence = float(sex_pred.get("female_confidence", 0.0) or 0.0)
            match_rate = float(sex_pred.get("match_rate", max(male_confidence, female_confidence) or 0.85) or 0.85)

            display_results["gender"] = {
                "predicted": predicted_sex,
                "confidence": match_rate,
                "confidence_scores": {"Male": male_confidence, "Female": female_confidence},
            }

        # Process region prediction
        display_results["ancestry"] = {"predicted": "Unknown", "confidence": 0.0}
        if "region_prediction" in prediction_results and prediction_results["region_prediction"]:
            region_pred = prediction_results["region_prediction"]
            predicted_pop = "Unknown"
            match_rate = 0.0
            confidence_scores = {}

            if "prediction" in region_pred and isinstance(region_pred["prediction"], dict):
                prediction_obj = region_pred["prediction"]
                if "predicted_population" in prediction_obj:
                    predicted_pop = prediction_obj["predicted_population"]
                if "match_rate" in prediction_obj and prediction_obj["match_rate"] is not None:
                    try:
                        match_rate = float(prediction_obj["match_rate"])
                    except (TypeError, ValueError):
                        match_rate = 0.80

            if "confidence_scores" in region_pred and isinstance(region_pred["confidence_scores"], dict):
                confidence_scores = region_pred["confidence_scores"]

            display_results["ancestry"] = {
                "predicted": predicted_pop,
                "confidence": match_rate,
                "confidence_scores": confidence_scores,
            }

            if predicted_pop in POPULATION_INFO:
                display_results["ancestry"]["description"] = POPULATION_INFO[predicted_pop]["description"]
                display_results["ancestry"]["code"] = POPULATION_INFO[predicted_pop]["code"]

        # Get user info for PDF report
        user_info = None
        if current_user.is_authenticated:
            user_info = {
                'name': current_user.username,
                'email': getattr(current_user, 'email', None)
            }

        return render_template(
            "prediction_results.html",
            results=display_results,
            sample_id=display_results["sample_id"],
            gender_loaded=True,
            ancestry_loaded=True,
            raw_snp_prediction=True,
            full_results=prediction_results,
            user_info=user_info,
        )

    except Exception as e:
        flash(f"Error displaying results: {str(e)}", "error")
        import traceback
        traceback.print_exc()
        return redirect(url_for("index"))


@predictions_page_bp.route("/get_physical_characteristics", methods=["POST"])
def get_physical_characteristics_api():
    """API endpoint to get physical characteristics prediction"""
    try:
        data = request.json
        gender_prediction = data.get("gender")
        ancestry_prediction = data.get("ancestry")
        sample_id = data.get("sample_id")

        if not gender_prediction or not ancestry_prediction:
            return jsonify({"success": False, "error": "Missing gender or ancestry prediction data"})

        gender_prediction = convert_to_serializable(gender_prediction)
        ancestry_prediction = convert_to_serializable(ancestry_prediction)

        if get_physical_characteristics:
            gemini_prediction = get_physical_characteristics(gender_prediction, ancestry_prediction)
            
            # Save to database if sample_id provided (filter by user for proper ownership)
            if sample_id and gemini_prediction.get("success"):
                try:
                    # Build query with user filter for proper ownership
                    query = AnalysisHistory.query.filter_by(sample_id=sample_id)
                    if current_user.is_authenticated:
                        # For logged-in users, only update their own analyses or unassigned ones
                        query = query.filter(
                            or_(AnalysisHistory.user_id == current_user.id, AnalysisHistory.user_id == None)
                        )
                    analysis = query.order_by(AnalysisHistory.created_at.desc()).first()
                    if analysis:
                        # Convert dict to JSON string for database storage
                        chars = gemini_prediction.get("characteristics", "")
                        if isinstance(chars, dict):
                            chars = json.dumps(chars)
                        analysis.physical_characteristics = chars
                        db.session.commit()
                        print(f"✅ Physical characteristics saved for {sample_id}")
                except Exception as db_err:
                    print(f"Warning: Could not save physical characteristics: {db_err}")
            
            return jsonify(gemini_prediction)
        else:
            return jsonify({"success": False, "error": "Physical characteristics service not available"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@predictions_page_bp.route("/get_disease_risk_report", methods=["POST"])
def get_disease_risk_report_api():
    """API endpoint to get disease risk report"""
    try:
        data = request.json
        gender_prediction = data.get("gender")
        ancestry_prediction = data.get("ancestry")
        sample_id = data.get("sample_id")

        if not gender_prediction or not ancestry_prediction:
            return jsonify({"success": False, "error": "Missing gender or ancestry prediction data"})

        gender_prediction = convert_to_serializable(gender_prediction)
        ancestry_prediction = convert_to_serializable(ancestry_prediction)

        if get_genetic_disease_risk:
            disease_report = get_genetic_disease_risk(gender_prediction, ancestry_prediction)
            
            # Save to database if sample_id provided (filter by user for proper ownership)
            if sample_id and disease_report.get("success"):
                try:
                    print(f"🔍 [Disease Risk] Looking for analysis with sample_id={sample_id}")
                    # Build query with user filter for proper ownership
                    query = AnalysisHistory.query.filter_by(sample_id=sample_id)
                    if current_user.is_authenticated:
                        print(f"🔍 [Disease Risk] User is authenticated: user_id={current_user.id}")
                        # For logged-in users, only update their own analyses or unassigned ones
                        query = query.filter(
                            or_(AnalysisHistory.user_id == current_user.id, AnalysisHistory.user_id == None)
                        )
                    else:
                        print(f"🔍 [Disease Risk] User is NOT authenticated")
                    analysis = query.order_by(AnalysisHistory.created_at.desc()).first()
                    if analysis:
                        # Convert diseases list to JSON string for storage
                        diseases = disease_report.get("diseases", [])
                        if isinstance(diseases, list):
                            analysis.disease_risk_report = json.dumps(diseases)
                        else:
                            analysis.disease_risk_report = disease_report.get("report", str(diseases))
                        db.session.commit()
                        print(f"✅ Disease risk report saved for {sample_id} (analysis_id={analysis.id})")
                    else:
                        print(f"⚠️ [Disease Risk] No analysis found for sample_id={sample_id}")
                        # Try to find any analysis with similar sample_id
                        all_analyses = AnalysisHistory.query.filter(
                            AnalysisHistory.sample_id.like(f"%{sample_id}%")
                        ).limit(5).all()
                        if all_analyses:
                            print(f"📋 [Disease Risk] Similar sample_ids found: {[a.sample_id for a in all_analyses]}")
                except Exception as db_err:
                    print(f"Warning: Could not save disease risk report: {db_err}")
            
            return jsonify(disease_report)
        else:
            return jsonify({"success": False, "error": "Disease risk service not available"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@predictions_page_bp.route("/get_health_guidance", methods=["POST"])
def get_health_guidance_api():
    """API endpoint to get AI health guidance based on disease risks"""
    try:
        data = request.json
        diseases = data.get("diseases", [])
        gender = data.get("gender", "Unknown")
        population = data.get("population", "Unknown")

        if not diseases:
            return jsonify({"success": False, "error": "Missing disease risk data"})

        if get_ai_health_guidance:
            guidance_report = get_ai_health_guidance(diseases, gender, population)
            return jsonify(guidance_report)
        else:
            return jsonify({"success": False, "error": "Health guidance service not available"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
