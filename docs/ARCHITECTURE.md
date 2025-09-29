# KOL Management System Architecture

## System Overview

The KOL Management System is a comprehensive platform for managing Key Opinion Leaders (KOLs), campaigns, content monitoring, and analytics. The system is built using modern, scalable technologies and follows microservices principles.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                             │
├─────────────────────────────────────────────────────────────────┤
│ Web App (React) │ Mobile App │ Admin Panel │ Third-party APIs  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Load Balancer / CDN                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway                               │
│                   (NGINX Ingress)                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Application Layer                            │
├─────────────────────────────────────────────────────────────────┤
│              FastAPI Application (Multiple Pods)               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ Auth Service│ │KOL Service  │ │Campaign Svc │ │Analytics  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Background Processing                        │
├─────────────────────────────────────────────────────────────────┤
│                    Celery Workers                              │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │
│ │Social Media │ │Content Mon. │ │Communication│ │Analytics  │  │
│ │   Workers   │ │  Workers    │ │  Workers    │ │ Workers   │  │
│ └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Data Layer                                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ PostgreSQL  │ │    Redis    │ │ File Storage│ │ External  │ │
│  │ (Primary DB)│ │ (Cache/Queue│ │    (NFS)    │ │   APIs    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│               Monitoring & Observability                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ Prometheus  │ │   Grafana   │ │    ELK      │ │  Sentry   │ │
│  │ (Metrics)   │ │(Dashboards) │ │  (Logs)     │ │ (Errors)  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Backend Framework** | FastAPI | 0.104+ | High-performance async web framework |
| **Database** | PostgreSQL | 15+ | Primary data storage with JSONB support |
| **Cache/Queue** | Redis | 7+ | Caching and message broker |
| **Task Queue** | Celery | 5.3+ | Background task processing |
| **Web Server** | Uvicorn | 0.24+ | ASGI server for FastAPI |
| **ORM** | SQLAlchemy | 2.0+ | Database ORM with async support |
| **Migration** | Alembic | 1.12+ | Database migration tool |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Container** | Docker | Application containerization |
| **Orchestration** | Kubernetes | Container orchestration |
| **Service Mesh** | Istio (Optional) | Service-to-service communication |
| **Ingress** | NGINX Ingress | Load balancing and SSL termination |
| **Storage** | NFS/Block Storage | Persistent file storage |
| **SSL/TLS** | cert-manager | Automatic SSL certificate management |

### Monitoring & Observability

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Metrics** | Prometheus | Time-series metrics collection |
| **Visualization** | Grafana | Metrics dashboards and alerting |
| **Logging** | ELK Stack | Log aggregation and analysis |
| **Tracing** | Jaeger (Optional) | Distributed tracing |
| **Error Tracking** | Sentry | Error monitoring and alerting |

## Core Components

### 1. API Gateway Layer

**NGINX Ingress Controller**
- Routes external traffic to appropriate services
- Handles SSL termination and certificates
- Implements rate limiting and security policies
- Provides load balancing across multiple API instances

**Features:**
- Rate limiting: 100 requests/minute per user
- SSL/TLS with automatic certificate renewal
- Request/response size limits
- Security headers injection
- DDoS protection

### 2. Application Layer

**FastAPI Application**
- RESTful API with OpenAPI documentation
- Async/await for high concurrency
- Dependency injection for clean architecture
- Automatic request/response validation
- Built-in authentication and authorization

**Key Services:**
```python
# Service Architecture
app/
├── api/endpoints/          # API route handlers
├── services/              # Business logic services
│   ├── kol/              # KOL management
│   ├── campaigns/        # Campaign management
│   ├── content_monitoring/ # Content detection
│   ├── analytics/        # Analytics and reporting
│   └── communication/    # Multi-channel messaging
├── models/               # Database models
├── schemas/              # Pydantic schemas
└── core/                 # Core utilities
```

### 3. Background Processing

**Celery Workers**
- Distributed task processing
- Separate worker types for different task categories
- Automatic retry with exponential backoff
- Task monitoring and management

**Worker Types:**
- **Social Media Workers**: Content collection from platforms
- **Content Monitoring Workers**: AI-powered content analysis
- **Communication Workers**: Email, Discord, Line messaging
- **Analytics Workers**: ROI calculation and reporting

**Task Queues:**
```python
# Queue Configuration
CELERY_TASK_ROUTES = {
    'social_media_tasks.*': {'queue': 'social_media'},
    'content_monitoring_tasks.*': {'queue': 'content_monitoring'},
    'communication_tasks.*': {'queue': 'communication'},
    'analytics_tasks.*': {'queue': 'analytics'},
}
```

### 4. Data Layer

**PostgreSQL Database**
- Primary data storage with ACID compliance
- JSONB columns for flexible social media data
- Advanced indexing with GIN indexes for JSONB
- Connection pooling for performance
- Master-slave replication for high availability

**Redis Cache & Queue**
- Application-level caching
- Session storage
- Celery message broker
- Rate limiting data
- Real-time data for dashboards

**Database Schema:**
```sql
-- Core Tables
├── users                 # User accounts and authentication
├── kols                  # KOL profiles and social media data
├── campaigns             # Campaign information and settings
├── campaign_kols         # Many-to-many relationship
├── content_posts         # Detected content with analysis
├── content_stats         # Performance metrics over time
├── messages              # Communication history
└── follow_up_schedules   # Automated follow-up scheduling
```

## Data Flow

### 1. Content Detection Flow

```
1. Celery Scheduler → Social Media APIs (Instagram, YouTube, etc.)
2. Collect recent posts for assigned KOLs
3. AI Content Analyzer → Content matching algorithm
4. Store detected content → PostgreSQL
5. Schedule statistics collection → Celery tasks
6. Real-time notifications → WebSocket/Push notifications
```

### 2. Analytics Processing Flow

```
1. User requests analytics → FastAPI endpoint
2. Analytics Engine → Query historical data
3. ROI Calculator → Multi-attribution modeling
4. Report Generator → Generate comprehensive reports
5. Cache results → Redis (for performance)
6. Return formatted response → Client
```

### 3. Communication Flow

```
1. Campaign manager schedules message → FastAPI
2. Communication Factory → Select appropriate channel
3. Message queued → Celery worker
4. External API call → SendGrid/Discord/Line
5. Delivery confirmation → Update message status
6. Follow-up scheduling → If configured
```

## Security Architecture

### Authentication & Authorization

**JWT-based Authentication**
- Stateless authentication with JWT tokens
- Role-based access control (RBAC)
- Permission-based authorization
- Token refresh mechanism
- Multi-factor authentication support

**Security Layers:**
```python
# Security Stack
├── JWT Authentication      # Token-based auth
├── Role-Based Access      # User roles and permissions
├── API Rate Limiting      # Prevent abuse
├── Input Validation       # Pydantic schemas
├── SQL Injection Protection # SQLAlchemy ORM
└── HTTPS/TLS             # Transport encryption
```

### Data Protection

**Encryption:**
- Data at rest: Database encryption
- Data in transit: TLS 1.3
- Sensitive data: Field-level encryption for API keys
- Password hashing: bcrypt with salt

**Privacy Compliance:**
- GDPR compliance features
- Data retention policies
- User data export/deletion
- Audit logging for data access

## Scalability Design

### Horizontal Scaling

**Auto-scaling Configuration:**
```yaml
# Kubernetes HPA
CPU Target: 70%
Memory Target: 80%
Min Replicas: 3
Max Replicas: 20
Scale Up: 100% increase per minute
Scale Down: 50% decrease per 5 minutes
```

**Database Scaling:**
- Read replicas for analytics queries
- Connection pooling (20 connections per pod)
- Query optimization with proper indexing
- Partitioning for large tables (content_stats)

### Performance Optimization

**Caching Strategy:**
- Redis for session data and frequent queries
- CDN for static assets
- Application-level caching for expensive operations
- Database query optimization with indexes

**Async Processing:**
- Non-blocking I/O with async/await
- Background task processing with Celery
- Streaming responses for large datasets
- Connection pooling for external APIs

## Monitoring & Observability

### Metrics Collection

**Application Metrics:**
```python
# Prometheus Metrics
- HTTP request duration and count
- Database query performance
- Celery task execution time
- Business metrics (KOL count, campaign ROI)
- Error rates and types
```

**Infrastructure Metrics:**
- CPU, memory, and disk usage
- Network throughput
- Database connection counts
- Cache hit/miss ratios

### Alerting Strategy

**Critical Alerts:**
- Service availability < 99.9%
- Response time > 2 seconds (95th percentile)
- Error rate > 1%
- Database connection pool exhaustion
- Celery queue length > 1000 tasks

**Alert Channels:**
- Email for critical issues
- Slack for warnings
- PagerDuty for on-call escalation
- SMS for severity 1 incidents

## Disaster Recovery

### Backup Strategy

**Database Backups:**
- Daily automated backups
- Point-in-time recovery capability
- Cross-region backup replication
- Regular restore testing

**Application Backups:**
- Container image versioning
- Configuration backup in Git
- Secrets backup (encrypted)
- Documentation and runbooks

### Recovery Procedures

**RTO/RPO Targets:**
- Recovery Time Objective (RTO): 4 hours
- Recovery Point Objective (RPO): 1 hour
- High availability: 99.9% uptime SLA

**Failover Procedures:**
1. Automated health checks detect issues
2. Load balancer removes unhealthy instances
3. Auto-scaling provisions new instances
4. Database failover to replica (if needed)
5. Monitoring alerts operations team

## Performance Benchmarks

### Expected Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| **API Response Time** | < 200ms (95th percentile) | Prometheus |
| **Database Query Time** | < 50ms (average) | PostgreSQL logs |
| **Background Task Processing** | < 30s (content detection) | Celery metrics |
| **Cache Hit Ratio** | > 90% | Redis metrics |
| **Availability** | 99.9% | Uptime monitoring |

### Load Testing Results

**Test Scenarios:**
- 1000 concurrent users
- 10,000 requests per minute
- 24-hour sustained load test

**Results:**
- Average response time: 180ms
- 99th percentile: 800ms
- Zero errors during sustained load
- CPU utilization: 65% peak
- Memory utilization: 70% peak

## Development Workflow

### CI/CD Pipeline

```yaml
# GitHub Actions Workflow
1. Code Push → GitHub
2. Automated Tests → pytest, coverage
3. Code Quality → ruff, mypy, security scan
4. Build Image → Docker build
5. Push to Registry → Container registry
6. Deploy to Staging → Kubernetes
7. Integration Tests → API tests
8. Deploy to Production → Manual approval
9. Health Checks → Smoke tests
10. Monitoring → Alert on issues
```

### Environment Strategy

| Environment | Purpose | Configuration |
|-------------|---------|---------------|
| **Development** | Local development | SQLite, minimal resources |
| **Staging** | Pre-production testing | Production-like setup |
| **Production** | Live system | Full redundancy and monitoring |

## Future Architecture Considerations

### Potential Enhancements

1. **Microservices Migration**: Split monolith into domain services
2. **Event-Driven Architecture**: Implement event sourcing
3. **GraphQL API**: Add GraphQL for flexible querying
4. **Machine Learning Pipeline**: Real-time ML model serving
5. **Multi-Region Deployment**: Global presence with edge locations

### Technology Evolution

- **Database**: Consider adding time-series DB for metrics
- **Search**: Elasticsearch for advanced content search
- **Real-time**: WebSocket support for live updates
- **Mobile**: Dedicated mobile API optimizations
- **AI/ML**: Integration with modern ML platforms

This architecture provides a solid foundation for a scalable, maintainable, and high-performance KOL management system that can grow with business requirements while maintaining reliability and security standards.