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
    "MEX": {"description": "Mexican Ancestry in Los Angeles, California", "region": "Americas"},
    "TSI": {"description": "Toscani in Italia", "region": "Europe"},
    "LWK": {"description": "Luhya in Webuye, Kenya", "region": "Africa"},
    "CHD": {"description": "Chinese in Metropolitan Denver, Colorado", "region": "Americas"},
    "MKK": {"description": "Maasai in Kinyawa, Kenya", "region": "Africa"},
}

# Short code to full population code mapping
# This maps single-letter codes (used in some data files) to full population codes
SHORT_CODE_TO_POPULATION = {
    "A": "ASW",  # African ancestry in Southwest USA
    "C": "CEU",  # Utah residents with Northern and Western European ancestry
    "H": "CHB",  # Han Chinese in Beijing, China
    "D": "CHD",  # Chinese in Metropolitan Denver, Colorado
    "G": "GIH",  # Gujarati Indians in Houston, Texas
    "J": "JPT",  # Japanese in Tokyo, Japan
    "L": "LWK",  # Luhya in Webuye, Kenya
    "M": "MEX",  # Mexican ancestry in Los Angeles, California
    "K": "MKK",  # Maasai in Kinyawa, Kenya
    "T": "TSI",  # Tuscan in Italy
    "Y": "YRI",  # Yoruban in Ibadan, Nigeria
}


def resolve_population_code(population):
    """
    Resolve a population code to its full form.
    Handles both full codes (CEU, YRI) and short codes (C, Y, H).
    
    Args:
        population: Population code (can be full like 'CEU' or short like 'C')
    
    Returns:
        tuple: (full_code, description, region)
    """
    if not population:
        return "Unknown", "Unknown Population", "Unknown"
    
    pop_upper = str(population).upper().strip()
    
    # First check if it's already a full code
    if pop_upper in POPULATION_INFO:
        info = POPULATION_INFO[pop_upper]
        return pop_upper, info.get("description", pop_upper), info.get("region", "Unknown")
    
    # Check if it's a short code
    if pop_upper in SHORT_CODE_TO_POPULATION:
        full_code = SHORT_CODE_TO_POPULATION[pop_upper]
        info = POPULATION_INFO.get(full_code, {})
        return full_code, info.get("description", full_code), info.get("region", "Unknown")
    
    # Unknown population - return as is
    return pop_upper, f"Population: {pop_upper}", "Unknown"


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
        
        # Use resolve_population_code to handle both full codes (CEU) and short codes (C, H)
        population, pop_description, region = resolve_population_code(population)
        
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
        
        # Use resolve_population_code to handle both full codes (CEU) and short codes (C, H)
        population, pop_description, region = resolve_population_code(population)
        
        print(f"🔍 Disease Risk: Gender={gender}, Population={population}, Description={pop_description}")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        
        prompt = f"""You are a genetics expert. Based on population genetics, assess disease risks for:

Gender: {gender}
Population: {population} ({pop_description})
Region: {region}

ONLY SELECT FROM THESE DISEASES:
- Alzheimer's disease
- Parkinson's disease
- Cancer susceptibility
- ADHD (Attention Deficit Hyperactivity Disorder)
- Colorectal cancer
- Prostate cancer
- Breast cancer
- Lung cancer
- Heart attack (Myocardial infarction)
- Coronary artery disease
- Stroke
- Type 2 diabetes
- Type 1 diabetes
- Obesity
- Hypertension (High blood pressure)
- Asthma
- Depression
- Bipolar disorder
- Schizophrenia
- Anxiety disorders
- Celiac disease
- Crohn's disease
- Lupus (Systemic lupus erythematosus)
- Rheumatoid arthritis
- Multiple sclerosis
- Osteoporosis
- Thyroid disorders
- Autism spectrum disorder
- Epilepsy
- Age-related macular degeneration
- Glaucoma
- Sickle cell disease
- Cystic fibrosis
- Hemophilia

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
- Select 5 diseases from the list above that are most relevant to {gender} and {population} population
- "risk" must be exactly: "high", "moderate", or "low" and donot make all disease from one risk level
- Use REAL gene names associated with each disease
- Use REAL prevalence percentages from scientific literature for {population} population
- For gender-specific diseases (Prostate cancer for males, Breast cancer for females), only include if appropriate
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


def get_ai_health_guidance(diseases, gender, population):
    """
    Get personalized health guidance based on disease risks.
    
    Args:
        diseases: List of disease risk objects
        gender: Gender of the person
        population: Population/Ancestry code
        
    Returns:
        dict with success status and guidance data
    """
    try:
        import google.generativeai as genai
        import json
        
        api_key = os.environ.get('GEMINI_API_KEY')
        model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
        
        if not api_key:
            return {"success": False, "error": "Gemini API key not configured"}
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        
        disease_names = ", ".join([d.get('name', 'Unknown') for d in diseases])
        
        prompt = f"""You are a health advisor. Based on genetic disease risks for a {gender} from {population} population:
Risks: {disease_names}

Return ONLY valid JSON (no markdown):
{{
    "guidance": {{
        "nutrition": ["brief tip 1", "brief tip 2", "brief tip 3"],
        "lifestyle": ["brief tip 1", "brief tip 2", "brief tip 3"],
        "screenings": ["brief tip 1", "brief tip 2", "brief tip 3"],
        "wellness": ["brief tip 1", "brief tip 2", "brief tip 3"]
    }},
    "summary": "One short sentence"
}}

Rules:
- Only 3 short tips per category (max 10 words each)
- Keep summary under 15 words
- Be concise"""

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
            guidance_data = json.loads(response_text)
            return {
                "success": True,
                "guidance": guidance_data.get("guidance", {}),
                "summary": guidance_data.get("summary", "")
            }
        except json.JSONDecodeError as e:
            print(f"⚠️ Guidance JSON parse error: {e}")
            return {"success": False, "error": "Could not parse AI response"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


__all__ = ['configure_gemini', 'get_physical_characteristics', 'get_genetic_disease_risk', 'get_ai_health_guidance', 'POPULATION_INFO', 'SHORT_CODE_TO_POPULATION', 'resolve_population_code']
