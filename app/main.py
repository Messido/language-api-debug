from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.middleware.logging import RequestLoggingMiddleware
from app.routes import vocabulary, review_cards, progress, ai_practice, students, teachers, relationships, groups, grammar, practice
from app.services.db import connect_to_mongodb, close_mongodb_connection

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongodb()
    yield
    # Shutdown
    await close_mongodb_connection()

app = FastAPI(title="Language API", lifespan=lifespan)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:3000",
    "https://language-app-rust.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(vocabulary.router, prefix="/api", tags=["vocabulary"])
app.include_router(review_cards.router, prefix="/api", tags=["review-cards"])
app.include_router(progress.router, prefix="/api", tags=["progress"])
app.include_router(ai_practice.router, prefix="/api", tags=["ai-practice"])
app.include_router(students.router, prefix="/api", tags=["students"])
app.include_router(teachers.router, prefix="/api", tags=["teachers"])
app.include_router(relationships.router, prefix="/api", tags=["relationships"])
app.include_router(groups.router, prefix="/api", tags=["groups"])
app.include_router(grammar.router, prefix="/api", tags=["grammar"])
app.include_router(practice.router, prefix="/api", tags=["practice"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Language Learning API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
