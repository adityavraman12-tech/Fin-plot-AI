from fastapi import FastAPI

from app.core.config import settings
from app.db.database import Base, engine
from app.db import models

from app.api.transactions import router as transaction_router
from app.api.profile import router as profile_router
from app.api.insights import router as insights_router
from app.api.copilot import router as copilot_router
from fastapi.middleware.cors import CORSMiddleware

# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.3.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://finplot-ai.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register APIs
app.include_router(transaction_router)
app.include_router(profile_router)
app.include_router(insights_router)
app.include_router(copilot_router)

@app.get("/")
def root():
    return {
        "message": "Personal Finance Coach API is running",
        "version": "0.3.0"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }