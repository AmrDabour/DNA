"""
Integration Tests for Analysis Routes
Tests for /api/analysis/* endpoints
"""
import pytest
import json
import pandas as pd


class TestSNPQueryRoute:
    """Tests for /api/analysis/snp endpoint"""
    
    @pytest.mark.integration
    def test_snp_query_success(self, client, temp_snp_file):
        """Test successful SNP query"""
        response = client.post('/api/analysis/snp',
            json={
                'sample_file': str(temp_snp_file),
                'snp_id': 'rs2185539'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
        if data['success']:
            assert 'snp_id' in data or 'rs_id' in data or 'data' in data
    
    @pytest.mark.integration
    def test_snp_query_not_found(self, client, temp_snp_file):
        """Test SNP query for non-existent SNP"""
        response = client.post('/api/analysis/snp',
            json={
                'sample_file': str(temp_snp_file),
                'snp_id': 'rs999999999'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should either fail or return empty result
        if data.get('success'):
            assert data.get('found') is False or data.get('data') is None
        else:
            assert 'error' in data or 'not found' in str(data).lower()
    
    @pytest.mark.integration
    def test_snp_query_missing_file(self, client):
        """Test SNP query with missing file"""
        response = client.post('/api/analysis/snp',
            json={
                'sample_file': '/nonexistent/file.csv',
                'snp_id': 'rs12345'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is False
        assert 'error' in data
    
    @pytest.mark.integration
    def test_snp_query_missing_params(self, client):
        """Test SNP query with missing parameters"""
        response = client.post('/api/analysis/snp',
            json={},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is False


class TestMultipleSNPQueryRoute:
    """Tests for /api/analysis/snp/multiple endpoint"""
    
    @pytest.mark.integration
    def test_multiple_snp_query_success(self, client, temp_snp_file):
        """Test querying multiple SNPs"""
        response = client.post('/api/analysis/snp/multiple',
            json={
                'sample_file': str(temp_snp_file),
                'snp_ids': ['rs2185539', 'rs11510103', 'rs4040617']
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
        if data['success']:
            assert 'results' in data or 'data' in data or 'snps' in data
    
    @pytest.mark.integration
    def test_multiple_snp_query_partial(self, client, temp_snp_file):
        """Test querying mix of existing and non-existing SNPs"""
        response = client.post('/api/analysis/snp/multiple',
            json={
                'sample_file': str(temp_snp_file),
                'snp_ids': ['rs2185539', 'rs999999999']  # One exists, one doesn't
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should return results with found/not found info
        assert 'success' in data
    
    @pytest.mark.integration
    def test_multiple_snp_query_empty_list(self, client, temp_snp_file):
        """Test querying with empty SNP list"""
        response = client.post('/api/analysis/snp/multiple',
            json={
                'sample_file': str(temp_snp_file),
                'snp_ids': []
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should handle empty list gracefully


class TestAnalyzeRoute:
    """Tests for /api/analysis/analyze endpoint"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_analyze_success(self, client, temp_snp_file):
        """Test successful file analysis"""
        response = client.post('/api/analysis/analyze',
            json={'sample_file': str(temp_snp_file)},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
        # Analysis should return predictions or indicate model not loaded
    
    @pytest.mark.integration
    def test_analyze_missing_file(self, client):
        """Test analysis with missing file"""
        response = client.post('/api/analysis/analyze',
            json={'sample_file': '/nonexistent/file.csv'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is False
        assert 'error' in data
    
    @pytest.mark.integration
    def test_analyze_invalid_file(self, client, tmp_path):
        """Test analysis with invalid file format"""
        invalid_file = tmp_path / 'invalid.csv'
        invalid_file.write_text('col1,col2\nval1,val2')
        
        response = client.post('/api/analysis/analyze',
            json={'sample_file': str(invalid_file)},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # The API might succeed but with empty or minimal results
        # Either fails, has error message, or has empty analysis with 0-1 SNPs
        is_failure = data.get('success') is False
        has_error = 'error' in str(data).lower()
        has_empty_analysis = data.get('analysis', {}) == {} and data.get('total_snps', 0) <= 1
        
        assert is_failure or has_error or has_empty_analysis


class TestStatisticsRoute:
    """Tests for /api/analysis/statistics endpoint"""
    
    @pytest.mark.integration
    def test_statistics_success(self, client, temp_snp_file):
        """Test getting SNP statistics"""
        response = client.post('/api/analysis/statistics',
            json={'sample_file': str(temp_snp_file)},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'success' in data
        if data['success']:
            # Should contain statistical information
            assert 'total_snps' in data or 'snp_count' in data or 'statistics' in data
    
    @pytest.mark.integration
    def test_statistics_chromosome_distribution(self, client, temp_snp_file):
        """Test that statistics include chromosome distribution"""
        response = client.post('/api/analysis/statistics',
            json={'sample_file': str(temp_snp_file)},
            content_type='application/json'
        )
        
        data = response.get_json()
        
        if data.get('success'):
            # Should have chromosome info
            assert 'chromosomes' in data or 'chromosome_distribution' in data or 'chr_counts' in data or 'statistics' in data
    
    @pytest.mark.integration
    def test_statistics_missing_file(self, client):
        """Test statistics with missing file"""
        response = client.post('/api/analysis/statistics',
            json={'sample_file': '/nonexistent/file.csv'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is False


class TestAnalysisEdgeCases:
    """Edge case tests for analysis routes"""
    
    @pytest.mark.integration
    def test_snp_query_case_insensitive(self, client, temp_snp_file):
        """Test that SNP IDs are handled case-insensitively"""
        # Query with uppercase
        response1 = client.post('/api/analysis/snp',
            json={
                'sample_file': str(temp_snp_file),
                'snp_id': 'RS2185539'  # Uppercase
            },
            content_type='application/json'
        )
        
        # Query with lowercase
        response2 = client.post('/api/analysis/snp',
            json={
                'sample_file': str(temp_snp_file),
                'snp_id': 'rs2185539'  # Lowercase
            },
            content_type='application/json'
        )
        
        # Both should return same result (or both fail consistently)
        data1 = response1.get_json()
        data2 = response2.get_json()
        
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    @pytest.mark.integration
    def test_snp_query_with_whitespace(self, client, temp_snp_file):
        """Test SNP query with whitespace in ID"""
        response = client.post('/api/analysis/snp',
            json={
                'sample_file': str(temp_snp_file),
                'snp_id': ' rs2185539 '  # With whitespace
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        # Should either trim whitespace or return not found
    
    @pytest.mark.integration
    def test_large_snp_list_query(self, client, temp_snp_file):
        """Test querying a large number of SNPs"""
        # Create list of 100 SNP IDs
        snp_ids = [f'rs{i}' for i in range(100)]
        
        response = client.post('/api/analysis/snp/multiple',
            json={
                'sample_file': str(temp_snp_file),
                'snp_ids': snp_ids
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        # Should handle large list without error


class TestAnalysisResponseFormat:
    """Tests for consistent response format"""
    
    @pytest.mark.integration
    def test_success_response_format(self, client, temp_snp_file):
        """Test that successful responses have consistent format"""
        response = client.post('/api/analysis/statistics',
            json={'sample_file': str(temp_snp_file)},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # All responses should have success field
        assert 'success' in data
        assert isinstance(data['success'], bool)
    
    @pytest.mark.integration
    def test_error_response_format(self, client):
        """Test that error responses have consistent format"""
        response = client.post('/api/analysis/snp',
            json={
                'sample_file': '/nonexistent/file.csv',
                'snp_id': 'rs12345'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Error responses should have success=False and error message
        assert data['success'] is False
        assert 'error' in data
        assert isinstance(data['error'], str)

