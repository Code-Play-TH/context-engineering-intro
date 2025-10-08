# Design Document - User Authentication & Role Management

## Overview

The User Authentication and Role Management system provides secure access control for the KOL Influencer Management Platform using JWT-based authentication with OAuth2 password flow. The system implements role-based access control (RBAC) with four distinct roles and comprehensive audit logging.

## Architecture

### High-Level Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  (Next.js)  │◀─────│   Backend    │◀─────│  Database   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Redis     │
                     │ (Sessions &  │
                     │  Tokens)     │
                     └──────────────┘
```

### Authentication Flow

```
1. User Login
   ├─▶ POST /api/v1/auth/login (email, password)
   ├─▶ Validate credentials (bcrypt)
   ├─▶ Generate JWT access token (30 min expiry)
   ├─▶ Generate refresh token (7 days expiry)
   ├─▶ Store hashed refresh token in DB
   └─▶ Return tokens to client

2. Protected Request
   ├─▶ Client sends access token in Authorization header
   ├─▶ Middleware validates JWT signature
   ├─▶ Extract user ID and role from token
   ├─▶ Check role permissions for endpoint
   └─▶ Allow/Deny request

3. Token Refresh
   ├─▶ POST /api/v1/auth/refresh (refresh_token)
   ├─▶ Validate refresh token hash in DB
   ├─▶ Generate new access token
   ├─▶ Generate new refresh token (rotation)
   ├─▶ Invalidate old refresh token
   └─▶ Return new tokens
```

## Components and Interfaces

### Backend Components

#### 1. Authentication Service (`app/services/auth_service.py`)

```python
class AuthService:
    async def login(email: str, password: str) -> TokenPair
    async def refresh_token(refresh_token: str) -> TokenPair
    async def logout(refresh_token: str) -> None
    async def verify_token(token: str) -> User
    async def hash_password(password: str) -> str
    async def verify_password(plain: str, hashed: str) -> bool
```

#### 2. User Service (`app/services/user_service.py`)

```python
class UserService:
    async def create_user(user_data: UserCreate) -> User
    async def get_user_by_id(user_id: int) -> User
    async def get_user_by_email(email: str) -> User
    async def update_user(user_id: int, user_data: UserUpdate) -> User
    async def deactivate_user(user_id: int) -> None
    async def list_users(filters: UserFilters) -> List[User]
```

#### 3. Permission Service (`app/services/permission_service.py`)

```python
class PermissionService:
    def check_permission(user_role: Role, resource: str, action: str) -> bool
    def get_role_permissions(role: Role) -> Dict[str, List[str]]
```

#### 4. Audit Service (`app/services/audit_service.py`)

```python
class AuditService:
    async def log_login(user_id: int, ip: str, user_agent: str, success: bool) -> None
    async def log_user_action(user_id: int, action: str, details: dict) -> None
    async def get_audit_logs(filters: AuditFilters) -> List[AuditLog]
```

### API Endpoints

#### Authentication Endpoints (`app/api/v1/auth.py`)

```python
POST   /api/v1/auth/login              # Login with email/password
POST   /api/v1/auth/refresh            # Refresh access token
POST   /api/v1/auth/logout             # Logout and invalidate tokens
POST   /api/v1/auth/password-reset     # Request password reset
POST   /api/v1/auth/password-reset/confirm  # Confirm password reset
GET    /api/v1/auth/me                 # Get current user info
```

#### User Management Endpoints (`app/api/v1/users.py`)

```python
POST   /api/v1/users                   # Create user (Admin only)
GET    /api/v1/users                   # List users (Admin only)
GET    /api/v1/users/{id}              # Get user details
PUT    /api/v1/users/{id}              # Update user
DELETE /api/v1/users/{id}              # Deactivate user (Admin only)
PUT    /api/v1/users/{id}/role         # Update user role (Admin only)
GET    /api/v1/users/{id}/audit-logs   # Get user audit logs (Admin only)
```

### Frontend Components

#### Authentication Context (`frontend/src/hooks/useAuth.ts`)

```typescript
interface AuthContext {
    user: User | null;
    login: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    refreshToken: () => Promise<void>;
    hasPermission: (resource: string, action: string) => boolean;
}
```

#### Protected Route Component (`frontend/src/components/auth/ProtectedRoute.tsx`)

```typescript
<ProtectedRoute requiredRole="campaign_manager">
    <CampaignDashboard />
</ProtectedRoute>
```

## Data Models

### User Model (`app/models/user.py`)

```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    role: Role  # Enum: admin, campaign_manager, account_executive, viewer
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = None
```

### RefreshToken Model (`app/models/refresh_token.py`)

```python
class RefreshToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    token_hash: str = Field(unique=True, index=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked: bool = Field(default=False)
```

### AuditLog Model (`app/models/audit_log.py`)

```python
class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(foreign_key="user.id")
    action: str  # login, logout, create_user, update_role, etc.
    resource: Optional[str]  # user, campaign, kol, etc.
    resource_id: Optional[int]
    details: dict = Field(default={}, sa_column=Column(JSON))
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
```

### Role Enum (`app/models/enums.py`)

```python
class Role(str, Enum):
    ADMIN = "admin"
    CAMPAIGN_MANAGER = "campaign_manager"
    ACCOUNT_EXECUTIVE = "account_executive"
    VIEWER = "viewer"
```

## Security Implementation

### Password Hashing

-   Use bcrypt with cost factor 12
-   Salt automatically generated per password
-   Never store plain text passwords

### JWT Token Structure

```json
{
    "sub": "user_id",
    "email": "user@example.com",
    "role": "campaign_manager",
    "exp": 1234567890,
    "iat": 1234567890
}
```

### Token Storage

-   Access tokens: Client-side (memory or secure cookie)
-   Refresh tokens: Database (hashed) + Client-side (HTTP-only cookie)
-   Never store tokens in localStorage (XSS vulnerability)

### Rate Limiting

-   Login attempts: 5 per 15 minutes per IP
-   Account lockout: 30 minutes after 5 failed attempts
-   Token refresh: 10 per hour per user

### RBAC Permission Matrix

| Resource       | Admin | Campaign Manager | Account Executive | Viewer |
| -------------- | ----- | ---------------- | ----------------- | ------ |
| Users          | CRUD  | R                | R                 | R      |
| Campaigns      | CRUD  | CRUD             | R                 | R      |
| KOLs           | CRUD  | CRUD             | CRUD              | R      |
| Briefs         | CRUD  | CRUD             | CRUD              | R      |
| Communications | CRUD  | R                | CRUD              | R      |
| Reports        | CRUD  | CRUD             | R                 | R      |
| System Config  | CRUD  | -                | -                 | -      |

## Error Handling

### Authentication Errors

```python
401 Unauthorized: Invalid credentials, expired token
403 Forbidden: Insufficient permissions
429 Too Many Requests: Rate limit exceeded
423 Locked: Account temporarily locked
```

### Error Response Format

```json
{
    "error": "authentication_failed",
    "message": "Invalid email or password",
    "details": null
}
```

## Testing Strategy

### Unit Tests

-   Password hashing and verification
-   JWT token generation and validation
-   Permission checking logic
-   Rate limiting logic

### Integration Tests

-   Login flow end-to-end
-   Token refresh flow
-   Password reset flow
-   Role-based access control
-   Account lockout mechanism

### Security Tests

-   SQL injection attempts
-   XSS attempts in user inputs
-   CSRF protection
-   Token tampering detection
-   Brute force protection

## Performance Considerations

### Caching Strategy

-   User permissions: Cache in Redis (5 min TTL)
-   Role definitions: Cache in memory (immutable)
-   Failed login attempts: Track in Redis with TTL

### Database Indexes

```sql
CREATE INDEX idx_user_email ON user(email);
CREATE INDEX idx_user_role ON user(role);
CREATE INDEX idx_refresh_token_hash ON refresh_token(token_hash);
CREATE INDEX idx_refresh_token_user ON refresh_token(user_id);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);
```

### Query Optimization

-   Use connection pooling (pool_size=20)
-   Lazy load relationships
-   Paginate audit logs (50 per page)

## Deployment Considerations

### Environment Variables

```bash
SECRET_KEY=<strong-random-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_RESET_EXPIRE_HOURS=1
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
```

### Migration Strategy

```bash
# Initial migration
alembic revision --autogenerate -m "create user and auth tables"
alembic upgrade head

# Seed admin user
python scripts/seed_admin.py
```

### Monitoring

-   Track failed login attempts
-   Monitor token refresh rates
-   Alert on unusual authentication patterns
-   Log all permission denials
