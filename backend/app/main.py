"""
FastAPI Application Entry Point

Initializes the FastAPI application with all routes, middleware, and configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.config import settings
from app.api import health, auth, decks, cards
from app.db.base import engine
from app.db.models import Base

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info("application_startup", env=settings.env)

    # Create database tables (in production, use Alembic migrations)
    if settings.is_development:
        logger.info("creating_database_tables")
        Base.metadata.create_all(bind=engine)

    yield

    # Shutdown
    logger.info("application_shutdown")
    engine.dispose()


# Initialize FastAPI app
app = FastAPI(
    title="OpenDeck API",
    description="AI-first flashcard generation backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(decks.router, prefix=settings.api_v1_prefix)
app.include_router(cards.router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "OpenDeck API",
        "version": "1.0.0",
        "environment": settings.env,
        "docs": "/docs",
    }
