"""
Agent Configuration - Environment variables and settings
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration for the DNA Agent"""
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
    
    # Model settings
    MODEL_NAME = os.getenv("AGENT_MODEL", "gemini-2.5-flash")
    TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("AGENT_MAX_TOKENS", "2048"))
    
    # Memory settings
    MEMORY_WINDOW_SIZE = int(os.getenv("MEMORY_WINDOW_SIZE", "20"))
    
    # File paths
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
    PATIENT_DATA_DIR = os.getenv("PATIENT_DATA_DIR", "./patient_snp_data")
    gender_model_dir = os.getenv("gender_model_dir", "./hapmap_data/gender_prediction_data")
    ANCESTRY_MODEL_DIR = os.getenv("ANCESTRY_MODEL_DIR", "./hapmap_data/Model_region")
    
    # Agent settings
    MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
    TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT", "120"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY and not cls.GOOGLE_AI_API_KEY:
            raise ValueError("GEMINI_API_KEY or GOOGLE_AI_API_KEY is required")
        return True
    
    @classmethod
    def get_api_key(cls):
        """Get the first available API key"""
        return cls.GEMINI_API_KEY or cls.GOOGLE_AI_API_KEY


config = Config()

