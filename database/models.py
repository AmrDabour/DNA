"""
Database Models - SQLAlchemy models for Users, Analysis History, and SNP Info
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150))
    avatar_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    analyses = db.relationship('AnalysisHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_analysis_count(self):
        """Get total number of analyses by this user"""
        return self.analyses.count()
    
    def get_recent_analyses(self, limit=5):
        """Get recent analyses"""
        return self.analyses.order_by(AnalysisHistory.created_at.desc()).limit(limit).all()
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'analysis_count': self.get_analysis_count(),
            'is_admin': self.is_admin
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class AnalysisHistory(db.Model):
    """Model to store analysis history"""
    __tablename__ = 'analysis_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    sample_id = db.Column(db.String(100), nullable=False, index=True)
    analysis_type = db.Column(db.String(50), nullable=False)  # 'combined', 'gender', 'ancestry', 'physical', 'disease_risk'
    
    # Prediction Results
    gender_prediction = db.Column(db.String(20))
    gender_confidence = db.Column(db.Float)
    gender_correct = db.Column(db.Boolean)
    
    ancestry_prediction = db.Column(db.String(100))
    ancestry_code = db.Column(db.String(10))
    ancestry_confidence = db.Column(db.Float)
    ancestry_correct = db.Column(db.Boolean)
    
    # Full results as JSON
    full_results = db.Column(db.Text)  # JSON string
    physical_characteristics = db.Column(db.Text)  # HTML/Text
    disease_risk_report = db.Column(db.Text)  # HTML/Text
    
    # Metadata
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    snp_count = db.Column(db.Integer)
    processing_time = db.Column(db.Float)
    
    # Status
    status = db.Column(db.String(20), default='completed')  # 'pending', 'processing', 'completed', 'failed'
    error_message = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Tags for organization
    tags = db.Column(db.String(500))  # Comma-separated tags
    notes = db.Column(db.Text)
    is_starred = db.Column(db.Boolean, default=False)
    
    def set_full_results(self, results_dict):
        """Store full results as JSON"""
        self.full_results = json.dumps(results_dict)
    
    def get_full_results(self):
        """Retrieve full results as dictionary"""
        if self.full_results:
            return json.loads(self.full_results)
        return {}
    
    def add_tag(self, tag):
        """Add a tag to the analysis"""
        current_tags = self.get_tags()
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = ','.join(current_tags)
    
    def remove_tag(self, tag):
        """Remove a tag from the analysis"""
        current_tags = self.get_tags()
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags = ','.join(current_tags)
    
    def get_tags(self):
        """Get list of tags"""
        if self.tags:
            return [t.strip() for t in self.tags.split(',') if t.strip()]
        return []
    
    def to_dict(self):
        """Convert analysis to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sample_id': self.sample_id,
            'analysis_type': self.analysis_type,
            'gender_prediction': self.gender_prediction,
            'gender_confidence': self.gender_confidence,
            'gender_correct': self.gender_correct,
            'ancestry_prediction': self.ancestry_prediction,
            'ancestry_code': self.ancestry_code,
            'ancestry_confidence': self.ancestry_confidence,
            'ancestry_correct': self.ancestry_correct,
            'physical_characteristics': self.physical_characteristics,
            'disease_risk_report': self.disease_risk_report,
            'file_name': self.file_name,
            'snp_count': self.snp_count,
            'processing_time': self.processing_time,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'tags': self.get_tags(),
            'notes': self.notes,
            'is_starred': self.is_starred
        }
    
    def __repr__(self):
        return f'<AnalysisHistory {self.sample_id} - {self.analysis_type}>'


class SNPInfo(db.Model):
    """Model to store SNP database information"""
    __tablename__ = 'snp_info'
    
    id = db.Column(db.Integer, primary_key=True)
    rs_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    chromosome = db.Column(db.String(5), index=True)
    position = db.Column(db.Integer)
    gene_name = db.Column(db.String(50), index=True)
    gene_symbol = db.Column(db.String(20))
    
    # Allele information
    ref_allele = db.Column(db.String(10))
    alt_allele = db.Column(db.String(10))
    minor_allele = db.Column(db.String(10))
    maf = db.Column(db.Float)  # Minor Allele Frequency
    
    # Functional information
    function_class = db.Column(db.String(50))  # intron, exon, missense, synonymous, etc.
    clinical_significance = db.Column(db.String(100))
    
    # Associated traits/diseases
    associated_traits = db.Column(db.Text)  # JSON array
    disease_associations = db.Column(db.Text)  # JSON array
    
    # Risk information
    risk_allele = db.Column(db.String(10))
    odds_ratio = db.Column(db.Float)
    population_specific = db.Column(db.String(100))
    
    # Additional info
    description = db.Column(db.Text)
    pubmed_ids = db.Column(db.Text)  # Comma-separated PubMed IDs
    
    # Source and timestamps
    source = db.Column(db.String(50))  # dbSNP, ClinVar, GWAS Catalog, etc.
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_associated_traits(self):
        """Get list of associated traits"""
        if self.associated_traits:
            return json.loads(self.associated_traits)
        return []
    
    def set_associated_traits(self, traits_list):
        """Set associated traits from list"""
        self.associated_traits = json.dumps(traits_list)
    
    def get_disease_associations(self):
        """Get list of disease associations"""
        if self.disease_associations:
            return json.loads(self.disease_associations)
        return []
    
    def set_disease_associations(self, diseases_list):
        """Set disease associations from list"""
        self.disease_associations = json.dumps(diseases_list)
    
    def to_dict(self):
        """Convert SNP info to dictionary"""
        return {
            'id': self.id,
            'rs_id': self.rs_id,
            'chromosome': self.chromosome,
            'position': self.position,
            'gene_name': self.gene_name,
            'gene_symbol': self.gene_symbol,
            'ref_allele': self.ref_allele,
            'alt_allele': self.alt_allele,
            'minor_allele': self.minor_allele,
            'maf': self.maf,
            'function_class': self.function_class,
            'clinical_significance': self.clinical_significance,
            'associated_traits': self.get_associated_traits(),
            'disease_associations': self.get_disease_associations(),
            'risk_allele': self.risk_allele,
            'odds_ratio': self.odds_ratio,
            'population_specific': self.population_specific,
            'description': self.description,
            'source': self.source
        }
    
    def __repr__(self):
        return f'<SNPInfo {self.rs_id}>'


class Notification(db.Model):
    """Model to store user notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    notification_type = db.Column(db.String(50))  # 'analysis_complete', 'system', 'warning', 'info'
    
    # Related analysis if applicable
    analysis_id = db.Column(db.Integer, db.ForeignKey('analysis_history.id'), nullable=True)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    analysis = db.relationship('AnalysisHistory', backref='notification')
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.notification_type,
            'analysis_id': self.analysis_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
    
    def __repr__(self):
        return f'<Notification {self.title}>'


class GeneticRiskProfile(db.Model):
    """Model to store genetic risk calculations"""
    __tablename__ = 'genetic_risk_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analysis_history.id'), nullable=True)
    sample_id = db.Column(db.String(100), nullable=False, index=True)
    
    # Overall risk scores
    overall_risk_score = db.Column(db.Float)
    cardiovascular_risk = db.Column(db.Float)
    diabetes_risk = db.Column(db.Float)
    cancer_risk = db.Column(db.Float)
    alzheimer_risk = db.Column(db.Float)
    
    # Detailed risk data (JSON)
    detailed_risks = db.Column(db.Text)  # JSON with all disease-specific risks
    
    # Protective factors
    protective_factors = db.Column(db.Text)  # JSON
    
    # Recommendations
    health_recommendations = db.Column(db.Text)  # HTML/Markdown
    lifestyle_recommendations = db.Column(db.Text)  # HTML/Markdown
    screening_recommendations = db.Column(db.Text)  # HTML/Markdown
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('risk_profiles', lazy='dynamic'))
    analysis = db.relationship('AnalysisHistory', backref='risk_profile')
    
    def get_detailed_risks(self):
        """Get detailed risks as dictionary"""
        if self.detailed_risks:
            return json.loads(self.detailed_risks)
        return {}
    
    def set_detailed_risks(self, risks_dict):
        """Set detailed risks from dictionary"""
        self.detailed_risks = json.dumps(risks_dict)
    
    def get_protective_factors(self):
        """Get protective factors as list"""
        if self.protective_factors:
            return json.loads(self.protective_factors)
        return []
    
    def set_protective_factors(self, factors_list):
        """Set protective factors from list"""
        self.protective_factors = json.dumps(factors_list)
    
    def to_dict(self):
        """Convert risk profile to dictionary"""
        return {
            'id': self.id,
            'sample_id': self.sample_id,
            'overall_risk_score': self.overall_risk_score,
            'cardiovascular_risk': self.cardiovascular_risk,
            'diabetes_risk': self.diabetes_risk,
            'cancer_risk': self.cancer_risk,
            'alzheimer_risk': self.alzheimer_risk,
            'detailed_risks': self.get_detailed_risks(),
            'protective_factors': self.get_protective_factors(),
            'health_recommendations': self.health_recommendations,
            'lifestyle_recommendations': self.lifestyle_recommendations,
            'screening_recommendations': self.screening_recommendations,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<GeneticRiskProfile {self.sample_id}>'


def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")


def create_admin_user(username='admin', email='admin@genovaai.com', password='admin123'):
    """Create default admin user if not exists (thread-safe)"""
    from sqlalchemy.exc import IntegrityError
    
    existing = User.query.filter_by(username=username).first()
    if not existing:
        try:
            admin = User(
                username=username,
                email=email,
                full_name='Administrator',
                is_admin=True,
                is_active=True
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Admin user created: {username} / {password}")
            return admin
        except IntegrityError:
            # Race condition: another worker created the user first
            db.session.rollback()
            existing = User.query.filter_by(username=username).first()
            print(f"ℹ️ Admin user '{username}' already exists (created by another process)")
            return existing
    else:
        print(f"ℹ️ Admin user '{username}' already exists")
        return existing
