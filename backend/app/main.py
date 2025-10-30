"""
FastAPI Application Entry Point

Initializes the FastAPI application with all routes, middleware, and configuration.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

# P0: Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.api import health, auth, decks, cards, topics, documents, fcm_tokens, notifications
from app.db.base import engine
from app.db.models import Base
from app.core.firebase import initialize_firebase

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()

# P0: Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


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

    # Initialize Firebase Admin SDK
    logger.info("initializing_firebase")
    initialize_firebase()

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

# P0: Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
app.include_router(topics.router, prefix=settings.api_v1_prefix)
app.include_router(documents.router, prefix=settings.api_v1_prefix)
app.include_router(fcm_tokens.router, prefix=settings.api_v1_prefix)
app.include_router(notifications.router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "OpenDeck API",
        "version": "1.0.0",
        "environment": settings.env,
        "docs": "/docs",
    }
