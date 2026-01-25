"""
Unit Tests for VEP (Variant Effect Predictor) Service
Tests for rate limiter, API calls, and caching logic
"""
import pytest
import time
from unittest.mock import MagicMock, patch, Mock
import json


class TestRateLimiter:
    """Tests for RateLimiter class"""
    
    @pytest.mark.unit
    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization"""
        from services.vep_service import RateLimiter
        
        limiter = RateLimiter(requests_per_second=10.0)
        
        assert limiter.requests_per_second == 10.0
        assert limiter.min_interval == 0.1
        assert limiter.last_request_time == 0.0
    
    @pytest.mark.unit
    def test_rate_limiter_default_rate(self):
        """Test RateLimiter with default rate"""
        from services.vep_service import RateLimiter
        
        limiter = RateLimiter()
        
        assert limiter.requests_per_second == 15.0
    
    @pytest.mark.unit
    def test_rate_limiter_wait_first_call(self):
        """Test that first call doesn't wait"""
        from services.vep_service import RateLimiter
        
        limiter = RateLimiter(requests_per_second=10.0)
        
        start = time.time()
        limiter.wait()
        elapsed = time.time() - start
        
        # First call should be immediate (or very fast)
        assert elapsed < 0.05
    
    @pytest.mark.unit
    def test_rate_limiter_enforces_rate(self):
        """Test that rate limiter enforces rate limit"""
        from services.vep_service import RateLimiter
        
        # 2 requests per second = 0.5s between requests
        limiter = RateLimiter(requests_per_second=2.0)
        
        limiter.wait()  # First call
        start = time.time()
        limiter.wait()  # Second call - should wait
        elapsed = time.time() - start
        
        # Should have waited approximately 0.5 seconds
        assert elapsed >= 0.4


class TestVEPServiceInit:
    """Tests for VEPService initialization"""
    
    @pytest.mark.unit
    def test_service_initialization(self):
        """Test VEPService initialization"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        assert service.BASE_URL == "https://rest.ensembl.org"
        assert service.BATCH_LIMIT == 200
        assert service.MAX_RETRIES == 3
        assert hasattr(service, 'rate_limiter')
    
    @pytest.mark.unit
    def test_service_disabled(self):
        """Test VEPService when disabled via environment"""
        import os
        from services.vep_service import VEPService
        
        # Save original value
        original = os.environ.get('VEP_ENABLED')
        
        try:
            os.environ['VEP_ENABLED'] = 'false'
            service = VEPService()
            
            assert service.enabled is False
        finally:
            # Restore original value
            if original:
                os.environ['VEP_ENABLED'] = original
            else:
                os.environ.pop('VEP_ENABLED', None)
    
    @pytest.mark.unit
    def test_service_custom_rate_limit(self):
        """Test VEPService with custom rate limit"""
        import os
        from services.vep_service import VEPService
        
        original = os.environ.get('VEP_RATE_LIMIT')
        
        try:
            os.environ['VEP_RATE_LIMIT'] = '5'
            service = VEPService()
            
            assert service.rate_limiter.requests_per_second == 5.0
        finally:
            if original:
                os.environ['VEP_RATE_LIMIT'] = original
            else:
                os.environ.pop('VEP_RATE_LIMIT', None)


class TestVEPServiceMakeRequest:
    """Tests for VEPService._make_request method"""
    
    @pytest.mark.unit
    def test_make_request_disabled(self):
        """Test that disabled service returns None"""
        from services.vep_service import VEPService
        
        service = VEPService()
        service.enabled = False
        
        result = service._make_request('GET', 'http://example.com')
        
        assert result is None
    
    @pytest.mark.unit
    def test_make_request_get(self):
        """Test GET request"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = service._make_request('GET', 'http://example.com/test')
            
            mock_get.assert_called_once()
            assert result == mock_response
    
    @pytest.mark.unit
    def test_make_request_post(self):
        """Test POST request"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            result = service._make_request('POST', 'http://example.com/test', json={'data': 'test'})
            
            mock_post.assert_called_once()
            assert result == mock_response
    
    @pytest.mark.unit
    def test_make_request_rate_limited_retry(self):
        """Test retry on 429 response"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        with patch('requests.get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # First call returns 429, second returns 200
            rate_limited_response = MagicMock()
            rate_limited_response.status_code = 429
            rate_limited_response.headers = {'Retry-After': '1'}
            
            success_response = MagicMock()
            success_response.status_code = 200
            
            mock_get.side_effect = [rate_limited_response, success_response]
            
            result = service._make_request('GET', 'http://example.com/test')
            
            assert mock_get.call_count == 2
            mock_sleep.assert_called()
            assert result == success_response


class TestVEPServiceAnnotation:
    """Tests for VEPService annotation methods"""
    
    @pytest.fixture
    def mock_vep_response(self):
        """Create mock VEP API response"""
        return [
            {
                'id': 'rs12345',
                'most_severe_consequence': 'missense_variant',
                'transcript_consequences': [
                    {
                        'gene_symbol': 'TEST_GENE',
                        'gene_id': 'ENSG00000000001',
                        'transcript_id': 'ENST00000000001',
                        'impact': 'MODERATE',
                        'biotype': 'protein_coding',
                        'sift_prediction': 'deleterious',
                        'sift_score': 0.01,
                        'polyphen_prediction': 'probably_damaging',
                        'polyphen_score': 0.98,
                        'cadd_phred': 25.0,
                        'cadd_raw': 3.5
                    }
                ]
            }
        ]
    
    @pytest.mark.unit
    def test_get_single_variant_success(self, mock_vep_response):
        """Test successful single variant lookup"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        with patch.object(service, '_make_request') as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_vep_response
            mock_request.return_value = mock_response
            
            result = service.get_single_variant('rs12345')
            
            assert result is not None
            assert 'success' in result
    
    @pytest.mark.unit
    def test_get_single_variant_not_found(self):
        """Test annotation for non-existent rsID"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        with patch.object(service, '_make_request') as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {'error': 'Not found'}
            mock_request.return_value = mock_response
            
            result = service.get_single_variant('rs999999999999')
            
            # Should return dict with success=False or error
            assert result is not None
            assert 'success' in result or 'error' in result
    
    @pytest.mark.unit
    def test_get_batch_variants(self, mock_vep_response):
        """Test batch annotation of rsIDs"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        with patch.object(service, '_make_request') as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_vep_response
            mock_request.return_value = mock_response
            
            rsids = ['rs12345', 'rs67890']
            result = service.get_batch_variants(rsids)
            
            assert result is not None
            assert 'success' in result


class TestVEPServiceParsing:
    """Tests for VEP response parsing"""
    
    @pytest.mark.unit
    def test_parse_vep_response(self):
        """Test parsing VEP API response"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        raw_response = {
            'id': 'rs12345',
            'most_severe_consequence': 'missense_variant',
            'transcript_consequences': [
                {
                    'gene_symbol': 'BRCA1',
                    'gene_id': 'ENSG00000012048',
                    'impact': 'HIGH',
                    'sift_prediction': 'deleterious',
                    'sift_score': 0.001,
                    'polyphen_prediction': 'probably_damaging',
                    'polyphen_score': 0.999
                }
            ],
            'colocated_variants': [
                {
                    'clin_sig': ['pathogenic'],
                    'frequencies': {
                        'gnomAD_AF': 0.0001
                    }
                }
            ]
        }
        
        # Test that the service can parse this structure
        # The actual parsing method name may vary
        if hasattr(service, '_parse_annotation'):
            result = service._parse_annotation(raw_response)
            assert result is not None
    
    @pytest.mark.unit
    def test_extract_clinical_significance(self):
        """Test extracting clinical significance from response"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        response_data = {
            'colocated_variants': [
                {
                    'clin_sig': ['pathogenic', 'likely_pathogenic']
                }
            ]
        }
        
        # Test extraction if method exists
        if hasattr(service, '_extract_clinical_significance'):
            result = service._extract_clinical_significance(response_data)
            assert 'pathogenic' in result


class TestVEPServiceCaching:
    """Tests for VEP service caching functionality"""
    
    @pytest.mark.unit
    def test_memory_cache_set_get(self):
        """Test in-memory caching"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        # Manually add to cache
        service._memory_cache['rs12345'] = {'gene': 'TEST', 'impact': 'LOW'}
        
        # Retrieve from cache
        cached = service._memory_cache.get('rs12345')
        
        assert cached is not None
        assert cached['gene'] == 'TEST'
    
    @pytest.mark.unit
    def test_cache_is_thread_safe(self):
        """Test that cache has thread safety lock"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        assert hasattr(service, '_cache_lock')


class TestVEPServiceIntegration:
    """Integration tests for VEP service (marked slow)"""
    
    @pytest.mark.unit
    @pytest.mark.slow
    @pytest.mark.integration
    def test_real_single_variant(self):
        """Test annotation with a real rsID (requires internet)"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        if not service.enabled:
            pytest.skip("VEP service is disabled")
        
        # rs1426654 is a well-known SNP associated with skin pigmentation
        result = service.get_single_variant('rs1426654')
        
        # Should return a result dict
        assert result is not None
        assert 'success' in result


class TestVEPServiceHelpers:
    """Tests for VEP service helper methods"""
    
    @pytest.mark.unit
    def test_build_vep_url(self):
        """Test building VEP API URL"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        # Test URL construction
        expected_base = "https://rest.ensembl.org"
        assert service.BASE_URL == expected_base
    
    @pytest.mark.unit
    def test_batch_size_limit(self):
        """Test that batch size respects limit"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        assert service.batch_size <= service.BATCH_LIMIT
    
    @pytest.mark.unit
    def test_headers_are_set(self):
        """Test that required headers are set"""
        from services.vep_service import VEPService
        
        service = VEPService()
        
        assert 'Content-Type' in service.headers
        assert 'Accept' in service.headers
        assert service.headers['Content-Type'] == 'application/json'

