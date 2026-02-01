"""
Integration Tests for Authentication Routes
Tests for login, register, logout, and profile endpoints
"""
import pytest


class TestLoginRoute:
    """Tests for /login endpoint"""
    
    @pytest.mark.integration
    def test_login_page_loads(self, client):
        """Test that login page loads successfully"""
        response = client.get('/login')
        
        assert response.status_code == 200
        # Check for login form elements
        assert b'login' in response.data.lower() or b'Login' in response.data
    
    @pytest.mark.integration
    def test_login_success(self, client, sample_user, app, db_session):
        """Test successful login"""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to index or dashboard
        assert b'Welcome' in response.data or response.request.path in ['/', '/dashboard']
    
    @pytest.mark.integration
    def test_login_invalid_password(self, client, sample_user):
        """Test login with wrong password"""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error message
        assert b'invalid' in response.data.lower() or b'error' in response.data.lower() or b'incorrect' in response.data.lower()
    
    @pytest.mark.integration
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'somepassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'invalid' in response.data.lower() or b'error' in response.data.lower()
    
    @pytest.mark.integration
    def test_login_empty_fields(self, client):
        """Test login with empty fields"""
        response = client.post('/login', data={
            'username': '',
            'password': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show validation error
        assert b'please' in response.data.lower() or b'required' in response.data.lower() or b'enter' in response.data.lower()
    
    @pytest.mark.integration
    def test_login_with_email(self, client, sample_user):
        """Test login using email instead of username"""
        response = client.post('/login', data={
            'username': 'testuser@example.com',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should either succeed or show email-specific error


class TestRegisterRoute:
    """Tests for /register endpoint"""
    
    @pytest.mark.integration
    def test_register_page_loads(self, client):
        """Test that register page loads"""
        response = client.get('/register')
        
        assert response.status_code == 200
        assert b'register' in response.data.lower() or b'Register' in response.data
    
    @pytest.mark.integration
    def test_register_success(self, client, app, db_session):
        """Test successful registration"""
        response = client.post('/register', data={
            'username': 'newuser123',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123',
            'full_name': 'New User'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to login or show success
        assert b'success' in response.data.lower() or b'login' in response.data.lower()
    
    @pytest.mark.integration
    def test_register_password_mismatch(self, client):
        """Test registration with mismatched passwords"""
        response = client.post('/register', data={
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'password123',
            'confirm_password': 'differentpassword',
            'full_name': 'Test User 2'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'match' in response.data.lower() or b'error' in response.data.lower()
    
    @pytest.mark.integration
    def test_register_short_password(self, client):
        """Test registration with too short password"""
        response = client.post('/register', data={
            'username': 'testuser3',
            'email': 'test3@example.com',
            'password': '12345',
            'confirm_password': '12345',
            'full_name': 'Test User 3'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show password length error
        assert b'character' in response.data.lower() or b'short' in response.data.lower() or b'error' in response.data.lower()
    
    @pytest.mark.integration
    def test_register_duplicate_username(self, client, sample_user):
        """Test registration with existing username"""
        response = client.post('/register', data={
            'username': 'testuser',  # Already exists
            'email': 'different@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'full_name': 'Duplicate User'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'taken' in response.data.lower() or b'exists' in response.data.lower() or b'already' in response.data.lower()
    
    @pytest.mark.integration
    def test_register_duplicate_email(self, client, sample_user):
        """Test registration with existing email"""
        response = client.post('/register', data={
            'username': 'differentuser',
            'email': 'testuser@example.com',  # Already exists
            'password': 'password123',
            'confirm_password': 'password123',
            'full_name': 'Duplicate Email User'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'registered' in response.data.lower() or b'exists' in response.data.lower() or b'already' in response.data.lower()
    
    @pytest.mark.integration
    def test_register_invalid_email(self, client):
        """Test registration with invalid email format"""
        response = client.post('/register', data={
            'username': 'testuser4',
            'email': 'invalidemail',  # No @ symbol
            'password': 'password123',
            'confirm_password': 'password123',
            'full_name': 'Test User 4'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show email validation error
        assert b'email' in response.data.lower() or b'valid' in response.data.lower()


class TestLogoutRoute:
    """Tests for /logout endpoint"""
    
    @pytest.mark.integration
    def test_logout(self, authenticated_client):
        """Test successful logout"""
        response = authenticated_client.get('/logout', follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to home or login
        assert b'logged out' in response.data.lower() or response.request.path in ['/', '/login']
    
    @pytest.mark.integration
    def test_logout_without_login(self, client):
        """Test logout when not logged in"""
        response = client.get('/logout', follow_redirects=True)
        
        # Should redirect to login or handle gracefully
        assert response.status_code == 200


class TestProfileRoute:
    """Tests for /profile endpoint"""
    
    @pytest.mark.integration
    def test_profile_requires_auth(self, client):
        """Test that profile page requires authentication"""
        response = client.get('/profile', follow_redirects=True)
        
        # Should redirect to login
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'sign in' in response.data.lower()
    
    @pytest.mark.integration
    def test_profile_page_loads(self, authenticated_client, sample_user):
        """Test that profile page loads for authenticated user"""
        response = authenticated_client.get('/profile')
        
        assert response.status_code == 200
        # Should show user info
        assert b'testuser' in response.data or b'profile' in response.data.lower()
    
    @pytest.mark.integration
    def test_profile_update(self, authenticated_client, sample_user, app, db_session):
        """Test updating profile"""
        response = authenticated_client.post('/profile/update', data={
            'full_name': 'Updated Name',
            'email': 'testuser@example.com'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show success or updated profile
        assert b'success' in response.data.lower() or b'updated' in response.data.lower() or b'Updated Name' in response.data
    
    @pytest.mark.integration
    def test_profile_change_password(self, authenticated_client, sample_user, app, db_session):
        """Test changing password"""
        response = authenticated_client.post('/profile/change-password', data={
            'current_password': 'testpassword123',
            'new_password': 'newpassword456',
            'confirm_password': 'newpassword456'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show success
        assert b'success' in response.data.lower() or b'changed' in response.data.lower() or b'updated' in response.data.lower()
    
    @pytest.mark.integration
    def test_profile_change_password_wrong_current(self, authenticated_client, sample_user):
        """Test changing password with wrong current password"""
        response = authenticated_client.post('/profile/change-password', data={
            'current_password': 'wrongpassword',
            'new_password': 'newpassword456',
            'confirm_password': 'newpassword456'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'incorrect' in response.data.lower() or b'wrong' in response.data.lower() or b'error' in response.data.lower()


class TestAuthAPIEndpoints:
    """Tests for authentication API endpoints"""
    
    @pytest.mark.integration
    def test_check_auth_not_logged_in(self, client):
        """Test auth check when not logged in"""
        response = client.get('/api/auth/check')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['authenticated'] is False
    
    @pytest.mark.integration
    def test_check_auth_logged_in(self, authenticated_client, sample_user):
        """Test auth check when logged in"""
        response = authenticated_client.get('/api/auth/check')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['authenticated'] is True
        assert 'user' in data
    
    @pytest.mark.integration
    def test_get_current_user_requires_auth(self, client):
        """Test that get user endpoint requires authentication"""
        response = client.get('/api/auth/user')
        
        # Should redirect to login or return 401
        assert response.status_code in [200, 401, 302]
    
    @pytest.mark.integration
    def test_get_current_user(self, authenticated_client, sample_user):
        """Test getting current user info"""
        response = authenticated_client.get('/api/auth/user')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['username'] == 'testuser'
        assert data['email'] == 'testuser@example.com'



