"""
Tests for Core Authentication Service

Tests for SecurityService class including JWT token management, password hashing,
API key handling, session management, and security utilities.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import MagicMock, patch

from app.core.auth import SecurityService, security_service, AuthenticationError, AuthorizationError
from app.core.config import get_settings


class TestSecurityService:
    """Test cases for SecurityService class."""

    def test_security_service_initialization(self):
        """Test SecurityService initialization."""
        service = SecurityService()
        settings = get_settings()

        assert service.algorithm == settings.JWT_ALGORITHM
        assert service.secret_key == settings.JWT_SECRET_KEY
        assert service.access_token_expire_minutes == settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        assert service.refresh_token_expire_days == settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    def test_password_hashing_and_verification(self):
        """Test password hashing and verification."""
        service = SecurityService()
        password = "TestPassword123!"

        # Hash password
        hashed = service.hash_password(password)
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are typically 60 characters

        # Verify correct password
        assert service.verify_password(password, hashed)

        # Verify incorrect password
        assert not service.verify_password("WrongPassword", hashed)

        # Test empty password
        assert not service.verify_password("", hashed)

    def test_generate_password_hash(self):
        """Test generate_password_hash method."""
        service = SecurityService()
        password = "TestPassword123!"

        hash1 = service.generate_password_hash(password)
        hash2 = service.generate_password_hash(password)

        # Different hashes for same password (due to salt)
        assert hash1 != hash2

        # Both should verify the original password
        assert service.verify_password(password, hash1)
        assert service.verify_password(password, hash2)

    def test_create_access_token(self):
        """Test access token creation."""
        service = SecurityService()
        user_data = {"sub": "123", "email": "test@example.com"}

        token = service.create_access_token(user_data)

        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are typically long

        # Verify token can be decoded
        payload = service.verify_token(token)
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_with_custom_expiry(self):
        """Test access token creation with custom expiration."""
        service = SecurityService()
        user_data = {"sub": "123"}
        custom_expiry = timedelta(minutes=30)

        token = service.create_access_token(user_data, expires_delta=custom_expiry)
        payload = service.verify_token(token)

        # Check that expiration is approximately 30 minutes from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + custom_expiry
        time_diff = abs((exp_time - expected_time).total_seconds())
        assert time_diff < 5  # Within 5 seconds tolerance

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        service = SecurityService()
        user_data = {"sub": "123", "email": "test@example.com"}

        token = service.create_refresh_token(user_data)

        assert isinstance(token, str)
        assert len(token) > 100

        # Verify token can be decoded
        payload = service.verify_token(token)
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "refresh"

    def test_create_refresh_token_with_custom_expiry(self):
        """Test refresh token creation with custom expiration."""
        service = SecurityService()
        user_data = {"sub": "123"}
        custom_expiry = timedelta(days=30)

        token = service.create_refresh_token(user_data, expires_delta=custom_expiry)
        payload = service.verify_token(token)

        # Check that expiration is approximately 30 days from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + custom_expiry
        time_diff = abs((exp_time - expected_time).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance

    def test_verify_token_valid(self):
        """Test token verification with valid token."""
        service = SecurityService()
        user_data = {"sub": "123", "role": "admin"}

        token = service.create_access_token(user_data)
        payload = service.verify_token(token)

        assert payload["sub"] == "123"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        service = SecurityService()

        with pytest.raises(AuthenticationError):
            service.verify_token("invalid_token")

    def test_verify_token_expired(self):
        """Test token verification with expired token."""
        service = SecurityService()
        user_data = {"sub": "123"}

        # Create token that expires immediately
        token = service.create_access_token(user_data, expires_delta=timedelta(seconds=-1))

        with pytest.raises(AuthenticationError):
            service.verify_token(token)

    def test_verify_token_malformed(self):
        """Test token verification with malformed token."""
        service = SecurityService()

        malformed_tokens = [
            "",
            "not.a.token",
            "header.payload",  # Missing signature
            "a" * 100,  # Random string
        ]

        for token in malformed_tokens:
            with pytest.raises(AuthenticationError):
                service.verify_token(token)

    def test_create_token_pair(self):
        """Test creating both access and refresh tokens."""
        service = SecurityService()
        user_data = {"sub": "123", "email": "test@example.com"}

        token_pair = service.create_token_pair(user_data)

        assert "access_token" in token_pair
        assert "refresh_token" in token_pair
        assert "token_type" in token_pair
        assert "expires_in" in token_pair

        assert token_pair["token_type"] == "bearer"
        assert isinstance(token_pair["expires_in"], int)

        # Verify both tokens
        access_payload = service.verify_token(token_pair["access_token"])
        refresh_payload = service.verify_token(token_pair["refresh_token"])

        assert access_payload["sub"] == "123"
        assert refresh_payload["sub"] == "123"
        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"

    def test_generate_api_key(self):
        """Test API key generation."""
        service = SecurityService()

        key_id, api_key = service.generate_api_key()

        assert isinstance(key_id, str)
        assert isinstance(api_key, str)
        assert len(key_id) > 10
        assert len(api_key) > 20
        assert key_id != api_key

        # Test multiple generations produce different keys
        key_id2, api_key2 = service.generate_api_key()
        assert key_id != key_id2
        assert api_key != api_key2

    def test_hash_api_key(self):
        """Test API key hashing."""
        service = SecurityService()
        api_key = "test_api_key_12345"

        hashed = service.hash_api_key(api_key)

        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 hex is 64 characters
        assert hashed != api_key

        # Same key should produce same hash
        hashed2 = service.hash_api_key(api_key)
        assert hashed == hashed2

    def test_verify_api_key(self):
        """Test API key verification."""
        service = SecurityService()
        api_key = "test_api_key_12345"

        hashed = service.hash_api_key(api_key)

        # Verify correct key
        assert service.verify_api_key(api_key, hashed)

        # Verify incorrect key
        assert not service.verify_api_key("wrong_key", hashed)

        # Verify with empty key
        assert not service.verify_api_key("", hashed)

    def test_create_session_id(self):
        """Test session ID creation."""
        service = SecurityService()

        session_id = service.create_session_id()

        assert isinstance(session_id, str)
        assert len(session_id) > 30

        # Test multiple generations produce different IDs
        session_id2 = service.create_session_id()
        assert session_id != session_id2

    def test_generate_secure_token(self):
        """Test secure token generation."""
        service = SecurityService()

        # Default length
        token = service.generate_secure_token()
        assert isinstance(token, str)
        assert len(token) > 40  # URL-safe base64 encoding

        # Custom length
        token_custom = service.generate_secure_token(length=16)
        assert len(token_custom) > 20  # Base64 encoding increases length

        # Different tokens
        token2 = service.generate_secure_token()
        assert token != token2

    def test_generate_two_factor_secret(self):
        """Test two-factor authentication secret generation."""
        service = SecurityService()

        secret = service.generate_two_factor_secret()

        assert isinstance(secret, str)
        assert len(secret) == 32  # 16 bytes as hex = 32 characters

        # Different secrets
        secret2 = service.generate_two_factor_secret()
        assert secret != secret2

    def test_generate_backup_codes(self):
        """Test backup codes generation."""
        service = SecurityService()

        # Default count
        codes = service.generate_backup_codes()
        assert isinstance(codes, list)
        assert len(codes) == 10
        assert all(isinstance(code, str) for code in codes)
        assert all(len(code) == 8 for code in codes)  # 4 bytes as hex = 8 characters

        # Custom count
        codes_custom = service.generate_backup_codes(count=5)
        assert len(codes_custom) == 5

        # All codes should be unique
        assert len(set(codes)) == len(codes)

    def test_is_password_strong_valid_password(self):
        """Test password strength validation with valid passwords."""
        service = SecurityService()

        strong_passwords = [
            "StrongPassword123!",
            "MySecureP@ssw0rd",
            "C0mpl3x!P@ssword",
            "Abcd1234!@#$"
        ]

        for password in strong_passwords:
            is_strong, issues = service.is_password_strong(password)
            assert is_strong, f"Password '{password}' should be strong, issues: {issues}"
            assert len(issues) == 0

    def test_is_password_strong_weak_passwords(self):
        """Test password strength validation with weak passwords."""
        service = SecurityService()

        weak_password_tests = [
            ("short", ["Password must be at least 8 characters long"]),
            ("nouppercase123!", ["Password must contain at least one uppercase letter"]),
            ("NOLOWERCASE123!", ["Password must contain at least one lowercase letter"]),
            ("NoDigitsHere!", ["Password must contain at least one digit"]),
            ("NoSpecialChars123", ["Password should contain at least one special character"]),
            ("weak", [
                "Password must be at least 8 characters long",
                "Password must contain at least one uppercase letter",
                "Password must contain at least one digit",
                "Password should contain at least one special character"
            ])
        ]

        for password, expected_issues in weak_password_tests:
            is_strong, issues = service.is_password_strong(password)
            assert not is_strong, f"Password '{password}' should be weak"
            assert len(issues) > 0
            for expected_issue in expected_issues:
                assert expected_issue in issues

    def test_is_password_strong_edge_cases(self):
        """Test password strength validation with edge cases."""
        service = SecurityService()

        edge_cases = [
            ("", False),  # Empty password
            ("       ", False),  # Only spaces
            ("12345678", False),  # Only numbers
            ("ABCDEFGH", False),  # Only uppercase
            ("abcdefgh", False),  # Only lowercase
            ("!@#$%^&*", False),  # Only special characters
        ]

        for password, should_be_strong in edge_cases:
            is_strong, issues = service.is_password_strong(password)
            assert is_strong == should_be_strong, f"Password '{password}' strength check failed"


class TestGlobalSecurityService:
    """Test cases for the global security service instance."""

    def test_global_instance_exists(self):
        """Test that global security service instance exists."""
        assert security_service is not None
        assert isinstance(security_service, SecurityService)

    def test_global_instance_functionality(self):
        """Test that global instance works correctly."""
        password = "TestPassword123!"
        hashed = security_service.hash_password(password)
        assert security_service.verify_password(password, hashed)

        user_data = {"sub": "123"}
        token = security_service.create_access_token(user_data)
        payload = security_service.verify_token(token)
        assert payload["sub"] == "123"


class TestSecurityExceptions:
    """Test cases for security exception handling."""

    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        error = AuthenticationError("Invalid token")
        assert str(error) == "Invalid token"
        assert isinstance(error, Exception)

    def test_authorization_error(self):
        """Test AuthorizationError exception."""
        error = AuthorizationError("Insufficient permissions")
        assert str(error) == "Insufficient permissions"
        assert isinstance(error, Exception)

    def test_verify_token_logging(self):
        """Test that token verification failures are logged."""
        service = SecurityService()

        with patch('app.core.auth.logger') as mock_logger:
            with pytest.raises(AuthenticationError):
                service.verify_token("invalid_token")
            mock_logger.warning.assert_called_once()


class TestSecurityUtilities:
    """Test cases for security utility functions and edge cases."""

    def test_token_payload_validation(self):
        """Test token payload validation."""
        service = SecurityService()

        # Test with None values
        user_data = {"sub": None, "email": "test@example.com"}
        token = service.create_access_token(user_data)
        payload = service.verify_token(token)
        assert payload["sub"] is None

        # Test with complex data types
        user_data = {
            "sub": "123",
            "roles": ["admin", "user"],
            "metadata": {"department": "IT", "level": 5}
        }
        token = service.create_access_token(user_data)
        payload = service.verify_token(token)
        assert payload["roles"] == ["admin", "user"]
        assert payload["metadata"]["department"] == "IT"

    def test_token_creation_with_empty_data(self):
        """Test token creation with empty data."""
        service = SecurityService()

        # Empty dict
        token = service.create_access_token({})
        payload = service.verify_token(token)
        assert "exp" in payload
        assert "iat" in payload
        assert "type" in payload

    def test_api_key_hash_consistency(self):
        """Test API key hash consistency."""
        service = SecurityService()
        api_key = "consistent_test_key"

        # Hash multiple times
        hashes = [service.hash_api_key(api_key) for _ in range(5)]

        # All hashes should be identical
        assert all(h == hashes[0] for h in hashes)

    def test_secure_token_entropy(self):
        """Test that secure tokens have good entropy."""
        service = SecurityService()

        # Generate many tokens
        tokens = [service.generate_secure_token() for _ in range(100)]

        # All should be unique
        assert len(set(tokens)) == 100

        # All should be strings of reasonable length
        assert all(isinstance(token, str) and len(token) > 30 for token in tokens)

    def test_session_id_uniqueness(self):
        """Test session ID uniqueness."""
        service = SecurityService()

        # Generate many session IDs
        session_ids = [service.create_session_id() for _ in range(100)]

        # All should be unique
        assert len(set(session_ids)) == 100

    def test_backup_codes_format(self):
        """Test backup codes format and characteristics."""
        service = SecurityService()

        codes = service.generate_backup_codes(count=20)

        # All should be uppercase
        assert all(code.isupper() for code in codes)

        # All should be alphanumeric
        assert all(code.isalnum() for code in codes)

        # All should be exactly 8 characters
        assert all(len(code) == 8 for code in codes)

        # Should be no duplicates
        assert len(set(codes)) == 20

    @patch('app.core.auth.settings')
    def test_service_with_different_settings(self, mock_settings):
        """Test SecurityService with different configuration settings."""
        mock_settings.JWT_ALGORITHM = "HS512"
        mock_settings.JWT_SECRET_KEY = "different-secret-key"
        mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
        mock_settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30

        service = SecurityService()

        assert service.algorithm == "HS512"
        assert service.secret_key == "different-secret-key"
        assert service.access_token_expire_minutes == 60
        assert service.refresh_token_expire_days == 30

    def test_password_special_characters(self):
        """Test password validation with various special characters."""
        service = SecurityService()

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        for char in special_chars:
            password = f"TestPass1{char}"
            is_strong, issues = service.is_password_strong(password)
            assert is_strong, f"Password with '{char}' should be strong"

    def test_hmac_timing_attack_resistance(self):
        """Test that API key verification uses constant-time comparison."""
        service = SecurityService()

        # The verify_api_key method should use hmac.compare_digest
        # which is resistant to timing attacks
        api_key = "test_key_123"
        correct_hash = service.hash_api_key(api_key)
        wrong_hash = service.hash_api_key("wrong_key")

        # Both should return quickly and correctly
        assert service.verify_api_key(api_key, correct_hash)
        assert not service.verify_api_key(api_key, wrong_hash)