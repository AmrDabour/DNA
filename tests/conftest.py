"""
Pytest Configuration and Fixtures
Global fixtures for Flask app, database, and test utilities
"""
import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['FLASK_SECRET_KEY'] = 'test-secret-key-for-testing'


# ============================================================
# Flask Application Fixtures
# ============================================================

@pytest.fixture(scope='session')
def app():
    """Create Flask application for testing"""
    from flask import Flask, render_template
    from flask_login import LoginManager
    from database import db, User
    
    # Create test app
    test_app = Flask(__name__, 
                     template_folder=str(project_root / 'web' / 'templates'),
                     static_folder=str(project_root / 'web' / 'static'))
    
    test_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'LOGIN_DISABLED': False,
        'UPLOAD_FOLDER': str(project_root / 'tests' / 'fixtures'),
    })
    
    # Initialize extensions
    db.init_app(test_app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(test_app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # Register blueprints
    try:
        from routes import register_blueprints
        register_blueprints(test_app)
    except ImportError:
        pass
    
    # Add index route (normally in app.py)
    @test_app.route('/')
    def index():
        return render_template('index.html', 
                               gender_loaded=False, 
                               ancestry_loaded=False,
                               gender_model_dir=None,
                               ancestry_model_dir=None)
    
    # Create tables
    with test_app.app_context():
        db.create_all()
    
    yield test_app
    
    # Cleanup
    with test_app.app_context():
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing"""
    from database import db
    
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        yield db.session
        
        # Cleanup after test
        db.session.rollback()
        
        # Clear all data from tables
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()


@pytest.fixture(scope='function')
def runner(app):
    """Create Flask CLI runner"""
    return app.test_cli_runner()


# ============================================================
# User Fixtures
# ============================================================

@pytest.fixture
def sample_user(app, db_session):
    """Create a sample user for testing"""
    from database import User
    
    user = User(
        username='testuser',
        email='testuser@example.com',
        full_name='Test User',
        is_active=True,
        is_admin=False
    )
    user.set_password('testpassword123')
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture
def admin_user(app, db_session):
    """Create an admin user for testing"""
    from database import User
    
    admin = User(
        username='admin',
        email='admin@example.com',
        full_name='Admin User',
        is_active=True,
        is_admin=True
    )
    admin.set_password('adminpassword123')
    db_session.add(admin)
    db_session.commit()
    
    return admin


@pytest.fixture
def authenticated_client(client, sample_user):
    """Create an authenticated test client"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(sample_user.id)
        sess['_fresh'] = True
    return client


# ============================================================
# Test Data Fixtures
# ============================================================

@pytest.fixture(scope='session')
def fixtures_dir():
    """Get path to fixtures directory"""
    return Path(__file__).parent / 'fixtures'


@pytest.fixture(scope='session')
def sample_snp_file(fixtures_dir):
    """Get path to sample SNP data file"""
    return fixtures_dir / 'sample_snp_data.csv'


@pytest.fixture
def sample_snp_data():
    """Sample SNP data as dictionary"""
    return {
        'CHR': [1, 1, 1, 2, 2],
        'SNP': ['rs2185539', 'rs11510103', 'rs4040617', 'rs6718526', 'rs1800497'],
        'GEN_DIST': [0, 0, 0, 0, 0],
        'POS': [556738, 557616, 557823, 1234567, 2345678],
        'Allele1': ['A', 'A', 'G', 'C', 'T'],
        'Allele2': ['A', 'G', 'G', 'C', 'A'],
        'Patient_ID': ['NA12345', 'NA12345', 'NA12345', 'NA12345', 'NA12345'],
        'Population': ['CEU', 'CEU', 'CEU', 'CEU', 'CEU'],
        'Sex': [1, 1, 1, 1, 1]
    }


@pytest.fixture
def temp_snp_file(sample_snp_data, tmp_path):
    """Create a temporary SNP CSV file"""
    import pandas as pd
    
    df = pd.DataFrame(sample_snp_data)
    file_path = tmp_path / 'test_sample.csv'
    df.to_csv(file_path, index=False)
    
    return file_path


# ============================================================
# Mock Fixtures
# ============================================================

@pytest.fixture
def mock_gemini():
    """Mock Gemini API responses"""
    with patch('google.generativeai.GenerativeModel') as mock:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Mocked AI response for testing"
        mock_model.generate_content.return_value = mock_response
        mock.return_value = mock_model
        yield mock


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB connection"""
    with patch('config.mongodb.get_mongo_client') as mock_client:
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_collection.find.return_value = []
        mock_collection.find_one.return_value = None
        mock_collection.count_documents.return_value = 0
        mock_db.__getitem__.return_value = mock_collection
        mock_client.return_value.__getitem__.return_value = mock_db
        yield mock_client


@pytest.fixture
def mock_vep_service():
    """Mock VEP service for testing"""
    with patch('services.vep_service.VEPService') as mock:
        mock_instance = MagicMock()
        mock_instance.annotate_rsids.return_value = {
            'success': True,
            'results': [],
            'cached': 0,
            'fetched': 0
        }
        mock_instance.enabled = True
        mock.return_value = mock_instance
        yield mock


# ============================================================
# Analysis History Fixtures
# ============================================================

@pytest.fixture
def sample_analysis(app, db_session, sample_user):
    """Create a sample analysis history entry"""
    from database import AnalysisHistory
    import json
    
    analysis = AnalysisHistory(
        user_id=sample_user.id,
        sample_id='NA12345',
        analysis_type='combined',
        gender_prediction='Male',
        gender_confidence=0.95,
        ancestry_prediction='European',
        ancestry_code='CEU',
        ancestry_confidence=0.87,
        file_name='test_sample.csv',
        snp_count=5000,
        processing_time=2.5,
        status='completed'
    )
    analysis.set_full_results({
        'gender': {'prediction': 'Male', 'confidence': 0.95},
        'ancestry': {'prediction': 'European', 'code': 'CEU', 'confidence': 0.87}
    })
    
    db_session.add(analysis)
    db_session.commit()
    
    return analysis


# ============================================================
# Population Data Fixtures
# ============================================================

@pytest.fixture
def population_info():
    """Standard population information"""
    return {
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


# ============================================================
# Utility Functions for Tests
# ============================================================

def login_user(client, username, password):
    """Helper function to log in a user"""
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


def logout_user(client):
    """Helper function to log out a user"""
    return client.get('/logout', follow_redirects=True)

