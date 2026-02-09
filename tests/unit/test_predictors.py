"""
Unit Tests for ML Predictor Classes
Tests for SexPredictor, AncestryPredictor, and GeneticPredictor
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np


class TestPopulationInfo:
    """Tests for POPULATION_INFO constant"""
    
    @pytest.mark.unit
    def test_population_info_structure(self, population_info):
        """Test that population info has correct structure"""
        assert len(population_info) == 11
        
        for code, info in population_info.items():
            assert 'code' in info
            assert 'description' in info
            assert len(info['code']) == 1  # Single letter code
    
    @pytest.mark.unit
    def test_known_populations_exist(self, population_info):
        """Test that all known populations exist"""
        expected_populations = ['ASW', 'CEU', 'CHB', 'CHD', 'GIH', 
                               'JPT', 'LWK', 'MEX', 'MKK', 'TSI', 'YRI']
        
        for pop in expected_populations:
            assert pop in population_info


class TestFindModelDirectories:
    """Tests for find_model_directories function"""
    
    @pytest.mark.unit
    def test_find_model_directories(self):
        """Test finding model directories"""
        from ml_models import find_model_directories
        
        gender_dir, ancestry_dir = find_model_directories()
        
        # At least one should be found if models exist
        # The function returns None for missing directories
        if gender_dir:
            assert os.path.exists(gender_dir)
            assert 'gender_prediction_package' in gender_dir
        
        if ancestry_dir:
            assert os.path.exists(ancestry_dir)
            assert 'region_prediction_package' in ancestry_dir


class TestGeneticPredictor:
    """Tests for GeneticPredictor class"""
    
    @pytest.mark.unit
    def test_predictor_initialization(self):
        """Test GeneticPredictor initialization"""
        from ml_models import GeneticPredictor
        
        predictor = GeneticPredictor()
        
        assert predictor.sex_predictor is None
        assert predictor.ancestry_predictor is None
    
    @pytest.mark.unit
    def test_load_sex_predictor_nonexistent(self):
        """Test loading sex predictor with non-existent directory"""
        from ml_models import GeneticPredictor
        
        predictor = GeneticPredictor()
        result = predictor.load_sex_predictor('/nonexistent/path')
        
        assert result is False
        assert predictor.sex_predictor is None
    
    @pytest.mark.unit
    def test_load_ancestry_predictor_nonexistent(self):
        """Test loading ancestry predictor with non-existent directory"""
        from ml_models import GeneticPredictor
        
        predictor = GeneticPredictor()
        result = predictor.load_ancestry_predictor('/nonexistent/path')
        
        assert result is False
        assert predictor.ancestry_predictor is None
    
    @pytest.mark.unit
    @pytest.mark.slow
    def test_load_sex_predictor_actual(self):
        """Test loading actual sex predictor model"""
        from ml_models import GeneticPredictor, find_model_directories
        
        predictor = GeneticPredictor()
        gender_dir, _ = find_model_directories()
        
        if gender_dir and os.path.exists(gender_dir):
            result = predictor.load_sex_predictor(gender_dir)
            assert result is True
            assert predictor.sex_predictor is not None
        else:
            pytest.skip("Gender model directory not available")
    
    @pytest.mark.unit
    @pytest.mark.slow
    def test_load_ancestry_predictor_actual(self):
        """Test loading actual ancestry predictor model"""
        from ml_models import GeneticPredictor, find_model_directories
        
        predictor = GeneticPredictor()
        _, ancestry_dir = find_model_directories()
        
        if ancestry_dir and os.path.exists(ancestry_dir):
            result = predictor.load_ancestry_predictor(ancestry_dir)
            assert result is True
            assert predictor.ancestry_predictor is not None
        else:
            pytest.skip("Ancestry model directory not available")


class TestSexPredictor:
    """Tests for SexPredictor class"""
    
    @pytest.fixture
    def mock_model(self):
        """Create a mock model for testing"""
        model = MagicMock()
        model.predict.return_value = np.array([1])  # Male
        return model
    
    @pytest.fixture
    def mock_features_df(self):
        """Create mock features dataframe"""
        return pd.DataFrame({
            'IID': ['NA12345', 'NA12346', 'NA12347'],
            'PC_1': [0.1, 0.2, 0.3],
            'PC_2': [-0.1, -0.2, -0.3],
            'PC_3': [0.05, 0.06, 0.07],
            'Population': ['CEU', 'YRI', 'JPT'],
            'Population_encoded': [0, 1, 2],
            'gender': [1, 2, 1]  # Male, Female, Male
        })
    
    @pytest.mark.unit
    def test_sex_labels(self):
        """Test sex labels mapping"""
        # Create minimal mock for testing
        with patch('ml_models.predictors.joblib.load') as mock_load:
            mock_load.return_value = MagicMock()
            
            with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
                model_path = f.name
            
            try:
                from ml_models.predictors import SexPredictor
                predictor = SexPredictor(model_path)
                
                assert predictor.sex_labels[1] == 'Male'
                assert predictor.sex_labels[2] == 'Female'
            finally:
                os.unlink(model_path)
    
    @pytest.mark.unit
    def test_predict_by_id_not_found(self):
        """Test prediction with non-existent sample ID"""
        with patch('ml_models.predictors.joblib.load') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
                model_path = f.name
            
            # Create temp features CSV
            features_df = pd.DataFrame({
                'IID': ['EXISTING_ID'],
                'PC_1': [0.1],
                'gender': [1]
            })
            
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f:
                features_df.to_csv(f.name, index=False)
                features_path = f.name
            
            try:
                from ml_models.predictors import SexPredictor
                predictor = SexPredictor(model_path, features_path=features_path)
                
                result = predictor.predict_by_id('NONEXISTENT_ID')
                assert result == (None, None, None, None)
            finally:
                os.unlink(model_path)
                os.unlink(features_path)


class TestAncestryPredictor:
    """Tests for AncestryPredictor class"""
    
    @pytest.mark.unit
    def test_known_populations(self):
        """Test that ancestry predictor has known populations"""
        with patch('ml_models.predictors.joblib.load') as mock_load:
            mock_model = MagicMock()
            mock_encoder = MagicMock()
            mock_encoder.classes_ = np.array(['CEU', 'YRI', 'JPT', 'CHB'])
            
            # Setup mock to return different objects for different calls
            mock_load.side_effect = [mock_model, mock_encoder]
            
            features_df = pd.DataFrame({
                'IID': ['NA12345'],
                'PC_1': [0.1],
                'PC_2': [0.2],
                'Population': ['CEU']
            })
            
            with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f1, \
                 tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f2, \
                 tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f3:
                
                model_path = f1.name
                encoder_path = f2.name
                features_df.to_csv(f3.name, index=False)
                features_path = f3.name
            
            try:
                from ml_models.predictors import AncestryPredictor
                predictor = AncestryPredictor(
                    model_path=model_path,
                    encoder_path=encoder_path,
                    features_path=features_path
                )
                
                assert 'CEU' in predictor.known_populations
                assert 'YRI' in predictor.known_populations
                assert len(predictor.known_populations) == 4
            finally:
                os.unlink(model_path)
                os.unlink(encoder_path)
                os.unlink(features_path)
    
    @pytest.mark.unit
    def test_predict_by_id_not_found(self):
        """Test prediction with non-existent sample ID"""
        with patch('ml_models.predictors.joblib.load') as mock_load:
            mock_model = MagicMock()
            mock_encoder = MagicMock()
            mock_encoder.classes_ = np.array(['CEU', 'YRI'])
            mock_load.side_effect = [mock_model, mock_encoder]
            
            features_df = pd.DataFrame({
                'IID': ['EXISTING_ID'],
                'PC_1': [0.1],
                'PC_2': [0.2],
                'Population': ['CEU']
            })
            
            with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f1, \
                 tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f2, \
                 tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f3:
                
                model_path = f1.name
                encoder_path = f2.name
                features_df.to_csv(f3.name, index=False)
                features_path = f3.name
            
            try:
                from ml_models.predictors import AncestryPredictor
                predictor = AncestryPredictor(
                    model_path=model_path,
                    encoder_path=encoder_path,
                    features_path=features_path
                )
                
                result = predictor.predict_by_id('NONEXISTENT_ID')
                assert result == (None, None)
            finally:
                os.unlink(model_path)
                os.unlink(encoder_path)
                os.unlink(features_path)


class TestBasePredictor:
    """Tests for BasePredictor class"""
    
    @pytest.mark.unit
    def test_get_available_samples_empty(self):
        """Test getting samples when no features loaded"""
        with patch('ml_models.predictors.joblib.load') as mock_load:
            mock_load.return_value = MagicMock()
            
            with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
                model_path = f.name
            
            try:
                from ml_models.predictors import BasePredictor
                predictor = BasePredictor(model_path)
                
                # No features loaded, should return empty list
                samples = predictor.get_available_samples()
                assert samples == []
            finally:
                os.unlink(model_path)
    
    @pytest.mark.unit
    def test_get_available_samples_with_features(self):
        """Test getting samples when features are loaded"""
        with patch('ml_models.predictors.joblib.load') as mock_load:
            mock_load.return_value = MagicMock()
            
            features_df = pd.DataFrame({
                'IID': ['NA12345', 'NA12346', 'NA12347'],
                'PC_1': [0.1, 0.2, 0.3]
            })
            
            with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f1, \
                 tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f2:
                
                model_path = f1.name
                features_df.to_csv(f2.name, index=False)
                features_path = f2.name
            
            try:
                from ml_models.predictors import BasePredictor
                predictor = BasePredictor(model_path, features_path=features_path)
                
                samples = predictor.get_available_samples()
                assert len(samples) == 3
                assert 'NA12345' in samples
                assert 'NA12346' in samples
                assert 'NA12347' in samples
            finally:
                os.unlink(model_path)
                os.unlink(features_path)


class TestModelIntegration:
    """Integration tests for model loading and prediction"""
    
    @pytest.mark.unit
    @pytest.mark.slow
    @pytest.mark.integration
    def test_full_prediction_pipeline(self):
        """Test full prediction pipeline if models are available"""
        from ml_models import GeneticPredictor, find_model_directories
        
        predictor = GeneticPredictor()
        gender_dir, ancestry_dir = find_model_directories()
        
        models_loaded = False
        
        if gender_dir:
            if predictor.load_sex_predictor(gender_dir):
                models_loaded = True
        
        if ancestry_dir:
            if predictor.load_ancestry_predictor(ancestry_dir):
                models_loaded = True
        
        if not models_loaded:
            pytest.skip("No models available for testing")
        
        # Test that loaded predictors have expected attributes
        if predictor.sex_predictor:
            assert hasattr(predictor.sex_predictor, 'model')
            assert hasattr(predictor.sex_predictor, 'sex_labels')
        
        if predictor.ancestry_predictor:
            assert hasattr(predictor.ancestry_predictor, 'model')
            assert hasattr(predictor.ancestry_predictor, 'known_populations')




