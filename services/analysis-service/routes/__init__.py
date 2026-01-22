# Analysis Service Routes Package
from .analysis_routes import analysis_bp
from .history_routes import history_bp
from .upload_routes import upload_bp
from .snp_routes import snp_bp

__all__ = ['analysis_bp', 'history_bp', 'upload_bp', 'snp_bp']
