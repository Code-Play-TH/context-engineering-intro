# Implementation Tasks - User Authentication & Role Management (MVP)

## Overview

This task list covers the MVP implementation of user authentication with JWT, basic RBAC, and essential user management features.

**Estimated Time: 5-7 days**

---

## Phase 1: Project Setup & Database Foundation

-   [x] 1. Set up project structure and dependencies

    -   Create backend directory structure (`app/api/v1/`, `app/core/`, `app/models/`, `app/services/`)
    -   Install core dependencies: FastAPI, SQLModel, Alembic, python-jose, passlib, python-dotenv
    -   Set up virtual environment (`venv_linux`)
    -   Create `.env.example` with required variables
    -   _Requirements: All_

-   [x] 2. Configure database connection

    -   Create `app/core/database.py` with PostgreSQL connection
    -   Set up SQLModel engine and session management
    -   Configure connection pooling (pool_size=20)
    -   Add database URL to environment variables
    -   _Requirements: All_

-   [x] 3. Initialize Alembic for migrations

    -   Run `alembic init alembic`
    -   Configure `alembic.ini` with database URL
    -   Update `alembic/env.py` to use SQLModel metadata
    -   Create initial migration structure
    -   _Requirements: All_

---

## Phase 2: Core Models & Authentication

-   [x] 4. Create User model

    -   Define `app/models/user.py` with User table
    -   Fields: id, email, hashed_password, full_name, role, is_active, created_at, updated_at, last_login_at
    -   Add Role enum (admin, campaign_manager, account_executive, viewer)
    -   Create database migration
    -   _Requirements: 1.1, 1.2_

-   [x] 5. Create RefreshToken model

    -   Define `app/models/refresh_token.py`
    -   Fields: id, user_id, token_hash, expires_at, created_at, revoked
    -   Add foreign key relationship to User
    -   Create database migration
    -   _Requirements: 1.4_

-   [x] 6. Implement password hashing utilities

    -   Create `app/core/security.py`
    -   Implement `hash_password()` using bcrypt (cost factor 12)
    -   Implement `verify_password()` for password verification
    -   Add password strength validation function
    -   _Requirements: 1.1, 1.5_

-   [x] 7. Implement JWT token generation and validation
    -   Add JWT functions to `app/core/security.py`
    -   Implement `create_access_token()` (30 min expiry)
    -   Implement `create_refresh_token()` (7 days expiry)
    -   Implement `verify_token()` for token validation
    -   Add token payload structure (user_id, email, role)
    -   _Requirements: 1.2, 1.4_

---

## Phase 3: Authentication Service & API

-   [x] 8. Create AuthService

    -   Create `app/services/auth_service.py`
    -   Implement `login(email, password)` method
    -   Implement `refresh_token(refresh_token)` method with token rotation
    -   Implement `logout(refresh_token)` method
    -   Add rate limiting check (5 attempts per 15 min) - Skipped for MVP
    -   _Requirements: 1.2, 1.4_

-   [x] 9. Create authentication endpoints

    -   Create `app/api/v1/auth.py`
    -   POST `/api/v1/auth/login` - Login with email/password
    -   POST `/api/v1/auth/refresh` - Refresh access token
    -   POST `/api/v1/auth/logout` - Logout and invalidate token
    -   GET `/api/v1/auth/me` - Get current user info
    -   Add request/response schemas
    -   _Requirements: 1.2_

-   [x] 10. Implement authentication middleware
    -   Create `app/core/auth.py` with `get_current_user` dependency
    -   Extract and validate JWT from Authorization header
    -   Return user object or raise 401 Unauthorized
    -   Add to protected endpoints
    -   _Requirements: 1.2, 1.3_

---

## Phase 4: User Management

-   [x] 11. Create UserService

    -   Create `app/services/user_service.py`
    -   Implement `create_user(user_data)` method
    -   Implement `get_user_by_id(user_id)` method
    -   Implement `get_user_by_email(email)` method
    -   Implement `update_user(user_id, user_data)` method
    -   Implement `deactivate_user(user_id)` method (soft delete)
    -   _Requirements: 1.1, 1.6_

-   [x] 12. Create user management endpoints
    -   Create `app/api/v1/users.py`
    -   POST `/api/v1/users` - Create user (Admin only)
    -   GET `/api/v1/users` - List users with pagination (Admin only)
    -   GET `/api/v1/users/{id}` - Get user details
    -   PUT `/api/v1/users/{id}` - Update user
    -   DELETE `/api/v1/users/{id}` - Deactivate user (Admin only)
    -   _Requirements: 1.1, 1.6_

---

## Phase 5: Role-Based Access Control (RBAC)

-   [x] 13. Implement permission checking

    -   Create `app/services/permission_service.py`
    -   Define permission matrix for 4 roles
    -   Implement `check_permission(user_role, resource, action)` method
    -   Create permission decorators for endpoints
    -   _Requirements: 1.3_

-   [x] 14. Add role-based endpoint protection
    -   Apply permission checks to user management endpoints
    -   Add `require_role` dependency for protected routes
    -   Test access control for all 4 roles
    -   Return 403 Forbidden for insufficient permissions
    -   _Requirements: 1.3_

---

## Phase 6: Password Management (MVP - Basic)

-   [x] 15. Implement password reset flow

    -   Add `request_password_reset(email)` to AuthService
    -   Generate reset token (1 hour expiry)
    -   Store reset token in database (or use JWT)
    -   POST `/api/v1/auth/password-reset` endpoint
    -   _Requirements: 1.5_

-   [x] 16. Implement password reset confirmation

    -   Add `confirm_password_reset(token, new_password)` to AuthService
    -   Validate reset token
    -   Update password and invalidate all refresh tokens
    -   POST `/api/v1/auth/password-reset/confirm` endpoint
    -   _Requirements: 1.5_

---

## Phase 7: Basic Audit Logging

-   [x] 17. Create AuditLog model

    -   Define `app/models/audit_log.py`
    -   Fields: id, user_id, action, resource, resource_id, details (JSON), ip_address, success, created_at
    -   Create database migration
    -   Add index on created_at
    -   _Requirements: 1.7_

-   [x] 18. Implement audit logging service
    -   Create `app/services/audit_service.py`
    -   Implement `log_login(user_id, ip, success)` method
    -   Implement `log_user_action(user_id, action, details)` method
    -   Add logging to login, logout, and user management actions
    -   _Requirements: 1.7_

---

## Phase 8: Testing & Validation

-   [x]\* 19. Write unit tests for authentication

    -   Test password hashing and verification
    -   Test JWT token generation and validation
    -   Test login with valid/invalid credentials
    -   Test token refresh and rotation
    -   _Requirements: All_

-   [x]\* 20. Write integration tests

    -   Test complete login flow
    -   Test password reset flow
    -   Test RBAC enforcement
    -   Test audit logging
    -   _Requirements: All_

---

## Phase 9: Database Seeding & Documentation

-   [x] 21. Create database seed script

    -   Create `scripts/seed_admin.py`
    -   Generate default admin user
    -   Add sample users for each role
    -   Document seeding process in README
    -   _Requirements: 1.1_

-   [ ] 22. Run migrations and verify
    -   Execute `alembic upgrade head`
    -   Verify all tables created correctly
    -   Run seed script
    -   Test login with seeded users
    -   _Requirements: All_

---

## Success Criteria

✅ Users can register and login with email/password  
✅ JWT tokens are generated and validated correctly  
✅ Token refresh works with rotation  
✅ 4 user roles have appropriate permissions  
✅ Password reset flow works  
✅ Audit logs capture authentication events  
✅ All endpoints return proper error codes (401, 403)  
✅ Database migrations run successfully

---

## Notes

-   Focus on core authentication first, skip advanced features
-   Use simple in-memory rate limiting for MVP (Redis later)
-   Email sending for password reset can be mocked initially
-   Comprehensive testing marked as optional (\*) for MVP speed
-   Account lockout can be added in Phase 2
