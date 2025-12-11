"""
Services Package - External service integrations
"""
from .gemini_service import (
    get_physical_characteristics,
    get_genetic_disease_risk,
    configure_gemini
)

__all__ = [
    'get_physical_characteristics',
    'get_genetic_disease_risk',
    'configure_gemini'
]
