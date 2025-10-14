"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, users, kols, campaigns, briefs, messages, rate_limits, performance, report_templates, reports
from app.core.config import settings


app = FastAPI(
    title="KOL Management System",
    description="Comprehensive platform for managing Key Opinion Leader campaigns",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(kols.router, prefix="/api/v1")
app.include_router(campaigns.router, prefix="/api/v1")
app.include_router(briefs.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(rate_limits.router, prefix="/api/v1")
app.include_router(performance.router, prefix="/api/v1")
app.include_router(report_templates.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "KOL Management System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
