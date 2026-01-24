"""
LangChain Tools - Simplified tools that call API endpoints
"""
from typing import Dict, List, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import requests
import os

# Base URL for API calls (configurable)
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:5001")

# Population information
POPULATION_INFO = {
    "ASW": {"code": "A", "description": "African ancestry in Southwest USA"},
    "CEU": {"code": "C", "description": "Utah residents with Northern and Western European ancestry from the CEPH collection"},
    "CHB": {"code": "H", "description": "Han Chinese in Beijing, China"},
    "CHD": {"code": "D", "description": "Chinese in Metropolitan Denver, Colorado"},
    "GIH": {"code": "G", "description": "Gujarati Indians in Houston, Texas"},
    "JPT": {"code": "J", "description": "Japanese in Tokyo, Japan"},
    "LWK": {"code": "L", "description": "Luhya in Webuye, Kenya"},
    "MEX": {"code": "M", "description": "Mexican ancestry in Los Angeles, California"},
    "MKK": {"code": "K", "description": "Maasai in Kinyawa, Kenya"},
    "TSI": {"code": "T", "description": "Tuscan in Italy"},
    "YRI": {"code": "Y", "description": "Yoruban in Ibadan, Nigeria (West Africa)"},
}


# ============================================================
# Input Schemas
# ============================================================

class SNPQueryInput(BaseModel):
    """Input schema for SNP query tool"""
    sample_file: str = Field(description="Path to the sample CSV file")
    snp_id: str = Field(description="The SNP ID to query (e.g., rs12345)")


class MultipleSNPQueryInput(BaseModel):
    """Input schema for multiple SNP query tool"""
    sample_file: str = Field(description="Path to the sample CSV file")
    snp_ids: List[str] = Field(description="List of SNP IDs to query")


class SampleFileInput(BaseModel):
    """Input schema for sample file operations"""
    sample_file: str = Field(description="Path to the sample CSV file")


class CompareSamplesInput(BaseModel):
    """Input schema for comparing samples"""
    sample_file_1: str = Field(description="Path to first sample CSV file")
    sample_file_2: str = Field(description="Path to second sample CSV file")


class PredictionInput(BaseModel):
    """Input schema for predictions with gender and population"""
    gender: str = Field(description="The gender (Male or Female)")
    population: str = Field(description="The population code (e.g., CHD, CEU, YRI)")


class ImageGenerationInput(BaseModel):
    """Input schema for generating person images"""
    gender: str = Field(description="The gender (Male or Female)")
    population: str = Field(description="The population code (e.g., CHD, CEU, YRI)")
    patient_id: str = Field(default="Unknown", description="Optional patient ID for the image")


class SNPExplainInput(BaseModel):
    """Input schema for explaining SNP significance"""
    snp_id: str = Field(description="The SNP ID to explain (e.g., rs12345)")


class GeneticFactsInput(BaseModel):
    """Input schema for genetic fun facts"""
    topic: str = Field(default="general", description="Topic for facts: general, ancestry, health, traits, evolution")


# ============================================================
# Helper function
# ============================================================

def call_api(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Make API call to the Flask backend"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=120)
        else:
            response = requests.post(url, json=data, timeout=120)
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Could not connect to API server"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# Sample Tools
# ============================================================

@tool
def list_available_samples() -> Dict[str, Any]:
    """
    List all available genetic sample files in the system.
    Use this to find samples that can be analyzed.
    
    Returns:
        dict: Contains list of samples with their metadata (patient_id, population, gender)
    """
    return call_api("/api/samples/list")


@tool
def get_population_info(population_code: str) -> Dict[str, Any]:
    """
    Get detailed information about a genetic population.
    
    Args:
        population_code: The population code (e.g., CEU, YRI, JPT, CHB)
        
    Returns:
        dict: Population description and details
    """
    return call_api(f"/api/samples/population/{population_code}")


@tool
def list_all_populations() -> Dict[str, Any]:
    """
    List all known genetic populations in the system.
    Use this to get information about all supported population groups.
    
    Returns:
        dict: All populations with their codes and descriptions
    """
    return call_api("/api/samples/populations")


@tool(args_schema=SampleFileInput)
def get_sample_info(sample_file: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific sample file.
    
    Args:
        sample_file: Path to the sample CSV file
        
    Returns:
        dict: Sample information including patient ID, population, gender, and SNP count
    """
    return call_api("/api/samples/info", "POST", {"sample_file": sample_file})


@tool(args_schema=CompareSamplesInput)
def compare_samples(sample_file_1: str, sample_file_2: str) -> Dict[str, Any]:
    """
    Compare genetic data between two samples.
    Useful for finding genetic similarities or differences.
    
    Args:
        sample_file_1: Path to the first sample CSV file
        sample_file_2: Path to the second sample CSV file
        
    Returns:
        dict: Comparison results including common SNPs and differences
    """
    return call_api("/api/samples/compare", "POST", {
        "sample_file_1": sample_file_1,
        "sample_file_2": sample_file_2
    })


# ============================================================
# Analysis Tools
# ============================================================

@tool(args_schema=SNPQueryInput)
def query_snp(sample_file: str, snp_id: str) -> Dict[str, Any]:
    """
    Query a specific SNP (Single Nucleotide Polymorphism) value from a sample file.
    
    Args:
        sample_file: Path to the sample CSV file
        snp_id: The SNP ID to query (e.g., rs12345)
        
    Returns:
        dict: SNP information including chromosome, position, and genotype
    """
    return call_api("/api/analysis/snp", "POST", {
        "sample_file": sample_file,
        "snp_id": snp_id
    })


@tool(args_schema=MultipleSNPQueryInput)
def query_multiple_snps(sample_file: str, snp_ids: List[str]) -> Dict[str, Any]:
    """
    Query multiple SNP values from a sample file at once.
    
    Args:
        sample_file: Path to the sample CSV file
        snp_ids: List of SNP IDs to query
        
    Returns:
        dict: Results for all requested SNPs
    """
    return call_api("/api/analysis/snp/multiple", "POST", {
        "sample_file": sample_file,
        "snp_ids": snp_ids
    })


@tool(args_schema=SampleFileInput)
def analyze_snp_file(sample_file: str) -> Dict[str, Any]:
    """
    Perform complete genetic analysis on an uploaded SNP file.
    Analyzes the file and reports gender, ancestry/population, and genetic statistics.
    Use this tool when user uploads a new SNP file or asks to analyze a sample.
    
    Args:
        sample_file: Path to the patient sample CSV file
        
    Returns:
        dict: Complete analysis with Gender Prediction, ancestry prediction, and sample statistics
    """
    return call_api("/api/analysis/analyze", "POST", {"sample_file": sample_file})


@tool(args_schema=SampleFileInput)
def get_snp_statistics(sample_file: str) -> Dict[str, Any]:
    """
    Get detailed statistics about SNPs in a sample file.
    Provides chromosome distribution, allele frequencies, and quality metrics.
    
    Args:
        sample_file: Path to the patient sample CSV file
        
    Returns:
        dict: Detailed SNP statistics
    """
    return call_api("/api/analysis/statistics", "POST", {"sample_file": sample_file})


# ============================================================
# Prediction Tools
# ============================================================

@tool(args_schema=PredictionInput)
def predict_physical_characteristics(gender: str, population: str) -> Dict[str, Any]:
    """
    Predict likely physical characteristics based on gender and ancestry.
    Uses AI to generate statistical predictions about hair, eyes, skin, facial features, and body structure.
    
    Args:
        gender: The Biological Gender (Male or Female)
        population: The population/ancestry code (e.g., CHD, CEU, YRI, JPT)
        
    Returns:
        dict: Physical characteristics predictions including hair, eyes, skin, facial features
    """
    return call_api("/api/predictions/physical", "POST", {
        "gender": gender,
        "population": population
    })


@tool(args_schema=PredictionInput)
def assess_genetic_disease_risk(gender: str, population: str) -> Dict[str, Any]:
    """
    Assess potential genetic disease risks based on gender and ancestry.
    Uses AI to provide information about diseases that have higher prevalence in certain populations.
    
    Args:
        gender: The Biological Gender (Male or Female)
        population: The population/ancestry code (e.g., CHD, CEU, YRI, JPT)
        
    Returns:
        dict: Disease risk assessment with conditions, risk levels, and recommendations
    """
    return call_api("/api/predictions/disease-risk", "POST", {
        "gender": gender,
        "population": population
    })


@tool(args_schema=SampleFileInput)
def get_physical_traits_from_sample(sample_file: str) -> Dict[str, Any]:
    """
    Get physical characteristics prediction directly from a sample file.
    Automatically extracts gender and population from the file and performs the prediction.
    Use this when user asks for physical characteristics after analyzing a sample.
    
    Args:
        sample_file: Path to the sample CSV file
        
    Returns:
        dict: Physical characteristics predictions
    """
    return call_api("/api/predictions/physical/from-sample", "POST", {"sample_file": sample_file})


@tool(args_schema=SampleFileInput)
def get_disease_risk_from_sample(sample_file: str) -> Dict[str, Any]:
    """
    Get genetic disease risk assessment directly from a sample file.
    Automatically extracts gender and population from the file and performs the assessment.
    Use this when user asks for disease risk after analyzing a sample.
    
    Args:
        sample_file: Path to the sample CSV file
        
    Returns:
        dict: Disease risk assessment with conditions, risk levels, and recommendations
    """
    return call_api("/api/predictions/disease-risk/from-sample", "POST", {"sample_file": sample_file})


@tool(args_schema=SampleFileInput)
def full_genetic_report(sample_file: str) -> Dict[str, Any]:
    """
    Generate a complete genetic report including analysis, physical characteristics, and disease risks.
    This is the most comprehensive analysis tool - use it when user wants everything.
    
    Args:
        sample_file: Path to the sample CSV file
        
    Returns:
        dict: Complete genetic report with all analyses
    """
    return call_api("/api/predictions/full-report", "POST", {"sample_file": sample_file})


# ============================================================
# Image Generation Tools
# ============================================================

@tool(args_schema=ImageGenerationInput)
def generate_person_image(gender: str, population: str, patient_id: str = "Unknown") -> Dict[str, Any]:
    """
    Generate an AI portrait image of a person based on their predicted gender and ancestry.
    Creates a realistic portrait showing typical physical characteristics for the population.
    Use this after analyzing a sample to visualize what the person might look like.
    
    Args:
        gender: The gender (Male or Female)
        population: The population/ancestry code (e.g., CHD, CEU, YRI, JPT)
        patient_id: Optional patient ID for naming the image
        
    Returns:
        dict: Contains image_data (base64), image_path, and description
    """
    return call_api("/api/predictions/generate-person-image", "POST", {
        "gender": gender,
        "population": population,
        "patient_id": patient_id
    })


@tool(args_schema=SampleFileInput)
def generate_image_from_sample(sample_file: str) -> Dict[str, Any]:
    """
    Generate an AI portrait image directly from a sample file.
    Automatically extracts gender and population from the analyzed sample.
    Use this when user wants to see what someone with this genetic profile might look like.
    
    Args:
        sample_file: Path to the sample CSV file
        
    Returns:
        dict: Contains image_data (base64), image_path, and description
    """
    return call_api("/api/predictions/generate-image-from-sample", "POST", {"sample_file": sample_file})


# ============================================================
# Fun & Educational Tools
# ============================================================

@tool(args_schema=GeneticFactsInput)
def get_genetic_fun_facts(topic: str = "general") -> Dict[str, Any]:
    """
    Get interesting and fun facts about genetics.
    Great for education and making genetic concepts more engaging.
    
    Args:
        topic: Topic for facts - "general", "ancestry", "health", "traits", or "evolution"
        
    Returns:
        dict: Fun facts about genetics with explanations
    """
    return call_api("/api/predictions/fun-facts", "POST", {"topic": topic})


@tool(args_schema=SNPExplainInput)
def explain_snp_significance(snp_id: str) -> Dict[str, Any]:
    """
    Explain the significance and known associations of a specific SNP.
    Provides educational information about what the SNP is known for.
    Use this when user asks about a specific SNP's meaning or importance.
    
    Args:
        snp_id: The SNP ID to explain (e.g., rs12345, rs1800497)
        
    Returns:
        dict: Explanation of the SNP, its gene, and known associations
    """
    return call_api("/api/predictions/explain-snp", "POST", {"snp_id": snp_id})


@tool(args_schema=PredictionInput)
def get_ancestry_deep_dive(gender: str, population: str) -> Dict[str, Any]:
    """
    Get a deep dive into ancestral origins and migration history.
    Provides fascinating details about population genetics and historical context.
    
    Args:
        gender: The gender (Male or Female)
        population: The population code (e.g., CHD, CEU, YRI)
        
    Returns:
        dict: Detailed ancestry information with historical context
    """
    return call_api("/api/predictions/ancestry-deep-dive", "POST", {
        "gender": gender,
        "population": population
    })


@tool(args_schema=CompareSamplesInput)
def calculate_genetic_relatedness(sample_file_1: str, sample_file_2: str) -> Dict[str, Any]:
    """
    Calculate genetic relatedness/similarity between two samples.
    Fun tool to see how genetically similar two individuals are.
    Can estimate relationship probability (siblings, cousins, unrelated).
    
    Args:
        sample_file_1: Path to first sample CSV file
        sample_file_2: Path to second sample CSV file
        
    Returns:
        dict: Genetic similarity score and estimated relationship
    """
    return call_api("/api/predictions/genetic-relatedness", "POST", {
        "sample_file_1": sample_file_1,
        "sample_file_2": sample_file_2
    })


@tool
def get_trait_predictions_guide() -> Dict[str, Any]:
    """
    Get a guide about what genetic traits can be predicted from SNP data.
    Lists traits that have genetic associations and their accuracy.
    Educational tool to understand the scope of genetic predictions.
    
    Returns:
        dict: Guide to predictable genetic traits with explanations
    """
    return call_api("/api/predictions/traits-guide", "GET")


@tool(args_schema=SampleFileInput)
def generate_genetic_summary_card(sample_file: str) -> Dict[str, Any]:
    """
    Generate a beautiful summary card with key genetic insights.
    Creates a concise, shareable overview of genetic analysis results.
    Perfect for a quick snapshot of genetic profile.
    
    Args:
        sample_file: Path to the sample CSV file
        
    Returns:
        dict: Formatted genetic summary card with key metrics
    """
    return call_api("/api/predictions/summary-card", "POST", {"sample_file": sample_file})


# ============================================================
# Tool Collection
# ============================================================

def get_all_tools():
    """Get all available tools for the agent"""
    return [
        # Sample Tools
        list_available_samples,
        get_population_info,
        list_all_populations,
        get_sample_info,
        compare_samples,
        # Analysis Tools
        query_snp,
        query_multiple_snps,
        analyze_snp_file,
        get_snp_statistics,
        # Prediction Tools
        predict_physical_characteristics,
        assess_genetic_disease_risk,
        get_physical_traits_from_sample,
        get_disease_risk_from_sample,
        full_genetic_report,
        # Image Generation Tools
        generate_person_image,
        generate_image_from_sample,
        # Fun & Educational Tools
        get_genetic_fun_facts,
        explain_snp_significance,
        get_ancestry_deep_dive,
        calculate_genetic_relatedness,
        get_trait_predictions_guide,
        generate_genetic_summary_card,
    ]


def get_tools_description() -> str:
    """Get a formatted description of all available tools"""
    tools = get_all_tools()
    descriptions = []
    
    for t in tools:
        desc = f"• **{t.name}**: {t.description.split('.')[0]}."
        descriptions.append(desc)
    
    return "\n".join(descriptions)
