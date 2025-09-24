"""FastAPI web application for OpenFood."""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..api.api import api_router
from ..core.config import get_settings


# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting OpenFood FastAPI application...")
    yield
    # Shutdown
    print("Shutting down OpenFood FastAPI application...")

app = FastAPI(
    title="OpenGov Food API",
    description="Comprehensive consumer protection and food safety inspection management system for environmental health departments across California counties",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Routes
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "OpenGov Food",
        "version": "1.0.0",
        "description": "Comprehensive consumer protection and food safety inspection management system for environmental health departments across California counties",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "OpenFood",
        "version": "1.0.0"
    }


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )