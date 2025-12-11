"""
Routes Package - Organized API endpoints and page routes
"""
from flask import Blueprint

# Create API blueprints (with /api prefix)
samples_bp = Blueprint('samples', __name__, url_prefix='/api/samples')
analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')
predictions_bp = Blueprint('predictions', __name__, url_prefix='/api/predictions')
agent_bp = Blueprint('agent', __name__, url_prefix='/api/agent')

# Import route modules to register them
from . import samples_routes
from . import analysis_routes
from . import predictions_routes
from . import agent_routes
from . import snp_routes  # SNP query and dataset builder routes
from . import upload_routes  # File upload and processing routes
from . import dashboard_routes  # Dashboard and map routes

# Import page blueprints (no URL prefix)
from .upload_routes import upload_bp
from .predictions_routes import predictions_page_bp
from .analysis_routes import analysis_page_bp
from .dashboard_routes import dashboard_bp

# Import new feature blueprints
from .auth_routes import auth_bp
from .history_routes import history_bp
from .snp_database_routes import snp_database_bp
from .risk_calculator_routes import risk_calculator_bp
from .notifications_routes import notifications_bp
from .pages_routes import pages_bp  # Static pages (Privacy, Terms, Contact)


def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    # API blueprints
    app.register_blueprint(samples_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(agent_bp)
    
    # Page blueprints (no prefix - direct routes)
    app.register_blueprint(upload_bp)
    app.register_blueprint(predictions_page_bp)
    app.register_blueprint(analysis_page_bp)
    app.register_blueprint(dashboard_bp)  # Dashboard and ancestry map
    
    # New feature blueprints
    app.register_blueprint(auth_bp)  # Authentication routes
    app.register_blueprint(history_bp)  # History routes
    app.register_blueprint(snp_database_bp)  # SNP Database routes
    app.register_blueprint(risk_calculator_bp)  # Risk Calculator routes
    app.register_blueprint(notifications_bp)  # Notifications routes
    app.register_blueprint(pages_bp)  # Static pages (Privacy, Terms, Contact)


