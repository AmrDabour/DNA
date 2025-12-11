"""
Gemini AI Service - Functions for AI-powered predictions
"""
import os
import json
import google.generativeai as genai

from utils.serialization import convert_to_serializable
from utils.formatting import format_characteristics_html, format_disease_report_html


def configure_gemini():
    """Configure Gemini API with the environment key"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        return True
    return False


def get_physical_characteristics(gender_prediction, ancestry_prediction):
    """
    Use Gemini API to predict physical characteristics based on gender and ancestry
    """
    try:
        # Configure the model
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 2048,
        }

        # Initialize Gemini model
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash", generation_config=generation_config
        )

        # Create the prompt
        prompt = f"""
        Based on genetic ancestry and Gender Prediction data, provide the MOST LIKELY single physical characteristic for each category with its statistical accuracy percentage.
        
        Genetic Data:
        - Gender: {gender_prediction['predicted'] if gender_prediction else 'Unknown'}
        - Ancestry: {ancestry_prediction['predicted'] if ancestry_prediction else 'Unknown'} 
        - Population Code: {ancestry_prediction['code'] if ancestry_prediction else 'Unknown'}
        - Population Description: {ancestry_prediction['description'] if ancestry_prediction else 'Unknown'}
        
        Return a structured JSON object with ONLY ONE specific value per characteristic and its accuracy percentage.
        IMPORTANT: Response must be in ENGLISH only.
        IMPORTANT: Only provide ONE value per field (the most common/likely), not multiple options.
        
        {{
          "gender": "[gender]",
          "ancestry": "[ancestry]",
          "population_code": "[code]",
          "physical_characteristics": {{
            "hair": {{
              "color": "single most common color",
              "color_accuracy": 85,
              "texture": "single most common texture",
              "texture_accuracy": 80
            }},
            "eyes": {{
              "color": "single most common color",
              "color_accuracy": 90,
              "shape": "single most common shape",
              "shape_accuracy": 75
            }},
            "skin": {{
              "tone": "single most common tone",
              "tone_accuracy": 88
            }},
            "facial_features": {{
              "nose": "single characteristic",
              "nose_accuracy": 70,
              "lips": "single characteristic",
              "lips_accuracy": 72,
              "face_shape": "single shape",
              "face_shape_accuracy": 65,
              "chin": "single characteristic",
              "chin_accuracy": 60,
              "cheekbones": "single characteristic",
              "cheekbones_accuracy": 68
            }},
            "body_structure": {{
              "height": "specific height description",
              "height_accuracy": 70,
              "build": "single body type",
              "build_accuracy": 65,
              "frame": "single frame size",
              "frame_accuracy": 68
            }},
            "other_traits": {{
              "trait1": "one distinctive trait",
              "trait1_accuracy": 60,
              "trait2": "another distinctive trait",
              "trait2_accuracy": 55
            }}
          }}
        }}
        
        IMPORTANT: Each value must be a SINGLE string (not an array), representing the most statistically common trait.
        IMPORTANT: Accuracy percentages should be realistic estimates based on population genetics data (typically 55-95%).
        IMPORTANT: Response must be in ENGLISH only.
        Only return the JSON without any explanations or extra text.
        """

        # Generate response
        response = model.generate_content(prompt)

        # Try to parse the response as JSON
        try:
            # Clean the response text (remove markdown code blocks if present)
            response_text = response.text.strip()
            
            # Handle various markdown code block formats
            if "```json" in response_text:
                # Extract content between ```json and ```
                start_idx = response_text.find("```json") + 7
                end_idx = response_text.find("```", start_idx)
                if end_idx != -1:
                    response_text = response_text[start_idx:end_idx].strip()
                else:
                    response_text = response_text[start_idx:].strip()
            elif response_text.startswith("```"):
                # Remove starting ```
                response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                # Remove language identifier if present (e.g., "json\n")
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Also handle if it starts with just "json" (without backticks)
            if response_text.startswith("json\n"):
                response_text = response_text[5:].strip()

            # Parse JSON
            characteristics_data = json.loads(response_text)

            # Process the data to ensure all items in arrays are strings
            cleaned_data = convert_to_serializable(characteristics_data)

            # Safely format the response for better display
            try:
                formatted_html = format_characteristics_html(cleaned_data)
                return {
                    "success": True,
                    "characteristics": formatted_html,
                    "raw_data": cleaned_data,
                }
            except Exception as formatting_error:
                # If there's an error in formatting, return the raw data in plain text
                return {
                    "success": True,
                    "characteristics": f"<pre>{json.dumps(cleaned_data, indent=2)}</pre>",
                    "error_details": str(formatting_error),
                }

        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            return {"success": True, "characteristics": f"<pre>{response.text}</pre>"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_genetic_disease_risk(gender_prediction, ancestry_prediction):
    """
    Use Gemini API to analyze potential genetic disease risks based on ancestry and gender
    """
    try:
        # Configure the model
        generation_config = {
            "temperature": 0.3,  # Lower temperature for more factual output
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 2048,
        }

        # Initialize Gemini model
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash", generation_config=generation_config
        )

        # Create the prompt
        prompt = f"""
        As a genetic analyst, provide an in-depth risk assessment report on potential genetic diseases and conditions 
        associated with the following genetic profile:
        
        Genetic Data:
        - Gender: {gender_prediction['predicted'] if gender_prediction else 'Unknown'}
        - Ancestry: {ancestry_prediction['predicted'] if ancestry_prediction else 'Unknown'} 
        - Population Code: {ancestry_prediction['code'] if ancestry_prediction else 'Unknown'}
        - Population Description: {ancestry_prediction['description'] if ancestry_prediction else 'Unknown'}
        
        Return a structured JSON object with genetic disease risk information for this profile:
        
        {{
          "profile_summary": {{
            "gender": "[gender]",
            "ancestry": "[ancestry]",
            "population_code": "[code]"
          }},
          "disease_risks": [
            {{
              "disease_name": "[name of genetic disease]",
              "risk_level": "[high/moderate/low]",
              "affected_genes": ["gene1", "gene2"],
              "description": "Brief description of the disease",
              "prevalence_in_population": "Statistical prevalence in this population",
              "key_mutations": ["specific genetic mutations if relevant"],
              "recommendations": ["general recommendations for monitoring or prevention"]
            }},
            // Additional diseases...
          ]
        }}
        
        IMPORTANT: Response must be in ENGLISH only.
        IMPORTANT: All arrays must contain only string elements, not nested arrays.
        IMPORTANT: Include at least 3-5 diseases or conditions that show significant prevalence differences based on ancestry.
        IMPORTANT: Focus on known conditions with established genetic links. Include ONLY factual information.
        IMPORTANT: For each disease, mention specific genes known to be associated with the condition.
        IMPORTANT: Base your response on factual genetic research about disease prevalence in different populations.
        """

        # Generate response
        response = model.generate_content(prompt)

        # Try to parse the response as JSON
        try:
            # Clean the response text (remove markdown code blocks if present)
            response_text = response.text
            if "```json" in response_text:
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            disease_data = json.loads(response_text)

            # Process the data to ensure all items in arrays are strings
            cleaned_data = convert_to_serializable(disease_data)

            # Format the response for better display
            try:
                formatted_html = format_disease_report_html(cleaned_data)
                return {
                    "success": True,
                    "report": formatted_html,
                    "raw_data": cleaned_data,
                }
            except Exception as formatting_error:
                # If there's an error in formatting, return the raw data in plain text
                return {
                    "success": True,
                    "report": f"<pre>{json.dumps(cleaned_data, indent=2)}</pre>",
                    "error_details": str(formatting_error),
                }

        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            return {"success": True, "report": f"<pre>{response.text}</pre>"}

    except Exception as e:
        return {"success": False, "error": str(e)}
