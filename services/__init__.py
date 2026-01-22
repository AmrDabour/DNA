"""
Services Module
Contains service functions for GenovaAI
"""
import os


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


__all__ = ['configure_gemini']
