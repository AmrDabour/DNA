"""
Integration Tests for Samples Routes
Tests for /api/samples/* endpoints
"""
import pytest
import json
import os
import tempfile
import pandas as pd


class TestListSamplesRoute:
    """Tests for /api/samples/list endpoint"""
    
    @pytest.mark.integration
    def test_list_samples_success(self, client):
        """Test listing samples returns successful response"""
        response = client.get('/api/samples/list')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
        assert data['success'] is True
        assert 'samples' in data
        assert 'total' in data
        assert isinstance(data['samples'], list)
    
    @pytest.mark.integration
    def test_list_samples_structure(self, client):
        """Test that sample list has correct structure"""
        response = client.get('/api/samples/list')
        data = response.get_json()
        
        if data['total'] > 0:
            sample = data['samples'][0]
            assert 'filename' in sample
            assert 'path' in sample
            assert 'patient_id' in sample
            assert 'population' in sample
            assert 'gender' in sample


class TestSampleInfoRoute:
    """Tests for /api/samples/info endpoint"""
    
    @pytest.mark.integration
    def test_sample_info_missing_file(self, client):
        """Test sample info with non-existent file"""
        response = client.post('/api/samples/info', 
            json={'sample_file': '/nonexistent/file.csv'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is False
        assert 'error' in data
    
    @pytest.mark.integration
    def test_sample_info_with_fixture(self, client, temp_snp_file):
        """Test sample info with test fixture file"""
        response = client.post('/api/samples/info',
            json={'sample_file': str(temp_snp_file)},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        assert 'patient_id' in data
        assert 'population' in data
        assert 'total_snps' in data
    
    @pytest.mark.integration
    def test_sample_info_no_file_param(self, client):
        """Test sample info without file parameter"""
        response = client.post('/api/samples/info',
            json={},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is False


class TestPopulationsRoute:
    """Tests for /api/samples/populations endpoint"""
    
    @pytest.mark.integration
    def test_list_populations(self, client, population_info):
        """Test listing all populations"""
        response = client.get('/api/samples/populations')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        assert 'populations' in data
        assert 'total' in data
        assert data['total'] == 11  # 11 HapMap populations
    
    @pytest.mark.integration
    def test_populations_structure(self, client):
        """Test population data structure"""
        response = client.get('/api/samples/populations')
        data = response.get_json()
        
        populations = data['populations']
        assert len(populations) > 0
        
        pop = populations[0]
        assert 'code' in pop
        assert 'short_code' in pop
        assert 'description' in pop


class TestPopulationInfoRoute:
    """Tests for /api/samples/population/<code> endpoint"""
    
    @pytest.mark.integration
    def test_get_population_info_ceu(self, client):
        """Test getting CEU population info"""
        response = client.get('/api/samples/population/CEU')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        assert data['code'] == 'CEU'
        assert 'description' in data
        assert 'European' in data['description'] or 'Utah' in data['description']
    
    @pytest.mark.integration
    def test_get_population_info_yri(self, client):
        """Test getting YRI population info"""
        response = client.get('/api/samples/population/YRI')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        assert data['code'] == 'YRI'
        assert 'Yoruban' in data['description'] or 'Nigeria' in data['description']
    
    @pytest.mark.integration
    def test_get_population_info_lowercase(self, client):
        """Test getting population info with lowercase code"""
        response = client.get('/api/samples/population/jpt')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should convert to uppercase and find it
        assert data['success'] is True
        assert data['code'] == 'JPT'
    
    @pytest.mark.integration
    def test_get_population_info_unknown(self, client):
        """Test getting info for unknown population"""
        response = client.get('/api/samples/population/UNKNOWN')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is False
        assert 'error' in data
        assert 'available_populations' in data


class TestCompareSamplesRoute:
    """Tests for /api/samples/compare endpoint"""
    
    @pytest.mark.integration
    def test_compare_samples_missing_files(self, client):
        """Test compare with non-existent files"""
        response = client.post('/api/samples/compare',
            json={
                'sample_file_1': '/nonexistent/file1.csv',
                'sample_file_2': '/nonexistent/file2.csv'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is False
        assert 'error' in data
    
    @pytest.mark.integration
    def test_compare_same_sample(self, client, temp_snp_file):
        """Test comparing a sample with itself"""
        response = client.post('/api/samples/compare',
            json={
                'sample_file_1': str(temp_snp_file),
                'sample_file_2': str(temp_snp_file)
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        # Same file should have 100% similarity
        assert data['similarity_rate'] == 100.0
        assert data['different_genotypes'] == 0
    
    @pytest.mark.integration
    def test_compare_samples_response_structure(self, client, temp_snp_file):
        """Test compare response structure"""
        response = client.post('/api/samples/compare',
            json={
                'sample_file_1': str(temp_snp_file),
                'sample_file_2': str(temp_snp_file)
            },
            content_type='application/json'
        )
        
        data = response.get_json()
        
        if data['success']:
            assert 'sample1' in data
            assert 'sample2' in data
            assert 'common_snps_count' in data
            assert 'unique_to_sample1' in data
            assert 'unique_to_sample2' in data
            assert 'matching_genotypes' in data
            assert 'different_genotypes' in data
            assert 'similarity_rate' in data
    
    @pytest.mark.integration
    def test_compare_different_samples(self, client, tmp_path):
        """Test comparing two different samples"""
        # Create two different sample files
        sample1_data = {
            'CHR': [1, 1, 2],
            'SNP': ['rs123', 'rs456', 'rs789'],
            'GEN_DIST': [0, 0, 0],
            'POS': [100, 200, 300],
            'Allele1': ['A', 'G', 'T'],
            'Allele2': ['A', 'G', 'T'],
            'Patient_ID': ['P1', 'P1', 'P1'],
            'Population': ['CEU', 'CEU', 'CEU'],
            'Sex': [1, 1, 1]
        }
        
        sample2_data = {
            'CHR': [1, 1, 2],
            'SNP': ['rs123', 'rs456', 'rs999'],  # Different SNP
            'GEN_DIST': [0, 0, 0],
            'POS': [100, 200, 400],
            'Allele1': ['A', 'C', 'G'],  # Different allele
            'Allele2': ['A', 'C', 'G'],
            'Patient_ID': ['P2', 'P2', 'P2'],
            'Population': ['YRI', 'YRI', 'YRI'],
            'Sex': [2, 2, 2]
        }
        
        file1 = tmp_path / 'sample1.csv'
        file2 = tmp_path / 'sample2.csv'
        
        pd.DataFrame(sample1_data).to_csv(file1, index=False)
        pd.DataFrame(sample2_data).to_csv(file2, index=False)
        
        response = client.post('/api/samples/compare',
            json={
                'sample_file_1': str(file1),
                'sample_file_2': str(file2)
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        assert data['common_snps_count'] == 2  # rs123 and rs456 are common
        assert data['unique_to_sample1'] == 1  # rs789
        assert data['unique_to_sample2'] == 1  # rs999


class TestSamplesEdgeCases:
    """Edge case tests for samples routes"""
    
    @pytest.mark.integration
    def test_sample_info_empty_file(self, client, tmp_path):
        """Test sample info with empty CSV file"""
        empty_file = tmp_path / 'empty.csv'
        empty_file.write_text('')
        
        response = client.post('/api/samples/info',
            json={'sample_file': str(empty_file)},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is False
    
    @pytest.mark.integration
    def test_sample_info_invalid_csv(self, client, tmp_path):
        """Test sample info with invalid CSV format"""
        invalid_file = tmp_path / 'invalid.csv'
        invalid_file.write_text('not,a,valid\nsnp,file,format')
        
        response = client.post('/api/samples/info',
            json={'sample_file': str(invalid_file)},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should fail validation due to missing SNP column
        assert data['success'] is False
    
    @pytest.mark.integration
    def test_population_info_special_characters(self, client):
        """Test population info with special characters in code"""
        response = client.get('/api/samples/population/CEU%20')
        
        # Should handle gracefully
        assert response.status_code in [200, 404]
    
    @pytest.mark.integration
    def test_samples_json_content_type(self, client, temp_snp_file):
        """Test that endpoints accept JSON content type"""
        response = client.post('/api/samples/info',
            data=json.dumps({'sample_file': str(temp_snp_file)}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data


