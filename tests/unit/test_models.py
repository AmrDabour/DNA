"""
Unit Tests for Database Models
Tests for User, AnalysisHistory, SNPInfo, and other models
"""
import pytest
import json
from datetime import datetime


class TestUserModel:
    """Tests for User model"""
    
    @pytest.mark.unit
    def test_user_creation(self, app, db_session):
        """Test creating a new user"""
        from database import User
        
        user = User(
            username='newuser',
            email='newuser@example.com',
            full_name='New User'
        )
        user.set_password('password123')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'newuser'
        assert user.email == 'newuser@example.com'
        assert user.full_name == 'New User'
        assert user.is_active is True
        assert user.is_admin is False
    
    @pytest.mark.unit
    def test_password_hashing(self, app, db_session):
        """Test password hashing and verification"""
        from database import User
        
        user = User(username='hashtest', email='hash@test.com')
        user.set_password('mysecretpassword')
        
        # Password should be hashed, not stored in plain text
        assert user.password_hash != 'mysecretpassword'
        assert user.password_hash is not None
        
        # Should verify correct password
        assert user.check_password('mysecretpassword') is True
        
        # Should reject wrong password
        assert user.check_password('wrongpassword') is False
    
    @pytest.mark.unit
    def test_user_to_dict(self, sample_user):
        """Test user serialization to dictionary"""
        user_dict = sample_user.to_dict()
        
        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'testuser@example.com'
        assert user_dict['full_name'] == 'Test User'
        assert 'password_hash' not in user_dict
        assert 'id' in user_dict
        assert 'created_at' in user_dict
    
    @pytest.mark.unit
    def test_user_repr(self, sample_user):
        """Test user string representation"""
        repr_str = repr(sample_user)
        assert 'testuser' in repr_str
    
    @pytest.mark.unit
    def test_unique_username(self, app, db_session, sample_user):
        """Test that usernames must be unique"""
        from database import User
        from sqlalchemy.exc import IntegrityError
        
        duplicate = User(
            username='testuser',  # Same as sample_user
            email='different@example.com'
        )
        duplicate.set_password('password')
        
        db_session.add(duplicate)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    @pytest.mark.unit
    def test_unique_email(self, app, db_session, sample_user):
        """Test that emails must be unique"""
        from database import User
        from sqlalchemy.exc import IntegrityError
        
        duplicate = User(
            username='differentuser',
            email='testuser@example.com'  # Same as sample_user
        )
        duplicate.set_password('password')
        
        db_session.add(duplicate)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestAnalysisHistoryModel:
    """Tests for AnalysisHistory model"""
    
    @pytest.mark.unit
    def test_analysis_creation(self, app, db_session, sample_user):
        """Test creating analysis history entry"""
        from database import AnalysisHistory
        
        analysis = AnalysisHistory(
            user_id=sample_user.id,
            sample_id='TEST123',
            analysis_type='combined',
            gender_prediction='Male',
            gender_confidence=0.95,
            ancestry_prediction='European',
            ancestry_code='CEU',
            ancestry_confidence=0.87,
            file_name='test.csv',
            snp_count=1000,
            status='completed'
        )
        
        db_session.add(analysis)
        db_session.commit()
        
        assert analysis.id is not None
        assert analysis.sample_id == 'TEST123'
        assert analysis.status == 'completed'
    
    @pytest.mark.unit
    def test_full_results_json(self, app, db_session, sample_user):
        """Test JSON storage and retrieval of full results"""
        from database import AnalysisHistory
        
        analysis = AnalysisHistory(
            user_id=sample_user.id,
            sample_id='JSON_TEST',
            analysis_type='combined'
        )
        
        test_results = {
            'gender': {'prediction': 'Male', 'confidence': 0.95},
            'ancestry': {'prediction': 'European', 'probabilities': [0.87, 0.1, 0.03]},
            'snp_count': 5000
        }
        
        analysis.set_full_results(test_results)
        db_session.add(analysis)
        db_session.commit()
        
        # Retrieve and verify
        retrieved = AnalysisHistory.query.filter_by(sample_id='JSON_TEST').first()
        results = retrieved.get_full_results()
        
        assert results['gender']['prediction'] == 'Male'
        assert results['ancestry']['prediction'] == 'European'
        assert results['snp_count'] == 5000
    
    @pytest.mark.unit
    def test_tags_management(self, sample_analysis):
        """Test adding and removing tags"""
        # Initially no tags
        assert sample_analysis.get_tags() == []
        
        # Add tags
        sample_analysis.add_tag('important')
        sample_analysis.add_tag('reviewed')
        
        assert 'important' in sample_analysis.get_tags()
        assert 'reviewed' in sample_analysis.get_tags()
        
        # Don't add duplicate
        sample_analysis.add_tag('important')
        tags = sample_analysis.get_tags()
        assert tags.count('important') == 1
        
        # Remove tag
        sample_analysis.remove_tag('reviewed')
        assert 'reviewed' not in sample_analysis.get_tags()
        assert 'important' in sample_analysis.get_tags()
    
    @pytest.mark.unit
    def test_analysis_to_dict(self, sample_analysis):
        """Test analysis serialization"""
        analysis_dict = sample_analysis.to_dict()
        
        assert analysis_dict['sample_id'] == 'NA12345'
        assert analysis_dict['analysis_type'] == 'combined'
        assert analysis_dict['gender_prediction'] == 'Male'
        assert analysis_dict['ancestry_code'] == 'CEU'
        assert 'created_at' in analysis_dict
    
    @pytest.mark.unit
    def test_analysis_repr(self, sample_analysis):
        """Test analysis string representation"""
        repr_str = repr(sample_analysis)
        assert 'NA12345' in repr_str
        assert 'combined' in repr_str


class TestSNPInfoModel:
    """Tests for SNPInfo model"""
    
    @pytest.mark.unit
    def test_snp_creation(self, app, db_session):
        """Test creating SNP info entry"""
        from database import SNPInfo
        
        snp = SNPInfo(
            rs_id='rs1234567',
            chromosome='1',
            position=12345678,
            gene_name='Test Gene',
            gene_symbol='TG1',
            ref_allele='A',
            alt_allele='G',
            maf=0.15,
            function_class='missense'
        )
        
        db_session.add(snp)
        db_session.commit()
        
        assert snp.id is not None
        assert snp.rs_id == 'rs1234567'
        assert snp.maf == 0.15
    
    @pytest.mark.unit
    def test_associated_traits_json(self, app, db_session):
        """Test traits JSON storage"""
        from database import SNPInfo
        
        snp = SNPInfo(rs_id='rs9999999')
        
        traits = ['Eye color', 'Hair color', 'Skin pigmentation']
        snp.set_associated_traits(traits)
        
        db_session.add(snp)
        db_session.commit()
        
        # Retrieve and verify
        retrieved = SNPInfo.query.filter_by(rs_id='rs9999999').first()
        retrieved_traits = retrieved.get_associated_traits()
        
        assert 'Eye color' in retrieved_traits
        assert 'Hair color' in retrieved_traits
        assert len(retrieved_traits) == 3
    
    @pytest.mark.unit
    def test_disease_associations_json(self, app, db_session):
        """Test disease associations JSON storage"""
        from database import SNPInfo
        
        snp = SNPInfo(rs_id='rs8888888')
        
        diseases = ['Type 2 Diabetes', 'Cardiovascular disease']
        snp.set_disease_associations(diseases)
        
        db_session.add(snp)
        db_session.commit()
        
        retrieved = SNPInfo.query.filter_by(rs_id='rs8888888').first()
        retrieved_diseases = retrieved.get_disease_associations()
        
        assert 'Type 2 Diabetes' in retrieved_diseases
        assert len(retrieved_diseases) == 2
    
    @pytest.mark.unit
    def test_snp_to_dict(self, app, db_session):
        """Test SNP serialization"""
        from database import SNPInfo
        
        snp = SNPInfo(
            rs_id='rs5555555',
            chromosome='5',
            position=5555555,
            gene_symbol='ABC1'
        )
        snp.set_associated_traits(['Trait1'])
        
        db_session.add(snp)
        db_session.commit()
        
        snp_dict = snp.to_dict()
        
        assert snp_dict['rs_id'] == 'rs5555555'
        assert snp_dict['chromosome'] == '5'
        assert snp_dict['gene_symbol'] == 'ABC1'
        assert 'associated_traits' in snp_dict


class TestNotificationModel:
    """Tests for Notification model"""
    
    @pytest.mark.unit
    def test_notification_creation(self, app, db_session, sample_user):
        """Test creating a notification"""
        from database import Notification
        
        notification = Notification(
            user_id=sample_user.id,
            title='Analysis Complete',
            message='Your genetic analysis has been completed.',
            notification_type='analysis_complete'
        )
        
        db_session.add(notification)
        db_session.commit()
        
        assert notification.id is not None
        assert notification.is_read is False
        assert notification.read_at is None
    
    @pytest.mark.unit
    def test_mark_as_read(self, app, db_session, sample_user):
        """Test marking notification as read"""
        from database import Notification
        
        notification = Notification(
            user_id=sample_user.id,
            title='Test',
            message='Test message',
            notification_type='info'
        )
        
        db_session.add(notification)
        db_session.commit()
        
        assert notification.is_read is False
        
        notification.mark_as_read()
        
        assert notification.is_read is True
        assert notification.read_at is not None
    
    @pytest.mark.unit
    def test_notification_to_dict(self, app, db_session, sample_user):
        """Test notification serialization"""
        from database import Notification
        
        notification = Notification(
            user_id=sample_user.id,
            title='Test Notification',
            message='This is a test',
            notification_type='system'
        )
        
        db_session.add(notification)
        db_session.commit()
        
        notif_dict = notification.to_dict()
        
        assert notif_dict['title'] == 'Test Notification'
        assert notif_dict['type'] == 'system'
        assert notif_dict['is_read'] is False


class TestGeneticRiskProfileModel:
    """Tests for GeneticRiskProfile model"""
    
    @pytest.mark.unit
    def test_risk_profile_creation(self, app, db_session, sample_user):
        """Test creating a risk profile"""
        from database import GeneticRiskProfile
        
        profile = GeneticRiskProfile(
            user_id=sample_user.id,
            sample_id='RISK_TEST',
            overall_risk_score=0.35,
            cardiovascular_risk=0.25,
            diabetes_risk=0.40,
            cancer_risk=0.15
        )
        
        db_session.add(profile)
        db_session.commit()
        
        assert profile.id is not None
        assert profile.overall_risk_score == 0.35
    
    @pytest.mark.unit
    def test_detailed_risks_json(self, app, db_session, sample_user):
        """Test detailed risks JSON storage"""
        from database import GeneticRiskProfile
        
        profile = GeneticRiskProfile(
            user_id=sample_user.id,
            sample_id='DETAIL_TEST'
        )
        
        detailed = {
            'breast_cancer': {'risk': 0.12, 'population_avg': 0.15},
            'heart_disease': {'risk': 0.25, 'population_avg': 0.20}
        }
        profile.set_detailed_risks(detailed)
        
        db_session.add(profile)
        db_session.commit()
        
        retrieved = GeneticRiskProfile.query.filter_by(sample_id='DETAIL_TEST').first()
        risks = retrieved.get_detailed_risks()
        
        assert 'breast_cancer' in risks
        assert risks['heart_disease']['risk'] == 0.25
    
    @pytest.mark.unit
    def test_protective_factors_json(self, app, db_session, sample_user):
        """Test protective factors JSON storage"""
        from database import GeneticRiskProfile
        
        profile = GeneticRiskProfile(
            user_id=sample_user.id,
            sample_id='PROTECT_TEST'
        )
        
        factors = ['APOE ε2 allele', 'Low LDL cholesterol gene variant']
        profile.set_protective_factors(factors)
        
        db_session.add(profile)
        db_session.commit()
        
        retrieved = GeneticRiskProfile.query.filter_by(sample_id='PROTECT_TEST').first()
        retrieved_factors = retrieved.get_protective_factors()
        
        assert len(retrieved_factors) == 2
        assert 'APOE ε2 allele' in retrieved_factors




