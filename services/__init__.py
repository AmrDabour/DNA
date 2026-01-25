"""
Services Module
Contains service functions for GenovaAI
"""
import os

# Population descriptions for physical/disease predictions
POPULATION_INFO = {
    "CEU": {"description": "Utah Residents with Northern and Western European Ancestry", "region": "Europe"},
    "YRI": {"description": "Yoruba in Ibadan, Nigeria", "region": "Africa"},
    "JPT": {"description": "Japanese in Tokyo, Japan", "region": "East Asia"},
    "CHB": {"description": "Han Chinese in Beijing, China", "region": "East Asia"},
    "GIH": {"description": "Gujarati Indians in Houston, Texas", "region": "South Asia"},
    "ASW": {"description": "African Ancestry in Southwest USA", "region": "Americas"},
    "MXL": {"description": "Mexican Ancestry in Los Angeles, California", "region": "Americas"},
    "TSI": {"description": "Toscani in Italia", "region": "Europe"},
    "LWK": {"description": "Luhya in Webuye, Kenya", "region": "Africa"},
    "CHD": {"description": "Chinese in Metropolitan Denver, Colorado", "region": "Americas"},
    "MKK": {"description": "Maasai in Kinyawa, Kenya", "region": "Africa"},
}


def configure_gemini():
    """
    Configure the Gemini API for the application.
    Sets up the API key from environment variables.
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if api_key:
        print("✅ Gemini API configured")
        return True
    else:
        print("⚠️ Gemini API key not set - AI features may be limited")
        return False


def get_physical_characteristics(gender_prediction, ancestry_prediction):
    """
    Get physical characteristics prediction using Gemini API.
    
    Args:
        gender_prediction: Gender prediction result (dict or str)
        ancestry_prediction: Ancestry/population prediction result (dict or str)
    
    Returns:
        dict with success status and characteristics data
    """
    try:
        import google.generativeai as genai
        import json
        
        api_key = os.environ.get('GEMINI_API_KEY')
        model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
        
        if not api_key:
            return {"success": False, "error": "Gemini API key not configured"}
        
        # Extract gender from prediction results - check multiple possible keys
        gender = "Unknown"
        if isinstance(gender_prediction, dict):
            for key in ['predicted', 'prediction', 'gender', 'sex', 'predicted_gender', 'result']:
                if key in gender_prediction and gender_prediction[key]:
                    gender = str(gender_prediction[key])
                    break
        elif gender_prediction:
            gender = str(gender_prediction)
        
        # Extract population from prediction results - check multiple possible keys
        population = "Unknown"
        if isinstance(ancestry_prediction, dict):
            # First try 'code' which is the population code like 'YRI', 'CEU'
            for key in ['code', 'predicted', 'prediction', 'population', 'ancestry', 'predicted_population', 'result']:
                if key in ancestry_prediction and ancestry_prediction[key]:
                    population = str(ancestry_prediction[key])
                    break
        elif ancestry_prediction:
            population = str(ancestry_prediction)
        
        # Normalize population code
        population = population.upper() if population else "Unknown"
        
        pop_info = POPULATION_INFO.get(population, {})
        pop_description = pop_info.get("description", population)
        region = pop_info.get("region", "Unknown Region")
        
        print(f"🔍 Physical Characteristics: Gender={gender}, Population={population}, Description={pop_description}")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        
        prompt = f"""You are a genetics expert. Based on population genetics data, provide SPECIFIC physical characteristics for:

Gender: {gender}
Population: {population} ({pop_description})
Region: {region}

IMPORTANT: Give SPECIFIC characteristics typical for this population. DO NOT say "varies" or "variable". Be specific based on scientific population genetics studies.

Return ONLY valid JSON (no markdown, no code blocks, no extra text):
{{
    "hair": {{"color": "Most common: [specific color]", "texture": "Typically [specific texture]"}},
    "eyes": {{"color": "Predominantly [specific color]", "shape": "[specific shape]"}},
    "skin": {{"tone": "[specific tone range]"}},
    "face": {{"features": "[2-3 specific features]"}},
    "body": {{"build": "[typical build for this population]"}},
    "traits": {{"other": "[one unique trait for this population]"}}
}}

Example for YRI (Yoruba Nigerian):
{{"hair": {{"color": "Black", "texture": "Tightly coiled (Type 4)"}}, "eyes": {{"color": "Dark brown", "shape": "Round to almond"}}, ...}}

Now provide for {population}:"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response - remove markdown code blocks if present
        if "```" in response_text:
            parts = response_text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    response_text = part
                    break
        
        response_text = response_text.strip()
        
        try:
            characteristics_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error: {e}, Response: {response_text[:200]}")
            # Fallback with population-specific defaults
            characteristics_data = {
                "hair": {"color": "Dark", "texture": "Varies by individual"},
                "eyes": {"color": "Brown", "shape": "Varies"},
                "skin": {"tone": "Medium"},
                "face": {"features": "Population-typical features"},
                "body": {"build": "Average build"},
                "traits": {"other": "Individual variation exists"}
            }
        
        return {
            "success": True,
            "characteristics": characteristics_data,
            "gender": gender,
            "population": population,
            "pop_description": pop_description
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_genetic_disease_risk(gender_prediction, ancestry_prediction, patient_id="Unknown"):
    """
    Get genetic disease risk assessment using Gemini API.
    
    Args:
        gender_prediction: Gender prediction result (dict or str)
        ancestry_prediction: Ancestry/population prediction result (dict or str)
        patient_id: Optional patient identifier
    
    Returns:
        dict with success status and diseases array
    """
    try:
        import google.generativeai as genai
        import json
        
        api_key = os.environ.get('GEMINI_API_KEY')
        model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
        
        if not api_key:
            return {"success": False, "error": "Gemini API key not configured"}
        
        # Extract gender from prediction results - check multiple possible keys
        gender = "Unknown"
        if isinstance(gender_prediction, dict):
            for key in ['predicted', 'prediction', 'gender', 'sex', 'predicted_gender', 'result']:
                if key in gender_prediction and gender_prediction[key]:
                    gender = str(gender_prediction[key])
                    break
        elif gender_prediction:
            gender = str(gender_prediction)
        
        # Extract population from prediction results - check multiple possible keys
        population = "Unknown"
        if isinstance(ancestry_prediction, dict):
            for key in ['code', 'predicted', 'prediction', 'population', 'ancestry', 'predicted_population', 'result']:
                if key in ancestry_prediction and ancestry_prediction[key]:
                    population = str(ancestry_prediction[key])
                    break
        elif ancestry_prediction:
            population = str(ancestry_prediction)
        
        population = population.upper() if population else "Unknown"
        
        pop_info = POPULATION_INFO.get(population, {})
        pop_description = pop_info.get("description", population)
        region = pop_info.get("region", "Unknown")
        
        print(f"🔍 Disease Risk: Gender={gender}, Population={population}, Description={pop_description}")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        
        prompt = f"""You are a genetics expert. Based on population genetics, list 5 genetic disease risks for:

Gender: {gender}
Population: {population} ({pop_description})
Region: {region}

Return ONLY valid JSON (no markdown, no code blocks):
{{
    "diseases": [
        {{
            "name": "Disease Name",
            "risk": "high",
            "genes": "GENE1, GENE2",
            "prevalence": "X%",
            "description": "One sentence about this disease"
        }}
    ]
}}

Rules:
- Include exactly 5 diseases
- "risk" must be exactly: "high", "moderate", or "low"
- Use REAL diseases with documented genetic links to {population} population
- Include REAL gene names
- Use REAL prevalence percentages from scientific literature
- Keep description to ONE sentence"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up markdown code blocks if present
        if "```" in response_text:
            parts = response_text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    response_text = part
                    break
        
        try:
            diseases_data = json.loads(response_text)
            diseases = diseases_data.get("diseases", [])
        except json.JSONDecodeError as e:
            print(f"⚠️ Disease JSON parse error: {e}")
            diseases = []
        
        return {
            "success": True,
            "diseases": diseases,
            "gender": gender,
            "population": population,
            "pop_description": pop_description,
            "patient_id": patient_id
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


__all__ = ['configure_gemini', 'get_physical_characteristics', 'get_genetic_disease_risk', 'POPULATION_INFO']
