"""
KOL Management System - FastAPI Application

Main FastAPI application with router registration and middleware configuration.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.core.config import get_settings
from app.core.database import init_db
from app.api.endpoints import auth, kols, campaigns, calendar, content_monitoring, analytics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting KOL Management System API")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down KOL Management System API")


# Create FastAPI application
app = FastAPI(
    title="KOL Management System API",
    description="""
    Comprehensive KOL (Key Opinion Leader) Influencer Management System

    ## Features

    * **KOL Management**: Full CRUD operations for KOL profiles
    * **Social Media Integration**: Multi-platform social media data collection
    * **Campaign Management**: End-to-end campaign lifecycle management
    * **Communication**: Multi-channel messaging (Email, Discord, Line)
    * **Analytics**: Advanced reporting, insights, and data visualization
    * **Background Tasks**: Asynchronous processing with Celery
    * **Content Monitoring**: AI-powered content analysis, brand safety, and compliance checking

    ## Authentication

    This API uses Bearer token authentication. Include your token in the Authorization header:
    ```
    Authorization: Bearer <your-token>
    ```

    ## Rate Limiting

    API endpoints are rate limited to ensure fair usage and system stability.
    """,
    version="1.0.0",
    contact={
        "name": "KOL Management System",
        "email": "support@kolsystem.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )


# Global exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """
    404 Not Found handler.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": "The requested resource was not found",
            "path": str(request.url.path)
        }
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Basic health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "KOL Management System API",
        "version": "1.0.0"
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with system information.
    """
    from app.tasks import check_task_system_health

    try:
        # Check task system health
        task_health = check_task_system_health()

        return {
            "status": "healthy",
            "service": "KOL Management System API",
            "version": "1.0.0",
            "components": {
                "database": "healthy",  # Will be implemented with actual DB health check
                "redis": "healthy",     # Will be implemented with actual Redis health check
                "task_system": task_health.get("overall_status", "unknown")
            },
            "task_queues": task_health.get("queue_lengths", {}),
            "active_workers": task_health.get("celery_health", {}).get("healthy_workers", 0)
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e) if settings.DEBUG else "Health check failed"
            }
        )


# API Information endpoints
@app.get("/info", tags=["Information"])
async def api_info():
    """
    API information and capabilities.
    """
    return {
        "name": "KOL Management System API",
        "version": "1.0.0",
        "description": "Comprehensive KOL Influencer Management System",
        "features": [
            "KOL Profile Management",
            "Social Media Integration",
            "Campaign Management",
            "Multi-channel Communication",
            "Performance Analytics",
            "Content Monitoring",
            "Background Task Processing"
        ],
        "supported_platforms": [
            "Instagram",
            "YouTube",
            "TikTok",
            "Twitter",
            "Facebook"
        ],
        "communication_channels": [
            "Email",
            "Discord",
            "Line Messaging"
        ]
    }


# Register API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(kols.router, prefix="/api/v1")
app.include_router(campaigns.router, prefix="/api/v1")
app.include_router(calendar.router, prefix="/api/v1")
app.include_router(content_monitoring.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")

# Additional routers will be added here as they are implemented
# app.include_router(communications.router, prefix="/api/v1")


# Custom OpenAPI schema
def custom_openapi():
    """
    Generate custom OpenAPI schema with additional information.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="KOL Management System API",
        version="1.0.0",
        description=app.description,
        routes=app.routes,
    )

    # Add custom schema extensions
    openapi_schema["info"]["x-logo"] = {
        "url": "https://via.placeholder.com/120x40?text=KOL+API"
    }

    # Add server information
    openapi_schema["servers"] = [
        {
            "url": settings.API_BASE_URL,
            "description": "Production server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # Add default security
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    API root endpoint with welcome message.
    """
    return {
        "message": "Welcome to the KOL Management System API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
        "info": "/info"
    }


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
        log_level="info"
    )