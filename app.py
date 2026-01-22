"""
DNA Genetic Prediction Web Application
Main Flask application file - handles app setup and core page routes
"""
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, current_user
import os
import pandas as pd
from dotenv import load_dotenv

# Try to import flasgger (optional)
try:
    from flasgger import Swagger
    SWAGGER_AVAILABLE = True
except ImportError:
    SWAGGER_AVAILABLE = False

# Try to import flask-cors (optional)
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False

# Load environment variables from .env file if it exists
load_dotenv()

# Import from our modules
from models import GeneticPredictor, POPULATION_INFO, find_model_directories
from services import configure_gemini
from database import db, User, init_db, create_admin_user
from config import get_database_url, wait_for_database, get_engine_options
from config.mongodb import wait_for_mongodb, get_snp_collection

# ============================================================
# Flask App Setup
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "genetic_prediction_app_secret_key"
)

# Enable CORS for frontend communication
if CORS_AVAILABLE:
    cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    print(f"✅ CORS enabled for origins: {cors_origins}")

# Database configuration - supports both SQLite and PostgreSQL
database_url = get_database_url()
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = get_engine_options()

# Log database type being used
if 'postgresql' in database_url:
    print(f"🐘 Using PostgreSQL database")
else:
    print(f"📦 Using SQLite database")

# Wait for database in production (Docker/K8s)
if os.environ.get('FLASK_ENV') == 'production':
    if not wait_for_database():
        print("❌ Could not connect to database. Exiting...")
        exit(1)

# Wait for MongoDB and auto-seed SNP database if empty
print("🔍 Checking MongoDB SNP database...")
if wait_for_mongodb():
    try:
        collection = get_snp_collection()
        existing_count = collection.count_documents({})
        
        if existing_count == 0:
            print("🌱 MongoDB SNP database is empty. Auto-seeding...")
            # Import seed function
            import sys
            scripts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
            if scripts_path not in sys.path:
                sys.path.insert(0, scripts_path)
            
            from seed_snp_database import seed_snp_database
            if seed_snp_database(skip_existing=True):
                print("✅ SNP database auto-seeded successfully!")
            else:
                print("⚠️ SNP database seeding failed, but continuing...")
        else:
            print(f"✅ MongoDB SNP database ready ({existing_count} SNPs)")
    except Exception as e:
        print(f"⚠️ Could not check/seed MongoDB: {e}")
        print("   App will continue, but SNP features may be limited")
else:
    print("⚠️ MongoDB not available. SNP features will be limited.")

# Initialize database
init_db(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))

# Swagger API Documentation Configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "DNA Genetic Prediction API",
        "description": "API for genetic population and Gender Prediction based on SNP data",
        "version": "1.0.0",
        "contact": {"name": "DNA Prediction Team"}
    },
    "basePath": "/",
    "schemes": ["http", "https"],
    "tags": [
        {"name": "Prediction", "description": "Genetic prediction endpoints"},
        {"name": "Samples", "description": "Sample data management"},
        {"name": "SNP Query", "description": "SNP data query endpoints"},
        {"name": "Dataset", "description": "Dataset building endpoints"},
        {"name": "Agent", "description": "AI Agent chat endpoints"},
        {"name": "Upload", "description": "File upload endpoints"},
        {"name": "Analysis", "description": "SNP analysis endpoints"}
    ]
}

if SWAGGER_AVAILABLE:
    swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Register blueprints from routes
try:
    from routes import register_blueprints
    register_blueprints(app)
    print("✅ Routes registered successfully!")
except ImportError as e:
    print(f"⚠️ Could not load routes: {e}")


# Context processor to make user available in all templates
@app.context_processor
def inject_user():
    """Inject current_user into all templates"""
    return dict(current_user=current_user)


# Create database tables on first run
with app.app_context():
    db.create_all()
    
    # Check and add missing columns if needed (for existing databases)
    try:
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        
        # Get existing columns for analysis_history table
        if 'analysis_history' in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns('analysis_history')]
            
            # Columns that might be missing in older databases
            columns_to_add = {
                'physical_characteristics': 'TEXT',
                'disease_risk_report': 'TEXT',
                'user_id': 'INTEGER'
            }
            
            for col_name, col_type in columns_to_add.items():
                if col_name not in existing_columns:
                    print(f"⚠️ Adding missing column: {col_name}")
                    try:
                        db.session.execute(text(f'ALTER TABLE analysis_history ADD COLUMN {col_name} {col_type}'))
                        db.session.commit()
                        print(f"✅ Added column: {col_name}")
                    except Exception as col_err:
                        print(f"Could not add column {col_name}: {col_err}")
                        db.session.rollback()
    except Exception as migration_err:
        print(f"Migration check skipped: {migration_err}")
    
    # Create default admin user
    create_admin_user(
        username=os.environ.get('ADMIN_USERNAME', 'admin'),
        email=os.environ.get('ADMIN_EMAIL', 'admin@genovaai.com'),
        password=os.environ.get('ADMIN_PASSWORD', 'admin123')
    )
    print("✅ Database tables created successfully!")


# Set up upload folder
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY environment variable not set. AI-based predictions will not work.")
else:
    configure_gemini()

# ============================================================
# Initialize Predictors (for index and samples pages)
# ============================================================

predictor = GeneticPredictor()
gender_model_dir, ancestry_model_dir = find_model_directories()
gender_loaded = False
ancestry_loaded = False

if gender_model_dir:
    gender_loaded = predictor.load_sex_predictor(gender_model_dir)

if ancestry_model_dir:
    ancestry_loaded = predictor.load_ancestry_predictor(ancestry_model_dir)


# ============================================================
# Core Page Routes (index, samples, chat)
# ============================================================

@app.route("/")
def index():
    return render_template(
        "index.html",
        gender_loaded=gender_loaded,
        ancestry_loaded=ancestry_loaded,
        gender_model_dir=gender_model_dir,
        ancestry_model_dir=ancestry_model_dir,
    )


@app.route("/upload_model_directories", methods=["POST"])
def upload_model_directories():
    global gender_loaded, ancestry_loaded, gender_model_dir, ancestry_model_dir

    if request.method == "POST":
        sex_dir = request.form.get("gender_model_dir")
        ancestry_dir = request.form.get("ancestry_model_dir")

        if sex_dir and os.path.exists(sex_dir):
            gender_loaded = predictor.load_sex_predictor(sex_dir)
            if gender_loaded:
                gender_model_dir = sex_dir
                flash("Gender Prediction model loaded successfully!", "success")
            else:
                flash("Failed to load Gender Prediction model.", "error")

        if ancestry_dir and os.path.exists(ancestry_dir):
            ancestry_loaded = predictor.load_ancestry_predictor(ancestry_dir)
            if ancestry_loaded:
                ancestry_model_dir = ancestry_dir
                flash("Ancestry prediction model loaded successfully!", "success")
            else:
                flash("Failed to load ancestry prediction model.", "error")

    return redirect(url_for("index"))


@app.route("/snp_query", methods=["GET"])
def snp_query():
    """Page for querying specific SNP values"""
    sample_files = []
    patient_data_dir = "patient_snp_data"
    
    if os.path.exists(patient_data_dir):
        for file in os.listdir(patient_data_dir):
            if file.endswith('.csv') and not file.startswith('all_patients'):
                sample_files.append({
                    'filename': file,
                    'path': os.path.join(patient_data_dir, file)
                })
    
    if os.path.exists(app.config["UPLOAD_FOLDER"]):
        for file in os.listdir(app.config["UPLOAD_FOLDER"]):
            if file.endswith('.csv'):
                sample_files.append({
                    'filename': file,
                    'path': os.path.join(app.config["UPLOAD_FOLDER"], file)
                })
    
    available_snps = []
    snps_file = "hapmap_data/gender_prediction_data/gender_selected_snps.csv"
    if os.path.exists(snps_file):
        try:
            snps_df = pd.read_csv(snps_file)
            available_snps = snps_df['SNP'].head(100).tolist()
        except Exception as e:
            print(f"Error loading SNPs: {e}")
    
    return render_template("snp_query.html", sample_files=sample_files, available_snps=available_snps)


@app.route("/chat")
def chat_page():
    """Render the AI Chat interface"""
    try:
        import importlib.util
        if importlib.util.find_spec("agent") is not None:
            return render_template("chat.html")
        else:
            flash("AI Agent is not available. Please install required dependencies.", "error")
            return redirect(url_for("index"))
    except ImportError:
        flash("AI Agent is not available. Please install required dependencies.", "error")
        return redirect(url_for("index"))


# ============================================================
# Static File Routes
# ============================================================

@app.route("/plots/<path:filename>")
def serve_plot(filename):
    """Serve plot files from the plots directory"""
    plots_dir = os.path.join(os.getcwd(), "plots")
    return send_from_directory(plots_dir, filename)


@app.route("/viz/<path:filename>")
def serve_visualization(filename):
    """Serve visualization files from the visualizations directory"""
    viz_dir = os.path.join(os.getcwd(), "visualizations")
    return send_from_directory(viz_dir, filename)


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    """Serve files from the uploads directory (including generated images)"""
    uploads_dir = os.path.join(os.getcwd(), "uploads")
    return send_from_directory(uploads_dir, filename)


# ============================================================
# Error Handlers
# ============================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    app.run(debug=True, port=5001)
