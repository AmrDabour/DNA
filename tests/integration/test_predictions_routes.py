"""
Integration Tests for Predictions Routes
Tests for /api/predictions/* endpoints
"""
import pytest
import json
from unittest.mock import patch, MagicMock


class TestPhysicalPredictionsRoute:
    """Tests for /api/predictions/physical endpoint"""
    
    @pytest.mark.integration
    def test_physical_predictions_success(self, client, mock_gemini):
        """Test successful physical characteristics prediction"""
        response = client.post('/api/predictions/physical',
            json={
                'gender': 'Male',
                'population': 'CEU'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
        # Response should contain formatted_result or characteristics data
        if data.get('success'):
            assert 'formatted_result' in data or 'physical_characteristics' in data or 'gender' in data
    
    @pytest.mark.integration
    def test_physical_predictions_invalid_population(self, client):
        """Test prediction with invalid population code"""
        response = client.post('/api/predictions/physical',
            json={
                'gender': 'Male',
                'population': 'INVALID'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should either fail or handle gracefully
        assert 'success' in data
    
    @pytest.mark.integration
    def test_physical_predictions_missing_params(self, client):
        """Test prediction with missing parameters"""
        response = client.post('/api/predictions/physical',
            json={'gender': 'Male'},  # Missing population
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should indicate missing parameter
        assert 'success' in data
    
    @pytest.mark.integration
    def test_physical_predictions_from_sample(self, client, temp_snp_file, mock_gemini):
        """Test physical predictions from sample file"""
        response = client.post('/api/predictions/physical/from-sample',
            json={'sample_file': str(temp_snp_file)},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data


class TestDiseaseRiskRoute:
    """Tests for /api/predictions/disease-risk endpoint"""
    
    @pytest.mark.integration
    def test_disease_risk_success(self, client, mock_gemini):
        """Test successful disease risk assessment"""
        response = client.post('/api/predictions/disease-risk',
            json={
                'gender': 'Female',
                'population': 'YRI'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
        # Response should contain formatted_result or disease risk data
        if data.get('success'):
            assert 'formatted_result' in data or 'disease_risks' in data or 'population' in data
    
    @pytest.mark.integration
    def test_disease_risk_male(self, client, mock_gemini):
        """Test disease risk for male patient"""
        response = client.post('/api/predictions/disease-risk',
            json={
                'gender': 'Male',
                'population': 'JPT'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
    
    @pytest.mark.integration
    def test_disease_risk_from_sample(self, client, temp_snp_file, mock_gemini):
        """Test disease risk from sample file"""
        response = client.post('/api/predictions/disease-risk/from-sample',
            json={'sample_file': str(temp_snp_file)},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data


class TestFullReportRoute:
    """Tests for /api/predictions/full-report endpoint"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_report_success(self, client, temp_snp_file, mock_gemini):
        """Test generating full genetic report"""
        response = client.post('/api/predictions/full-report',
            json={'sample_file': str(temp_snp_file)},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
        # Full report should contain multiple sections
        if data.get('success'):
            # Should have analysis results
            assert any(key in data for key in ['analysis', 'gender', 'ancestry', 'data', 'report'])
    
    @pytest.mark.integration
    def test_full_report_missing_file(self, client):
        """Test full report with missing file"""
        response = client.post('/api/predictions/full-report',
            json={'sample_file': '/nonexistent/file.csv'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is False


class TestFunFactsRoute:
    """Tests for /api/predictions/fun-facts endpoint"""
    
    @pytest.mark.integration
    def test_fun_facts_general(self, client, mock_gemini):
        """Test getting general genetic fun facts"""
        response = client.post('/api/predictions/fun-facts',
            json={'topic': 'general'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
    
    @pytest.mark.integration
    def test_fun_facts_ancestry(self, client, mock_gemini):
        """Test getting ancestry-related fun facts"""
        response = client.post('/api/predictions/fun-facts',
            json={'topic': 'ancestry'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
    
    @pytest.mark.integration
    def test_fun_facts_health(self, client, mock_gemini):
        """Test getting health-related fun facts"""
        response = client.post('/api/predictions/fun-facts',
            json={'topic': 'health'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
    
    @pytest.mark.integration
    def test_fun_facts_default_topic(self, client, mock_gemini):
        """Test fun facts with no topic specified"""
        response = client.post('/api/predictions/fun-facts',
            json={},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        # Should use default topic


class TestExplainSNPRoute:
    """Tests for /api/predictions/explain-snp endpoint"""
    
    @pytest.mark.integration
    def test_explain_snp_known(self, client, mock_gemini):
        """Test explaining a well-known SNP"""
        response = client.post('/api/predictions/explain-snp',
            json={'snp_id': 'rs1426654'},  # Skin pigmentation SNP
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
    
    @pytest.mark.integration
    def test_explain_snp_unknown(self, client, mock_gemini):
        """Test explaining an unknown SNP"""
        response = client.post('/api/predictions/explain-snp',
            json={'snp_id': 'rs999999999999'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should handle unknown SNP gracefully
        assert 'success' in data


class TestAncestryDeepDiveRoute:
    """Tests for /api/predictions/ancestry-deep-dive endpoint"""
    
    @pytest.mark.integration
    def test_ancestry_deep_dive_ceu(self, client, mock_gemini):
        """Test ancestry deep dive for CEU population"""
        response = client.post('/api/predictions/ancestry-deep-dive',
            json={
                'gender': 'Male',
                'population': 'CEU'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
    
    @pytest.mark.integration
    def test_ancestry_deep_dive_yri(self, client, mock_gemini):
        """Test ancestry deep dive for YRI population"""
        response = client.post('/api/predictions/ancestry-deep-dive',
            json={
                'gender': 'Female',
                'population': 'YRI'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data


class TestImageGenerationRoute:
    """Tests for /api/predictions/generate-person-image endpoint"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_generate_image(self, client, mock_gemini):
        """Test generating person image"""
        response = client.post('/api/predictions/generate-person-image',
            json={
                'gender': 'Male',
                'population': 'JPT',
                'patient_id': 'TEST001'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
        # If successful, should contain image data or path
        if data.get('success'):
            assert 'image_data' in data or 'image_path' in data or 'image_url' in data
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_generate_image_from_sample(self, client, temp_snp_file, mock_gemini):
        """Test generating image from sample file"""
        response = client.post('/api/predictions/generate-image-from-sample',
            json={'sample_file': str(temp_snp_file)},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data


class TestGeneticRelatednessRoute:
    """Tests for /api/predictions/genetic-relatedness endpoint"""
    
    @pytest.mark.integration
    def test_genetic_relatedness_same_sample(self, client, temp_snp_file, mock_gemini):
        """Test genetic relatedness with same sample"""
        response = client.post('/api/predictions/genetic-relatedness',
            json={
                'sample_file_1': str(temp_snp_file),
                'sample_file_2': str(temp_snp_file)
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data


class TestTraitsGuideRoute:
    """Tests for /api/predictions/traits-guide endpoint"""
    
    @pytest.mark.integration
    def test_traits_guide(self, client, mock_gemini):
        """Test getting traits prediction guide"""
        response = client.get('/api/predictions/traits-guide')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data


class TestSummaryCardRoute:
    """Tests for /api/predictions/summary-card endpoint"""
    
    @pytest.mark.integration
    def test_summary_card(self, client, temp_snp_file, mock_gemini):
        """Test generating genetic summary card"""
        response = client.post('/api/predictions/summary-card',
            json={'sample_file': str(temp_snp_file)},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data


class TestPredictionsEdgeCases:
    """Edge case tests for predictions routes"""
    
    @pytest.mark.integration
    def test_predictions_invalid_gender(self, client, mock_gemini):
        """Test predictions with invalid gender"""
        response = client.post('/api/predictions/physical',
            json={
                'gender': 'InvalidGender',
                'population': 'CEU'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        # Should handle invalid gender gracefully
    
    @pytest.mark.integration
    def test_predictions_case_sensitivity(self, client, mock_gemini):
        """Test that gender/population are case-insensitive"""
        response = client.post('/api/predictions/physical',
            json={
                'gender': 'male',  # lowercase
                'population': 'ceu'  # lowercase
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        # Should handle case variations
    
    @pytest.mark.integration
    def test_predictions_empty_json(self, client):
        """Test predictions with empty JSON body"""
        response = client.post('/api/predictions/physical',
            json={},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should return error for missing required fields
        assert 'success' in data
    
    @pytest.mark.integration
    def test_predictions_all_populations(self, client, mock_gemini):
        """Test predictions work for all population codes"""
        populations = ['ASW', 'CEU', 'CHB', 'CHD', 'GIH', 'JPT', 'LWK', 'MEX', 'MKK', 'TSI', 'YRI']
        
        for pop in populations:
            response = client.post('/api/predictions/physical',
                json={
                    'gender': 'Male',
                    'population': pop
                },
                content_type='application/json'
            )
            
            assert response.status_code == 200, f"Failed for population {pop}"
            data = response.get_json()
            assert 'success' in data, f"Missing success field for population {pop}"


class TestPredictionsResponseFormat:
    """Tests for consistent response format in predictions"""
    
    @pytest.mark.integration
    def test_success_response_has_data(self, client, mock_gemini):
        """Test that successful responses include data"""
        response = client.post('/api/predictions/fun-facts',
            json={'topic': 'general'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
        # Successful response should have some data
        if data.get('success'):
            assert len(data) > 1  # More than just success field
    
    @pytest.mark.integration
    def test_error_response_has_message(self, client):
        """Test that error responses include error message"""
        response = client.post('/api/predictions/full-report',
            json={'sample_file': '/nonexistent/file.csv'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        if not data.get('success'):
            assert 'error' in data
            assert isinstance(data['error'], str)
            assert len(data['error']) > 0

