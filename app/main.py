from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.middleware.logging import RequestLoggingMiddleware
from app.routes import vocabulary, review_cards, progress
from app.services.db import connect_to_mongodb, close_mongodb_connection

# Initialize logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("🚀 Starting Language Learning API...")
    await connect_to_mongodb()
    yield
    await close_mongodb_connection()
    logger.info("👋 Shutting down Language Learning API...")


app = FastAPI(
    title="Language Learning API",
    description="API for the language learning app - serves vocabulary from Google Sheets",
    version="1.0.0",
    lifespan=lifespan
)


# Global exception handler - catches ALL unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that logs all unhandled exceptions.
    Returns a clean error response while logging the full stack trace.
    """
    logger.exception(
        f"Unhandled exception | Path: {request.url.path} | "
        f"Method: {request.method} | Error: {str(exc)}"
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred",
            "path": str(request.url.path)
        }
    )


# Add request logging middleware (before CORS)
app.add_middleware(RequestLoggingMiddleware)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",              # Vite dev server
        "http://localhost:5174",              # Vite alternate port
        "http://localhost:3000",              # Alternative dev port
        "https://language-app-rust.vercel.app" # Production Vercel frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vocabulary.router, prefix="/api", tags=["vocabulary"])
app.include_router(review_cards.router, prefix="/api", tags=["review-cards"])
app.include_router(progress.router, prefix="/api", tags=["progress"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Language Learning API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
