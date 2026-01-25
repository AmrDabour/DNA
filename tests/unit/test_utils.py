"""
Unit Tests for Utility Functions
Tests for formatting and serialization utilities
"""
import pytest
import numpy as np
import json


class TestSerializationUtils:
    """Tests for serialization utility functions"""
    
    @pytest.mark.unit
    def test_convert_numpy_int64(self):
        """Test converting numpy int64 to Python int"""
        from utils.serialization import convert_to_serializable
        
        value = np.int64(42)
        result = convert_to_serializable(value)
        
        assert result == 42
        assert isinstance(result, int)
        assert not isinstance(result, np.integer)
    
    @pytest.mark.unit
    def test_convert_numpy_int32(self):
        """Test converting numpy int32 to Python int"""
        from utils.serialization import convert_to_serializable
        
        value = np.int32(100)
        result = convert_to_serializable(value)
        
        assert result == 100
        assert isinstance(result, int)
    
    @pytest.mark.unit
    def test_convert_numpy_float64(self):
        """Test converting numpy float64 to Python float"""
        from utils.serialization import convert_to_serializable
        
        value = np.float64(3.14159)
        result = convert_to_serializable(value)
        
        assert abs(result - 3.14159) < 0.0001
        assert isinstance(result, float)
        assert not isinstance(result, np.floating)
    
    @pytest.mark.unit
    def test_convert_numpy_float32(self):
        """Test converting numpy float32 to Python float"""
        from utils.serialization import convert_to_serializable
        
        value = np.float32(2.718)
        result = convert_to_serializable(value)
        
        assert isinstance(result, float)
    
    @pytest.mark.unit
    def test_convert_numpy_bool(self):
        """Test converting numpy bool to Python bool"""
        from utils.serialization import convert_to_serializable
        
        value = np.bool_(True)
        result = convert_to_serializable(value)
        
        assert result is True
        assert isinstance(result, bool)
    
    @pytest.mark.unit
    def test_convert_numpy_array(self):
        """Test converting numpy array to Python list"""
        from utils.serialization import convert_to_serializable
        
        value = np.array([1, 2, 3, 4, 5])
        result = convert_to_serializable(value)
        
        assert result == [1, 2, 3, 4, 5]
        assert isinstance(result, list)
    
    @pytest.mark.unit
    def test_convert_nested_dict(self):
        """Test converting nested dict with numpy values"""
        from utils.serialization import convert_to_serializable
        
        value = {
            'count': np.int64(10),
            'average': np.float64(5.5),
            'values': np.array([1, 2, 3]),
            'nested': {
                'score': np.float32(0.95)
            }
        }
        result = convert_to_serializable(value)
        
        assert result['count'] == 10
        assert isinstance(result['count'], int)
        assert result['values'] == [1, 2, 3]
        assert isinstance(result['nested']['score'], float)
    
    @pytest.mark.unit
    def test_convert_list_with_numpy(self):
        """Test converting list containing numpy values"""
        from utils.serialization import convert_to_serializable
        
        value = [np.int64(1), np.float64(2.5), np.bool_(False)]
        result = convert_to_serializable(value)
        
        assert result == [1, 2.5, False]
        assert all(not isinstance(x, (np.integer, np.floating, np.bool_)) for x in result)
    
    @pytest.mark.unit
    def test_convert_preserves_regular_types(self):
        """Test that regular Python types are preserved"""
        from utils.serialization import convert_to_serializable
        
        value = {
            'string': 'hello',
            'int': 42,
            'float': 3.14,
            'bool': True,
            'none': None,
            'list': [1, 2, 3]
        }
        result = convert_to_serializable(value)
        
        assert result == value
    
    @pytest.mark.unit
    def test_convert_unknown_type(self):
        """Test that unknown types are converted to string"""
        from utils.serialization import convert_to_serializable
        
        class CustomObject:
            def __str__(self):
                return "custom_object"
        
        value = CustomObject()
        result = convert_to_serializable(value)
        
        assert result == "custom_object"
        assert isinstance(result, str)
    
    @pytest.mark.unit
    def test_result_is_json_serializable(self):
        """Test that result can be serialized to JSON"""
        from utils.serialization import convert_to_serializable
        
        value = {
            'numpy_int': np.int64(42),
            'numpy_float': np.float64(3.14),
            'numpy_array': np.array([1, 2, 3]),
            'nested': {
                'more_numpy': np.float32(0.5)
            }
        }
        result = convert_to_serializable(value)
        
        # Should not raise an exception
        json_str = json.dumps(result)
        assert json_str is not None
        
        # Should round-trip correctly
        parsed = json.loads(json_str)
        assert parsed['numpy_int'] == 42


class TestEnsureStringItems:
    """Tests for ensure_string_items function"""
    
    @pytest.mark.unit
    def test_convert_simple_list(self):
        """Test converting simple list to strings"""
        from utils.serialization import ensure_string_items
        
        items = [1, 2, 3, 4.5, True]
        result = ensure_string_items(items)
        
        assert result == ['1', '2', '3', '4.5', 'True']
        assert all(isinstance(x, str) for x in result)
    
    @pytest.mark.unit
    def test_convert_nested_list(self):
        """Test converting nested list to strings"""
        from utils.serialization import ensure_string_items
        
        items = [1, [2, 3], [4, [5, 6]]]
        result = ensure_string_items(items)
        
        assert result[0] == '1'
        assert result[1] == ['2', '3']
        assert result[2][1] == ['5', '6']
    
    @pytest.mark.unit
    def test_convert_dict(self):
        """Test converting dict values to strings"""
        from utils.serialization import ensure_string_items
        
        items = {'a': 1, 'b': 2.5, 'c': True}
        result = ensure_string_items(items)
        
        assert result == {'a': '1', 'b': '2.5', 'c': 'True'}
    
    @pytest.mark.unit
    def test_convert_nested_dict(self):
        """Test converting nested dict to strings"""
        from utils.serialization import ensure_string_items
        
        items = {'outer': {'inner': 42}}
        result = ensure_string_items(items)
        
        assert result['outer']['inner'] == '42'
    
    @pytest.mark.unit
    def test_convert_single_value(self):
        """Test converting single value to string"""
        from utils.serialization import ensure_string_items
        
        result = ensure_string_items(42)
        assert result == '42'
        
        result = ensure_string_items(3.14)
        assert result == '3.14'


class TestFormattingUtils:
    """Tests for formatting utility functions"""
    
    @pytest.mark.unit
    def test_get_accuracy_badge_high(self):
        """Test accuracy badge for high accuracy"""
        from utils.formatting import get_accuracy_badge
        
        badge = get_accuracy_badge(90)
        
        assert 'bg-success' in badge
        assert '90%' in badge
    
    @pytest.mark.unit
    def test_get_accuracy_badge_medium(self):
        """Test accuracy badge for medium accuracy"""
        from utils.formatting import get_accuracy_badge
        
        badge = get_accuracy_badge(70)
        
        assert 'bg-warning' in badge
        assert '70%' in badge
    
    @pytest.mark.unit
    def test_get_accuracy_badge_low(self):
        """Test accuracy badge for low accuracy"""
        from utils.formatting import get_accuracy_badge
        
        badge = get_accuracy_badge(50)
        
        assert 'bg-secondary' in badge
        assert '50%' in badge
    
    @pytest.mark.unit
    def test_get_accuracy_badge_invalid(self):
        """Test accuracy badge with invalid input"""
        from utils.formatting import get_accuracy_badge
        
        badge = get_accuracy_badge('invalid')
        assert badge == ''
        
        badge = get_accuracy_badge(None)
        assert badge == ''
    
    @pytest.mark.unit
    def test_format_characteristics_html_basic(self):
        """Test formatting physical characteristics to HTML"""
        from utils.formatting import format_characteristics_html
        
        data = {
            'gender': 'Male',
            'ancestry': 'European',
            'population_code': 'CEU',
            'physical_characteristics': {
                'hair': {
                    'color': 'Brown',
                    'color_accuracy': 85,
                    'texture': 'Straight',
                    'texture_accuracy': 75
                },
                'eyes': {
                    'color': 'Blue',
                    'color_accuracy': 90,
                    'shape': 'Almond',
                    'shape_accuracy': 70
                },
                'skin': {
                    'tone': 'Light',
                    'tone_accuracy': 80
                },
                'facial_features': {},
                'body_structure': {},
                'other_traits': {}
            }
        }
        
        html = format_characteristics_html(data)
        
        assert 'Male' in html
        assert 'European' in html
        assert 'CEU' in html
        assert 'Brown' in html
        assert 'Blue' in html
        assert 'Light' in html
    
    @pytest.mark.unit
    def test_format_characteristics_html_missing_data(self):
        """Test formatting with missing physical characteristics"""
        from utils.formatting import format_characteristics_html
        
        data = {
            'gender': 'Female',
            'ancestry': 'Asian',
            'population_code': 'JPT'
            # No physical_characteristics
        }
        
        html = format_characteristics_html(data)
        
        assert 'Incomplete Data' in html or 'No physical characteristics' in html
    
    @pytest.mark.unit
    def test_format_characteristics_html_array_values(self):
        """Test formatting with array values (backwards compatibility)"""
        from utils.formatting import format_characteristics_html
        
        data = {
            'gender': 'Male',
            'ancestry': 'African',
            'population_code': 'YRI',
            'physical_characteristics': {
                'hair': {
                    'color': ['Black'],  # Array format
                    'texture': ['Curly']
                },
                'eyes': {
                    'color': ['Brown'],
                    'shape': ['Round']
                },
                'skin': {
                    'tone': ['Dark']
                },
                'facial_features': {},
                'body_structure': {},
                'other_traits': {}
            }
        }
        
        html = format_characteristics_html(data)
        
        assert 'Black' in html
        assert 'Curly' in html
    
    @pytest.mark.unit
    def test_format_disease_report_html_basic(self):
        """Test formatting disease report to HTML"""
        from utils.formatting import format_disease_report_html
        
        data = {
            'profile_summary': {
                'gender': 'Male',
                'ancestry': 'European',
                'population_code': 'CEU'
            },
            'disease_risks': [
                {
                    'disease_name': 'Type 2 Diabetes',
                    'risk_level': 'Moderate Risk',
                    'description': 'A metabolic disease',
                    'affected_genes': ['TCF7L2', 'PPARG'],
                    'prevalence_in_population': '10%',
                    'key_mutations': ['rs7903146'],
                    'recommendations': ['Regular exercise', 'Healthy diet']
                }
            ]
        }
        
        html = format_disease_report_html(data)
        
        assert 'Type 2 Diabetes' in html
        assert 'Moderate Risk' in html
        assert 'TCF7L2' in html
        assert 'Regular exercise' in html
    
    @pytest.mark.unit
    def test_format_disease_report_html_high_risk(self):
        """Test formatting disease report with high risk"""
        from utils.formatting import format_disease_report_html
        
        data = {
            'profile_summary': {
                'gender': 'Female',
                'ancestry': 'European',
                'population_code': 'CEU'
            },
            'disease_risks': [
                {
                    'disease_name': 'Breast Cancer',
                    'risk_level': 'High Risk',
                    'description': 'A type of cancer',
                    'affected_genes': ['BRCA1'],
                    'recommendations': ['Regular screening']
                }
            ]
        }
        
        html = format_disease_report_html(data)
        
        assert 'bg-danger' in html  # High risk color
        assert 'Breast Cancer' in html
    
    @pytest.mark.unit
    def test_format_disease_report_html_low_risk(self):
        """Test formatting disease report with low risk"""
        from utils.formatting import format_disease_report_html
        
        data = {
            'profile_summary': {
                'gender': 'Male',
                'ancestry': 'Asian',
                'population_code': 'JPT'
            },
            'disease_risks': [
                {
                    'disease_name': 'Lactose Intolerance',
                    'risk_level': 'Low Risk',
                    'description': 'Difficulty digesting lactose',
                    'affected_genes': ['LCT'],
                    'recommendations': []
                }
            ]
        }
        
        html = format_disease_report_html(data)
        
        assert 'bg-success' in html  # Low risk color
    
    @pytest.mark.unit
    def test_format_disease_report_html_empty_risks(self):
        """Test formatting disease report with no risks"""
        from utils.formatting import format_disease_report_html
        
        data = {
            'profile_summary': {
                'gender': 'Male',
                'ancestry': 'European',
                'population_code': 'CEU'
            },
            'disease_risks': []
        }
        
        html = format_disease_report_html(data)
        
        assert 'No Disease Risk Data' in html or 'No specific disease' in html

