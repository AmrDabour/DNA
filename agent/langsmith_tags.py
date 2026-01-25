"""
LangSmith Tagging Constants and Utilities
"""
from enum import Enum
from typing import List, Optional
import os


class TraceTags(str, Enum):
    """Standard tags for DNA Agent traces"""
    
    # Environment tags
    PRODUCTION = "env:production"
    STAGING = "env:staging"
    DEVELOPMENT = "env:development"
    
    # Feature tags
    ANALYSIS = "feature:analysis"
    PREDICTION = "feature:prediction"
    IMAGE_GEN = "feature:image_generation"
    EDUCATION = "feature:education"
    COMPARISON = "feature:comparison"
    
    # Tool category tags
    TOOL_SNP = "tool:snp"
    TOOL_SAMPLE = "tool:sample"
    TOOL_DISEASE = "tool:disease"
    TOOL_TRAITS = "tool:traits"
    TOOL_IMAGE = "tool:image"
    
    # Quality tags
    HIGH_CONFIDENCE = "quality:high_confidence"
    LOW_CONFIDENCE = "quality:low_confidence"
    NEEDS_REVIEW = "quality:needs_review"
    
    # Response type tags
    QUICK_RESPONSE = "response:quick"
    DETAILED_RESPONSE = "response:detailed"
    ERROR_RESPONSE = "response:error"


def get_environment_tag() -> str:
    """Get the current environment tag based on ENV variable"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    tag_map = {
        "production": TraceTags.PRODUCTION,
        "prod": TraceTags.PRODUCTION,
        "staging": TraceTags.STAGING,
        "stage": TraceTags.STAGING,
        "development": TraceTags.DEVELOPMENT,
        "dev": TraceTags.DEVELOPMENT,
    }
    
    return tag_map.get(env, TraceTags.DEVELOPMENT).value


def get_tags_for_tools(tool_names: List[str]) -> List[str]:
    """Generate tags based on tools used"""
    tags = set()
    
    tool_tag_map = {
        # Analysis tools
        "analyze_snp_file": [TraceTags.ANALYSIS, TraceTags.TOOL_SNP],
        "get_snp_statistics": [TraceTags.ANALYSIS, TraceTags.TOOL_SNP],
        "query_snp": [TraceTags.ANALYSIS, TraceTags.TOOL_SNP],
        "query_multiple_snps": [TraceTags.ANALYSIS, TraceTags.TOOL_SNP],
        
        # Sample tools
        "list_available_samples": [TraceTags.TOOL_SAMPLE],
        "get_sample_info": [TraceTags.TOOL_SAMPLE],
        "compare_samples": [TraceTags.COMPARISON, TraceTags.TOOL_SAMPLE],
        
        # Prediction tools
        "get_disease_risk_from_sample": [TraceTags.PREDICTION, TraceTags.TOOL_DISEASE],
        "assess_genetic_disease_risk": [TraceTags.PREDICTION, TraceTags.TOOL_DISEASE],
        "predict_physical_characteristics": [TraceTags.PREDICTION, TraceTags.TOOL_TRAITS],
        "get_physical_traits_from_sample": [TraceTags.PREDICTION, TraceTags.TOOL_TRAITS],
        "full_genetic_report": [TraceTags.PREDICTION, TraceTags.TOOL_DISEASE, TraceTags.TOOL_TRAITS],
        
        # Image tools
        "generate_person_image": [TraceTags.IMAGE_GEN, TraceTags.TOOL_IMAGE],
        "generate_image_from_sample": [TraceTags.IMAGE_GEN, TraceTags.TOOL_IMAGE],
        
        # Educational tools
        "get_genetic_fun_facts": [TraceTags.EDUCATION],
        "explain_snp_significance": [TraceTags.EDUCATION, TraceTags.TOOL_SNP],
        "get_ancestry_deep_dive": [TraceTags.EDUCATION],
        "get_trait_predictions_guide": [TraceTags.EDUCATION],
        "generate_genetic_summary_card": [TraceTags.PREDICTION],
        
        # Comparison tools
        "calculate_genetic_relatedness": [TraceTags.COMPARISON, TraceTags.TOOL_SAMPLE],
    }
    
    for tool_name in tool_names:
        if tool_name in tool_tag_map:
            for tag in tool_tag_map[tool_name]:
                tags.add(tag.value)
    
    return list(tags)


def get_quality_tag(confidence_score: float) -> str:
    """Get quality tag based on confidence score"""
    if confidence_score >= 0.8:
        return TraceTags.HIGH_CONFIDENCE.value
    elif confidence_score >= 0.5:
        return TraceTags.LOW_CONFIDENCE.value
    else:
        return TraceTags.NEEDS_REVIEW.value


def build_run_tags(
    tools_used: Optional[List[str]] = None,
    confidence: Optional[float] = None,
    is_error: bool = False,
    custom_tags: Optional[List[str]] = None
) -> List[str]:
    """
    Build a complete list of tags for a run
    
    Args:
        tools_used: List of tool names used in the run
        confidence: Confidence score of the response
        is_error: Whether the run resulted in an error
        custom_tags: Additional custom tags
    
    Returns:
        List of tag strings
    """
    tags = []
    
    # Add environment tag
    tags.append(get_environment_tag())
    
    # Add tool-based tags
    if tools_used:
        tags.extend(get_tags_for_tools(tools_used))
    
    # Add quality tag
    if confidence is not None:
        tags.append(get_quality_tag(confidence))
    
    # Add error tag
    if is_error:
        tags.append(TraceTags.ERROR_RESPONSE.value)
    
    # Add custom tags
    if custom_tags:
        tags.extend(custom_tags)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)
    
    return unique_tags



