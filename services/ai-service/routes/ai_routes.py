"""
AI Routes - REST API for Gemini AI
AI Service Microservice
"""
from flask import Blueprint, request, jsonify
import os
import google.generativeai as genai

ai_bp = Blueprint('ai', __name__)


# Population Information
POPULATION_INFO = {
    "ASW": {"code": "A", "description": "African ancestry in Southwest USA"},
    "CEU": {"code": "C", "description": "Utah residents with Northern and Western European ancestry"},
    "CHB": {"code": "H", "description": "Han Chinese in Beijing, China"},
    "CHD": {"code": "D", "description": "Chinese in Metropolitan Denver, Colorado"},
    "GIH": {"code": "G", "description": "Gujarati Indians in Houston, Texas"},
    "JPT": {"code": "J", "description": "Japanese in Tokyo, Japan"},
    "LWK": {"code": "L", "description": "Luhya in Webuye, Kenya"},
    "MEX": {"code": "M", "description": "Mexican ancestry in Los Angeles, California"},
    "MKK": {"code": "K", "description": "Maasai in Kinyawa, Kenya"},
    "TSI": {"code": "T", "description": "Tuscan in Italy"},
    "YRI": {"code": "Y", "description": "Yoruban in Ibadan, Nigeria"},
}


def get_gemini_model():
    """Get configured Gemini model"""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY")
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    
    if not api_key:
        return None, "Gemini API key not configured"
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name=model_name), None


# ============================================================
# Physical Characteristics Endpoint
# ============================================================

@ai_bp.route('/api/ai/physical', methods=['POST'])
def predict_physical_characteristics():
    """
    Generate physical characteristics prediction using Gemini AI
    
    POST /api/ai/physical
    Body: {"gender": "Male", "population": "CEU"}
    
    Returns: {"success": true, "characteristics": "..."}
    """
    try:
        model, error = get_gemini_model()
        if error:
            return jsonify({"success": False, "error": error}), 503
        
        data = request.get_json() or {}
        gender = data.get('gender')
        population = data.get('population')
        
        if not gender or not population:
            return jsonify({
                "success": False,
                "error": "gender and population are required"
            }), 400
        
        pop_description = POPULATION_INFO.get(population.upper(), {}).get("description", population)
        
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
- **Height Range:** Typical range for {gender}
- **Build:** Common body types

### ⚠️ Disclaimer
These are population-level statistical tendencies. Individual traits vary significantly based on specific genetic variations.

Important: Keep the response concise and factual. Use markdown formatting. Include relevant emojis."""

        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "characteristics": response.text,
            "gender": gender,
            "population": population
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# Disease Risk Analysis Endpoint
# ============================================================

@ai_bp.route('/api/ai/disease-risk', methods=['POST'])
def analyze_disease_risk():
    """
    Generate disease risk analysis using Gemini AI
    
    POST /api/ai/disease-risk
    Body: {"gender": "Male", "population": "CEU", "snp_data": {...}}
    
    Returns: {"success": true, "report": "..."}
    """
    try:
        model, error = get_gemini_model()
        if error:
            return jsonify({"success": False, "error": error}), 503
        
        data = request.get_json() or {}
        gender = data.get('gender', 'Unknown')
        population = data.get('population', 'Unknown')
        snp_data = data.get('snp_data', {})
        age = data.get('age')
        
        pop_description = POPULATION_INFO.get(population.upper(), {}).get("description", population)
        
        # Build SNP info for the prompt
        snp_info = ""
        if snp_data:
            snp_info = "\n\nRelevant genetic variants:\n"
            for rs_id, info in list(snp_data.items())[:20]:  # Limit to 20 SNPs
                snp_info += f"- {rs_id}: {info.get('genotype', 'Unknown')} - {info.get('gene', 'Unknown gene')}\n"
        
        prompt = f"""Generate a genetic disease risk report for:
- Gender: {gender}
- Population: {population} ({pop_description})
{f'- Age: {age}' if age else ''}
{snp_info}

Create a comprehensive health risk report in markdown format:

## 🏥 Genetic Health Risk Report

**Subject Profile:** {gender} | {population}

---

### 🫀 Cardiovascular Health
- **Risk Level:** [Low/Moderate/Elevated]
- **Key Factors:** List relevant population-specific risk factors
- **Recommendations:** Preventive measures

### 🩸 Metabolic Conditions
- **Type 2 Diabetes Risk:** Assessment based on population data
- **Metabolic Syndrome:** Risk factors

### 🧬 Cancer Screening Priorities
- List relevant cancer screenings based on gender and population
- Recommended screening ages

### 🧠 Neurological Health
- Population-specific considerations
- Prevention strategies

### 💪 Recommendations
1. Lifestyle modifications
2. Screening schedule
3. Preventive measures

### ⚠️ Important Disclaimer
This report is based on population-level statistics and should not replace professional medical advice. Consult healthcare providers for personalized guidance.

Keep the response informative but concise. Use medical-appropriate language."""

        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "report": response.text,
            "gender": gender,
            "population": population
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# Health Insights Chat Endpoint
# ============================================================

@ai_bp.route('/api/ai/chat', methods=['POST'])
def health_chat():
    """
    Interactive health insights chat using Gemini AI
    
    POST /api/ai/chat
    Body: {"message": "...", "context": {...}}
    
    Returns: {"success": true, "response": "..."}
    """
    try:
        model, error = get_gemini_model()
        if error:
            return jsonify({"success": False, "error": error}), 503
        
        data = request.get_json() or {}
        message = data.get('message')
        context = data.get('context', {})
        
        if not message:
            return jsonify({
                "success": False,
                "error": "message is required"
            }), 400
        
        # Build context from genetic data
        context_info = ""
        if context:
            context_info = f"""
User's genetic profile:
- Gender: {context.get('gender', 'Unknown')}
- Population: {context.get('population', 'Unknown')}
- Previous analysis: {context.get('analysis_summary', 'None available')}
"""
        
        prompt = f"""You are a genetic health assistant. Provide helpful, accurate information about genetics and health.

{context_info}

User question: {message}

Guidelines:
1. Provide accurate, science-based information
2. Always recommend consulting healthcare professionals for medical decisions
3. Be clear about limitations of genetic predictions
4. Use accessible language while being scientifically accurate
5. Include relevant disclaimers when discussing health risks

Response:"""

        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "response": response.text
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# SNP Interpretation Endpoint
# ============================================================

@ai_bp.route('/api/ai/interpret-snp', methods=['POST'])
def interpret_snp():
    """
    Get AI interpretation of specific SNP
    
    POST /api/ai/interpret-snp
    Body: {"rs_id": "rs12345", "genotype": "AA", "gene": "BRCA1"}
    
    Returns: {"success": true, "interpretation": "..."}
    """
    try:
        model, error = get_gemini_model()
        if error:
            return jsonify({"success": False, "error": error}), 503
        
        data = request.get_json() or {}
        rs_id = data.get('rs_id')
        genotype = data.get('genotype')
        gene = data.get('gene', 'Unknown')
        
        if not rs_id:
            return jsonify({
                "success": False,
                "error": "rs_id is required"
            }), 400
        
        prompt = f"""Provide a brief interpretation of this genetic variant:

- SNP ID: {rs_id}
- Genotype: {genotype or 'Not specified'}
- Gene: {gene}

Include:
1. What this gene/variant is associated with
2. What the genotype might indicate (if known)
3. Clinical significance (if any)
4. Any relevant research findings

Keep response concise (2-3 paragraphs). Include disclaimer about consulting professionals."""

        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "rs_id": rs_id,
            "interpretation": response.text
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# Population Comparison Endpoint
# ============================================================

@ai_bp.route('/api/ai/population-info', methods=['GET'])
def get_population_info():
    """
    Get detailed information about a population
    
    GET /api/ai/population-info?population=CEU
    
    Returns: {"success": true, "info": "..."}
    """
    try:
        population = request.args.get('population')
        
        if not population:
            return jsonify({
                "success": False,
                "error": "population parameter is required"
            }), 400
        
        pop_data = POPULATION_INFO.get(population.upper())
        
        if not pop_data:
            return jsonify({
                "success": False,
                "error": f"Unknown population: {population}"
            }), 404
        
        model, error = get_gemini_model()
        if error:
            # Return basic info without AI enhancement
            return jsonify({
                "success": True,
                "population": population.upper(),
                "code": pop_data["code"],
                "description": pop_data["description"],
                "ai_enhanced": False
            }), 200
        
        prompt = f"""Provide a brief overview of the {population.upper()} population group ({pop_data['description']}):

Include:
1. Geographic origins
2. Key genetic characteristics
3. Common genetic variants in this population
4. Health considerations specific to this group

Keep response concise (2-3 paragraphs)."""

        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "population": population.upper(),
            "code": pop_data["code"],
            "description": pop_data["description"],
            "detailed_info": response.text,
            "ai_enhanced": True
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@ai_bp.route('/api/ai/populations', methods=['GET'])
def list_populations():
    """
    List all supported populations
    
    GET /api/ai/populations
    
    Returns: {"success": true, "populations": {...}}
    """
    return jsonify({
        "success": True,
        "populations": POPULATION_INFO
    }), 200
