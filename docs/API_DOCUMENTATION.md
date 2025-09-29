# KOL Management System API Documentation

## Overview

The KOL Management System API provides comprehensive functionality for managing Key Opinion Leaders (KOLs), campaigns, content monitoring, and analytics. This RESTful API is built with FastAPI and follows OpenAPI 3.0 specifications.

## Base URL

- **Production**: `https://api.kolsystem.com`
- **Staging**: `https://staging-api.kolsystem.com`
- **Development**: `http://localhost:8000`

## Authentication

The API uses Bearer token authentication with JWT tokens.

### Getting a Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

### Using the Token

Include the token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Core Endpoints

### 🔐 Authentication

#### Login
```http
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "full_name": "Full Name",
    "is_active": true
  }
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
```

#### Logout
```http
POST /api/v1/auth/logout
```

### 👥 KOL Management

#### List KOLs
```http
GET /api/v1/kols?page=1&size=20&status=active&niche=fashion
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `size` (int): Items per page (default: 20, max: 100)
- `status` (string): Filter by status (active, inactive, blacklisted)
- `niche` (string): Filter by niche category
- `min_followers` (int): Minimum follower count
- `platform` (string): Filter by social media platform

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Fashion Influencer",
      "email": "influencer@example.com",
      "social_media_accounts": {
        "instagram": {
          "handle": "fashion_influencer",
          "verified": true,
          "followers": 100000
        }
      },
      "niche": ["fashion", "lifestyle"],
      "status": "active",
      "follower_counts": {
        "instagram": 100000
      },
      "engagement_rates": {
        "instagram": 0.05
      },
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

#### Get KOL by ID
```http
GET /api/v1/kols/{kol_id}
```

#### Create KOL
```http
POST /api/v1/kols
```

**Request Body:**
```json
{
  "name": "New Influencer",
  "email": "new@example.com",
  "social_media_accounts": {
    "instagram": {
      "handle": "new_influencer",
      "verified": false
    }
  },
  "niche": ["beauty", "skincare"],
  "communication_preferences": ["email", "discord"]
}
```

#### Update KOL
```http
PUT /api/v1/kols/{kol_id}
```

#### Delete KOL
```http
DELETE /api/v1/kols/{kol_id}
```

#### Get KOL Performance
```http
GET /api/v1/kols/{kol_id}/performance?start_date=2024-01-01&end_date=2024-01-31
```

### 📋 Campaign Management

#### List Campaigns
```http
GET /api/v1/campaigns?status=active&start_date=2024-01-01
```

**Query Parameters:**
- `status` (string): Filter by status (draft, active, paused, completed)
- `start_date` (date): Filter campaigns starting after this date
- `end_date` (date): Filter campaigns ending before this date
- `budget_min` (float): Minimum budget filter
- `budget_max` (float): Maximum budget filter

#### Create Campaign
```http
POST /api/v1/campaigns
```

**Request Body:**
```json
{
  "name": "Summer Fashion Campaign",
  "description": "Promote summer collection",
  "start_date": "2024-06-01T00:00:00Z",
  "end_date": "2024-08-31T23:59:59Z",
  "budget": 50000.00,
  "target_kpis": {
    "total_reach": 1000000,
    "engagement_rate": 0.05,
    "roi_percentage": 250
  },
  "required_keywords": ["summer", "fashion"],
  "required_hashtags": ["#summerfashion"],
  "brand_names": ["FashionBrand"]
}
```

#### Assign KOL to Campaign
```http
POST /api/v1/campaigns/{campaign_id}/assign-kol
```

**Request Body:**
```json
{
  "kol_id": 1,
  "compensation": 5000.00,
  "currency": "USD",
  "deliverables_total": 5,
  "notes": "5 Instagram posts and 2 stories"
}
```

#### Get Campaign Performance
```http
GET /api/v1/campaigns/{campaign_id}/performance
```

**Response:**
```json
{
  "campaign_id": 1,
  "total_reach": 750000,
  "total_engagement": 37500,
  "engagement_rate": 0.05,
  "total_posts": 15,
  "verified_posts": 12,
  "pending_posts": 3,
  "roi_percentage": 225.5,
  "total_cost": 45000.00,
  "total_value": 146475.00,
  "kol_performance": [
    {
      "kol_id": 1,
      "kol_name": "Fashion Influencer",
      "posts": 5,
      "reach": 200000,
      "engagement": 10000,
      "roi": 180.5
    }
  ]
}
```

### 📊 Content Monitoring

#### Get Campaign Content
```http
GET /api/v1/campaigns/{campaign_id}/content?status=pending
```

#### Verify Content
```http
POST /api/v1/content/{content_id}/verify
```

**Request Body:**
```json
{
  "verification_status": "verified",
  "notes": "Content meets all campaign requirements"
}
```

#### Get Content Analytics
```http
GET /api/v1/content/{content_id}/analytics
```

### 📈 Analytics and Reporting

#### Generate Campaign Report
```http
POST /api/v1/campaigns/{campaign_id}/generate-report
```

**Request Body:**
```json
{
  "report_type": "comprehensive",
  "include_comparisons": true,
  "include_forecasts": true,
  "format": "json",
  "sections": ["executive_summary", "performance_metrics", "recommendations"]
}
```

#### Calculate ROI
```http
POST /api/v1/analytics/roi/calculate
```

**Request Body:**
```json
{
  "campaign_id": 1,
  "attribution_model": "linear",
  "include_soft_metrics": true
}
```

#### Get Dashboard Data
```http
GET /api/v1/analytics/dashboard?time_range=last_30_days
```

### 💬 Communication

#### Send Message
```http
POST /api/v1/communications/send
```

**Request Body:**
```json
{
  "kol_id": 1,
  "channel": "email",
  "subject": "Campaign Update",
  "message": "Your campaign performance is excellent!",
  "scheduled_at": "2024-01-15T10:00:00Z"
}
```

#### Schedule Follow-up
```http
POST /api/v1/communications/schedule-followup
```

## Response Formats

### Success Response
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  }
}
```

### Pagination Response
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5,
  "has_next": true,
  "has_prev": false
}
```

## Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **204 No Content**: Resource deleted successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Default**: 100 requests per minute per user
- **Bulk operations**: 10 requests per minute
- **Analytics**: 20 requests per minute

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Webhooks

The system can send webhooks for important events:

### Content Detection
```json
{
  "event": "content.detected",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "content_id": 123,
    "campaign_id": 1,
    "kol_id": 1,
    "confidence_score": 0.85,
    "verification_status": "pending"
  }
}
```

### Campaign Status Change
```json
{
  "event": "campaign.status_changed",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "campaign_id": 1,
    "old_status": "active",
    "new_status": "completed"
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `AUTHENTICATION_FAILED` | Invalid credentials |
| `AUTHORIZATION_FAILED` | Insufficient permissions |
| `VALIDATION_ERROR` | Request validation failed |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `DUPLICATE_RESOURCE` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `EXTERNAL_API_ERROR` | External service error |
| `PROCESSING_ERROR` | Background processing error |

## SDK and Examples

### Python SDK
```python
from kol_api import KOLSystemClient

client = KOLSystemClient(
    base_url="https://api.kolsystem.com",
    api_key="your_api_key"
)

# Get KOLs
kols = client.kols.list(status="active", niche="fashion")

# Create campaign
campaign = client.campaigns.create({
    "name": "Summer Campaign",
    "budget": 10000,
    "start_date": "2024-06-01",
    "end_date": "2024-08-31"
})
```

### JavaScript SDK
```javascript
import { KOLSystemClient } from '@kolsystem/js-sdk';

const client = new KOLSystemClient({
  baseURL: 'https://api.kolsystem.com',
  apiKey: 'your_api_key'
});

// Get campaign performance
const performance = await client.campaigns.getPerformance(campaignId);
```

### cURL Examples
```bash
# Get KOLs
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.kolsystem.com/api/v1/kols?page=1&size=20"

# Create campaign
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Campaign","budget":5000}' \
  "https://api.kolsystem.com/api/v1/campaigns"
```

## Testing

### Postman Collection
Import our Postman collection for easy API testing:
- [KOL System API Collection](./postman/KOL_System_API.postman_collection.json)

### OpenAPI Specification
- [OpenAPI 3.0 Spec](./openapi.json)
- Interactive docs available at `/docs` endpoint

## Support

For API support:
- **Documentation**: [https://docs.kolsystem.com](https://docs.kolsystem.com)
- **Email**: api-support@kolsystem.com
- **Slack**: #api-support (for enterprise customers)

## Changelog

### v1.0.0 (2024-01-01)
- Initial API release
- Core KOL and campaign management
- Content monitoring and analytics
- Authentication and authorization

For detailed changelog, see [CHANGELOG.md](./CHANGELOG.md)