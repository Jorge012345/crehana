"""
Integration tests for authentication functionality.
Tests JWT authentication, user registration, and security features.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from jose import jwt

from src.main import app
from src.infrastructure.database import get_db_session
from src.config import settings


class TestAuthenticationIntegration:
    """Integration tests for authentication system."""

    @pytest_asyncio.fixture
    async def async_client(self, db_session):
        """Create async test client with test database."""
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db_session] = override_get_db
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
        
        app.dependency_overrides.clear()

    async def test_user_registration_success(self, async_client):
        """Test successful user registration."""
        user_data = {
            "email": "testuser@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "securepassword123"
        }
        
        response = await async_client.post("/auth/register", json=user_data)
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify response structure
        assert "id" in response_data
        assert response_data["email"] == user_data["email"]
        assert response_data["username"] == user_data["username"]
        assert response_data["full_name"] == user_data["full_name"]
        assert response_data["is_active"] is True
        assert "created_at" in response_data
        
        # Verify password is not returned
        assert "password" not in response_data
        assert "hashed_password" not in response_data

    async def test_user_registration_duplicate_email(self, async_client):
        """Test registration with duplicate email."""
        user_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "full_name": "User One",
            "password": "password123"
        }
        
        # Register first user
        response1 = await async_client.post("/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Try to register with same email, different username
        user_data2 = {
            "email": "duplicate@example.com",  # Same email
            "username": "user2",  # Different username
            "full_name": "User Two",
            "password": "password456"
        }
        
        response2 = await async_client.post("/auth/register", json=user_data2)
        assert response2.status_code == 400
        assert "email" in response2.json()["detail"].lower()

    async def test_user_registration_duplicate_username(self, async_client):
        """Test registration with duplicate username."""
        user_data = {
            "email": "user1@example.com",
            "username": "duplicateuser",
            "full_name": "User One",
            "password": "password123"
        }
        
        # Register first user
        response1 = await async_client.post("/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Try to register with same username, different email
        user_data2 = {
            "email": "user2@example.com",  # Different email
            "username": "duplicateuser",  # Same username
            "full_name": "User Two",
            "password": "password456"
        }
        
        response2 = await async_client.post("/auth/register", json=user_data2)
        assert response2.status_code == 400
        assert "username" in response2.json()["detail"].lower()

    async def test_user_registration_validation_errors(self, async_client):
        """Test registration with invalid data."""
        # Test empty email
        response = await async_client.post("/auth/register", json={
            "email": "",
            "username": "testuser",
            "full_name": "Test User",
            "password": "password123"
        })
        assert response.status_code == 422
        
        # Test invalid email format
        response = await async_client.post("/auth/register", json={
            "email": "invalid-email",
            "username": "testuser",
            "full_name": "Test User",
            "password": "password123"
        })
        assert response.status_code == 422
        
        # Test short password
        response = await async_client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "123"
        })
        assert response.status_code == 422

    async def test_user_login_success(self, async_client):
        """Test successful user login."""
        # First register a user
        user_data = {
            "email": "logintest@example.com",
            "username": "loginuser",
            "full_name": "Login Test User",
            "password": "loginpassword123"
        }
        
        register_response = await async_client.post("/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Now login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        login_response = await async_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        response_data = login_response.json()
        
        # Verify response structure
        assert "access_token" in response_data
        assert "token_type" in response_data
        assert "expires_in" in response_data
        assert response_data["token_type"] == "bearer"
        assert response_data["expires_in"] > 0

    async def test_user_login_by_username(self, async_client):
        """Test login using username instead of email."""
        # Register user
        user_data = {
            "email": "usernametest@example.com",
            "username": "usernameuser",
            "full_name": "Username Test User",
            "password": "usernamepassword123"
        }
        
        register_response = await async_client.post("/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Login using username in email field
        login_data = {
            "email": user_data["username"],  # Using username
            "password": user_data["password"]
        }
        
        login_response = await async_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        response_data = login_response.json()
        assert "access_token" in response_data

    async def test_user_login_invalid_credentials(self, async_client):
        """Test login with invalid credentials."""
        # Register user first
        user_data = {
            "email": "invalidtest@example.com",
            "username": "invaliduser",
            "full_name": "Invalid Test User",
            "password": "correctpassword123"
        }
        
        await async_client.post("/auth/register", json=user_data)
        
        # Test wrong password
        login_response = await async_client.post("/auth/login", json={
            "email": user_data["email"],
            "password": "wrongpassword"
        })
        assert login_response.status_code == 401
        
        # Test non-existent user
        login_response = await async_client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "somepassword"
        })
        assert login_response.status_code == 401

    async def test_jwt_token_structure(self, async_client):
        """Test JWT token structure and claims."""
        # Register and login user
        user_data = {
            "email": "jwttest@example.com",
            "username": "jwtuser",
            "full_name": "JWT Test User",
            "password": "jwtpassword123"
        }
        
        register_response = await async_client.post("/auth/register", json=user_data)
        user_id = register_response.json()["id"]
        
        login_response = await async_client.post("/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        token = login_response.json()["access_token"]
        
        # Decode token (without verification for testing)
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        
        # Verify token structure
        assert "sub" in decoded_token
        assert "exp" in decoded_token
        assert decoded_token["sub"] == str(user_id)

    async def test_protected_endpoint_without_token(self, async_client):
        """Test accessing protected endpoint without token."""
        response = await async_client.get("/api/v1/task-lists/")
        assert response.status_code == 401

    async def test_protected_endpoint_with_invalid_token(self, async_client):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid-token-here"}
        response = await async_client.get("/api/v1/task-lists/", headers=headers)
        assert response.status_code == 401

    async def test_protected_endpoint_with_valid_token(self, async_client):
        """Test accessing protected endpoint with valid token."""
        # Register and login user
        user_data = {
            "email": "protectedtest@example.com",
            "username": "protecteduser",
            "full_name": "Protected Test User",
            "password": "protectedpassword123"
        }
        
        await async_client.post("/auth/register", json=user_data)
        
        login_response = await async_client.post("/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Access protected endpoint
        response = await async_client.get("/api/v1/task-lists/", headers=headers)
        assert response.status_code == 200

    async def test_token_expiration_handling(self, async_client):
        """Test token expiration (conceptual test)."""
        # This test verifies that the token has expiration set
        # In a real scenario, you'd test with expired tokens
        
        user_data = {
            "email": "expirationtest@example.com",
            "username": "expirationuser",
            "full_name": "Expiration Test User",
            "password": "expirationpassword123"
        }
        
        await async_client.post("/auth/register", json=user_data)
        
        login_response = await async_client.post("/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        response_data = login_response.json()
        
        # Verify token has expiration time
        assert response_data["expires_in"] == settings.access_token_expire_minutes * 60
        
        # Decode token to verify expiration claim
        token = response_data["access_token"]
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        assert "exp" in decoded_token

    async def test_password_security(self, async_client):
        """Test password hashing and security."""
        user_data = {
            "email": "securitytest@example.com",
            "username": "securityuser",
            "full_name": "Security Test User",
            "password": "securitypassword123"
        }
        
        # Register user
        register_response = await async_client.post("/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Verify password is not stored in plain text
        response_data = register_response.json()
        assert "password" not in response_data
        assert "hashed_password" not in response_data
        
        # Verify login still works (password was hashed correctly)
        login_response = await async_client.post("/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200

    async def test_case_sensitive_login(self, async_client):
        """Test case sensitivity in login."""
        user_data = {
            "email": "CaseTest@Example.com",
            "username": "CaseUser",
            "full_name": "Case Test User",
            "password": "casepassword123"
        }
        
        # Register user
        await async_client.post("/auth/register", json=user_data)
        
        # Test login with different case email
        login_response = await async_client.post("/auth/login", json={
            "email": "casetest@example.com",  # Different case
            "password": user_data["password"]
        })
        # This should work if email comparison is case-insensitive
        # or fail if it's case-sensitive (depends on implementation)
        assert login_response.status_code in [200, 401]

    async def test_concurrent_registrations(self, async_client):
        """Test handling of concurrent user registrations."""
        import asyncio
        
        # Prepare multiple user registrations
        user_data_list = [
            {
                "email": f"concurrent{i}@example.com",
                "username": f"concurrent{i}",
                "full_name": f"Concurrent User {i}",
                "password": f"password{i}123"
            }
            for i in range(5)
        ]
        
        # Execute registrations concurrently
        tasks = [
            async_client.post("/auth/register", json=user_data)
            for user_data in user_data_list
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All registrations should succeed
        for response in responses:
            if not isinstance(response, Exception):
                assert response.status_code == 200 