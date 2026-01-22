"""
Database Module for Analysis Service
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class AnalysisHistory(db.Model):
    """Analysis history model - matches actual database schema"""
    __tablename__ = 'analysis_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=True)
    analysis_type = db.Column(db.String(50), nullable=False, default='general')
    status = db.Column(db.String(20), default='pending')
    results = db.Column(db.Text, nullable=True)  # JSON stored as text
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    snp_count = db.Column(db.Integer, default=0)
    
    # Alias properties for backward compatibility
    @property
    def sample_id(self):
        """Alias: sample_id derived from file_name"""
        return self.file_name.rsplit('.', 1)[0] if self.file_name else None
    
    @property
    def full_results(self):
        """Alias: full_results same as results"""
        return self.results
    
    @property
    def gender_prediction(self):
        """Extract gender from results JSON"""
        try:
            if self.results:
                data = json.loads(self.results)
                return data.get('gender_prediction') or data.get('gender')
        except:
            pass
        return None
    
    @property
    def gender_confidence(self):
        """Extract gender confidence from results JSON"""
        try:
            if self.results:
                data = json.loads(self.results)
                return data.get('gender_confidence')
        except:
            pass
        return None
    
    @property
    def ancestry_prediction(self):
        """Extract ancestry from results JSON"""
        try:
            if self.results:
                data = json.loads(self.results)
                return data.get('ancestry_prediction') or data.get('ancestry') or data.get('region')
        except:
            pass
        return None
    
    @property
    def ancestry_code(self):
        """Extract ancestry code from results JSON"""
        try:
            if self.results:
                data = json.loads(self.results)
                return data.get('ancestry_code') or data.get('region_code')
        except:
            pass
        return None
    
    @property
    def ancestry_confidence(self):
        """Extract ancestry confidence from results JSON"""
        try:
            if self.results:
                data = json.loads(self.results)
                return data.get('ancestry_confidence') or data.get('region_confidence')
        except:
            pass
        return None
    
    @property
    def processing_time(self):
        """Calculate processing time if completed"""
        if self.completed_at and self.created_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None
    
    @property
    def updated_at(self):
        """Alias: updated_at same as completed_at or created_at"""
        return self.completed_at or self.created_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sample_id': self.sample_id,
            'file_name': self.file_name,
            'analysis_type': self.analysis_type,
            'status': self.status,
            'results': json.loads(self.results) if self.results else None,
            'full_results': json.loads(self.full_results) if self.full_results else None,
            'gender_prediction': self.gender_prediction,
            'gender_confidence': self.gender_confidence,
            'ancestry_prediction': self.ancestry_prediction,
            'ancestry_code': self.ancestry_code,
            'ancestry_confidence': self.ancestry_confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'snp_count': self.snp_count,
            'processing_time': self.processing_time,
            'error_message': self.error_message
        }


class SNPInfo(db.Model):
    """SNP information model - matches existing database schema"""
    __tablename__ = 'snp_info'
    
    id = db.Column(db.Integer, primary_key=True)
    rsid = db.Column(db.String(20), unique=True, nullable=False, index=True)
    chromosome = db.Column(db.String(10), nullable=True)
    position = db.Column(db.Integer, nullable=True)
    gene = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    risk_allele = db.Column(db.String(10), nullable=True)
    normal_allele = db.Column(db.String(10), nullable=True)
    phenotype = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Alias properties for compatibility with routes that use different names
    @property
    def rs_id(self):
        return self.rsid
    
    @property
    def gene_name(self):
        return self.gene
    
    @property
    def gene_symbol(self):
        return self.gene
    
    @property
    def clinical_significance(self):
        return None  # Not in current schema
    
    @property
    def associated_traits(self):
        return self.phenotype  # Map phenotype to traits
    
    @property
    def disease_associations(self):
        return None  # Not in current schema
    
    @property
    def ref_allele(self):
        return self.normal_allele
    
    @property
    def alt_allele(self):
        return self.risk_allele
    
    @property
    def maf(self):
        return None  # Not in current schema
    
    @property
    def source(self):
        return "dbSNP"  # Default source
    
    def get_associated_traits(self):
        """Get list of associated traits"""
        if self.phenotype:
            return [self.phenotype]
        return []
    
    def get_disease_associations(self):
        """Get list of disease associations"""
        return []
    
    def to_dict(self):
        return {
            'id': self.id,
            'rs_id': self.rsid,
            'rsid': self.rsid,
            'chromosome': self.chromosome,
            'position': self.position,
            'gene': self.gene,
            'gene_name': self.gene,
            'gene_symbol': self.gene,
            'description': self.description,
            'risk_allele': self.risk_allele,
            'ref_allele': self.normal_allele,
            'alt_allele': self.risk_allele,
            'phenotype': self.phenotype,
            'associated_traits': self.get_associated_traits(),
            'disease_associations': self.get_disease_associations(),
            'clinical_significance': None,
            'source': 'dbSNP'
        }


def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)
    with app.app_context():
        try:
            # Use inspect to check existing tables before creating
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'analysis_history' not in existing_tables:
                db.create_all()
                print("Analysis Service: Database tables created")
            else:
                print("Analysis Service: Tables already exist, skipping creation")
        except Exception as e:
            print(f"Analysis Service: Database init warning: {e}")
