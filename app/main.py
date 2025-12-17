from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import vocabulary

app = FastAPI(
    title="Language Learning API",
    description="API for the language learning app - serves vocabulary from Google Sheets",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      # Vite dev server
        "http://localhost:3000",      # Alternative dev port
        "https://your-app.vercel.app" # Production URL - update this
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vocabulary.router, prefix="/api", tags=["vocabulary"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Language Learning API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
